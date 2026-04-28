import re as _re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, field_validator, ValidationError  # noqa: F401


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
    # New: LLM provider-level failures (inspired by hermes error_classifier.py)
    AUTH = "auth"
    AUTH_PERMANENT = "auth_permanent"
    BILLING = "billing"
    RATE_LIMIT = "rate_limit"
    OVERLOADED = "overloaded"
    PAYLOAD_TOO_LARGE = "payload_too_large"
    PROVIDER_POLICY_BLOCKED = "provider_policy_blocked"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RecoveryHint:
    """Structured recovery hints attached to a classified error."""
    retryable: bool = False
    should_compress: bool = False
    should_fallback: bool = False


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
    system_instruction: Optional[str] = None
    depends_on: List[str] = []
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
    FailureClass.AUTH: RecoveryRecipe(
        failure_class=FailureClass.AUTH,
        actions=[RecoveryAction.RETRY_WITH_REPAIR],
        max_attempts=1,
    ),
    FailureClass.AUTH_PERMANENT: RecoveryRecipe(
        failure_class=FailureClass.AUTH_PERMANENT,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.BILLING: RecoveryRecipe(
        failure_class=FailureClass.BILLING,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.RATE_LIMIT: RecoveryRecipe(
        failure_class=FailureClass.RATE_LIMIT,
        actions=[RecoveryAction.RETRY_WITH_REPAIR],
        max_attempts=3,
    ),
    FailureClass.OVERLOADED: RecoveryRecipe(
        failure_class=FailureClass.OVERLOADED,
        actions=[RecoveryAction.RETRY_WITH_REPAIR],
        max_attempts=2,
    ),
    FailureClass.PAYLOAD_TOO_LARGE: RecoveryRecipe(
        failure_class=FailureClass.PAYLOAD_TOO_LARGE,
        actions=[RecoveryAction.REDUCE_CONTEXT],
        max_attempts=2,
    ),
    FailureClass.PROVIDER_POLICY_BLOCKED: RecoveryRecipe(
        failure_class=FailureClass.PROVIDER_POLICY_BLOCKED,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=0,
    ),
    FailureClass.UNKNOWN: RecoveryRecipe(
        failure_class=FailureClass.UNKNOWN,
        actions=[RecoveryAction.ESCALATE],
        max_attempts=1,
    ),
}


# ── Regex-based error classification (inspired by hermes error_classifier.py) ─
# Ordered list: first match wins. Each tuple is (compiled_regex, FailureClass, RecoveryHint).

_CLASSIFICATION_PATTERNS: list = [
    # Auth - permanent (invalid key, revoked)
    (_re.compile(r"invalid.*(api.?key|credential|token)", _re.I),
     FailureClass.AUTH_PERMANENT, RecoveryHint(retryable=False, should_fallback=True)),
    (_re.compile(r"(api.?key|token)\s*(revoked|expired|invalid|disabled)", _re.I),
     FailureClass.AUTH_PERMANENT, RecoveryHint(retryable=False, should_fallback=True)),
    (_re.compile(r"permission\s*denied|unauthorized|403.*forbidden", _re.I),
     FailureClass.AUTH_PERMANENT, RecoveryHint(retryable=False, should_fallback=True)),

    # Auth - transient (could be temporary)
    (_re.compile(r"401|authentication\s*(failed|error|required)", _re.I),
     FailureClass.AUTH, RecoveryHint(retryable=True, should_fallback=True)),

    # Billing
    (_re.compile(r"(quota|credit|billing|budget)\s*(exhaust|exceed|limit|deplet)", _re.I),
     FailureClass.BILLING, RecoveryHint(retryable=False, should_fallback=True)),
    (_re.compile(r"insufficient\s*(funds|credits|quota|balance)", _re.I),
     FailureClass.BILLING, RecoveryHint(retryable=False, should_fallback=True)),
    (_re.compile(r"payment\s*required|402", _re.I),
     FailureClass.BILLING, RecoveryHint(retryable=False, should_fallback=True)),

    # Rate limit
    (_re.compile(r"rate.?limit|too\s*many\s*requests|429|throttl", _re.I),
     FailureClass.RATE_LIMIT, RecoveryHint(retryable=True)),
    (_re.compile(r"(requests?|tokens?)\s*per\s*(minute|second|hour)\s*(limit|exceed)", _re.I),
     FailureClass.RATE_LIMIT, RecoveryHint(retryable=True)),
    (_re.compile(r"resource\s*exhausted", _re.I),
     FailureClass.RATE_LIMIT, RecoveryHint(retryable=True)),

    # Overloaded
    (_re.compile(r"(server|service)\s*(overloaded|unavailable|busy)|503|502", _re.I),
     FailureClass.OVERLOADED, RecoveryHint(retryable=True, should_fallback=True)),
    (_re.compile(r"capacity|temporarily\s*unavailable|try\s*again\s*later", _re.I),
     FailureClass.OVERLOADED, RecoveryHint(retryable=True)),

    # Context overflow
    (_re.compile(r"context.?(length|window|limit)|maximum.?context|token.?limit\s*exceed", _re.I),
     FailureClass.CONTEXT_OVERFLOW, RecoveryHint(retryable=True, should_compress=True)),
    (_re.compile(r"prompt\s*(is\s*)?too\s*(long|large)", _re.I),
     FailureClass.CONTEXT_OVERFLOW, RecoveryHint(retryable=True, should_compress=True)),

    # Payload too large
    (_re.compile(r"payload\s*too\s*large|413|request.*(too\s*large|size\s*exceed)", _re.I),
     FailureClass.PAYLOAD_TOO_LARGE, RecoveryHint(retryable=True, should_compress=True)),
    (_re.compile(r"image\s*(too\s*large|size\s*exceed)", _re.I),
     FailureClass.PAYLOAD_TOO_LARGE, RecoveryHint(retryable=False)),

    # Provider policy blocked
    (_re.compile(r"(content\s*)?policy\s*(violation|block)|harm\s*categor", _re.I),
     FailureClass.PROVIDER_POLICY_BLOCKED, RecoveryHint(retryable=False)),
    (_re.compile(r"(safety|content)\s*filter|blocked\s*by\s*(safety|content|policy)", _re.I),
     FailureClass.LLM_BLOCKED, RecoveryHint(retryable=False)),

    # Timeout
    (_re.compile(r"time\s*out|timed?\s*out|deadline\s*exceed", _re.I),
     FailureClass.LLM_TIMEOUT, RecoveryHint(retryable=True, should_compress=True)),
    (_re.compile(r"read\s*timeout|connect\s*timeout|socket\s*timeout", _re.I),
     FailureClass.LLM_TIMEOUT, RecoveryHint(retryable=True)),

    # Git conflicts
    (_re.compile(r"(merge|rebase)\s*conflict", _re.I),
     FailureClass.GIT_CONFLICT, RecoveryHint(retryable=False)),
]


def classify_failure(error: Exception) -> FailureClass:
    """Classify an exception into a FailureClass for targeted recovery.

    Uses ordered regex patterns (first match wins), falling back to
    type-based checks for JSONDecodeError and CalledProcessError.
    """
    import json as _json
    import subprocess as _sp

    # Type-based fast paths
    if isinstance(error, _json.JSONDecodeError):
        return FailureClass.JSON_PARSE
    if isinstance(error, _sp.CalledProcessError):
        msg = str(error).lower()
        if "conflict" in msg or "merge" in msg:
            return FailureClass.GIT_CONFLICT
        return FailureClass.UNKNOWN

    # Regex pattern matching (first match wins)
    msg = str(error)
    for pattern, fc, _ in _CLASSIFICATION_PATTERNS:
        if pattern.search(msg):
            return fc

    return FailureClass.UNKNOWN


def get_recovery_hint(error: Exception) -> RecoveryHint:
    """Get structured recovery hints for an error.

    Returns RecoveryHint with retryable/should_compress/should_fallback flags.
    """
    import json as _json

    if isinstance(error, _json.JSONDecodeError):
        return RecoveryHint(retryable=True)

    msg = str(error)
    for pattern, _, hint in _CLASSIFICATION_PATTERNS:
        if pattern.search(msg):
            return hint

    return RecoveryHint(retryable=False)


class JobEvent(BaseModel):
    t: int
    type: str
    agent: Optional[str] = None
    failure_class: Optional[FailureClass] = None
    detail: Optional[str] = None
    data: Optional[dict] = None
