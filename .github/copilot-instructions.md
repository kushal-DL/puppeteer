# Project Guidelines — HiveShip (auto-sdlc)

## What This Project Is

An autonomous SDLC orchestrator deployed as a FastAPI container on Azure Container Apps. It receives a user goal (via `/teams-trigger` or GitHub PR webhook), decomposes it into an agent DAG via an LLM planner, executes the DAG in parallel threads, self-reviews the output, and opens a GitHub PR with the result.

## Codebase Layout

The project uses a `src/` layout with the `hiveship` Python package:

```
auto-sdlc/
├── src/hiveship/                    # Main Python package
│   ├── __init__.py
│   ├── app.py                       # FastAPI entry — mounts routers, calls setup_logging()
│   ├── config.py                    # Env vars, constants, fast-fail
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
│       ├── status.py                # GET /health, /status, /stream
│       └── webhook.py               # POST /github-webhook
├── tests/                           # Test suite (mirrors src/)
│   ├── conftest.py
│   └── unit/
│       ├── test_models.py
│       ├── test_hardening.py
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
├── docker/                          # Dockerfile + docker-compose
├── docs/                            # Architecture diagrams, analysis
├── pyproject.toml                   # Modern packaging (replaces requirements.txt)
└── .env.example                     # Template for env vars
```

## Module Map

| Module | Responsibility |
|--------|---------------|
| `hiveship.app` | FastAPI entry point — mounts routers, calls `setup_logging()`, no logic |
| `hiveship.config` | All env vars, constants, fast-fail checks, ACA warning, `COMPRESSION_TARGET`, `AGENT_OUTPUT_CAP`, `DAG_TURN_BUDGET` |
| `hiveship.models` | Pydantic schemas: `AgentTask`, `WorkflowPlan`, `FileArtifact`, `DeliveryPlan`, `ReviewResult`, `FileRequest`. Error classification: `FailureClass` (20+ regex patterns), `RecoveryHint`, `classify_failure()`, `get_recovery_hint()` |
| `hiveship.logging` | `RedactingFormatter` (6 patterns), `set_session_context(job_id)`, `setup_logging()` with rotating handlers |
| `hiveship.llm` | LLM abstraction: `sync_generate_with_retry` (jittered backoff), `sync_generate_and_parse`, usage accumulation (`get_total_cost`, `reset_usage`), `LLM_MAX_RETRIES`, `LLM_FALLBACK_ENABLED` |
| `hiveship.llm.base` | `LLMModel` protocol, `UsageRecord` dataclass, `PRICING` dict, `estimate_cost()`, `make_usage()` |
| `hiveship.llm.gemini` | Gemini adapter (google-genai SDK) + `ResponseShim` with usage extraction |
| `hiveship.llm.ollama` | Ollama adapter (OpenAI-compat + native) with usage extraction |
| `hiveship.engine.dag` | DAG executor: `_run_single_agent`, `_spawn_helper_agent`, `execute_dag` — with memory/skill injection and trajectory compression |
| `hiveship.engine.job_store` | Thread-safe in-memory job dict |
| `hiveship.engine.planner` | `validate_plan_against_repo` (pre-validation) |
| `hiveship.engine.compression` | `should_compress()`, `compress_context()` — head/tail protection, LLM summarise or truncation fallback |
| `hiveship.memory.store` | `MemoryStore` — CRUD on `.hiveship/memory.md`, injection scanning (11 patterns), deduplication, 3000 char limit |
| `hiveship.memory.manager` | `MemoryManager` — `prefetch()` frozen snapshot, `build_memory_context_block()`, `build_extraction_prompt()`, `apply_extracted_entries()` |
| `hiveship.memory.history` | `JobHistoryDB` — SQLite WAL + FTS5, `record_job()`, `record_message()`, `search_messages()`, jitter retry on lock contention |
| `hiveship.memory.search` | `search_past_jobs()` — FTS5 grouped by job, windowed snippet extraction, `format_search_results_for_prompt()` |
| `hiveship.memory.skills` | `SkillStore` — discover/load/create/patch/delete, YAML frontmatter, `build_skill_index_for_prompt()`, `build_skill_content_for_agent()` |
| `hiveship.git.client` | `run_git` (Basic-auth header injection), `github_api_request` |
| `hiveship.workspace.files` | `validate_files`, `write_files`, `read_agent_files`, `validate_cross_references` |
| `hiveship.workspace.repo` | `sanitize_branch_name`, `get_repo_summary` |
| `hiveship.routes.status` | `/health`, `/status/{job_id}`, `/stream/{job_id}` (SSE) |
| `hiveship.routes.generation` | `/teams-trigger`, `_sync_generation_pipeline` — full pipeline with memory prefetch, skill discovery, history search, extraction, cost recording |
| `hiveship.routes.webhook` | `/github-webhook`, `_sync_pr_revision` (PR comment → fix → push) |

## LLM Integration

### SDK: `google-genai` (package `google-genai`, import `from google import genai`)

- Client: `genai.Client(api_key=...)` — initialized once in `llm.py`
- Call: `client.models.generate_content(model=..., contents=..., config=...)`
- Model: `gemini-2.5-flash`

### Structured Output

Structured output is enforced at the API level, **not** via prompt text:

1. `sync_generate_and_parse()` sets `config["response_schema"] = PydanticClass`
2. `GeminiModel.generate_content()` sets `response_mime_type = "application/json"` and passes the config dict to the SDK
3. The SDK's `t.t_schema()` resolves `$ref`/`$defs`, converts types to Gemini-native (`STRING`, `OBJECT`, `ARRAY`), adds `property_ordering`

**NEVER** manually call `model_json_schema()` to set `response_json_schema` — this bypasses the SDK transform and causes the model to echo the schema definition instead of producing actual values.

## Code Style

- Python 3.11, type hints on public functions. No runtime `typing.TYPE_CHECKING` tricks.
- Pydantic v2 models with `field_validator` (not `validator`).
- Synchronous LLM/git operations run in `asyncio.to_thread` to avoid blocking the FastAPI event loop.
- Background pipelines are thread-based (not Celery/RQ) — acceptable for single-instance POC.
- PowerShell client targets PS 5.1+ (Windows built-in); avoid PS 7-only syntax.
- All `write_text()` calls must specify `encoding="utf-8"` (Windows `charmap` codec breaks on Unicode).

## Architecture Constraints

- The DAG engine (`hiveship.engine.dag`) uses `concurrent.futures.ThreadPoolExecutor(max_workers=4)` with `wait(FIRST_COMPLETED)`.
- Agents communicate via file-based artifacts on disk (`artifacts_dir/*.txt`). Blocked agents emit `_BLOCKED.json` signal files.
- `MAX_DYNAMIC_AGENTS = 6` and `MAX_BLOCKS_PER_AGENT = 2` prevent helper-budget exhaustion.
- Planner pre-validation in `hiveship.engine.planner` re-prompts the planner if it references files that don't exist in the cloned repo.
- Git auth uses `http.extraHeader` injection — PAT is never written to disk or `.gitconfig`.
- Path traversal and protected-path guards live in `hiveship.workspace.files.validate_files`.
- Memory store (`hiveship.memory.store`) scans all entries with 11 regex patterns for prompt injection, exfiltration, and invisible unicode before persisting.
- `MemoryManager` uses a frozen snapshot pattern — mutations during a run don't affect prompts mid-pipeline.
- `JobHistoryDB` uses SQLite WAL mode with FTS5 full-text search. Falls back to LIKE-based search if FTS5 is unavailable.
- Trajectory compression (`hiveship.engine.compression`) protects the first 2 and last 3 context entries, summarising the middle.
- Error classification (`hiveship.models.classify_failure`) uses 20+ compiled regex patterns returning typed `FailureClass` + `RecoveryHint`.
- LLM retries use decorrelated jitter backoff: `min(cap, base * 2^attempt + random)`.

## Build & Deploy

```bash
# Local development (needs GITHUB_TOKEN, WEBHOOK_SECRET, and GEMINI_API_KEY or OLLAMA_BASE_URL)
pip install -e ".[dev]"
uvicorn hiveship.app:app --host 0.0.0.0 --port 80

# Run tests
pytest tests/

# Container
docker build -f docker/Dockerfile -t hiveship .
docker run -p 80:80 --env-file .env hiveship

# Docker Compose (app + dashboard)
docker compose -f docker/docker-compose.yml up
```

## Testing a Goal (PowerShell)

```powershell
# Edit the CONFIGURATION section in client/sdlc.ps1, then:
.\client\sdlc.ps1
```

## Conventions

- Never log or print PATs, API keys, or auth headers. `run_git` redacts `Authorization` on error.
- LLM responses are always fence-stripped (```` ```json ``` ````) before `json.loads`.
- Job events use millisecond-epoch timestamps (`int(time.time() * 1000)`).
- Bot self-loop prevention: skip comments from `BOT_USERNAME` or starting with `BOT_COMMENT_PREFIX`.
- All imports use fully-qualified `hiveship.*` paths (e.g. `from hiveship.config import GEMINI_KEY`).
