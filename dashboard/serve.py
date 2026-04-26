"""Standalone observability dashboard for HiveShip.

Runs as a separate process — zero coupling with the production app.
Polls the HiveShip API for job data, reads mock_llm telemetry from
dashboard/telemetry.jsonl, and serves a single-page dashboard UI.

Usage:
    python dashboard/serve.py                                   # defaults
    python dashboard/serve.py --hiveship http://localhost:80     # custom URL
    python dashboard/serve.py --port 8050                       # custom port
"""

import argparse
import json
import os
import threading
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from db import init_db, upsert_job, get_jobs, get_job, get_llm_calls, get_stats as db_get_stats, delete_job, correlate_calls_to_current_job, get_analytics

# ── Config ────────────────────────────────────────────────────────────────────
DASHBOARD_DIR = Path(__file__).parent
CACHE_PATH = DASHBOARD_DIR / "cache.jsonl"
TELEMETRY_PATH = DASHBOARD_DIR / "telemetry.jsonl"
HIVESHIP_URL = "http://localhost:80"
POLL_INTERVAL = 2  # seconds


# ── Cache: append-only JSONL for job snapshots ────────────────────────────────
_cache_lock = threading.Lock()
_job_cache: dict = {}   # job_id → latest snapshot


def _load_cache():
    """Load previously cached job snapshots from disk."""
    if not CACHE_PATH.exists():
        return
    with open(CACHE_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                job = json.loads(line)
                _job_cache[job["job_id"]] = job
            except (json.JSONDecodeError, KeyError):
                continue


def _save_snapshot(job: dict):
    """Append a job snapshot to the cache file and persist to DB."""
    with _cache_lock:
        _job_cache[job["job_id"]] = job
    with open(CACHE_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(job, ensure_ascii=False) + "\n")
    try:
        upsert_job(job)
        correlate_calls_to_current_job()
    except Exception:
        pass  # DB write failure should not break polling


# ── Telemetry reader (from mock_llm.py) ───────────────────────────────────────
def _read_telemetry() -> list:
    """Read all telemetry records from the mock LLM log."""
    if not TELEMETRY_PATH.exists():
        return []
    records = []
    with open(TELEMETRY_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records


# ── HiveShip API poller ──────────────────────────────────────────────────────
def _poll_hiveship():
    """Background thread: poll /api/jobs and /status/{id} from HiveShip."""
    while True:
        try:
            # Discover jobs
            req = urllib.request.Request(f"{HIVESHIP_URL}/api/jobs")
            with urllib.request.urlopen(req, timeout=5) as resp:
                jobs_list = json.loads(resp.read().decode())

            # Fetch full status for each job
            for summary in jobs_list:
                jid = summary["job_id"]
                # Skip terminal jobs we already cached
                cached = _job_cache.get(jid)
                if cached and cached.get("status") in ("complete", "failed"):
                    continue
                try:
                    req2 = urllib.request.Request(f"{HIVESHIP_URL}/status/{jid}")
                    with urllib.request.urlopen(req2, timeout=5) as resp2:
                        full_job = json.loads(resp2.read().decode())
                        _save_snapshot(full_job)
                except Exception:
                    pass  # server may have restarted

        except (urllib.error.URLError, OSError):
            pass  # HiveShip not running — serve from cache
        except Exception:
            pass

        time.sleep(POLL_INTERVAL)


# ── HTTP Handler ──────────────────────────────────────────────────────────────
class DashboardHandler(SimpleHTTPRequestHandler):
    """Serves the dashboard HTML and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_message(self, format, *args):
        pass  # quiet

    def do_GET(self):
        # ── API endpoints ─────────────────────────────────────────────────
        if self.path == "/api/jobs":
            # Try DB first, fall back to in-memory cache
            try:
                summaries = get_jobs()
            except Exception:
                jobs = list(_job_cache.values())
                summaries = []
                for j in jobs:
                    events = j.get("events", [])
                    first_t = events[0]["t"] if events else 0
                    last_t = events[-1]["t"] if events else 0
                    duration_ms = last_t - first_t if first_t else 0
                    summaries.append({
                        "job_id": j["job_id"],
                        "goal": j.get("goal", ""),
                        "status": j.get("status", "unknown"),
                        "current_step": j.get("current_step", ""),
                        "agent_count": len(j.get("agent_states", {})),
                        "event_count": len(events),
                        "started_at": first_t,
                        "duration_ms": duration_ms,
                    })
                summaries.sort(key=lambda x: x["started_at"], reverse=True)
            self._json_response(summaries)
            return

        if self.path.startswith("/api/jobs/"):
            rest = self.path[len("/api/jobs/"):]
            # /api/jobs/{id}/llm-calls
            if "/llm-calls" in rest:
                job_id = rest.split("/")[0]
                try:
                    calls = get_llm_calls(job_id)
                except Exception:
                    calls = []
                self._json_response(calls)
                return
            # /api/jobs/{id}
            job_id = rest.split("/")[0] if "/" in rest else rest
            try:
                job = get_job(job_id)
            except Exception:
                job = _job_cache.get(job_id)
            if not job:
                self.send_error(404, "Job not found")
                return
            self._json_response(job)
            return

        if self.path == "/api/telemetry":
            # Return from DB if available, fall back to file
            try:
                records = get_llm_calls()
            except Exception:
                records = _read_telemetry()
            self._json_response(records)
            return

        if self.path == "/api/analytics":
            try:
                data = get_analytics()
            except Exception as e:
                data = {"error": str(e)}
            self._json_response(data)
            return

        if self.path == "/api/stats":
            try:
                stats = db_get_stats()
            except Exception:
                # Fallback to in-memory
                jobs = list(_job_cache.values())
                total = len(jobs)
                completed = sum(1 for j in jobs if j.get("status") == "complete")
                failed = sum(1 for j in jobs if j.get("status") == "failed")
                durations = []
                for j in jobs:
                    events = j.get("events", [])
                    if len(events) >= 2:
                        durations.append(events[-1]["t"] - events[0]["t"])
                avg_duration = int(sum(durations) / len(durations)) if durations else 0
                telemetry = _read_telemetry()
                llm_calls = sum(1 for r in telemetry if r.get("type") == "llm_request")
                stats = {
                    "total_jobs": total,
                    "completed": completed,
                    "failed": failed,
                    "success_rate": round(completed / total * 100, 1) if total else 0,
                    "avg_duration_ms": avg_duration,
                    "total_llm_calls": llm_calls,
                    "total_tokens": 0,
                    "total_prompt_tokens": 0,
                    "total_response_tokens": 0,
                    "avg_llm_duration_ms": 0,
                    "max_llm_duration_ms": 0,
                }
            self._json_response(stats)
            return

        # ── Serve dashboard HTML (default to index.html) ──────────────────
        if self.path == "/" or self.path == "/dashboard":
            self.path = "/index.html"

        super().do_GET()

    def do_DELETE(self):
        """Handle DELETE requests."""
        if self.path.startswith("/api/jobs/"):
            job_id = self.path[len("/api/jobs/"):].split("/")[0]
            try:
                found = delete_job(job_id)
            except Exception:
                found = False
            with _cache_lock:
                _job_cache.pop(job_id, None)
            if found:
                self._json_response({"ok": True, "deleted": job_id})
            else:
                self.send_error(404, "Job not found")
            return
        self.send_error(404)

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def main():
    global HIVESHIP_URL, POLL_INTERVAL

    parser = argparse.ArgumentParser(description="HiveShip Observability Dashboard")
    parser.add_argument("--port", type=int, default=8050, help="Dashboard port (default 8050)")
    parser.add_argument("--hiveship", type=str, default="http://localhost:80",
                        help="HiveShip API base URL")
    parser.add_argument("--poll", type=int, default=2, help="Poll interval seconds (default 2)")
    parser.add_argument("--keep-cache", action="store_true",
                        help="Keep cache from previous runs (default: start fresh)")
    args = parser.parse_args()

    HIVESHIP_URL = args.hiveship.rstrip("/")
    POLL_INTERVAL = args.poll

    # Initialize SQLite DB
    init_db()
    print(f"SQLite DB: {DASHBOARD_DIR / 'hiveship_obs.db'}")

    if args.keep_cache:
        _load_cache()
        print(f"Loaded {len(_job_cache)} cached jobs from {CACHE_PATH}")
    else:
        # Start fresh — clear in-memory cache (DB persists across runs)
        if CACHE_PATH.exists():
            CACHE_PATH.unlink()
        print("Starting fresh (in-memory cache cleared, DB preserved)")

    # Start background poller
    poller = threading.Thread(target=_poll_hiveship, daemon=True)
    poller.start()

    server = HTTPServer(("0.0.0.0", args.port), DashboardHandler)
    print(f"\n\033[1m\033[93m╔══════════════════════════════════════════════════╗\033[0m")
    print(f"\033[1m\033[93m║   HiveShip Observability Dashboard               ║\033[0m")
    print(f"\033[1m\033[93m║   http://localhost:{args.port}/                         ║\033[0m")
    print(f"\033[1m\033[93m╚══════════════════════════════════════════════════╝\033[0m")
    print(f"\nPolling HiveShip at: {HIVESHIP_URL}")
    print(f"Mock LLM telemetry: {TELEMETRY_PATH}")
    print(f"Cache: {CACHE_PATH}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
