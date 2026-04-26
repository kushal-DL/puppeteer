# CDE - Detailed Sprint Stories & Subtasks (Sprints 4-6)

**Team:** 9 developers | **Capacity:** ~65 SP/sprint | **Go-live:** Jul 7, 2026  
**Planning rule (Sprints 4+):** 1 SP = 1 person-day. Every story is independently assignable to one developer.

## Team Structure

| Team | Senior Tech Lead (Python) | PySpark Developer | Python Developer |
|------|--------------------------|-------------------|------------------|
| **A** | **Suresh** | Prashanth | Pankaj |
| **B** | **Raghuram** | Gulfraz | Shikhar |
| **C** | **Uttam** | Naveen | Nisarg |

> Senior Tech Leads drive design/review. Sprints 4-6 stories are small, independently assignable units with test-first and baseline observability embedded in the deliverable.

---

# Sprint 4 - K8s Dumb Fetcher, SQS/KEDA Cross-Boundary & API Enrichment
**Apr 29 - May 12** | **65 SP total**

**Goal (unchanged):** Implement the Step Functions to K8s bridge through SQS Task Tokens, scale the worker through KEDA, build the dumb fetcher for concurrent API enrichment, and complete CDP subscription sync as part of the initialization flow.

## Sprint 4 Delivery Guardrails
- Every implementation story starts with contract tests, manifest validation, or mocked integration tests before production code or infrastructure changes.
- Every touched component emits structured logs, counters, latency metrics, and health signals so Sprint 7 only hardens what is already present.
- Every story must finish with concrete delivery evidence: checked-in code/manifests, test output, and runtime artifacts or logs.

## Sprint 4 Developer-Assignable Stories

| ID | Story | SP | Assignee | Test-First Output | Observability Output |
|----|-------|---:|----------|-------------------|----------------------|
| 4.1 | Implement task-token bridge contract and SFN wait state | 7 | Suresh | Message contract + ASL tests | Queue publish/suspend metrics |
| 4.2 | Implement bridge timeout, failure routes, and callback validation | 7 | Pankaj | Negative-path + callback tests | Timeout/resume latency metrics |
| 4.3 | Deliver KEDA worker deployment with auth and scale-to-zero | 6 | Uttam | Manifest + auth smoke tests | Scale and auth health metrics |
| 4.4 | Build fetcher artifact loader and strategy config resolver | 7 | Shikhar | Loader/parsing fixture tests | Artifact read and config logs |
| 4.5 | Build async fetch engine with retry and error policy | 6 | Raghuram | Concurrency + retry tests | Request latency and retry counters |
| 4.6 | Implement response streaming to S3 with durability checks | 6 | Gulfraz | Streaming write tests | Write throughput and failure metrics |
| 4.7 | Implement pluggable JWT and mTLS auth modes | 7 | Naveen | Auth-mode contract tests | Auth-mode usage and auth latency |
| 4.8 | Add fetcher baseline observability and worker heartbeat | 6 | Prashanth | Log/metric contract tests | Per-call metrics and heartbeat |
| 4.9 | Implement task-token success/failure callback package | 7 | Nisarg | Callback payload tests | Callback success/failure counters |
| 4.10 | Implement CDP subscription sync, consent chain, and enablement | 6 | Raghuram | API diff + enablement tests | Sync and enablement counters |

---

## Sprint 4 Story Details

### Story 4.1: Implement Task-Token Bridge Contract and SFN Wait State
**SP: 7 | Assignee:** Suresh (Team A)

**Description:** Deliver the Step Functions to SQS task-token bridge as one coherent unit: approved message contract, ASL wait state, and required payload fields for worker handoff.

**Acceptance Criteria:**
- Contract and ASL changes are checked in together, including required payload fields (task token, execution IDs, S3 URIs, correlation data)
- Contract tests and ASL simulation tests pass for valid and invalid message payloads
- One execution evidence record shows state entering wait mode with a valid queue message
- Story handoff includes contract path, ASL path, test output, and sample message payload

---

### Story 4.2: Implement Bridge Timeout, Failure Routes, and Callback Validation
**SP: 7 | Assignee:** Pankaj (Team A)

**Description:** Deliver operationally safe bridge behavior with timeout/Catch routing plus callback validation so orchestration resumes or fails predictably.

**Acceptance Criteria:**
- ASL timeout and failure routing changes are checked in with explicit target states
- Automated negative-path tests cover timeout, malformed callback payload, and callback failure cases
- A callback smoke test proves successful resume from wait state
- Logs/metrics include timeout threshold, timeout count, callback success count, and callback failure count

---

### Story 4.3: Deliver KEDA Worker Deployment with Auth and Scale-to-Zero
**SP: 6 | Assignee:** Uttam (Team C)

**Description:** Deliver worker runtime readiness in one story: KEDA ScaledJob manifest, queue access authentication pattern, and verified scale-to-zero behavior.

**Acceptance Criteria:**
- ScaledJob manifests and auth configuration (IRSA or approved Vault path) are checked in
- Validation run proves queue polling works without static credentials in code
- Scale test proves zero pods when idle and automatic scale-up/scale-down on queue activity
- Story evidence includes manifest paths, auth smoke output, and scale timeline (pod start/end timestamps)

---

### Story 4.4: Build Fetcher Artifact Loader and Strategy Config Resolver
**SP: 7 | Assignee:** Shikhar (Team B)

**Description:** Deliver fetcher runtime setup logic that loads UUID/strategy artifacts from S3 and resolves a normalized runtime config for API execution.

**Acceptance Criteria:**
- Loader and parser code are checked in with a normalized config object schema
- Tests cover successful load, missing object, malformed object, and unsupported config values
- Logs include loaded object keys, strategy identifier, resolved target count, and parse failures
- Story handoff includes parser schema, test output, and sample normalized config

---

### Story 4.5: Build Async Fetch Engine with Retry and Error Policy
**SP: 6 | Assignee:** Raghuram (Team B)

**Description:** Deliver the production fetch engine as one unit: bounded concurrency, retry/backoff for transient failures, and terminal error classification.

**Acceptance Criteria:**
- Async request engine and retry policy code are checked in with configurable concurrency and retry limits
- Tests prove concurrency caps, retry on 429/503, and terminal handling for non-retryable failures
- Run evidence shows mixed-success workload completion without worker crash
- Metrics/logs include request latency distribution, in-flight count, retry count, and terminal failure count

---

### Story 4.6: Implement Response Streaming to S3 with Durability Checks
**SP: 6 | Assignee:** Gulfraz (Team B)

**Description:** Deliver immediate response persistence to intermediary S3, including write durability checks and output key strategy.

**Acceptance Criteria:**
- Streaming writer code is checked in with one-response-per-object behavior and deterministic key pattern
- Tests prove incremental writes occur during processing and not only at batch end
- Validation run confirms persisted response count matches completed request count
- Logs/metrics include write duration, bytes written, success count, and write failure count

---

### Story 4.7: Implement Pluggable JWT and mTLS Auth Modes
**SP: 7 | Assignee:** Naveen (Team C)

**Description:** Deliver both supported API auth paths (JWT and mTLS) behind a strategy-driven selector so runtime can switch mode by config.

**Acceptance Criteria:**
- Auth selection code is checked in with a single strategy-driven switch between JWT and mTLS
- Tests validate token injection path, certificate path loading, and explicit failure on missing credentials
- One authenticated request evidence sample is captured for each mode
- Logs include selected auth mode and auth setup latency without exposing secrets or cert content

---

### Story 4.8: Add Fetcher Baseline Observability and Worker Heartbeat
**SP: 6 | Assignee:** Prashanth (Team A)

**Description:** Deliver baseline observability for the fetcher so every run has traceable logs, metrics, and health signals before Sprint 7 hardening.

**Acceptance Criteria:**
- Structured log schema is checked in for request lifecycle, correlation fields, status, latency, and payload size
- Metrics are implemented for success/failure counts, retry counts, and batch duration
- Worker heartbeat/progress signal is emitted at a defined interval during active processing
- Story evidence includes one run log sample, metric list, and heartbeat proof

---

### Story 4.9: Implement Task-Token Success/Failure Callback Package
**SP: 7 | Assignee:** Nisarg (Team C)

**Description:** Deliver the callback package that reports final worker outcome to Step Functions using consistent success and failure payload contracts.

**Acceptance Criteria:**
- Callback code is checked in for both `send_task_success` and `send_task_failure` paths
- Contract tests validate required fields, serialization, and error mapping in callback payloads
- One positive and one negative callback execution evidence record is captured
- Logs/metrics include callback duration, callback success count, and callback failure count

---

### Story 4.10: Implement CDP Subscription Sync, Consent Chain, and Enablement
**SP: 6 | Assignee:** Raghuram (Team B)

**Description:** Deliver the initialization business flow as one assignable unit: CDP subscription diff, consent chain trigger, and ingestion enablement for newly added companies.

**Acceptance Criteria:**
- Sync and enablement code is checked in with explicit handling for add/remove/no-change outcomes
- Tests cover diff outcomes and enablement behavior for zero-add, single-add, and multi-add cases
- One devscratch run record includes detected changes, enablement requests, and final sync status
- Logs/metrics include add/remove counts, enablement count, and consent-chain completion status

---

# Sprint 5 - Pass 2: Rule Evaluation, Broadcast Join & Filtered Egress
**May 13 - May 26** | **65 SP total**

**Goal (unchanged):** Load Pass 1 and raw API data into Glue Pass 2, resolve report-to-agency mappings through broadcast joins, evaluate final business rules, write curated JSONL to Egress S3, and support conditional skipping when enrichment is not required.

## Sprint 5 Delivery Guardrails
- Every transformation story begins with fixture-backed Spark tests or contract tests before implementation.
- Pass 2 metrics, stage-level row counts, and output manifests are required delivery artifacts, not optional polish.
- Every story must finish with checked-in code, test evidence, and output/runtime evidence aligned to the story boundary.

## Sprint 5 Developer-Assignable Stories

| ID | Story | SP | Assignee | Test-First Output | Observability Output |
|----|-------|---:|----------|-------------------|----------------------|
| 5.1 | Deliver Pass 2 input contract and loaders for parquet + API datasets | 6 | Gulfraz | Contract + loader tests | Input read metrics |
| 5.2 | Deliver Travel/Spend normalization with schema mismatch handling | 6 | Shikhar | Normalization + mismatch tests | Parse/mismatch counters |
| 5.3 | Deliver report-to-booking and report-to-agency mapping pipeline | 6 | Naveen | Join + aggregation tests | Join cardinality metrics |
| 5.4 | Deliver broadcast/left-join integration back to Pass 1 dataset | 6 | Uttam | Join strategy tests | Join strategy and null counters |
| 5.5 | Deliver join correctness validation and optimizer assertions | 6 | Nisarg | Plan + fixture validation tests | Plan selection logs |
| 5.6 | Deliver approved-agency and Complete-fallback keep rules | 6 | Prashanth | Rule contract tests | Rule-hit counters |
| 5.7 | Deliver competitor guardrail precedence and rule ordering | 6 | Suresh | Precedence regression tests | Competitor-drop counter |
| 5.8 | Deliver full Phase 2 business-rule regression suite | 6 | Pankaj | End-to-end rule suite | Rule-path summary metrics |
| 5.9 | Deliver egress JSONL writer with cleanup and idempotent overwrite | 6 | Raghuram | Egress + overwrite tests | Output file/count metrics |
| 5.10 | Deliver output manifest publication to orchestration | 5 | Pankaj | Manifest contract tests | Manifest publish metrics |
| 5.11 | Deliver requires_api_enrichment skip path behavior | 6 | Uttam | Skip-path simulation tests | Branch selection metrics |

---

## Sprint 5 Story Details

### Story 5.1: Deliver Pass 2 Input Contract and Loaders for Parquet + API Datasets
**SP: 6 | Assignee:** Gulfraz (Team B)

**Description:** Deliver the complete Pass 2 data ingress layer: input contract, parquet loader, API JSONL loader, and source-level ingestion evidence.

**Acceptance Criteria:**
- Input contract and both loaders are checked in with clear path/config contracts
- Tests cover valid inputs, empty inputs, malformed files, and missing partitions
- One fixture-backed run proves both sources load with expected schema and counts
- Logs/metrics include per-source read count, read duration, and source error count

---

### Story 5.2: Deliver Travel/Spend Normalization with Schema Mismatch Handling
**SP: 6 | Assignee:** Shikhar (Team B)

**Description:** Deliver normalization for Travel and Spend responses and reconcile schema mismatches into one canonical dataset for joins.

**Acceptance Criteria:**
- Normalization code is checked in for both API sources with a shared canonical schema
- Tests cover missing optional fields, malformed payloads, and source mismatch scenarios
- One sample normalized dataset artifact is produced from mixed source fixtures
- Logs/metrics include parse success/failure per source and mismatch event count

---

### Story 5.3: Deliver Report-to-Booking and Report-to-Agency Mapping Pipeline
**SP: 6 | Assignee:** Naveen (Team C)

**Description:** Deliver the core enrichment mapping flow from report IDs to bookings and then to report-level agency arrays.

**Acceptance Criteria:**
- Join and aggregation code is checked in with documented keys and output semantics
- Tests cover single booking, multiple bookings, duplicate mappings, and empty mapping cases
- A fixture run produces expected mapping outputs for known report IDs
- Logs/metrics include join input/output counts and agency-array size distribution

---

### Story 5.4: Deliver Broadcast/Left-Join Integration Back to Pass 1 Dataset
**SP: 6 | Assignee:** Uttam (Team C)

**Description:** Deliver integration of agency mapping back into Pass 1 via broadcast or left join while preserving no-booking reports.

**Acceptance Criteria:**
- Join-back transformation is checked in with explicit handling for no-booking preservation
- Tests validate schema retention, row retention, and null mapping behavior
- One logical plan sample confirms expected join strategy selection in representative workload
- Logs/metrics include join strategy, null mapping count, and post-join row count

---

### Story 5.5: Deliver Join Correctness Validation and Optimizer Assertions
**SP: 6 | Assignee:** Nisarg (Team C)

**Description:** Deliver a verification layer that asserts join correctness and prevents silent optimizer regressions.

**Acceptance Criteria:**
- Plan assertion tests and fixture correctness tests are checked in for join pipeline stages
- Tests validate expected report-to-agency resolution for known scenarios
- Validation artifacts include at least one broadcast case and one non-broadcast case
- Story handoff includes plan evidence, fixture set, and passing test output

---

### Story 5.6: Deliver Approved-Agency and Complete-Fallback Keep Rules
**SP: 6 | Assignee:** Prashanth (Team A)

**Description:** Deliver the two keep paths in one assignable unit: approved agency keep and Complete-enabled no-booking fallback.

**Acceptance Criteria:**
- Rule code is checked in with explicit predicates and comments for auditability
- Tests cover approved-only, fallback-only, mixed, and null-config scenarios
- One rule-path matrix artifact shows expected keep/drop decisions for fixture scenarios
- Logs/metrics include approved-keep count and fallback-keep count

---

### Story 5.7: Deliver Competitor Guardrail Precedence and Rule Ordering
**SP: 6 | Assignee:** Suresh (Team A)

**Description:** Deliver precedence enforcement so competitor presence drops the report even when keep rules otherwise match.

**Acceptance Criteria:**
- Guardrail precedence logic is checked in and positioned ahead of downstream keep outputs
- Tests cover pure competitor, mixed competitor+approved, and competitor-absent scenarios
- A precedence evidence artifact demonstrates competitor rule overriding keep paths
- Logs/metrics include competitor-triggered drop count and final drop reason distribution

---

### Story 5.8: Deliver Full Phase 2 Business-Rule Regression Suite
**SP: 6 | Assignee:** Pankaj (Team A)

**Description:** Deliver complete regression coverage for combined Phase 2 rule behavior so future changes are safely detectable.

**Acceptance Criteria:**
- Regression suite is checked in with scenario coverage for all keep/drop branches
- Test runner instructions are documented and executable locally
- One full passing run report is attached as story evidence
- Story handoff includes suite path, scenario inventory, and baseline expected outputs

---

### Story 5.9: Deliver Egress JSONL Writer with Cleanup and Idempotent Overwrite
**SP: 6 | Assignee:** Raghuram (Team B)

**Description:** Deliver final output writing as one unit: cleanup of join-only columns, JSONL emission, deterministic file sizing, and overwrite idempotency.

**Acceptance Criteria:**
- Egress writer code is checked in with schema cleanup and overwrite controls
- Tests verify schema correctness, overwrite behavior, and deterministic output file strategy
- One rerun proof shows overwrite replacing prior output instead of appending duplicates
- Logs/metrics include output record count, output file count, and write duration

---

### Story 5.10: Deliver Output Manifest Publication to Orchestration
**SP: 5 | Assignee:** Pankaj (Team A)

**Description:** Deliver publication of pass summary and output manifest for downstream orchestration and operational visibility.

**Acceptance Criteria:**
- Manifest payload builder and publish logic are checked in with required fields
- Contract tests validate payload structure and required audit attributes
- One successful publication artifact is captured with output path and final counts
- Logs/metrics include publish success/failure and manifest version

---

### Story 5.11: Deliver requires_api_enrichment Skip Path Behavior
**SP: 6 | Assignee:** Uttam (Team C)

**Description:** Deliver the full no-enrichment branch when strategy disables API enrichment, including orchestration branch and output correctness.

**Acceptance Criteria:**
- Strategy flag handling and orchestration branch changes are checked in
- Simulation tests prove K8s and Pass 2 are skipped when enrichment is disabled
- One sample execution graph confirms direct route and valid output generation
- Logs/metrics include branch selection counts and skip-path completion duration

---

# Sprint 6 - IFM Integration, E2E Pipeline & Data Validation
**May 27 - Jun 9** | **65 SP total**

**Goal (unchanged):** Integrate with IFM for AmexGBT delivery, run full end-to-end smoke testing, build the validation suite, prove idempotency, and validate negative/error paths before hardening.

## Sprint 6 Delivery Guardrails
- Every validation and integration story must end with published evidence, not only verbal confirmation.
- E2E runs must retain correlation-aware logs, phase timings, and artifact references for later hardening work.
- Manual verification is allowed only when it produces explicit output artifacts, screenshots, reports, or defect records.

## Sprint 6 Developer-Assignable Stories

| ID | Story | SP | Assignee | Test-First Output | Observability Output |
|----|-------|---:|----------|-------------------|----------------------|
| 6.1 | Deliver IFM contract, source integration, auth, and notifications | 6 | Suresh | Contract + integration tests | Delivery and notify metrics |
| 6.2 | Deliver IFM pickup and confirmation validation flow | 6 | Pankaj | Pickup/confirm smoke tests | Pickup-confirm latency metrics |
| 6.3 | Deliver realistic E2E fixture pack and expected outcomes | 6 | Shikhar | Fixture validation tests | Fixture inventory and coverage logs |
| 6.4 | Deliver full E2E smoke execution and trace evidence | 6 | Raghuram | E2E run checklist | End-to-end and phase timing metrics |
| 6.5 | Deliver stage-output and business-rule count validation | 6 | Gulfraz | Stage comparison tests | Stage-level row-count metrics |
| 6.6 | Deliver timing and KEDA scaling evidence package | 6 | Naveen | Evidence checklist tests | Scale and timing baseline metrics |
| 6.7 | Deliver expected-output manifests and comparator engine | 6 | Nisarg | Manifest + comparator tests | Validation match/mismatch metrics |
| 6.8 | Deliver diff reporting and optional validation orchestration stage | 7 | Uttam | Diff + integration tests | Validation stage duration/status metrics |
| 6.9 | Deliver idempotency and overwrite verification suite | 5 | Gulfraz | Repeat-run comparison tests | Equality and overwrite metrics |
| 6.10 | Deliver negative-path resilience test pack and alert verification | 5 | Raghuram | Failure-path tests | Failure, retry, timeout, alert metrics |
| 6.11 | Deliver defect register and rerun handoff package | 6 | Suresh | Handoff checklist validation | Defect and readiness summary metrics |

---

## Sprint 6 Story Details

### Story 6.1: Deliver IFM Contract, Source Integration, Auth, and Notifications
**SP: 6 | Assignee:** Suresh (Team A)

**Description:** Deliver IFM integration foundations as one assignable package: delivery contract, source/pickup config, auth setup, and failure notification route.

**Acceptance Criteria:**
- Delivery contract and integration/auth configuration are checked in or documented in deployment-controlled files
- Validation tests prove naming/path contract is accepted and failure notifications route correctly
- One controlled delivery attempt captures pickup and notification behavior evidence
- Logs/metrics include pickup attempts, auth outcome, and notification success/failure

---

### Story 6.2: Deliver IFM Pickup and Confirmation Validation Flow
**SP: 6 | Assignee:** Pankaj (Team A)

**Description:** Deliver a repeatable validation flow that proves files move from egress through IFM pickup to confirmation checkpoint.

**Acceptance Criteria:**
- Validation procedure or script is checked in and runnable in dev environment
- At least one successful pickup-confirmation run is recorded with file name and timestamps
- Evidence includes pickup reference, confirmation reference, and route details
- Logs/metrics include pickup-to-confirmation latency and confirmation success count

---

### Story 6.3: Deliver Realistic E2E Fixture Pack and Expected Outcomes
**SP: 6 | Assignee:** Shikhar (Team B)

**Description:** Deliver fixture inputs and expected outcomes required to run reliable end-to-end validation without ad-hoc data assumptions.

**Acceptance Criteria:**
- Fixture pack and expected outcome definitions are checked in with scenario index
- Validation tests confirm fixtures load correctly at pipeline entry points
- Coverage matrix maps each fixture to expected keep/drop outcomes
- Story evidence includes fixture inventory, expected outcomes, and validation output

---

### Story 6.4: Deliver Full E2E Smoke Execution and Trace Evidence
**SP: 6 | Assignee:** Raghuram (Team B)

**Description:** Deliver one complete E2E run from orchestration trigger through delivery with traceable identifiers and run report.

**Acceptance Criteria:**
- Full pipeline run completes without hidden manual data edits during execution
- Evidence includes Step Functions execution ID, Glue run IDs, worker identifiers, and delivery confirmation reference
- Run report captures phase timing and key pass/fail checkpoints
- Logs/metrics include end-to-end duration and phase completion timestamps

---

### Story 6.5: Deliver Stage-Output and Business-Rule Count Validation
**SP: 6 | Assignee:** Gulfraz (Team B)

**Description:** Deliver the stage-level validation artifacts proving counts and rule behavior match expected fixture outcomes.

**Acceptance Criteria:**
- Validation artifact is checked in comparing expected vs actual counts across Pass 1, enrichment, Pass 2, and egress
- At least one E2E run shows counts matching expected outcomes or documents explicit mismatches
- Mismatch report template is included for reusable defect triage
- Logs/metrics include stage-level row counts and mismatch counts

---

### Story 6.6: Deliver Timing and KEDA Scaling Evidence Package
**SP: 6 | Assignee:** Naveen (Team C)

**Description:** Deliver measurable runtime baselines by packaging phase timing and KEDA scale behavior evidence from smoke runs.

**Acceptance Criteria:**
- Timing/scaling evidence package is checked in with phase durations and scale events
- Captured evidence includes at least one full scale-up and scale-down cycle with timestamps
- Data sources for evidence (logs/metrics/screenshots) are linked and reproducible
- Story handoff includes baseline summary and identified tuning candidates

---

### Story 6.7: Deliver Expected-Output Manifests and Comparator Engine
**SP: 6 | Assignee:** Nisarg (Team C)

**Description:** Deliver automated output correctness checking using checked-in expected manifests and comparator execution.

**Acceptance Criteria:**
- Expected-output manifests and comparator code are checked in with versioned fixture references
- Tests cover match, missing record, extra record, and malformed manifest scenarios
- One comparator run evidence record is produced for latest smoke output
- Logs/metrics include expected count, actual count, matched count, and mismatch count

---

### Story 6.8: Deliver Diff Reporting and Optional Validation Orchestration Stage
**SP: 7 | Assignee:** Uttam (Team C)

**Description:** Deliver readable mismatch diagnostics and orchestration integration so validation can run as an optional post-step.

**Acceptance Criteria:**
- Diff reporter and orchestration toggle for validation stage are checked in
- Tests validate enable/disable behavior and false-positive/false-negative reporting format
- One orchestration run proves validation stage can be enabled without changing core path behavior
- Logs/metrics include validation stage status, duration, and diff counts by type

---

### Story 6.9: Deliver Idempotency and Overwrite Verification Suite
**SP: 5 | Assignee:** Gulfraz (Team B)

**Description:** Deliver repeat-run verification proving deterministic outputs and overwrite behavior across identical reruns.

**Acceptance Criteria:**
- Repeat-run test suite is checked in and executes two runs against identical input
- Comparison output confirms deterministic fields and overwrite-not-append behavior
- Failing conditions are clearly reported with file-level and record-level differences
- Logs/metrics include run durations, equality result, and overwrite verification status

---

### Story 6.10: Deliver Negative-Path Resilience Test Pack and Alert Verification
**SP: 5 | Assignee:** Raghuram (Team B)

**Description:** Deliver resilience coverage for API/S3/ORC/timeout failures plus verification that alerts and correlation tracing work in those scenarios.

**Acceptance Criteria:**
- Negative-path test pack is checked in for API failures, malformed inputs, storage failures, and timeout scenarios
- Verification checklist confirms logs, alerts, and cross-service correlation data for exercised failures
- One traced failure example is documented end-to-end from trigger to alert
- Logs/metrics include failure type counters, retry counts, timeout counts, and alert issuance counts

---

### Story 6.11: Deliver Defect Register and Rerun Handoff Package
**SP: 6 | Assignee:** Suresh (Team A)

**Description:** Deliver sprint closure artifacts required for controlled handoff: defect register, rerun checklist, readiness status, and next actions.

**Acceptance Criteria:**
- Defect register and rerun checklist are published in agreed team location with version/date
- Handoff summary explicitly lists open risks, blocked items, and owner for each follow-up action
- Readiness section includes objective entry/exit criteria for Sprint 7 hardening
- Story evidence includes artifact links and sign-off record from sprint review
