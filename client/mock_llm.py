"""Mock OpenAI-compatible LLM server for HiveShip testing.

Designed to be driven by GitHub Copilot Chat in agent mode:
  - HiveShip sends prompts to /v1/chat/completions (standard OpenAI API)
  - The request BLOCKS until a response is posted
  - Copilot polls GET /pending to see the waiting prompt
  - Copilot posts the answer to POST /respond
  - The blocked /v1/chat/completions returns that answer to HiveShip

Copilot workflow:
  1. Start this server:     python client/mock_llm.py
  2. Start HiveShip:        uvicorn hiveship.app:app --port 80
  3. Start dashboard:       python dashboard/serve.py
  4. Trigger a job:         Invoke-RestMethod http://localhost:80/teams-trigger ...
  5. Poll GET /pending — read the prompt — POST /respond with answer — repeat

No interactive input(). No stdin. Everything is HTTP.
"""

import argparse
import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

import sys
_DASHBOARD_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "dashboard")
sys.path.insert(0, _DASHBOARD_DIR)
from db import init_db, insert_llm_request, update_llm_response, correlate_calls_to_current_job


class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── Pending-request queue (one slot — HiveShip calls are sequential per agent) ─
_pending_lock = threading.Lock()
_pending_event = threading.Event()      # signaled when a response arrives
_pending_prompt: dict | None = None     # the prompt waiting for a response
_pending_response: str | None = None    # the response from Copilot/user

# ── Globals ───────────────────────────────────────────────────────────────────
_call_counter = 0
_counter_lock = threading.Lock()

_telemetry_path = os.path.join(_DASHBOARD_DIR, "telemetry.jsonl")


def _log_telemetry(record: dict) -> None:
    record["ts"] = int(time.time() * 1000)
    with open(_telemetry_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _next_id():
    global _call_counter
    with _counter_lock:
        _call_counter += 1
        return _call_counter


GOLD  = "\033[93m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
DIM   = "\033[90m"
RESET = "\033[0m"
BOLD  = "\033[1m"


class MockLLMHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ── GET endpoints ─────────────────────────────────────────────────────
    def do_GET(self):
        if self.path == "/v1/models":
            self._json_ok({
                "object": "list",
                "data": [{"id": "mock", "object": "model", "owned_by": "hiveship-mock"}],
            })
            return

        if self.path == "/pending":
            # Return the current pending prompt (or empty if none)
            with _pending_lock:
                if _pending_prompt is not None:
                    self._json_ok({"pending": True, **_pending_prompt})
                else:
                    self._json_ok({"pending": False})
            return

        if self.path == "/calls":
            # Return all telemetry records (for Copilot to inspect)
            records = []
            if os.path.exists(_telemetry_path):
                with open(_telemetry_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                records.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            self._json_ok(records)
            return

        self.send_error(404)

    # ── POST endpoints ────────────────────────────────────────────────────
    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(content_len)

        if self.path == "/v1/chat/completions":
            self._handle_completion(raw)
            return

        if self.path == "/respond":
            self._handle_respond(raw)
            return

        self.send_error(404)

    def _handle_completion(self, raw: bytes):
        """OpenAI-compatible completion — blocks until /respond is called."""
        global _pending_prompt, _pending_response

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
            return

        call_id = _next_id()
        messages = payload.get("messages", [])
        model = payload.get("model", "mock")
        response_format = payload.get("response_format")

        system_msg = ""
        user_msg = ""
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            elif m["role"] == "user":
                user_msg = m["content"]

        schema_name = None
        schema_props = []
        if response_format:
            js = response_format.get("json_schema", {})
            schema_name = js.get("name")
            schema_props = list(js.get("schema", {}).get("properties", {}).keys())

        # Log to telemetry
        _log_telemetry({
            "type": "llm_request",
            "call_id": call_id,
            "model": model,
            "system": system_msg[:500],
            "prompt": user_msg,
            "schema": schema_name,
        })

        # Persist to DB
        try:
            insert_llm_request(call_id, model, schema_name, system_msg, user_msg)
            correlate_calls_to_current_job()
        except Exception:
            pass

        # Print to terminal
        print(f"\n{GOLD}{'═'*60}{RESET}")
        print(f"{GOLD}  CALL #{call_id}  │  schema: {schema_name or 'text'}{RESET}")
        print(f"{GOLD}{'═'*60}{RESET}")
        if system_msg:
            print(f"{DIM}[SYS] {system_msg[:150]}{'...' if len(system_msg)>150 else ''}{RESET}")
        print(f"{CYAN}[PROMPT] {user_msg[:300]}{'...' if len(user_msg)>300 else ''}{RESET}")
        print(f"{GOLD}  ⏳ Waiting for response via POST /respond ...{RESET}")

        # ── Set pending prompt and WAIT ───────────────────────────────────
        with _pending_lock:
            _pending_response = None
            _pending_event.clear()
            _pending_prompt = {
                "call_id": call_id,
                "system": system_msg,
                "prompt": user_msg,
                "schema": schema_name,
                "schema_props": schema_props,
                "model": model,
            }

        # Block until /respond is called (timeout 10 min)
        t0 = time.perf_counter()
        got_response = _pending_event.wait(timeout=600)
        duration_ms = int((time.perf_counter() - t0) * 1000)

        with _pending_lock:
            response_text = _pending_response or ""
            _pending_prompt = None
            _pending_response = None

        if not got_response:
            response_text = '{"error": "Mock LLM timeout — no response posted to /respond within 10 minutes"}'
            print(f"\n{GOLD}  ⚠ TIMEOUT — no response received{RESET}")

        # Log response to telemetry
        _log_telemetry({
            "type": "llm_response",
            "call_id": call_id,
            "response": response_text[:2000],
            "duration_ms": duration_ms,
        })

        # Persist response to DB
        try:
            update_llm_response(call_id, response_text[:2000], duration_ms)
        except Exception:
            pass

        print(f"{GREEN}  ✓ Response #{call_id} — {len(response_text)} chars, {duration_ms}ms{RESET}")

        # Build OpenAI response
        self._json_ok({
            "id": f"mock-{call_id}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response_text},
                "finish_reason": "stop",
            }],
            "usage": {
                "prompt_tokens": len(user_msg.split()),
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(user_msg.split()) + len(response_text.split()),
            },
        })

    def _handle_respond(self, raw: bytes):
        """Receive a response from Copilot/user and unblock the waiting completion."""
        global _pending_response

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON body")
            return

        response_text = payload.get("response", "")
        if isinstance(response_text, dict):
            response_text = json.dumps(response_text)

        with _pending_lock:
            if _pending_prompt is None:
                self._json_ok({"ok": False, "error": "No pending prompt"})
                return
            _pending_response = response_text
            _pending_event.set()

        self._json_ok({"ok": True, "call_id": _pending_prompt["call_id"] if _pending_prompt else None})

    def _json_ok(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description="Mock LLM server for HiveShip testing")
    parser.add_argument("--port", type=int, default=11435, help="Port (default 11435)")
    args = parser.parse_args()

    # Clear telemetry file on start (session-scoped hot log)
    with open(_telemetry_path, "w", encoding="utf-8") as f:
        pass

    # Initialize SQLite DB (persistent across restarts)
    init_db()

    server = ThreadingHTTPServer(("0.0.0.0", args.port), MockLLMHandler)
    server.timeout = None

    print(f"\n{BOLD}{GOLD}╔══════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{GOLD}║   HiveShip Mock LLM Server                          ║{RESET}")
    print(f"{BOLD}{GOLD}║                                                      ║{RESET}")
    print(f"{BOLD}{GOLD}║   LLM endpoint:  http://localhost:{args.port}/v1/chat/completions  ║{RESET}")  # noqa
    print(f"{BOLD}{GOLD}║   Poll prompts:  GET  http://localhost:{args.port}/pending    ║{RESET}")
    print(f"{BOLD}{GOLD}║   Send answer:   POST http://localhost:{args.port}/respond    ║{RESET}")
    print(f"{BOLD}{GOLD}╚══════════════════════════════════════════════════════╝{RESET}")
    print(f"\nCopilot agent workflow:")
    print(f"  1. Poll:    Invoke-RestMethod http://localhost:{args.port}/pending")
    print(f"  2. Answer:  Invoke-RestMethod -Method Post -Uri http://localhost:{args.port}/respond \\")
    print(f'              -Body \'{{"response": "your answer"}}\' -ContentType application/json')
    print(f"\nTelemetry: {_telemetry_path}")
    print(f"\n{GREEN}Waiting for LLM calls...{RESET}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down mock LLM server.")
        server.server_close()


if __name__ == "__main__":
    main()
