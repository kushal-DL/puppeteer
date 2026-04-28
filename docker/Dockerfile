FROM python:3.11-slim

WORKDIR /app

# git is required at runtime (clone, commit, push inside pipelines)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/* \
    && git config --global user.email "agent@pipeline.local" \
    && git config --global user.name "AI Pipeline Agent"

# Install package (deps cached via pyproject.toml layer)
COPY pyproject.toml .
COPY src/ ./src/
RUN pip install --no-cache-dir .

EXPOSE 80

CMD ["uvicorn", "hiveship.app:app", "--host", "0.0.0.0", "--port", "80"]
