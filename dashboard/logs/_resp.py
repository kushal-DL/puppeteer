"""Write response for current call."""
import json, pathlib

readme = """\
# silver-pancake

A FastAPI application containerized with Docker best practices.

## Docker Setup

### Dockerfile.txt

This project uses a **multi-stage Docker build** for a lean, secure production image:

**Stage 1 (Builder):**
- Base image: `python:3.11.9-slim`
- Creates a Python virtual environment at `/opt/venv`
- Installs all pip dependencies from `requirements.txt` into the venv

**Stage 2 (Runtime):**
- Base image: `python:3.11.9-slim`
- Copies only the pre-built venv from the builder stage (no build tools in production)
- Installs `curl` (for health checks) and `git` (for runtime needs)
- Runs as non-root user `appuser` for security
- Exposes port 80
- Includes a `HEALTHCHECK` that polls `/health` every 30 seconds

### Building & Running

```bash
docker build -f Dockerfile.txt -t silver-pancake .
docker run -p 80:80 --env-file .env silver-pancake
```

### .dockerignore

The `.dockerignore` file excludes non-essential directories from the Docker context:
- `business-case/`, `docs/`, `sandbox/`, `legacy/`, `dashboard/`
- `.git/`, `__pycache__/`, `*.pyc`, `.env`, `.venv`

## API

The app runs on port 80 via uvicorn. Check health at `GET /health`.

## Dependencies

See `requirements.txt`:
- fastapi
- uvicorn
- pydantic
- google-generativeai
"""

delivery = {
    "files": [
        {"path": "README.md", "content": readme},
    ],
    "commit_message": "docs: add README with Docker setup explanation",
    "pr_title": "Add README with Docker build explanation",
}

resp = {"response": delivery}
pathlib.Path("dashboard/logs/current_response.json").write_text(
    json.dumps(resp, ensure_ascii=False), encoding="utf-8"
)
print("OK")
