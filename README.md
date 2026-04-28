# HiveShip

An autonomous SDLC orchestrator that transforms plain-English goals into fully executed, PR-delivered codebase changes — with zero human intervention. Unlike stateless coding assistants, HiveShip **learns from every run**: it accumulates repository knowledge, indexes past jobs, and codifies reusable procedures — so the 50th PR against a repo is measurably better and cheaper than the 1st.

```
Developer           HiveShip                         GitHub
   │                   │                                │
   │  "Build X"        │                                │
   ├──────────────────►│                                │
   │                   │  1. Recall (memory + skills)   │
   │                   │  2. Plan  (LLM decomposes)     │
   │                   │  3. Execute (parallel agents)  │
   │                   │  4. Review (self-check)        │
   │                   │  5. Ship   ─────────────────► PR
   │                   │  6. Learn  (extract facts)     │
   │                   │                                │
   │  "@sdlc-bot fix"  │◄─────── webhook ──────────────┤
   │                   │  7. Investigate + fix ────────► Push
```

---

## Why HiveShip (vs. Copilot / Claude Code)

Tools like GitHub Copilot Coding Agent and Claude Code are excellent developer assistants. HiveShip is justified when specific conditions apply:

| Condition | HiveShip Advantage |
|-----------|-------------------|
| **Data sovereignty** | Runs on your Azure infra. With Ollama, fully air-gapped — your code never leaves your network. Copilot and Claude Code send code to external APIs. |
| **Cost at scale** | Token-cost only; one instance serves the whole org. No per-seat licensing. For large teams, the cost curve is fundamentally different. |
| **Pipeline control** | Every step (plan, execute, review, deliver) is customisable. Add compliance checks, architecture gates, domain-specific validation. Vendor tools ship what they ship. |
| **Automatic knowledge capture** | Memory, job history, and skills are extracted automatically after every run. Copilot's `copilot-instructions.md` and Claude's `CLAUDE.md` require manual maintenance — in practice, they rot. |
| **Vendor independence** | Not locked into GitHub/Anthropic roadmaps. Swap LLM providers, modify review logic, extend the DAG — it's your system. |

**What HiveShip is NOT:**
- Not a replacement for interactive coding assistants (Copilot in the IDE, Claude Code at the terminal)
- Not stronger on raw model quality — Copilot uses GPT-4o/Claude; HiveShip uses Gemini Flash (cheaper, less capable on complex reasoning)
- Not zero-maintenance — it's another system to operate, monitor, and upgrade

**Best positioning:** Developers use Copilot/Claude at their desk for interactive work. HiveShip runs in the background handling the queue of well-defined tasks (add endpoint, write migration, fix accessibility, update docs). They're complementary.

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

- **Secure by Default** — Git authentication uses header injection (PAT never written to disk or `.gitconfig`). Secrets are redacted in all logs via `RedactingFormatter`. Path traversal and protected-path guards prevent writes to `.github/`, `.git/`, `.env`, etc.

- **Persistent Memory** — HiveShip maintains a per-repo memory store (`.hiveship/memory.md`) with injection-scanning guards (11 regex patterns for prompt injection, exfiltration, invisible unicode). After each PR, the system extracts useful facts from the run and adds them to memory. All entries are deduplicated and capped at 3000 chars. Mutations during a run don't affect prompts (frozen snapshot pattern).

- **Job History & Session Search** — Every job is recorded in a SQLite database (WAL mode + FTS5 full-text search). Past jobs are searchable by goal, agent output, or repo — and relevant history snippets are injected into the planner prompt so agents benefit from prior work.

- **Reusable Skills** — HiveShip discovers and codifies procedural knowledge as skills (`.hiveship/skills/{name}/SKILL.md`). Skills are created automatically after complex jobs (4+ agents), indexed for the planner, and injected as full procedures for agents. Supports per-repo and global skill directories.

- **Trajectory Compression** — When agent context grows too large, HiveShip compresses the middle of the context (protecting the first 2 and last 3 entries) via LLM summarisation or truncation fallback. This keeps token costs bounded on long runs.

- **Token & Cost Tracking** — Every LLM call records input/output tokens and estimated cost. Usage is accumulated per-job and recorded in history. Supports pricing for Gemini model tiers.

- **Smart Error Classification** — 20+ regex patterns classify failures into typed categories (rate limit, billing, auth, context overflow, payload too large, safety block, etc.). Each category maps to a `RecoveryHint` with `retryable`, `should_compress`, and `should_fallback` flags. Retry uses decorrelated jitter backoff.

- **Redacting Observability** — Structured logging with `RedactingFormatter` that strips API keys, Bearer/Basic tokens, GitHub PATs, and Google API keys. Per-job log correlation via thread-local `session_context`. Rotating file handlers for `agent.log` and `errors.log`.

---

## Architecture

```
auto-sdlc/
├── src/hiveship/                    # Main Python package
│   ├── __init__.py
│   ├── app.py                       # FastAPI entry — mounts routers, calls setup_logging()
│   ├── config.py                    # Env vars, constants, fast-fail checks
│   ├── models.py                    # Pydantic v2 schemas + error classification
│   ├── logging.py                   # RedactingFormatter, rotating handlers, session context
│   ├── llm/                         # LLM abstraction (multi-adapter)
│   │   ├── __init__.py              # sync_generate_with_retry, usage accumulation, jittered backoff
│   │   ├── base.py                  # LLMModel protocol, UsageRecord, PRICING, estimate_cost
│   │   ├── gemini.py                # GeminiModel (google-genai SDK) + usage extraction
│   │   └── ollama.py                # OllamaModel (OpenAI-compat + native) + usage extraction
│   ├── engine/                      # DAG execution engine
│   │   ├── __init__.py
│   │   ├── dag.py                   # DAG executor, agent runner, helpers, memory/skill injection
│   │   ├── job_store.py             # Thread-safe in-memory job tracking
│   │   ├── planner.py               # Plan generation + pre-validation
│   │   └── compression.py           # Trajectory compression (head/tail protect, LLM summarise)
│   ├── memory/                      # Learning loop — memory, history, skills
│   │   ├── __init__.py              # Re-exports: MemoryStore, MemoryManager, JobHistoryDB, etc.
│   │   ├── store.py                 # MemoryStore: CRUD on .hiveship/memory.md, injection scanning
│   │   ├── manager.py               # MemoryManager: prefetch, frozen snapshot, extraction prompt
│   │   ├── history.py               # JobHistoryDB: SQLite WAL + FTS5, job/message recording
│   │   ├── search.py                # search_past_jobs: FTS5 search, windowed snippet extraction
│   │   └── skills.py                # SkillStore: discover, load, create, patch, YAML frontmatter
│   ├── git/                         # Git & GitHub integration
│   │   ├── __init__.py
│   │   └── client.py                # run_git, github_api_request
│   ├── workspace/                   # File I/O and repo interaction
│   │   ├── __init__.py
│   │   ├── files.py                 # validate_files, write_files, cross-refs
│   │   └── repo.py                  # sanitize_branch_name, get_repo_summary
│   └── routes/                      # FastAPI route modules
│       ├── __init__.py
│       ├── generation.py            # POST /teams-trigger — full pipeline with learning loop
│       ├── status.py                # GET /health, /status/{job_id}, /stream/{job_id} (SSE)
│       └── webhook.py               # POST /github-webhook — PR comment → fix → push
├── tests/                           # Test suite (mirrors src/)
│   ├── conftest.py
│   └── unit/
│       ├── test_models.py
│       ├── test_hardening.py        # Error classification + compression tests
│       ├── engine/
│       │   └── test_job_store.py
│       ├── memory/
│       │   ├── test_store.py
│       │   ├── test_manager.py
│       │   ├── test_history.py
│       │   ├── test_search.py
│       │   └── test_skills.py
│       └── workspace/
│           ├── test_files.py
│           └── test_repo.py
├── client/                          # Client scripts & dev-test launchers
│   ├── sdlc.ps1                     # PowerShell TUI client (production)
│   ├── copilot_bridge.py            # Copilot-driven file-bridge orchestrator
│   ├── dev_launch.py                # Simple server launcher (manual testing)
│   └── mock_llm.py                  # Blocking mock LLM server for dev-test
├── dashboard/                       # Observability UI (standalone app)
│   ├── serve.py
│   ├── index.html
│   └── db.py
├── docker/                          # Container build
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                            # Architecture diagrams, analysis
│   ├── architecture/
│   │   ├── diagram-executive.mmd
│   │   └── diagram-technical.mmd
│   └── analysis/
│       └── failure-modes.md
├── pyproject.toml                   # Modern packaging (pip install -e ".[dev]")
├── .env.example                     # Template for env vars
└── README.md
```

### Module Responsibilities

| Module | What It Does |
|--------|-------------|
| `hiveship.app` | Mounts FastAPI routers, calls `setup_logging()`. No business logic. |
| `hiveship.config` | Loads env vars, sets pipeline limits (`COMPRESSION_TARGET`, `AGENT_OUTPUT_CAP`, `DAG_TURN_BUDGET`), fails fast on missing credentials. |
| `hiveship.models` | Pydantic schemas: `AgentTask`, `WorkflowPlan`, `FileArtifact`, `DeliveryPlan`, `ReviewResult`. Error classification: `FailureClass` (20+ typed modes), `RecoveryHint`, `classify_failure()`, `get_recovery_hint()`. |
| `hiveship.logging` | `RedactingFormatter` (6 regex patterns), `set_session_context(job_id)` for per-job correlation, `setup_logging()` with rotating file handlers. |
| `hiveship.llm` | `sync_generate_with_retry` (jittered backoff), `sync_generate_and_parse`, usage accumulation (`get_total_cost()`, `reset_usage()`). |
| `hiveship.llm.base` | `LLMModel` protocol, `UsageRecord` dataclass, `PRICING` dict, `estimate_cost()`, `make_usage()`. |
| `hiveship.llm.gemini` | Gemini adapter (`google-genai` SDK) + `ResponseShim` with usage extraction. |
| `hiveship.llm.ollama` | Ollama adapter (OpenAI-compat + native) with usage extraction. |
| `hiveship.engine.dag` | DAG executor with memory/skill injection, trajectory compression, helper spawning, cascade pruning. |
| `hiveship.engine.job_store` | Thread-safe dict-based job store with event logs. |
| `hiveship.engine.planner` | `validate_plan_against_repo` — re-prompts planner on missing file references. |
| `hiveship.engine.compression` | `should_compress()`, `compress_context()` — head/tail protection, LLM summarisation or truncation fallback. |
| `hiveship.memory.store` | `MemoryStore` — CRUD on `.hiveship/memory.md`, injection scanning (11 patterns), deduplication, 3000 char limit. |
| `hiveship.memory.manager` | `MemoryManager` — `prefetch()` with frozen snapshot, `build_memory_context_block()`, `build_extraction_prompt()`, `apply_extracted_entries()`. |
| `hiveship.memory.history` | `JobHistoryDB` — SQLite WAL + FTS5, `record_job()`, `record_message()`, `search_messages()`, decorrelated jitter retry on lock contention. |
| `hiveship.memory.search` | `search_past_jobs()` — FTS5 grouped by job, windowed snippet extraction, `format_search_results_for_prompt()`. |
| `hiveship.memory.skills` | `SkillStore` — discover/load/create/patch/delete, YAML frontmatter parsing, `build_skill_index_for_prompt()`, `build_skill_content_for_agent()`. |
| `hiveship.git.client` | `run_git()` (Basic-auth header injection), `github_api_request()`. PAT never touches disk. |
| `hiveship.workspace.files` | `validate_files()` (path traversal guard), `write_files()`, `read_agent_files()`, `validate_cross_references()`. |
| `hiveship.workspace.repo` | `sanitize_branch_name()`, `get_repo_summary()`. |
| `hiveship.routes.generation` | `/teams-trigger` — full pipeline: memory prefetch → skill discovery → history search → plan → DAG → review → PR → extract memory/skills → record history. |
| `hiveship.routes.status` | `/health`, `/status/{job_id}`, `/stream/{job_id}` (SSE). |
| `hiveship.routes.webhook` | `/github-webhook` — PR comment → investigate → fix → push. |

---

## Pipeline Flow

### Generation (Goal → Pull Request)

1. **Initialise** — Create job in history DB, set session context for log correlation, reset usage counters.
2. **Recall** — Prefetch memory (frozen snapshot), discover skills, search past jobs for relevant history.
3. **Clone** — Shallow-clone the target repo's base branch.
4. **Plan** — LLM decomposes the goal into a `WorkflowPlan` with up to 8 specialist agents. Memory, skill index, and history snippets are injected into the planner prompt.
5. **Pre-Validate** — Check that all `read_files` and `input_keys` referenced in the plan actually exist. Re-prompt the planner if not.
6. **Execute DAG** — Run agents in parallel. Each agent receives file context + upstream artifacts + memory block + skill procedures. Trajectory compression kicks in when context exceeds `COMPRESSION_TARGET`.
7. **Deliver** — A delivery agent synthesizes all artifacts into self-contained source files with a commit message and PR title.
8. **Cross-Reference Check** — Validate that inter-file imports resolve.
9. **Self-Review Loop** — Reviewer checks for concrete issues. Fixer corrects. Repeat up to `MAX_REVIEW_CYCLES`.
10. **Ship** — Write files, commit, push feature branch, open PR against base branch.
11. **Learn** — Extract memory entries from the run via LLM. Create skills for complex jobs (4+ agents). Record final status and cost in history DB.

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

Create a `.env` file at the repo root (never committed). Copy from `.env.example`:

```env
# Required
GITHUB_TOKEN=ghp_your_pat_here
WEBHOOK_SECRET=your_webhook_secret
REPO_OWNER=your_github_username_or_org
REPO_NAME=your_repo_name

# LLM provider (at least one required)
GEMINI_API_KEY=your_gemini_key          # if using Gemini
OLLAMA_BASE_URL=http://localhost:11434   # if using Ollama
OLLAMA_MODEL=llama3                      # Ollama model name
DEFAULT_LLM_PROVIDER=gemini              # "gemini" or "ollama"

# Optional
BASE_BRANCH=develop                      # target branch for PRs
BOT_USERNAME=your_github_username        # for webhook self-loop prevention
```

> **Note:** `REPO_OWNER` and `REPO_NAME` set the default target repo. You can also override them per-request by passing `repo_owner` and `repo_name` in the `/teams-trigger` request body — this lets a single HiveShip deployment target repos across different owners and orgs. Your `GITHUB_TOKEN` must have access to all target repos.

### Run Locally

```bash
pip install -e ".[dev]"
uvicorn hiveship.app:app --host 0.0.0.0 --port 80
```

### Run Tests

```bash
pytest tests/
```

### Run with Docker

```bash
docker build -f docker/Dockerfile -t hiveship .
docker run -p 80:80 --env-file .env hiveship
```

### Docker Compose (app + dashboard)

```bash
docker compose -f docker/docker-compose.yml up
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

## Dev-Test Mode (Copilot Bridge — No LLM API Key Required)

`client/copilot_bridge.py` provides a file-based testing bridge where **GitHub Copilot acts as the LLM**. HiveShip runs its full pipeline (plan → DAG → review → PR), but instead of calling Gemini or Ollama, each LLM call is routed to a file that Copilot reads and responds to. No Gemini/OpenAI API key needed — only `GITHUB_TOKEN` is required (for cloning and PR creation).

### Prerequisites

- **VS Code** with the [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot) extension installed
- **Python 3.11+**
- A **GitHub PAT** (fine-grained) with `Contents: Read and write` + `Pull requests: Read and write` on the target repo

### Step-by-Step

1. **Clone and install:**
   ```bash
   git clone https://github.com/kushal-DL/puppeteer.git
   cd puppeteer
   pip install -e ".[dev]"
   ```

2. **Configure `.env`** at the repo root (copy from `.env.example`):
   ```env
   GITHUB_TOKEN=github_pat_...        # your fine-grained PAT
   WEBHOOK_SECRET=any-random-string
   REPO_OWNER=your-org-or-username    # target repo owner
   REPO_NAME=your-target-repo         # target repo name
   BASE_BRANCH=main                   # branch PRs target
   ```

3. **Open VS Code** in the `puppeteer` folder:
   ```bash
   code .
   ```

4. **Switch Copilot to Agent mode:** Open the Copilot Chat panel (Ctrl+Shift+I), click the mode dropdown at the top, and select **"Agent"**.

5. **Ask Copilot to run the bridge:** In the Copilot Agent chat, type:
   ```
   run the command: python client/copilot_bridge.py "your goal text here"
   ```
   Copilot will execute the command in the terminal. The script starts three servers:
   - Mock LLM server (port 11435)
   - HiveShip (port 80)
   - Dashboard (port 8050 — open http://localhost:8050/static/index.html to watch)

6. **Copilot handles the rest:** Each time HiveShip needs an LLM response, the script writes the prompt to `client/logs/current_prompt.json`. Copilot reads it, crafts a response, and writes `client/logs/current_response.json`. This repeats for every agent in the DAG (typically 10–15 calls for a complex goal).

7. **PR is created** on the target repo when all agents complete and the review passes.

### How It Works Under the Hood

1. Starts a mock LLM server (port 11435), HiveShip (port 80), and the dashboard (port 8050).
2. Triggers a generation job with the given goal.
3. Each time HiveShip needs an LLM response, the mock server blocks. The script polls for the pending prompt and writes it to `client/logs/current_prompt.json`.
4. Copilot reads the prompt, crafts a response, and writes `client/logs/current_response.json`.
5. The script reads the response file and posts it to the mock LLM, which unblocks HiveShip.
6. After the PR is created, the script polls GitHub for PR comments (3-minute window) and automatically triggers revision jobs the same way.

The full learning-loop pipeline runs in dev-test mode: memory prefetch, skill discovery, history search, and post-PR extraction. Copilot will see memory/skill context in the prompts when available.

### Configuration

Environment variables (set in `.env` at the repo root):
- `REPO_OWNER` / `REPO_NAME` — **required** target repository
- `GITHUB_TOKEN` — **required** for cloning and PR creation (needs `Contents` + `Pull requests` write permissions)
- `BASE_BRANCH` — branch PRs target (default: `develop`)
- `DEV_TEST_GOAL` — override the default goal text

There is also a simpler launcher (`client/dev_launch.py`) that starts the servers and triggers the job but does not run the file-bridge loop — useful for manual testing via HTTP.

---

## Configuration Reference

All configuration is done via the **`.env` file** at the repo root (see `.env.example` for a template). Environment variables are loaded at startup by `hiveship.config`. For containerized deployments, pass them via `--env-file .env` or your orchestrator's secrets manager.

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | *required* | GitHub PAT with repo access |
| `WEBHOOK_SECRET` | *required* | HMAC secret for webhook verification |
| `REPO_OWNER` | *required* | GitHub owner or org for the target repo |
| `REPO_NAME` | *required* | GitHub repository name |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_API_KEY` | — | API key for remote Ollama/OpenAI-compat endpoints |
| `OLLAMA_MODEL` | `llama3` | Model name for Ollama |
| `DEFAULT_LLM_PROVIDER` | `gemini` | `"gemini"` or `"ollama"` |
| `BASE_BRANCH` | `develop` | Target branch for generated PRs |
| `BOT_USERNAME` | — | GitHub username to detect self-loop |
| `BASE_WORKSPACE` | `/app/workspace` | Working directory for repo clones |
| `MAX_REVIEW_CYCLES` | `2` | Maximum self-review iterations (0–5) |
| `COMPRESSION_TARGET` | `30000` | Char threshold before trajectory compression triggers |
| `AGENT_OUTPUT_CAP` | `12000` | Max chars per agent output |
| `DAG_TURN_BUDGET` | `200000` | Total char budget for the DAG execution |
| `LLM_MAX_RETRIES` | `3` | Max retries per LLM call (with jittered backoff) |
| `LLM_FALLBACK_ENABLED` | `true` | Whether to fallback to alternate provider on failure |

> **Multi-repo support:** `REPO_OWNER` and `REPO_NAME` in `.env` set the defaults. You can override them per-request by including `repo_owner` and `repo_name` in the `/teams-trigger` JSON body. This allows targeting repos from any owner or org. Your `GITHUB_TOKEN` must have access to all target repos.

### Pipeline Limits

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_DYNAMIC_AGENTS` | 6 | Max helper agents spawned per job |
| `MAX_BLOCKS_PER_AGENT` | 2 | Block limit before an agent is failed |
| `ARTIFACT_CHAR_LIMIT` | 12,000 | Max chars per artifact read |
| `READ_BUDGET` | 30,000 | Total char budget for file reads per agent |
| `MAX_READ_FILES` | 10 | Max repo files an agent can read |
| `MEMORY_CHAR_LIMIT` | 3,000 | Max chars in persistent memory store |
| `SKILL_CONTENT_BUDGET` | 5,000 | Max chars of skill content injected per agent |

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

Failures are classified into 20+ typed modes (`FailureClass`), each mapped to a `RecoveryHint` with `retryable`, `should_compress`, and `should_fallback` flags:

| Failure | Recovery |
|---------|----------|
| `json_parse` | Retry with repair prompt |
| `cross_ref_broken` | Validate and fix |
| `review_rejected` | Corrective prompt |
| `agent_blocked` | Spawn helper |
| `llm_timeout` | Retry with jittered backoff |
| `context_overflow` | Compress context and retry |
| `rate_limit` | Retry with exponential backoff |
| `billing` | Fallback to alternate provider |
| `auth` / `auth_permanent` | Fail fast (no retry) |
| `overloaded` | Retry with backoff |
| `payload_too_large` | Compress and retry |
| `provider_policy_blocked` | Fallback to alternate provider |
| `llm_blocked` | Retry with rephrased prompt |
| `dag_stalled` | Escalate |

---

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).
