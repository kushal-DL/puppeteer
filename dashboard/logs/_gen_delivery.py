"""Generate the DeliveryPlan response for the Dockerfile rewrite job."""
import json
from pathlib import Path

dockerfile_content = """\
# ---- Stage 1: Builder -------------------------------------------------------
FROM python:3.11.9-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Runtime -------------------------------------------------------
FROM python:3.11.9-slim AS runtime

# Install runtime system dependencies:
#   git  - required for clone/commit/push inside pipelines
#   curl - required for HEALTHCHECK
RUN apt-get update \\
    && apt-get install -y --no-install-recommends git curl \\
    && rm -rf /var/lib/apt/lists/* \\
    && git config --system user.email "agent@pipeline.local" \\
    && git config --system user.name "AI Pipeline Agent"

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user for security
RUN groupadd --gid 1000 appuser \\
    && useradd --uid 1000 --gid 1000 --create-home appuser

WORKDIR /app

# Copy only the application source files (not the entire repo)
COPY app.py config.py models.py llm.py dag.py job_store.py git_utils.py workspace.py ./
COPY routes/ ./routes/

# Ensure the non-root user owns the app directory
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\
    CMD curl -f http://localhost:80/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
"""

dockerignore_content = """\
# Exclude non-production directories from Docker build context
business-case/
docs/
sandbox/
legacy/
dashboard/

# Version control
.git/
.github/

# Python artifacts
__pycache__/
*.pyc
*.pyo

# Environment and config
.env
.env.*

# Documentation
*.md

# Editor/IDE files
.gitignore
auto-sdlc.code-workspace
Dockerfile.txt
.dockerignore

# Other non-production directories
pipeline-docs/
client/

# Notebooks and data
*.ipynb
*.jsonl
"""

delivery = {
    "files": [
        {"path": "Dockerfile.txt", "content": dockerfile_content},
        {"path": ".dockerignore", "content": dockerignore_content},
    ],
    "commit_message": "refactor: multi-stage Dockerfile with venv, non-root user, and HEALTHCHECK",
    "pr_title": "Rewrite Dockerfile to multi-stage build with security hardening",
}

response = {"response": json.dumps(delivery, ensure_ascii=False)}
Path("dashboard/logs/current_response.json").write_text(
    json.dumps(response, ensure_ascii=False), encoding="utf-8"
)
print(f"Wrote DeliveryPlan ({len(delivery['files'])} files) to current_response.json")
