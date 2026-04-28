"""Ollama / OpenAI-compatible LLM adapter."""

import json
import logging
import time
import urllib.error
import urllib.request

from hiveship.config import OLLAMA_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL
from hiveship.llm.base import make_usage
from hiveship.llm.gemini import ResponseShim

logger = logging.getLogger(__name__)


class OllamaModel:
    """Drop-in replacement for GeminiModel.

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
                    # Extract usage from OpenAI-compat response
                    usage = None
                    raw_usage = body.get("usage")
                    if raw_usage:
                        usage = make_usage(
                            input_tokens=raw_usage.get("prompt_tokens", 0),
                            output_tokens=raw_usage.get("completion_tokens", 0),
                            model=self.model_name,
                        )
                    return ResponseShim(text, usage=usage)
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
        # Extract usage from native Ollama response
        usage = None
        if "prompt_eval_count" in body or "eval_count" in body:
            usage = make_usage(
                input_tokens=body.get("prompt_eval_count", 0),
                output_tokens=body.get("eval_count", 0),
                model=self.model_name,
            )
        return ResponseShim(text, usage=usage)
