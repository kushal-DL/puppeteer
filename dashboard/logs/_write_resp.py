"""Helper to write LLM response file (avoids PowerShell encoding issues)."""
import json, pathlib, sys

# Arg 1 is the raw content. If it's valid JSON, write as-is; otherwise wrap.
raw = sys.argv[1] if len(sys.argv) > 1 else ""
try:
    data = json.loads(raw)
    if "response" in data:
        out_text = raw
    else:
        out_text = json.dumps({"response": raw})
except (json.JSONDecodeError, TypeError):
    out_text = json.dumps({"response": raw})

out = pathlib.Path("dashboard/logs/current_response.json")
out.write_text(out_text, encoding="utf-8")
