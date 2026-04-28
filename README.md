# HiveShip

An autonomous SDLC orchestrator that transforms plain-English goals into fully executed, PR-delivered codebase changes — with zero human intervention.

Describe what you want built. HiveShip decomposes your goal into a team of specialist AI agents, executes them in parallel as a dependency-aware DAG, self-reviews the output for correctness, and opens a pull request with the result. When you leave review comments on the PR, HiveShip picks them up via webhook and autonomously pushes fixes.

```
Developer           HiveShip                         GitHub
   │                   │                                │
   │  "Build X"        │                                │
   ├──────────────────►│                                │
   │                   │  1. Plan  (LLM decomposes)     │
   │                   │  2. Execute (parallel agents)  │
   │                   │  3. Review (self-check)        │
   │                   │  4. Ship   ─────────────────► PR
   │                   │                                │
   │  "@sdlc-bot fix"  │◄──────── webhook ──────────────┤
   │                   │  5. Investigate + fix ────────► Push
```

---

## Features

- **Multi-Agent DAG Execution** — Goals are decomposed into 1–8 specialist agents (planner, coder, tester, documenter, etc.) that run in parallel with dependency resolution via `ThreadPoolExecutor`. Agents communicate through file-based artifacts.

- **Dynamic Helper Spawning** — When an agent is blocked (missing context, unresolved dependency), HiveShip automatically spawns a helper agent to unblock it. Up to 6 dynamic helpers per job, with per-agent block limits to prevent runaway spirals.

- **Self-Review Loop** — After all agents complete, a reviewer agent checks the combined output for concrete issues (syntax errors, missing imports, security bugs). A fixer agent corrects problems, and the cycle repeats until approved or the maximum review cycles are exhausted.

- **Cross-Reference Validation** — Before committing, HiveShip validates that all inter-file imports and references in the delivered code actually resolve.

- **Cascade Pruning** — If an agent fails, all transitive dependents are pruned instantly rather than left hanging.

- **Dual LLM Provider Support** — Works with **Google Gemini** (via `google-genai` SDK) and **Ollama** (auto-detects native vs. OpenAI-compatible mode). Structured output is enforced at the API level, not via prompt text.

- **GitHub Webhook Integration** — Receives PR comment events via `/github-webhook` (HMAC-verified). When someone comments on a HiveShip PR, it autonomously investigates the feedback, generates a fix, and pushes a new commit.

- **Real-Time Event Streaming** — The `/stream/{job_id}` endpoint delivers Server-Sent Events so clients can watch the DAG unfold live: agent starts, completions, failures, helper spawns, and pipeline phases.

- **Observability Dashboard** — A standalone web UI (Flask-based) that polls HiveShip for job data, tracks LLM call telemetry, and visualises agent state timelines and event logs.

- **Secure by Default** — Git authentication uses header injection (PAT never written to disk or `.gitconfig`). Secrets are redacted in all logs. Path traversal and protected-path guards prevent writes to `.github/`, `.git/`, `.env`, etc.

---

## Architecture

```
auto-sdlc/
├── app.py              # FastAPI entry point — mounts routers only
├── config.py           # Environment variables, constants, fast-fail checks
├── models.py           # Pydantic v2 schemas (AgentTask, WorkflowPlan, ReviewResult, etc.)
├── llm.py              # LLM abstraction: GeminiModel, OllamaModel, retry logic
├── dag.py              # DAG execution engine: parallel agents, helper spawning, pruning
├── job_store.py        # Thread-safe in-memory job tracking with event logs
├── git_utils.py        # Git subprocess wrapper with Basic-auth header injection
├── workspace.py        # File I/O: validation, write, read with budgets, repo summary
├── routes/
│   ├── generation.py   # /teams-trigger — planner → DAG → review → PR
│   ├── status.py       # /health, /status/{job_id}, /stream/{job_id} (SSE)
│   └── webhook.py      # /github-webhook — PR comment → investigate → fix → push
├── client/
│   └── sdlc.ps1        # PowerShell CLI: interactive goal → live DAG event stream
├── dashboard/
│   ├── serve.py        # Observability dashboard server
│   ├── index.html      # Single-page dashboard UI (dark theme)
│   ├── db.py           # SQLite persistence for jobs and LLM calls
│   ├── dev_test.py     # Copilot-driven testing bridge (no API key required)
│   └── mock_llm.py     # Lightweight mock LLM server for dev-test
├── legacy/
│   └── app_old.py      # Monolithic single-file version (~2000 lines)
├── Dockerfile.txt      # Container image (Python 3.11-slim + git)
└── requirements.txt
```

### Module Responsibilities

| Module | What It Does |
|--------|-------------|
| `app.py` | Mounts FastAPI routers. No business logic. |
| `config.py` | Loads env vars (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `WEBHOOK_SECRET`), sets pipeline limits, fails fast on missing credentials. |
| `models.py` | All Pydantic schemas: `AgentTask`, `WorkflowPlan`, `FileArtifact`, `DeliveryPlan`, `ReviewResult`, `FailureClass` (12 typed failure modes), `RecoveryRecipe`, `AgentStatus` lifecycle enum. |
| `llm.py` | Unified LLM interface. `GeminiModel` wraps the `google-genai` SDK. `OllamaModel` auto-detects native Ollama vs OpenAI-compatible endpoints. `sync_generate_and_parse()` handles structured output with retry. |
| `dag.py` | Runs the agent DAG with `ThreadPoolExecutor(max_workers=4)` and `wait(FIRST_COMPLETED)`. Handles blocked agents, helper spawning, cascade pruning, and per-agent lifecycle tracking. |
| `job_store.py` | Thread-safe dict-based job store. Tracks status, events (ms-epoch timestamps), and per-agent lifecycle states. |
| `git_utils.py` | `run_git()` injects `http.extraHeader` for Basic-auth. `github_api_request()` for REST API calls. PAT never touches disk. |
| `workspace.py` | `get_repo_summary()`, `validate_files()` (path traversal guard), `write_files()`, `read_agent_files()` with configurable budgets. |

---

## Pipeline Flow

### Generation (Goal → Pull Request)

1. **Clone** — Shallow-clone the target repo's base branch.
2. **Plan** — LLM decomposes the goal into a `WorkflowPlan` with up to 8 specialist agents.
3. **Pre-Validate** — Check that all `read_files` and `input_keys` referenced in the plan actually exist. Re-prompt the planner if not.
4. **Execute DAG** — Run agents in parallel. Each agent reads file context + upstream artifact context, generates output, and writes to `artifacts_dir/*.txt`. Blocked agents emit `_BLOCKED.json` → helpers are spawned automatically.
5. **Deliver** — A delivery agent synthesizes all artifacts into self-contained source files with a commit message and PR title.
6. **Cross-Reference Check** — Validate that inter-file imports resolve.
7. **Self-Review Loop** — Reviewer checks for concrete issues (syntax, missing imports, security). Fixer corrects. Repeat up to `MAX_REVIEW_CYCLES`.
8. **Ship** — Write files, commit, push feature branch, open PR against base branch.

### Revision (PR Comment → Fix → Push)

1. GitHub sends a webhook event when someone comments on a HiveShip PR.
2. HiveShip parses the PR diff, identifies affected files, and summarises the changes.
3. A reviewer agent evaluates the comment, then a fixer agent generates corrections.
4. The fix is committed and pushed to the same PR branch.

---

## Quickstart

### Prerequisites

- Python 3.11+
- A GitHub PAT with repo access
- A webhook secret (any random string — configure it on both ends)
- One of:
  - `GEMINI_API_KEY` (for Google Gemini)
  - An Ollama instance (local or remote)

### Environment Variables

Create a `.env` file at the repo root (never committed):

```env
GITHUB_TOKEN=ghp_your_pat_here
WEBHOOK_SECRET=your_webhook_secret
GEMINI_API_KEY=your_gemini_key          # if using Gemini
OLLAMA_BASE_URL=http://localhost:11434   # if using Ollama
OLLAMA_MODEL=llama3                      # Ollama model name
DEFAULT_LLM_PROVIDER=gemini              # "gemini" or "ollama"
BASE_BRANCH=develop                      # target branch for PRs
```

### Run Locally

```bash
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 80
```

### Run with Docker

```bash
docker build -f Dockerfile.txt -t hiveship .
docker run -p 80:80 --env-file .env hiveship
```

### Deploy to Azure Container Apps

```bash
# Build and push to your container registry, then deploy:
az containerapp up \
  --name hiveship \
  --image <registry>/hiveship:latest \
  --env-vars GITHUB_TOKEN=<pat> WEBHOOK_SECRET=<secret> GEMINI_API_KEY=<key> \
  --target-port 80

# IMPORTANT: On ACA Consumption profiles, set minReplicas >= 1 with
# cpuAllocation: Always — otherwise the CPU throttles to ~0 when idle,
# freezing background pipeline threads.
```

---

## Usage

### PowerShell Client

The interactive CLI (`client/sdlc.ps1`) is the easiest way to submit goals and watch the DAG execute in real time.

1. Edit the configuration block at the top of `client/sdlc.ps1`:
   ```powershell
   $BaseUrl      = "https://your-app.azurecontainerapps.io"
   $LlmProvider  = "gemini"       # or "ollama"
   $OllamaBaseUrl = ""            # Ollama endpoint if using ollama
   $OllamaModel  = "llama3"       # Ollama model name
   $ReviewCycles = 3              # 0–5
   ```

2. Run:
   ```powershell
   .\client\sdlc.ps1
   ```

3. Enter your goal when prompted (multiline — blank line to submit). The client streams colour-coded DAG events:
   - ◷ `agent_started` (yellow)
   - ✓ `agent_done` (green)
   - ✗ `agent_failed` (red)
   - ⊘ `agent_pruned` (yellow)
   - ⚡ `helper_spawned` (magenta)

### HTTP API

**Trigger a generation job:**

```bash
curl -X POST http://localhost/teams-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Add a REST endpoint that returns server uptime",
    "llm_provider": "gemini",
    "review_cycles": 2
  }'
```

Response: `{ "job_id": "abc123", "status": "running" }`

**Check job status:**

```bash
curl http://localhost/status/abc123
```

**Stream live events (SSE):**

```bash
curl -N http://localhost/stream/abc123
```

**Health check:**

```bash
curl http://localhost/health
```

### GitHub Webhook

Configure a webhook on your GitHub repository:

- **URL**: `https://your-app.azurecontainerapps.io/github-webhook`
- **Content type**: `application/json`
- **Secret**: Same value as `WEBHOOK_SECRET`
- **Events**: Issue comments

When someone comments on a HiveShip-created PR, the system automatically investigates and pushes fixes.

---

## Observability Dashboard

A standalone web UI for monitoring jobs, agent states, and LLM call telemetry.

```bash
cd dashboard
python serve.py --hiveship http://localhost:80 --port 8050
```

Open `http://localhost:8050`. The dashboard shows:
- Job list with status badges (running / complete / failed)
- Agent state timelines per job
- Event log with timestamps
- PR link badges
- LLM call analytics

---

## Dev-Test Mode (No API Key Required)

`dashboard/dev_test.py` provides a file-based testing bridge that lets you (or an AI assistant like Copilot) drive the LLM responses manually — no API key needed.

```bash
python dashboard/dev_test.py "your goal text"
python dashboard/dev_test.py                    # uses a default goal
```

How it works:
1. Starts a mock LLM server, HiveShip, and the dashboard locally.
2. Triggers a generation job.
3. Each time HiveShip needs an LLM response, the mock server writes `current_prompt.json`.
4. You (or Copilot) read the prompt, craft a response, and write `current_response.json`.
5. The pipeline continues with your response.
6. After the PR is created, the script polls GitHub for review comments and can trigger revision jobs the same way.

This is useful for understanding the pipeline, debugging agent behaviour, or testing without burning API credits.

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | *required* | GitHub PAT with repo access |
| `WEBHOOK_SECRET` | *required* | HMAC secret for webhook verification |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_API_KEY` | — | API key for remote Ollama/OpenAI-compat endpoints |
| `OLLAMA_MODEL` | `llama3` | Model name for Ollama |
| `DEFAULT_LLM_PROVIDER` | `gemini` | `"gemini"` or `"ollama"` |
| `BASE_BRANCH` | `develop` | Target branch for generated PRs |
| `BOT_USERNAME` | `kushal-sharma-24` | GitHub username to detect self-loop |
| `BASE_WORKSPACE` | `/app/workspace` | Working directory for repo clones |
| `MAX_REVIEW_CYCLES` | `2` | Maximum self-review iterations (0–5) |

### Pipeline Limits

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_DYNAMIC_AGENTS` | 6 | Max helper agents spawned per job |
| `MAX_BLOCKS_PER_AGENT` | 2 | Block limit before an agent is failed |
| `ARTIFACT_CHAR_LIMIT` | 12,000 | Max chars per artifact read |
| `READ_BUDGET` | 30,000 | Total char budget for file reads per agent |
| `MAX_READ_FILES` | 10 | Max repo files an agent can read |

---

## LLM Providers

### Google Gemini

Uses the `google-genai` SDK (`from google import genai`). Model: `gemini-2.5-flash`. Structured output is enforced at the API level via `response_mime_type="application/json"` and `response_schema`.

### Ollama

Supports two modes, auto-detected based on the base URL and model name:

- **Native Ollama** (`/api/chat`) — Used when the URL is `localhost:11434` and the model name has no `/`. Schema passed via the `format` field.
- **OpenAI-Compatible** (`/v1/chat/completions`) — Used for remote endpoints or HuggingFace model names (containing `/`). Schema passed as `response_format.json_schema`.

---

## Agent Lifecycle

Each agent in the DAG follows this state machine:

```
PENDING → RUNNING → COMPLETED
                  → FAILED
                  → BLOCKED → (helper spawned) → re-queued
                  → PRUNED (cascaded from upstream failure)
```

Failures are classified into 12 typed modes (`FailureClass`), each mapped to a recovery recipe:

| Failure | Recovery |
|---------|----------|
| `json_parse` | Retry with repair prompt |
| `cross_ref_broken` | Validate and fix |
| `review_rejected` | Corrective prompt |
| `agent_blocked` | Spawn helper |
| `llm_timeout` | Retry with repair |
| `context_overflow` | Reduce context and retry |
| `dag_stalled` | Escalate |

---

## License

Private repository. All rights reserved.
