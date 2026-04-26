"""HiveShip Dev-Test Launcher — file-based bridge for Copilot-driven testing.

Usage (from repo root):
    python dashboard/dev_test.py "your goal text here"
    python dashboard/dev_test.py                         # uses default goal

After the generation job creates a PR, the script keeps running for 3 minutes
and polls the real PR for @sdlc-bot comments via GitHub API.  When a comment
is detected it automatically triggers a revision job (linked to the parent)
and runs the file-bridge loop for the revision LLM calls.

This script:
  1. Kills any existing servers on ports 11435, 80, 8050
  2. Clears stale telemetry / cache / workspace dirs
  3. Starts mock LLM (port 11435), HiveShip (port 80), dashboard (port 8050)
  4. Triggers a generation job with the given goal
  5. Enters a file-based bridge loop for generation LLM calls
  6. After PR is created, polls GitHub for @sdlc-bot PR comments (3 min window)
  7. On comment detected: triggers revision job → bridge loop for revision

Copilot (or any external tool) reads current_prompt.json, crafts a genuine
response, and writes current_response.json. No mocked/canned answers.

Dashboard: http://localhost:8050
"""

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def _load_dotenv(env_file: Path) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (if not already set)."""
    if not env_file.is_file():
        return
    with open(env_file, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            if key and key not in os.environ:
                os.environ[key] = value


# Auto-load .env from repo root so tokens are available in fresh terminals
_load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# On Windows, use CREATE_NEW_PROCESS_GROUP so Ctrl+C in parent doesn't kill children.
_POPEN_FLAGS = {}
if platform.system() == "Windows":
    _POPEN_FLAGS["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

# ── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
DASHBOARD_DIR = REPO_ROOT / "dashboard"
LOGS_DIR = DASHBOARD_DIR / "logs"
MOCK_LLM_PORT = 11435
HIVESHIP_PORT = 80
DASHBOARD_PORT = 8050
PROMPT_FILE = LOGS_DIR / "current_prompt.json"
RESPONSE_FILE = LOGS_DIR / "current_response.json"
RESPONSE_TIMEOUT = 600  # 10 minutes per prompt
COMMENT_POLL_WINDOW = 180  # 3 minutes waiting for PR comments
COMMENT_POLL_INTERVAL = 5  # seconds between GitHub API polls

# GitHub config (read from env, populated by _load_dotenv)
REPO_OWNER = "kushal-sharma-24"
REPO_NAME = "silver-pancake"
# In dev-test mode the human commenter IS the repo owner, so we don't
# filter out any username.  The production webhook uses BOT_USERNAME
# from config.py to skip bot self-loops, but here we want every comment.
BOT_USERNAME_SKIP = ""  # set to a GitHub login to ignore, or empty to accept all
BOT_MENTION = "@sdlc-bot"

DEFAULT_GOAL = (
    "create a chess game for me in a python file which i can run in a terminal. "
    "i want to be able to play against a bot but you cant program the bot to "
    "brute force its way to a checkmate. You can program the bot with some sort "
    "of algorithm if you like or in any other way but no brute force."
)

GOLD = "\033[93m"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
DIM = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"


# ── Utility functions ─────────────────────────────────────────────────────────

def _port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _kill_port(port: int):
    """Kill whatever is listening on the given port (Windows)."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                pid = parts[-1]
                if pid.isdigit() and int(pid) > 0:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", pid],
                        capture_output=True, timeout=5,
                    )
                    print(f"  Killed PID {pid} on port {port}")
    except Exception as e:
        print(f"  Warning: could not kill port {port}: {e}")


def _wait_for_port(port: int, timeout: float = 15.0) -> bool:
    """Wait until a port is accepting connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use(port):
            return True
        time.sleep(0.3)
    return False


def _http_get(url: str, timeout: float = 5.0):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _http_post(url: str, body: dict, timeout: float = 10.0):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _clean_handoff_files():
    """Remove any stale prompt/response handoff files."""
    for f in [PROMPT_FILE, RESPONSE_FILE]:
        if f.exists():
            f.unlink()


def _job_status(job_id: str) -> dict | None:
    """Check HiveShip job status. Returns None if unreachable."""
    try:
        return _http_get(f"http://localhost:{HIVESHIP_PORT}/status/{job_id}")
    except Exception:
        return None


def _github_api_get(path: str) -> dict | list:
    """GET request to the GitHub REST API using GITHUB_TOKEN."""
    token = os.environ.get("GITHUB_TOKEN", "")
    url = path if path.startswith("https://") else f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _poll_pr_comments(pr_number: int, after_ts: str) -> dict | None:
    """Poll GitHub for new comments on a PR created after `after_ts`.

    Checks both issue comments (general) and review comments (file-level).
    Accepts ANY new comment — the @sdlc-bot mention is not required in
    dev-test mode because the human is commenting directly.

    Args:
        pr_number: GitHub PR number.
        after_ts: ISO 8601 timestamp — only consider comments created after this.

    Returns:
        The first matching comment dict, or None if none found.
    """
    all_comments: list[dict] = []

    # 1. Issue comments (general PR conversation)
    try:
        issue_path = f"/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
        all_comments.extend(_github_api_get(issue_path))
    except Exception:
        pass

    # 2. Pull-request review comments (file-level)
    try:
        review_path = f"/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
        all_comments.extend(_github_api_get(review_path))
    except Exception:
        pass

    for c in all_comments:
        # Skip a specific bot user if configured
        if BOT_USERNAME_SKIP and c["user"]["login"] == BOT_USERNAME_SKIP:
            continue
        if c["created_at"] <= after_ts:
            continue
        # Accept any new comment (no @sdlc-bot mention required in dev mode)
        return c
    return None


def _run_bridge_loop(job_id: str, label: str = "Generation") -> int:
    """Run the file-bridge loop until the job completes. Returns calls answered."""
    calls_answered = 0
    try:
        while True:
            status = _job_status(job_id)
            if status:
                s = status.get("status", "")
                if s in ("complete", "failed"):
                    print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
                    print(f"{BOLD}  {label} Job {job_id} → {s.upper()}{RESET}")
                    if status.get("error"):
                        print(f"  {RED}Error: {status['error']}{RESET}")
                    if status.get("result"):
                        print(f"  {GREEN}Result: {status['result']}{RESET}")
                    print(f"  Calls answered: {calls_answered}")
                    if status.get("agent_states"):
                        print(f"  Agent states: {json.dumps(status['agent_states'])}")
                    print(f"{BOLD}{GOLD}{'═' * 60}{RESET}")
                    # Persist final state to dashboard DB
                    try:
                        import sys as _sys
                        _sys.path.insert(0, str(DASHBOARD_DIR))
                        from db import init_db, upsert_job
                        init_db()
                        upsert_job(status)
                        print(f"  {DIM}Final state saved to dashboard DB{RESET}")
                    except Exception as _e:
                        print(f"  {DIM}Warning: could not save final state to DB: {_e}{RESET}")
                    break

            # Poll for pending prompt
            try:
                pending = _http_get(f"http://localhost:{MOCK_LLM_PORT}/pending")
            except Exception:
                time.sleep(1)
                continue

            if not pending.get("pending"):
                time.sleep(1)
                continue

            call_id = pending["call_id"]
            schema = pending.get("schema") or "text"

            print(f"  {GOLD}▶ Call #{call_id}{RESET} | schema: {BOLD}{schema}{RESET}")
            prompt_preview = pending.get("prompt", "")[:150]
            print(f"    {DIM}{prompt_preview}{'...' if len(pending.get('prompt', '')) > 150 else ''}{RESET}")

            # Write prompt to file for Copilot to read
            _clean_handoff_files()
            PROMPT_FILE.write_text(
                json.dumps(pending, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"    {CYAN}Wrote prompt → {PROMPT_FILE.name}  (awaiting response...){RESET}")

            # Wait for response file to appear
            t0 = time.time()
            while time.time() - t0 < RESPONSE_TIMEOUT:
                if RESPONSE_FILE.exists():
                    time.sleep(0.3)
                    break
                time.sleep(0.5)
            else:
                print(f"    {RED}✗ Timeout ({RESPONSE_TIMEOUT}s) waiting for response file.{RESET}")
                try:
                    _http_post(f"http://localhost:{MOCK_LLM_PORT}/respond", {
                        "response": '{"error": "Timeout waiting for response file"}',
                    })
                except Exception:
                    pass
                _clean_handoff_files()
                continue

            # Read response
            try:
                raw = RESPONSE_FILE.read_text(encoding="utf-8")
                resp_data = json.loads(raw)
            except (json.JSONDecodeError, OSError) as e:
                print(f"    {RED}✗ Failed to read response file: {e}{RESET}")
                _clean_handoff_files()
                continue

            response_text = resp_data.get("response", "")
            if isinstance(response_text, dict):
                response_text = json.dumps(response_text, ensure_ascii=False)

            duration = time.time() - t0
            print(f"    {GREEN}✓ Response received{RESET} — {len(response_text)} chars, {duration:.1f}s")

            # POST to mock LLM
            try:
                _http_post(f"http://localhost:{MOCK_LLM_PORT}/respond", {
                    "response": response_text,
                })
                calls_answered += 1
            except Exception as e:
                print(f"    {RED}✗ Failed to POST response: {e}{RESET}")

            _clean_handoff_files()
            time.sleep(0.3)
    except KeyboardInterrupt:
        print(f"\n{GOLD}{label} bridge interrupted.{RESET}")

    return calls_answered


def _run_bridge_loop(job_id: str, label: str = "Generation") -> int:
    """Run the file-bridge loop until the job completes. Returns calls answered."""
    calls_answered = 0
    try:
        while True:
            status = _job_status(job_id)
            if status:
                s = status.get("status", "")
                if s in ("complete", "failed"):
                    print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
                    print(f"{BOLD}  {label} Job {job_id} → {s.upper()}{RESET}")
                    if status.get("error"):
                        print(f"  {RED}Error: {status['error']}{RESET}")
                    if status.get("result"):
                        print(f"  {GREEN}Result: {status['result']}{RESET}")
                    print(f"  Calls answered: {calls_answered}")
                    if status.get("agent_states"):
                        print(f"  Agent states: {json.dumps(status['agent_states'])}")
                    print(f"{BOLD}{GOLD}{'═' * 60}{RESET}")
                    # Persist final state to dashboard DB
                    try:
                        import sys as _sys
                        _sys.path.insert(0, str(DASHBOARD_DIR))
                        from db import init_db, upsert_job
                        init_db()
                        upsert_job(status)
                        print(f"  {DIM}Final state saved to dashboard DB{RESET}")
                    except Exception as _e:
                        print(f"  {DIM}Warning: could not save final state to DB: {_e}{RESET}")
                    break

            # Poll for pending prompt
            try:
                pending = _http_get(f"http://localhost:{MOCK_LLM_PORT}/pending")
            except Exception:
                time.sleep(1)
                continue

            if not pending.get("pending"):
                time.sleep(1)
                continue

            call_id = pending["call_id"]
            schema = pending.get("schema") or "text"

            print(f"  {GOLD}▶ Call #{call_id}{RESET} | schema: {BOLD}{schema}{RESET}")
            prompt_preview = pending.get("prompt", "")[:150]
            print(f"    {DIM}{prompt_preview}{'...' if len(pending.get('prompt', '')) > 150 else ''}{RESET}")

            # Write prompt to file for Copilot to read
            _clean_handoff_files()
            PROMPT_FILE.write_text(
                json.dumps(pending, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"    {CYAN}Wrote prompt → {PROMPT_FILE.name}  (awaiting response...){RESET}")

            # Wait for response file to appear
            t0 = time.time()
            while time.time() - t0 < RESPONSE_TIMEOUT:
                if RESPONSE_FILE.exists():
                    time.sleep(0.3)
                    break
                time.sleep(0.5)
            else:
                print(f"    {RED}✗ Timeout ({RESPONSE_TIMEOUT}s) waiting for response file.{RESET}")
                try:
                    _http_post(f"http://localhost:{MOCK_LLM_PORT}/respond", {
                        "response": '{"error": "Timeout waiting for response file"}',
                    })
                except Exception:
                    pass
                _clean_handoff_files()
                continue

            # Read response
            try:
                raw = RESPONSE_FILE.read_text(encoding="utf-8")
                resp_data = json.loads(raw)
            except (json.JSONDecodeError, OSError) as e:
                print(f"    {RED}✗ Failed to read response file: {e}{RESET}")
                _clean_handoff_files()
                continue

            response_text = resp_data.get("response", "")
            if isinstance(response_text, dict):
                response_text = json.dumps(response_text, ensure_ascii=False)

            duration = time.time() - t0
            print(f"    {GREEN}✓ Response received{RESET} — {len(response_text)} chars, {duration:.1f}s")

            # POST to mock LLM
            try:
                _http_post(f"http://localhost:{MOCK_LLM_PORT}/respond", {
                    "response": response_text,
                })
                calls_answered += 1
            except Exception as e:
                print(f"    {RED}✗ Failed to POST response: {e}{RESET}")

            _clean_handoff_files()
            time.sleep(0.3)
    except KeyboardInterrupt:
        print(f"\n{GOLD}{label} bridge interrupted.{RESET}")

    return calls_answered


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GOAL

    print(f"\n{BOLD}{GOLD}╔══════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{GOLD}║   HiveShip Dev-Test  (Copilot file-bridge mode)         ║{RESET}")
    print(f"{BOLD}{GOLD}╚══════════════════════════════════════════════════════════╝{RESET}\n")

    # ── Step 1: Kill old servers ──────────────────────────────────────────
    print(f"{CYAN}[1/7] Killing old servers...{RESET}")
    for port in [MOCK_LLM_PORT, HIVESHIP_PORT, DASHBOARD_PORT]:
        if _port_in_use(port):
            _kill_port(port)
        else:
            print(f"  Port {port} is free")
    time.sleep(1)

    # ── Step 2: Clean stale state ─────────────────────────────────────────
    print(f"{CYAN}[2/7] Cleaning stale state...{RESET}")
    # Telemetry.jsonl and cache.jsonl are session-scoped hot logs
    # (mock_llm truncates telemetry on start). DB persists across runs.
    _clean_handoff_files()

    workspace_base = Path(os.environ.get(
        "BASE_WORKSPACE",
        os.path.join(os.environ.get("TEMP", "/tmp"), "hiveship-workspace"),
    ))
    if workspace_base.exists():
        for d in workspace_base.iterdir():
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
        print(f"  Cleared {workspace_base}")

    # ── Step 3: Start servers ─────────────────────────────────────────────
    print(f"{CYAN}[3/7] Starting servers...{RESET}")

    python = sys.executable

    env = os.environ.copy()
    env["OLLAMA_BASE_URL"] = f"http://localhost:{MOCK_LLM_PORT}"
    env["OLLAMA_MODEL"] = "mock"
    env["DEFAULT_LLM_PROVIDER"] = "ollama"
    if "BASE_WORKSPACE" not in env:
        env["BASE_WORKSPACE"] = str(Path(env.get("TEMP", "/tmp")) / "hiveship-workspace")

    if not env.get("GITHUB_TOKEN"):
        print(f"{RED}  ERROR: GITHUB_TOKEN env var not set. Set it before running.{RESET}")
        sys.exit(1)
    if not env.get("WEBHOOK_SECRET"):
        env["WEBHOOK_SECRET"] = "test-secret"

    env["ENABLE_TEST_ENDPOINTS"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    LOGS_DIR.mkdir(exist_ok=True)
    log_mock = open(LOGS_DIR / "mock_llm.log", "w", encoding="utf-8")
    log_hive = open(LOGS_DIR / "hiveship.log", "w", encoding="utf-8")
    log_dash = open(LOGS_DIR / "dashboard.log", "w", encoding="utf-8")

    child_procs = []

    mock_proc = subprocess.Popen(
        [python, str(DASHBOARD_DIR / "mock_llm.py"), "--port", str(MOCK_LLM_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_mock, stderr=log_mock,
        **_POPEN_FLAGS,
    )
    child_procs.append(mock_proc)
    print(f"  Mock LLM     → PID {mock_proc.pid} (port {MOCK_LLM_PORT})")

    hiveship_proc = subprocess.Popen(
        [python, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(HIVESHIP_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_hive, stderr=log_hive,
        **_POPEN_FLAGS,
    )
    child_procs.append(hiveship_proc)
    print(f"  HiveShip     → PID {hiveship_proc.pid} (port {HIVESHIP_PORT})")

    dash_proc = subprocess.Popen(
        [python, str(DASHBOARD_DIR / "serve.py"), "--port", str(DASHBOARD_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_dash, stderr=log_dash,
        **_POPEN_FLAGS,
    )
    child_procs.append(dash_proc)
    print(f"  Dashboard    → PID {dash_proc.pid} (port {DASHBOARD_PORT})")

    # ── Step 4: Wait for servers ──────────────────────────────────────────
    print(f"\n{CYAN}[4/7] Waiting for servers to be ready...{RESET}")
    for name, port in [("Mock LLM", MOCK_LLM_PORT), ("HiveShip", HIVESHIP_PORT), ("Dashboard", DASHBOARD_PORT)]:
        if _wait_for_port(port, timeout=20):
            print(f"  {GREEN}✓{RESET} {name} ready on port {port}")
        else:
            print(f"  {RED}✗{RESET} {name} failed to start on port {port}")
            log_map = {"Mock LLM": "mock_llm.log", "HiveShip": "hiveship.log", "Dashboard": "dashboard.log"}
            log_file = LOGS_DIR / log_map.get(name, "")
            if log_file.exists():
                log_mock.flush(); log_hive.flush(); log_dash.flush()
                content = log_file.read_text(encoding="utf-8", errors="replace")
                if content.strip():
                    print(f"  {DIM}--- {log_file.name} ---{RESET}")
                    for line in content.strip().splitlines()[-15:]:
                        print(f"  {DIM}{line}{RESET}")
            print(f"{RED}Aborting. Check dashboard/logs/ for full output.{RESET}")
            sys.exit(1)

    # ── Step 5: Trigger generation job ───────────────────────────────────
    print(f"\n{CYAN}[5/7] Triggering generation job...{RESET}")
    print(f"  Goal: {goal[:100]}{'...' if len(goal) > 100 else ''}")

    result = _http_post(f"http://localhost:{HIVESHIP_PORT}/teams-trigger", {
        "text": goal,
        "llm_provider": "ollama",
    })

    job_id = result["job_id"]
    print(f"  {GREEN}✓{RESET} Job {BOLD}{job_id}{RESET} accepted")

    print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
    print(f"{BOLD}{GOLD}  All servers running. Job {job_id} in progress.{RESET}")
    print(f"{BOLD}{GOLD}{'═' * 60}{RESET}")
    print(f"\n  {BOLD}Dashboard:{RESET}  http://localhost:{DASHBOARD_PORT}")
    print(f"  {BOLD}Job status:{RESET} http://localhost:{HIVESHIP_PORT}/status/{job_id}")
    print(f"\n  {BOLD}Prompt file:{RESET}  dashboard/logs/current_prompt.json")
    print(f"  {BOLD}Response file:{RESET} dashboard/logs/current_response.json")

    # ── Step 6: File-based bridge loop (generation) ───────────────────────
    print(f"\n{CYAN}[6/7] Entering file-bridge loop (Generation)...{RESET}")
    print(f"  Waiting for LLM calls. Copilot reads prompt file, writes response file.\n")

    gen_calls = _run_bridge_loop(job_id, label="Generation")
    print(f"  {DIM}Generation bridge completed ({gen_calls} calls).{RESET}")

    # ── Step 7: Poll for PR comments → Revision ──────────────────────────
    # Check if a PR was created
    status = _job_status(job_id)
    pr_number = status.get("pr_number") if status else None
    pr_url = status.get("pr_url") if status else None

    if not pr_number:
        print(f"\n{DIM}  No PR created (pr_number not found in job). Skipping revision phase.{RESET}")
        # Grace period before shutdown
        print(f"  {DIM}Waiting 5s for dashboard to sync...{RESET}")
        time.sleep(5)
    else:
        print(f"\n{BOLD}{GOLD}{'═' * 60}{RESET}")
        print(f"{BOLD}{GOLD}  PR #{pr_number} created: {pr_url}{RESET}")
        print(f"{BOLD}{GOLD}{'═' * 60}{RESET}")
        print(f"\n{CYAN}[7/7] Polling for {BOT_MENTION} comments on PR #{pr_number}...{RESET}")
        print(f"  Comment on the PR to trigger a revision.")
        print(f"  Polling every {COMMENT_POLL_INTERVAL}s for {COMMENT_POLL_WINDOW}s.\n")

        # Record the current time as the baseline — only consider comments after this
        poll_start = time.time()
        # ISO 8601 timestamp for GitHub API filtering
        after_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(poll_start))
        comment_found = None

        try:
            while time.time() - poll_start < COMMENT_POLL_WINDOW:
                remaining = int(COMMENT_POLL_WINDOW - (time.time() - poll_start))
                print(f"  {DIM}Polling... ({remaining}s remaining){RESET}", end="\r")

                comment_found = _poll_pr_comments(pr_number, after_ts)
                if comment_found:
                    print(f"\n  {GREEN}✓ Comment detected!{RESET}")
                    print(f"    {BOLD}Author:{RESET} {comment_found['user']['login']}")
                    print(f"    {BOLD}Body:{RESET}   {comment_found['body'][:120]}")
                    break

                time.sleep(COMMENT_POLL_INTERVAL)
            else:
                print(f"\n  {DIM}No {BOT_MENTION} comment detected within {COMMENT_POLL_WINDOW}s.{RESET}")

        except KeyboardInterrupt:
            print(f"\n{GOLD}Comment polling interrupted.{RESET}")
            comment_found = None

        if comment_found:
            # ── Trigger revision via /test-webhook ────────────────────────
            print(f"\n{CYAN}  Triggering revision job...{RESET}")
            rev_result = _http_post(f"http://localhost:{HIVESHIP_PORT}/test-webhook", {
                "pr_number": pr_number,
                "comment_body": comment_found["body"],
                "parent_job_id": job_id,
            })
            rev_job_id = rev_result["job_id"]
            print(f"  {GREEN}✓{RESET} Revision Job {BOLD}{rev_job_id}{RESET} accepted (parent: {job_id})")

            # ── File-bridge loop for revision ─────────────────────────────
            print(f"\n{CYAN}  Entering file-bridge loop (Revision)...{RESET}")
            print(f"  Expecting 3 LLM calls: FileRequest → DeliveryPlan → ReviewResult\n")

            rev_calls = _run_bridge_loop(rev_job_id, label="Revision")
            print(f"  {DIM}Revision bridge completed ({rev_calls} calls).{RESET}")

        # Grace period before shutdown
        print(f"\n  {DIM}Waiting 5s for dashboard to sync final state...{RESET}")
        time.sleep(5)

    # ── Cleanup ───────────────────────────────────────────────────────────
    _clean_handoff_files()
    for proc in child_procs:
        try:
            proc.terminate()
        except Exception:
            pass
    print(f"{DIM}Child processes terminated.{RESET}")


if __name__ == "__main__":
    main()
