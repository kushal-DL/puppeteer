"""Unit tests for job store."""

from hiveship.engine.job_store import (
    append_job_event,
    create_job,
    get_job,
    list_jobs,
    set_agent_state,
    update_job,
)
from hiveship.models import AgentStatus


def test_create_and_get_job():
    job = create_job("test-001", "build something")
    assert job["status"] == "accepted"
    retrieved = get_job("test-001")
    assert retrieved is not None
    assert retrieved["goal"] == "build something"


def test_update_job():
    create_job("test-002", "another goal")
    update_job("test-002", status="running", current_step="planning")
    job = get_job("test-002")
    assert job["status"] == "running"
    assert job["current_step"] == "planning"


def test_append_job_event():
    create_job("test-003", "event test")
    append_job_event("test-003", "agent_started", agent="agent_a")
    job = get_job("test-003")
    assert len(job["events"]) == 1
    assert job["events"][0]["type"] == "agent_started"


def test_set_agent_state():
    create_job("test-004", "state test")
    set_agent_state("test-004", "agent_x", AgentStatus.RUNNING)
    job = get_job("test-004")
    assert job["agent_states"]["agent_x"] == "running"
