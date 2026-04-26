# CDP Data Subscription API – Reference

> **Status:** Confirmed (sourced from wiki + OpenAPI spec)
> **Last updated:** 2026-03-19
> **Owner / upstream contact:** DataPlatform team — Slack `#ask-dataplatform`
> **Product Manager:** Denis Polyakov
> **Dev Manager (Egress / DSub API):** Prakash Vaidyanathan
> **OpenAPI spec:** [dataSubscription.yaml](https://github.concur.com/DataPlatformFoundation/schema/blob/master/Egress/dataSubscription.yaml)
> **JIRA board:** [RavenClaw Board](https://jira.concur.com/secure/RapidBoard.jspa?rapidView=3555)

---

## Table of Contents

1. [Purpose](#1-purpose)
2. [Base URL](#2-base-url)
3. [Authentication](#3-authentication)
4. [Required Headers](#4-required-headers)
5. [Endpoints](#5-endpoints)
   - [Create Subscription](#51-create-subscription)
   - [Get Subscription Info](#52-get-subscription-info)
   - [List Subscriptions by S3 Bucket](#53-list-subscriptions-by-s3-bucket)
   - [List Approved Subscribers](#54-list-approved-subscribers)
   - [On-Demand Backfill](#55-on-demand-backfill)
   - [Remove Filter Values](#56-remove-filter-values)
   - [Terminate Subscription](#57-terminate-subscription)
6. [DSL Query – Data Shape Definition](#6-dsl-query--data-shape-definition)
7. [Output Data Structure](#7-output-data-structure)
8. [SNS Notifications](#8-sns-notifications)
9. [Batch Group Configuration](#9-batch-group-configuration)
10. [Error Payloads](#10-error-payloads)
11. [Design Considerations](#11-design-considerations)
12. [Client Integration Notes](#12-client-integration-notes)
13. [Open Clarifications](#13-open-clarifications)

---

## 1. Purpose

The **CDP Data Subscription API** is an SAP Concur-internal provisioning API that allows *Data Consumers* to configure scheduled, incremental data delivery from the Core Data Pipeline (CDP) Datalake to a consumer-owned AWS S3 bucket.

Key capabilities:

- Subscribe to any data shape (table + column projection) in the CDP Datalake
- Receive scheduled incremental deliveries (new/updated/deleted records since last delivery)
- First delivery includes full historical data (unless a `startWatermark` is set)
- Filter deliveries to specific company UUIDs (batch subscriptions)
- Receive job status updates via AWS SNS
- Trigger on-demand backfills for a specific time window

> **This is a provisioning API only** — it does not return business data directly. All data is delivered asynchronously to the subscriber's S3 bucket.

---

## 2. Base URL

| Environment | Region | Base URL |
|-------------|--------|----------|
| Integration | us-west-2 | `https://subscription-integration.service.cnqr.tech` |
| US2 (Production) | us-west-2 | `https://subscription.service.cnqr.tech` |
| EU2 (Production) | eu-central-1 | `https://subscription.service.cnqr.tech` |
| APJ1 (Production) | ap-northeast-1 | ----------------------------------------|
| CCPS (Production) | us-gov-west-1 | --------------------------------------- |

> **Note:** US2 and EU2 share the same production base URL. Routing to the correct region is handled transparently by the service.

> **Note:** All endpoints are relative to the base URL above. Set `CDP_SUBSCRIPTION_API_BASE_URL` as an environment variable per deployment target.

---

## 3. Authentication

| Property | Value |
|----------|-------|
| Mechanism | **mTLS (mutual TLS) — certificate-based** |
| How it works | The caller's service certificate Common Name (CN) must be pre-approved by the CDP team |
| Onboarding | Raise a JIRA Story in project [DPF](https://jira.concur.com/projects/DPF), Epic [DPF-5059](https://jira.concur.com/browse/DPF-5059), Components: `AWS Egress Requests, egress` |
| Turnaround | 1–3 business days |
| Certificate propagation | **`concur-forwarded-for`** is injected automatically by **ServiceMesh** from the client certificate CN. **Callers must not set this header.** |
| Token / secret | None — no Bearer token or API key is used |
| Contact email | `BigDataPlatformRD@concur.com` |

> **No OAuth token is required.** Authentication is enforced at the infrastructure/mTLS layer. ServiceMesh extracts the client certificate's Common Name and injects it as `concur-forwarded-for`. If the CN is not in CDP's allowlist, all requests return `403 Forbidden`.

---

## 4. Required Headers

| Header | Type | Required | Description |
|--------|------|----------|-------------|
| `Content-Type` | string | Yes (POST/PUT/PATCH) | Must be `application/json` |
| `dsl-version` | string | **Yes** | Semantic version of the DSL used to author the `dsl-query` (e.g. `1.0.0`) |
| `concur-correlationid` | string (UUID v4) | Recommended | RFC 4122 UUID for end-to-end tracking and troubleshooting. Include on every request. |
| `request-id-alias` | string | No | Human-readable alias for the subscription (e.g. `expense-daily-extract`) |
| `output-bucket-format` | string | No | Output file format for the S3 delivery: `orc` (default) or `json` |
| `concur-forwarded-for` | string | **ServiceMesh only** | Common Name of the client certificate. **Never set by the caller** — injected by ServiceMesh. Required internally for authorization; used on `GET /subscribers` to filter results by caller identity. |

---

## 5. Endpoints

### Endpoint Summary

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/datasubscription/v2/schedule` | Create a new subscription |
| `GET` | `/datasubscription/v2/groups/{group-id}/requests/{request-id}` | Get subscription details |
| `GET` | `/datasubscription/v2/list/s3bucketpaths` | List subscriptions by S3 bucket path |
| `GET` | `/datasubscription/v2/subscribers` | List approved subscriber (group) names |
| `PUT` | `/datasubscription/v2/groups/{group-id}/requests/{request-id}/filters` | On-demand backfill |
| `PATCH` | `/datasubscription/v2/groups/{group-id}/requests/{request-id}/filters` | Remove filter values |
| `DELETE` | `/datasubscription/v2/terminate/groups/{group-id}/requests/{request-id}` | Terminate subscription |
| `PUT` | `/datasubscription/v2/groups/{group-id}` | Update group schedule / format *(Not yet implemented — use Slack)* |

---

### 5.1 Create Subscription

```
POST /datasubscription/v2/schedule
```

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `output-bucket-format` | string | No | `orc` | Output file format: `orc` or `json` |
| `run-initial-now` | boolean | No | `false` | Trigger the first delivery immediately after creation |

#### Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dsl-query` | string | **Yes** | GraphQL query defining the data shape (one table per subscription) |
| `s3-bucket-arn` | string | **Yes** | ARN or path of the target S3 bucket (e.g. `s3://bucket-name/prefix`) |
| `schedule` | string | No | Quartz cron expression for recurring delivery. Omit with `run-initial-now=true` for one-shot delivery |
| `notification-topic-arn` | string | No | ARN of an AWS SNS topic to receive job status notifications |
| `startWatermark` | string (RFC 3339) | No | Left-bound timestamp. Defaults to `1970-01-01T00:00:00Z` (full history) |
| `group.name` | string | No | CDP-approved subscriber group name (see [Section 9](#9-batch-group-configuration)) |
| `group.filter.column` | string | No | Column to apply the company filter on. Must be present in `dsl-query` |
| `group.filter.values` | string[] | No | Initial set of company UUID values to filter on |

#### Request Example

```bash
curl -X POST 'https://subscription-integration.service.cnqr.tech/datasubscription/v2/schedule?run-initial-now=true&output-bucket-format=orc' \
  -H 'Content-Type: application/json' \
  -H 'dsl-version: 1.0.0' \
  -H 'concur-correlationid: 550e8400-e29b-41d4-a716-446655440000' \
  -H 'request-id-alias: expense-daily-extract' \
  -d '{
    "dsl-query": "query { tables { ... on spend_user { companyId, id, firstName, lastName, email }}}",
    "s3-bucket-arn": "s3://my-team-bucket/data-subscription",
    "schedule": "0 0 2 ? * *",
    "notification-topic-arn": "arn:aws:sns:us-west-2:123456789012:egress-notifications",
    "startWatermark": "2024-01-01T00:00:00Z",
    "group": {
      "name": "DS",
      "filter": {
        "column": "companyId",
        "values": [
          "6689dd23-861e-4da1-9305-ba05ad96675a",
          "7789ee34-962f-5eb2-a406-cb06be07786b"
        ]
      }
    }
  }'
```

#### Response (202 Accepted)

```json
{
  "group-id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "jobs": [
    {
      "request-id": "11111111-2222-3333-4444-555555555555",
      "expected-start-time": "2024-01-15T02:00:00Z",
      "filter-values": [
        "6689dd23-861e-4da1-9305-ba05ad96675a",
        "7789ee34-962f-5eb2-a406-cb06be07786b"
      ]
    }
  ]
}
```

| Response Field | Type | Description |
|----------------|------|-------------|
| `group-id` | string (UUID v3) | Groups jobs for batching and backfilling. **Deterministic** — derived as a UUID Type 3 (MD5 hash) of: `group_name` + ordered DSL parse result + `s3_bucket_arn` + `request_id_alias` + `filter-column`. Same inputs always produce the same `group-id`. Use for all subsequent calls. |
| `jobs` | array | List of scheduled delivery jobs |
| `jobs[].request-id` | string (UUID v4) | Unique identifier for each delivery job |
| `jobs[].expected-start-time` | string (ISO 8601) | When the delivery job is expected to start (±5 minutes) |
| `jobs[].filter-values` | string[] | Filter values assigned to this job |

---

### 5.2 Get Subscription Info

```
GET /datasubscription/v2/groups/{group-id}/requests/{request-id}
```

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group-id` | string (UUID) | Yes | Group ID returned at subscription creation |
| `request-id` | string (UUID) | Yes | Request ID returned at subscription creation |

#### Request Example

```bash
curl -X GET \
  'https://subscription-integration.service.cnqr.tech/datasubscription/v2/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/requests/11111111-2222-3333-4444-555555555555' \
  -H 'concur-correlationid: 550e8400-e29b-41d4-a716-446655440001'
```

#### Response (200 OK)

```json
{
  "expected-start-time": "2024-01-15T02:00:00Z",
  "schedule": "0 0 2 ? * *",
  "request-id-alias": "expense-daily-extract",
  "group-name": "DS",
  "filter-column": "companyId",
  "filter-values": [
    "6689dd23-861e-4da1-9305-ba05ad96675a",
    "7789ee34-962f-5eb2-a406-cb06be07786b"
  ]
}
```

---

### 5.3 List Subscriptions by S3 Bucket

```
GET /datasubscription/v2/list/s3bucketpaths?s3-bucket-path={path}
```

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `s3-bucket-path` | string | Yes | S3 bucket path used when the subscription was created (e.g. `s3://my-team-bucket/data-subscription`) |

#### Request Example

```bash
curl -X GET \
  'https://subscription-integration.service.cnqr.tech/datasubscription/v2/list/s3bucketpaths?s3-bucket-path=s3://my-team-bucket/data-subscription' \
  -H 'concur-correlationid: 550e8400-e29b-41d4-a716-446655440002'
```

#### Response (200 OK)

```json
[
  {
    "request-id": "11111111-2222-3333-4444-555555555555",
    "s3-bucket-path": "s3://my-team-bucket/data-subscription",
    "dsl-query": "query { tables { ... on spend_user { companyId, id, firstName, lastName, email }}}",
    "dsl-version": "1.0.0",
    "output-bucket-format": "orc",
    "schedule": "0 0 2 ? * *",
    "next-fire-time": "2024-01-15T02:00:00Z",
    "request-id-alias": "expense-daily-extract",
    "notification-topic-arn": "arn:aws:sns:us-west-2:123456789012:egress-notifications"
  }
]
```

---

### 5.4 List Approved Subscribers

```
GET /datasubscription/v2/subscribers
```

Returns the list of CDP-approved group names the caller is permitted to use. Results are **filtered by the caller's certificate CN** — only names authorised for that CN are returned. Use this to verify your group name before creating a subscription.

#### Response (200 OK)

```json
{
  "names": ["SMB", "DS", "BI", "IFM", "SCT", "BDC"]
}
```

---

### 5.5 On-Demand Backfill

```
PUT /datasubscription/v2/groups/{group-id}/requests/{request-id}/filters
```

Triggers an immediate data extraction for specific filter values within a defined watermark range. Use this to re-deliver or backfill data for a past time window.

#### Request Body

```json
{
  "filter-values": ["6689dd23-861e-4da1-9305-ba05ad96675a"],
  "startWatermark": "2023-01-01T00:00:00Z",
  "endWatermark": "2023-12-31T23:59:59Z"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filter-values` | string[] | **Yes** | Company UUIDs to backfill. Values are case-sensitive. |
| `startWatermark` | string (RFC 3339) | No | Left-bound of the backfill window. Defaults to `1970-01-01T00:00:00Z`. Must be earlier than current time and earlier than `endWatermark`. |
| `endWatermark` | string (RFC 3339) | No | Right-bound of the backfill window. Defaults to the current time when the job executes. Must be earlier than current time and greater than `startWatermark`. |

#### Response (202 Accepted)

```json
{
  "expected-start-time": "2024-01-14T15:30:00Z"
}
```

---

### 5.6 Remove Filter Values

```
PATCH /datasubscription/v2/groups/{group-id}/requests/{request-id}/filters
```

Removes specific company UUID values from an existing subscription's filter list.

> **Warning:** If all filter values are removed, the subscription is automatically terminated and `request-deleted` is set to `true`.

> **Note:** If the provided filter values do not exist on the subscription, a `200` is returned without error (silent no-op). If the subscription itself is not found, a `410 Gone` is returned.

#### Request Body

```json
{
  "filter-values": ["7789ee34-962f-5eb2-a406-cb06be07786b"]
}
```

#### Response (200 OK)

```json
{
  "request-deleted": false
}
```

| Field | Type | Description |
|-------|------|-------------|
| `request-deleted` | boolean | `true` if removal caused the subscription to be terminated (all values removed) |

---

### 5.7 Terminate Subscription

```
DELETE /datasubscription/v2/terminate/groups/{group-id}/requests/{request-id}
```

Permanently terminates the subscription and stops all scheduled deliveries.

#### Request Example

```bash
curl -X DELETE \
  'https://subscription-integration.service.cnqr.tech/datasubscription/v2/terminate/groups/a1b2c3d4-e5f6-7890-abcd-ef1234567890/requests/11111111-2222-3333-4444-555555555555' \
  -H 'concur-correlationid: 550e8400-e29b-41d4-a716-446655440005'
```

#### Response: `204 No Content`

---

### 5.8 Update Group Schedule *(Not Implemented)*

```
PUT /datasubscription/v2/groups/{group-id}
```

Updates schedule or output settings for **all request-ids** belonging to the given `group-id`. This endpoint is defined in the OpenAPI spec but is **not yet implemented**. Use Slack `#ask-dataplatform` to request schedule changes in the interim.

#### Request Body

```json
{
  "schedule": "0 0 4 ? * *",
  "notification-topic-arn": "arn:aws:sns:us-west-2:123456789012:egress-notifications",
  "output-bucket-format": "orc"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schedule` | string (Quartz cron) | No | New delivery schedule for all jobs in the group |
| `notification-topic-arn` | string | No | New SNS topic ARN for notifications |
| `output-bucket-format` | string | No | New output format: `orc` or `json` |

#### Response: `200 OK` (no body)

---

## 6. DSL Query – Data Shape Definition

The `dsl-query` field uses GraphQL syntax to define which table and columns to subscribe to.

### Rules

- **One table per subscription** — each subscription must target exactly one table
- **Column names are case-sensitive and must be lowercase**
- **Only top-level JSON attributes** are supported (no nested field traversal)
- **Equality filters** can be applied inline within the query

### Projection Example (select specific columns)

```graphql
query {
  tables {
    ... on spend_user {
      companyId
      id
      firstName
      lastName
      email
    }
  }
}
```

### Equality Filter Example

```graphql
query {
  tables {
    ... on bike_share_trips {
      trip_id(equals: "12345")
      passholder_type(equals: "Monthly Pass")
      finished(equals: "true")
    }
  }
}
```

> **Note:** All equality filter values must be wrapped in quotes as strings, regardless of the actual data type.

Equivalent SQL:

```sql
SELECT trip_id, passholder_type, finished
FROM bike_share_trips
WHERE trip_id = 12345
  AND passholder_type = 'Monthly Pass'
  AND finished = true
```

---

## 7. Output Data Structure

### File Formats

| Format | Description |
|--------|-------------|
| `orc` | Apache ORC (default) — columnar, compressed, efficient for analytics |
| `json` | JSON Lines — one record per line |

### S3 Folder Structure

Each subscription delivery writes to three sub-folders under the subscription's folder:

```
s3://<your-bucket>/<your-prefix>/
  <request-id>/
    upserts/
      <epoch-timestamp>/
        part-00000.orc      ← new and updated records
    deletes/
      <epoch-timestamp>/
        part-00000.orc      ← deleted records
    classifications/
      <epoch-timestamp>/
        classifications.json ← data privacy classification for all fields
```

**Example paths** (request-id `2c3030df`, first delivery at epoch `0000001643907955683`):

```
s3://dp_bucket/dp_prefix/2c3030df-4017-48ca-afc7-7415806559d8/upserts/0000001643907955683/part-00000.orc
s3://dp_bucket/dp_prefix/2c3030df-4017-48ca-afc7-7415806559d8/deletes/0000001643907955683/part-00000.orc
s3://dp_bucket/dp_prefix/2c3030df-4017-48ca-afc7-7415806559d8/classifications/0000001643907955683/classifications.json
```

### CDP-Added System Columns

CDP injects the following columns into every delivered record:

| Column | Source | Type | Description |
|--------|--------|------|-------------|
| `dp_unique_key` | egress | string | Surrogate key — concatenation of PK values with `_` separator; `dp-null-value` used for nulls |
| `dp_unique_key_columns` | egress | string | Comma-delimited list of column names forming the unique key |
| `dp_last_modified_timestamp` | egress | timestamp | UTC timestamp when CDP first saw this record's modification |
| `dl_company_id` | db | string | Company UUID mapped from `entity_code` via Core Profile API |
| `dl_entity_code` | db | string | Expense entity code from `CT_HOST.ENTITY_CODE` |
| `dl_env_type` | db | string | Environment type from `CT_HOST.ENV_TYPE` |
| `dl_produced_timestamp` | db | long (epoch) | Timestamp of transactional DB data pull |
| `dl_src_last_modified_timestamp` | db / egress | timestamp | Timestamp of last record modification in source DB. **Used for high-water mark tracking.** |
| `dl_is_deleted` | db / object | boolean | `true` if the record is soft-deleted and will appear in the `deletes/` folder |
| `dl_primary_key` | db / object | string | Comma-delimited PK column names |
| `dl_src_env` | db | integer | Numeric source environment code (see table below) |
| `dl_version` | db | long | `dl_src_last_modified_timestamp` or `dl_produced_timestamp`, whichever is non-null |

**`dl_src_env` values:**

| Value | Environment |
|-------|-------------|
| 1001 | US1 |
| 1002 | EU1 |
| 2000 | Integration |
| 2001 | US2 |
| 2002 | EU2 |

> **Warning:** `dl_` columns are informational and may change without notice. Only `dp_` columns are part of the stable egress contract.

---

## 8. SNS Notifications

Configure an SNS topic to receive job status updates for each delivery.

### Setup

1. Create an SNS topic in your AWS account
2. Register the topic ARN in the [egress-notification-permissions](https://github.concur.com/DataPlatformFoundation/egress-notification-permissions) repository (PR required)
3. Provide the topic ARN in `notification-topic-arn` when creating the subscription
4. Subscribe your consumer (SQS, Lambda, HTTP endpoint) to the topic

### SNS Message Envelope

The raw SNS message looks like:

```json
{
  "Type": "Notification",
  "MessageId": "82914116-5bc2-5119-b90b-167781a4f68b",
  "TopicArn": "arn:aws:sns:us-west-2:243458229906:egress-notification-test",
  "Message": "eyJncm91cC1pZCI6Ii4uLiJ9",
  "Timestamp": "2020-06-15T20:20:54.389Z",
  "SignatureVersion": "1",
  "Signature": "<aws-signature>",
  "SigningCertURL": "https://sns.us-west-2.amazonaws.com/SimpleNotificationService-xxx.pem",
  "UnsubscribeURL": "https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&..."
}
```

> **Important:** The `Message` field is **Base64-encoded**. Decode it before parsing.

### Decoded Notification Payload

```json
{
  "group-id": "b44abc26-72f5-43fe-8986-8fc5a07f81f1",
  "request-id": "3342a711-bdab-48f3-8c1d-85ab9196c34b",
  "request-id-alias": "expense",
  "job-status": "SUCCESS",
  "extra-data": {
    "start-watermark": "1970-01-01T00:00:00Z",
    "end-watermark": "2020-06-20T20:02:07.191Z",
    "upsert-row-count": 100,
    "delete-row-count": 50,
    "s3-path-upsert": "s3://datalake-core-test/outtask_user/3342a711-.../upserts/0000001643907955683/",
    "s3-path-delete": "s3://datalake-core-test/outtask_user/3342a711-.../deletes/0000001643907955683/",
    "s3-path-classification": "s3://datalake-core-test/outtask_user/3342a711-.../classifications/0000001643907955683/"
  }
}
```

### `job-status` Values

| Status | Path | Description |
|--------|------|-------------|
| `STARTING` | Happy path 1 | Pre-flight check started |
| `DSLQUERY VALID` | Happy path 2 | DSL query validated successfully |
| `DSLQUERY INVALID` | Error | DSL query failed validation |
| `REQUEST AUTHORIZED` | Happy path 3 | S3 bucket access confirmed |
| `REQUEST UNAUTHORIZED` | Error | S3 bucket access denied |
| `SUBMITTED` | Happy path 4 | Delivery job submitted to EMR |
| `RUNNING` | Happy path 5 | Delivery job running |
| `SUCCESS` | Happy path 6 | Delivery completed; `extra-data` contains S3 paths and row counts |
| `FAILED` | Error | EMR job failure |
| `REQUEST DELETED` | Terminal | Subscription was terminated by subscriber |

**Job status flow (success):**
```
STARTING → DSLQUERY VALID → REQUEST AUTHORIZED → SUBMITTED → RUNNING → SUCCESS
```

### `extra-data` Fields (on `SUCCESS`)

| Field | Type | Description |
|-------|------|-------------|
| `start-watermark` | string (RFC 3339) | Left-bound (exclusive) of the delivered data window |
| `end-watermark` | string (RFC 3339) | Right-bound (inclusive) of the delivered data window |
| `upsert-row-count` | integer | Number of upsert records delivered |
| `delete-row-count` | integer | Number of delete records delivered |
| `s3-path-upsert` | string | S3 prefix for upsert files (present if `upsert-row-count > 0`) |
| `s3-path-delete` | string | S3 prefix for delete files (present if `delete-row-count > 0`) |
| `s3-path-classification` | string | S3 prefix for the classifications file |

### Decoding Notifications

**Python:**

```python
import base64
import json

def decode_cdp_notification(sns_message: dict) -> dict:
    """Decode a base64-encoded CDP SNS notification."""
    encoded = sns_message["Message"]
    return json.loads(base64.b64decode(encoded))

# Usage
notification = decode_cdp_notification(raw_sns_message)
status = notification["job-status"]
if status == "SUCCESS":
    extra = notification.get("extra-data", {})
    upsert_path = extra.get("s3-path-upsert")
    upsert_count = extra.get("upsert-row-count", 0)
```

**Node.js:**

```js
function decodeCdpNotification(snsMessage) {
  const decoded = Buffer.from(snsMessage.Message, 'base64').toString('utf-8');
  return JSON.parse(decoded);
}

// Usage
const notification = decodeCdpNotification(rawSnsMessage);
if (notification['job-status'] === 'SUCCESS') {
  const upsertPath = notification['extra-data']?.['s3-path-upsert'];
}
```

---

## 9. Batch Group Configuration

### Approved Group Names

| Group Name | Description |
|------------|-------------|
| `SMB` | Small Business |
| `DS` | Data Services |
| `BI` | Business Intelligence |
| `IFM` | Integration & Financial Management |
| `SCT` | SAP Concur Travel |
| `BDC` | Business Data Cloud |

> To register a new group name, contact the DataPlatform team via `#ask-dataplatform`.

### Filter Value Limits

| Environment | Max `filter-values` per subscription |
|-------------|--------------------------------------|
| US2, EU2, APJ1 | 1,000 |
| USPSCC, CCPS | 1 |

> **CMK/CSK environments (`integration-dev`, `uspscc`):** Exactly **1** company UUID per subscription is required. Multiple UUIDs will cause the job to fail with `EgressSpecException`.

### Schedule Format

Uses [Quartz cron expressions](http://www.quartz-scheduler.org/documentation/quartz-2.3.0/tutorials/crontrigger.html) (6 fields):

```
┌──── second (0-59)
│ ┌──── minute (0-59)
│ │ ┌──── hour (0-23)
│ │ │ ┌──── day-of-month (1-31 or ?)
│ │ │ │ ┌──── month (1-12 or JAN-DEC)
│ │ │ │ │ ┌──── day-of-week (1-7 or SUN-SAT, or ?)
│ │ │ │ │ │
* * * ? * *
```

Common schedules:

| Cron | Runs |
|------|------|
| `0 0 2 ? * *` | Daily at 02:00 UTC |
| `0 0 */6 ? * *` | Every 6 hours |
| `0 0 3 ? * MON-FRI` | Weekdays at 03:00 UTC |
| `0 0 1 1 * ?` | Monthly (1st of each month at 01:00 UTC) |

---

## 10. Error Payloads

### HTTP Status Codes

| Code | When |
|------|------|
| `202 Accepted` | Subscription created / backfill submitted |
| `200 OK` | Successful GET or PATCH; also returned when removing non-existent filter values (silent no-op) |
| `204 No Content` | Successful DELETE (terminate) |
| `400 Bad Request` | Request validation failed (see table below) |
| `403 Forbidden` | Certificate CN not in CDP allowlist, S3/SNS permissions missing, or `GET /subscribers` CN not permitted |
| `410 Gone` | Subscription (batch request) not found — returned by PATCH and DELETE, not `404` |
| `500 Internal Server Error` | CDP internal failure |

### 400 – Validation Errors

| Error message | Cause | Fix |
|---------------|-------|-----|
| `dsl-version is missing or invalid` | `dsl-version` header absent or wrong format | Add header `dsl-version: 1.0.0` |
| `dsl-query is missing or invalid` | GraphQL syntax error or missing wrapper | Check `query { tables { ... on table_name { ... } } }` structure |
| `s3-bucket-arn is missing` | `s3-bucket-arn` not in request body | Add `"s3-bucket-arn": "s3://..."` |
| `schedule is invalid` | Bad Quartz cron expression | Use 6-field Quartz format |
| `group provided is invalid` | Group name not in approved list | Use approved name or register a new one |
| `filter.column not in query` | Filter column not selected in DSL query | Add the column to the DSL projection |
| `filter-values size must be >= 1` | Empty filter array | Provide at least 1 value |
| `filter-values exceeds limit` | Exceeds environment max | Stay within per-environment limits |

**Confirmed error envelope (all endpoints):**

```json
{
  "errors": [
    {
      "message": "<human-readable description>",
      "type": "<ExceptionClassName>",
      "extra-data": {}
    }
  ]
}
```

> **Note:** Always parse `errors[0].message` for the error description and `errors[0].type` for the exception class. `extra-data` is an optional key-value map.

**400 example:**

```json
{
  "errors": [
    {
      "message": "Filter values size must be >= 1",
      "type": "ValidationException",
      "extra-data": { "filter-values": "[]" }
    }
  ]
}
```

### 403 – Forbidden

**Common causes:**
- Certificate CN not permitted by CDP (requires JIRA DPF onboarding ticket)
- S3 bucket policy does not include the CDP Egress role ARN
- S3 bucket not registered in [egress-job-permissions](https://github.concur.com/DataPlatformFoundation/egress-job-permissions)
- SNS topic not registered in [egress-notification-permissions](https://github.concur.com/DataPlatformFoundation/egress-notification-permissions)

> No body is returned on `403` — check your certificate CN registration and bucket/topic permissions.

### 410 – Gone *(replaces 404)*

Returned by PATCH (remove filters) and DELETE (terminate) when the subscription cannot be found.

```json
{
  "errors": [
    {
      "message": "request not found",
      "type": "ResourceGoneException",
      "extra-data": {}
    }
  ]
}
```

### 500 – Internal Server Error

```json
{
  "errors": [
    {
      "message": "an error occurred processing the request",
      "type": "ApplicationException",
      "extra-data": {}
    }
  ]
}
```

> On a 500, note the `concur-correlationid` you sent and share it with the DataPlatform team in `#ask-dataplatform`.

---

## 11. Design Considerations

- **Provisioning only.** The API schedules data delivery; it does not return business data directly.
- **Incremental delivery.** Every batch contains only changes since the last delivery. The very first delivery is a full historical load (unless `startWatermark` is set).
- **Schedule is a start-time target.** Actual delivery can be ±5 minutes depending on queue depth.
- **Use SNS to trigger processing.** Poll the S3 path only *after* receiving a `SUCCESS` notification. Do not poll on a timer.
- **Deduplication.** CDP performs best-effort deduplication, but subscribers **must** handle duplicate records (e.g., two `MODIFY` events with the same timestamp for the same object).
- **Data minimisation.** Only select the columns your service actually needs in the `dsl-query`.
- **Deletes are unified.** CDP combines regular deletes and Regulatory (OTD) deletes. Treat all records in the `deletes/` folder as potential regulatory deletes.
- **Compliance.** The subscriber owns compliance from the S3 bucket outward. Consult the [DPP team](https://sap.sharepoint.com/sites/126557) for current GDPR/OTD requirements.
- **CMK/CSK environments.** Use exactly one company UUID per subscription in `integration-dev` and `uspscc` environments.
- **No schedule-change API (yet).** There is currently no API endpoint to modify a subscription's schedule after creation. The `PUT /groups/{group-id}` endpoint is defined in the spec but not implemented. Use Slack `#ask-dataplatform` to request schedule changes.
- **No list-all-subscriptions API.** Fetching all subscriptions for a team is only possible by filtering on a specific S3 bucket path (`GET /list/s3bucketpaths?s3-bucket-path=...`).

---

## 12. Client Integration Notes

### Node.js (current Control Plane)

```js
const axios = require('axios');

// Create subscription
async function createSubscription(payload) {
  const response = await axios.post(
    `${process.env.CDP_SUBSCRIPTION_API_BASE_URL}/datasubscription/v2/schedule`,
    payload,
    {
      params: { 'run-initial-now': true, 'output-bucket-format': 'orc' },
      headers: {
        'Content-Type': 'application/json',
        'dsl-version': '1.0.0',
        'concur-correlationid': generateUUID(),
      },
      // mTLS: configure httpsAgent with client cert + key
      httpsAgent: new https.Agent({
        cert: fs.readFileSync(process.env.CLIENT_CERT_PATH),
        key:  fs.readFileSync(process.env.CLIENT_KEY_PATH),
      }),
    }
  );
  return response.data; // { group-id, jobs }
}
```

- Set `CDP_SUBSCRIPTION_API_BASE_URL` per environment.
- Load the mTLS client certificate via `https.Agent`. The cert CN must match the CDP allowlist.
- Always send `concur-correlationid` (UUID v4) for traceability.
- Map `400` → validation error (parse `errors[0].message`), `403` → auth/permission error, `410` → subscription not found (not `404`), `500` → contact DataPlatform with the `concur-correlationid`.

### Python (future module)

```python
import httpx
import uuid
import ssl

ssl_ctx = ssl.create_default_context()
ssl_ctx.load_cert_chain(certfile="client.crt", keyfile="client.key")

async def create_subscription(payload: dict) -> dict:
    async with httpx.AsyncClient(verify=ssl_ctx) as client:
        response = await client.post(
            f"{CDP_SUBSCRIPTION_API_BASE_URL}/datasubscription/v2/schedule",
            json=payload,
            params={"run-initial-now": "true", "output-bucket-format": "orc"},
            headers={
                "dsl-version": "1.0.0",
                "concur-correlationid": str(uuid.uuid4()),
            },
        )
        response.raise_for_status()
        return response.json()  # { "group-id": ..., "jobs": [...] }
```

- Use `httpx.AsyncClient` with an `ssl.SSLContext` loaded with the client certificate.
- Field names in request/response use kebab-case (e.g. `group-id`, `request-id`). Map to Python-friendly names at the service boundary if needed.
- Parse errors as: `response.json()["errors"][0]["message"]`.
- The SNS `Message` field is Base64-encoded — always decode before parsing (see [Section 8](#8-sns-notifications)).

---

*OpenAPI source of truth: [dataSubscription.yaml](https://github.concur.com/DataPlatformFoundation/schema/blob/master/Egress/dataSubscription.yaml)*
