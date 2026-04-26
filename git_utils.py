import json
import logging
import os
import subprocess
import urllib.error
import urllib.request
from typing import Optional

from config import _GIT_AUTH_HEADER, GITHUB_PAT

logger = logging.getLogger(__name__)


def run_git(*args, cwd=None, timeout: int = 120):
    """Run a git command with Basic-auth header injection — PAT never on disk."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    git_args = ["git", "-c", f"http.extraHeader={_GIT_AUTH_HEADER}"] + list(args)
    try:
        return subprocess.run(
            git_args, cwd=cwd, check=True, timeout=timeout,
            capture_output=True, text=True, env=env,
        )
    except subprocess.CalledProcessError as e:
        safe_cmd = [
            arg if "Authorization" not in str(arg) else "http.extraHeader=[REDACTED]"
            for arg in e.cmd
        ]
        logger.error(f"Git failed: {safe_cmd}\nstderr: {e.stderr}")
        raise


def github_api_request(method: str, url: str, payload: Optional[dict] = None) -> dict:
    """Make an authenticated GitHub REST API call."""
    headers = {
        "Authorization": f"Bearer {GITHUB_PAT}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "SDLC-Bot",
    }
    data = None
    if payload:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        logger.error(f"GitHub API {method} {url} failed: {e.read().decode()}")
        raise
