import threading
import time
from typing import Any, Dict, Optional


_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def create_job(job_id: str, goal: str) -> Dict[str, Any]:
    """Register a new job and return its initial state dict."""
    job: Dict[str, Any] = {
        "job_id": job_id,
        "goal": goal,
        "status": "accepted",
        "current_step": "queued",
        "result": None,
        "error": None,
        "events": [],
        "agent_states": {},
    }
    with _jobs_lock:
        _jobs[job_id] = job
    return job


def update_job(job_id: str, **fields) -> None:
    """Thread-safe in-place job update."""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(fields)


def append_job_event(job_id: str, event_type: str, failure_class=None, **data) -> None:
    """Append a timestamped, optionally failure-typed event to the job log."""
    entry = {"t": int(time.time() * 1000), "type": event_type, **data}
    if failure_class is not None:
        entry["failure_class"] = failure_class
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["events"].append(entry)


def set_agent_state(job_id: str, agent_name: str, status) -> None:
    """Update the lifecycle state of a specific agent (thread-safe)."""
    val = status.value if hasattr(status, 'value') else str(status)
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["agent_states"][agent_name] = val


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Return the job dict (shared reference, not a copy) or None."""
    with _jobs_lock:
        return _jobs.get(job_id)


def list_jobs() -> list:
    """Return summary list of all jobs (id, goal, status, step, agent count)."""
    with _jobs_lock:
        return [
            {
                "job_id": j["job_id"],
                "goal": j["goal"],
                "status": j["status"],
                "current_step": j["current_step"],
                "agent_count": len(j.get("agent_states", {})),
                "event_count": len(j.get("events", [])),
            }
            for j in _jobs.values()
        ]
