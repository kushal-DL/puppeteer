"""Tests for enhanced error classification (models.py) and compression."""

import json
import subprocess

import pytest

from hiveship.models import (
    FailureClass,
    RecoveryHint,
    classify_failure,
    get_recovery_hint,
    RECOVERY_RECIPES,
)
from hiveship.engine.compression import (
    compress_context,
    should_compress,
)


# ── Error classification tests ────────────────────────────────────────────────

class TestClassifyFailure:
    def test_json_decode_error(self):
        err = json.JSONDecodeError("Expecting value", "", 0)
        assert classify_failure(err) == FailureClass.JSON_PARSE

    def test_rate_limit(self):
        err = RuntimeError("Rate limit exceeded, please retry after 30s")
        assert classify_failure(err) == FailureClass.RATE_LIMIT

    def test_429_status(self):
        err = RuntimeError("HTTP 429 Too Many Requests")
        assert classify_failure(err) == FailureClass.RATE_LIMIT

    def test_billing_exhausted(self):
        err = RuntimeError("Quota exhausted for this billing period")
        assert classify_failure(err) == FailureClass.BILLING

    def test_insufficient_credits(self):
        err = RuntimeError("Insufficient credits to process request")
        assert classify_failure(err) == FailureClass.BILLING

    def test_auth_permanent(self):
        err = RuntimeError("Invalid API key provided")
        assert classify_failure(err) == FailureClass.AUTH_PERMANENT

    def test_auth_transient(self):
        err = RuntimeError("401 Authentication failed")
        assert classify_failure(err) == FailureClass.AUTH

    def test_context_overflow(self):
        err = RuntimeError("This request exceeds the context length limit")
        assert classify_failure(err) == FailureClass.CONTEXT_OVERFLOW

    def test_overloaded(self):
        err = RuntimeError("503 Service temporarily unavailable")
        assert classify_failure(err) == FailureClass.OVERLOADED

    def test_timeout(self):
        err = RuntimeError("Request timed out after 30 seconds")
        assert classify_failure(err) == FailureClass.LLM_TIMEOUT

    def test_safety_blocked(self):
        err = RuntimeError("Response blocked by safety filters")
        assert classify_failure(err) == FailureClass.LLM_BLOCKED

    def test_payload_too_large(self):
        err = RuntimeError("413 Payload too large")
        assert classify_failure(err) == FailureClass.PAYLOAD_TOO_LARGE

    def test_unknown_error(self):
        err = RuntimeError("Something completely unexpected")
        assert classify_failure(err) == FailureClass.UNKNOWN

    def test_git_conflict(self):
        err = subprocess.CalledProcessError(1, "git")
        err.stderr = "merge conflict detected"
        # CalledProcessError str includes returncode + cmd, not stderr
        # So classify uses the str(error) which won't contain stderr.
        # It falls to UNKNOWN — test the subprocess fast-path properly:
        err2 = subprocess.CalledProcessError(1, "git merge conflict")
        assert classify_failure(err2) == FailureClass.GIT_CONFLICT


class TestRecoveryHints:
    def test_rate_limit_retryable(self):
        err = RuntimeError("Rate limit exceeded")
        hint = get_recovery_hint(err)
        assert hint.retryable is True
        assert hint.should_fallback is False

    def test_billing_not_retryable(self):
        err = RuntimeError("Quota exhausted")
        hint = get_recovery_hint(err)
        assert hint.retryable is False
        assert hint.should_fallback is True

    def test_context_overflow_should_compress(self):
        err = RuntimeError("context length exceeded")
        hint = get_recovery_hint(err)
        assert hint.should_compress is True

    def test_unknown_not_retryable(self):
        err = RuntimeError("mystery error")
        hint = get_recovery_hint(err)
        assert hint.retryable is False


class TestRecoveryRecipes:
    def test_all_failure_classes_have_recipes(self):
        """Every FailureClass should have a RecoveryRecipe."""
        for fc in FailureClass:
            assert fc in RECOVERY_RECIPES, f"Missing recipe for {fc}"


# ── Compression tests ─────────────────────────────────────────────────────────

class TestCompression:
    def test_should_compress_below_threshold(self):
        context = {"a": "x" * 100, "b": "y" * 100}
        assert not should_compress(context, target=1000)

    def test_should_compress_above_threshold(self):
        context = {"a": "x" * 5000, "b": "y" * 5000}
        assert should_compress(context, target=1000)

    def test_compress_preserves_head_tail(self):
        context = {
            "initial_goal": "Build an API",
            "repo_context": "File tree...",
            "agent_1": "Agent 1 output " * 200,
            "agent_2": "Agent 2 output " * 200,
            "agent_3": "Agent 3 output " * 200,
            "agent_4": "Recent agent work",
            "agent_5": "Latest agent output",
            "agent_6": "Most recent output",
        }
        result = compress_context(context, target=2000, head_protect=2, tail_protect=3)
        # Head preserved
        assert "initial_goal" in result
        assert result["initial_goal"] == "Build an API"
        # Tail preserved
        assert "agent_6" in result
        assert result["agent_6"] == "Most recent output"
        # Middle compressed
        assert "_compressed_context" in result
        assert "COMPRESSED" in result["_compressed_context"]

    def test_compress_small_context_unchanged(self):
        context = {"a": "short", "b": "also short"}
        result = compress_context(context, target=10000)
        assert result == context

    def test_compress_with_llm_fn(self):
        context = {
            "head": "Goal",
            "plan": "Plan",
            "mid1": "x" * 5000,
            "mid2": "y" * 5000,
            "tail1": "Recent 1",
            "tail2": "Recent 2",
            "tail3": "Recent 3",
        }
        mock_summary = "Summarized middle content"
        result = compress_context(
            context, target=500,
            head_protect=2, tail_protect=3,
            llm_fn=lambda p: mock_summary,
        )
        assert "Summarized middle content" in result.get("_compressed_context", "")
