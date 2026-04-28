"""Planner pre-validation — extracted from routes/generation.py."""

import pathlib

from hiveship.models import WorkflowPlan


def validate_plan_against_repo(
    plan: WorkflowPlan,
    job_workspace: pathlib.Path,
    seed_artifacts: list,
) -> list:
    """Return warning strings for impossible read_files / input_keys references.

    Called after planning but before DAG execution. If violations are found the
    pipeline re-prompts the planner with a corrective hint — eliminating the
    most common cause of block-spirals (agents expecting files that don't exist).
    """
    existing_files = {
        str(p.relative_to(job_workspace)).replace("\\", "/")
        for p in job_workspace.rglob("*")
        if p.is_file() and ".git" not in p.parts
    }
    warnings = []
    for agent in plan.agents:
        missing_files = [f for f in agent.read_files if f not in existing_files]
        if missing_files:
            warnings.append(
                f"Agent '{agent.agent_name}' requests read_files that do not "
                f"exist in the repo: {missing_files}"
            )
        # Root agents (no deps) may only reference seed artifacts
        if not agent.depends_on:
            bad_keys = [k for k in agent.input_keys if k not in seed_artifacts]
            if bad_keys:
                warnings.append(
                    f"Agent '{agent.agent_name}' references input_keys not yet "
                    f"available as seed artifacts: {bad_keys}"
                )
    return warnings
