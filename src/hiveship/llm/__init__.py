"""LLM abstraction layer — public API.

Usage:
    from hiveship.llm import create_models, sync_generate_with_retry, sync_generate_and_parse
"""

import json
import logging
import random
import re
import time
from typing import List, Optional, Type, TypeVar

from pydantic import ValidationError

from hiveship.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from hiveship.llm.base import UsageRecord, make_usage
from hiveship.llm.gemini import GeminiModel, ResponseShim, get_gemini_client
from hiveship.llm.ollama import OllamaModel

logger = logging.getLogger(__name__)

# ── System instructions (shared across both providers) ───────────────────────
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


# ── Factory ───────────────────────────────────────────────────────────────────
def _create_model(
    provider: str,
    system_instruction: str,
    ollama_model: str = "",
    ollama_base_url: str = "",
):
    if provider == "ollama":
        return OllamaModel(ollama_model or OLLAMA_MODEL, system_instruction, ollama_base_url)
    if not get_gemini_client():
        raise RuntimeError("Gemini requested but GEMINI_API_KEY is not set.")
    return GeminiModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction,
    )


def create_models(
    provider: str = "gemini",
    ollama_model: str = "",
    ollama_base_url: str = "",
):
    """Return (planner, executor, reviewer, fixer) for the chosen provider."""
    return (
        _create_model(provider, _PLANNER_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _EXECUTOR_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _REVIEWER_INSTRUCTION, ollama_model, ollama_base_url),
        _create_model(provider, _FIXER_INSTRUCTION, ollama_model, ollama_base_url),
    )


# Default Gemini instances (None if key absent — callers must check)
if get_gemini_client():
    planner_model, executor_model, reviewer_model, fixer_model = create_models("gemini")
else:
    planner_model = executor_model = reviewer_model = fixer_model = None


# ── Generation helpers ────────────────────────────────────────────────────────

# Max retries (configurable via env)
import os
LLM_MAX_RETRIES = int(os.environ.get("LLM_MAX_RETRIES", "3"))
LLM_FALLBACK_ENABLED = os.environ.get(
    "LLM_FALLBACK_ENABLED", "true"
).strip().lower() in ("1", "true", "yes")


def _jittered_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """Decorrelated jitter backoff: min(cap, base * 2^attempt + random).

    Returns the delay in seconds. Inspired by hermes-agent's retry pattern.
    """
    exponential = base * (2 ** attempt)
    jitter = random.uniform(0, exponential)
    return min(cap, exponential + jitter)


def extract_text(resp) -> str:
    """Safely extract text from a Gemini or Ollama response object."""
    if not resp.candidates:
        raise ValueError("AI response blocked by safety filters.")
    if not resp.candidates[0].content.parts:
        raise ValueError("AI returned an empty response.")
    return resp.candidates[0].content.parts[0].text


def extract_usage(resp) -> Optional[UsageRecord]:
    """Extract usage record from a response if available."""
    return getattr(resp, "usage", None)


# ── Usage accumulator (thread-local per pipeline run) ─────────────────────────
_usage_records: List[UsageRecord] = []


def get_accumulated_usage() -> List[UsageRecord]:
    """Return all usage records accumulated during this pipeline run."""
    return list(_usage_records)


def reset_usage() -> None:
    """Clear accumulated usage records (call at pipeline start)."""
    _usage_records.clear()


def get_total_cost() -> float:
    """Sum estimated cost across all accumulated usage records."""
    return sum(r.estimated_cost_usd for r in _usage_records)


def sync_generate_with_retry(model, prompt, config=None, max_retries: int = -1) -> str:
    """Synchronous LLM call with jittered exponential backoff.

    Uses decorrelated jitter for retry delays. Accumulates usage records.
    If max_retries is -1, uses LLM_MAX_RETRIES from config.
    """
    if max_retries < 0:
        max_retries = LLM_MAX_RETRIES
    for attempt in range(max_retries + 1):
        try:
            resp = model.generate_content(prompt, generation_config=config or {})
            # Track usage
            usage = extract_usage(resp)
            if usage:
                _usage_records.append(usage)
            return extract_text(resp)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = _jittered_backoff(attempt)
            logger.warning(
                f"LLM call failed (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {wait:.1f}s: {e}"
            )
            time.sleep(wait)


_T = TypeVar("_T")


def sync_generate_and_parse(
    model,
    prompt: str,
    schema_class: Type[_T],
    config=None,
    max_retries: int = 2,
) -> _T:
    """Generate + JSON-parse + Pydantic-validate with corrective retry.

    The schema_class is passed to the LLM provider via API-level structured
    output (Gemini response_schema / OpenAI json_schema / Ollama format).
    The schema is NEVER dumped into the prompt text — this eliminates
    schema-echo failures entirely.
    """
    effective_config = dict(config or {})
    effective_config["response_schema"] = schema_class

    effective_prompt = prompt
    for attempt in range(max_retries + 1):
        try:
            text = sync_generate_with_retry(model, effective_prompt, effective_config, max_retries=0)
            text = re.sub(r"^\s*```(?:json)?\s*\n?", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\n?\s*```\s*$", "", text).strip()
            # Use raw_decode to parse only the first JSON value,
            # ignoring trailing text / duplicate objects the LLM may emit.
            idx = text.index("{") if "{" in text else 0
            try:
                parsed, _ = json.JSONDecoder().raw_decode(text, idx)
            except json.JSONDecodeError:
                repaired = re.sub(r',\s*([}\]])', r'\1', text)  # trailing commas
                repaired = repaired.replace('\r\n', '\\n').replace('\r', '\\n')
                r_idx = repaired.index("{") if "{" in repaired else 0
                parsed, _ = json.JSONDecoder().raw_decode(repaired, r_idx)
            # Detect schema echo — should be extremely rare now that schema is
            # not in the prompt, but keep as a safety net.
            if (
                isinstance(parsed, dict)
                and "properties" in parsed
                and parsed.get("type") == "object"
            ):
                raise ValueError(
                    "Model returned the JSON schema definition instead of actual values."
                )
            return schema_class(**parsed)
        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            if attempt == max_retries:
                raise
            logger.warning(f"Parse/validation failed (attempt {attempt + 1}): {e}")
            # Detect likely output truncation
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
                      "file content \u2014 use only essential code, no comments or "
                      "docstrings. Ensure the JSON is properly closed."
                )
            elif is_malformed_json:
                effective_prompt = (
                    prompt
                    + "\n\nCRITICAL: Your previous JSON response had a syntax error: "
                      f"{e}\n"
                      "Common causes:\n"
                      "- Unescaped double quotes inside string values (use \\\" instead of \")\n"
                      "- Unescaped backslashes (use \\\\\\\\ instead of \\\\)\n"
                      "- Literal newlines inside strings (use \\n instead)\n"
                      "- Trailing commas after the last element in arrays/objects\n"
                      "Ensure ALL string values containing code have properly escaped "
                      "special characters. Output ONLY valid JSON."
                )
            else:
                effective_prompt = (
                    prompt
                    + "\n\nIMPORTANT: Return a JSON object with actual values filled in. "
                      "Do NOT return the schema definition itself. For example, if the "
                      "schema says '\"approved\": bool', return '\"approved\": true'."
                )
            time.sleep(2 ** attempt)


# Re-export everything needed by other modules
__all__ = [
    "GeminiModel",
    "OllamaModel",
    "ResponseShim",
    "UsageRecord",
    "_create_model",
    "create_models",
    "extract_text",
    "extract_usage",
    "get_accumulated_usage",
    "get_total_cost",
    "make_usage",
    "planner_model",
    "executor_model",
    "reviewer_model",
    "fixer_model",
    "reset_usage",
    "sync_generate_with_retry",
    "sync_generate_and_parse",
]
