"""One-shot: write the DeliveryPlan response file."""
import json
from pathlib import Path

dockerfile = (
    "# Stage 1: Builder\n"
    "FROM python:3.11.9-slim AS builder\n"
    "\n"
    "WORKDIR /build\n"
    "\n"
    "RUN python -m venv /opt/venv\n"
    'ENV PATH="/opt/venv/bin:$PATH"\n'
    "\n"
    "COPY requirements.txt .\n"
    "RUN pip install --no-cache-dir --upgrade pip && \\\n"
    "    pip install --no-cache-dir -r requirements.txt\n"
    "\n"
    "# Stage 2: Runtime\n"
    "FROM python:3.11.9-slim\n"
    "\n"
    "# Install runtime system dependencies (git for repo ops, curl for healthcheck)\n"
    "RUN apt-get update && \\\n"
    "    apt-get install -y --no-install-recommends git curl && \\\n"
    "    rm -rf /var/lib/apt/lists/*\n"
    "\n"
    "# Configure git identity\n"
    'RUN git config --global user.email "agent@pipeline.local" && \\\n'
    '    git config --global user.name "AI Pipeline Agent"\n'
    "\n"
    "# Create non-root user\n"
    "RUN useradd --create-home --shell /bin/bash appuser\n"
    "\n"
    "WORKDIR /app\n"
    "\n"
    "# Copy virtualenv from builder stage\n"
    "COPY --from=builder /opt/venv /opt/venv\n"
    'ENV PATH="/opt/venv/bin:$PATH"\n'
    "\n"
    "# Copy application source files\n"
    "COPY app.py config.py models.py llm.py dag.py job_store.py git_utils.py workspace.py ./\n"
    "COPY routes/ ./routes/\n"
    "COPY requirements.txt ./\n"
    "\n"
    "# Set ownership to non-root user\n"
    "RUN chown -R appuser:appuser /app\n"
    "\n"
    "USER appuser\n"
    "\n"
    "EXPOSE 80\n"
    "\n"
    "HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \\\n"
    "    CMD curl -f http://localhost:80/health || exit 1\n"
    "\n"
    'CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]\n'
)

dockerignore = (
    "# Directories excluded from Docker build context\n"
    "business-case/\n"
    "docs/\n"
    "sandbox/\n"
    "legacy/\n"
    "dashboard/\n"
    "\n"
    "# Version control\n"
    ".git\n"
    ".github\n"
    ".gitignore\n"
    "\n"
    "# Python artifacts\n"
    "__pycache__/\n"
    "*.pyc\n"
    "*.pyo\n"
    "*.egg-info/\n"
    "dist/\n"
    "build/\n"
    ".eggs/\n"
    "\n"
    "# Environment and secrets\n"
    ".env\n"
    ".env.*\n"
    "\n"
    "# Node\n"
    "node_modules/\n"
    "\n"
    "# IDE and OS\n"
    ".vscode/\n"
    ".idea/\n"
    "*.swp\n"
    "*.swo\n"
    ".DS_Store\n"
    "Thumbs.db\n"
    "\n"
    "# Misc\n"
    "*.md\n"
    "!README.md\n"
    "*.code-workspace\n"
    "pipeline-docs/\n"
    "client/\n"
)

plan = {
    "files": [
        {"path": "Dockerfile.txt", "content": dockerfile},
        {"path": ".dockerignore", "content": dockerignore},
    ],
    "commit_message": "feat: multi-stage Dockerfile with venv, non-root user, healthcheck, and .dockerignore",
    "pr_title": "Multi-stage Dockerfile build with security hardening",
}

resp = {"response": json.dumps(plan, ensure_ascii=False)}
Path("dashboard/logs/current_response.json").write_text(
    json.dumps(resp, ensure_ascii=False), encoding="utf-8"
)
print("Written DeliveryPlan response")
