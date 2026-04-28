"""HiveShip Dev Launcher — one script to start everything fresh.

Usage (from repo root):
    python client/dev_launch.py "your goal text here"
    python client/dev_launch.py                          # uses default chess goal

This script:
  1. Kills any existing servers on ports 11435, 80, 8050
  2. Clears stale telemetry / cache / workspace dirs
  3. Starts mock LLM (port 11435), HiveShip (port 80), dashboard (port 8050)
  4. Triggers a job with the given goal
  5. Prints the job_id and instructions for the prompt-answer loop

After this script finishes, poll GET http://localhost:11435/pending and
POST http://localhost:11435/respond to answer each LLM call.

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
# Do NOT use DETACHED_PROCESS — it hides errors and can break uvicorn.
_POPEN_FLAGS = {}
if platform.system() == "Windows":
    _POPEN_FLAGS["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

# ── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
CLIENT_DIR = REPO_ROOT / "client"
DASHBOARD_DIR = REPO_ROOT / "dashboard"
MOCK_LLM_PORT = 11435
HIVESHIP_PORT = 80
DASHBOARD_PORT = 8050

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


def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_GOAL

    print(f"\n{BOLD}{GOLD}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{GOLD}║   HiveShip Test Launcher                            ║{RESET}")
    print(f"{BOLD}{GOLD}╚══════════════════════════════════════════════════════╝{RESET}\n")

    # ── Step 1: Kill old servers ──────────────────────────────────────────
    print(f"{CYAN}[1/5] Killing old servers...{RESET}")
    for port in [MOCK_LLM_PORT, HIVESHIP_PORT, DASHBOARD_PORT]:
        if _port_in_use(port):
            _kill_port(port)
        else:
            print(f"  Port {port} is free")
    time.sleep(1)

    # ── Step 2: Clean stale state ─────────────────────────────────────────
    print(f"{CYAN}[2/5] Cleaning stale state...{RESET}")
    # Telemetry.jsonl and cache.jsonl are session-scoped hot logs
    # (mock_llm truncates telemetry on start). DB persists across runs.

    workspace_base = Path(os.environ.get("BASE_WORKSPACE", os.path.join(os.environ.get("TEMP", "/tmp"), "hiveship-workspace")))
    if workspace_base.exists():
        for d in workspace_base.iterdir():
            if d.is_dir():
                shutil.rmtree(d, ignore_errors=True)
        print(f"  Cleared {workspace_base}")

    # ── Step 3: Start servers ─────────────────────────────────────────────
    print(f"{CYAN}[3/5] Starting servers...{RESET}")

    python = sys.executable

    # Env vars for HiveShip
    env = os.environ.copy()
    env["OLLAMA_BASE_URL"] = f"http://localhost:{MOCK_LLM_PORT}"
    env["OLLAMA_MODEL"] = "mock"
    env["DEFAULT_LLM_PROVIDER"] = "ollama"
    if "BASE_WORKSPACE" not in env:
        env["BASE_WORKSPACE"] = str(Path(env.get("TEMP", "/tmp")) / "hiveship-workspace")

    # Check required env vars
    if not env.get("GITHUB_TOKEN"):
        print(f"{RED}  ERROR: GITHUB_TOKEN env var not set. Set it before running.{RESET}")
        sys.exit(1)
    if not env.get("WEBHOOK_SECRET"):
        env["WEBHOOK_SECRET"] = "test-secret"

    # Force UTF-8 for child process stdout/stderr (Windows cp1252 breaks on box chars)
    env["PYTHONIOENCODING"] = "utf-8"

    # Log files for server output
    logs_dir = CLIENT_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_mock = open(logs_dir / "mock_llm.log", "w", encoding="utf-8")
    log_hive = open(logs_dir / "hiveship.log", "w", encoding="utf-8")
    log_dash = open(logs_dir / "dashboard.log", "w", encoding="utf-8")

    # Start mock LLM
    mock_proc = subprocess.Popen(
        [python, str(CLIENT_DIR / "mock_llm.py"), "--port", str(MOCK_LLM_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_mock, stderr=log_mock,
        **_POPEN_FLAGS,
    )
    print(f"  Mock LLM     → PID {mock_proc.pid} (port {MOCK_LLM_PORT})")

    # Start HiveShip
    hiveship_proc = subprocess.Popen(
        [python, "-m", "uvicorn", "hiveship.app:app", "--host", "0.0.0.0", "--port", str(HIVESHIP_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_hive, stderr=log_hive,
        **_POPEN_FLAGS,
    )
    print(f"  HiveShip     → PID {hiveship_proc.pid} (port {HIVESHIP_PORT})")

    # Start dashboard
    dash_proc = subprocess.Popen(
        [python, str(DASHBOARD_DIR / "serve.py"), "--port", str(DASHBOARD_PORT)],
        cwd=str(REPO_ROOT), env=env, stdout=log_dash, stderr=log_dash,
        **_POPEN_FLAGS,
    )
    print(f"  Dashboard    → PID {dash_proc.pid} (port {DASHBOARD_PORT})")

    # Wait for all servers to be ready
    print(f"\n{CYAN}[4/5] Waiting for servers to be ready...{RESET}")
    for name, port in [("Mock LLM", MOCK_LLM_PORT), ("HiveShip", HIVESHIP_PORT), ("Dashboard", DASHBOARD_PORT)]:
        if _wait_for_port(port, timeout=20):
            print(f"  {GREEN}✓{RESET} {name} ready on port {port}")
        else:
            print(f"  {RED}✗{RESET} {name} failed to start on port {port}")
            # Show log for debugging
            log_map = {"Mock LLM": "mock_llm.log", "HiveShip": "hiveship.log", "Dashboard": "dashboard.log"}
            log_file = logs_dir / log_map.get(name, "")
            if log_file.exists():
                log_hive.flush(); log_mock.flush(); log_dash.flush()
                content = log_file.read_text(encoding="utf-8", errors="replace")
                if content.strip():
                    print(f"  {DIM}--- {log_file.name} ---{RESET}")
                    for line in content.strip().splitlines()[-15:]:
                        print(f"  {DIM}{line}{RESET}")
            print(f"{RED}Aborting. Check dashboard/logs/ for full output.{RESET}")
            sys.exit(1)

    # ── Step 4: Trigger job ───────────────────────────────────────────────
    print(f"\n{CYAN}[5/5] Triggering job...{RESET}")
    print(f"  Goal: {goal[:100]}{'...' if len(goal)>100 else ''}")

    result = _http_post(f"http://localhost:{HIVESHIP_PORT}/teams-trigger", {
        "text": goal,
        "llm_provider": "ollama",
    })

    job_id = result["job_id"]
    print(f"  {GREEN}✓{RESET} Job {BOLD}{job_id}{RESET} accepted")

    # ── Done — print instructions ─────────────────────────────────────────
    print(f"\n{BOLD}{GOLD}{'═'*60}{RESET}")
    print(f"{BOLD}{GOLD}  All servers running. Job {job_id} in progress.{RESET}")
    print(f"{BOLD}{GOLD}{'═'*60}{RESET}")
    print(f"""
  {BOLD}Dashboard:{RESET}    http://localhost:{DASHBOARD_PORT}
  {BOLD}Mock LLM:{RESET}     http://localhost:{MOCK_LLM_PORT}
  {BOLD}Job status:{RESET}   http://localhost:{HIVESHIP_PORT}/status/{job_id}

  {BOLD}Prompt-answer loop:{RESET}
    Poll:   GET  http://localhost:{MOCK_LLM_PORT}/pending
    Answer: POST http://localhost:{MOCK_LLM_PORT}/respond
            Body: {{"response": "your answer here"}}

  {BOLD}Check job status:{RESET}
    GET http://localhost:{HIVESHIP_PORT}/status/{job_id}
""")

    print(f"{GREEN}Waiting for first LLM call...{RESET}", end="", flush=True)
    for _ in range(60):
        try:
            pending = _http_get(f"http://localhost:{MOCK_LLM_PORT}/pending")
            if pending.get("pending"):
                print(f" {GREEN}ready!{RESET}")
                print(f"\n  First prompt (call #{pending['call_id']}, schema: {pending.get('schema', 'text')}):")
                print(f"  {DIM}{pending.get('prompt', '')[:200]}...{RESET}\n")
                break
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1)
    else:
        print(f"\n{RED}  Timeout waiting for first LLM call. Check HiveShip logs.{RESET}")


if __name__ == "__main__":
    main()
