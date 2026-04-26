# CDE Observability Layer — Implementation Guide

**Version:** 1.0  
**Date:** April 1, 2026  
**Owner:** CDE Pipeline Team  
**Governing Sprints:** Sprint 2 (contracts baseline), Sprint 3 (correlation propagation and filter-chain observability), Sprint 4-6 (K8s bridge/fetcher observability, Pass 2 observability, E2E validation evidence)

---

## 1. Purpose

This document defines how every CDE service component implements logging, metrics, health signals, and cross-service tracing. It aligns with:

- **Application Log Format (v2)** — the mandatory Concur Logging Service mapping for structured JSON logs
- **GDPR Logging requirements** — ensuring no sensitive personal data (PII) enters logs
- **Concur K8s stdout/stderr logging** — the required container logging path via FluentBit/kube-logging
- **AWS Lambda logging** — single-line JSON to stdout, collected by the Central Logging pipeline
- **Elasticsearch Watcher alerting** — proactive change-detection over indexed log data

All CDE components must comply with these contracts starting Sprint 2.

---

## 2. Logging Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       CDE Logging Data Flow                             │
│                                                                         │
│  ┌───────────────┐   stdout/JSON    ┌───────────────────┐               │
│  │  K8s Workers  │ ───────────────► │  FluentBit        │               │
│  │  (Pods)       │                  │  (DaemonSet)      │               │
│  └───────────────┘                  └───────┬───────────┘               │
│                                             │                           │
│  ┌───────────────┐   stdout/JSON    ┌───────▼────────────┐              │
│  │  AWS Lambda   │ ───────────────► │  Central Logging   │              │
│  │  (Init/CB)    │                  │  S3 → Logstash     │              │
│  └───────────────┘                  └────────┬───────────┘              │
│                                              │                          │
│  ┌───────────────┐   Spark Log4j    ┌────────▼───────────┐              │
│  │  AWS Glue     │ ───────────────► │  CloudWatch Logs   │──► Logstash  │
│  │  (core_runner)│                  │  → S3 bucket       │              │
│  └───────────────┘                  └────────────────────┘              │
│                                             │                           │
│                                    ┌────────▼────────────┐              │
│                                    │  Elasticsearch      │              │
│                                    │  (Logging Service)  │              │
│                                    └────────┬────────────┘              │
│                                             │                           │
│                               ┌─────────────▼───────────────┐           │
│                               │  Kibana (search, dashboard, │           │
│                               │  Watcher alerts)            │           │
│                               └─────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Application Log Format (v2) — Required Field Contract

All CDE log events must produce single-line JSON conforming to the Concur Application Log Format v2 mapping. This is enforced via JSON Schema at `src/contracts/log_contract_v2.json` (Sprint 2 baseline).

### 3.1 Required Fields

Every log line emitted by any CDE component **must** contain at minimum:

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `type` | string | Always `"log"` for application logs | `"log"` |
| `data_version` | integer | Always `2` | `2` |
| `application` | string | Application identifier | `"cde"` |
| `roletype` | string | Component/service role | `"cde-glue"`, `"cde-init-lambda"` |
| `level` | string | Log level: `debug`, `info`, `warn`, `error` | `"info"` |
| `@timestamp` | ISO 8601 | Event timestamp in UTC | `"2026-04-01T12:00:00.000Z"` |
| `correlation_id` | UUID v4 | Cross-service trace identifier (lowercase, hyphenated) | `"550e8400-e29b-41d4-a716-446655440000"` |

**Critical:** If `type`, `data_version`, or `application` are missing or invalid, the log document is routed to the `trash` index and will **not** appear in Kibana under normal index patterns.

### 3.2 Recommended Fields

| Field | Type | When Used |
|-------|------|-----------|
| `name` | string | Named structured event (e.g., `"bootstrap_started"`) |
| `description` | string | Human-readable detail |
| `execution_id` | string | SFN/Glue execution identifier |
| `duration_ms` | float | Latency measurement |
| `environment` | string | Deployment environment (`integration`, `production`) |
| `application_version` | string | Running version (`"1.0.0"`) |
| `category` | string | Log event category for grouping |

### 3.3 Custom Bucket

CDE will request a custom bucket **`cde_data`** in the Logging Service mapping for pipeline-specific fields that do not fit into common fields. Custom bucket fields follow the `_data` suffix naming convention. Examples:

| Field Path | Type | Purpose |
|------------|------|---------|
| `cde_data.pass_number` | integer | Current Glue pass (1 or 2) |
| `cde_data.strategy_name` | string | Active strategy (`"expense"`, `"trip"`) |
| `cde_data.strategy_version` | string | Strategy module version |
| `cde_data.input_row_count` | long | Rows read in current stage |
| `cde_data.output_row_count` | long | Rows written in current stage |
| `cde_data.filter_stage` | string | Current filter name (`"dedup"`, `"consent_join"`) |
| `cde_data.dropped_row_count` | long | Rows filtered out at this stage |

Custom bucket requests will be submitted through the Concur Logging Service Request process per the documented procedure.

### 3.4 Minimal Valid Log Example

```json
{
  "type": "log",
  "data_version": 2,
  "application": "cde",
  "roletype": "cde-glue",
  "level": "info",
  "@timestamp": "2026-04-01T12:34:56.789Z",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "bootstrap_started",
  "description": "Glue job bootstrap initiated for pass 1",
  "cde_data": {
    "pass_number": 1,
    "strategy_name": "expense",
    "strategy_version": "1.0.0"
  }
}
```

---

## 4. Data Privacy and PII Compliance

Per Concur Logging Service policy and GDPR Logging requirements:

| Rule | Implementation |
|------|----------------|
| **No sensitive PII in logs** | UUIDs are logged as-is (not sensitive). Names, emails, credit card numbers, passwords must never appear in log fields. |
| **No PCI data** | Payment card data is never logged. Logging Service is not a SIEM or PCI-compliant store. |
| **JWT token masking** | Logging Service ingestion pipeline auto-masks JWT tokens matching `/(eyJhbGciOi\|eyJ0eXAiOiJKV1Qi\|eyJraWQiOi)…/`. However, CDE code should avoid logging tokens in the first place. |
| **consent_mapping contents** | The `consent_mapping.json` contains company UUIDs and consent dates. UUIDs may appear in logs for tracing, but consent dates must not be logged in bulk. |
| **Vault secrets** | Vault-retrieved credentials are never logged. Only success/failure of auth retrieval and latency are emitted. (Sprint 4 auth/runtime hardening) |
| **Document size** | Keep individual log events well under 1 MB. Logging Service drops documents > 10 MB and truncates fields > 256 KB. |

---

## 5. Per-Service Logging Contracts

### 5.1 AWS Lambda — Init Lambda (`src/lambda/init_lambda.py`)

**Shipping method:** Single-line JSON to stdout → AWS Central Logging pipeline → S3 bucket → Logstash → Elasticsearch.  
Per the AWS Lambda logging doc, Lambda logs require no Filebeat installation. All JSON stdout is automatically collected in ATM environments.

**Roletype:** `cde-init-lambda`

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `strategy_load_started` | info | `strategy_name`, `s3_key`, `correlation_id` | 2 |
| `strategy_loaded` | info | `version`, `class_name` | 2 |
| `interface_validated` | info | `method_list` | 2 |
| `workflow_flags_returned` | info | `requires_api_enrichment` | 2 |

**Metrics:**
- `cde.lambda.strategy_load_success_count` (counter)
- `cde.lambda.strategy_load_failure_count` (counter, labeled by `error_type`)

**Error events:** `StrategyNotFoundError`, `StrategyImportError`, `InterfaceValidationError`, `StrategyTimeoutError` — each logged at `error` level with exception class and message.

---

### 5.2 AWS Lambda — Callback Lambda (`src/lambda/callback_lambda.py`)

**Shipping method:** Same as Init Lambda — stdout JSON → Central Logging → Elasticsearch.

**Roletype:** `cde-callback-lambda`

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `callback_received` | info | `token_hash`, `execution_id`, `correlation_id` | 4 |
| `callback_error` | error | `error_code`, `message` | 4 |
| `sns_consume_started` | info | `topic_name`, `message_id` | 4 |

**Metrics:**
- `cde.sfn.callback_success_count` (counter)
- `cde.sfn.callback_failure_count` (counter)

---

### 5.3 AWS Step Functions

**Shipping method:** Step Functions does not emit custom application logs directly. Observability comes from:
1. CloudWatch Metrics (built-in): execution duration, state transition counts
2. Execution history events (queryable via API)
3. Named log events emitted by Init Lambda and Callback Lambda at each boundary crossing

**Roletype:** `cde-sfn` (used in custom metric names only)

| Metric | Type | Labels | Sprint |
|--------|------|--------|--------|
| `cde.sfn.state_duration_ms` | histogram | `state_name` | 2 |
| `cde.sfn.state_transitions` | counter | `from_state`, `to_state` | 2 |
| `cde.sfn.choice_branch_selection` | counter | `branch_name` | 2 |
| `cde.sfn.async_timeout_count` | counter | — | 4 |
| `cde.sfn.callback_success_count` | counter | — | 4 |
| `cde.sfn.callback_failure_count` | counter | — | 4 |

---

### 5.4 AWS Glue — `core_runner.py` and Strategy Modules

**Shipping method:** Spark/Glue uses Log4j. CDE configures a custom JSON appender to emit structured logs compatible with Application Log Format v2. Glue job logs are written to CloudWatch Logs → forwarded to Logstash via the Central Logging pipeline.

**Roletype:** `cde-glue`

#### 5.4.1 Bootstrap and Routing Events (Sprint 2)

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `strategy_class_selected` | info | `strategy_name`, `class_name` | 2 |
| `glue_arguments_parsed` | info | `pass_number`, `execution_id` | 2 |
| `strategy_instantiated` | info | `version`, `requires_api_enrichment` | 2 |
| `bootstrap_started` | info | `app.name`, `app.version`, `pass_number`, `correlation_id` | 2 |
| `bootstrap_completed` | info | `bootstrap_status`, `bootstrap_duration_ms` | 2 |
| `bootstrap_failed` | error | `reason`, `error_message` | 2 |

**Metrics:**
- `cde.glue.strategy_import_duration_ms` (histogram)
- `cde.glue.argument_parse_duration_ms` (histogram)
- `cde.glue.bootstrap_duration_ms` (histogram)
- `cde.glue.pass_number_selected` (counter, labeled `pass=1`, `pass=2`)
- `cde.glue.bootstrap_failure_count` (counter, labeled by `error_type`)

#### 5.4.2 Data I/O Events (Sprint 2 baseline, Sprint 5 Pass 2 extension)

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `orc_read_started` | info | `s3_path`, `correlation_id` | 2 |
| `orc_read_completed` | info | `row_count`, `duration_ms` | 2 |
| `parquet_write_completed` | info | `s3_path`, `row_count`, `file_size_bytes` | 2 |
| `pass2_noop_identity_transform` | info | `input_rows`, `output_rows` | 5 |

**Metrics:**
- `cde.glue.input_row_count` (counter, labeled `pass=1`, `pass=2`)
- `cde.glue.output_row_count` (counter, labeled by pass)
- `cde.glue.io_duration_ms` (histogram, labeled by operation: `read_orc`, `write_pass1_parquet`, `read_pass1_parquet`, `write_pass2_parquet`)

#### 5.4.3 Ingestion and Schema Validation Events (Sprint 3)

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `ingestion_started` | info | `format`, `input_path`, `correlation_id` | 3 |
| `schema_validation_completed` | info | `valid_count`, `invalid_count`, `null_field_count` | 3 |
| `invalid_row_logged` | warn | `row_index`, `missing_field_names` or `null_field_names` | 3 |
| `read_completed` | info | `row_count`, `duration_ms` | 3 |

**Metrics:**
- `cde.glue.schema_validation_failure_count` (counter, labeled by reason: `missing_field`, `null_value`, `bad_type`, `parse_error`)
- `cde.glue.read_duration_ms` (histogram)

#### 5.4.4 Pass 1 Filter Stage Events (Sprint 3)

Each filter stage inside `strategy.apply_transform(..., pass_id=1, ...)` emits entry/exit events:

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `dedup_stage_completed` | info | `input_rows`, `output_rows`, `dropped_count` | 3 |
| `consent_join_completed` | info | `input_rows`, `matched_count`, `unmatched_count` | 3 |
| `category_filter_completed` | info | `input_rows`, `output_rows`, `dropped_count` | 3 |
| `filter_chain_completed` | info | `stage_count`, per-stage `row_counts` array | 3 |

**Metrics:**
- `cde.glue.dedup_dropped_count` (counter)
- `cde.glue.consent_join_hit_count` / `consent_join_miss_count` (counters)
- `cde.glue.category_filter_dropped_count` (counter)
- `cde.glue.filter_stage_row_count` (gauge, labeled by `stage_name`)

#### 5.4.5 UUID Extraction and Output Events (Sprint 3)

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `uuid_extraction_completed` | info | `uuid_count`, `output_path` | 3 |
| `pass1_parquet_written` | info | `row_count`, `s3_path`, `file_size_bytes` | 3 |
| `pass1_completion_sns_published` | info | `topic_arn`, `message_id` | 3 |

**Metrics:**
- `cde.glue.uuid_extract_count` (counter)
- `cde.glue.pass1_output_row_count` (counter)
- `cde.sns.publish_count` (counter, labeled by `topic_name`)

#### 5.4.6 Pass 2 Rule and Egress Observability (Sprint 5)

Sprint 5 introduces Pass 2-specific observability expectations for loader, normalization, join, rule evaluation, egress, and optional skip-path execution.

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `pass2_inputs_loaded` | info | `pass1_row_count`, `api_row_count`, `duration_ms` | 5 |
| `pass2_normalization_completed` | info | `travel_parsed_count`, `spend_parsed_count`, `mismatch_count` | 5 |
| `pass2_mapping_join_completed` | info | `join_strategy`, `post_join_row_count`, `null_mapping_count` | 5 |
| `pass2_rules_evaluated` | info | `kept_count`, `dropped_count`, `competitor_drop_count` | 5 |
| `pass2_egress_written` | info | `output_path`, `record_count`, `file_count`, `duration_ms` | 5 |
| `pass2_manifest_published` | info | `manifest_path`, `manifest_version`, `publish_status` | 5 |
| `pass2_enrichment_skipped` | info | `requires_api_enrichment`, `branch_duration_ms` | 5 |

**Metrics:**
- `cde.glue.input_row_count` (counter)
- `cde.glue.output_row_count` (counter)
- `cde.glue.io_duration_ms` (histogram)
- `cde.glue.read_duration_ms` (histogram)

---

### 5.5 SNS Event Topics (Sprint 2 baseline, Sprint 4 callback path)

**Shipping method:** SNS events are not logs per se, but the publisher and consumer code emit log events around publish/consume operations.

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `sns_publish_requested` | info | `topic_name`, `correlation_id` | 2 |
| `sns_publish_completed` | info | `topic_arn`, `message_id` | 2 |

**Metrics:**
- `cde.sns.publish_count` (counter, labeled by `topic_name`)
- `cde.sns.consume_to_callback_latency_ms` (histogram, labeled by `topic_name`)

**Payload contracts:**
- `cde-raw-data-arrival`: `{"bucket", "key", "event_time", "correlation_id"}` — validated by contract tests (Sprint 2)
- `cde-glue-pass1-complete`: `{"execution_id", "pass_number", "job_status", "output_location", "record_count"}` — validated by contract tests (Sprint 2)

---

### 5.6 Kubernetes Workers (SQS Consumer / API Enrichment)

**Shipping method:** K8s pods write JSON to stdout/stderr. FluentBit (kube-logging DaemonSet) automatically collects from every worker node and ships to Logstash → Elasticsearch. No Filebeat installation needed.

This is the **recommended** method per the Containerized Services Logging documentation: "applications just need to send logs to stdout/stderr, properly formatted, and logs are automatically collected."

**Roletype:** `cde-k8s-worker`

| Named Event | Level | Key Fields | Sprint |
|-------------|-------|------------|--------|
| `sqs_message_received` | info | `message_id`, `correlation_id`, `task_token_hash` | 4 |
| `api_call_attempt` | info | `attempt_number`, `status_code_or_exception`, `backoff_duration_ms` | 4 |
| `api_call_failed_retryable` | warn | `status_code`, `attempts_remaining` | 4 |
| `api_call_failed_terminal` | error | `status_code`, `request_id` | 4 |
| `batch_partial_success` | warn | `success_count`, `failure_count`, `failed_company_ids` | 4 |
| `consent_mapping_builder_started` | info | `input_record_count` | 4 |
| `consent_mapping_write_completed` | info | `entry_count`, `file_size_bytes`, `s3_path` | 4 |
| `task_callback_sent` | info | `execution_id`, `task_token_hash` | 4 |

**Metrics:**
- `cde.api.retry_attempt_count` (histogram)
- `cde.api.backoff_duration_ms` (histogram, labeled by `attempt_number`)
- `cde.api.terminal_failure_count` (counter, labeled by `endpoint`, `status_code`)
- `cde.consent_mapping.entry_count` (counter)
- `cde.consent_mapping.write_duration_ms` (histogram)

---

## 6. Correlation ID Propagation (Sprint 3 baseline, Sprint 4 cross-boundary enforcement)

The `correlation_id` field is the single most important observability primitive in CDE. It enables tracing a complete pipeline execution across all service boundaries in Kibana.

### 6.1 Generation

Generated **once** at EventBridge trigger time as UUID v4 (lowercase with hyphens, 36 characters).  
Example: `550e8400-e29b-41d4-a716-446655440000`

### 6.2 Propagation Path

```
 EventBridge                  Step Functions               Init Lambda
 ┌───────────┐  detail.       ┌──────────────┐  InputPath  ┌───────────┐
 │ Schedule  │──correlation──►│ Execution    │──$.corr────►│ Handler   │
 │ Rule      │  _id           │ Input        │  elation_id │           │
 └───────────┘                └─────┬────────┘             └───────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     ▼              ▼              ▼
              ┌────────────┐ ┌──────────┐ ┌─────────────┐
              │ Glue Job   │ │ SQS Msg  │ │ SNS Message │
              │ --corr..   │ │ Attribute│ │ Attribute   │
              │ _id arg    │ │ corr_id  │ │ corr_id     │
              └────────────┘ └──────────┘ └──────┬──────┘
                                                 ▼
                                          ┌─────────────┐
                                          │ Callback    │
                                          │ Lambda      │
                                          │ event.MA.   │
                                          │ correlation │
                                          │ _id         │
                                          └─────────────┘
```

### 6.3 Boundary Transport Summary

| # | Boundary | Transport Mechanism | Field Path |
|---|----------|---------------------|------------|
| 1 | EventBridge → Step Functions | Event detail JSON | `detail.correlation_id` |
| 2 | Step Functions → Init Lambda | Lambda InputPath | `correlation_id` |
| 3 | Step Functions → Glue | Glue job argument | `--correlation_id` |
| 4 | Step Functions → SQS | SQS message attribute | `correlation_id` (string) |
| 5 | Glue → SNS | SNS message attribute | `correlation_id` (string) |
| 6 | SNS → Callback Lambda | MessageAttributes | `event.MessageAttributes.correlation_id.StringValue` |

### 6.4 Correlation Coverage Metrics

| Metric | Type | Purpose |
|--------|------|---------|
| `cde.correlation.coverage_rate` | gauge (0–1) | Ratio of events that carry a valid `correlation_id` |
| `cde.correlation.missing_correlation_count` | counter | Increment when `correlation_id` is absent at a boundary |
| `cde.correlation.propagation_latency_ms` | histogram | Labeled per boundary hop |

### 6.5 Searching in Kibana

To trace an entire pipeline execution:

```
correlation_id: "550e8400-e29b-41d4-a716-446655440000"
```

This query, scoped to the `log-2` index pattern, returns every event from Init Lambda, Glue, K8s worker, Callback Lambda, and SNS publisher for that single run.

---

## 7. Metric Naming Taxonomy

All CDE metrics follow a strict naming pattern enforced by contract tests (Sprint 2 baseline):

```
^cde\.[a-z_]+\.(count|duration_ms|latency_ms)$
```

### 7.1 Namespace Structure

```
cde.
├── sfn.                          # Step Functions orchestration
│   ├── state_duration_ms
│   ├── state_transitions
│   ├── choice_branch_selection
│   ├── async_timeout_count
│   ├── callback_success_count
│   └── callback_failure_count
├── lambda.                       # Lambda functions
│   ├── strategy_load_success_count
│   └── strategy_load_failure_count
├── glue.                         # Glue job processing
│   ├── bootstrap_duration_ms
│   ├── pass_number_selected
│   ├── bootstrap_failure_count
│   ├── strategy_import_duration_ms
│   ├── argument_parse_duration_ms
│   ├── input_row_count
│   ├── output_row_count
│   ├── io_duration_ms
│   ├── read_duration_ms
│   ├── schema_validation_failure_count
│   ├── dedup_dropped_count
│   ├── consent_join_hit_count
│   ├── consent_join_miss_count
│   ├── category_filter_dropped_count
│   ├── filter_stage_row_count
│   ├── uuid_extract_count
│   └── pass1_output_row_count
├── sns.                          # SNS event topics
│   ├── publish_count
│   └── consume_to_callback_latency_ms
├── api.                          # External API calls
│   ├── retry_attempt_count
│   ├── backoff_duration_ms
│   └── terminal_failure_count
├── consent_mapping.              # Consent mapping builder
│   ├── entry_count
│   ├── write_duration_ms
│   └── write_status
└── correlation.                  # Cross-service tracing
    ├── coverage_rate
    ├── missing_correlation_count
    └── propagation_latency_ms
```

---

## 8. Health Signals

### 8.1 Kubernetes Workers

K8s pods expose standard health probes per the CDE health signal contract (`src/contracts/health_signals.json`, Sprint 2 baseline):

| Probe | Path | Interval | Threshold |
|-------|------|----------|-----------|
| Readiness | `/health/ready` | 10s | 3 failures → not ready |
| Liveness | `/health/live` | 30s | 5 failures → restart |

Probe responses are JSON:
```json
{"status": "ok", "component": "cde-k8s-worker", "timestamp": "2026-04-01T12:00:00Z"}
```

### 8.2 HeartBeat Monitoring

For uptime monitoring of dependent services (Config API, Consent API, S3 endpoints), the team may deploy Elastic HeartBeat probes. HeartBeat supports ICMP, TCP, and HTTP monitors, and results are indexed in `heartbeat-*` pattern in Kibana. This provides:

- Service availability dashboards
- SLA compliance tracking
- Dependency health alerting via Watcher

### 8.3 Glue Job Heartbeat

Long-running Glue jobs emit periodic progress events:
```json
{
  "type": "log",
  "data_version": 2,
  "application": "cde",
  "roletype": "cde-glue",
  "level": "info",
  "name": "heartbeat",
  "correlation_id": "...",
  "cde_data": {
    "pass_number": 1,
    "rows_processed": 50000,
    "elapsed_ms": 120000
  }
}
```

This satisfies the Sprint 2 guardrail: "heartbeat/progress signals are required for long-running or async stages."

---

## 9. Shipping Methods by Component

| Component | Runtime | Log Shipping Method | Reference Doc |
|-----------|---------|---------------------|---------------|
| Init Lambda | AWS Lambda | stdout JSON → Central Logging S3 → Logstash | AWS Lambda logging doc |
| Callback Lambda | AWS Lambda | stdout JSON → Central Logging S3 → Logstash | AWS Lambda logging doc |
| Glue `core_runner.py` | AWS Glue (Spark) | Log4j JSON appender → CloudWatch → Logstash | Application Logging doc |
| K8s SQS Worker | Kubernetes Pod | stdout JSON → FluentBit DaemonSet → Logstash | Containerized Services Logging doc |
| K8s API Fetcher | Kubernetes Pod | stdout JSON → FluentBit DaemonSet → Logstash | Containerized Services Logging doc |

**Key rules from Concur docs:**
1. Kubernetes: just send to stdout/stderr in correct JSON format. FluentBit (kube-logging) auto-collects. No Filebeat needed.
2. Lambda: single-line JSON to stdout. Collected by CLZ pipeline to S3, then Logstash picks up.
3. All: incorrect JSON format means logs end up in the Kibana `trash` index and are effectively invisible.

---

## 10. Alerting with Elasticsearch Watcher

The team will configure Watcher alerts for critical failure scenarios:

| Alert | Condition | Action | Sprint |
|-------|-----------|--------|--------|
| Pipeline stall | No `pass1_completion_sns_published` event within 4 hours of scheduled trigger | Slack notification to `#cde-alerts` | 3 |
| High schema validation failure rate | `cde.glue.schema_validation_failure_count` > 5% of `input_row_count` in 1 hour | Email to on-call + Slack | 3 |
| API terminal failure spike | `cde.api.terminal_failure_count` > 10 in 15 minutes | PagerDuty escalation | 3 |
| Missing correlation ID | `cde.correlation.missing_correlation_count` > 0 in any 1-hour window | Slack warning | 3 |
| Async callback timeout | `cde.sfn.async_timeout_count` > 0 | Email to on-call | 4 |

Watcher definitions will be maintained in the repository under `infrastructure/watchers/` and follow the Watcher Tips best practices documented in the Concur Logging Service docs.

---

## 11. Anti-Patterns to Avoid

Per the Concur Logging Service Bad Practices documentation:

| Anti-Pattern | CDE Mitigation |
|--------------|----------------|
| **Wildcard queries in dashboards** | All Kibana dashboards must scope queries to specific index patterns (`log-2`) and use `application: "cde"` filter |
| **Excessive logging under failure** | Error loops (e.g., dependency down) must use rate-limited logging: log first occurrence + periodic summary, not one event per retry |
| **Redundant field duplication** | Never duplicate a value in both `description` and `exception_obj.message`. Use one field per purpose |
| **Short dashboard refresh rates** | CDE Kibana dashboards default to 5-minute refresh, never below 1 minute |
| **Missing time range filters** | All saved searches and Watcher queries must include `@timestamp` range filter |
| **No index defined in Timelion/TSVB** | Always specify index pattern explicitly in visualizations |

---

## 12. Log Retention and Data Tiers

Per Concur Logging Service data tier architecture:

| Tier | Data Age | Storage | Query Latency |
|------|----------|---------|---------------|
| **Hot** | 0–4 hours | SSD with replicas (c6gd) | < 5s |
| **Cold** | 4 hours – 5 days | SSD, no replicas (i3en), replica in S3 | < 20s |
| **Frozen** | 5 days – retention limit | Searchable snapshot in S3 | < 5 min (first), < 20s (cached) |

**Default application log retention:** 6 weeks.  
**GDPR audit logs (`access-*`, `change-*`):** 13 months retention, different DR/backup.

For historical investigation beyond the hot tier, use Kibana Saved Sessions (async search) to avoid cluster overload.

---

## 13. Contract Artifacts and Test Evidence

| Artifact | Path | Sprint |
|----------|------|--------|
| Log field contract schema | `src/contracts/log_contract_v2.json` | 2 |
| Metric naming taxonomy | `src/contracts/metric_taxonomy.md` | 2 |
| Health signal contract | `src/contracts/health_signals.json` | 2 |
| SFN payload envelope schema | `src/contracts/sfn_payload_v2.json` | 2 |
| Reference payload examples | `docs/payload_examples/*.json` | 2 |
| Contract validation tests | `tests/unit/test_contracts.py` | 2 |
| Correlation propagation tests | `tests/unit/test_correlation_propagation.py` | 3 |
| E2E tracing evidence | `tests/integration/trace_evidence_snapshot.json` | 6 |

---

## 14. Implementation Checklist

Every developer implementing CDE sprint deliverables must verify:

- [ ] All log events are single-line JSON with required fields (`type`, `data_version`, `application`, `roletype`, `level`, `@timestamp`)
- [ ] `correlation_id` is present in **every** log line
- [ ] No sensitive PII or PCI data in any log field
- [ ] Named events use the `name` field (not embedded in `description`)
- [ ] Metrics follow the `cde.<namespace>.<metric_name>` taxonomy
- [ ] Custom data uses the `cde_data` bucket (not ad-hoc top-level fields)
- [ ] K8s components log to stdout/stderr only (no file-based logging)
- [ ] Lambda components produce single-line JSON to stdout
- [ ] Error logging is rate-limited (no flood on dependency failure)
- [ ] Contract tests pass for any new payload or event schema
