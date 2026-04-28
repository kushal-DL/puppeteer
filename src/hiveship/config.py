import base64
import logging
import os
import pathlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Credentials & identity ────────────────────────────────────────────────────
GEMINI_KEY     = os.environ.get("GEMINI_API_KEY")
GITHUB_PAT     = os.environ.get("GITHUB_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
DEFAULT_REPO_OWNER = os.environ.get("REPO_OWNER", "")
DEFAULT_REPO_NAME  = os.environ.get("REPO_NAME", "")
BASE_BRANCH    = os.environ.get("BASE_BRANCH", "develop")
BOT_USERNAME   = os.environ.get("BOT_USERNAME", "")
BOT_MENTION    = "@sdlc-bot"
BOT_COMMENT_PREFIX = "\U0001f916"  # 🤖

# ── Test / dev endpoints ──────────────────────────────────────────────────────
ENABLE_TEST_ENDPOINTS = os.environ.get(
    "ENABLE_TEST_ENDPOINTS", ""
).strip().lower() in ("1", "true", "yes")

# ── Alternative LLM (Ollama / OpenAI-compat) ─────────────────────────────────
OLLAMA_BASE_URL      = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY       = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_MODEL         = os.environ.get("OLLAMA_MODEL", "llama3")
DEFAULT_LLM_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "gemini")

# ── Fast-fail on missing critical vars ───────────────────────────────────────
_TESTING = os.environ.get("TESTING", "").strip().lower() in ("1", "true", "yes")

if not _TESTING:
    if not GITHUB_PAT or not WEBHOOK_SECRET:
        raise RuntimeError("Critical env vars missing: GITHUB_TOKEN, WEBHOOK_SECRET")
    if not DEFAULT_REPO_OWNER or not DEFAULT_REPO_NAME:
        raise RuntimeError(
            "REPO_OWNER and REPO_NAME must be set in .env (or passed per-request)."
        )
    if not GEMINI_KEY and not os.environ.get("OLLAMA_BASE_URL"):
        raise RuntimeError(
            "No LLM provider configured. Set GEMINI_API_KEY or OLLAMA_BASE_URL."
        )

# GitHub git HTTPS uses Basic auth.  base64("x-access-token:<PAT>") is the
# standard PAT credential encoding — never written to disk.
_GIT_AUTH_HEADER = (
    "Authorization: Basic "
    + base64.b64encode(f"x-access-token:{GITHUB_PAT}".encode()).decode()
)

# ── Pipeline constants ────────────────────────────────────────────────────────
BASE_WORKSPACE    = pathlib.Path(os.environ.get("BASE_WORKSPACE", "/app/workspace"))
BLOCKED_PATHS     = {".github", ".git", ".env"}
ARTIFACT_CHAR_LIMIT  = 12_000
MAX_READ_FILES    = 10
READ_BUDGET       = 30_000
MAX_REVIEW_CYCLES = 2

# DAG execution limits
MAX_DYNAMIC_AGENTS   = 6
MAX_BLOCKS_PER_AGENT = 2

# Context compression
COMPRESSION_TARGET = int(os.environ.get("COMPRESSION_TARGET", "30000"))

# Three-tier output capping
AGENT_OUTPUT_CAP   = int(os.environ.get("AGENT_OUTPUT_CAP", str(ARTIFACT_CHAR_LIMIT)))
DAG_TURN_BUDGET    = int(os.environ.get("DAG_TURN_BUDGET", "200000"))

KEY_FILES = [
    "README.md", "requirements.txt", "setup.py", "pyproject.toml",
    "package.json", "tsconfig.json",
    "Cargo.toml",
    "pom.xml", "build.gradle",
    "go.mod",
    "Makefile", "docker-compose.yml",
]

# ACA DEPLOYMENT NOTE: Background jobs run in threads inside this container.
# On the ACA Consumption workload profile, CPU is throttled to ~zero once the
# active HTTP request count drops to zero — which freezes background threads.
# Set minReplicas >= 1 AND cpuAllocation: Always, or use a Dedicated profile.
logger.warning(
    "ACA: Ensure cpuAllocation=Always (or Dedicated profile) to prevent "
    "background job starvation."
)
