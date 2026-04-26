# Project Guidelines — auto-sdlc

## What This Project Is

An autonomous SDLC orchestrator deployed as a FastAPI container on Azure Container Apps. It receives a user goal (via `/teams-trigger` or GitHub PR webhook), decomposes it into an agent DAG via an LLM planner, executes the DAG in parallel threads, self-reviews the output, and opens a GitHub PR with the result.

## Codebase Layout

Two implementations exist:

- **Modular app** (root: `app.py` + `config.py`, `models.py`, `llm.py`, `dag.py`, `job_store.py`, `git_utils.py`, `workspace.py`, `routes/`) — production layout. Stays flat at root for Dockerfile COPY and `uvicorn app:app`.
- **Monolithic app** (`legacy/app_old.py`) — single ~2000-line file with all logic. Kept for prototyping. **Must stay in sync** with the modular version for all LLM/schema/pipeline changes.

## Repository Structure

```
auto-sdlc/
├── app.py, config.py, models.py, llm.py    # Production app modules (root)
├── dag.py, job_store.py, git_utils.py, workspace.py
├── routes/                                  # FastAPI route modules
├── client/sdlc.ps1                          # PowerShell client
├── legacy/app_old.py                        # Monolithic version
├── docs/                                    # Diagrams, analysis, references
├── sandbox/                                 # Experiments, notebooks
├── Dockerfile.txt, requirements.txt, .dockerignore
```

## Module Map

| Module | Responsibility |
|--------|---------------|
| `app.py` | FastAPI entry point — mounts routers only, no logic |
| `config.py` | All env vars, constants, fast-fail checks, ACA warning |
| `models.py` | Pydantic schemas: `AgentTask`, `WorkflowPlan`, `FileArtifact`, `DeliveryPlan`, `ReviewResult`, `FileRequest` |
| `llm.py` | LLM abstraction: `GeminiModel` (google-genai SDK), `OllamaModel` (OpenAI-compat + native), `sync_generate_with_retry`, `sync_generate_and_parse` |
| `job_store.py` | Thread-safe in-memory job dict (`create_job`, `update_job`, `append_job_event`, `get_job`) |
| `git_utils.py` | `run_git` (Basic-auth header injection), `github_api_request` |
| `workspace.py` | File I/O helpers: `sanitize_branch_name`, `get_repo_summary`, `validate_files`, `write_files`, `read_agent_files`, `read_artifact_context` |
| `dag.py` | DAG execution engine: `_run_single_agent`, `_spawn_helper_agent`, `execute_dag` |
| `routes/status.py` | `/health`, `/status/{job_id}`, `/stream/{job_id}` (SSE) |
| `routes/generation.py` | `/teams-trigger`, `_sync_generation_pipeline`, planner pre-validation |
| `routes/webhook.py` | `/github-webhook`, `_sync_pr_revision` (PR comment → fix → push) |
| `client/sdlc.ps1` | PowerShell client: interactive goal prompt → dispatch → live DAG event stream |
| `Dockerfile.txt` | Container image definition (Python 3.11-slim + git) |

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

- The DAG engine (`dag.py`) uses `concurrent.futures.ThreadPoolExecutor(max_workers=4)` with `wait(FIRST_COMPLETED)`.
- Agents communicate via file-based artifacts on disk (`artifacts_dir/*.txt`). Blocked agents emit `_BLOCKED.json` signal files.
- `MAX_DYNAMIC_AGENTS = 6` and `MAX_BLOCKS_PER_AGENT = 2` prevent helper-budget exhaustion.
- Planner pre-validation in `routes/generation.py` re-prompts the planner if it references files that don't exist in the cloned repo.
- Git auth uses `http.extraHeader` injection — PAT is never written to disk or `.gitconfig`.
- Path traversal and protected-path guards live in `workspace.validate_files`.

## Build & Deploy

```bash
# Local (needs GITHUB_TOKEN, WEBHOOK_SECRET, and GEMINI_API_KEY or OLLAMA_BASE_URL)
uvicorn app:app --host 0.0.0.0 --port 80

# Container
docker build -f Dockerfile.txt -t auto-sdlc .
docker run -p 80:80 --env-file .env auto-sdlc
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
- When changing LLM/schema/pipeline logic, apply the same change to **both** `legacy/app_old.py` and the modular files.
