"""Tests for hiveship.memory.history — JobHistoryDB CRUD, FTS5, WAL."""

import pytest

from hiveship.memory.history import JobHistoryDB, JobRecord, MessageRecord


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_history.db"
    d = JobHistoryDB(db_path=db_path)
    yield d
    d.close()


def test_record_and_get_job(db):
    """Basic job insert and retrieve."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Add feature",
    ))
    job = db.get_job("j1")
    assert job is not None
    assert job["goal"] == "Add feature"
    assert job["repo_owner"] == "acme"


def test_upsert_job(db):
    """Recording same job_id updates instead of failing."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Add feature",
    ))
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Add feature",
        status="complete", outcome="PR created",
    ))
    job = db.get_job("j1")
    assert job["status"] == "complete"
    assert job["outcome"] == "PR created"


def test_record_and_get_messages(db):
    """Message insert and retrieve by job_id."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Test",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="agent", agent_name="coder",
        prompt_summary="Write code for...",
        response_summary="Here is the implementation of the REST API endpoint...",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="reviewer", agent_name="reviewer",
        prompt_summary="Review...",
        response_summary="Code looks good, approved.",
    ))
    msgs = db.get_job_messages("j1")
    assert len(msgs) == 2
    assert msgs[0]["agent_name"] == "coder"


def test_fts5_search(db):
    """Full-text search finds matching messages."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="REST API",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="agent", agent_name="coder",
        prompt_summary="Create endpoint",
        response_summary="Implemented REST API with authentication middleware",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="agent", agent_name="tester",
        prompt_summary="Write tests",
        response_summary="Added unit tests for the database layer",
    ))
    results = db.search_messages("authentication")
    assert len(results) >= 1
    assert any("authentication" in r.get("response_summary", "").lower() for r in results)


def test_search_filters_by_repo(db):
    """Search can be filtered by repo_owner + repo_name."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="API",
    ))
    db.record_job(JobRecord(
        job_id="j2", repo_owner="other", repo_name="lib", goal="API",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="agent", agent_name="a1",
        prompt_summary="Create API",
        response_summary="REST API endpoint created",
    ))
    db.record_message(MessageRecord(
        job_id="j2", role="agent", agent_name="a2",
        prompt_summary="Create lib",
        response_summary="REST API library function added",
    ))
    results = db.search_messages("REST API", repo_owner="acme", repo_name="app")
    # FTS5 match may return both since both contain "REST API"
    # At minimum, j1 should be present
    job_ids = {r["job_id"] for r in results}
    assert "j1" in job_ids
    # j2 should NOT be present (different repo)
    assert "j2" not in job_ids


def test_update_job_status(db):
    """update_job_status sets final fields."""
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Test",
    ))
    db.update_job_status("j1", status="complete", pr_url="https://github.com/pr/1")
    job = db.get_job("j1")
    assert job["status"] == "complete"
    assert job["pr_url"] == "https://github.com/pr/1"
    assert job["ended_at"] is not None


def test_get_recent_jobs(db):
    """get_recent_jobs returns jobs in reverse chronological order."""
    for i in range(5):
        db.record_job(JobRecord(
            job_id=f"j{i}", repo_owner="acme", repo_name="app",
            goal=f"Goal {i}", started_at=float(i),
        ))
    recent = db.get_recent_jobs(repo_owner="acme", repo_name="app", limit=3)
    assert len(recent) == 3
    assert recent[0]["job_id"] == "j4"  # Most recent first


def test_nonexistent_job_returns_none(db):
    """get_job returns None for unknown job_id."""
    assert db.get_job("nonexistent") is None
