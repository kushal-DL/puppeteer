"""Job history persistence — SQLite WAL with FTS5 full-text search.

Stores job metadata and per-agent message summaries for cross-session recall.
Inspired by hermes-agent's session chaining pattern.
"""

import json
import logging
import os
import pathlib
import random
import sqlite3
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = pathlib.Path(
    os.environ.get("HIVESHIP_HISTORY_DB", "")
    or str(pathlib.Path.home() / ".hiveship" / "history.db")
)

# Retry config for SQLite lock contention (decorrelated jitter)
_MAX_RETRIES = 15
_BASE_DELAY_MS = 20
_MAX_DELAY_MS = 150

# WAL checkpoint interval
_CHECKPOINT_INTERVAL = 50


@dataclass
class JobRecord:
    job_id: str
    repo_owner: str
    repo_name: str
    goal: str
    status: str = "running"
    plan_json: str = ""
    outcome: str = ""
    error: str = ""
    branch: str = ""
    pr_url: str = ""
    total_cost_usd: float = 0.0
    started_at: float = field(default_factory=time.time)
    ended_at: Optional[float] = None


@dataclass
class MessageRecord:
    job_id: str
    role: str  # planner, agent, reviewer, helper
    agent_name: str
    prompt_summary: str
    response_summary: str
    tokens_in: int = 0
    tokens_out: int = 0
    timestamp: float = field(default_factory=time.time)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    plan_json TEXT DEFAULT '',
    outcome TEXT DEFAULT '',
    error TEXT DEFAULT '',
    branch TEXT DEFAULT '',
    pr_url TEXT DEFAULT '',
    total_cost_usd REAL DEFAULT 0.0,
    started_at REAL NOT NULL,
    ended_at REAL
);

CREATE TABLE IF NOT EXISTS job_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(job_id),
    role TEXT NOT NULL,
    agent_name TEXT NOT NULL DEFAULT '',
    prompt_summary TEXT NOT NULL DEFAULT '',
    response_summary TEXT NOT NULL DEFAULT '',
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    timestamp REAL NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_job ON job_messages(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_repo ON jobs(repo_owner, repo_name);
"""

_FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS job_messages_fts
USING fts5(response_summary, content=job_messages, content_rowid=id);
"""

_FTS_TRIGGER_SQL = """
CREATE TRIGGER IF NOT EXISTS job_messages_ai AFTER INSERT ON job_messages BEGIN
    INSERT INTO job_messages_fts(rowid, response_summary)
    VALUES (new.id, new.response_summary);
END;
"""


class JobHistoryDB:
    """SQLite-backed job history with FTS5 search.

    Uses WAL mode for concurrent reads and decorrelated jitter retry on
    lock contention (hermes pattern).
    """

    def __init__(self, db_path: Optional[pathlib.Path] = None):
        self._db_path = db_path or _DEFAULT_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_count = 0
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript(_SCHEMA_SQL)
        # FTS5 in a separate step — may fail on minimal SQLite builds
        try:
            conn.executescript(_FTS_SQL)
            conn.executescript(_FTS_TRIGGER_SQL)
            self._fts_available = True
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 not available, search disabled: {e}")
            self._fts_available = False
        conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(
                str(self._db_path),
                timeout=10,
                check_same_thread=False,
            )
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def _execute_with_retry(self, sql: str, params=(), commit=True):
        """Execute with decorrelated jitter retry on lock contention."""
        conn = self._get_conn()
        delay_ms = _BASE_DELAY_MS
        for attempt in range(_MAX_RETRIES):
            try:
                cursor = conn.execute(sql, params)
                if commit:
                    conn.commit()
                    self._write_count += 1
                    if self._write_count % _CHECKPOINT_INTERVAL == 0:
                        try:
                            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
                        except sqlite3.OperationalError:
                            pass
                return cursor
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < _MAX_RETRIES - 1:
                    jitter = random.randint(0, delay_ms)
                    time.sleep(jitter / 1000.0)
                    delay_ms = min(_MAX_DELAY_MS, delay_ms * 2)
                    continue
                raise
        raise sqlite3.OperationalError("Database locked after max retries")

    # ── Write operations ──────────────────────────────────────────────────────

    def record_job(self, rec: JobRecord) -> None:
        """Insert or update a job record."""
        self._execute_with_retry(
            """INSERT INTO jobs
               (job_id, repo_owner, repo_name, goal, status, plan_json,
                outcome, error, branch, pr_url, total_cost_usd, started_at, ended_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(job_id) DO UPDATE SET
                   status=excluded.status, plan_json=excluded.plan_json,
                   outcome=excluded.outcome, error=excluded.error,
                   branch=excluded.branch, pr_url=excluded.pr_url,
                   total_cost_usd=excluded.total_cost_usd, ended_at=excluded.ended_at
            """,
            (
                rec.job_id, rec.repo_owner, rec.repo_name, rec.goal,
                rec.status, rec.plan_json, rec.outcome, rec.error,
                rec.branch, rec.pr_url, rec.total_cost_usd,
                rec.started_at, rec.ended_at,
            ),
        )

    def record_message(self, msg: MessageRecord) -> None:
        """Insert a message record (agent prompt/response summary)."""
        self._execute_with_retry(
            """INSERT INTO job_messages
               (job_id, role, agent_name, prompt_summary, response_summary,
                tokens_in, tokens_out, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                msg.job_id, msg.role, msg.agent_name,
                msg.prompt_summary, msg.response_summary,
                msg.tokens_in, msg.tokens_out, msg.timestamp,
            ),
        )

    def update_job_status(
        self,
        job_id: str,
        status: str,
        outcome: str = "",
        error: str = "",
        pr_url: str = "",
        branch: str = "",
        total_cost_usd: float = 0.0,
    ) -> None:
        """Update a job's final status."""
        self._execute_with_retry(
            """UPDATE jobs SET status=?, outcome=?, error=?, pr_url=?,
               branch=?, total_cost_usd=?, ended_at=?
               WHERE job_id=?""",
            (status, outcome, error, pr_url, branch, total_cost_usd, time.time(), job_id),
        )

    # ── Read operations ───────────────────────────────────────────────────────

    def get_job(self, job_id: str) -> Optional[dict]:
        """Retrieve a single job by ID."""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        return dict(row) if row else None

    def get_job_messages(self, job_id: str) -> List[dict]:
        """Retrieve all messages for a job."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM job_messages WHERE job_id=? ORDER BY timestamp",
            (job_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_messages(
        self,
        query: str,
        repo_owner: str = "",
        repo_name: str = "",
        limit: int = 20,
    ) -> List[dict]:
        """Full-text search across job messages.

        Returns message rows with their job metadata, ranked by relevance.
        """
        if not self._fts_available:
            return self._fallback_search(query, repo_owner, repo_name, limit)

        conn = self._get_conn()
        # FTS5 query — escape special chars
        safe_query = query.replace('"', '""')
        sql = """
            SELECT m.*, j.goal, j.status AS job_status, j.repo_owner, j.repo_name
            FROM job_messages_fts fts
            JOIN job_messages m ON m.id = fts.rowid
            JOIN jobs j ON j.job_id = m.job_id
            WHERE job_messages_fts MATCH ?
        """
        params: list = [f'"{safe_query}"']
        if repo_owner and repo_name:
            sql += " AND j.repo_owner = ? AND j.repo_name = ?"
            params.extend([repo_owner, repo_name])
        sql += " ORDER BY rank LIMIT ?"
        params.append(limit)
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.OperationalError:
            return self._fallback_search(query, repo_owner, repo_name, limit)

    def _fallback_search(
        self, query: str, repo_owner: str, repo_name: str, limit: int,
    ) -> List[dict]:
        """LIKE-based fallback when FTS5 is unavailable."""
        conn = self._get_conn()
        sql = """
            SELECT m.*, j.goal, j.status AS job_status, j.repo_owner, j.repo_name
            FROM job_messages m
            JOIN jobs j ON j.job_id = m.job_id
            WHERE m.response_summary LIKE ?
        """
        params: list = [f"%{query}%"]
        if repo_owner and repo_name:
            sql += " AND j.repo_owner = ? AND j.repo_name = ?"
            params.extend([repo_owner, repo_name])
        sql += " ORDER BY m.timestamp DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def get_recent_jobs(
        self,
        repo_owner: str = "",
        repo_name: str = "",
        limit: int = 10,
    ) -> List[dict]:
        """Get recent jobs, optionally filtered by repo."""
        conn = self._get_conn()
        if repo_owner and repo_name:
            rows = conn.execute(
                "SELECT * FROM jobs WHERE repo_owner=? AND repo_name=? "
                "ORDER BY started_at DESC LIMIT ?",
                (repo_owner, repo_name, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM jobs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
