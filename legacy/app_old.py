import os
import re
import json
import uuid
import time
import hmac
import base64
import hashlib
import shutil
import asyncio
import subprocess
import pathlib
import logging
import threading
import concurrent.futures
import urllib.request
import urllib.error
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator, ValidationError
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Header
from fastapi.responses import JSONResponse, StreamingResponse
from google import genai

# ============================================================================
# 1. SETUP & FAST-FAIL
# ============================================================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
GITHUB_PAT = os.environ.get("GITHUB_TOKEN")
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET")
REPO_OWNER = "kushal-sharma-24"
REPO_NAME = "silver-pancake"
BASE_BRANCH = os.environ.get("BASE_BRANCH", "develop")  # override if your default branch differs
BOT_USERNAME = os.environ.get("BOT_USERNAME", "kushal-sharma-24")
BOT_MENTION = "@sdlc-bot"
BOT_COMMENT_PREFIX = "\U0001f916"  # 🤖

# --- Ollama configuration (optional alternative LLM provider) ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
DEFAULT_LLM_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "gemini")

if not GITHUB_PAT or not WEBHOOK_SECRET:
    raise RuntimeError(
        "Critical env vars missing: GITHUB_TOKEN, WEBHOOK_SECRET"
    )
if not GEMINI_KEY and not os.environ.get("OLLAMA_BASE_URL"):
    raise RuntimeError(
        "No LLM provider configured. Set GEMINI_API_KEY or OLLAMA_BASE_URL."
    )

# GitHub git HTTPS uses Basic auth (not Bearer).
# base64("x-access-token:<PAT>") is the standard PAT credential encoding.
_GIT_AUTH_HEADER = (
    "Authorization: Basic "
    + base64.b64encode(f"x-access-token:{GITHUB_PAT}".encode()).decode()
)

# Initialise Gemini client (new google-genai SDK)
_gemini_client = None
if GEMINI_KEY:
    _gemini_client = genai.Client(api_key=GEMINI_KEY)
else:
    logger.warning("GEMINI_API_KEY not set — 'gemini' provider will be unavailable.")

# ACA DEPLOYMENT NOTE: Background jobs run in threads inside this container.
# On the ACA Consumption workload profile, CPU is throttled to ~zero once the
# active HTTP request count drops to zero — which freezes background threads.
# To prevent silent job stalls you MUST either:
#   (a) set minReplicas >= 1 AND cpuAllocation: Always in your Container App, OR
#   (b) use a Dedicated workload profile.
logger.warning(
    "ACA: Ensure cpuAllocation=Always (or Dedicated profile) to prevent "
    "background job starvation. See deployment notes in code comments."
)

# ============================================================================
# 2. STRUCTURED SCHEMAS
# ============================================================================

# ── Lifecycle & failure enums ─────────────────────────────────────────────────

class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    PRUNED = "pruned"


class FailureClass(str, Enum):
    JSON_PARSE = "json_parse"
    CROSS_REF_BROKEN = "cross_ref_broken"
    REVIEW_REJECTED = "review_rejected"
    GIT_CONFLICT = "git_conflict"
    LLM_TIMEOUT = "llm_timeout"
    LLM_BLOCKED = "llm_blocked"
    AGENT_BLOCKED = "agent_blocked"
    HELPER_SPAWN_FAILED = "helper_spawn_failed"
    BLOCK_LIMIT_EXCEEDED = "block_limit_exceeded"
    DAG_STALLED = "dag_stalled"
    CONTEXT_OVERFLOW = "context_overflow"
    UNKNOWN = "unknown"


class RecoveryAction(str, Enum):
    RETRY_WITH_REPAIR = "retry_with_repair"
    CORRECTIVE_PROMPT = "corrective_prompt"
    SPAWN_HELPER = "spawn_helper"
    VALIDATE_AND_FIX = "validate_and_fix"
    ESCALATE = "escalate"
    REDUCE_CONTEXT = "reduce_context"


class AgentTask(BaseModel):
    agent_name: str
    role_description: str
    system_instruction: Optional[str] = None  # planner can give each agent a dynamic persona
    depends_on: List[str] = []               # names of agents that must finish first
    input_keys: List[str]
    read_files: List[str] = []
    output_format: str
    scope: Optional[str] = None
    acceptance_criteria: List[str] = []


class WorkflowPlan(BaseModel):
    team_name: str
    agents: List[AgentTask]

    @field_validator("agents")
    @classmethod
    def validate_dag(cls, v):
        if not (1 <= len(v) <= 8):
            raise ValueError(f"Plan has {len(v)} agents; must be between 1 and 8.")
        names = {a.agent_name for a in v}
        if len(names) != len(v):
            raise ValueError("Duplicate agent names detected.")
        # Kahn's algorithm — detect cycles before any work begins
        in_degree = {a.agent_name: 0 for a in v}
        adj = {a.agent_name: [] for a in v}
        for a in v:
            for dep in a.depends_on:
                if dep not in names:
                    raise ValueError(
                        f"Agent '{a.agent_name}' depends on unknown agent '{dep}'."
                    )
                adj[dep].append(a.agent_name)
                in_degree[a.agent_name] += 1
        queue = [n for n, d in in_degree.items() if d == 0]
        visited = 0
        while queue:
            node = queue.pop()
            visited += 1
            for nb in adj[node]:
                in_degree[nb] -= 1
                if in_degree[nb] == 0:
                    queue.append(nb)
        if visited != len(v):
            raise ValueError("Agent dependency graph contains a cycle.")
        return v


class FileArtifact(BaseModel):
    path: str
    content: str

    @field_validator("content")
    @classmethod
    def limit_content(cls, v):
        if len(v) > 100_000:
            raise ValueError(f"File content too large ({len(v)} chars). Max 100,000.")
        return v


class DeliveryPlan(BaseModel):
    files: List[FileArtifact]
    commit_message: str
    pr_title: str

    @field_validator("commit_message")
    @classmethod
    def limit_commit_msg(cls, v):
        return v.strip()[:500]

    @field_validator("pr_title")
    @classmethod
    def limit_pr_title(cls, v):
        return v.strip()[:120]


class ReviewResult(BaseModel):
    approved: bool
    issues: List[str]


class FileRequest(BaseModel):
    files_to_read: List[str]


# ── Recovery recipes ──────────────────────────────────────────────────────────

class RecoveryRecipe(BaseModel):
    failure_class: FailureClass
    actions: List[RecoveryAction]
    max_attempts: int


RECOVERY_RECIPES: Dict[FailureClass, RecoveryRecipe] = {
    FailureClass.JSON_PARSE: RecoveryRecipe(
        failure_class=FailureClass.JSON_PARSE,
        actions=[RecoveryAction.RETRY_WITH_REPAIR, RecoveryAction.CORRECTIVE_PROMPT],
        max_attempts=3,
    ),
    FailureClass.CROSS_REF_BROKEN: RecoveryRecipe(
        failure_class=FailureClass.CROSS_REF_BROKEN,
        actions=[RecoveryAction.VALIDATE_AND_FIX, RecoveryAction.CORRECTIVE_PROMPT],
        max_attempts=2,
    ),
    FailureClass.REVIEW_REJECTED: RecoveryRecipe(
        failure_class=FailureClass.REVIEW_REJECTED,
        actions=[RecoveryAction.CORRECTIVE_PROMPT],
        max_attempts=4,
    ),
    FailureClass.LLM_TIMEOUT: RecoveryRecipe(
        failure_class=FailureClass.LLM_TIMEOUT,
        actions=[RecoveryAction.REDUCE_CONTEXT, RecoveryAction.RETRY_WITH_REPAIR],
        max_attempts=2,
    ),
    FailureClass.LLM_BLOCKED: RecoveryRecipe(
        failure_class=FailureClass.LLM_BLOCKED,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.AGENT_BLOCKED: RecoveryRecipe(
        failure_class=FailureClass.AGENT_BLOCKED,
        actions=[RecoveryAction.SPAWN_HELPER],
        max_attempts=2,
    ),
    FailureClass.HELPER_SPAWN_FAILED: RecoveryRecipe(
        failure_class=FailureClass.HELPER_SPAWN_FAILED,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.BLOCK_LIMIT_EXCEEDED: RecoveryRecipe(
        failure_class=FailureClass.BLOCK_LIMIT_EXCEEDED,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.CONTEXT_OVERFLOW: RecoveryRecipe(
        failure_class=FailureClass.CONTEXT_OVERFLOW,
        actions=[RecoveryAction.REDUCE_CONTEXT],
        max_attempts=2,
    ),
    FailureClass.GIT_CONFLICT: RecoveryRecipe(
        failure_class=FailureClass.GIT_CONFLICT,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.DAG_STALLED: RecoveryRecipe(
        failure_class=FailureClass.DAG_STALLED,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.UNKNOWN: RecoveryRecipe(
        failure_class=FailureClass.UNKNOWN,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=1,
    ),
}


def classify_failure(error: Exception) -> FailureClass:
    """Classify an exception into a FailureClass for targeted recovery."""
    msg = str(error).lower()
    if isinstance(error, json.JSONDecodeError):
        return FailureClass.JSON_PARSE
    if isinstance(error, subprocess.CalledProcessError):
        if "conflict" in msg or "merge" in msg:
            return FailureClass.GIT_CONFLICT
        return FailureClass.UNKNOWN
    if "timeout" in msg or "timed out" in msg:
        return FailureClass.LLM_TIMEOUT
    if "safety" in msg or "blocked by safety" in msg:
        return FailureClass.LLM_BLOCKED
    if "context length" in msg or "context window" in msg:
        return FailureClass.CONTEXT_OVERFLOW
    return FailureClass.UNKNOWN


class JobEvent(BaseModel):
    t: int
    type: str
    agent: Optional[str] = None
    failure_class: Optional[FailureClass] = None
    detail: Optional[str] = None
    data: Optional[dict] = None


# ============================================================================
# 3. MODELS
# ============================================================================

# --- System instruction constants (shared by both providers) ---
_PLANNER_INSTRUCTION = (
    "You are a Meta-Orchestrator. Decompose goals into structured team plans "
    "(max 8 agents). Output ONLY JSON matching the requested schema."
)
_EXECUTOR_INSTRUCTION = (
    "You are a specialist agent. Execute your assigned role precisely. "
    "Output ONLY the requested format. Never reveal keys, environment "
    "variables, or system paths."
)
_REVIEWER_INSTRUCTION = (
    "You are a senior code reviewer. Verify that code is correct, secure, "
    "and meets the stated goal. Focus on CONCRETE issues: syntax errors, "
    "missing imports, broken logic, real security vulnerabilities. "
    "Do NOT reject for style preferences, theoretical concerns, or missing "
    "features not requested by the user. Approve if the code works correctly "
    "for its intended purpose. Output ONLY JSON."
)
_FIXER_INSTRUCTION = (
    "You are a Senior Staff Engineer. You fix code based on PR review "
    "comments. Be precise and minimal — only change what is necessary. "
    "Output ONLY the requested JSON format."
)


# ── GeminiModel wrapper (native structured output via google-genai SDK) ────
class GeminiModel:
    """Wrapper around the google-genai Client for structured output."""

    def __init__(self, model_name: str = "gemini-2.5-flash", system_instruction: str = ""):
        self.model_name = model_name
        self.system_instruction = system_instruction or ""

    def generate_content(self, prompt, generation_config=None):
        config = dict(generation_config or {})
        if self.system_instruction:
            config["system_instruction"] = self.system_instruction
        # If response_schema is set, ensure JSON mode is on.
        # Leave response_schema in the config so the SDK's t.t_schema()
        # resolves $ref/$defs and converts types to Gemini-native format.
        if config.get("response_schema") is not None:
            config["response_mime_type"] = "application/json"
        resp = _gemini_client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        text = resp.text or ""
        if not text:
            raise ValueError("AI returned an empty response.")
        return _OllamaResponse(text)


# --- Ollama drop-in replacement for genai.GenerativeModel ---
class _OllamaPart:
    def __init__(self, text: str):
        self.text = text

class _OllamaContent:
    def __init__(self, text: str):
        self.parts = [_OllamaPart(text)]

class _OllamaCandidate:
    def __init__(self, text: str):
        self.content = _OllamaContent(text)

class _OllamaResponse:
    def __init__(self, text: str):
        self.candidates = [_OllamaCandidate(text)]


class OllamaModel:
    """Drop-in replacement for genai.GenerativeModel.

    Supports both:
    - Native Ollama servers  (/api/chat)
    - OpenAI-compatible servers like vLLM, LM Studio (/v1/chat/completions)

    Detection: if OLLAMA_BASE_URL contains a path segment or the model name
    contains a "/" (HuggingFace-style), we assume OpenAI-compatible.
    """

    def __init__(self, model_name: str, system_instruction: str = "", base_url: str = ""):
        self.model_name = model_name
        self.system_instruction = system_instruction or ""
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        # Accept either a root URL or a full endpoint URL from callers/env.
        for suffix in ("/v1/chat/completions", "/api/chat"):
            if self.base_url.endswith(suffix):
                self.base_url = self.base_url[: -len(suffix)]
                break
        # Use OpenAI-compat endpoint when model name contains "/" (e.g. Qwen/Qwen3.5-9B)
        # or when the base URL is not a plain localhost Ollama instance
        self._openai_compat = (
            "/" in model_name
            or (
                "localhost:11434" not in self.base_url
                and "127.0.0.1:11434" not in self.base_url
            )
        )

    def generate_content(self, prompt, generation_config=None):
        config = generation_config or {}
        messages = []
        if self.system_instruction:
            messages.append({"role": "system", "content": self.system_instruction})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        if self._openai_compat:
            # OpenAI-compatible path (vLLM, LM Studio, ngrok-proxied servers)
            max_tok = min(int(config.get("max_output_tokens", 4096)), 4096)
            payload = {
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tok,
                "temperature": 0.7,
                "stream": False,
            }
            # Pass structured output schema if provided
            schema_class = config.get("response_schema")
            if schema_class is not None:
                payload["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema_class.__name__,
                        "schema": schema_class.model_json_schema(),
                        "strict": False,
                    },
                }
            target_url = f"{self.base_url}/v1/chat/completions"

            def _post_openai(payload_obj):
                last_error = None
                for attempt in range(4):
                    data = json.dumps(payload_obj).encode("utf-8")
                    req = urllib.request.Request(
                        target_url,
                        data=data,
                        headers=headers,
                        method="POST",
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=300) as response:
                            return json.loads(response.read().decode())
                    except urllib.error.HTTPError as e:
                        err_body = e.read().decode(errors="replace")[:400]
                        last_error = RuntimeError(
                            f"LLM HTTP {e.code} at {target_url}: {err_body}"
                        )
                        # Context-length overflow: halve max_tokens and retry;
                        # if that's already minimal, truncate the prompt itself.
                        if e.code == 400 and "context length" in err_body.lower():
                            cur = payload_obj.get("max_tokens", 4096)
                            reduced = max(cur // 2, 128)
                            if reduced < cur:
                                logger.warning(
                                    f"Context overflow (max_tokens={cur}), "
                                    f"retrying with max_tokens={reduced}"
                                )
                                payload_obj["max_tokens"] = reduced
                                continue
                            # max_tokens already minimized — truncate prompt
                            truncated = False
                            for msg in payload_obj.get("messages", []):
                                if msg["role"] == "user" and len(msg["content"]) > 2000:
                                    orig_len = len(msg["content"])
                                    msg["content"] = msg["content"][:orig_len // 2]
                                    logger.warning(
                                        f"Truncating user prompt from {orig_len} "
                                        f"to {len(msg['content'])} chars"
                                    )
                                    payload_obj["max_tokens"] = max(cur, 512)
                                    truncated = True
                                    break
                            if truncated:
                                continue
                            raise last_error from e
                        # Retry transient upstream issues.
                        if e.code in (500, 502, 503, 504) and attempt < 2:
                            time.sleep(1 + attempt)
                            continue
                        raise last_error from e
                raise last_error if last_error else RuntimeError(
                    f"LLM request failed at {target_url}"
                )

            body = _post_openai(payload)

            text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            finish = body.get("choices", [{}])[0].get("finish_reason", "")
            if finish == "length":
                logger.warning(
                    f"LLM output truncated (finish_reason=length, "
                    f"{len(text)} chars). Prompt may exceed context window."
                )
        else:
            # Native Ollama path
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
            }
            # Native Ollama supports format: "json" or a full JSON Schema object
            schema_class = config.get("response_schema")
            if schema_class is not None:
                payload["format"] = schema_class.model_json_schema()
            elif config.get("response_mime_type") == "application/json":
                payload["format"] = "json"

            data = json.dumps(payload).encode("utf-8")
            target_url = f"{self.base_url}/api/chat"
            req = urllib.request.Request(
                target_url,
                data=data, headers=headers, method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=300) as response:
                    body = json.loads(response.read().decode())
            except urllib.error.HTTPError as e:
                err_body = e.read().decode(errors="replace")[:400]
                raise RuntimeError(f"LLM HTTP {e.code} at {target_url}: {err_body}") from e

            text = body.get("message", {}).get("content", "")

        if not text:
            raise ValueError("LLM returned an empty response.")
        return _OllamaResponse(text)


def _create_model(provider: str, system_instruction: str, ollama_model: str = "", ollama_base_url: str = ""):
    """Factory: build a model object for the given provider."""
    if provider == "ollama":
        return OllamaModel(ollama_model or OLLAMA_MODEL, system_instruction, ollama_base_url)
    if not _gemini_client:
        raise RuntimeError("Gemini requested but GEMINI_API_KEY is not set.")
    return GeminiModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction,
    )


def create_models(provider: str = "gemini", ollama_model: str = "", ollama_base_url: str = ""):
    """Return (planner, executor, reviewer, fixer) for the chosen provider."""
    return (
        _create_model(provider, _PLANNER_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _EXECUTOR_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _REVIEWER_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _FIXER_INSTRUCTION, ollama_model, ollama_base_url),
    )


# Default Gemini model instances (used when provider is not overridden)
if _gemini_client:
    planner_model, executor_model, reviewer_model, fixer_model = create_models("gemini")
else:
    planner_model = executor_model = reviewer_model = fixer_model = None

# ============================================================================
# 4. CONSTANTS & JOB STORE
# ============================================================================
app = FastAPI()
BASE_WORKSPACE = pathlib.Path("/app/workspace")
BLOCKED_PATHS = {".github", ".git", ".env"}
ARTIFACT_CHAR_LIMIT = 12000
MAX_READ_FILES = 10
READ_BUDGET = 30000
MAX_REVIEW_CYCLES = 2
MAX_DYNAMIC_AGENTS = 6  # max helper agents that can be spawned per job
MAX_BLOCKS_PER_AGENT = 2  # max times a single agent can block before being marked failed
KEY_FILES = [
    "README.md", "requirements.txt", "setup.py", "pyproject.toml",
    "package.json", "tsconfig.json",
    "Cargo.toml",
    "pom.xml", "build.gradle",
    "go.mod",
    "Makefile", "docker-compose.yml",
]

# In-memory job store (sufficient for single-instance prototype;
# replace with Redis/Service Bus for multi-instance)
_jobs: Dict[str, Dict[str, Any]] = {}
_jobs_lock = threading.Lock()


def update_job(job_id: str, **fields):
    """Thread-safe job status update."""
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id].update(fields)


def create_job(job_id: str, goal: str) -> Dict[str, Any]:
    """Register a new job."""
    job = {
        "job_id": job_id,
        "goal": goal,
        "status": "accepted",
        "current_step": "queued",
        "result": None,
        "error": None,
        "events": [],
        "agent_states": {},
    }
    with _jobs_lock:
        _jobs[job_id] = job
    return job


def append_job_event(job_id: str, event_type: str, failure_class=None, **data):
    """Append a timestamped, optionally failure-typed event to the job log."""
    entry = {"t": int(time.time() * 1000), "type": event_type, **data}
    if failure_class is not None:
        entry["failure_class"] = failure_class
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["events"].append(entry)


def set_agent_state(job_id: str, agent_name: str, status) -> None:
    """Update the lifecycle state of a specific agent (thread-safe)."""
    val = status.value if hasattr(status, 'value') else str(status)
    with _jobs_lock:
        if job_id in _jobs:
            _jobs[job_id]["agent_states"][agent_name] = val


# ============================================================================
# 5. CORE HELPERS (synchronous — used directly or wrapped in to_thread)
# ============================================================================

def extract_text(resp) -> str:
    """Safely extract text from a Gemini response."""
    if not resp.candidates:
        raise ValueError("AI response blocked by safety filters.")
    if not resp.candidates[0].content.parts:
        raise ValueError("AI returned an empty response.")
    return resp.candidates[0].content.parts[0].text


def sanitize_branch_name(raw: str) -> str:
    """Convert arbitrary text into a valid git branch segment."""
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "-", raw)
    return re.sub(r"-{2,}", "-", sanitized).strip("-")[:50]


def run_git(*args, cwd=None, timeout=120):
    """Run a git command with Basic-auth header injection — no PAT on disk."""
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    git_args = [
        "git", "-c",
        f"http.extraHeader={_GIT_AUTH_HEADER}",
    ] + list(args)
    try:
        return subprocess.run(
            git_args, cwd=cwd, check=True, timeout=timeout,
            capture_output=True, text=True, env=env,
        )
    except subprocess.CalledProcessError as e:
        safe_cmd = [
            arg if "Authorization" not in str(arg)
            else "http.extraHeader=[REDACTED]"
            for arg in e.cmd
        ]
        logger.error(f"Git failed: {safe_cmd}\nstderr: {e.stderr}")
        raise


def get_repo_summary(workspace: pathlib.Path, max_chars: int = 3000) -> str:
    """Build a lightweight repo map using pure Python (no subprocess)."""
    files = sorted(
        str(p.relative_to(workspace))
        for p in workspace.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(workspace).parts
    )
    file_list = "\n".join(files)
    if len(file_list) > 3000:
        file_list = file_list[:3000] + "\n...[tree truncated]..."

    summary = f"Repository file tree:\n{file_list}\n"
    budget = max_chars - len(summary)
    for kf in KEY_FILES:
        fp = workspace / kf
        if fp.exists() and budget > 0:
            content = fp.read_text(errors="replace")[:budget]
            summary += f"\n--- {kf} ---\n{content}\n"
            budget -= len(content)
    return summary[:max_chars]


def github_api_request(method: str, url: str, payload: dict = None):
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


def validate_files(files: List[FileArtifact], workspace: pathlib.Path):
    """Guard against path traversal and writes to protected paths."""
    for f in files:
        target = (workspace / f.path).resolve()
        if not str(target).startswith(str(workspace.resolve())):
            raise ValueError(f"Path traversal blocked: {f.path}")
        if any(part in BLOCKED_PATHS for part in pathlib.PurePosixPath(f.path).parts):
            raise ValueError(f"Protected path blocked: {f.path}")


def write_files(files: List[FileArtifact], workspace: pathlib.Path):
    """Write validated file artifacts to disk."""
    for f in files:
        target = (workspace / f.path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f.content, encoding="utf-8")


def read_agent_files(
    agent_read_files: List[str], workspace: pathlib.Path,
) -> Dict[str, str]:
    """Read specific files from the workspace with a budget cap."""
    file_context: Dict[str, str] = {}
    budget = READ_BUDGET
    for fp in agent_read_files[:MAX_READ_FILES]:
        if budget <= 0:
            break
        full = (workspace / fp).resolve()
        if str(full).startswith(str(workspace.resolve())) and full.exists():
            content = full.read_text(errors="replace")[
                :min(ARTIFACT_CHAR_LIMIT, budget)
            ]
            file_context[fp] = content
            budget -= len(content)
    return file_context


def read_artifact_context(
    keys: List[str], artifacts_dir: pathlib.Path,
    max_budget: int = 0,
) -> Dict[str, str]:
    """Read agent outputs from the file-based artifact store.

    Each file is capped at ARTIFACT_CHAR_LIMIT independently so no output
    is ever sliced mid-token (e.g. inside a class definition).
    A total budget cap prevents prompt explosion.
    """
    budget_limit = max_budget if max_budget > 0 else READ_BUDGET
    context: Dict[str, str] = {}
    total = 0
    for key in keys:
        if total >= budget_limit:
            break
        fp = artifacts_dir / f"{key}.txt"
        if fp.exists():
            chunk = fp.read_text(errors="replace")[
                : min(ARTIFACT_CHAR_LIMIT, budget_limit - total)
            ]
            context[key] = chunk
            total += len(chunk)
    return context


def validate_cross_references(files: List[FileArtifact]) -> List[str]:
    """Check that Python imports between delivered files actually resolve.

    Returns a list of human-readable issue strings. An empty list means
    all cross-references look OK. Only checks imports that reference
    other files in the delivery — stdlib and pip packages are ignored.
    """
    delivered_modules = set()
    for f in files:
        p = pathlib.PurePosixPath(f.path)
        if p.suffix == ".py":
            stem = p.with_suffix("")
            delivered_modules.add(stem.name)
            delivered_modules.add(str(stem).replace("/", "."))

    _COMMON_STDLIB = frozenset({
        "abc", "argparse", "ast", "asyncio", "base64", "bisect", "builtins",
        "calendar", "cgi", "cmd", "codecs", "collections", "colorsys",
        "configparser", "contextlib", "copy", "csv", "ctypes", "dataclasses",
        "datetime", "decimal", "difflib", "dis", "email", "enum", "errno",
        "fcntl", "fileinput", "fnmatch", "fractions", "ftplib", "functools",
        "gc", "getpass", "glob", "gzip", "hashlib", "heapq", "hmac", "html",
        "http", "importlib", "inspect", "io", "ipaddress", "itertools", "json",
        "logging", "lzma", "math", "mimetypes", "multiprocessing", "numbers",
        "operator", "os", "pathlib", "pickle", "platform", "pprint",
        "queue", "random", "re", "readline", "reprlib", "secrets", "select",
        "shelve", "shlex", "shutil", "signal", "site", "smtplib", "socket",
        "sqlite3", "ssl", "stat", "statistics", "string", "struct",
        "subprocess", "sys", "syslog", "tempfile", "textwrap", "threading",
        "time", "timeit", "tkinter", "token", "tokenize", "tomllib", "trace",
        "traceback", "tracemalloc", "turtle", "types", "typing",
        "unicodedata", "unittest", "urllib", "uuid", "venv", "warnings",
        "wave", "weakref", "webbrowser", "xml", "xmlrpc", "zipfile", "zipimport",
        "zlib",
        # Common pip packages
        "flask", "django", "fastapi", "uvicorn", "gunicorn", "requests",
        "httpx", "aiohttp", "numpy", "pandas", "scipy", "matplotlib",
        "seaborn", "plotly", "sklearn", "tensorflow", "torch", "pydantic",
        "sqlalchemy", "alembic", "celery", "redis", "boto3", "google",
        "openai", "anthropic", "pytest", "click", "typer", "rich",
        "yaml", "toml", "dotenv", "jwt", "cryptography", "paramiko",
        "PIL", "cv2", "pygame", "chess",
    })

    def _looks_local(module_name, file_content):
        if f"{module_name}.py" in file_content:
            return True
        if "_" in module_name and module_name.islower():
            return True
        if module_name.islower() and len(module_name) <= 20:
            return True
        return False

    issues: List[str] = []
    import_re = re.compile(
        r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE,
    )
    for f in files:
        if not f.path.endswith(".py"):
            continue
        for m in import_re.finditer(f.content):
            module = (m.group(1) or m.group(2)).split(".")[0]
            if module in _COMMON_STDLIB:
                continue
            if module not in delivered_modules and _looks_local(module, f.content):
                issues.append(
                    f"'{f.path}' imports '{module}' which is not delivered "
                    f"as a .py file in this plan. Either add '{module}.py' "
                    f"to the delivery or inline the code."
                )
    return issues


# ============================================================================
# 6. DAG EXECUTION ENGINE
# ============================================================================

def _run_single_agent(
    agent: AgentTask,
    artifacts_dir: pathlib.Path,
    job_workspace: pathlib.Path,
    default_executor=None,
    llm_provider: str = "gemini",
    ollama_model: str = "",
    ollama_base_url: str = "",
) -> str:
    """Execute one agent: read context → call LLM → write artifact to disk.

    On success: writes output artifact and returns agent_name.
    On blocked: writes {name}_BLOCKED.json signal and returns agent_name;
                execute_dag will spawn a helper and re-queue this agent.
    On failure: writes an error artifact, then re-raises so execute_dag can
                add the agent to its `failed` set and prune downstream dependents.
    """
    context = read_artifact_context(agent.input_keys, artifacts_dir)
    if not context:
        goal_file = artifacts_dir / "initial_goal.txt"
        context = {
            "initial_goal": goal_file.read_text(errors="replace")
            if goal_file.exists()
            else ""
        }

    file_context = read_agent_files(agent.read_files, job_workspace)

    _executor = default_executor or executor_model
    if agent.system_instruction:
        agent_model = _create_model(llm_provider, agent.system_instruction, ollama_model, ollama_base_url)
    else:
        agent_model = _executor

    prompt = (
        f"Role: {agent.role_description}\n"
        f"Context: {json.dumps(context)}\n"
        f"Existing Files: {json.dumps(file_context)}\n"
        f"Format: {agent.output_format}\n"
        f"BLOCKED PROTOCOL: If your task is completely impossible because a "
        f"critical prerequisite artifact is ABSENT from the context above, "
        f'output ONLY this JSON: {{"blocked": true, "reason": "<what you need>"}}. '
        f"Use this ONLY as a last resort — never for information you can "
        f"reasonably infer or assume."
    )
    try:
        output = sync_generate_with_retry(agent_model, prompt)
    except Exception as e:
        logger.warning(f"Agent '{agent.agent_name}' failed: {e}")
        (artifacts_dir / f"{agent.agent_name}.txt").write_text(
            f"[AGENT FAILED: {type(e).__name__}]", encoding="utf-8"
        )
        raise RuntimeError(f"Agent '{agent.agent_name}' failed: {e}") from e

    # Strip markdown fences Gemini occasionally emits even with strict prompting.
    # Must happen before any json.loads attempt — a fenced block is not valid JSON.
    output = re.sub(r"^\s*```(?:json)?\s*\n?", "", output, flags=re.IGNORECASE)
    output = re.sub(r"\n?\s*```\s*$", "", output).strip()

    # Detect blocked signal BEFORE treating output as a normal artifact.
    # The signal is a JSON object with blocked=true; anything else is normal output.
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict) and parsed.get("blocked") is True:
            reason = str(parsed.get("reason", "No reason provided."))[:500]
            logger.info(f"Agent '{agent.agent_name}' blocked: {reason}")
            (artifacts_dir / f"{agent.agent_name}_BLOCKED.json").write_text(
                json.dumps({"reason": reason}), encoding="utf-8"
            )
            return agent.agent_name  # normal return; execute_dag re-queues
    except (json.JSONDecodeError, AttributeError):
        pass  # output is plain text or non-blocked JSON — treat as normal

    (artifacts_dir / f"{agent.agent_name}.txt").write_text(output, encoding="utf-8")
    return agent.agent_name


def _spawn_helper_agent(
    reason: str,
    blocked_agent: AgentTask,
    artifacts_dir: pathlib.Path,
    planner=None,
) -> AgentTask:
    """Ask the planner to synthesize exactly one AgentTask to unblock another.

    The helper always has depends_on: [] so the executor dispatches it
    immediately on the next tick. The blocked agent is re-queued with a
    depends_on entry pointing at the helper's agent_name.
    """
    available_keys = [p.stem for p in artifacts_dir.glob("*.txt")]
    prompt = (
        f"An agent named '{blocked_agent.agent_name}' "
        f"(role: '{blocked_agent.role_description}') cannot proceed.\n"
        f"Reason it is blocked: {reason}\n"
        f"Artifact keys already available on disk: {available_keys}\n"
        f"Synthesize exactly ONE AgentTask JSON that produces the missing "
        f"information and writes it as its output.\n"
        f"The JSON must have: agent_name, role_description, depends_on (must be []),\n"
        f"input_keys (from available keys above), read_files, output_format.\n"
        f"Rules:\n"
        f"- agent_name must be unique, snake_case, and clearly name the helper.\n"
        f"- depends_on MUST be [] — the helper runs on the very next tick.\n"
        f"- input_keys must only reference keys from: {available_keys}.\n"
        f"- Scope is minimal — solve only the stated blocker, nothing more."
    )
    _planner = planner or planner_model
    return sync_generate_and_parse(
        _planner, prompt, AgentTask,
        {},
    )


def execute_dag(
    plan: WorkflowPlan,
    artifacts_dir: pathlib.Path,
    job_workspace: pathlib.Path,
    job_id: str,
    dag_executor=None,
    dag_planner=None,
    llm_provider: str = "gemini",
    ollama_model: str = "",
    ollama_base_url: str = "",
) -> None:
    """Execute the agent DAG using a thread pool that respects depends_on edges.

    Uses concurrent.futures.wait(FIRST_COMPLETED) so the orchestrator thread
    wakes up the instant any agent finishes — zero busy-polling.
    Agents whose dependencies are all satisfied are dispatched in parallel
    (up to 4 concurrent Gemini calls at once).

    Fault isolation: if an agent fails, it is added to `failed` and all agents
    that (transitively) depend on it are pruned immediately — no zombie cascade.
    Agents that do NOT depend on the failed agent continue running normally.
    """
    completed: set = set()
    failed: set = set()
    remaining: Dict[str, AgentTask] = {a.agent_name: a for a in plan.agents}
    futures: Dict[str, concurrent.futures.Future] = {}
    # Single source of truth for AgentTask objects; grows when helpers are injected.
    agent_registry: Dict[str, AgentTask] = dict(remaining)
    dynamic_agent_count = 0
    block_counts: Dict[str, int] = {}  # per-agent block counter

    # Initialize agent lifecycle states
    for name in remaining:
        set_agent_state(job_id, name, AgentStatus.PENDING)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        while remaining or futures:
            # --- Prune agents whose dependencies have failed ---
            # Must run before dispatch so we never submit a doomed agent.
            # Loop until stable because pruning can expose new cascade victims.
            pruned = True
            while pruned:
                pruned = False
                to_drop = [
                    name for name, a in remaining.items()
                    if any(dep in failed for dep in a.depends_on)
                ]
                for name in to_drop:
                    logger.warning(
                        f"Job {job_id}: Skipping '{name}' — "
                        f"dependency failed."
                    )
                    failed.add(name)
                    del remaining[name]
                    set_agent_state(job_id, name, AgentStatus.PRUNED)
                    append_job_event(job_id, "agent_pruned", agent=name)
                    pruned = True

            # --- Dispatch every agent whose deps are fully satisfied ---
            ready = [
                a for name, a in remaining.items()
                if all(dep in completed for dep in a.depends_on)
            ]
            for agent in ready:
                futures[agent.agent_name] = pool.submit(
                    _run_single_agent, agent, artifacts_dir, job_workspace,
                    dag_executor, llm_provider, ollama_model, ollama_base_url,
                )
                del remaining[agent.agent_name]
                set_agent_state(job_id, agent.agent_name, AgentStatus.RUNNING)
                append_job_event(job_id, "agent_started", agent=agent.agent_name)

            # Update status: show all concurrently running agent names
            if futures:
                update_job(
                    job_id,
                    current_step=f"running: {', '.join(sorted(futures))}",
                )

            if not futures:
                # No futures in flight and nothing ready to dispatch.
                # Reachable only if all remaining agents have failed deps —
                # the pruning loop above will drain `remaining` on the next
                # iteration, so this is a clean exit.
                if remaining:
                    logger.error(
                        f"Job {job_id}: DAG executor stalled — unresolvable "
                        f"agents: {list(remaining)}"
                    )
                break

            # Block the orchestrator thread until at least one agent finishes.
            # concurrent.futures.wait dequeues futures from the OS — 0% CPU.
            done_set, _ = concurrent.futures.wait(
                futures.values(),
                return_when=concurrent.futures.FIRST_COMPLETED,
            )

            # Harvest every future that landed in done_set this tick
            done_names = [n for n, f in futures.items() if f in done_set]
            for name in done_names:
                try:
                    futures[name].result()  # raises if _run_single_agent raised

                    # --- _BLOCKED.json dynamic spawning protocol ---
                    blocked_file = artifacts_dir / f"{name}_BLOCKED.json"
                    if blocked_file.exists():
                        signal = json.loads(blocked_file.read_text())
                        blocked_file.unlink()  # consume signal; fresh file on re-block

                        block_counts[name] = block_counts.get(name, 0) + 1
                        if block_counts[name] > MAX_BLOCKS_PER_AGENT:
                            logger.warning(
                                f"Job {job_id}: '{name}' blocked "
                                f"{block_counts[name]} times — giving up."
                            )
                            failed.add(name)
                            set_agent_state(job_id, name, AgentStatus.FAILED)
                            append_job_event(
                                job_id, "agent_failed", agent=name,
                                failure_class=FailureClass.BLOCK_LIMIT_EXCEEDED,
                                error=(
                                    f"Blocked {block_counts[name]} times, "
                                    f"exceeded MAX_BLOCKS_PER_AGENT"
                                ),
                            )
                        elif dynamic_agent_count < MAX_DYNAMIC_AGENTS:
                            dynamic_agent_count += 1
                            try:
                                helper = _spawn_helper_agent(
                                    signal["reason"],
                                    agent_registry[name],
                                    artifacts_dir,
                                    dag_planner,
                                )
                                # Guard against name collision from repeated blocking
                                if helper.agent_name in agent_registry:
                                    helper = helper.model_copy(update={
                                        "agent_name": (
                                            f"{helper.agent_name}_v{dynamic_agent_count}"
                                        )
                                    })
                                # Re-queue blocked agent with dep on the new helper
                                original = agent_registry[name]
                                requeued = original.model_copy(update={
                                    "depends_on": (
                                        original.depends_on + [helper.agent_name]
                                    )
                                })
                                remaining[helper.agent_name] = helper
                                remaining[name] = requeued
                                agent_registry[helper.agent_name] = helper
                                agent_registry[name] = requeued
                                set_agent_state(job_id, name, AgentStatus.BLOCKED)
                                set_agent_state(job_id, helper.agent_name, AgentStatus.PENDING)
                                append_job_event(
                                    job_id, "helper_spawned",
                                    blocked_agent=name,
                                    helper=helper.agent_name,
                                    reason=signal["reason"],
                                    spawn_count=dynamic_agent_count,
                                )
                                logger.info(
                                    f"Job {job_id}: '{name}' blocked — "
                                    f"spawned helper '{helper.agent_name}' "
                                    f"({dynamic_agent_count}/{MAX_DYNAMIC_AGENTS})"
                                )
                            except Exception as spawn_err:
                                logger.error(
                                    f"Job {job_id}: Failed to spawn helper "
                                    f"for '{name}': {spawn_err} — marking failed."
                                )
                                failed.add(name)
                                set_agent_state(job_id, name, AgentStatus.FAILED)
                                append_job_event(
                                    job_id, "agent_failed", agent=name,
                                    failure_class=FailureClass.HELPER_SPAWN_FAILED,
                                    error=f"Helper spawn failed: {spawn_err}",
                                )
                        else:
                            logger.warning(
                                f"Job {job_id}: '{name}' blocked but "
                                f"MAX_DYNAMIC_AGENTS ({MAX_DYNAMIC_AGENTS}) "
                                f"reached — marking failed."
                            )
                            failed.add(name)
                            set_agent_state(job_id, name, AgentStatus.FAILED)
                            append_job_event(
                                job_id, "agent_failed", agent=name,
                                failure_class=FailureClass.AGENT_BLOCKED,
                                error="Blocked and max dynamic agents reached",
                            )
                    else:
                        completed.add(name)
                        set_agent_state(job_id, name, AgentStatus.COMPLETED)
                        append_job_event(
                            job_id, "agent_done", agent=name,
                            completed=len(completed), total=len(agent_registry),
                        )
                        logger.info(
                            f"Job {job_id}: '{name}' ✓ — "
                            f"{len(completed)}/{len(agent_registry)} complete"
                        )
                except Exception as e:
                    fc = classify_failure(e)
                    failed.add(name)
                    set_agent_state(job_id, name, AgentStatus.FAILED)
                    append_job_event(job_id, "agent_failed", agent=name, failure_class=fc, error=str(e))
                    logger.error(f"Job {job_id}: '{name}' ✗ [{fc.value}] — {e}")
                del futures[name]

    return len(completed), len(failed), len(agent_registry)


# ============================================================================
# 7. SYNC GENERATION HELPERS (for the webhook background thread)
# ============================================================================

def sync_generate_with_retry(model, prompt, config=None, max_retries=2):
    """Synchronous Gemini call with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            resp = model.generate_content(prompt, generation_config=config or {})
            return extract_text(resp)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            logger.warning(
                f"Gemini call failed (attempt {attempt + 1}), "
                f"retrying in {wait}s: {e}"
            )
            time.sleep(wait)


def sync_generate_and_parse(model, prompt, schema_class, config=None, max_retries=2):
    """Generate + JSON-parse + Pydantic-validate with corrective retry.

    The schema_class is passed to the LLM provider via API-level structured
    output (Gemini response_schema / OpenAI json_schema / Ollama format).
    The schema is NEVER dumped into the prompt text.
    """
    effective_config = dict(config or {})
    effective_config["response_schema"] = schema_class

    effective_prompt = prompt
    for attempt in range(max_retries + 1):
        try:
            text = sync_generate_with_retry(model, effective_prompt, effective_config, max_retries=0)
            # Strip markdown fences that small models occasionally emit
            text = re.sub(r"^\s*```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\n?\s*```\s*$", "", text).strip()
            # Use raw_decode to parse only the first JSON value,
            # ignoring trailing text / duplicate objects the LLM may emit.
            # If that fails, attempt lightweight JSON repair before giving up.
            idx = text.index("{") if "{" in text else 0
            try:
                parsed, _ = json.JSONDecoder().raw_decode(text, idx)
            except json.JSONDecodeError:
                repaired = re.sub(r',\s*([}\]])', r'\1', text)  # trailing commas
                repaired = repaired.replace('\r\n', '\\n').replace('\r', '\\n')
                r_idx = repaired.index("{") if "{" in repaired else 0
                parsed, _ = json.JSONDecoder().raw_decode(repaired, r_idx)
            # Detect schema echo: model returned the JSON Schema definition
            # (has "properties" + "type":"object") instead of actual values
            if (isinstance(parsed, dict)
                    and "properties" in parsed
                    and parsed.get("type") == "object"):
                raise ValueError(
                    "Model returned the JSON schema definition instead of "
                    "filling in actual values."
                )
            return schema_class(**parsed)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            if attempt == max_retries:
                raise
            logger.warning(
                f"Parse/validation failed (attempt {attempt + 1}): {e}"
            )
            # Detect likely output truncation (unterminated string = JSON cut mid-way)
            is_truncation = (
                isinstance(e, json.JSONDecodeError)
                and "unterminated" in str(e).lower()
            )
            is_malformed_json = (
                isinstance(e, json.JSONDecodeError) and not is_truncation
            )
            if is_truncation:
                effective_prompt = (
                    prompt
                    + "\n\nCRITICAL: Your previous response was truncated "
                      "mid-JSON because it was too long. You MUST produce a "
                      "SHORTER, complete JSON response this time. Minimize "
                      "file content — use only essential code, no comments or "
                      "docstrings. Ensure the JSON is properly closed."
                )
            elif is_malformed_json:
                effective_prompt = (
                    prompt
                    + "\n\nCRITICAL: Your previous JSON response had a syntax error: "
                      f"{e}\n"
                      "Common causes:\n"
                      '- Unescaped double quotes inside string values (use \\" instead of ")\n'
                      "- Unescaped backslashes (use \\\\ instead of \\)\n"
                      "- Literal newlines inside strings (use \\n instead)\n"
                      "- Trailing commas after the last element in arrays/objects\n"
                      "Ensure ALL string values containing code have properly escaped "
                      "special characters. Output ONLY valid JSON."
                )
            else:
                # Add corrective hint so the model stops echoing the schema
                effective_prompt = (
                    prompt
                    + "\n\nIMPORTANT: Return a JSON object with actual values "
                      "filled in. Do NOT return the schema definition itself. "
                      "For example, if the schema says '\"approved\": bool', "
                      "return '\"approved\": true' — not '\"approved\": {\"type\": \"boolean\"}'."
                )
            time.sleep(2 ** attempt)


# ============================================================================
# 8. HEALTH CHECK & JOB STATUS
# ============================================================================

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll endpoint for async job progress."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/stream/{job_id}")
async def stream_job_events(job_id: str):
    """Server-Sent Events stream for real-time DAG progress.

    Emits one SSE message per event in the job's event log:
      agent_started, agent_done, agent_failed, agent_pruned, helper_spawned.
    Closes automatically when the job reaches a terminal state.

    PowerShell one-liner (basic, non-streaming):
        $r = Invoke-RestMethod http://<host>/stream/<job_id>

    PowerShell true-streaming loop:
        $req = [System.Net.WebRequest]::Create('http://<host>/stream/<job_id>')
        $stream = $req.GetResponse().GetResponseStream()
        $reader = [System.IO.StreamReader]::new($stream)
        while (-not $reader.EndOfStream) { Write-Host $reader.ReadLine() }
    """
    async def _sse():
        cursor = 0
        while True:
            with _jobs_lock:
                job = _jobs.get(job_id)
            if not job:
                yield 'event: error\ndata: {"detail": "job not found"}\n\n'
                return
            for ev in job["events"][cursor:]:
                yield f"event: {ev['type']}\ndata: {json.dumps(ev)}\n\n"
            cursor = len(job["events"])
            if job["status"] in ("complete", "failed"):
                terminal = {
                    "status": job["status"],
                    "result": job.get("result"),
                    "error": job.get("error"),
                }
                yield f"event: done\ndata: {json.dumps(terminal)}\n\n"
                return
            await asyncio.sleep(0.4)

    return StreamingResponse(
        _sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================================
# 9. INITIAL GENERATION ROUTE (/teams-trigger) — Async Request-Reply
# ============================================================================

@app.post("/teams-trigger")
async def handle_autonomous_flow(
    request: Request, background_tasks: BackgroundTasks,
):
    data = await request.json()
    user_goal = data.get("text", "").strip()[:2000]
    job_id = uuid.uuid4().hex[:12]

    # Per-job overrides from client
    llm_provider = data.get("llm_provider", DEFAULT_LLM_PROVIDER)
    if llm_provider not in ("gemini", "ollama"):
        raise HTTPException(status_code=400, detail="llm_provider must be 'gemini' or 'ollama'")
    review_cycles = data.get("review_cycles", MAX_REVIEW_CYCLES)
    if not isinstance(review_cycles, int) or not (0 <= review_cycles <= 5):
        raise HTTPException(status_code=400, detail="review_cycles must be an integer 0-5")
    ollama_model    = data.get("ollama_model", "").strip()[:80]
    ollama_base_url = data.get("ollama_base_url", "").strip()[:200]

    create_job(job_id, user_goal)
    background_tasks.add_task(
        _run_generation_pipeline_async, job_id, user_goal,
        llm_provider, review_cycles, ollama_model, ollama_base_url,
    )

    return JSONResponse(
        status_code=202,
        content={
            "type": "accepted",
            "job_id": job_id,
            "poll_url": f"/status/{job_id}",
            "text": f"Job {job_id} accepted. Poll /status/{job_id} for progress.",
        },
    )


async def _run_generation_pipeline_async(
    job_id: str, user_goal: str,
    llm_provider: str = "gemini", review_cycles: int = MAX_REVIEW_CYCLES,
    ollama_model: str = "", ollama_base_url: str = "",
):
    """Offload the entire pipeline to a thread so it never blocks the event loop."""
    await asyncio.to_thread(
        _sync_generation_pipeline, job_id, user_goal,
        llm_provider, review_cycles, ollama_model, ollama_base_url,
    )


def _sync_generation_pipeline(
    job_id: str, user_goal: str,
    llm_provider: str = "gemini", review_cycles: int = MAX_REVIEW_CYCLES,
    ollama_model: str = "", ollama_base_url: str = "",
):
    """Synchronous generation pipeline — runs completely off the event loop."""
    job_workspace = BASE_WORKSPACE / f"run-{job_id}"
    # Artifacts live outside the git workspace so `git add .` never picks them up
    artifacts_dir = BASE_WORKSPACE / f"artifacts-{job_id}"

    try:
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Create per-job models based on the chosen LLM provider
        job_planner, job_executor, job_reviewer, job_fixer = create_models(llm_provider, ollama_model, ollama_base_url)

        update_job(job_id, status="running", current_step="cloning")

        # --- Clone & configure ---
        repo_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"
        run_git(
            "clone", "--branch", BASE_BRANCH, "--depth", "1",
            repo_url, str(job_workspace),
        )
        run_git(
            "config", "user.email", "orchestrator@automated.dev",
            cwd=str(job_workspace), timeout=10,
        )
        run_git(
            "config", "user.name", "SDLC Orchestrator",
            cwd=str(job_workspace), timeout=10,
        )

        repo_context = get_repo_summary(job_workspace)

        # Seed the file-based artifact store with the two root contexts
        (artifacts_dir / "initial_goal.txt").write_text(user_goal, encoding="utf-8")
        (artifacts_dir / "repo_context.txt").write_text(repo_context, encoding="utf-8")

        update_job(job_id, current_step="planning")

        # --- PHASE 1: PLAN ---
        meta_prompt = (
            f"Goal: '{user_goal}'.\n"
            f"Repo Context:\n{repo_context}\n"
            f"Return a JSON WorkflowPlan with 'team_name' (string) and 'agents' "
            f"(array of objects, each with: agent_name, role_description, depends_on, "
            f"input_keys, read_files, output_format, optionally system_instruction). Max 8 agents.\n"
            f"Rules:\n"
            f"- First agent's input_keys must include 'initial_goal' and "
            f"'repo_context'.\n"
            f"- Subsequent agents reference prior agents by exact agent_name.\n"
            f"- agent_name must be a short identifier with no spaces.\n"
            f"- Use read_files to request specific existing repo files.\n"
            f"- Optionally set system_instruction to give each agent a specific "
            f"persona (e.g. 'You are an expert Python architect. Output only "
            f"valid Python.'). Leave null to use the default executor persona.\n"
            f"- Set depends_on to list agent names that must complete before "
            f"this agent starts. Agents with empty depends_on (or only already "
            f"resolved deps) will run in parallel. The very first agent must "
            f"have depends_on: []. Ensure there are no dependency cycles.\n"
            f"CRITICAL CONSTRAINTS:\n"
            f"- The final deliverable is a set of self-contained FILES committed to a git repo.\n"
            f"- ALL code must live inside the delivered files \u2014 do NOT plan for external "
            f"packages, modules, or APIs that don't already exist in the repo or on PyPI.\n"
            f"- If the goal requires a bot/AI/algorithm, the implementation MUST be "
            f"inline in the delivered source files, not in a separate undelivered module.\n"
            f"- Each agent's output is a TEXT ARTIFACT. The final 'delivery plan' agent "
            f"will synthesize all artifacts into actual source files \u2014 plan accordingly."
        )
        plan = sync_generate_and_parse(
            job_planner, meta_prompt, WorkflowPlan,
            {},
        )

        # --- Planner pre-validation ---
        # Catch agents requesting files that don't exist in the repo.
        # This is the #1 cause of block-spirals.
        existing_files = {
            str(p.relative_to(job_workspace)).replace("\\", "/")
            for p in job_workspace.rglob("*")
            if p.is_file() and ".git" not in p.parts
        }
        warnings = []
        seed_artifacts = ["initial_goal", "repo_context"]
        for agent in plan.agents:
            missing = [f for f in agent.read_files if f not in existing_files]
            if missing:
                warnings.append(
                    f"Agent '{agent.agent_name}' requests read_files that "
                    f"do not exist: {missing}"
                )
            if not agent.depends_on:
                bad_keys = [k for k in agent.input_keys if k not in seed_artifacts]
                if bad_keys:
                    warnings.append(
                        f"Agent '{agent.agent_name}' references input_keys "
                        f"not yet available: {bad_keys}"
                    )
        if warnings:
            warning_text = "\n".join(f"- {w}" for w in warnings)
            logger.warning(f"Job {job_id}: Plan issues:\n{warning_text}")
            corrective = (
                meta_prompt
                + f"\n\nWARNING — your previous plan had these issues:\n"
                  f"{warning_text}\nFix all of them in the new plan."
            )
            plan = sync_generate_and_parse(
                job_planner, corrective, WorkflowPlan,
                {},
            )

        # --- PHASE 2: AGENT DAG EXECUTION ---
        # Agents whose depends_on are satisfied run in parallel via a
        # ThreadPoolExecutor; the orchestrator wakes on FIRST_COMPLETED.
        dag_ok, dag_fail, dag_total = execute_dag(
            plan, artifacts_dir, job_workspace, job_id,
            dag_executor=job_executor, dag_planner=job_planner,
            llm_provider=llm_provider, ollama_model=ollama_model,
            ollama_base_url=ollama_base_url,
        )

        # Circuit breaker: abort if less than half the agents succeeded
        if dag_total > 0 and dag_ok < dag_total * 0.5:
            update_job(
                job_id, status="failed", current_step="dag_incomplete",
                failure_class=FailureClass.DAG_STALLED,
                error=(
                    f"DAG too degraded: only {dag_ok}/{dag_total} agents "
                    f"completed ({dag_fail} failed). Aborting — not enough "
                    f"context to produce a meaningful delivery."
                ),
            )
            return

        # --- PHASE 3: DELIVERY PLAN ---
        update_job(job_id, current_step="generating delivery plan")
        # Read all agent outputs — use a tighter budget to fit small context windows.
        # 16 000 chars ≈ 4 000 tokens; leaves room for schema + completion in 8 K models.
        all_keys = [p.stem for p in artifacts_dir.glob("*.txt")]
        artifact_context = read_artifact_context(all_keys, artifacts_dir, max_budget=16000)
        delivery_prompt = (
            f"TASK: Synthesize all agent artifacts into production-ready, self-contained files.\n\n"
            f"Artifacts from agents:\n{json.dumps(artifact_context)}\n\n"
            f"Return a JSON DeliveryPlan with 'files' (array of objects with 'path' and 'content'), "
            f"'commit_message' (string), and 'pr_title' (string).\n\n"
            f"RULES:\n"
            f"- Merge ALL code from the artifacts into complete, runnable source files.\n"
            f"- Every file must be self-contained: all imports must resolve to the standard "
            f"library, a pip package from requirements.txt, or another file in this delivery.\n"
            f"- Do NOT reference external modules, packages, or repos that are not delivered "
            f"or available on PyPI.\n"
            f"- If multiple artifacts describe the same functionality (e.g. a bot algorithm), "
            f"merge them into a single coherent implementation inside the main file or a "
            f"co-delivered module.\n"
            f"- Include a requirements.txt ONLY with real pip-installable packages.\n"
            f"- Include complete, actually runnable code \u2014 not stubs or pseudocode.\n"
            f"CROSS-FILE REFERENCES (CRITICAL):\n"
            f"- Before writing any import statement like 'from X import Y', verify that "
            f"module X exists as another file in your delivery (e.g. X.py).\n"
            f"- If you define a function/class in one file and import it in another, "
            f"the EXACT function/class name must match between the files.\n"
            f"- Prefer fewer, larger files over many small files to reduce cross-file risk.\n"
            f"- If in doubt, put everything in a single file."
        )
        delivery = sync_generate_and_parse(
            job_executor, delivery_prompt, DeliveryPlan,
            {},
            max_retries=4,
        )

        # --- Structural pre-review: catch broken cross-references early ---
        xref_issues = validate_cross_references(delivery.files)
        if xref_issues:
            xref_text = "\n".join(f"- {i}" for i in xref_issues)
            logger.warning(f"Job {job_id}: Cross-reference issues:\n{xref_text}")
            update_job(job_id, current_step="fixing cross-references")
            file_manifest = [f.path for f in delivery.files]
            delivery = sync_generate_and_parse(
                job_executor,
                f"The delivery has BROKEN CROSS-FILE REFERENCES:\n{xref_text}\n\n"
                f"Current files in delivery: {file_manifest}\n"
                f"Current file contents:\n"
                f"{json.dumps([{'path': f.path, 'content': f.content[:ARTIFACT_CHAR_LIMIT]} for f in delivery.files])}\n\n"
                f"FIX RULES:\n"
                f"- For each broken import, either add the missing .py file to the delivery "
                f"OR move the imported code inline into the file that needs it.\n"
                f"- Verify EVERY 'from X import Y' has a matching file X.py with Y defined.\n"
                f"- Output the COMPLETE fixed delivery (files array, commit_message, pr_title).",
                DeliveryPlan,
                {},
                max_retries=4,
            )

        # --- PHASE 4: REVIEW & RETRY LOOP ---
        update_job(job_id, current_step="self-review")

        for cycle in range(review_cycles + 1):
            # Cap per-file content for review. 6000 chars ≈ 150 lines — enough
            # to see real issues without blowing the 8K context window.
            REVIEW_FILE_CAP = 6000
            review_input = {
                "goal": user_goal,
                "files": [
                    {
                        "path": f.path,
                        "content": f.content[:REVIEW_FILE_CAP],
                        "truncated": len(f.content) > REVIEW_FILE_CAP,
                    }
                    for f in delivery.files
                ],
                "commit_message": delivery.commit_message,
            }
            review_prompt = (
                f"Review these FILES to be committed against the goal "
                f"'{user_goal}':\n"
                f"{json.dumps(review_input, indent=2)}\n"
                f"Check for CONCRETE, FIXABLE issues only:\n"
                f"- Does the code actually run? Are there syntax errors or missing imports?\n"
                f"- Does it meet the stated goal?\n"
                f"- Are there real security vulnerabilities (SQL injection, path traversal, etc.)?\n"
                f"- Do NOT reject for vague/theoretical concerns like 'potential security risk'.\n"
                f"- Do NOT reject for missing features the user didn't ask for.\n"
                f"- Do NOT reject because a module is implemented inline instead of as a package.\n"
                f"- Each issue in your list must describe a SPECIFIC problem and HOW to fix it.\n"
                f"Return a JSON object with 'approved' (boolean) and 'issues' (array of strings)."
            )
            review = sync_generate_and_parse(
                job_reviewer, review_prompt, ReviewResult,
                {},
            )

            if review.approved:
                break

            if cycle == review_cycles:
                issues = "\n- ".join(review.issues)
                update_job(
                    job_id, status="failed",
                    current_step="review_rejected",
                    failure_class=FailureClass.REVIEW_REJECTED,
                    error=(
                        f"Team '{plan.team_name}' failed review after "
                        f"{review_cycles + 1} attempts.\n"
                        f"Issues:\n- {issues}"
                    ),
                )
                return

            update_job(job_id, current_step=f"review fix (cycle {cycle + 1})")
            FIX_FILE_CAP = 6000
            rejected_files = [
                {"path": f.path, "content": f.content[:FIX_FILE_CAP]}
                for f in delivery.files
            ]
            file_manifest = [f.path for f in delivery.files]
            fix_prompt = (
                f"A code reviewer REJECTED the delivery with these issues:\n"
                f"{json.dumps(review.issues)}\n\n"
                f"Files in current delivery: {file_manifest}\n"
                f"Current files (fix these):\n{json.dumps(rejected_files)}\n\n"
                f"RULES FOR FIXING:\n"
                f"- Fix EVERY issue listed above.\n"
                f"- Keep all code SELF-CONTAINED \u2014 all imports must resolve to stdlib, "
                f"pip packages, or other files in this delivery.\n"
                f"- If a missing module is referenced, implement it INLINE in the relevant file "
                f"or as a co-delivered .py file.\n"
                f"- For EVERY 'from X import Y' in any file, verify X.py exists in the delivery "
                f"and Y is actually defined in X.py.\n"
                f"- Output COMPLETE file contents, not patches or diffs.\n"
                f"- Do NOT introduce new external dependencies that don't exist on PyPI.\n\n"
                f"Return the complete fixed DeliveryPlan with 'files', 'commit_message', and 'pr_title'."
            )
            delivery = sync_generate_and_parse(
                job_executor, fix_prompt, DeliveryPlan,
                {},
                max_retries=4,
            )

        # --- PHASE 5: PR WORKFLOW ---
        if not delivery.files:
            update_job(
                job_id, status="complete", current_step="done",
                result=(
                    f"Team '{plan.team_name}' analyzed the goal but "
                    f"produced no file changes."
                ),
            )
            return

        update_job(job_id, current_step="pushing to GitHub")
        validate_files(delivery.files, job_workspace)

        branch_name = (
            f"auto/{sanitize_branch_name(plan.team_name)}/{job_id}"
        )
        run_git("checkout", "-b", branch_name, cwd=str(job_workspace))
        write_files(delivery.files, job_workspace)

        run_git("add", ".", cwd=str(job_workspace), timeout=30)
        diff = run_git(
            "diff", "--cached", "--stat", cwd=str(job_workspace), timeout=30,
        )
        if not diff.stdout.strip():
            update_job(
                job_id, status="complete", current_step="done",
                result=(
                    f"Team '{plan.team_name}' ran but produced no net "
                    f"changes to the codebase."
                ),
            )
            return

        run_git(
            "commit", "-m", delivery.commit_message,
            cwd=str(job_workspace), timeout=30,
        )
        run_git(
            "push", "origin", branch_name,
            cwd=str(job_workspace), timeout=120,
        )

        pr_body = (
            f"**Autonomous PR** generated by Team `{plan.team_name}`.\n\n"
            f"**Goal:** {user_goal}\n\n"
            f"**Files changed:** {len(delivery.files)}\n\n"
            f"To request changes, comment on this PR mentioning "
            f"`{BOT_MENTION}`."
        )
        pr_data = github_api_request(
            "POST",
            f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls",
            {
                "title": delivery.pr_title,
                "head": branch_name,
                "base": BASE_BRANCH,
                "body": pr_body,
            },
        )

        update_job(
            job_id, status="complete", current_step="done",
            pr_number=pr_data.get("number"),
            pr_url=pr_data.get("html_url"),
            pr_branch=branch_name,
            result=(
                f"\u2705 Team '{plan.team_name}' passed review and deployed.\n"
                f"PR: {pr_data.get('html_url')}"
            ),
        )

    except Exception as e:
        fc = classify_failure(e)
        logger.exception(f"Job {job_id} failed [{fc.value}]")
        detail = str(e)
        if isinstance(e, subprocess.CalledProcessError) and e.stderr:
            detail = f"{detail} | stderr: {e.stderr.strip()[:500]}"
        update_job(
            job_id, status="failed", current_step="error",
            failure_class=fc,
            error=f"Orchestration failed [{fc.value}]: {type(e).__name__}: {detail}",
        )
    finally:
        shutil.rmtree(job_workspace, ignore_errors=True)
        shutil.rmtree(artifacts_dir, ignore_errors=True)


# ============================================================================
# 10. GITHUB WEBHOOK ROUTE
# ============================================================================

@app.post("/github-webhook")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None),
):
    payload_bytes = await request.body()

    # --- Validate webhook signature ---
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing signature")
    expected_mac = hmac.new(
        WEBHOOK_SECRET.encode(), payload_bytes, hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(
        f"sha256={expected_mac}", x_hub_signature_256,
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # --- Only process issue_comment events (PR comments are issue comments) ---
    if x_github_event != "issue_comment":
        return {"status": "ignored_event"}

    payload = json.loads(payload_bytes)

    if payload.get("action") != "created":
        return {"status": "ignored_action"}
    if "pull_request" not in payload.get("issue", {}):
        return {"status": "ignored_not_pr"}

    comment_body = payload["comment"]["body"]
    commenter = payload["comment"]["user"]["login"]
    pr_api_url = payload["issue"]["pull_request"]["url"]
    comments_url = payload["issue"]["comments_url"]

    # --- Prevent infinite loops ---
    if commenter == BOT_USERNAME or comment_body.startswith(BOT_COMMENT_PREFIX):
        return {"status": "ignored_bot"}

    # --- Only respond to directed mentions ---
    if BOT_MENTION not in comment_body:
        return {"status": "ignored_not_addressed"}

    job_id = uuid.uuid4().hex[:12]

    background_tasks.add_task(
        process_pr_revision,
        pr_api_url, comments_url, comment_body, job_id, None,
    )
    return JSONResponse(
        status_code=202,
        content={"status": "accepted", "job_id": job_id},
    )


# ============================================================================
# 11. REVISION ENGINE (runs entirely in a background thread)
# ============================================================================

async def process_pr_revision(
    pr_api_url: str,
    comments_url: str,
    comment_body: str,
    job_id: str,
    parent_job_id: str | None = None,
):
    """Async entry point — offloads all blocking work to a thread."""
    await asyncio.to_thread(
        _sync_pr_revision, pr_api_url, comments_url, comment_body, job_id,
        parent_job_id,
    )


def _sync_pr_revision(
    pr_api_url: str,
    comments_url: str,
    comment_body: str,
    job_id: str,
    parent_job_id: str | None = None,
):
    """Synchronous revision pipeline — runs completely off the event loop."""
    job_workspace = BASE_WORKSPACE / f"fix-{job_id}"
    _, _, rev_reviewer, rev_fixer = create_models(DEFAULT_LLM_PROVIDER)

    create_job(job_id, goal=f"PR Revision: {comment_body[:120]}")
    update_job(
        job_id, status="running", current_step="cloning",
        job_type="revision", parent_job_id=parent_job_id,
    )

    try:
        # 1. Acknowledge receipt
        github_api_request("POST", comments_url, {
            "body": (
                f"\U0001f916 **Revision Acknowledged.** Investigating... "
                f"(Job: `{job_id}`)"
            ),
        })

        # 2. Get PR info & clone the feature branch
        pr_data = github_api_request("GET", pr_api_url)
        branch_name = pr_data["head"]["ref"]
        repo_url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}.git"

        run_git(
            "clone", "--branch", branch_name, "--depth", "1",
            repo_url, str(job_workspace),
        )
        run_git(
            "config", "user.email", "orchestrator@automated.dev",
            cwd=str(job_workspace), timeout=10,
        )
        run_git(
            "config", "user.name", "SDLC Orchestrator",
            cwd=str(job_workspace), timeout=10,
        )

        # 3. Get PR diff for context (may fail on shallow clone)
        pr_diff = ""
        try:
            run_git(
                "fetch", "origin", BASE_BRANCH, "--depth", "1",
                cwd=str(job_workspace), timeout=60,
            )
            diff_result = run_git(
                "diff", "FETCH_HEAD..HEAD",
                cwd=str(job_workspace), timeout=30,
            )
            pr_diff = diff_result.stdout[:ARTIFACT_CHAR_LIMIT]
        except subprocess.CalledProcessError:
            logger.warning(
                f"Job {job_id}: Could not compute PR diff (shallow clone)"
            )

        # 4. Investigation: which files does the fixer need?
        update_job(job_id, current_step="investigating")
        repo_tree = get_repo_summary(job_workspace, max_chars=3000)

        inv_prompt = (
            f"User commented on a PR: '{comment_body}'\n"
            f"PR diff against {BASE_BRANCH}:\n{pr_diff}\n"
            f"Repo file tree:\n{repo_tree}\n"
            f"Which files (max {MAX_READ_FILES}) do you need to read to "
            f"address this comment? Return a JSON with 'files_to_read' (array of file paths)."
        )
        file_req = sync_generate_and_parse(
            rev_fixer, inv_prompt, FileRequest,
            {},
        )

        # 5. Read requested files
        file_context = read_agent_files(
            file_req.files_to_read, job_workspace,
        )

        # 6. Generate the fix
        update_job(job_id, current_step="fixing")
        fix_prompt = (
            f"User Comment: '{comment_body}'\n"
            f"PR diff against {BASE_BRANCH}:\n{pr_diff}\n"
            f"Existing Files:\n{json.dumps(file_context)}\n"
            f"Fix ONLY what the user asked for. Do not revert other changes.\n"
            f"Return a JSON DeliveryPlan with 'files' (array of {{path, content}}), "
            f"'commit_message', and 'pr_title'."
        )
        delivery = sync_generate_and_parse(
            rev_fixer, fix_prompt, DeliveryPlan,
            {},
        )

        # 7. Review gate
        update_job(job_id, current_step="reviewing")
        review_input = {
            "comment": comment_body,
            "files": [
                {"path": f.path, "content": f.content[:ARTIFACT_CHAR_LIMIT]}
                for f in delivery.files
            ],
        }
        review_prompt = (
            f"Review this fix against the user comment: '{comment_body}'\n"
            f"Files to commit:\n{json.dumps(review_input, indent=2)}\n"
            f"Is this fix correct and minimal? Return a JSON with 'approved' (boolean) "
            f"and 'issues' (array of strings)."
        )
        review = sync_generate_and_parse(
            rev_reviewer, review_prompt, ReviewResult,
            {},
        )

        if not review.approved:
            issues = "\n- ".join(review.issues)
            github_api_request("POST", comments_url, {
                "body": (
                    f"\U0001f916 Generated a fix but the reviewer rejected it:\n"
                    f"- {issues}\n\n"
                    f"Please provide more specific guidance."
                ),
            })
            update_job(job_id, status="complete", current_step="done",
                       result=f"Reviewer rejected: {issues[:200]}")
            return

        # 8. Apply changes & push
        update_job(job_id, current_step="pushing")
        if not delivery.files:
            github_api_request("POST", comments_url, {
                "body": (
                    "\U0001f916 Analyzed the comment but determined no file "
                    "changes are needed."
                ),
            })
            update_job(job_id, status="complete", current_step="done",
                       result="No file changes needed")
            return

        validate_files(delivery.files, job_workspace)
        write_files(delivery.files, job_workspace)

        run_git("add", ".", cwd=str(job_workspace), timeout=30)
        diff = run_git(
            "diff", "--cached", "--stat",
            cwd=str(job_workspace), timeout=30,
        )
        if not diff.stdout.strip():
            github_api_request("POST", comments_url, {
                "body": (
                    "\U0001f916 Code analysis complete, but no net changes "
                    "were produced."
                ),
            })
            update_job(job_id, status="complete", current_step="done",
                       result="No net changes produced")
            return

        run_git(
            "commit", "-m", delivery.commit_message,
            cwd=str(job_workspace), timeout=30,
        )
        run_git(
            "push", "origin", branch_name,
            cwd=str(job_workspace), timeout=120,
        )

        github_api_request("POST", comments_url, {
            "body": (
                f"\U0001f916 **Revision Complete.** Pushed fix: "
                f"`{delivery.commit_message}`"
            ),
        })
        update_job(job_id, status="complete", current_step="done",
                   result=f"Pushed fix: {delivery.commit_message}")

    except Exception as exc:
        logger.exception(f"Revision Job {job_id} failed")
        update_job(job_id, status="failed", current_step="error",
                   error=f"Revision failed: {type(exc).__name__}: {exc}")
        try:
            github_api_request("POST", comments_url, {
                "body": (
                    f"\U0001f6d1 **Revision Failed.** Check container logs "
                    f"for Job `{job_id}`."
                ),
            })
        except Exception:
            logger.error(
                f"Job {job_id}: Also failed to post failure notification."
            )
    finally:
        if job_workspace.exists():
            shutil.rmtree(job_workspace, ignore_errors=True)