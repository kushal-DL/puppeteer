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
    import json as _json
    import subprocess as _sp

    msg = str(error).lower()
    if isinstance(error, _json.JSONDecodeError):
        return FailureClass.JSON_PARSE
    if isinstance(error, _sp.CalledProcessError):
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
