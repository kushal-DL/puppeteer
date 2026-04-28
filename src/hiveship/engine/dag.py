import concurrent.futures
import json
import logging
import pathlib
import re
from typing import Dict, Set, Tuple

from hiveship.config import ARTIFACT_CHAR_LIMIT, MAX_BLOCKS_PER_AGENT, MAX_DYNAMIC_AGENTS
from hiveship.engine.compression import compress_context, should_compress
from hiveship.engine.job_store import append_job_event, set_agent_state, update_job
from hiveship.llm import _create_model, executor_model, planner_model, sync_generate_and_parse, sync_generate_with_retry
from hiveship.models import AgentStatus, AgentTask, FailureClass, WorkflowPlan, classify_failure
from hiveship.workspace import read_agent_files, read_artifact_context

logger = logging.getLogger(__name__)


# ── Single-agent runner ───────────────────────────────────────────────────────

def _run_single_agent(
    agent: AgentTask,
    artifacts_dir: pathlib.Path,
    job_workspace: pathlib.Path,
    default_executor=None,
    llm_provider: str = "gemini",
    ollama_model: str = "",
    ollama_base_url: str = "",
    memory_block: str = "",
    skill_content: str = "",
) -> str:
    """Execute one agent: read context → call LLM → write artifact to disk.

    Returns the agent_name in all cases so the caller can find it in futures.
    On block: writes a ``_BLOCKED.json`` signal file; execute_dag re-queues.
    On failure: writes an error artifact then re-raises.
    """
    context = read_artifact_context(agent.input_keys, artifacts_dir)
    if not context:
        goal_file = artifacts_dir / "initial_goal.txt"
        context = {
            "initial_goal": goal_file.read_text(errors="replace")
            if goal_file.exists()
            else ""
        }

    # Compress context if it exceeds budget
    if should_compress(context):
        context = compress_context(context)

    file_context = read_agent_files(agent.read_files, job_workspace)

    _executor = default_executor or executor_model
    agent_model = (
        _create_model(llm_provider, agent.system_instruction, ollama_model, ollama_base_url)
        if agent.system_instruction
        else _executor
    )

    prompt = (
        f"Role: {agent.role_description}\n"
        f"Context: {json.dumps(context)}\n"
        f"Existing Files: {json.dumps(file_context)}\n"
    )

    # Inject memory context (frozen snapshot from job start)
    if memory_block:
        prompt += f"\nRepository Knowledge:\n{memory_block}\n"

    # Inject skill content if planner referenced skills
    if skill_content:
        prompt += f"\nProcedures:\n{skill_content}\n"

    prompt += (
        f"Format: {agent.output_format}\n"
        f"BLOCKED PROTOCOL: If your task is completely impossible because a "
        f"critical prerequisite artifact is ABSENT from the context above, "
        f'output ONLY this JSON: {{"blocked": true, "reason": "<what you need>"}}. '
        f"Use this ONLY as a last resort — never for information you can "
        f"reasonably infer or assume."
    )

    try:
        output = sync_generate_with_retry(agent_model, prompt)
    except Exception as e:
        logger.warning(f"Agent '{agent.agent_name}' failed: {e}")
        (artifacts_dir / f"{agent.agent_name}.txt").write_text(
            f"[AGENT FAILED: {type(e).__name__}]", encoding="utf-8"
        )
        raise RuntimeError(f"Agent '{agent.agent_name}' failed: {e}") from e

    # Strip markdown fences Gemini occasionally emits even with strict prompting
    output = re.sub(r"^\s*```(?:json)?\s*\n?", "", output, flags=re.IGNORECASE)
    output = re.sub(r"\n?\s*```\s*$", "", output).strip()

    # Detect blocked signal BEFORE treating output as a normal artifact
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and parsed.get("blocked") is True:
            reason = str(parsed.get("reason", "No reason provided."))[:500]
            logger.info(f"Agent '{agent.agent_name}' blocked: {reason}")
            (artifacts_dir / f"{agent.agent_name}_BLOCKED.json").write_text(
                json.dumps({"reason": reason}), encoding="utf-8"
            )
            return agent.agent_name
    except (json.JSONDecodeError, AttributeError):
        pass  # plain text or non-blocked JSON — treat as normal

    (artifacts_dir / f"{agent.agent_name}.txt").write_text(output, encoding="utf-8")
    return agent.agent_name


# ── Helper spawner ────────────────────────────────────────────────────────────

def _spawn_helper_agent(
    reason: str,
    blocked_agent: AgentTask,
    artifacts_dir: pathlib.Path,
    planner=None,
) -> AgentTask:
    """Ask the planner to synthesize exactly one AgentTask to unblock another."""
    available_keys = [p.stem for p in artifacts_dir.glob("*.txt")]
    prompt = (
        f"An agent named '{blocked_agent.agent_name}' "
        f"(role: '{blocked_agent.role_description}') cannot proceed.\n"
        f"Reason it is blocked: {reason}\n"
        f"Artifact keys already available on disk: {available_keys}\n"
        f"Synthesize exactly ONE AgentTask JSON that produces the missing "
        f"information and writes it as its output.\n"
        f"The JSON must have: agent_name, role_description, depends_on (must be []),\n"
        f"input_keys (from available keys above), read_files, output_format.\n"
        f"Rules:\n"
        f"- agent_name must be unique, snake_case, and clearly name the helper.\n"
        f"- depends_on MUST be [] — the helper runs on the very next tick.\n"
        f"- input_keys must only reference keys from: {available_keys}.\n"
        f"- Scope is minimal — solve only the stated blocker, nothing more."
    )
    _planner = planner or planner_model
    return sync_generate_and_parse(
        _planner, prompt, AgentTask,
        {},
    )


# ── DAG executor ──────────────────────────────────────────────────────────────

def execute_dag(
    plan: WorkflowPlan,
    artifacts_dir: pathlib.Path,
    job_workspace: pathlib.Path,
    job_id: str,
    dag_executor=None,
    dag_planner=None,
    llm_provider: str = "gemini",
    ollama_model: str = "",
    ollama_base_url: str = "",
    memory_block: str = "",
    skill_content: str = "",
) -> Tuple[int, int, int]:
    """Execute the agent DAG via a ThreadPoolExecutor that respects depends_on.

    Uses concurrent.futures.wait(FIRST_COMPLETED) — zero busy-polling.
    Agents whose dependencies are satisfied run in parallel (up to 4 threads).

    Returns (completed_count, failed_count, total_agent_count).
    """
    completed: Set[str] = set()
    failed: Set[str] = set()
    remaining: Dict[str, AgentTask] = {a.agent_name: a for a in plan.agents}
    futures: Dict[str, concurrent.futures.Future] = {}
    # Single source of truth for AgentTask objects — grows when helpers injected
    agent_registry: Dict[str, AgentTask] = dict(remaining)

    # Initialize agent lifecycle states
    for name in remaining:
        set_agent_state(job_id, name, AgentStatus.PENDING)

    dynamic_agent_count = 0
    block_counts: Dict[str, int] = {}
    block_reasons: Dict[str, list] = {}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while remaining or futures:
            # ── Prune transitive dependents of failed agents ──────────────────
            pruned = True
            while pruned:
                pruned = False
                to_drop = [
                    name for name, a in remaining.items()
                    if any(dep in failed for dep in a.depends_on)
                ]
                for name in to_drop:
                    logger.warning(f"Job {job_id}: Skipping '{name}' — dependency failed.")
                    failed.add(name)
                    del remaining[name]
                    set_agent_state(job_id, name, AgentStatus.PRUNED)
                    append_job_event(job_id, "agent_pruned", agent=name)
                    pruned = True

            # ── Dispatch all ready agents ─────────────────────────────────────
            ready = [
                a for name, a in remaining.items()
                if all(dep in completed for dep in a.depends_on)
            ]
            for agent in ready:
                futures[agent.agent_name] = pool.submit(
                    _run_single_agent, agent, artifacts_dir, job_workspace,
                    dag_executor, llm_provider, ollama_model, ollama_base_url,
                    memory_block, skill_content,
                )
                del remaining[agent.agent_name]
                set_agent_state(job_id, agent.agent_name, AgentStatus.RUNNING)
                append_job_event(job_id, "agent_started", agent=agent.agent_name)

            if futures:
                update_job(job_id, current_step=f"running: {', '.join(sorted(futures))}")

            if not futures:
                if remaining:
                    logger.error(
                        f"Job {job_id}: DAG executor stalled — unresolvable: {list(remaining)}"
                    )
                break

            # Block until at least one future completes (0% CPU)
            done_set, _ = concurrent.futures.wait(
                futures.values(), return_when=concurrent.futures.FIRST_COMPLETED
            )

            done_names = [n for n, f in futures.items() if f in done_set]
            for name in done_names:
                try:
                    futures[name].result()

                    # ── Dynamic helper protocol ───────────────────────────────
                    blocked_file = artifacts_dir / f"{name}_BLOCKED.json"
                    if blocked_file.exists():
                        signal = json.loads(blocked_file.read_text())
                        blocked_file.unlink()
                        reason = signal["reason"]

                        # Per-agent block limit
                        block_counts[name] = block_counts.get(name, 0) + 1
                        if block_counts[name] > MAX_BLOCKS_PER_AGENT:
                            logger.warning(
                                f"Job {job_id}: '{name}' exceeded block limit "
                                f"({MAX_BLOCKS_PER_AGENT}) — failing."
                            )
                            failed.add(name)
                            set_agent_state(job_id, name, AgentStatus.FAILED)
                            append_job_event(
                                job_id, "agent_failed", agent=name,
                                failure_class=FailureClass.BLOCK_LIMIT_EXCEEDED,
                                error=f"Exceeded block limit ({MAX_BLOCKS_PER_AGENT})",
                            )
                            del futures[name]
                            continue

                        # Duplicate-reason detection
                        prev_reasons = block_reasons.get(name, [])
                        is_duplicate = any(
                            reason.lower() in prev.lower()
                            or prev.lower() in reason.lower()
                            for prev in prev_reasons
                        )
                        if is_duplicate:
                            logger.warning(
                                f"Job {job_id}: '{name}' blocked for same reason again — failing."
                            )
                            failed.add(name)
                            set_agent_state(job_id, name, AgentStatus.FAILED)
                            append_job_event(
                                job_id, "agent_failed", agent=name,
                                failure_class=FailureClass.AGENT_BLOCKED,
                                error=f"Repeated block reason: {reason[:200]}",
                            )
                            del futures[name]
                            continue

                        block_reasons.setdefault(name, []).append(reason)

                        if dynamic_agent_count < MAX_DYNAMIC_AGENTS:
                            dynamic_agent_count += 1
                            try:
                                helper = _spawn_helper_agent(
                                    reason, agent_registry[name],
                                    artifacts_dir, dag_planner,
                                )
                                # Guard against name collision from repeated blocking
                                if helper.agent_name in agent_registry:
                                    helper = helper.model_copy(update={
                                        "agent_name": f"{helper.agent_name}_v{dynamic_agent_count}"
                                    })
                                original = agent_registry[name]
                                requeued = original.model_copy(update={
                                    "depends_on": original.depends_on + [helper.agent_name]
                                })
                                remaining[helper.agent_name] = helper
                                remaining[name] = requeued
                                agent_registry[helper.agent_name] = helper
                                agent_registry[name] = requeued
                                set_agent_state(job_id, name, AgentStatus.BLOCKED)
                                set_agent_state(job_id, helper.agent_name, AgentStatus.PENDING)
                                append_job_event(
                                    job_id, "helper_spawned",
                                    blocked_agent=name,
                                    helper=helper.agent_name,
                                    reason=reason,
                                    spawn_count=dynamic_agent_count,
                                )
                                logger.info(
                                    f"Job {job_id}: '{name}' blocked — spawned "
                                    f"'{helper.agent_name}' "
                                    f"({dynamic_agent_count}/{MAX_DYNAMIC_AGENTS})"
                                )
                            except Exception as spawn_err:
                                logger.error(
                                    f"Job {job_id}: Failed to spawn helper for "
                                    f"'{name}': {spawn_err} — marking failed."
                                )
                                failed.add(name)
                                set_agent_state(job_id, name, AgentStatus.FAILED)
                                append_job_event(
                                    job_id, "agent_failed", agent=name,
                                    failure_class=FailureClass.HELPER_SPAWN_FAILED,
                                    error=f"Helper spawn failed: {spawn_err}",
                                )
                        else:
                            logger.warning(
                                f"Job {job_id}: '{name}' blocked but "
                                f"MAX_DYNAMIC_AGENTS ({MAX_DYNAMIC_AGENTS}) reached — failing."
                            )
                            failed.add(name)
                            set_agent_state(job_id, name, AgentStatus.FAILED)
                            append_job_event(
                                job_id, "agent_failed", agent=name,
                                failure_class=FailureClass.AGENT_BLOCKED,
                                error="Blocked and max dynamic agents reached",
                            )
                    else:
                        completed.add(name)
                        set_agent_state(job_id, name, AgentStatus.COMPLETED)
                        append_job_event(
                            job_id, "agent_done", agent=name,
                            completed=len(completed), total=len(agent_registry),
                        )
                        logger.info(
                            f"Job {job_id}: '{name}' \u2713 — "
                            f"{len(completed)}/{len(agent_registry)} complete"
                        )

                except Exception as e:
                    fc = classify_failure(e)
                    failed.add(name)
                    set_agent_state(job_id, name, AgentStatus.FAILED)
                    append_job_event(job_id, "agent_failed", agent=name, failure_class=fc, error=str(e))
                    logger.error(f"Job {job_id}: '{name}' \u2717 [{fc.value}] — {e}")

                del futures[name]

    return len(completed), len(failed), len(agent_registry)
