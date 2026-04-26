"""Write Call #5 DeliveryPlan response."""
import json, pathlib

dockerfile = """\
# Stage 1: Builder - install dependencies into a virtual environment
FROM python:3.11.9-slim AS builder

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - lean production image
FROM python:3.11.9-slim

RUN apt-get update \\
    && apt-get install -y --no-install-recommends curl git \\
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY app.py config.py models.py llm.py dag.py job_store.py git_utils.py workspace.py ./
COPY routes/ ./routes/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=15s \\
    CMD curl -f http://localhost:80/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
"""

dockerignore = """\
business-case/
docs/
sandbox/
legacy/
dashboard/
.git/
__pycache__/
*.pyc
*.pyo
.env
.venv
*.egg-info/
"""

delivery = {
    "files": [
        {"path": "Dockerfile.txt", "content": dockerfile},
        {"path": ".dockerignore", "content": dockerignore},
    ],
    "commit_message": "feat: multi-stage Dockerfile with venv, non-root user, and HEALTHCHECK",
    "pr_title": "Rewrite Dockerfile.txt with multi-stage build, non-root user, and HEALTHCHECK",
}

resp = {"response": delivery}
pathlib.Path("dashboard/logs/current_response.json").write_text(
    json.dumps(resp, ensure_ascii=False), encoding="utf-8"
)
print("Written OK")
