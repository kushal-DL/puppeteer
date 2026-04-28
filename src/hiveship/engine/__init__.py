"""Engine sub-package — DAG execution, job tracking, and planning.

Usage:
    from hiveship.engine import execute_dag
    from hiveship.engine.job_store import create_job, update_job
    from hiveship.engine.planner import validate_plan_against_repo
"""

from hiveship.engine.dag import execute_dag

__all__ = ["execute_dag"]
