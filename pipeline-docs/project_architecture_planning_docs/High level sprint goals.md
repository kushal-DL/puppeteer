# CDE v3.0 — High-Level Sprint Goals

**Team:** 9 developers | **Capacity:** ~70 SP/sprint | **Sprint cadence:** 2 weeks
**Go-live target:** July 7, 2026 (Tuesday, end of Sprint 8)

---

## Sprint 1 — Foundation & Infrastructure Setup *(In Progress)*
**Mar 18 – Mar 31**

Establish all foundational infrastructure: AWS resource provisioning via CloudFormation, K8s hello-world service on Kraken (Vault, service mesh, RPL), API contract discovery, logging/observability documentation, and IFM onboarding.

---

## Sprint 2 — Core Pipeline Skeleton & Strategy Pattern
**Apr 1 – Apr 14**

Build the Step Functions state machine skeleton (EventBridge → Init Lambda → Glue trigger). Implement `core_runner.py` with S3 I/O and Strategy class loading. Create `expense_strategy.py` stub. First green-path execution end-to-end with dummy data.

---

## Sprint 3 — Pass 1: CDP Ingestion, Pre-Filtering & UUID Extraction
**Apr 15 – Apr 28**

Implement CDP JSONL ingestion in Glue. Build Tier 1 SQL pre-filters in `expense_strategy.py` (consent cutoff, travel category filter, deduplication). Extract surviving UUIDs to Config S3. Wire SNS data-arrival notification to wake Step Functions. Hydrate consent mapping via K8s Job → Config API → S3.

---

## Sprint 4 — K8s Dumb Fetcher, SQS/KEDA Cross-Boundary & API Enrichment
**Apr 29 – May 12**

Implement SQS Task Token pattern. Build K8s Dumb Fetcher: pull UUIDs from S3, call Travel/Spend APIs concurrently, stream raw responses to S3, send Task Token callback. Configure KEDA ScaledJob. Implement JWT/cert auth for CTE API calls.

---

## Sprint 5 — Pass 2: Rule Evaluation, Broadcast Join & Filtered Egress
**May 13 – May 26**

Implement Glue Pass 2: load raw API responses, broadcast join against Phase 1 dataset. Build Phase 2 business rules in `expense_strategy.py` (TMC agency check, competitor guardrail, Complete-enabled config). Write filtered JSONL to Egress S3. Implement conditional phase-skipping via Init Lambda.

---

## Sprint 6 — IFM Integration, E2E Pipeline & Data Validation
**May 27 – Jun 9**

Integrate Egress S3 with IFM for secure AmexGBT delivery. Build data validation suite against known-good test fixtures. Full E2E smoke test. Verify pipeline idempotency. Begin error-path testing.

---

## Sprint 7 — Observability, Error Handling & Hardening
**Jun 10 – Jun 23**

Implement `dv2`-compliant structured logging across all components. Add `correlation_id` propagation. Build CloudWatch dashboards and SNS alerting. Implement Step Functions retry/catch blocks. Add circuit breaker and backoff to K8s Job. Load test with production-scale data.

---

## Sprint 8 — Production Readiness, Security & Go-Live
**Jun 24 – Jul 7**

AppSec scans (SAST, DAST, dependency audit). CMK encryption for S3. Operational runbook. Deploy to production. Shadow-mode dry-run with real CDP data. Go/no-go review. Enable IFM production delivery. **Go-live.**

---

## Timeline

```
Sprint 1  Mar 18 – Mar 31  Foundation & Infra
Sprint 2  Apr  1 – Apr 14  Pipeline Skeleton & Strategy
Sprint 3  Apr 15 – Apr 28  Pass 1 (Ingestion & Pre-filter)
Sprint 4  Apr 29 – May 12  K8s Fetcher & KEDA
Sprint 5  May 13 – May 26  Pass 2 (Rules & Egress)
Sprint 6  May 27 – Jun  9  IFM Integration & E2E
Sprint 7  Jun 10 – Jun 23  Observability & Hardening
Sprint 8  Jun 24 – Jul  7  Prod Readiness & Go-Live ✅
```


