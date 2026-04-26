# CDE - Detailed Sprint Stories & Subtasks Sprints 7-8

**Team:** 9 developers | **Capacity:** ~65 SP/sprint | **Go-live:** Jul 7, 2026

## Team Structure

| Team | Senior Tech Lead (Python) | PySpark Developer | Python Developer |
|------|---------------------------|-------------------|------------------|
| **A** | Suresh | Prashanth | Pankaj |
| **B** | Raghuram | Gulfraz | Shikhar |
| **C** | Uttam | Naveen | Nisarg |

---

# Sprint 7 - Observability, Error Handling & Hardening
**Jun 10 - Jun 23** | ~65 SP

### Sprint 7 Story Assignments

| Story | SP | Owner | Team |
|-------|----|-------|------|
| 7.1 dv2 Structured Logging | 16 | Suresh | A |
| 7.2 Correlation ID Propagation | 13 | Raghuram | B |
| 7.3 CloudWatch Dashboards & Alerting | 13 | Uttam | C |
| 7.4 SFN Retry & Error Handling | 10 | Suresh | A |
| 7.5 Load Testing | 13 | Raghuram | B |
| **Total** | **65** | | |

### Sprint 7 Developer Load

| Developer | Role | 7.1 | 7.2 | 7.3 | 7.4 | 7.5 | Total |
|-----------|------|-----|-----|-----|-----|-----|-------|
| Suresh | Lead (A) | 3 | - | 2 | 2 | - | **7** |
| Prashanth | PySpark (A) | 4 | - | - | 2 | 3 | **9** |
| Pankaj | Python (A) | 3 | 2 | - | - | 2 | **7** |
| Raghuram | Lead (B) | - | 2 | - | 2 | 2 | **6** |
| Gulfraz | PySpark (B) | - | 2 | 2 | 1 | 2 | **7** |
| Shikhar | Python (B) | 3 | 2 | 2 | - | - | **7** |
| Uttam | Lead (C) | - | 2 | 2 | - | 2 | **6** |
| Naveen | PySpark (C) | - | 3 | 2 | 2 | 2 | **9** |
| Nisarg | Python (C) | 3 | - | 3 | 1 | - | **7** |
| **Total** | | **16** | **13** | **13** | **10** | **13** | **65** |

---

### Story 7.1: dv2-Compliant Structured Logging Across All Components
**SP: 16** | **Owner:** Suresh (Team A)

**Description:** Implement Concur `dv2` Application Log Format compliant structured JSON logging in all CDE components: K8s Job (Python), Init Lambda (Python), AWS Glue (PySpark). Each log line must be a single-line JSON object with required fields: `@timestamp`, `type`, `data_version`, `application`, `roletype`, `correlation_id`, `name`, `level`. Use `structlog` for K8s/Lambda and Python's `logging` with a custom JSON formatter for Glue.

**Acceptance Criteria:**
- All components emit single-line JSON logs to STDOUT conforming to dv2 format
- Required fields present on every log line: `@timestamp` (ISO8601), `type: "log"`, `data_version: 2`, `application: "cde"`, `roletype`, `correlation_id`
- Logs are under 1MB per line (dv2 size limitation)
- Log level correctly set: INFO for normal operations, WARN for retries, ERROR for failures
- Logs are indexed correctly in Elasticsearch (not trashed due to format violations)

**Subtasks:**
- **[3 SP] [Pankaj]** Implement `structlog` JSON formatter for K8s Job with dv2 required fields as bound context
- **[3 SP] [Shikhar]** Implement `structlog` JSON formatter for Init Lambda with dv2 required fields
- **[4 SP] [Prashanth]** Implement Python `logging.Formatter` subclass for Glue that outputs dv2-compliant JSON to STDOUT
- **[3 SP] [Suresh]** Add `correlation_id`, `application`, `roletype`, `environment` as base context to all formatters
- **[3 SP] [Nisarg]** Validate log output against dv2 field requirements - test one log line per component in Kibana

---

### Story 7.2: Correlation ID Propagation End-to-End
**SP: 13** | **Owner:** Raghuram (Team B)

**Description:** Implement `correlation_id` generation and propagation across the entire pipeline. Step Functions generates the correlation ID on execution start. It flows through: Init Lambda -> SQS message -> K8s Job -> CTE API calls (as `concur-correlationid` HTTP header) -> Glue job arguments -> SNS messages. Every log line across all components includes the same correlation ID, enabling end-to-end tracing in Kibana.

**Acceptance Criteria:**
- Step Functions generates a UUID `correlation_id` at execution start and passes it to all downstream states
- Init Lambda receives and logs with `correlation_id`
- SQS message body includes `correlation_id`; K8s Job extracts and uses it for all logging and API calls
- K8s Job sends `concur-correlationid` header on all CTE API calls
- Glue job receives `correlation_id` as a job argument and includes it in all log lines
- A single Kibana query on `correlation_id` returns logs from all components for one pipeline run

**Subtasks:**
- **[2 SP] [Raghuram]** Add `correlation_id` generation to Step Functions input processing (use `States.UUID()` or Lambda-generated)
- **[2 SP] [Uttam]** Pass `correlation_id` through all Step Functions state outputs/inputs
- **[2 SP] [Shikhar]** Include `correlation_id` in SQS message body; extract in K8s Job
- **[2 SP] [Pankaj]** Add `concur-correlationid` header to all HTTP requests in K8s Job
- **[3 SP] [Naveen]** Pass `correlation_id` as `--correlation_id` Glue job argument; bind to logging context
- **[2 SP] [Gulfraz]** Test: run pipeline -> query Kibana with correlation_id -> verify logs from Lambda, K8s, Glue all appear

---

### Story 7.3: CloudWatch Dashboards & SNS Alerting
**SP: 13** | **Owner:** Uttam (Team C)

**Description:** Build CloudWatch dashboards and alerts for operational monitoring. Dashboard shows: Step Functions execution status (success/fail/running), Glue job duration and DPU usage, SQS queue depth, K8s Job success/failure counts, and pipeline end-to-end latency. SNS alerts fire on: pipeline failure, Glue job timeout, SQS DLQ message arrival, and K8s Job failure.

**Acceptance Criteria:**
- CloudWatch dashboard exists with widgets for: SFN execution status, Glue duration, SQS depth, pipeline latency
- SNS alert configured for: Step Functions execution failure
- SNS alert configured for: Glue job exceeding 30-minute timeout
- SNS alert configured for: message arriving in SQS dead-letter queue
- Alert notifications delivered to CDE team Slack channel or email distribution list

**Subtasks:**
- **[2 SP] [Uttam]** Create CloudWatch dashboard with Step Functions execution metrics (succeeded, failed, timed out)
- **[2 SP] [Naveen]** Add Glue job widgets: execution duration, DPU-hours consumed, records processed (from custom metrics)
- **[2 SP] [Gulfraz]** Add SQS widgets: queue depth, age of oldest message, DLQ message count
- **[3 SP] [Nisarg]** Create SNS topic for CDE alerts; subscribe team Slack webhook or email
- **[2 SP] [Suresh]** Create CloudWatch Alarms: SFN failure -> SNS, Glue timeout -> SNS, SQS DLQ > 0 -> SNS
- **[2 SP] [Shikhar]** Test each alert by triggering a failure condition and verifying notification delivery

---

### Story 7.4: Step Functions Retry & Error Handling Blocks
**SP: 10** | **Owner:** Suresh (Team A)

**Description:** Add production-grade retry and Catch blocks to every Task state in the Step Functions state machine. Glue jobs retry on transient failures (service unavailable) with exponential backoff. Lambda retries on throttling. SQS Task Token states handle timeout with a fallback error state. A terminal "PipelineFailure" state logs the error, publishes an SNS alert, and marks the execution as failed.

**Acceptance Criteria:**
- All Task states have Retry blocks for transient errors (ServiceUnavailable, ThrottlingException) with exponential backoff
- All Task states have Catch blocks routing to the PipelineFailure state
- PipelineFailure state logs the error context and publishes to the alert SNS topic
- Task Token wait states have HeartbeatSeconds configured with Catch for States.Timeout
- Tested: each error path correctly routes to PipelineFailure and fires the alert

**Subtasks:**
- **[2 SP] [Prashanth]** Add Retry blocks to Glue Task states: `IntervalSeconds: 30, MaxAttempts: 3, BackoffRate: 2`
- **[2 SP] [Raghuram]** Add Retry blocks to Lambda Task state: `IntervalSeconds: 5, MaxAttempts: 3`
- **[2 SP] [Suresh]** Add Catch blocks to all Task states routing to `PipelineFailure` state
- **[1 SP] [Nisarg]** Implement `PipelineFailure` state: log error context, publish to SNS alert topic, fail execution
- **[1 SP] [Gulfraz]** Add `HeartbeatSeconds: 3600` to SQS Task Token state with Catch for `States.Timeout`
- **[2 SP] [Naveen]** Test each error path: force Glue failure, force Lambda timeout, force Task Token timeout

---

### Story 7.5: Load Testing with Production-Scale Data
**SP: 13** | **Owner:** Raghuram (Team B)

**Description:** Generate a production-scale test dataset (matching expected daily CDP export volume - estimate: 500K-1M records, 2-5 GB ORC) and run the full pipeline end-to-end. Measure: Glue Pass 1 duration, K8s API fetch throughput, Glue Pass 2 duration, total pipeline latency. Identify bottlenecks and fix performance issues. Validate that KEDA scales correctly and that no component OOMs.

**Acceptance Criteria:**
- Test dataset of 500K+ records (2+ GB) processes successfully end-to-end
- Glue Pass 1 completes within 15 minutes
- K8s API fetch phase completes within 30 minutes
- Glue Pass 2 completes within 15 minutes
- Total pipeline latency documented; no OOM failures in any component
- Performance bottleneck report filed with recommendations (if any)

**Subtasks:**
- **[3 SP] [Prashanth]** Generate production-scale ORC fixture: 500K records with realistic distribution of valid/invalid data
- **[2 SP] [Raghuram]** Run full pipeline and record timing per phase from Step Functions execution history
- **[2 SP] [Gulfraz]** Monitor Glue executor memory and shuffle metrics during both passes
- **[2 SP] [Pankaj]** Monitor K8s Job memory usage during concurrent API calls
- **[2 SP] [Uttam]** Validate KEDA scales pod correctly and returns to zero after completion
- **[2 SP] [Naveen]** Document results: phase timings, resource utilization, identified bottlenecks, recommended Glue DPU count

---

# Sprint 8 - Production Readiness, Security & Go-Live
**Jun 24 - Jul 7** | ~65 SP

### Sprint 8 Story Assignments

| Story | SP | Owner | Team |
|-------|----|-------|------|
| 8.1 AppSec Scans & Remediation | 13 | Raghuram | B |
| 8.2 S3 Encryption (CMK) & IAM Hardening | 13 | Raghuram | B |
| 8.3 Operational Runbook | 13 | Uttam | C |
| 8.4 Prod Deployment & Shadow-Mode | 15 | Suresh | A |
| 8.5 Go/No-Go Review & Go-Live | 7 | Suresh | A |
| 8.6 Post-Go-Live Buffer | 4 | Uttam | C |
| **Total** | **65** | | |

### Sprint 8 Developer Load

| Developer | Role | 8.1 | 8.2 | 8.3 | 8.4 | 8.5 | 8.6 | Total |
|-----------|------|-----|-----|-----|-----|-----|-----|-------|
| Suresh | Lead (A) | - | 2 | - | 3 | 2 | - | **7** |
| Prashanth | PySpark (A) | - | - | 4 | 2 | 1 | - | **7** |
| Pankaj | Python (A) | 2 | - | 2 | 2 | 1 | - | **7** |
| Raghuram | Lead (B) | - | 4 | 3 | - | - | - | **7** |
| Gulfraz | PySpark (B) | 3 | 2 | - | 2 | 1 | - | **8** |
| Shikhar | Python (B) | 3 | 2 | - | 2 | - | - | **7** |
| Uttam | Lead (C) | - | - | 2 | 2 | 1 | 2 | **7** |
| Naveen | PySpark (C) | - | 3 | 2 | 2 | - | 1 | **8** |
| Nisarg | Python (C) | 5 | - | - | - | 1 | 1 | **7** |
| **Total** | | **13** | **13** | **13** | **15** | **7** | **4** | **65** |

---

### Story 8.1: AppSec Scans & Vulnerability Remediation
**SP: 13** | **Owner:** Raghuram (Team B)

**Description:** Execute all required security scans: SAST (static code analysis), DAST (dynamic application security testing), dependency vulnerability audit (Snyk/Mend), and container image scanning for the K8s Job Docker image. Remediate all critical and high-severity findings. Document accepted risks for medium/low findings.

**Acceptance Criteria:**
- SAST scan completed on all Python code (core_runner.py, Strategy files, K8s Job)
- DAST scan completed against K8s Job endpoints (if any) and Lambda
- Dependency audit completed: zero critical/high vulnerabilities in requirements.txt
- Container image scan completed: zero critical/high CVEs in K8s Job Docker image
- Remediation evidence documented; accepted risks (if any) signed off by AppSec team

**Subtasks:**
- **[3 SP] [Nisarg]** Run SAST tool on all Python source files; remediate critical/high findings
- **[3 SP] [Shikhar]** Run dependency vulnerability scan on `requirements.txt` and `Pipfile`; upgrade vulnerable packages
- **[3 SP] [Gulfraz]** Run container image scan on K8s Job Docker image; rebuild with patched base image if needed
- **[2 SP] [Nisarg]** Run DAST scan against deployed K8s service and Lambda endpoints
- **[2 SP] [Pankaj]** Document scan results and accepted risks in the security review artifact

---

### Story 8.2: S3 Encryption (CMK) & IAM Hardening
**SP: 13** | **Owner:** Raghuram (Team B)

**Description:** Upgrade all CDE S3 buckets to use Customer Managed Keys (CMK) for server-side encryption. Review and tighten all IAM policies to enforce least-privilege: Glue should read raw and intermediary and write egress; K8s Job should read strategy and read/write intermediary; Lambda should read strategy and invoke Glue. Remove any wildcard permissions from Sprint 1 provisioning.

**Acceptance Criteria:**
- All 4 S3 buckets encrypted with CMK (Raw, Strategy, Intermediary, Egress)
- CMK key policy grants access only to CDE service roles
- Glue IAM role: read raw + intermediary, write egress - no other S3 access
- K8s Job IAM role: read strategy + read/write intermediary only - no raw or egress access
- Lambda IAM role: read strategy, invoke Glue, publish SNS - no S3 write
- Existing pipeline still functions correctly after IAM policy tightening

**Subtasks:**
- **[2 SP] [Raghuram]** Create CMK key in KMS with key policy scoped to CDE service roles
- **[2 SP] [Raghuram]** Update CloudFormation: S3 bucket encryption from SSE-S3 to SSE-KMS with CMK ARN
- **[2 SP] [Gulfraz]** Audit Glue IAM role: remove wildcards, scope to specific bucket ARNs and actions
- **[3 SP] [Naveen]** Audit K8s Job IAM role: scope to strategy bucket (read) and intermediary bucket (read/write) only
- **[2 SP] [Shikhar]** Audit Lambda IAM role: scope to strategy bucket read + Glue invoke + SNS publish
- **[2 SP] [Suresh]** Run full pipeline E2E after IAM changes to validate no permission breakage

---

### Story 8.3: Operational Runbook
**SP: 13** | **Owner:** Uttam (Team C)

**Description:** Write a comprehensive operational runbook covering: manual pipeline re-trigger steps, failure triage decision tree (which component failed, how to identify, how to recover), rollback procedures, KEDA troubleshooting, Glue cluster sizing guidance, and escalation contacts. The runbook is the primary reference for on-call engineers.

**Acceptance Criteria:**
- Runbook covers: how to manually trigger the pipeline outside the cron schedule
- Runbook covers: failure triage flowchart (Step Functions error -> identify stage -> recovery action)
- Runbook covers: how to re-run from a specific phase (e.g., re-run only Pass 2 without repeating Pass 1 + K8s fetch)
- Runbook covers: KEDA troubleshooting (pod not spinning up, stuck jobs, DLQ messages)
- Runbook covers: Glue cluster sizing (when to increase DPU count)
- Runbook covers: escalation matrix (CDE team -> Platform team -> CTE API owners)
- Runbook reviewed by at least 2 team members

**Subtasks:**
- **[2 SP] [Uttam]** Write manual pipeline trigger procedure: Step Functions console, AWS CLI command, EventBridge test event
- **[3 SP] [Raghuram]** Write failure triage decision tree: for each Step Functions state, document failure modes and recovery steps
- **[2 SP] [Prashanth]** Write phase re-run procedures: how to skip to Pass 2, how to re-run only K8s fetch
- **[2 SP] [Naveen]** Write KEDA troubleshooting guide: check ScaledJob status, SQS queue, pod logs, DLQ
- **[2 SP] [Prashanth]** Write Glue sizing guide: DPU recommendations based on data volume, when to adjust
- **[2 SP] [Pankaj]** Write escalation matrix with Slack channels, Jira queues, and on-call contacts

---

### Story 8.4: Production Deployment & Shadow-Mode Dry Run
**SP: 15** | **Owner:** Suresh (Team A)

**Description:** Deploy the complete CDE pipeline to the production AWS account. Execute a shadow-mode dry run: the pipeline processes real CDP production data end-to-end but IFM delivery is disabled (writes to Egress S3 only). Validate output against production data characteristics. Compare record counts and filtering ratios against expectations from the architecture team.

**Acceptance Criteria:**
- All CloudFormation stacks deployed to production AWS account
- K8s Job deployed to production Kraken cluster with Vault, service mesh, and KEDA
- Pipeline executes successfully with real CDP production data
- IFM delivery is disabled (Egress S3 write only) during shadow mode
- Output record counts validated against architecture team's expected filtering ratios
- No PII or sensitive data leaks identified in output validation
- CloudWatch dashboards and alerts operational in production

**Subtasks:**
- **[3 SP] [Suresh]** Deploy CloudFormation stacks to production AWS account (S3, SFN, Lambda, Glue, SQS, SNS, EventBridge)
- **[2 SP] [Pankaj]** Deploy K8s Job to production Kraken cluster; validate Vault secrets, mesh routing, KEDA ScaledJob
- **[2 SP] [Shikhar]** Configure IFM integration in disabled/shadow mode (write to Egress S3 but don't trigger delivery)
- **[2 SP] [Prashanth]** Trigger pipeline with next CDP production export; monitor all phases in Step Functions console
- **[2 SP] [Gulfraz]** Validate output: record counts, filtering ratios, data quality spot checks
- **[2 SP] [Uttam]** Verify CloudWatch dashboards populate correctly with production metrics
- **[2 SP] [Naveen]** Verify SNS alerts fire correctly (test with intentional failure)

---

### Story 8.5: Go/No-Go Review & Production Go-Live
**SP: 7** | **Owner:** Suresh (Team A)

**Description:** Conduct formal go/no-go review with Engineering, Architecture, and Platform stakeholders. Present: shadow-mode results, security scan status, operational runbook, monitoring dashboards, and risk assessment. Upon approval, enable IFM production delivery and switch EventBridge cron to the production schedule. First real delivery to AmexGBT.

**Acceptance Criteria:**
- Go/no-go presentation delivered covering: test results, security posture, ops readiness, risk register
- All stakeholders sign off (Engineering, Architecture, Platform, AppSec)
- IFM production delivery enabled
- EventBridge cron set to production schedule (daily)
- First production pipeline execution completes and delivers data to AmexGBT
- Post-go-live monitoring active for 48 hours with team on standby

**Subtasks:**
- **[2 SP] [Suresh]** Prepare go/no-go slide deck: shadow results, scan status, runbook link, dashboard screenshots, open risks
- **[1 SP] [Nisarg]** Schedule review meeting with Engineering, Architecture, Platform, and AppSec leads
- **[1 SP] [Pankaj]** Upon approval: enable IFM production delivery configuration
- **[1 SP] [Prashanth]** Upon approval: update EventBridge cron rule to production schedule
- **[1 SP] [Gulfraz]** Monitor first production execution end-to-end; validate AmexGBT confirms receipt
- **[1 SP] [Uttam]** Maintain on-call standby for 48 hours post-go-live

---

### Story 8.6: Post-Go-Live Monitoring & Stabilization Buffer
**SP: 4** | **Owner:** Uttam (Team C)

**Description:** Reserve capacity for post-go-live bug fixes, performance tuning, and operational issues discovered in the first production runs. This is not pre-planned work - it is buffer for the unexpected.

**Acceptance Criteria:**
- Team has 4 SP of unallocated capacity for reactive work
- Any production issues discovered within the sprint are triaged and fixed
- Post-mortem documented for any production incidents

**Subtasks:**
- **[2 SP] [Uttam]** Triage and fix production bugs as they arise
- **[1 SP] [Naveen]** Tune Glue DPU count or K8s Job concurrency if production performance differs from load test
- **[1 SP] [Nisarg]** Document post-mortem for any incidents


