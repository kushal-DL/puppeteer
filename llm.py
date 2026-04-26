import json
import logging
import re
import time
import urllib.error
import urllib.request
from typing import Type, TypeVar

from google import genai
from pydantic import ValidationError

from config import GEMINI_KEY, OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL

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

# Initialise Gemini client (new google-genai SDK)
_gemini_client = None
if GEMINI_KEY:
    _gemini_client = genai.Client(api_key=GEMINI_KEY)
else:
    logger.warning("GEMINI_API_KEY not set — 'gemini' provider will be unavailable.")


# ── GeminiModel wrapper (uses new google-genai SDK with native structured output) ──
class GeminiModel:
    """Wrapper around the google-genai Client that mirrors the OllamaModel API.

    Key difference from the old genai.GenerativeModel: structured output is
    enforced at the API level via `response_schema` — the model never sees
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
        return _OllamaResponse(text)


# ── Ollama response shims (shared by GeminiModel and OllamaModel) ─────────────
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


# ── OllamaModel ───────────────────────────────────────────────────────────────
class OllamaModel:
    """Drop-in replacement for genai.GenerativeModel.

    Supports both:
    - Native Ollama servers  (/api/chat)
    - OpenAI-compatible servers like vLLM, LM Studio (/v1/chat/completions)

    Detection: if the model name contains "/" (HuggingFace-style) or the base
    URL is not a plain localhost Ollama instance, assume OpenAI-compatible.
    """

    def __init__(self, model_name: str, system_instruction: str = "", base_url: str = ""):
        self.model_name = model_name
        self.system_instruction = system_instruction or ""
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        # Strip endpoint suffix if a full URL was passed
        for suffix in ("/v1/chat/completions", "/api/chat"):
            if self.base_url.endswith(suffix):
                self.base_url = self.base_url[: -len(suffix)]
                break
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
            return self._call_openai_compat(messages, headers, config)
        return self._call_native_ollama(messages, headers, config)

    def _call_openai_compat(self, messages, headers, config):
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
        last_error = None
        for attempt in range(4):
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(target_url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=300) as response:
                    body = json.loads(response.read().decode())
                    text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                    if not text:
                        raise ValueError("LLM returned an empty response.")
                    return _OllamaResponse(text)
            except urllib.error.HTTPError as e:
                err_body = e.read().decode(errors="replace")[:400]
                last_error = RuntimeError(f"LLM HTTP {e.code} at {target_url}: {err_body}")
                if e.code == 400 and "context length" in err_body.lower():
                    cur = payload.get("max_tokens", 2048)
                    reduced = max(cur // 2, 128)
                    if reduced < cur:
                        logger.warning(
                            f"Context overflow (max_tokens={cur}), retrying with {reduced}"
                        )
                        payload["max_tokens"] = reduced
                        continue
                    raise last_error from e
                if e.code in (500, 502, 503, 504) and attempt < 2:
                    time.sleep(1 + attempt)
                    continue
                raise last_error from e
        raise last_error or RuntimeError(f"LLM request failed at {target_url}")

    def _call_native_ollama(self, messages, headers, config):
        payload: dict = {"model": self.model_name, "messages": messages, "stream": False}
        # Native Ollama supports format: "json" or a full JSON Schema object
        schema_class = config.get("response_schema")
        if schema_class is not None:
            payload["format"] = schema_class.model_json_schema()
        elif config.get("response_mime_type") == "application/json":
            payload["format"] = "json"
        target_url = f"{self.base_url}/api/chat"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(target_url, data=data, headers=headers, method="POST")
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


# ── Factory ───────────────────────────────────────────────────────────────────
def _create_model(
    provider: str,
    system_instruction: str,
    ollama_model: str = "",
    ollama_base_url: str = "",
):
    if provider == "ollama":
        return OllamaModel(ollama_model or OLLAMA_MODEL, system_instruction, ollama_base_url)
    if not _gemini_client:
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
if _gemini_client:
    planner_model, executor_model, reviewer_model, fixer_model = create_models("gemini")
else:
    planner_model = executor_model = reviewer_model = fixer_model = None


# ── Generation helpers ────────────────────────────────────────────────────────
def extract_text(resp) -> str:
    """Safely extract text from a Gemini or Ollama response object."""
    if not resp.candidates:
        raise ValueError("AI response blocked by safety filters.")
    if not resp.candidates[0].content.parts:
        raise ValueError("AI returned an empty response.")
    return resp.candidates[0].content.parts[0].text


def sync_generate_with_retry(model, prompt, config=None, max_retries: int = 2) -> str:
    """Synchronous LLM call with exponential backoff."""
    for attempt in range(max_retries + 1):
        try:
            resp = model.generate_content(prompt, generation_config=config or {})
            return extract_text(resp)
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            logger.warning(
                f"LLM call failed (attempt {attempt + 1}), retrying in {wait}s: {e}"
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
