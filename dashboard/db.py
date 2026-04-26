"""SQLite persistence layer for the HiveShip Observability Dashboard.

Tables:
  - jobs: full job snapshots (upserted on each poll)
  - llm_calls: per-LLM-call telemetry (prompt, response, tokens, latency)

Zero external dependencies — uses Python stdlib sqlite3.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

DB_PATH = Path(__file__).parent / "hiveship_obs.db"

_local = threading.local()


def _conn() -> sqlite3.Connection:
    """Return a thread-local connection (SQLite is not thread-safe by default)."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(str(DB_PATH), timeout=10)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def init_db() -> None:
    """Create tables if they don't exist."""
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id       TEXT PRIMARY KEY,
            goal         TEXT NOT NULL DEFAULT '',
            status       TEXT NOT NULL DEFAULT 'accepted',
            current_step TEXT NOT NULL DEFAULT '',
            error        TEXT,
            result       TEXT,
            job_type     TEXT NOT NULL DEFAULT 'generation',
            parent_job_id TEXT,
            pr_number    INTEGER,
            pr_url       TEXT,
            pr_branch    TEXT,
            created_at   INTEGER NOT NULL,
            updated_at   INTEGER NOT NULL,
            events_json  TEXT NOT NULL DEFAULT '[]',
            agent_states_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS llm_calls (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id         TEXT,
            call_id        INTEGER NOT NULL,
            model          TEXT,
            schema_name    TEXT,
            system_prompt  TEXT,
            user_prompt    TEXT,
            response       TEXT,
            duration_ms    INTEGER,
            prompt_tokens  INTEGER DEFAULT 0,
            response_tokens INTEGER DEFAULT 0,
            created_at     INTEGER NOT NULL,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_llm_calls_job ON llm_calls(job_id);
        CREATE INDEX IF NOT EXISTS idx_llm_calls_callid ON llm_calls(call_id);
    """)
    c.commit()

    # ── Schema migration: add columns if upgrading from older DB ──────────
    existing = {
        row[1] for row in c.execute("PRAGMA table_info(jobs)").fetchall()
    }
    migrations = [
        ("job_type", "TEXT NOT NULL DEFAULT 'generation'"),
        ("parent_job_id", "TEXT"),
        ("pr_number", "INTEGER"),
        ("pr_url", "TEXT"),
        ("pr_branch", "TEXT"),
    ]
    for col_name, col_def in migrations:
        if col_name not in existing:
            try:
                c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_def}")
            except sqlite3.OperationalError:
                pass  # column already exists (WAL race or prior partial migration)
    c.commit()


# ── Token estimation ──────────────────────────────────────────────────────────

def _estimate_tokens(text: str) -> int:
    """Rough token estimate: word_count * 1.3."""
    if not text:
        return 0
    return int(len(text.split()) * 1.3)


# ── Jobs ──────────────────────────────────────────────────────────────────────

def upsert_job(job: dict) -> None:
    """Insert or update a job snapshot."""
    c = _conn()
    now = int(time.time() * 1000)
    events = job.get("events", [])
    created_at = events[0]["t"] if events else now

    c.execute("""
        INSERT INTO jobs (job_id, goal, status, current_step, error, result,
                          job_type, parent_job_id, pr_number, pr_url, pr_branch,
                          created_at, updated_at, events_json, agent_states_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            goal = excluded.goal,
            status = excluded.status,
            current_step = excluded.current_step,
            error = excluded.error,
            result = excluded.result,
            job_type = excluded.job_type,
            parent_job_id = excluded.parent_job_id,
            pr_number = excluded.pr_number,
            pr_url = excluded.pr_url,
            pr_branch = excluded.pr_branch,
            updated_at = excluded.updated_at,
            events_json = excluded.events_json,
            agent_states_json = excluded.agent_states_json
    """, (
        job["job_id"],
        job.get("goal", ""),
        job.get("status", "accepted"),
        job.get("current_step", ""),
        job.get("error"),
        job.get("result"),
        job.get("job_type", "generation"),
        job.get("parent_job_id"),
        job.get("pr_number"),
        job.get("pr_url"),
        job.get("pr_branch"),
        created_at,
        now,
        json.dumps(events, ensure_ascii=False),
        json.dumps(job.get("agent_states", {}), ensure_ascii=False),
    ))
    c.commit()


def get_jobs() -> list[dict]:
    """Return all jobs as summary dicts, newest first."""
    c = _conn()
    rows = c.execute("""
        SELECT job_id, goal, status, current_step, error,
               job_type, parent_job_id, pr_number, pr_url,
               created_at, updated_at, events_json, agent_states_json
        FROM jobs ORDER BY created_at DESC
    """).fetchall()

    summaries = []
    for r in rows:
        events = json.loads(r["events_json"])
        first_t = events[0]["t"] if events else 0
        last_t = events[-1]["t"] if events else 0
        duration_ms = last_t - first_t if first_t else 0
        agent_states = json.loads(r["agent_states_json"])
        summaries.append({
            "job_id": r["job_id"],
            "goal": r["goal"],
            "status": r["status"],
            "current_step": r["current_step"],
            "job_type": r["job_type"] or "generation",
            "parent_job_id": r["parent_job_id"],
            "pr_number": r["pr_number"],
            "pr_url": r["pr_url"],
            "agent_count": len(agent_states),
            "event_count": len(events),
            "started_at": first_t,
            "duration_ms": duration_ms,
        })
    return summaries


def get_job(job_id: str) -> dict | None:
    """Return the full job dict (with events and agent_states)."""
    c = _conn()
    row = c.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        return None
    return {
        "job_id": row["job_id"],
        "goal": row["goal"],
        "status": row["status"],
        "current_step": row["current_step"],
        "error": row["error"],
        "result": row["result"],
        "job_type": row["job_type"] or "generation",
        "parent_job_id": row["parent_job_id"],
        "pr_number": row["pr_number"],
        "pr_url": row["pr_url"],
        "pr_branch": row["pr_branch"],
        "events": json.loads(row["events_json"]),
        "agent_states": json.loads(row["agent_states_json"]),
    }


def delete_job(job_id: str) -> bool:
    """Delete a job and its LLM calls. Returns True if found."""
    c = _conn()
    cur = c.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    c.commit()
    return cur.rowcount > 0


# ── LLM Calls ────────────────────────────────────────────────────────────────

def insert_llm_request(call_id: int, model: str, schema_name: str | None,
                        system_prompt: str, user_prompt: str,
                        job_id: str | None = None) -> None:
    """Insert an LLM request record (response filled in later)."""
    c = _conn()
    c.execute("""
        INSERT INTO llm_calls (job_id, call_id, model, schema_name,
                               system_prompt, user_prompt,
                               prompt_tokens, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, call_id, model, schema_name,
        system_prompt, user_prompt,
        _estimate_tokens(system_prompt) + _estimate_tokens(user_prompt),
        int(time.time() * 1000),
    ))
    c.commit()


def update_llm_response(call_id: int, response: str, duration_ms: int) -> None:
    """Fill in the response for an existing LLM call record."""
    c = _conn()
    c.execute("""
        UPDATE llm_calls
        SET response = ?, duration_ms = ?, response_tokens = ?
        WHERE call_id = ? AND response IS NULL
    """, (
        response, duration_ms, _estimate_tokens(response), call_id,
    ))
    c.commit()


def get_llm_calls(job_id: str | None = None) -> list[dict]:
    """Return LLM calls, optionally filtered by job_id."""
    c = _conn()
    if job_id:
        rows = c.execute(
            "SELECT * FROM llm_calls WHERE job_id = ? ORDER BY call_id",
            (job_id,),
        ).fetchall()
    else:
        rows = c.execute("SELECT * FROM llm_calls ORDER BY call_id").fetchall()

    return [
        {
            "call_id": r["call_id"],
            "job_id": r["job_id"],
            "model": r["model"],
            "schema": r["schema_name"],
            "system": r["system_prompt"] or "",
            "prompt": r["user_prompt"] or "",
            "response": r["response"] or "",
            "duration_ms": r["duration_ms"],
            "prompt_tokens": r["prompt_tokens"] or 0,
            "response_tokens": r["response_tokens"] or 0,
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def get_llm_stats() -> dict:
    """Aggregate LLM stats across all calls."""
    c = _conn()
    row = c.execute("""
        SELECT
            COUNT(*) AS total_calls,
            COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tokens,
            COALESCE(SUM(response_tokens), 0) AS total_response_tokens,
            COALESCE(AVG(duration_ms), 0) AS avg_duration_ms,
            COALESCE(MAX(duration_ms), 0) AS max_duration_ms,
            COALESCE(MIN(CASE WHEN duration_ms > 0 THEN duration_ms END), 0) AS min_duration_ms
        FROM llm_calls WHERE response IS NOT NULL
    """).fetchone()

    return {
        "total_calls": row["total_calls"],
        "total_prompt_tokens": row["total_prompt_tokens"],
        "total_response_tokens": row["total_response_tokens"],
        "total_tokens": row["total_prompt_tokens"] + row["total_response_tokens"],
        "avg_duration_ms": int(row["avg_duration_ms"]),
        "max_duration_ms": row["max_duration_ms"],
        "min_duration_ms": row["min_duration_ms"],
    }


# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Aggregate dashboard stats: jobs + LLM."""
    c = _conn()
    job_row = c.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
        FROM jobs
    """).fetchone()

    total = job_row["total"]
    completed = job_row["completed"] or 0
    failed = job_row["failed"] or 0

    # Average duration from events
    dur_row = c.execute("""
        SELECT AVG(
            json_extract(events_json, '$[#-1].t') - json_extract(events_json, '$[0].t')
        ) AS avg_dur
        FROM jobs WHERE json_array_length(events_json) >= 2
    """).fetchone()
    avg_duration = int(dur_row["avg_dur"]) if dur_row["avg_dur"] else 0

    llm = get_llm_stats()

    return {
        "total_jobs": total,
        "completed": completed,
        "failed": failed,
        "success_rate": round(completed / total * 100, 1) if total else 0,
        "avg_duration_ms": avg_duration,
        "total_llm_calls": llm["total_calls"],
        "total_tokens": llm["total_tokens"],
        "total_prompt_tokens": llm["total_prompt_tokens"],
        "total_response_tokens": llm["total_response_tokens"],
        "avg_llm_duration_ms": llm["avg_duration_ms"],
        "max_llm_duration_ms": llm["max_duration_ms"],
    }


# ── Job-LLM Correlation ──────────────────────────────────────────────────────

def correlate_calls_to_current_job() -> None:
    """Assign uncorrelated LLM calls (job_id IS NULL) to the most recent running job."""
    c = _conn()
    running = c.execute(
        "SELECT job_id FROM jobs WHERE status NOT IN ('complete', 'failed') ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    if not running:
        return
    c.execute(
        "UPDATE llm_calls SET job_id = ? WHERE job_id IS NULL",
        (running["job_id"],),
    )
    c.commit()


# ── Analytics Aggregates ──────────────────────────────────────────────────────

# Gemini 3.1 Pro Preview pricing (standard ≤200K context)
LLM_INPUT_COST_PER_1M = 2.00   # USD per 1M input tokens
LLM_OUTPUT_COST_PER_1M = 12.00  # USD per 1M output tokens


def _extract_repo(pr_url: str | None) -> str:
    """Extract 'owner/repo' from a GitHub PR URL, or return 'unknown'."""
    if not pr_url:
        return "unknown"
    # https://github.com/owner/repo/pull/N
    parts = pr_url.replace("https://", "").replace("http://", "").split("/")
    # ['github.com', 'owner', 'repo', 'pull', 'N']
    if len(parts) >= 3:
        return f"{parts[1]}/{parts[2]}"
    return "unknown"


def get_analytics() -> dict:
    """Return all analytics aggregates in a single payload."""
    c = _conn()

    # ── KPIs ──────────────────────────────────────────────────────────────
    job_row = c.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) AS completed,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed,
            SUM(CASE WHEN status NOT IN ('complete','failed') THEN 1 ELSE 0 END) AS active,
            SUM(CASE WHEN job_type = 'generation' THEN 1 ELSE 0 END) AS gen_count,
            SUM(CASE WHEN job_type = 'revision' THEN 1 ELSE 0 END) AS rev_count
        FROM jobs
    """).fetchone()

    total = job_row["total"] or 0
    completed = job_row["completed"] or 0
    failed = job_row["failed"] or 0
    active = job_row["active"] or 0
    gen_count = job_row["gen_count"] or 0
    rev_count = job_row["rev_count"] or 0

    success_rate = round(completed / total * 100, 1) if total else 0

    # Revision rate: % of generation jobs that have at least one child revision
    gen_with_rev = 0
    if gen_count:
        row = c.execute("""
            SELECT COUNT(DISTINCT parent_job_id) AS cnt
            FROM jobs WHERE job_type = 'revision' AND parent_job_id IS NOT NULL
        """).fetchone()
        gen_with_rev = row["cnt"] or 0
    revision_rate = round(gen_with_rev / gen_count * 100, 1) if gen_count else 0

    # Avg durations by type
    dur_rows = c.execute("""
        SELECT job_type,
            AVG(json_extract(events_json, '$[#-1].t') - json_extract(events_json, '$[0].t')) AS avg_dur
        FROM jobs WHERE json_array_length(events_json) >= 2
        GROUP BY job_type
    """).fetchall()
    avg_dur = {}
    for r in dur_rows:
        avg_dur[r["job_type"] or "generation"] = int(r["avg_dur"]) if r["avg_dur"] else 0

    # LLM totals
    llm_row = c.execute("""
        SELECT
            COUNT(*) AS total_calls,
            COALESCE(SUM(prompt_tokens), 0) AS total_prompt_tok,
            COALESCE(SUM(response_tokens), 0) AS total_response_tok
        FROM llm_calls WHERE response IS NOT NULL
    """).fetchone()
    total_prompt_tok = llm_row["total_prompt_tok"]
    total_response_tok = llm_row["total_response_tok"]
    total_tokens = total_prompt_tok + total_response_tok
    total_cost = (total_prompt_tok / 1_000_000 * LLM_INPUT_COST_PER_1M +
                  total_response_tok / 1_000_000 * LLM_OUTPUT_COST_PER_1M)

    kpis = {
        "total_jobs": total,
        "completed": completed,
        "failed": failed,
        "active": active,
        "gen_count": gen_count,
        "rev_count": rev_count,
        "success_rate": success_rate,
        "revision_rate": revision_rate,
        "avg_duration_gen_ms": avg_dur.get("generation", 0),
        "avg_duration_rev_ms": avg_dur.get("revision", 0),
        "total_tokens": total_tokens,
        "total_prompt_tokens": total_prompt_tok,
        "total_response_tokens": total_response_tok,
        "total_cost_usd": round(total_cost, 4),
        "total_llm_calls": llm_row["total_calls"],
    }

    # ── Job History (all jobs, newest first) ──────────────────────────────
    rows = c.execute("""
        SELECT job_id, goal, status, current_step, job_type, parent_job_id,
               pr_number, pr_url, pr_branch, created_at, updated_at,
               events_json, agent_states_json
        FROM jobs ORDER BY created_at DESC
    """).fetchall()

    history = []
    for r in rows:
        events = json.loads(r["events_json"])
        first_t = events[0]["t"] if events else 0
        last_t = events[-1]["t"] if events else 0
        duration_ms = last_t - first_t if first_t else 0
        agents = json.loads(r["agent_states_json"])
        repo = _extract_repo(r["pr_url"])

        # Per-job LLM stats
        llm = c.execute("""
            SELECT COUNT(*) AS calls,
                   COALESCE(SUM(prompt_tokens),0) AS ptok,
                   COALESCE(SUM(response_tokens),0) AS rtok
            FROM llm_calls WHERE job_id = ? AND response IS NOT NULL
        """, (r["job_id"],)).fetchone()

        history.append({
            "job_id": r["job_id"],
            "goal": r["goal"],
            "status": r["status"],
            "job_type": r["job_type"] or "generation",
            "parent_job_id": r["parent_job_id"],
            "repo": repo,
            "pr_number": r["pr_number"],
            "pr_url": r["pr_url"],
            "created_at": r["created_at"],
            "duration_ms": duration_ms,
            "agent_count": len(agents),
            "llm_calls": llm["calls"],
            "tokens": llm["ptok"] + llm["rtok"],
        })

    # ── Failure Breakdown ─────────────────────────────────────────────────
    # By failure_class (from events JSON)
    failure_rows = c.execute("""
        SELECT j.value ->> 'failure_class' AS fc, COUNT(*) AS cnt
        FROM jobs, json_each(jobs.events_json) AS j
        WHERE j.value ->> 'failure_class' IS NOT NULL
          AND j.value ->> 'failure_class' != ''
        GROUP BY fc ORDER BY cnt DESC
    """).fetchall()
    failure_by_class = [{"class": r["fc"], "count": r["cnt"]} for r in failure_rows]

    # By pipeline stage at failure
    stage_rows = c.execute("""
        SELECT current_step AS stage, COUNT(*) AS cnt
        FROM jobs WHERE status = 'failed' AND current_step != ''
        GROUP BY current_step ORDER BY cnt DESC
    """).fetchall()
    failure_by_stage = [{"stage": r["stage"], "count": r["cnt"]} for r in stage_rows]

    # ── LLM Performance by schema ─────────────────────────────────────────
    schema_rows = c.execute("""
        SELECT schema_name,
            COUNT(*) AS calls,
            COALESCE(AVG(duration_ms), 0) AS avg_dur,
            COALESCE(SUM(prompt_tokens), 0) AS ptok,
            COALESCE(SUM(response_tokens), 0) AS rtok
        FROM llm_calls WHERE response IS NOT NULL
        GROUP BY schema_name ORDER BY calls DESC
    """).fetchall()
    llm_by_schema = [{
        "schema": r["schema_name"] or "text",
        "calls": r["calls"],
        "avg_duration_ms": int(r["avg_dur"]),
        "prompt_tokens": r["ptok"],
        "response_tokens": r["rtok"],
        "cost_usd": round(
            r["ptok"] / 1_000_000 * LLM_INPUT_COST_PER_1M +
            r["rtok"] / 1_000_000 * LLM_OUTPUT_COST_PER_1M, 4),
    } for r in schema_rows]

    # ── Repository Activity ───────────────────────────────────────────────
    repo_map: dict[str, dict] = {}
    for h in history:
        repo = h["repo"]
        if repo not in repo_map:
            repo_map[repo] = {
                "repo": repo, "total_jobs": 0, "completed": 0,
                "failed": 0, "tokens": 0, "last_activity": 0,
            }
        rm = repo_map[repo]
        rm["total_jobs"] += 1
        if h["status"] == "complete":
            rm["completed"] += 1
        if h["status"] == "failed":
            rm["failed"] += 1
        rm["tokens"] += h["tokens"]
        if h["created_at"] > rm["last_activity"]:
            rm["last_activity"] = h["created_at"]
    repos = sorted(repo_map.values(), key=lambda x: x["last_activity"], reverse=True)
    for r in repos:
        r["success_rate"] = round(r["completed"] / r["total_jobs"] * 100, 1) if r["total_jobs"] else 0

    return {
        "kpis": kpis,
        "history": history,
        "failure_by_class": failure_by_class,
        "failure_by_stage": failure_by_stage,
        "llm_by_schema": llm_by_schema,
        "repos": repos,
    }
