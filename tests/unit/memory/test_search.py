"""Tests for hiveship.memory.search — session search with smart windowing."""

import pytest

from hiveship.memory.history import JobHistoryDB, JobRecord, MessageRecord
from hiveship.memory.search import search_past_jobs, format_search_results_for_prompt, _extract_window


@pytest.fixture
def populated_db(tmp_path):
    db = JobHistoryDB(db_path=tmp_path / "test.db")
    # Create two jobs with different topics
    db.record_job(JobRecord(
        job_id="j1", repo_owner="acme", repo_name="app", goal="Add REST API",
    ))
    db.record_job(JobRecord(
        job_id="j2", repo_owner="acme", repo_name="app", goal="Fix database migrations",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="agent", agent_name="coder",
        prompt_summary="Build API",
        response_summary="Implemented REST API with Express.js and JWT authentication middleware",
    ))
    db.record_message(MessageRecord(
        job_id="j1", role="reviewer", agent_name="reviewer",
        prompt_summary="Review API",
        response_summary="REST API looks good but needs rate limiting",
    ))
    db.record_message(MessageRecord(
        job_id="j2", role="agent", agent_name="migrator",
        prompt_summary="Fix migrations",
        response_summary="Fixed database migration script for PostgreSQL schema changes",
    ))
    yield db
    db.close()


def test_search_finds_relevant_jobs(populated_db):
    """Search returns jobs matching the query."""
    results = search_past_jobs(populated_db, "REST API", repo_owner="acme", repo_name="app")
    assert len(results) >= 1
    assert any(r.job_id == "j1" for r in results)


def test_search_groups_by_job(populated_db):
    """Multiple messages from same job are grouped."""
    results = search_past_jobs(populated_db, "REST", top_n=5)
    j1_results = [r for r in results if r.job_id == "j1"]
    assert len(j1_results) <= 1  # Should be grouped, not duplicated


def test_search_empty_query(populated_db):
    """Empty query returns nothing."""
    results = search_past_jobs(populated_db, "")
    assert results == []


def test_search_no_results(populated_db):
    """Non-matching query returns empty list."""
    results = search_past_jobs(populated_db, "kubernetes deployment yaml")
    assert results == []


def test_extract_window_centers_on_match():
    """Window extraction centers on the match with 25/75 split."""
    text = "A" * 100 + "TARGET" + "B" * 100
    snippet = _extract_window(text, "TARGET", 50)
    assert "TARGET" in snippet


def test_extract_window_no_match():
    """When no exact match, returns start of text."""
    text = "Some long text about nothing relevant"
    snippet = _extract_window(text, "nonexistent", 20)
    assert snippet.startswith("Some")


def test_format_search_results_empty():
    """Empty results produce empty string."""
    assert format_search_results_for_prompt([]) == ""


def test_format_search_results_structure(populated_db):
    """Formatted output contains job goals and snippets."""
    results = search_past_jobs(populated_db, "REST API")
    output = format_search_results_for_prompt(results)
    if results:
        assert "Past Related Work" in output
        assert "REST API" in output
