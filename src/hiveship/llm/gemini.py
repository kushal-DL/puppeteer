"""Gemini LLM adapter using the google-genai SDK."""

import logging

from google import genai

from hiveship.config import GEMINI_KEY
from hiveship.llm.base import make_usage

logger = logging.getLogger(__name__)

# Initialise Gemini client (new google-genai SDK)
_gemini_client = None
if GEMINI_KEY:
    _gemini_client = genai.Client(api_key=GEMINI_KEY)
else:
    logger.warning("GEMINI_API_KEY not set — 'gemini' provider will be unavailable.")


# ── Response shims (shared by GeminiModel and OllamaModel) ────────────────────

class _ResponsePart:
    def __init__(self, text: str):
        self.text = text


class _ResponseContent:
    def __init__(self, text: str):
        self.parts = [_ResponsePart(text)]


class _ResponseCandidate:
    def __init__(self, text: str):
        self.content = _ResponseContent(text)


class ResponseShim:
    """Uniform response wrapper so extract_text() works for all providers.

    Includes optional .usage attribute for token tracking.
    """

    def __init__(self, text: str, usage=None):
        self.candidates = [_ResponseCandidate(text)]
        self.usage = usage  # UsageRecord or None


class GeminiModel:
    """Wrapper around the google-genai Client that mirrors the OllamaModel API.

    Key difference from the old genai.GenerativeModel: structured output is
    enforced at the API level via ``response_schema`` — the model never sees
    raw JSON Schema text in the prompt, eliminating schema-echo failures.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", system_instruction: str = ""):
        self.model_name = model_name
        self.system_instruction = system_instruction or ""

    def generate_content(self, prompt, generation_config=None):
        """Call Gemini via the new SDK. Returns a shim response for compatibility."""
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
        # Wrap in shim so extract_text() works uniformly
        text = resp.text or ""
        if not text:
            raise ValueError("AI returned an empty response.")

        # Extract usage metadata for cost tracking
        usage = None
        try:
            um = getattr(resp, "usage_metadata", None)
            if um:
                usage = make_usage(
                    input_tokens=getattr(um, "prompt_token_count", 0) or 0,
                    output_tokens=getattr(um, "candidates_token_count", 0) or 0,
                    model=self.model_name,
                )
        except Exception:
            pass  # Usage extraction is best-effort

        return ResponseShim(text, usage=usage)


def get_gemini_client():
    """Return the singleton Gemini client (or None if not configured)."""
    return _gemini_client
