"""Write a response JSON file for the dev_test file bridge.

Reads plain text from dashboard/logs/response_draft.txt, wraps it into
the expected JSON format, and writes dashboard/logs/current_response.json.

Usage:  python dashboard/_write_response.py
"""
import json
from pathlib import Path

DRAFT = Path("dashboard/logs/response_draft.txt")
OUT = Path("dashboard/logs/current_response.json")

text = DRAFT.read_text(encoding="utf-8").strip()
payload = json.dumps({"response": text}, ensure_ascii=False)
OUT.write_text(payload, encoding="utf-8")
DRAFT.unlink()
print(f"Wrote {len(payload)} chars to {OUT} (draft was {len(text)} chars)")
