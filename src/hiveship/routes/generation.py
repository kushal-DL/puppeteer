import asyncio
import json
import logging
import pathlib
import shutil
import subprocess
import uuid

from fastapi import BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from hiveship.config import (
    ARTIFACT_CHAR_LIMIT, BASE_BRANCH, BASE_WORKSPACE,
    BOT_MENTION, DEFAULT_LLM_PROVIDER, DEFAULT_REPO_NAME,
    DEFAULT_REPO_OWNER, MAX_REVIEW_CYCLES,
)
from hiveship.engine import execute_dag
from hiveship.engine.job_store import create_job, update_job
from hiveship.engine.planner import validate_plan_against_repo
from hiveship.git import github_api_request, run_git
from hiveship.llm import create_models, sync_generate_and_parse, sync_generate_with_retry, get_total_cost, reset_usage
from hiveship.logging import set_session_context
from hiveship.memory.manager import MemoryManager
from hiveship.memory.history import JobHistoryDB, JobRecord, MessageRecord
from hiveship.memory.search import search_past_jobs, format_search_results_for_prompt
from hiveship.memory.skills import (
    SkillStore, build_skill_index_for_prompt, build_skill_content_for_agent,
    SKILL_EXTRACTION_PROMPT,
)
from hiveship.models import DeliveryPlan, FailureClass, ReviewResult, WorkflowPlan, classify_failure
from hiveship.workspace import (
    get_repo_summary, read_artifact_context,
    sanitize_branch_name, validate_cross_references, validate_files, write_files,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── HTTP endpoint ─────────────────────────────────────────────────────────────

@router.post("/teams-trigger")
async def handle_autonomous_flow(
    request: Request,
    background_tasks: BackgroundTasks,
):
    data = await request.json()
    user_goal    = data.get("text", "").strip()[:2000]
    job_id       = uuid.uuid4().hex[:12]
    llm_provider = data.get("llm_provider", DEFAULT_LLM_PROVIDER)
    if llm_provider not in ("gemini", "ollama"):
        raise HTTPException(status_code=400, detail="llm_provider must be 'gemini' or 'ollama'")
    review_cycles = data.get("review_cycles", MAX_REVIEW_CYCLES)
    if not isinstance(review_cycles, int) or not (0 <= review_cycles <= 5):
        raise HTTPException(status_code=400, detail="review_cycles must be an integer 0-5")
    ollama_model    = data.get("ollama_model", "").strip()[:80]
    ollama_base_url = data.get("ollama_base_url", "").strip()[:200]

    # Per-request repo targeting — falls back to .env defaults
    repo_owner = data.get("repo_owner", "").strip()[:80] or DEFAULT_REPO_OWNER
    repo_name  = data.get("repo_name", "").strip()[:80] or DEFAULT_REPO_NAME
    if not repo_owner or not repo_name:
        raise HTTPException(
            status_code=400,
            detail="repo_owner and repo_name are required (set in request body or REPO_OWNER/REPO_NAME env vars)",
        )

    create_job(job_id, user_goal)
    background_tasks.add_task(
        _run_generation_pipeline_async, job_id, user_goal,
        llm_provider, review_cycles, ollama_model, ollama_base_url,
        repo_owner, repo_name,
    )
    return JSONResponse(
        status_code=202,
        content={
            "type": "accepted",
            "job_id": job_id,
            "poll_url": f"/status/{job_id}",
            "text": f"Job {job_id} accepted. Poll /status/{job_id} for progress.",
        },
    )


async def _run_generation_pipeline_async(
    job_id, user_goal, llm_provider, review_cycles, ollama_model, ollama_base_url,
    repo_owner, repo_name,
):
    """Offload entire pipeline to a thread — never blocks the event loop."""
    await asyncio.to_thread(
        _sync_generation_pipeline, job_id, user_goal,
        llm_provider, review_cycles, ollama_model, ollama_base_url,
        repo_owner, repo_name,
    )


# ── Synchronous pipeline ──────────────────────────────────────────────────────

def _sync_generation_pipeline(
    job_id: str,
    user_goal: str,
    llm_provider: str = DEFAULT_LLM_PROVIDER,
    review_cycles: int = MAX_REVIEW_CYCLES,
    ollama_model: str = "",
    ollama_base_url: str = "",
    repo_owner: str = "",
    repo_name: str = "",
):
    """Synchronous pipeline — runs entirely off the FastAPI event loop."""
    job_workspace = BASE_WORKSPACE / f"run-{job_id}"
    artifacts_dir = BASE_WORKSPACE / f"artifacts-{job_id}"

    # Initialize history DB and usage tracking
    history_db = None
    try:
        history_db = JobHistoryDB()
    except Exception as e:
        logger.warning(f"Job {job_id}: History DB init failed (non-fatal): {e}")

    try:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        set_session_context(job_id)
        reset_usage()

        job_planner, job_executor, job_reviewer, _ = create_models(
            llm_provider, ollama_model, ollama_base_url,
        )

        update_job(job_id, status="running", current_step="cloning")

        repo_url = f"https://github.com/{repo_owner}/{repo_name}.git"
        run_git("clone", "--branch", BASE_BRANCH, "--depth", "1", repo_url, str(job_workspace))
        run_git("config", "user.email", "orchestrator@automated.dev",
                cwd=str(job_workspace), timeout=10)
        run_git("config", "user.name", "SDLC Orchestrator",
                cwd=str(job_workspace), timeout=10)

        # Record job in history
        if history_db:
            history_db.record_job(JobRecord(
                job_id=job_id, repo_owner=repo_owner, repo_name=repo_name,
                goal=user_goal,
            ))

        repo_context = get_repo_summary(job_workspace)
        (artifacts_dir / "initial_goal.txt").write_text(user_goal, encoding="utf-8")
        (artifacts_dir / "repo_context.txt").write_text(repo_context, encoding="utf-8")

        # ── Memory: load frozen snapshot ──────────────────────────────────────
        memory_mgr = MemoryManager(job_workspace)
        memory_mgr.prefetch()
        memory_block = memory_mgr.build_memory_context_block()

        # ── Skills: discover available procedures ─────────────────────────────
        skill_store = SkillStore(job_workspace)
        skills = skill_store.discover()
        skill_index = build_skill_index_for_prompt(skills)

        # ── History: search past jobs for relevant context ────────────────────
        history_block = ""
        if history_db:
            try:
                past_jobs = search_past_jobs(
                    history_db, user_goal[:200],
                    repo_owner=repo_owner, repo_name=repo_name, top_n=3,
                )
                history_block = format_search_results_for_prompt(past_jobs)
            except Exception as e:
                logger.warning(f"Job {job_id}: History search failed (non-fatal): {e}")

        update_job(job_id, current_step="planning")

        meta_prompt = (
            f"Goal: '{user_goal}'.\n"
            f"Repo Context:\n{repo_context}\n"
        )
        if memory_block:
            meta_prompt += f"\n{memory_block}\n"
        if skill_index:
            meta_prompt += f"\n{skill_index}\n"
        if history_block:
            meta_prompt += f"\n{history_block}\n"
        meta_prompt += (
            f"\nReturn a JSON WorkflowPlan with 'team_name' (string) and 'agents' "
            f"(array of objects, each with: agent_name, role_description, depends_on, "
            f"input_keys, read_files, output_format, optionally system_instruction). Max 8 agents.\n"
            f"Rules:\n"
            f"- First agent's input_keys must include 'initial_goal' and 'repo_context'.\n"
            f"- Subsequent agents reference prior agents by exact agent_name.\n"
            f"- agent_name must be a short identifier with no spaces.\n"
            f"- Use read_files ONLY for files that actually appear in the "
            f"repo tree shown above. Do NOT reference files that do not exist.\n"
            f"- Optionally set system_instruction to give each agent a specific persona.\n"
            f"- Set depends_on to list agent names that must complete first.\n"
            f"- Ensure there are no dependency cycles.\n"
            f"CRITICAL CONSTRAINTS:\n"
            f"- The final deliverable is a set of self-contained FILES committed to a git repo.\n"
            f"- ALL code must live inside the delivered files — do NOT plan for external "
            f"packages, modules, or APIs that don't already exist in the repo or on PyPI.\n"
            f"- If the goal requires a bot/AI/algorithm, the implementation MUST be "
            f"inline in the delivered source files, not in a separate undelivered module.\n"
            f"- Each agent's output is a TEXT ARTIFACT. The final 'delivery plan' agent "
            f"will synthesize all artifacts into actual source files — plan accordingly."
        )
        plan = sync_generate_and_parse(
            job_planner, meta_prompt, WorkflowPlan,
            {},
        )

        # ── Planner pre-validation ────────────────────────────────────────────
        seed_artifacts = ["initial_goal", "repo_context"]
        warnings = validate_plan_against_repo(plan, job_workspace, seed_artifacts)
        if warnings:
            warning_text = "\n".join(f"- {w}" for w in warnings)
            logger.warning(f"Job {job_id}: Plan pre-validation issues:\n{warning_text}")
            corrective_prompt = (
                meta_prompt
                + f"\n\nWARNING — your previous plan had these issues:\n{warning_text}\n"
                + "Fix all of them in the new plan."
            )
            plan = sync_generate_and_parse(
                job_planner, corrective_prompt, WorkflowPlan,
                {},
            )

        # ── DAG execution ─────────────────────────────────────────────────────
        # Build skill content for agents (full SKILL.md bodies)
        skill_names = [s.name for s in skills]
        dag_skill_content = build_skill_content_for_agent(skill_names, skill_store)

        dag_ok, dag_fail, dag_total = execute_dag(
            plan, artifacts_dir, job_workspace, job_id,
            dag_executor=job_executor, dag_planner=job_planner,
            llm_provider=llm_provider,
            ollama_model=ollama_model, ollama_base_url=ollama_base_url,
            memory_block=memory_block, skill_content=dag_skill_content,
        )

        if dag_total > 0 and dag_ok < dag_total * 0.5:
            update_job(
                job_id, status="failed", current_step="dag_incomplete",
                failure_class=FailureClass.DAG_STALLED,
                error=(
                    f"DAG too degraded: only {dag_ok}/{dag_total} agents "
                    f"completed ({dag_fail} failed). Aborting."
                ),
            )
            return

        # ── Delivery plan ─────────────────────────────────────────────────────
        update_job(job_id, current_step="generating delivery plan")
        all_keys = [p.stem for p in artifacts_dir.glob("*.txt")]
        artifact_context = read_artifact_context(all_keys, artifacts_dir)
        delivery = sync_generate_and_parse(
            job_executor,
            f"TASK: Synthesize all agent artifacts into production-ready, self-contained files.\n\n"
            f"Artifacts from agents:\n{json.dumps(artifact_context)}\n\n"
            f"Return a JSON DeliveryPlan with 'files' (array of objects with 'path' and 'content'), "
            f"'commit_message' (string), and 'pr_title' (string).\n\n"
            f"RULES:\n"
            f"- Merge ALL code from the artifacts into complete, runnable source files.\n"
            f"- Every file must be self-contained: all imports must resolve to the standard "
            f"library, a pip package from requirements.txt, or another file in this delivery.\n"
            f"- Do NOT reference external modules, packages, or repos that are not delivered "
            f"or available on PyPI.\n"
            f"- If multiple artifacts describe the same functionality (e.g. a bot algorithm), "
            f"merge them into a single coherent implementation inside the main file or a "
            f"co-delivered module.\n"
            f"- Include a requirements.txt ONLY with real pip-installable packages.\n"
            f"- Include complete, actually runnable code — not stubs or pseudocode.\n"
            f"CROSS-FILE REFERENCES (CRITICAL):\n"
            f"- Before writing any import statement like 'from X import Y', verify that "
            f"module X exists as another file in your delivery (e.g. X.py).\n"
            f"- If you define a function/class in one file and import it in another, "
            f"the EXACT function/class name must match between the files.\n"
            f"- Prefer fewer, larger files over many small files to reduce cross-file risk.\n"
            f"- If in doubt, put everything in a single file.",
            DeliveryPlan,
            {},
            max_retries=4,
        )

        # ── Structural pre-review: catch broken cross-references early ────────
        xref_issues = validate_cross_references(delivery.files)
        if xref_issues:
            xref_text = "\n".join(f"- {i}" for i in xref_issues)
            logger.warning(f"Job {job_id}: Cross-reference issues:\n{xref_text}")
            update_job(job_id, current_step="fixing cross-references")
            file_manifest = [f.path for f in delivery.files]
            delivery = sync_generate_and_parse(
                job_executor,
                f"The delivery has BROKEN CROSS-FILE REFERENCES:\n{xref_text}\n\n"
                f"Current files in delivery: {file_manifest}\n"
                f"Current file contents:\n"
                f"{json.dumps([{'path': f.path, 'content': f.content[:ARTIFACT_CHAR_LIMIT]} for f in delivery.files])}\n\n"
                f"FIX RULES:\n"
                f"- For each broken import, either add the missing .py file to the delivery "
                f"OR move the imported code inline into the file that needs it.\n"
                f"- Verify EVERY 'from X import Y' has a matching file X.py with Y defined.\n"
                f"- Output the COMPLETE fixed delivery (files array, commit_message, pr_title).",
                DeliveryPlan,
                {},
                max_retries=4,
            )

        # ── Review / fix loop ─────────────────────────────────────────────────
        update_job(job_id, current_step="self-review")

        for cycle in range(review_cycles + 1):
            review_input = {
                "goal": user_goal,
                "files": [
                    {"path": f.path, "content": f.content[:ARTIFACT_CHAR_LIMIT]}
                    for f in delivery.files
                ],
                "commit_message": delivery.commit_message,
            }
            review = sync_generate_and_parse(
                job_reviewer,
                f"Review these FILES against the goal '{user_goal}':\n"
                f"{json.dumps(review_input, indent=2)}\n"
                f"Check for CONCRETE, FIXABLE issues only:\n"
                f"- Does the code actually run? Are there syntax errors or missing imports?\n"
                f"- Does it meet the stated goal?\n"
                f"- Are there real security vulnerabilities (SQL injection, path traversal, etc.)?\n"
                f"- Do NOT reject for vague/theoretical concerns like 'potential security risk'.\n"
                f"- Do NOT reject for missing features the user didn't ask for.\n"
                f"- Do NOT reject because a module is implemented inline instead of as a package.\n"
                f"- Each issue in your list must describe a SPECIFIC problem and HOW to fix it.\n"
                f"Return a JSON object with 'approved' (boolean) and 'issues' (array of strings).",
                ReviewResult,
                {},
            )

            if review.approved:
                break

            if cycle == review_cycles:
                update_job(
                    job_id, status="failed", current_step="review_rejected",
                    failure_class=FailureClass.REVIEW_REJECTED,
                    error=(
                        f"Team '{plan.team_name}' failed review after "
                        f"{review_cycles + 1} attempts.\n"
                        f"Issues:\n- " + "\n- ".join(review.issues)
                    ),
                )
                return

            update_job(job_id, current_step=f"review fix (cycle {cycle + 1})")
            rejected_files = [
                {"path": f.path, "content": f.content[:ARTIFACT_CHAR_LIMIT]}
                for f in delivery.files
            ]
            file_manifest = [f.path for f in delivery.files]
            delivery = sync_generate_and_parse(
                job_executor,
                f"A code reviewer REJECTED the delivery with these issues:\n"
                f"{json.dumps(review.issues)}\n\n"
                f"Files in current delivery: {file_manifest}\n"
                f"Current files (fix these):\n{json.dumps(rejected_files)}\n\n"
                f"RULES FOR FIXING:\n"
                f"- Fix EVERY issue listed above.\n"
                f"- Keep all code SELF-CONTAINED — all imports must resolve to stdlib, "
                f"pip packages, or other files in this delivery.\n"
                f"- If a missing module is referenced, implement it INLINE in the relevant file "
                f"or as a co-delivered .py file.\n"
                f"- For EVERY 'from X import Y' in any file, verify X.py exists in the delivery "
                f"and Y is actually defined in X.py.\n"
                f"- Output COMPLETE file contents, not patches or diffs.\n"
                f"- Do NOT introduce new external dependencies that don't exist on PyPI.\n\n"
                f"Return the complete fixed DeliveryPlan with 'files', 'commit_message', and 'pr_title'.",
                DeliveryPlan,
                {},
                max_retries=4,
            )

        # ── PR workflow ───────────────────────────────────────────────────────
        if not delivery.files:
            update_job(
                job_id, status="complete", current_step="done",
                result=f"Team '{plan.team_name}' analyzed the goal but produced no file changes.",
            )
            return

        update_job(job_id, current_step="pushing to GitHub")
        validate_files(delivery.files, job_workspace)

        branch_name = f"auto/{sanitize_branch_name(plan.team_name)}/{job_id}"
        run_git("checkout", "-b", branch_name, cwd=str(job_workspace))
        write_files(delivery.files, job_workspace)
        run_git("add", ".", cwd=str(job_workspace), timeout=30)

        diff = run_git("diff", "--cached", "--stat", cwd=str(job_workspace), timeout=30)
        if not diff.stdout.strip():
            update_job(
                job_id, status="complete", current_step="done",
                result=f"Team '{plan.team_name}' ran but produced no net changes.",
            )
            return

        run_git("commit", "-m", delivery.commit_message, cwd=str(job_workspace), timeout=30)
        run_git("push", "origin", branch_name, cwd=str(job_workspace), timeout=120)

        pr_data = github_api_request(
            "POST",
            f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls",
            {
                "title": delivery.pr_title,
                "head": branch_name,
                "base": BASE_BRANCH,
                "body": (
                    f"**Autonomous PR** generated by Team `{plan.team_name}`.\n\n"
                    f"**Goal:** {user_goal}\n\n"
                    f"**Files changed:** {len(delivery.files)}\n\n"
                    f"To request changes, comment on this PR mentioning `{BOT_MENTION}`."
                ),
            },
        )

        # ── Post-PR learning: extract memory & skills ─────────────────────────
        file_paths = [f.path for f in delivery.files]
        total_cost = get_total_cost()

        # Memory extraction — discover repo conventions from this run
        try:
            extraction_prompt = memory_mgr.build_extraction_prompt(user_goal, file_paths)
            raw_entries = sync_generate_with_retry(job_executor, extraction_prompt)
            # Parse JSON array of strings
            import json as _json
            entries = _json.loads(raw_entries)
            if isinstance(entries, list):
                errs = memory_mgr.apply_extracted_entries(
                    [str(e) for e in entries if isinstance(e, str)]
                )
                if errs:
                    logger.info(f"Job {job_id}: Memory extraction skipped {len(errs)} entries")
        except Exception as e:
            logger.info(f"Job {job_id}: Memory extraction failed (non-fatal): {e}")

        # Skill extraction — create procedure from complex jobs
        if len(plan.agents) >= 4:
            try:
                agent_summary = "\n".join(
                    f"- {a.agent_name}: {a.role_description}" for a in plan.agents
                )
                skill_prompt = SKILL_EXTRACTION_PROMPT.format(
                    goal=user_goal,
                    agent_count=len(plan.agents),
                    agent_summary=agent_summary,
                    file_list="\n".join(f"- {p}" for p in file_paths),
                )
                skill_content = sync_generate_with_retry(job_executor, skill_prompt)
                # Extract skill name from frontmatter
                import re as _re
                name_match = _re.search(r"name:\s*(.+)", skill_content)
                skill_name = name_match.group(1).strip() if name_match else f"auto-{job_id}"
                skill_store.create(skill_name, skill_content)
            except Exception as e:
                logger.info(f"Job {job_id}: Skill extraction failed (non-fatal): {e}")

        # Update history DB with final status
        if history_db:
            try:
                history_db.update_job_status(
                    job_id, status="complete",
                    outcome=f"PR created: {pr_data.get('html_url')}",
                    pr_url=pr_data.get("html_url", ""),
                    branch=branch_name,
                    total_cost_usd=total_cost,
                )
            except Exception as e:
                logger.warning(f"Job {job_id}: History update failed (non-fatal): {e}")

        update_job(
            job_id, status="complete", current_step="done",
            pr_number=pr_data.get("number"),
            pr_url=pr_data.get("html_url"),
            pr_branch=branch_name,
            result=(
                f"\u2705 Team '{plan.team_name}' passed review and deployed.\n"
                f"PR: {pr_data.get('html_url')}\n"
                f"Cost: ${total_cost:.6f}"
            ),
        )

    except Exception as e:
        fc = classify_failure(e)
        logger.exception(f"Job {job_id} failed [{fc.value}]")
        detail = str(e)
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            detail = f"{detail} | stderr: {e.stderr.strip()[:500]}"
        update_job(
            job_id, status="failed", current_step="error",
            failure_class=fc,
            error=f"Orchestration failed [{fc.value}]: {type(e).__name__}: {detail}",
        )
        # Record failure in history
        if history_db:
            try:
                history_db.update_job_status(
                    job_id, status="failed",
                    error=f"[{fc.value}] {detail[:500]}",
                    total_cost_usd=get_total_cost(),
                )
            except Exception:
                pass
    finally:
        if history_db:
            try:
                history_db.close()
            except Exception:
                pass
        shutil.rmtree(job_workspace, ignore_errors=True)
        shutil.rmtree(artifacts_dir, ignore_errors=True)
