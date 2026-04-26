# Data Pipeline for Complete
## Objective
Provide high-level architecture for building a data pipeline for expense data to flow to AmexGBT.

## Consideration
- Expense data is just the first in priority, however, there are more use-cases to come, such as trip data. Therefore, the architecture should be generic enough to allow extending to support additional use-cases
- Focus on the data consumption and filtering, rather than on the data extraction, as filtering the data is not trivial and requires API calls to Spend and travel APIs.
- Leverage existing artifacts (frameworks, APIs, schemas, platform capabilities) to deliver the first iteration within a few months.
  - The platform team made it clear, that they will not support any change in DDS, and since DDS cannot be leveraged as-is, it will not be used.  

## Proposal
Create complete-data-exporter service (CDE), which subscribes to Core Data Platform (CDP) exports, filters data based on defined rules, and exports through IFM to AmexGBT.

## Architectural Design Document: Complete Data Exporter (CDE)
**Architecture Paradigm:** Serverless Orchestration, Ephemeral Kubernetes Workers, and Stateful Distributed Compute.

![](complete_data_exporter_architecture.png)

## 1. Executive Summary

Complete Data Exporter (CDE) ingests ORC (preferred) or JSONL payloads from CDP, enriches records through internal CTE APIs, evaluates filtering rules, and sends curated output to AmexGBT through IFM. The design separates **Orchestration**, **Network I/O**, and **Heavy Compute** to keep component responsibilities clear and reduce operational coupling.
AWS Step Functions controls workflow state. Kubernetes Jobs handle external/internal API fetches and callbacks. AWS Glue (PySpark) performs distributed filtering and joins.

## 2. Core Architectural Principles

### 2.1 Dumb Fetcher and Smart Compute
The Kubernetes Job executes API calls but does **not** evaluate business rules or large joins in pod memory. It writes **RAW API Responses** to S3. AWS Glue then loads those responses and executes `KEEP/DROP` evaluation with distributed joins. This split avoids concentrating large state in Kubernetes pods and keeps compute-heavy logic in Spark.

### 2.2 Cross-Boundary Communication (SQS and KEDA)
AWS Step Functions operates in AWS while CTE APIs are reached from an internal Kubernetes cluster. The architecture uses a **Payload vs. Signal** pattern with AWS SQS and KEDA:
* Step Functions does not communicate with Kubernetes directly. Instead, it drops a tiny "Signal" message (containing a Task Token and S3 URIs) into an **AWS SQS** queue.
* **KEDA** monitors the SQS queue. When the queue is empty, no worker pod is running.
* When a message arrives, KEDA starts a worker Job. The worker reads payload data from S3, performs API work, sends the Task Token callback to Step Functions, and exits.

### 2.3 Pre-Filtering Logic (Spark Cost & Latency Reduction)
To reduce AWS Glue compute costs and downstream API rate-limiting, CDE enforces aggressive **Tier 1 SQL Pre-Filtering** during Pass 1.
Before extracting UUIDs or performing expensive array explosions, `core_runner.py` dynamically injects Catalyst-optimized SQL filters defined in the Strategy file. 
* *Example:* `submitTimestamp >= consentDate AND companyId IS NOT NULL`.
When you apply a filter (for example, `WHERE expenseType IN ('AIRFE', 'LODGT')`), Catalyst can push that filter to the data source so Spark reads less data.

For this to be maximally effective, the file format matters:

| Format                 | What gets skipped                                                                                    |
|------------------------|------------------------------------------------------------------------------------------------------|
| ORC                    | Entire stripe/row groups are skipped using ORC statistics and indexes                                |
| Parquet                | Entire row groups are skipped using per-column min/max statistics stored in the file footer          |
| Parquet + partitioning | Entire S3 prefixes/files are skipped (Partition Pruning - a subset of predicate pushdown)            |
| JSONL (fallback format) | Nothing skipped - Spark must read every line; predicate pushdown doesn't help here                 |

For CDE Pass 1, CDP will publish ORC so Spark can apply predicate pushdown during ingestion pre-filtering. JSONL remains supported for compatibility/fallback flows but does not provide pushdown benefits.

By dropping invalid or non-consented records at the very beginning of the DAG, the pipeline reduces the size of the UUID extract file. This directly reduces the number of HTTP calls the Kubernetes Job must make, which in turn reduces the data volume AWS Glue must process during Pass 2.

### 2.4 Code-as-Configuration (Strategy Pattern)
Core infrastructure (Step Functions, Lambda, Kubernetes Job, `core_runner.py`) stays domain-agnostic. Pipeline-specific logic (expense rules, future trip rules, API targets, auth mode, schema expectations) is implemented in version-controlled Python Strategy scripts such as `expense_strategy.py`. Init Lambda reads the strategy at runtime and returns workflow config used by Step Functions, including whether API enrichment is required.

---

## 3. Architecture Zones

* **Zone 1: Core Sources & Internal APIs:** Upstream systems including CDP (Raw Data Generator) and the internal CTE backend APIs (Subscriptions, Consent, Config, and Travel/Spend mapping).
* **Zone 2: Control Plane & Execution:** AWS EventBridge provides scheduling. AWS Step Functions holds orchestration state. Init Lambda parses strategy configuration. A **Callback Lambda** bridges SNS notifications to wake the Step Function. AWS SQS carries task-token messages that trigger ephemeral Kubernetes Jobs through KEDA.
* **Zone 3: PySpark Compute Engine:** AWS Glue runs the generic `core_runner.py`, which dynamically imports the Strategy and executes Spark DataFrame operations, Tier 1 pre-filters, and Pass 2 rule evaluation.
* **Zone 4: Downstream Egress:** Curated data is written to the S3 Egress bucket, triggering the Integration File Manager (IFM) to securely route it to external partners.

---

## 4. End-to-End Data Flow

The following details the complete operational sequence:

### Phase 1: Initialization & Sync
1. **Wakes Up:** AWS EventBridge triggers the AWS Step Function via Cron.
2. **Invokes Init:** Step Function invokes the Init Lambda.
3. **Returns Workflow Rules:** Init Lambda reads the Strategy file from the Strategy S3 bucket and returns a JSON workflow payload to Step Functions (determining if Pass 2 or API phases are needed).
4. **Drops Sync Task:** Step Function drops an initialization message and Task Token into SQS.
5. **KEDA Triggers Job:** KEDA spins up the Kubernetes Job.
6. **Reads Configs:** The K8s Job downloads the Strategy file from the Strategy S3 bucket to obtain CTE API endpoints and Auth criteria.
7. **Executes Sync:** The K8s Job syncs Complete-onboarded customers and consent dates with CTE APIs.
8. **Triggers Generation:** The CTE API sync triggers CDP data extraction.
9. **Drops Raw Extract:** CDP uploads the raw export (ORC preferred as confirmed by the CDP Data Subscription API capabilities https://github.concur.com/DataPlatformFoundation/core-data-pipeline-wiki/wiki/Data-Subscription-API-Onboarding. JSONL supported as fallback.) to the Raw S3 Bucket.

### Phase 2: Ingestion & Pass 1 (Extraction)
10. **Fires Event:** S3 triggers an AWS SNS notification indicating data arrival.
11. **Notify Lambda & Wake Step Function:** The SNS event triggers a dedicated **Callback Lambda**, which in turn executes the API call to wake the suspended Step Function.
12. **Native Sync:** Step Function natively triggers AWS Glue (`core_runner.py`) for Pass 1.
13. **Reads Raw Data:** Glue loads the raw extract (ORC preferred) from S3.
14a. **Extracts UUIDs:** Glue applies aggressive **Pre-Filtering Logic** (Tier 1 SQL filters) to drop invalid rows. It extracts the surviving UUIDs and Pass 1 Parquet output, then writes them to the Intermediary S3 bucket.
14b. **Egress Contract Validation (Fail-Fast):** Before proceeding, Spark evaluates the surviving DataFrame against the `expected_egress_schema` defined in the Strategy file. If CDP has destructively altered upstream fields (e.g., renamed or dropped pass-through columns required by AmexGBT), the job immediately raises a `SchemaContractViolationError`. Step Functions catches this, routes to the DLQ, and prevents expensive/wasted API fetches in Phase 3.
15. **Fires Completion Event:** Glue publishes an SNS notification that Pass 1 is complete.
16. **Notify Lambda & Wake Step Function:** The SNS event triggers the **Callback Lambda**, which executes the API call to wake the Step Function to proceed to the next phase.

### Phase 3: Async API Enrichment (The Dumb Fetcher)
17. **Conditional Drop:** If the Strategy requires API enrichment, Step Function drops a new message and Task Token into SQS.
18. **KEDA Triggers Job:** KEDA spins up the Kubernetes Job again.
19. **Downloads Blueprints:** The K8s Job downloads the UUID JSON from the Intermediary S3 bucket and the Strategy file from the Strategy S3 bucket to get target URLs.
20. **Fetches Data:** The K8s Job concurrently executes HTTP requests against the Travel/Spend APIs.
21. **Writes RAW Responses:** The K8s Job acts as a pass-through proxy, dumping the **RAW API Responses** directly into the Intermediary S3 bucket (avoiding OOM risks).
22. **Sends Callback:** The K8s Job sends the Task Token back to Step Functions, signaling success.

### Phase 4: Pass 2 (Evaluation & Egress)
23. **Native Sync:** Step Function natively triggers AWS Glue for Pass 2.
24. **Reads RAW Responses:** Glue reads both the Phase 1 dataset and the new RAW API Responses from the Intermediary S3 bucket.
25. **Evaluates Rules & Writes Data:** `core_runner.py` hands the data to the Strategy script. The Strategy uses distributed Spark memory to evaluate the AmexGBT leakage/contamination rules, applying a broadcast join to drop unapproved records. The final data is written to the S3 Egress Bucket.
26. **Pushes Final JSONL:** The S3 Egress bucket triggers IFM.
27. **Delivers Data:** IFM securely transmits the payload to AmexGBT.

## Expense Report Filters
- Share only submitted reports, that were submitted after the customer's consent date.
- Share only reports that:
  - Contain at least one expense line of one of these travel related expense category types: ABFEE, AIRFE, AIRFR,
CARRT, LODGA, LODGN, LODGT, LODGX or RAILX.
  - There is a related booking, that was made by an AmexGBT related agency or there is no related booking, and the
expense report's user is associated with a travel config that is Complete enabled.
    - This is checked based on the user's current configuration, may differ from the time of the report submission 
  - **However**: if one of the lines of the report is related to a booking that was made by another agency, we don't share!

### Expense Report Data
As mentioned, in the first iteration, the expense report data shared with AmexGBT will be based on the existing CDP export.
<br><br><u>Sample of exported data</u>
```json
{
    "data": {
        "approvalStatus": "A_PEND",
        "auditStatus": "NOTR",
        "businessPurpose": "report purpose",
        "cashAdvanceReturnAmount": 0.0,
        "cashAdvanceUtilizedAmount": 0.0,
        "comments": [
        ],
        "companyId": "f7ca7f76-be18-4417-871e-623bef6e9809",
        "country": "US",
        "countrySubdivision": "US-WA",
        "creationTimestamp": "2022-05-18T08:04:46.523Z",
        "delegateApproved": false,
        "delegateCreated": false,
        "delegateSubmitted": false,
        "everSentBack": false,
        "exceptionApproved": true,
        "exceptionLevelMax": 0,
        "exceptionLevelTotal": 0,
        "expenses": [
            {
                "adjustedAmount": 100.0,
                "approvedAmount": 100.0,
                "attendeeCount": 0,
                "businessPurpose": "Automation-Purpose",
                "calculatedAdjustedAmount": 0.0,
                "claimedAmount": 100.0,
                "comments": [
                    {
                        "addedBy": "d91e7e7d-af7e-496c-8fe5-8c9656343c43",
                        "addedFor": "d91e7e7d-af7e-496c-8fe5-8c9656343c43",
                        "commentText": "0",
                        "creationTimestamp": "2022-05-18T08:04:50.797Z"
                    }
                ],
                "exceptionCount": 0,
                "exceptions": [
                ],
                "exchangeRate": {
                    "direction": "M",
                    "value": 1.0
                },
                "expenseType": "LUNCH",
                "foreignOrDomestic": "HOME",
                "hasEReceipt": false,
                "hasMissingReceiptAffidavit": false,
                "hasVAT": false,
                "id": "2b8df8d3-a26f-0a49-b0d1-e77dd8c321a7",
                "imageRequired": false,
                "isBillable": false,
                "isPersonal": false,
                "paymentType": "CASH",
                "postedAmount": 100.0,
                "receiptReceived": false,
                "receiptRequired": false,
                "receiptType": "N",
                "spendCategory": "MEALS",
                "taxes": [
                ],
                "totalReclaimAdjustedAmount": 0.0,
                "totalReclaimPostedAmount": 0.0,
                "totalTaxAdjustedAmount": 0.0,
                "totalTaxPostedAmount": 0.0,
                "transactionAmount": 100.0,
                "transactionCurrencyCode": "USD",
                "transactionDate": "2022-05-18T00:00:00Z",
                "transactionType": "REG"
            }
        ],
        "firstSubmitTimestamp": "2022-05-18T08:04:54.04Z",
        "hasReceipts": false,
        "hasReceivedCashAdvanceReturn": false,
        "hasReceivedPaperReceipts": false,
        "isFinancialIntegrationEnabled": false,
        "isReceiptImageAvailable": false,
        "isReceiptImageRequired": false,
        "isReceiptRequired": false,
        "isReopened": false,
        "ledgerCode": "DEFAULT",
        "limitApproved": false,
        "paymentStatus": "P_NOTP",
        "reimbursementCurrency": "USD",
        "rejectionReasonCodes": [
        ],
        "reportDate": "2022-05-18",
        "reportId": "2882F506C1CE4055BEC6",
        "reportingGroup": {
            "name": "Global"
        },
        "reportName": "EDLS Test Entity Setup Report",
        "reportNumber": "OS7WG2",
        "reportOwner": "d91e7e7d-af7e-496c-8fe5-8c9656343c43",
        "revisionTimestamp": "2022-05-18T08:04:54.59Z",
        "startDate": "2022-05-18",
        "submitTimestamp": "2022-05-18T08:04:54.04Z",
        "totalAmountDueCompanyCard": 0.0,
        "totalApprovedAmount": 100.0,
        "totalClaimedAmount": 100.0,
        "totalPaymentConfirmedAmount": 0.0,
        "totalPersonalAmount": 0.0,
        "totalPostedAmount": 100.0,
        "workflowSteps": [
            {
                "actionTimeStamp": "2022-05-18T08:04:54.337Z",
                "entryTimeStamp": "2022-05-18T08:04:53.957Z",
                "finalStatus": "A_FILE",
                "name": "Report Submitted",
                "roleCode": "SYSTEM",
                "sequenceNumber": 1,
                "stepId": "f00cfa0e-2ad7-0341-bef5-7984844b6588"
            },
            {
                "actor": "b81d34f5-a588-4218-a467-52053abf5ec1",
                "entryTimeStamp": "2022-05-18T08:04:54.337Z",
                "name": "Manager Approval",
                "roleCode": "MANAGER",
                "sequenceNumber": 2,
                "stepId": "963ab73b-7536-1547-af15-90f42e328d61"
            },
            {
                "name": "Approval for Processing",
                "roleCode": "ACCT_CLERK",
                "sequenceNumber": 3,
                "stepId": "c4f53eb2-00f5-6546-a99f-0a228f99ab08"
            },
            {
                "name": "Prepayment Validation",
                "roleCode": "SYSTEM",
                "sequenceNumber": 4,
                "stepId": "c066674a-1ce8-cf43-a1aa-dbc390ae46ff"
            },
            {
                "name": "Processing Payment",
                "roleCode": "SYSTEM",
                "sequenceNumber": 5,
                "stepId": "a66e3bc7-139a-d14f-b6f4-3053072ee79e"
            }
        ]
    },
    "datacontenttype": "application/json",
    "id": "db2fb231-86b2-4936-9a52-3df07bed83be",
    "sequence": "001652861094590",
    "source": "/us2/concur/f7ca7f76-be18-4417-871e-623bef6e9809",
    "specversion": "1.0",
    "subject": "f7ca7f76-be18-4417-871e-623bef6e9809.2882F506C1CE4055BEC6",
    "time": "2022-05-18T08:04:54.59Z",
    "type": "sap.concur.ExpenseReports.Upserted.v1"
}
```

### Additional Technical Details
- Runtime components and language:
    - Init Lambda: Python
    - AWS Glue jobs (`core_runner.py` + strategy modules): PySpark/Python
    - Kubernetes worker Job (Dumb Fetcher): Python
- Orchestration and eventing:
    - EventBridge for schedule-based trigger
    - Step Functions for workflow orchestration and conditional branching
    - SNS for data-arrival and completion notifications
    - SQS + task-token callback pattern for Step Functions to Kubernetes handoff
- S3 Bucket Organization & Data Retention:
    - **Strategy bucket:** Strategy files follow semantic versioning (e.g., `s3://cde-strategies/expense/v1.0.0/expense_strategy.py`). Each deployment creates a new immutable version. EventBridge triggers pass the *pinned* strategy version to the Init Lambda to avoid mid-execution version mismatches.
    - **Intermediary bucket:** Execution-specific working data. Retention follows a tiered lifecycle: Pass 1 Parquet (90 days for debugging), Raw API Responses (90 days due to fetch cost/compliance), and UUID extracts (30 days, easily regenerated).
    - **Raw bucket:** Inbound CDP exports.
    - **Egress bucket:** Final JSONL output for IFM delivery.
- Data formats and storage:
    - CDP raw input: ORC preferred as confirmed by the CDP Data Subscription API capabilities (https://github.concur.com/DataPlatformFoundation/core-data-pipeline-wiki/wiki/Data-Subscription-API-Onboarding). JSONL supported as fallback.
    - Pass 1 output for downstream compute: Parquet in Intermediary S3
    - API enrichment output: RAW JSON responses in Intermediary S3
    - Final output for IFM handoff: JSONL in Egress S3
- Kubernetes platform practices:
    - Run worker as ephemeral Job in Kraken Kubernetes
    - Use KEDA ScaledJob for SQS-driven scale from zero
    - Implement worker idempotency: The job checks the Intermediary S3 bucket (via ETags or object existence) for previous partial writes before initiating rate-limited, expensive CTE API fetches.
    - Use Vault for secrets and token/certificate retrieval
    - Use service mesh controls for internal traffic policy where required
- Reliability and operations:
    - Retry and Catch policies on Step Functions task states
    - DLQ for failed async message processing
    - Structured JSON logging with correlation_id propagation across Lambda, Kubernetes, and Glue
    - Detailed observability contracts (logging fields, metrics taxonomy, health signals, and alerting) are defined in [cde_observability_layer_implementation.md](cde_observability_layer_implementation.md)
    - Strict IAM Boundary Model & Least Privilege:
    
| Component | S3 Bucket Access | Other Permissions & Network |
| :--- | :--- | :--- |
| **Init Lambda** | Strategy (Read) | None |
| **Glue Pass 1** | Raw (Read), Strategy (Read), Intermediary (Write) | SNS Publish. *No direct internet access (VPC endpoints only).* |
| **Glue Pass 2** | Intermediary (Read), Egress (Write) | *No direct internet access.* |
| **K8s Job** | Intermediary (Read/Write), Strategy (Read) | Secrets Manager (CTE creds). |
| **Step Functions** | None | Native integrations (Lambda Invoke, Glue StartJobRun, SQS SendMessage). |

- Delivery engineering:
    - Deploy infrastructure and jobs through CloudFormation and standard release pipeline (RPL)
- Disaster Recovery (DR) & Data Loss Strategy:
    - **RPO (Recovery Point Objective):** 24 hours. (Can reprocess the previous day's daily CDP batch export).
    - **RTO (Recovery Time Objective):** 4 hours. (Targeted to deliver before AmexGBT's consumption window closes).
    - **Failure Responses:** Glue schema violations route to DLQ for manual runbook triggers; AWS region failures accept the 24hr RTO as Step Functions lacks cross-region failover; Corrupted deliveries require manual IFM recall procedures.

## Parking Lot
- KMS CMK scope and key policy finalization
- OTD and GDPR review outcomes and implementation tasks
- Runbook ownership and on-call handoff checklist

## References
- Aha: https://sapconcur.aha.io/epics/CASTLE-E-23
- Jira: https://jira.concur.com//browse/CASTLE-950
- Implementation options ADR: https://github.concur.com/jads/architecture/blob/egencia-dataleak/expense/gbt-egencia-integration/ADR-002-leakage-detection-interface.md
- Expense report filtering logic ADR: https://github.concur.com/jads/architecture/blob/egencia-dataleak/expense/gbt-egencia-integration/ADR-001-leakage-detection-divisional-view.md
- CDE Observability Layer Implementation: [cde_observability_layer_implementation.md](cde_observability_layer_implementation.md)