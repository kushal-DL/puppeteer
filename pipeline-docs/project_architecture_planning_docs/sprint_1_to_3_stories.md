# CDE - Detailed Sprint Stories & Subtasks (Sprints 1-3)

**Team:** 9 developers | **Capacity:** ~65 SP/sprint | **Go-live:** Jul 7, 2026  
**Planning rule (Sprints 2+):** 1 SP = 1 person-day. Every story is independently assignable to one developer.

## Team Structure

| Team | Senior Tech Lead (Python) | PySpark Developer | Python Developer |
|------|--------------------------|-------------------|------------------|
| **A** | **Suresh** | Prashanth | Pankaj |
| **B** | **Raghuram** | Gulfraz | Shikhar |
| **C** | **Uttam** | Naveen | Nisarg |

> Senior Tech Leads drive design/review. Sprints 2+ stories are small, independently assignable units with test-first and baseline observability.

---

# Sprint 1 - Foundation & Infrastructure Setup
**Mar 18 - Mar 31** | ~65 SP | *(In Progress - stories listed for reference only)*

- API Contract Discovery & Cross-Language Interface Definition
- Provisioning AWS Glue, Step Functions, EventBridge, SQS, Lambda, SNS, S3 with CloudFormation scripts
  - Request a test user in AWS devscratch
- Complete Data Exporter hello-world service setup in Kraken Kubernetes
  - Add service and developers to Vault namespace
  - Service mesh configuration
  - RPL setup
- Document Logging, Health Checks and Standard Scans for Architectural Components
- IFM knowledge ramp-up + onboarding

---

# Sprint 2 - Core Pipeline Skeleton & Strategy Pattern
**Apr 1 - Apr 14** | **65 SP total**

**Goal (unchanged):** Build the Step Functions skeleton (EventBridge → Init Lambda → Glue → wait/resume), implement `core_runner.py` and `expense_strategy.py` stubs, and complete a first green-path end-to-end run with dummy data.

## Sprint 2 Delivery Guardrails
- Every implementation story starts with tests or contract checks before production code.
- Every touched service (Step Functions, Lambda, Glue, K8s placeholder) must emit baseline logs, metrics, and health/readiness signals.
- Every story is independently assignable to one developer.
- Logging must use structured JSON aligned to Application Log Format (v2), include `correlation_id` propagation, and exclude sensitive personal data.
- Containerized components must emit logs to stdout/stderr; heartbeat/progress signals are required for long-running or async stages.

## Sprint 2 Developer-Assignable Stories

| ID | Story | SP | Assignee | Test-First Output | Observability Output |
|----|-------|---:|----------|-------------------|----------------------|
| 2.1 | Deliver baseline observability and SFN payload contracts | 7 | Suresh | Contract/schema tests | Shared log+metric contract |
| 2.2 | Deliver Step Functions skeleton orchestration path | 8 | Pankaj | ASL simulation tests | State transition + branch metrics |
| 2.3 | Deliver wait-token timeout and callback validation package | 6 | Shikhar | Negative-path + callback tests | Timeout/resume metrics |
| 2.4 | Deliver Init Lambda strategy loader and base interface | 7 | Raghuram | Lambda + interface tests | Loader success/failure metrics |
| 2.5 | Deliver strategy implementation, import, and argument parsing | 6 | Nisarg | Strategy/import/parser tests | Strategy selection + parse logs |
| 2.6 | Deliver Glue bootstrap and pass-routing scaffold | 6 | Naveen | Bootstrap/routing tests | Job startup + pass metrics |
| 2.7 | Deliver ORC/Parquet I/O and Pass 2 no-op data path | 7 | Prashanth | Fixture round-trip tests | I/O count and latency metrics |
| 2.8 | Deliver raw-arrival and glue-done SNS event wiring | 7 | Gulfraz | Event payload contract tests | Topic publish/consume counters |
| 2.9 | Deliver CDP fixture generation pack and catalog | 6 | Nisarg | Fixture generation/shape tests | Fixture inventory metrics |
| 2.10 | Deliver Sprint 2 green-path E2E and regression evidence | 5 | Uttam | E2E + regression runbook tests | End-to-end timing + correlation evidence |

---

## Sprint 2 Story Details

### Story 2.1: Deliver Baseline Observability and SFN Payload Contracts
**SP: 7 | Assignee:** Suresh (Team A)

**Description:** Deliver versioned JSON Schema contract definitions and reference payload bundles for baseline cross-service observability. The observability contract defines minimum required log fields (correlation_id, service, timestamp, level, message, execution_id), metric naming taxonomy, and health-signal formats used by all downstream Zone 2 and Zone 3 components. The SFN payload contract defines the state input/output envelope and field constraints for Init Lambda, Choice branching, Glue task arguments, and callback stages.

**Scope:**
- Log field contracts in `src/contracts/log_contract_v2.json` (JSON Schema)
- Metric naming taxonomy in `src/contracts/metric_taxonomy.md` with examples: `cde.sfn.state_duration_ms`, `cde.sfn.state_transitions`, `cde.sfn.choice_branch_selection`
- Health signal contract in `src/contracts/health_signals.json` (readiness and liveliness probe formats)
- SFN payload envelope schema in `src/contracts/sfn_payload_v2.json` (requires: `execution_id`, `correlation_id`, `data` envelope, `config` object for workflow flags)

**Acceptance Criteria:**
1. JSON Schema files are checked into `src/contracts/` with versioning in filename (e.g., `log_contract_v2.json`); each schema includes field type constraints, required field list, and schema format declaration
2. Contract tests in `tests/unit/test_contracts.py` validate: all required log fields present with correct types, metrics follow naming pattern (regex: `^cde\.[a-z_]+\.(count|duration_ms|latency_ms)$`), malformed payloads rejected by validators, SFN state envelope conforms to schema
3. One reference payload bundle is generated and checked into `docs/payload_examples/` with four JSON files: `init_lambda_input.json`, `init_lambda_output.json`, `glue_task_input.json`, `callback_success_payload.json`
4. Story handoff includes: contract file paths, passing test output with example validation results, and one-paragraph approval note from tech lead

---

### Story 2.2: Deliver Step Functions Skeleton Orchestration Path
**SP: 8 | Assignee:** Pankaj (Team A)

**Description:** Deliver the generic Step Functions ASL skeleton. The state machine defines the complete fixed integration topology — EventBridge trigger, Init Lambda invocation (which loads the strategy file from S3 and returns workflow flags), Choice branching on those flags, Pass 1 and Pass 2 Glue task states, wait-token/callback async pattern, SQS message dispatch for KEDA worker scaling, and terminal states — but contains zero domain or strategy-specific logic. All workflow decisions are driven exclusively by the flags returned by Init Lambda.

**Architecture Scope:** Zone 2 Control Plane orchestration path (EventBridge schedule, Step Functions ASL states, Lambda and Glue task wiring).

**Acceptance Criteria:**
- ASL and deployment template changes are checked in and validated with no lint errors
- Simulation tests cover happy path and API-skip branch behavior
- EventBridge rule and SFN target wiring are deployed/configured for scheduled execution
- Execution evidence includes one successful run graph with expected state order and execution ID

---

### Story 2.3: Deliver Wait-Token Timeout and Callback Validation Package
**SP: 6 | Assignee:** Shikhar (Team B)

**Description:** Deliver robust async callback handling for the Kubernetes worker boundary including task-token timeout routing, callback payload validation, and resumability proof. This story implements the Step Functions wait state that follows the SQS message drop in the API-enrichment branch (executed when Init Lambda flags `requires_api_enrichment: true`). The wait state must enforce a timeout threshold of 24 hours and route timeout or callback validation failures to a DLQ task, while successful callbacks validate the task token and execution ID before resuming to the Pass 2 Glue task.

**Scope:**
- Wait state timeout threshold: `PT24H` (24 hours, configurable via CloudFormation parameter `AsyncTimeoutSeconds`)
- Callback message validation: task token and execution ID must be present and non-empty (enforced by Step Functions callback API validation)
- Timeout catch handler: catches `States.TaskFailedTimedOut`, routes to DLQ state named `AsyncCallbackDLQ`
- Callback error catch handler: catches `States.ALL` on callback errors, logs event, routes to DLQ

**Acceptance Criteria:**
1. Wait state with timeout/catch logic is checked into `infrastructure/step_functions/sfn_template.json`; timeout set to `PT24H` (configurable via `AsyncTimeoutSeconds` parameter); catch handler named `AsyncCallbackDLQ`; wait state transitions to Pass 2 Glue task on successful callback
2. State machine simulator tests in `tests/unit/test_sfn_states.py` validate: successful callback with valid task token resumes to correct downstream state, timeout after 24h triggers catch handler, invalid/missing task token in callback parameters rejected by Step Functions callback API validation
3. One callback smoke test in `tests/integration/test_async_callback.py` proves full path: SQS message drop → wait state entry → simulated K8s callback with valid task token and execution ID → resumed to Pass 2 state; test uses `AWSStepFunctionsClient.start_execution()` and `send_task_success()` with recorded execution ID
4. Logs include 4 named events: `async_callback_started` (with state_name), `callback_received` (with token_hash and execution_id), `timeout_occurred` (with wait_duration_sec), `callback_error` (with error_code and message); metrics: `cde.sfn.async_timeout_count`, `cde.sfn.callback_success_count`, `cde.sfn.callback_failure_count`

---

### Story 2.4: Deliver Init Lambda Strategy Loader and Base Interface
**SP: 7 | Assignee:** Raghuram (Team B)

**Description:** Deliver the Init Lambda strategy-loading infrastructure with a formal base interface so strategy modules can be loaded, validated, and executed consistently. Init Lambda reads the strategy Python module from the Strategy S3 bucket (path pattern: `s3://strategy-bucket/strategies/<strategy_name>_strategy.py`), dynamically imports the strategy class, instantiates it, and invokes its required methods to obtain workflow flags. The Lambda must validate that the strategy class implements all required interface methods before returning the flags to Step Functions for branch selection.

**Scope:**
- Base interface class `BaseStrategy` in `src/cde/strategy/base.py` with required abstract methods:
  - `requires_api_enrichment() -> bool`: returns whether downstream Pass 2 requires API-enriched data
  - `get_version() -> str`: returns strategy version (e.g., "1.0.0")
- Init Lambda source in `src/lambda/init_lambda.py`
- Lambda environment variables: `STRATEGY_BUCKET`, `STRATEGY_KEY_PREFIX` (default: `strategies/`)
- Lambda input from SFN: `{"strategy_name": "expense", "execution_id": "...", "correlation_id": "..."}`
- Lambda output JSON: `{"execution_id": "...", "correlation_id": "...", "requires_api_enrichment": bool, "strategy_version": "...", "strategy_name": "..."}`

**Acceptance Criteria:**
1. `BaseStrategy` abstract base class and Init Lambda loader code are checked into `src/cde/strategy/base.py` and `src/lambda/init_lambda.py`; base class uses `@abstractmethod` decorator for `requires_api_enrichment()` and `get_version()`; loader function signature: `load_strategy(strategy_name: str) -> BaseStrategy`
2. Unit tests in `tests/unit/test_init_lambda.py` cover 5 scenarios: (a) valid strategy load and instantiation (returns `BaseStrategy` with both methods implemented), (b) missing strategy file in S3 (raises `StrategyNotFoundError` with S3 key in message), (c) malformed strategy file (Python syntax error, raises `StrategyImportError` with line number), (d) strategy class missing required method (raises `InterfaceValidationError` listing missing methods), (e) S3 read timeout after 30s (raises `StrategyTimeoutError`)
3. Lambda output JSON conforms to contract from Story 2.1; test validates all 5 required output fields present with correct types; mocked S3 returns valid strategy Python code, loader returns valid instance
4. Logs include 4 named events: `strategy_load_started` (with strategy_name, s3_key), `strategy_loaded` (with version, class_name), `interface_validated` (with method_list), `workflow_flags_returned` (with requires_api_enrichment); metrics: `cde.lambda.strategy_load_success_count`, `cde.lambda.strategy_load_failure_count` (labeled by error_type)

---

### Story 2.5: Deliver Strategy Implementation, Import, and Argument Parsing
**SP: 6 | Assignee:** Nisarg (Team C)

**Description:** Deliver the first concrete strategy implementation (`ExpenseStrategy` class) and the Glue job argument parsing layer so `core_runner.py` can execute architecture-defined flow: SQL prefilter first, then complex transformations through `apply_transform`. The expense strategy implements the `BaseStrategy` interface from Story 2.4 and provides Pass 1/Pass 2 behavior through strategy-owned SQL and transformation methods. Glue receives the strategy name via job argument `--strategy_name` and dynamically imports and instantiates the strategy class at runtime.

**Scope:**
- Expense strategy class `ExpenseStrategy` in `src/cde/strategies/expense_strategy.py` implementing `BaseStrategy` interface
- Required methods in `ExpenseStrategy`: `__init__()` (no arguments), `requires_api_enrichment() -> bool`, `get_version() -> str`, `get_prefilter_sql(pass_id: int) -> str`, `apply_transform(df: DataFrame, pass_id: int, context: dict) -> DataFrame`
- Glue job arguments (passed via `--arg` in job definition):
  - `--strategy_name` (required, string: "expense")
  - `--pass_number` (required, int: 1 or 2)
  - `--correlation_id` (required, UUID string)
  - `--raw_s3_path` (required for Pass 1, string: `s3://bucket/path`)
  - `--intermediary_s3_path` (required for Pass 2, string: `s3://bucket/path`)
  - `--execution_id` (required, string for logging)
- Strategy config output shape: `{"requires_api_enrichment": bool, "version": str, "pass_handlers": ["execute_pass1", "execute_pass2"]}`

**Acceptance Criteria:**
1. `ExpenseStrategy` class is checked into `src/cde/strategies/expense_strategy.py` with signature: `class ExpenseStrategy(BaseStrategy):`; all 5 required methods implemented; `requires_api_enrichment()` returns bool (concrete value for Sprint 2), `get_version()` returns "1.0.0", `get_prefilter_sql(pass_id)` returns valid SQL string, and `apply_transform(...)` returns DataFrame
2. Glue argument parsing code in `src/cde/core_runner.py` with function `parse_glue_arguments(sys.argv) -> dict` that validates all 6 required arguments present and correct types; tests in `tests/unit/test_glue_arguments.py` cover: (a) valid parse with all args, (b) missing `--strategy_name` (raises `MissingArgumentError`), (c) missing `--pass_number` (raises `MissingArgumentError`), (d) invalid pass_number value (not 1 or 2, raises `InvalidArgumentError`), (e) malformed correlation_id UUID (raises `ValidationError`)
3. Strategy config snapshot test in `tests/unit/test_expense_strategy.py` validates `ExpenseStrategy().requires_api_enrichment()` returns expected bool, `get_version()` returns "1.0.0", `get_prefilter_sql(pass_id=1)` returns non-empty SQL, and `apply_transform(...)` exists and returns DataFrame; test artifact checked into `tests/fixtures/expense_strategy_snapshot.json`
4. Logs include 3 named events: `strategy_class_selected` (with strategy_name, class_name), `glue_arguments_parsed` (with pass_number, execution_id), `strategy_instantiated` (with version, requires_api_enrichment); metrics: `cde.glue.strategy_import_duration_ms`, `cde.glue.argument_parse_duration_ms`

---

### Story 2.6: Deliver Glue Bootstrap and Pass-Routing Scaffold
**SP: 6 | Assignee:** Naveen (Team C)

**Description:** Deliver the Glue job bootstrap and pass-routing dispatcher so the job initializes with baseline logs/metrics, selects pass behavior (Pass 1 or Pass 2) based on the Glue job argument `--pass_number`, and executes the architecture sequence in `core_runner.py`: SQL prefilter first, then complex transformations via `strategy.apply_transform(...)`. The bootstrap validates received Glue arguments (via Story 2.5), instantiates the selected strategy (via Story 2.4), and emits startup telemetry including app name, app version, selected pass number, and correlation ID.

**Scope:**
- Bootstrap code in `src/cde/core_runner.py` function `bootstrap_and_route()`
- Pass routing dispatcher: if `--pass_number == 1`, invoke `prefilter_sql = strategy.get_prefilter_sql(1)` then `strategy.apply_transform(df, pass_id=1, context=...)`; if `--pass_number == 2`, invoke `prefilter_sql = strategy.get_prefilter_sql(2)` then `strategy.apply_transform(df, pass_id=2, context=...)`
- Controlled failure triggers (tested as exception paths):
  1. Missing `--pass_number` argument: raises `MissingArgumentError`, logs `bootstrap_failed` event with reason "missing_pass_number"
  2. Invalid `--pass_number` value (not 1 or 2): raises `InvalidArgumentError`, logs `bootstrap_failed` event with reason "invalid_pass_number", invalid_value field
  3. Strategy instantiation failure (import error, missing method): raises `StrategyInstantiationError`, logs `bootstrap_failed` event with reason and error_message
- Startup telemetry: bootstrap duration, selected pass, strategy version

**Acceptance Criteria:**
1. Bootstrap and pass-routing code in `src/cde/core_runner.py` (function `bootstrap_and_route()`) with clear if/elif for pass 1 vs. 2 routing; argument validation called before routing; structure includes SQL prefilter + transform chain: `if pass_number == 1: sql = strategy.get_prefilter_sql(1); df = apply_sql_prefilter(df, sql); return strategy.apply_transform(df, 1, context); elif pass_number == 2: sql = strategy.get_prefilter_sql(2); df = apply_sql_prefilter(df, sql); return strategy.apply_transform(df, 2, context); else: raise InvalidArgumentError`
2. Tests in `tests/unit/test_glue_bootstrap.py` cover: (a) valid bootstrap with `--pass_number=1` (routes to Pass 1 handler, returns result), (b) valid bootstrap with `--pass_number=2` (routes to Pass 2 handler), (c) missing `--pass_number` (raises `MissingArgumentError`, logs `bootstrap_failed` event), (d) invalid `--pass_number=3` (raises `InvalidArgumentError`), (e) strategy instantiation failure (raises `StrategyInstantiationError`)
3. Runtime evidence from one successful `--pass_number=1` bootstrap includes logs with: `app.name="cde"`, `app.version="1.0.0"`, `pass_number=1`, `correlation_id=<uuid>`, `bootstrap_status="success"`, `bootstrap_duration_ms=<value>`
4. Metrics include: `cde.glue.bootstrap_duration_ms` (histogram), `cde.glue.pass_number_selected` (labeled counter: `pass=1`, `pass=2`), `cde.glue.bootstrap_failure_count` (labeled by error_type: `missing_arg`, `invalid_arg`, `instantiation_error`)

---

### Story 2.7: Deliver ORC/Parquet I/O and Pass 2 No-Op Data Path
**SP: 7 | Assignee:** Prashanth (Team A)

**Description:** Deliver the core data I/O path including ORC input ingestion for Pass 1, Parquet output writes to the Intermediary S3 bucket, and Pass 2 no-op behavior. For Pass 2 in Sprint 2, no-op means reading the Pass 1 Parquet output from Intermediary S3 and writing it unchanged to the Egress S3 bucket (identity transformation), allowing full end-to-end validation of the data pipeline without implementing actual Pass 2 business rules. All I/O operations are wired to strategy methods so Pass 1 and Pass 2 handlers call the appropriate I/O routines.

**Scope:**
- ORC input path: reads from `s3://<raw_bucket>/year=YYYY/month=MM/day=DD/` prefix (partitioned by submission date)
- Pass 1 Parquet output: writes to `s3://<intermediary_bucket>/pass1/<execution_id>/<query_timestamp>_pass1.parquet` (deterministic naming)
- Query timestamp format: ISO 8601 UTC with milliseconds (e.g., `20260401T120000000Z`)
- Intermediary bucket lifecycle policy: 30-day expiration (auto-delete)
- Pass 2 input path: reads from `s3://<intermediary_bucket>/pass1/<execution_id>/<query_timestamp>_pass1.parquet`
- Pass 2 no-op: reads Pass 1 parquet unchanged, writes to `s3://<egress_bucket>/<execution_id>/<query_timestamp>_pass2_noop.parquet`
- Strategy handler interface: Pass 1 calls `strategy.execute_pass1(df: DataFrame) -> DataFrame`, Pass 2 calls `strategy.execute_pass2(df: DataFrame) -> DataFrame`

**Acceptance Criteria:**
1. I/O code checked into `src/cde/io_handler.py` with functions: `read_orc_from_raw(s3_path: str, correlation_id: str) -> DataFrame`, `write_parquet(df: DataFrame, s3_path: str, correlation_id: str)`, `read_parquet(s3_path: str, correlation_id: str) -> DataFrame`; Pass 2 no-op handler in `core_runner.py` is identity: read parquet, write to egress unchanged
2. Tests in `tests/unit/test_io_handler.py` cover: (a) fixture ORC file round-trip (read 1000 rows, write to Parquet, verify row count and schema preserved), (b) Pass 2 no-op round-trip (read Pass 1 parquet, write to simulated egress, verify row count and field count match), (c) field names preserved in output (test against schema from Story 2.1)
3. One successful run evidence: Pass 1 reads `s3://raw/year=2026/month=04/day=01/` (10,000 rows), writes `s3://intermediary/pass1/<execution_id>/20260401T120000000Z_pass1.parquet` (10,000 rows); Pass 2 reads same parquet, writes `s3://egress/<execution_id>/20260401T120000000Z_pass2_noop.parquet` (10,000 rows); checksum verification confirms identity
4. Logs include: `orc_read_started` (with s3_path), `orc_read_completed` (with row_count), `parquet_write_completed` (with s3_path, row_count, file_size_bytes), `pass2_noop_identity_transform` (with input_rows, output_rows); metrics: `cde.glue.input_row_count` (labeled: pass=1, pass=2), `cde.glue.output_row_count` (labeled), `cde.glue.io_duration_ms` (labeled by operation: read_orc, write_pass1_parquet, read_pass1_parquet, write_pass2_parquet)

---

### Story 2.8: Deliver Raw-Arrival and Glue-Done SNS Event Wiring
**SP: 7 | Assignee:** Gulfraz (Team B)

**Description:** Deliver both SNS integration points required for Step Functions orchestration: (1) raw data arrival trigger (S3 event → SNS → Callback Lambda → Step Functions resume) and (2) Glue completion notification (Glue job completion → SNS publish). The story includes S3 event notification configuration, two SNS topic definitions with required payload schemas (from Story 2.1 contracts), IAM role policies, and the Callback Lambda wiring that receives SNS events and invokes the Step Functions callback API to resume the wait state.

**Scope:**
- SNS topic 1: `cde-raw-data-arrival` — published by S3 raw bucket when objects match prefix `year=*/month=*/day=*/*.{orc,jsonl}`
- SNS topic 2: `cde-glue-pass1-complete` — published by Glue Pass 1 job at completion; SNS topic `cde-glue-pass2-complete` reserved for future sprint
- Raw-arrival payload schema (from Story 2.1): `{"bucket": string, "key": string, "event_time": ISO8601, "correlation_id": string}`
- Glue-done payload schema: `{"execution_id": string, "pass_number": int, "job_status": "SUCCEEDED"|"FAILED", "output_location": string, "record_count": int}`
- Callback Lambda: `src/lambda/callback_lambda.py` invoked by SNS event, extracting task token from SFN execution context, calling `stepfunctions.send_task_success(taskToken=<token>, output=<payload>)` on success or `send_task_failure()` on job failure

**Acceptance Criteria:**
1. SNS topics `cde-raw-data-arrival` and `cde-glue-pass1-complete` created in CloudFormation template `infrastructure/cloudformation/cde_stack.json`; S3 event notification configured on raw bucket with filter rule for object suffix `*.orc` or `*.jsonl` and prefix pattern `year=*/month=*/day=*/`; Glue job configured with SNS publish on completion (via CloudFormation); IAM policies include: `sns:Publish` on both topic ARNs, `states:SendTaskSuccess`, `states:SendTaskFailure` on state machine ARN
2. Contract tests in `tests/unit/test_sns_payloads.py` validate: raw-arrival payload has all 4 required fields (bucket, key, event_time, correlation_id) with correct types; glue-done payload has all 5 required fields (execution_id, pass_number, job_status, output_location, record_count) with correct types; malformed payloads rejected by validators
3. Integration test in `tests/integration/test_sns_wiring.py`: upload .orc file to `s3://raw/year=2026/month=04/day=01/test.orc`, verify SNS message published to `cde-raw-data-arrival` topic with expected payload structure (bucket, key, correlation_id fields present)
4. One Glue Pass 1 completion run publishes SNS message to `cde-glue-pass1-complete` with valid payload; logs include: `sns_publish_requested` (with topic_name), `sns_publish_completed` (with topic_arn, message_id); metrics: `cde.sns.publish_count` (labeled by topic_name), `cde.sns.consume_to_callback_latency_ms` (labeled by topic_name)

---

### Story 2.9: Deliver CDP Fixture Generation Pack and Catalog
**SP: 6 | Assignee:** Nisarg (Team C)

**Description:** Deliver the reusable Sprint 2 fixture set for downstream rule testing, including generator tooling, scenario coverage, and cataloged expectations.

**Architecture Scope:** Test-data layer supporting Zone 3 Spark transformations and Zone 2 orchestration simulations.

**Acceptance Criteria:**
- Fixture generator script and fixture catalog README are checked in
- At least 5 named scenarios are produced (valid, non-consented, non-travel, duplicate revisions, edge cases)
- Validation tests confirm generated schema correctness and required field coverage
- Story evidence includes fixture inventory, generation command, and storage location

---

### Story 2.10: Deliver Sprint 2 Green-Path E2E and Regression Evidence
**SP: 5 | Assignee:** Uttam (Team C)

**Description:** Deliver Sprint 2 closure evidence through one complete green-path run and regression execution with clear artifact and telemetry references.

**Architecture Scope:** End-to-end validation across Zone 2 orchestration, Zone 3 Glue processing, and intermediary/egress S3 artifact boundaries.

**Acceptance Criteria:**
- One E2E run completes from EventBridge trigger through Pass 2 without manual state edits
- Evidence includes execution ID, state graph screenshot, output locations, and expected counts
- Regression suite output is attached/linked and all Sprint 2 checks pass
- Run report records timing, findings, open defects, and handoff notes for Sprint 3

---

# Sprint 3 - Pass 1: CDP Ingestion, Pre-Filtering & UUID Extraction
**Apr 15 - Apr 28** | **65 SP total**

**Goal (unchanged):** Implement CDP ingestion in Glue, Tier 1 pre-filters, UUID extraction to intermediary S3, real SNS/SFN data-arrival wiring, and consent mapping hydration.

## Sprint 3 Delivery Guardrails
- Tests are authored first for every new rule, API client, and event payload.
- Baseline observability from Sprint 2 is extended, not deferred.
- Regression suite is updated and executed for every merged story.
- All logs must remain structured JSON (Application Log Format v2), must carry `correlation_id`, and must not include sensitive personal data.
- For API and async stages, acceptance evidence must include heartbeat/progress logs, retry/failure metrics, and correlation search proof.

## Sprint 3 Developer-Assignable Stories

| ID | Story | SP | Assignee | Test-First Output | Observability Output |
|----|-------|---:|----------|-------------------|----------------------|
| 3.1 | Deliver correlation propagation and cross-service tracing baseline | 6 | Raghuram | Correlation contract tests | End-to-end traceability metrics |
| 3.2 | Deliver ORC/JSONL ingestion and schema validation package | 7 | Gulfraz | Ingestion/schema tests | Read + schema error metrics |
| 3.3 | Deliver Config/Consent API clients with Vault-backed auth | 7 | Pankaj | Client/auth contract tests | API + auth latency metrics |
| 3.4 | Deliver API retry/backoff and partial-failure handling | 5 | Prashanth | Retry/error policy tests | Retry and terminal-failure counters |
| 3.5 | Deliver consent_mapping build, validation, and write path | 5 | Prashanth | Mapping schema tests | Mapping size + write status metrics |
| 3.6 | Deliver dedup rule implementation and validation | 6 | Naveen | Dedup fixture tests | Dedup drop-count metrics |
| 3.7 | Deliver consent broadcast-join rule and validation | 6 | Naveen | Join fixture tests | Join hit/miss metrics |
| 3.8 | Deliver travel-category filtering and re-aggregation rule | 6 | Uttam | Category filter tests | Category hit/drop metrics |
| 3.9 | Deliver filter-order optimization and stage count telemetry | 5 | Uttam | Plan/order assertion tests | Stage row-count metrics |
| 3.10 | Deliver UUID extraction, parquet output, and SNS completion payload | 7 | Shikhar | Output payload contract tests | UUID/output/publish metrics |
| 3.11 | Deliver real S3→SNS→SFN wiring and Sprint 3 regression evidence | 5 | Suresh | Integration + regression tests | End-to-end parse and run metrics |

---

## Sprint 3 Story Details

### Story 3.1: Deliver Correlation Propagation and Cross-Service Tracing Baseline
**SP: 6 | Assignee:** Raghuram (Team B)

**Description:** Deliver end-to-end correlation ID propagation so every Sprint 3 execution can be traced across Zone 2 orchestration events, Zone 3 Glue jobs, and SNS handoff boundaries. The correlation ID is generated once at EventBridge trigger time (UUID v4, lowercase with hyphens) and propagated through all downstream service boundaries via explicit field/attribute names at each hop: `detail.correlation_id` in EventBridge event, `correlation_id` in Step Functions input, `--correlation_id` in Glue job arguments, and `correlation_id` SNS message attribute. Every service component validates correlation ID presence and emits metrics tracking coverage rate and missing-correlation incidents.

**Scope:**
- Correlation ID generation: EventBridge rule populates `detail.correlation_id` field with UUID v4 (lowercase with hyphens, e.g., `550e8400-e29b-41d4-a716-446655440000`) at trigger time
- Transport mechanism by boundary:
  1. EventBridge → Step Functions: `detail.correlation_id` includes in event detail, mapped to step function execution input as `correlation_id` key
  2. Step Functions → Init Lambda: `correlation_id` included in Lambda `InputPath` payload parameter
  3. Step Functions → Glue Pass 1: `--correlation_id` Glue job argument
  4. Step Functions → SQS (K8s Job dispatch): SQS message attribute with attribute key `correlation_id` (string type)
  5. Glue → SNS (pass completion): SNS message attribute with attribute name `correlation_id` (string type)
  6. SNS → Callback Lambda: `correlation_id` extracted from message attributes into Lambda context via `event.MessageAttributes.correlation_id.StringValue`
- Correlation ID field name: consistently named `correlation_id` at all boundaries (not `trace_id`, `request_id`, etc.)
- Format: UUID v4 lowercase with hyphens, 36 characters

**Acceptance Criteria:**
1. Correlation propagation code checked into: `infrastructure/step_functions/sfn_template.json` (Pass `$.detail.correlation_id` via `InputPath` to all task inputs), `src/lambda/init_lambda.py` (receive and pass forward), `src/cde/core_runner.py` (read `--correlation_id` and pass to logging context), `src/lambda/callback_lambda.py` (extract from SNS message attributes); all transitions include correlation_id in `ResultPath`
2. Contract tests in `tests/unit/test_correlation_propagation.py` validate: EventBridge detail includes `correlation_id` field matching UUID v4 regex, SFN input includes `correlation_id` passed to Lambda, Glue logs include `correlation_id` field in all event objects (every log line has field), SNS message attributes include `correlation_id` with correct string value
3. One traced execution evidence set from `tests/integration/test_correlation_endtoend.py::test_full_sprint3_tracing`: captures EventBridge event, SFN execution input, all Glue logs, SNS message attributes, Callback Lambda logs; verifies same `correlation_id: <UUID-X>` appears in all 6 hops; evidence artifact saved to `tests/integration/trace_evidence_snapshot.json`
4. Logs include `correlation_id` as string field in every event; metrics: `cde.correlation.coverage_rate` (gauge: ratio of events with correlation_id, 0-1), `cde.correlation.missing_correlation_count` (counter; increment when field is absent), `cde.correlation.propagation_latency_ms` (histogram labeled by boundary: eventbridge_to_sfn, sfn_to_lambda, lambda_to_glue, glue_to_sns, sns_to_callback)

---

### Story 3.2: Deliver ORC/JSONL Ingestion and Schema Validation Package
**SP: 7 | Assignee:** Gulfraz (Team B)

**Description:** Deliver robust input ingestion for CDP data with ORC as the primary path and JSONL as fallback, plus explicit schema validation and error diagnostics. The ingestion code detects the input format by file extension, reads the data into a Spark DataFrame, validates all required top-level and nested fields against the CDP schema, and logs diagnostics including field presence, data type compliance, and row counts of valid vs. corrupt records. On validation failure, corrupt rows are logged and skipped (not failed), allowing partial success and downstream processing with valid records.

**Scope:**
- Input formats: ORC (primary, file suffix `.orc`) and JSONL (fallback, file suffix `.jsonl`); auto-detect by file extension
- Required top-level fields in CDP payload (validation enforces):
  - `data.companyId` (UUID, not null)
  - `data.reportId` (string, not null)
  - `data.submitTimestamp` (ISO 8601 timestamp string, not null)
  - `data.expenses` (array type, not null, length >= 1)
- Required nested fields in each expense record (in `data.expenses[]`):
  - `expenseType` (string, not null)
  - `id` (UUID, not null)
- Validation error handling: on validation failure, skip the row (do not halt job), log `invalid_row_encountered` event with reason code (missing_field, null_value, bad_type, parse_error)
- Schema validation output: summary metrics of valid/invalid/null rows

**Acceptance Criteria:**
1. ORC and JSONL ingestion code checked into `src/cde/ingest.py` with functions: `detect_format(filepath: str) -> str` (returns "orc" or "jsonl"), `read_orc(s3_path: str) -> DataFrame`, `read_jsonl(s3_path: str) -> DataFrame`, `validate_schema(df: DataFrame) -> (DataFrame, dict)` (returns valid rows and validation summary); validation against required fields enumerated in code comments with field paths
2. Tests in `tests/unit/test_ingestion.py` cover: (a) ORC happy path (loads, preserves nested schema), (b) JSONL happy path (parses strings to correct types), (c) JSONL with malformed JSON line (skipped, counted as invalid), (d) missing `data.companyId` field (row marked invalid, skipped), (e) null `data.submitTimestamp` (row skipped, logged), (f) missing `data.expenses` array (row skipped), (g) expense record missing `expenseType` (that expense record excluded but report processed if other expenses exist)
3. One fixture-backed run: reads 1000-row CDP fixture ORC file, validates all required fields, outputs 1000-row schema-valid DataFrame; diagnostic logs show: `input_row_count: 1000, valid_row_count: 1000, invalid_row_count: 0, null_field_count: 0`
4. Logs include: `ingestion_started` (with format, input_path, correlation_id), `schema_validation_completed` (with valid_count, invalid_count, null_field_count by field name), `invalid_row_logged` (one per invalid row, with row_index, missing_field_names, or null_field_names), `read_completed` (with row_count, duration_ms); metrics: `cde.glue.input_row_count`, `cde.glue.schema_validation_failure_count` (labeled by reason: missing_field, null_value, bad_type, parse_error), `cde.glue.read_duration_ms`

---

### Story 3.3: Deliver Config/Consent API Clients with Vault-Backed Auth
**SP: 7 | Assignee:** Pankaj (Team A)

**Description:** Deliver both upstream API clients and credential retrieval contract as one package to support consent hydration with secure auth.

**Architecture Scope:** Zone 1 internal API dependencies (Config/Consent services) with credential retrieval used by worker/control integrations.

**Acceptance Criteria:**
- Config API client, Consent API client, and Vault credential retrieval code are checked in
- Tests cover success, timeout, non-2xx responses, invalid token, and malformed response scenarios
- One sample normalized `companyId -> consentDate` output artifact is generated from mocked responses
- Logs/metrics include API latency, auth retrieval latency, status-code distribution, and auth failure count

---

### Story 3.4: Deliver API Retry/Backoff and Partial-Failure Handling
**SP: 5 | Assignee:** Prashanth (Team A)

**Description:** Deliver shared resilience behavior for Config/Consent API calls (Story 3.3) so transient failures are retried with exponential backoff and non-recoverable failures are handled without halting the entire job. The retry wrapper applies to both API clients, classifying HTTP status codes and exceptions into retryable (429, 503, 504) and terminal (400, 401, 403, 404, 500, 502) categories. Partial success means: if some company IDs receive consent dates and others fail with terminal errors (e.g., 404 not found), the job logs the terminal failures and continues processing with the successful results.

**Scope:**
- Retry parameters:
  - Max attempts: 3 per API call
  - Backoff algorithm: exponential with jitter, base 1 second
  - Backoff formula: `min(10, 1 * 2^(attempt-1)) + random(0, 1000)ms`
  - Attempt 1: 1s + jitter, Attempt 2: 2s + jitter, Attempt 3: 4s + jitter (capped at 10s)
  - Retryable status codes: 429 (Too Many Requests), 503 (Service Unavailable), 504 (Gateway Timeout)
  - Terminal status codes: 400, 401, 403, 404, 500, 502, and any other HTTP error not in retryable list
  - Retryable exceptions: `socket.timeout`, `ConnectionError` (network transients)
  - Terminal exceptions: `ValueError` (bad request format), `NotImplementedError`
- Partial success definition for consent batch: API returns 200 OK with mixed results; some companyIds have `consentDate` values, others have `status: "NO_CONSENT"` (not an error; means no consent exists for that company). Partial success on retry failure: some batch requests succeed, others exhaust max retries (logged as terminal failures), job continues processing successful results

**Acceptance Criteria:**
1. Retry wrapper code checked into `src/cde/api_retry.py` with function: `retry_with_backoff(api_call: Callable, max_attempts: int = 3, base_backoff_sec: float = 1.0) -> Any`; status code classification in `classify_http_status(status: int) -> Literal['RETRYABLE', 'TERMINAL']`; exception classification in `classify_exception(ex: Exception) -> Literal['RETRYABLE', 'TERMINAL']`
2. Tests in `tests/unit/test_api_retry.py` cover: (a) 429 response first attempt, 200 on second → retry succeeds, (b) 503 response all 3 attempts → terminal failure after max retries, (c) 404 response (immediate terminal, no retry), (d) network timeout first attempt, success on retry, (e) partial batch success: 10 company IDs batched, 2 timeout/retry successfully, 1 gets 404 (terminal), 7 get 200 → returns results for 9 companies and failure log for 1
3. Controlled run evidence in `tests/integration/test_api_retry_scenarios.py`: (a) mock API server configured to return 503 on first request, 200 on second → client retries and succeeds; (b) mock server returns 400 on all attempts → fails immediately without further retries; (c) batch call with mixed results (2 IDs timeout, retry to success; 1 ID gets 404; 7 IDs succeed) → method returns 9-entry mapping and logs 1 failure with company ID and HTTP status
4. Logs include: `api_call_attempt` (with attempt_number, status_code_or_exception, backoff_duration_ms), `api_call_failed_retryable` (with status_code, attempts_remaining), `api_call_failed_terminal` (with status_code, request_id), `batch_partial_success` (with success_count, failure_count, failed_company_ids); metrics: `cde.api.retry_attempt_count` (histogram), `cde.api.backoff_duration_ms` (histogram labeled by attempt_number), `cde.api.terminal_failure_count` (counter labeled by endpoint and status_code)

---

### Story 3.5: Deliver consent_mapping Build, Validation, and Write Path
**SP: 5 | Assignee:** Prashanth (Team A)

**Description:** Deliver deterministic creation of `consent_mapping.json` as the canonical record of company-to-consent-date mappings to be used in Pass 1 broadcast-join filtering (Story 3.7). The mapping is built from the Config/Consent API client output (Story 3.3 and 3.4), deduplicated by companyId preserving the latest consent date, ordered alphabetically by companyId for deterministic file output, and written to the Intermediary S3 bucket with a named path pattern. The mapping JSON file serves as the broadcast table for the Spark join operation in Pass 1 rule evaluation.

**Scope:**
- Input data source: DataFrame from Story 3.3 API client with schema `[companyId: UUID, consentDate: ISO8601 date string]`
- Deduplication logic: if multiple consent records exist for same companyId, keep the one with latest consentDate; if consentDates are equal, stable secondary sort by companyId (deterministic)
- Output schema for `consent_mapping.json` (JSON object, one mapping per line not JSONL):
  ```json
  {
    "<companyId_UUID>": "<ISO8601_date_YYYY-MM-DD>",
    "<companyId_UUID>": "<ISO8601_date_YYYY-MM-DD>"
  }
  ```
  Keys are companyId UUIDs (lowercase with hyphens), values are ISO 8601 date strings (YYYY-MM-DD format, date only, no time)
- Ordering: alphabetically sorted by companyId key for deterministic output
- S3 output path pattern: `s3://<intermediary_bucket>/pass1/<execution_id>/consent_mapping_<query_timestamp>.json` where query_timestamp is ISO 8601 UTC (e.g., `20260401T120000Z`)
- File format: JSON object (pretty-printed with 2-space indent for debuggability)

**Acceptance Criteria:**
1. Mapping builder code checked into `src/cde/consent_mapping.py` with functions: `build_consent_mapping(df_consent: DataFrame) -> dict`, `deduplicate_by_latest_consent_date(df: DataFrame) -> DataFrame`, `write_consent_mapping(mapping: dict, s3_path: str) -> bool`; deduplication preserves latest consentDate per companyId; output dict keys are sorted alphabetically
2. Schema validation tests in `tests/unit/test_consent_mapping.py` validate: (a) mapping keys are valid UUIDs (regex match), (b) mapping values are ISO date strings (YYYY-MM-DD format), (c) no null/empty entries, (d) keys are sorted alphabetically, (e) round-trip S3 write/read produces identical object
3. One generated mapping artifact: fixture with 42 input consent records (including 3 duplicates for same companyId with different dates) produces 40 unique mappings in output; S3 write to `s3://intermediary/pass1/<exec_id>/consent_mapping_20260401T090000Z.json`, file size ~2.4KB, pretty-printed with 2-space indent
4. Logs include: `consent_mapping_builder_started` (with input_record_count), `deduplicate_completed` (with input_count, output_count, duplicate_count), `consent_mapping_write_completed` (with entry_count, file_size_bytes, s3_path); metrics: `cde.consent_mapping.entry_count` (counter), `cde.consent_mapping.write_duration_ms` (histogram), `cde.consent_mapping.write_status` (counter labeled by outcome: success, failure)

---

### Story 3.6: Deliver Dedup Rule Implementation and Validation
**SP: 6 | Assignee:** Naveen (Team C)

**Description:** Deliver the report-level deduplication stage using latest revision selection and prove correctness with fixture-based validation.

**Architecture Scope:** Zone 3 Tier 1 filtering logic in strategy-driven Spark transformations.

**Acceptance Criteria:**
- Dedup transformation code is checked in with clear window ordering semantics
- Tests cover single revision, multiple revisions, and equal timestamp edge cases
- Fixture-backed evidence confirms one surviving latest revision per reportId
- Logs/metrics include input rows, output rows, and dedup drop count

---

### Story 3.7: Deliver Consent Broadcast-Join Rule and Validation
**SP: 6 | Assignee:** Naveen (Team C)

**Description:** Deliver consent eligibility filtering via broadcast join against the consent mapping artifact (Story 3.5) so only reports with valid, timely consent are included in Pass 1 output. The join is configured as broadcast (consent_mapping is small, fits in executor memory), keyed on `data.companyId`, with consent date enforcement: a report is kept only if it has a matching consent entry AND the report's submitTimestamp is greater than or equal to the consent date. Reports with null companyId or missing mapping entry are dropped. The join also emits metrics for hit/miss rates to validate filtering effectiveness.

**Scope:**
- Join key: `data.companyId` from CDP report (left side) matched to companyId from `consent_mapping.json` (right side)
- Consent enforcement expression: `submitTimestamp >= consentDate` (report submitted on or after consent date)
- Missing mapping behavior: DROP the report (left anti-join on missing key)
- Null companyId behavior: DROP the report (pre-filter before join: `data.companyId IS NOT NULL`)
- Join type: broadcast hash join (consent_mapping broadcast to all executors)
- Output fields: all original report fields from dataset (join adds no new fields, only filters rows)

**Acceptance Criteria:**
1. Join/filter code checked into `src/cde/pass1_rules.py` with function: `apply_consent_filter(df_reports: DataFrame, consent_mapping: DataFrame) -> DataFrame`; implementation: (a) filter `data.companyId IS NOT NULL`, (b) broadcast consent_mapping, (c) join on companyId, (d) filter `submitTimestamp >= consentDate`, (e) select original report columns (drop the consentDate from join)
2. Tests in `tests/unit/test_consent_filter.py` cover: (a) matched consent scenario (10 reports with valid companyIds + 10 consent mappings for same companies, all submit dates >= consent dates → 10 kept), (b) pre-consent submission (report submit date < consent date → dropped), (c) missing mapping entry (companyId in report but not in consent_mapping → dropped), (d) null companyId (dropped by pre-filter)
3. Fixture-backed run in `tests/integration/test_consent_filter_fixtures.py`: 100-report fixture with 80 valid companies in consent mapping (20 companies have no mapping), 100 reports with submission dates >= consent dates (for matched companies) → input 100 reports, output 80 kept (matching mapping), 20 dropped (missing mapping); exact counts verified in logs
4. Logs include: `consent_filter_started` (with input_report_count, input_mapping_entry_count), `null_companyid_filtered` (count), `consent_join_completed` (with join_hit_count, join_miss_count, reports_kept, reports_dropped), `timestamp_filter_applied` (with pre_consent_count, post_consent_count); metrics: `cde.consent_filter.join_hits` (counter), `cde.consent_filter.join_misses` (counter), `cde.consent_filter.kept_report_count` (counter), `cde.consent_filter.dropped_report_count` (counter labeled by reason: missing_mapping, pre_consent_submit, null_companyid)

---

### Story 3.8: Deliver Travel-Category Filtering and Re-Aggregation Rule
**SP: 6 | Assignee:** Uttam (Team C)

**Description:** Deliver category-based filtering of expense lines and report-level reconstruction with explicit handling for empty/non-travel outcomes. The rule filters individual expense records to keep only those with travel-related category types from the approved allowlist, then re-aggregates expense totals at the report level. Reports where all expense lines are non-travel categories are dropped entirely (zero kept expenses → zero-row report → dropped). The filtering happens after dedup and consent filter (Story 3.6, 3.7 in execution order) and before UUID extraction (Story 3.10) so downstream API calls focus on travel-eligible reports.

**Scope:**
- Travel expense category allowlist (9 codes, exact match required): `ABFEE, AIRFE, AIRFR, CARRT, LODGA, LODGN, LODGT, LODGX, RAILX`
- Field to filter: `data.expenses[].expenseType` (string, must match one of the 9 codes exactly)
- Filtering logic: explode `expenses` array into individual rows, filter by expenseType in allowlist, drop non-matching records, re-aggregate by reportId
- Re-aggregation: reconstruct report-level object with filtered expenses array; preserve all original top-level report fields
- Empty report handling: if report has zero kept expenses after filtering, drop the entire report from output (do not output report with empty expenses array)
- Metrics: report-level keeps/drops, per-category hit counts

**Acceptance Criteria:**
1. Category filter and re-aggregation code checked into `src/cde/pass1_rules.py` with function: `apply_travel_category_filter(df_reports: DataFrame) -> DataFrame`; allowlist hardcoded as Python list: `TRAVEL_CATEGORIES = ["ABFEE", "AIRFE", "AIRFR", "CARRT", "LODGA", "LODGN", "LODGT", "LODGX", "RAILX"]` in module constants; implementation: explode, filter `expenseType IN TRAVEL_CATEGORIES`, drop empty reports
2. Tests in `tests/unit/test_travel_category_filter.py` cover: (a) mixed categories (report with 2 AIRFE + 1 LUNCH → 2 kept, report not dropped), (b) fully non-travel (report with all LUNCH, MEALS → dropped), (c) single qualifying category (report with 1 AIRFE + others → 1 kept), (d) empty expenses array input (dropped)
3. Transformation artifact from `tests/integration/test_travel_category_fixtures.py`: fixture with 50 reports (100 total expenses) → exploded view 100 rows (one per expense), after filter 55 expenses kept (matching allowlist), re-aggregated to 40 reports (10 reports had all non-travel expenses → dropped); artifact saved to `tests/fixtures/travel_filter_transformation_snapshot.json`
4. Logs include: `travel_category_filter_started` (with input_report_count, input_expense_count), `category_hit_totals` (dict with count per category: ABFEE: X, AIRFE: Y, etc.), `non_travel_category_drop_count` (individual expense lines dropped), `empty_report_drop_count` (entire reports with zero kept expenses), `filter_completed` (with output_report_count, output_expense_count); metrics: `cde.travel_filter.report_kept_count`, `cde.travel_filter.report_dropped_count`, `cde.travel_filter.category_hit_count` (labeled counter by category_code: ABFEE, AIRFE, etc.)

---

### Story 3.9: Deliver Filter-Order Optimization and Stage Count Telemetry
**SP: 5 | Assignee:** Uttam (Team C)

**Description:** Deliver optimized filter composition order (dedup → consent → category) with stage-level telemetry proving that early filters reduce downstream dataset size and cost. In architecture terms, `core_runner.py` invokes `strategy.apply_transform(...)`, and inside that transform chain the Pass 1 composition is hardcoded in this exact order: (1) dedup removes duplicate revisions by latest timestamp, reducing dataset by ~5-10% for typical expense patterns; (2) consent join filters pre-consent reports, reducing 15-25% for partial-consent populations; (3) category filter removes non-travel expenses, reducing another 30-50%. At each stage, row count is logged so observability can verify data reduction is happening and rules are working as intended. Spark query plan is asserted at test time to confirm all three filters are in the execution plan in the expected order.

**Scope:**
- Filter composition order in code (inside `strategy.apply_transform(..., pass_id=1, ...)`): execute `dedup_df = apply_dedup(...)`; then `consent_df = apply_consent_filter(dedup_df, ...)`; then `category_df = apply_travel_category_filter(consent_df); return category_df`
- Filter order rationale: (a) dedup is cheapest (single-pass window function), (b) consent is medium-cost (distributed join + filter), (c) category is most expensive (array explosion then re-aggregation); early filters reduce input size to expensive operations
- Spark query plan assertion (test phase): after materializing final DataFrame, call `df.explain(mode='formatted')` and parse output to verify: (1) Window node (for dedup) appears before BroadcastHashJoin, (2) BroadcastHashJoin appears before Filter (for category), (3) all three appear in execution DAG
- Stage-level telemetry: after each filter stage, emit row count (input → output) and drop count (rows/reports dropped)

**Acceptance Criteria:**
1. Filter composition code in `src/cde/pass1_rules.py` function `apply_all_pass1_filters(df: DataFrame) -> DataFrame` is invoked by `strategy.apply_transform(..., pass_id=1, ...)` and executes three filters in exact order with named intermediate variables and intermediate row-count logging; composition structure:
   ```python
   dedup_df = apply_dedup(df)
   consent_df = apply_consent_filter(dedup_df, mapping)
   category_df = apply_travel_category_filter(consent_df)
   return category_df
   ```
2. Plan assertion tests in `tests/unit/test_filter_plan_optimization.py`: (a) after creating final filtered DataFrame, call `df.explain(mode='formatted')` and capture output as string, (b) parse for stage names using regex (search for "Window", "BroadcastHashJoin", "Filter"), (c) assert order: Window appears before BroadcastHashJoin in output string, BroadcastHashJoin appears before Filter, (d) test artifact saved to `tests/fixtures/expected_plan_ordering.txt` with sample plan snapshot
3. One execution run with row-count progression in `tests/integration/test_filter_stage_counts.py`: fixture with 10,000 reports → after dedup 9,800 reports (200 duplicates dropped) → after consent 7,800 reports (2,000 pre-consent dropped) → after category 4,200 reports (3,600 non-travel dropped); all counts logged and captured in test output/logs
4. Logs include: `filter_stage_started` (with stage_name: "dedup"|"consent"|"category"), `filter_stage_completed` (with stage_name, input_row_count, output_row_count, dropped_count); metrics: `cde.filter_stage.row_count` (labeled histogram by stage: input_dedup, output_dedup, input_consent, output_consent, input_category, output_category), `cde.filter_stage.drop_count` (labeled counter by stage); query plan snapshot stored at `tests/fixtures/spark_plan_<test_case_id>.txt` for audit trail

---

### Story 3.10: Deliver UUID Extraction, Parquet Output, and SNS Completion Payload
**SP: 7 | Assignee:** Shikhar (Team B)

**Description:** Deliver all Sprint 3 pass-out artifacts: UUID extract, filtered parquet output, and completion SNS payload with audit fields.

**Architecture Scope:** Zone 3 Pass 1 outputs to Intermediary S3 plus Zone 2 completion signaling via SNS payload contract.

**Acceptance Criteria:**
- UUID extraction, parquet write, and SNS payload builder code are checked in
- Tests validate UUID uniqueness/order, parquet read-back schema, and payload contract fields
- One successful run publishes `uuid_extract.json`, `pass1_output/`, and completion payload evidence
- Logs/metrics include UUID count, output size/file count, and publish success/failure metrics

---

### Story 3.11: Deliver Real S3→SNS→SFN Wiring and Sprint 3 Regression Evidence
**SP: 5 | Assignee:** Suresh (Team A)

**Description:** Deliver production-grade raw data arrival wiring and close Sprint 3 with end-to-end regression evidence and handoff artifacts.

**Architecture Scope:** Zone 2 event chain (S3 -> SNS -> Step Functions -> Glue args) and Sprint 3 end-to-end handoff verification.

**Acceptance Criteria:**
- Infrastructure/ASL changes are checked in for S3 event -> SNS -> SFN resume path
- Integration tests prove uploaded object path is correctly propagated into Glue input args
- One full Sprint 3 run evidence package includes execution IDs, output artifact paths, and stage counts
- Regression report is published with pass/fail summary, observed metrics, and recorded follow-up defects

---
