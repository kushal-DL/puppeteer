# CDE API Integration Playbook — Expense Leakage Detection

> **Status:** Draft
> **Last updated:** 2026-04-06
> **Purpose:** Defines every API call the CDE K8s Dumb Fetcher must make, in what order, with what inputs and filters, to support the full Pass 2 rule evaluation for AmexGBT expense leakage detection.

---

## Table of Contents

1. [Architecture Context](#1-architecture-context)
2. [Business Rule Recap](#2-business-rule-recap)
3. [Data Needed for Rule Evaluation](#3-data-needed-for-rule-evaluation)
4. [API Call Inventory](#4-api-call-inventory)
   - [Call 1 — CDP Subscription (Expense Reports)](#call-1--cdp-subscription-expense-reports)
   - [Call 2 — Travel Profile Service: Get User Default Travel Config](#call-2--travel-profile-service-get-user-default-travel-config)
   - [Call 3 — Config-API: Resolve Travel Config Details](#call-3--config-api-resolve-travel-config-details)
   - [Call 4 — Config-API: Resolve Travel Config for a Booking](#call-4--config-api-resolve-travel-config-for-a-booking)
5. [Call Sequencing & Data Flow](#5-call-sequencing--data-flow)
6. [Field Mapping: API Response → Pass 2 Dataset](#6-field-mapping-api-response--pass-2-dataset)
7. [Booking Agency vs. User Default Config — Independence](#7-booking-agency-vs-user-default-config--independence)
8. [Decision Matrix](#8-decision-matrix)
9. [Edge Cases & Open Questions](#9-edge-cases--open-questions)

---

## 1. Architecture Context

CDE uses a **two-pass PySpark architecture** where:

- **Pass 1 (Glue):** Ingests raw CDP expense report ORC data, applies Tier 1 pre-filters, deduplicates, and extracts UUIDs for fan-out.
- **K8s Dumb Fetcher (Phase 3):** Reads the UUID extract from S3, concurrently calls CTE APIs (travel-profile-service, config-api) to fetch enrichment data, and writes RAW JSON responses back to intermediary S3. **No business logic runs here.**
- **Pass 2 (Glue):** Loads Pass 1 parquet + API enrichment data from S3, performs broadcast joins, evaluates the 5-condition export rule, and writes egress output.

The Dumb Fetcher needs to produce the following JSONL files in intermediary S3:

| File | Contents | Source API |
|------|----------|------------|
| `customers.jsonl` | Customer consent dates | CTE Consent API (out of scope — synced in Phase 1) |
| `users.jsonl` | User → default `travel_config_id` mapping | travel-profile-service |
| `travel_configs.jsonl` | Travel config → `agency_type` + `complete_enabled` | config-api |
| `bookings.jsonl` | Booking → `agency_type` (AmexGBT vs Other) | config-api (via travel config on the booking) |
| `expense_lines.jsonl` | Flattened expense lines with `booking_id`, `trip_id`, `expenseType` | Derived from Pass 1 CDP data (no API call) |

---

## 2. Business Rule Recap

A report is exported to AmexGBT **only if ALL conditions are true**:

```
should_export =
    is_submitted
    AND is_after_consent
    AND has_required_category
    AND (has_amex_booking OR (has_no_booking AND user_default_cfg_is_amex_complete))
    AND NOT has_non_amex_booking        ← "Poison Pill" guardrail
```

| Condition | What it checks | Data source |
|-----------|----------------|-------------|
| `is_submitted` | `submitTimestamp IS NOT NULL` | CDP expense report |
| `is_after_consent` | `submitTimestamp >= consentDate` | CDP report + `customers.jsonl` |
| `has_required_category` | At least one expense line has `expenseType` ∈ {`ABFEE`, `AIRFE`, `AIRFR`, `CARRT`, `LODGA`, `LODGN`, `LODGT`, `LODGX`, `RAILX`} | CDP report `expenses[]` array |
| `has_amex_booking` | Any expense line references a `bookingUuid` whose booking's `agency_type == "AmexGBT"` | CDP `expenses[].bookingUuid` → `bookings.jsonl` |
| `has_no_booking` | No expense line in the report has a non-null `bookingUuid` | CDP report |
| `user_default_cfg_is_amex_complete` | User's default travel config has `agency_type == "AmexGBT"` AND `complete_enabled == true` | `users.jsonl` → `travel_configs.jsonl` |
| `has_non_amex_booking` | Any expense line references a booking with `agency_type != "AmexGBT"` | CDP `expenses[].bookingUuid` → `bookings.jsonl` |

---

## 3. Data Needed for Rule Evaluation

### 3.1 From CDP (Pass 1 — No API Call Needed)

These fields come directly from the CDP expense report subscription:

| Field | Location in CDP Payload | Used For |
|-------|------------------------|----------|
| `reportId` | `data.reportId` | Primary key, deduplication |
| `companyId` | `data.companyId` | Tier 1 filter, join to customers |
| `reportOwner` | `data.reportOwner` (user UUID) | Join to users |
| `submitTimestamp` | `data.submitTimestamp` | Consent check |
| `expenses[].expenseType` | `data.expenses[].expenseType` | Category filter |
| `expenses[].bookingUuid` | `data.expenses[].bookingUuid` | Booking agency check |
| `expenses[].tripUuid` | `data.expenses[].tripUuid` | Alternate booking lookup |
| `expenses[].id` | `data.expenses[].id` | Expense line identity |
| `revisionTimestamp` | `data.revisionTimestamp` | Deduplication sort key |

### 3.2 From CTE APIs (K8s Dumb Fetcher)

| Dataset | Required Fields | Source API |
|---------|----------------|------------|
| Users | `user_id`, `default_travel_config_id` | travel-profile-service |
| Travel Configs | `travel_config_id`, `agency_type`, `complete_enabled` (i.e. `castleEnabled`) | config-api |
| Bookings | `booking_id`, `travel_config_id`, `agency_type` | config-api (resolve via travel config UUID on the booking) |

---

## 4. API Call Inventory

---

### Call 1 — CDP Subscription (Expense Reports)

> **When:** One-time setup (provisioning). Not called per-execution.
> **Who calls it:** DevOps / pipeline setup, not the Dumb Fetcher.

This is the data ingestion subscription — it provisions the raw CDP data that feeds Pass 1.

#### Endpoint

```
POST /datasubscription/v2/schedule?run-initial-now=true&output-bucket-format=orc
```

#### Base URL

| Environment | URL |
|-------------|-----|
| Integration | `https://subscription-integration.service.cnqr.tech` |
| US2 / EU2 (Production) | `https://subscription.service.cnqr.tech` |

#### Authentication

**mTLS (mutual TLS)** — No OAuth token. Service certificate CN must be pre-approved by CDP team.
- Onboard via JIRA: project `DPF`, Epic `DPF-5059`, Components: `AWS Egress Requests, egress`
- `concur-forwarded-for` is injected automatically by ServiceMesh (never set by caller)

#### Required Headers

```
Content-Type: application/json
dsl-version: 1.0.0
concur-correlationid: <UUID v4>
request-id-alias: cde-expense-reports
```

#### Request Body

```json
{
  "dsl-query": "query { tables { expense_reports { reportId companyId reportOwner submitTimestamp firstSubmitTimestamp revisionTimestamp creationTimestamp approvalStatus paymentStatus auditStatus businessPurpose country countrySubdivision reimbursementCurrency reportDate reportName reportNumber startDate endDate ledgerCode totalApprovedAmount totalClaimedAmount totalPostedAmount expenses } } }",
  "s3-bucket-arn": "s3://cde-raw-bucket/cdp-expense-exports",
  "schedule": "0 0 2 ? * *",
  "notification-topic-arn": "arn:aws:sns:us-west-2:123456789012:cde-cdp-arrival",
  "group.name": "SCT",
  "group.filter.column": "companyId",
  "group.filter.values": ["<company-uuid-1>", "<company-uuid-2>"]
}
```

> **Note:** DSL query must target exactly one table. Column names are case-sensitive and lowercase. The `expenses` field is a nested JSON array — CDP delivers it as-is.

#### Response (202 Accepted)

```json
{
  "group-id": "<uuid-v3>",
  "jobs": [
    {
      "request-id": "<uuid-v4>",
      "expected-start-time": "2026-04-07T02:00:00Z",
      "filter-values": ["<company-uuid-1>"]
    }
  ]
}
```

#### SNS Notification Decoding

CDP SNS notifications are **Base64-encoded**. Decode before parsing:

```python
import base64, json

def decode_cdp_notification(sns_message: dict) -> dict:
    return json.loads(base64.b64decode(sns_message["Message"]))
```

Monitor for `job-status == "SUCCESS"` to know when data is ready in S3.

#### Key Output Fields for Downstream

From the `extra-data` on `SUCCESS`:
- `s3-path-upsert`: S3 prefix for new/updated records
- `s3-path-delete`: S3 prefix for deleted records
- `upsert-row-count` / `delete-row-count`: Row counts
- `start-watermark` / `end-watermark`: Delivery window bounds

---

### Call 2 — Travel Profile Service: Get User Default Travel Config

> **When:** Phase 3 (Dumb Fetcher), once per unique `reportOwner` UUID from Pass 1 UUID extract.
> **Purpose:** Resolve each user's **default travel config ID/UUID** for the "no-booking fallback" rule.

#### Option A — Tiamat v2 (Recommended)

Best for CDE because it returns the `General.TravelConfigID` directly plus the DynamoDB-backed `general.travelConfigUUID`.

**Endpoint:**

```
GET /api/v2/tiamat/profile
```

**Base URL:**

```
https://tps.travel-profile.service.cnqr.tech
```

**Authentication:** Bearer JWT (service-to-service). The service CN must be registered with TPS.

```
Authorization: Bearer <YOUR_TOKEN_HERE>
```

**Required Headers:**

```
concur-companyid: <company-uuid>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uuid` | string | **Yes** (use this) | User UUID (= `reportOwner` from CDP) |
| `projections` | string | No | Comma-separated field projections to limit response size |

**Request Example:**

```bash
curl -X GET \
  'https://tps.travel-profile.service.cnqr.tech/api/v2/tiamat/profile?uuid=06cb0fb3-9a1d-4644-815e-f6d13b8faa18' \
  -H 'Authorization: Bearer <token>' \
  -H 'concur-companyid: bdd640fb-0667-4ad1-9c80-317fa3b1799d'
```

**Fields to Extract from Response:**

```json
{
  "General": {
    "TravelConfigID": 12345,
    "RuleClass": "Standard",
    "CompanyId": 67890,
    "AgencyNumber": "ABC123"
  },
  "Internal": {
    "UUID": "06cb0fb3-9a1d-4644-815e-f6d13b8faa18",
    "CUUID": "bdd640fb-0667-4ad1-9c80-317fa3b1799d"
  }
}
```

| Response Field | Maps To (users.jsonl) | Usage |
|----------------|----------------------|-------|
| `Internal.UUID` | `user_id` | Join key to expense reports (`reportOwner`) |
| `Internal.CUUID` | `customer_id` | Company UUID |
| `General.TravelConfigID` | `default_travel_config_id` (numeric) | Join to config-api to resolve agency type |

**Output — users.jsonl row:**

```json
{
  "user_id": "06cb0fb3-9a1d-4644-815e-f6d13b8faa18",
  "customer_id": "bdd640fb-0667-4ad1-9c80-317fa3b1799d",
  "default_travel_config_id": 12345
}
```

#### Option B — TPS v1 DynamoDB Profile

Alternative if Tiamat v2 is unavailable. Returns `general.travelConfigUUID` (UUID form) and `general.travelConfigId` (numeric).

**Endpoint:**

```
GET /api/v1/travelProfile/profile
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `uuid` | string | **Yes** | User UUID |

**Required Headers:**

```
concur-companyid: <company-uuid>
```

**Fields to Extract:**

```json
{
  "uuid": "06cb0fb3-...",
  "companyUUID": "bdd640fb-...",
  "general": {
    "travelConfigUUID": "e465e150-bd9c-46b3-ad3c-2d6d1a3d1fa7",
    "travelConfigId": 12345
  }
}
```

| Response Field | Maps To (users.jsonl) |
|----------------|----------------------|
| `uuid` | `user_id` |
| `companyUUID` | `customer_id` |
| `general.travelConfigUUID` | `default_travel_config_id` (UUID form — use this for config-api join) |
| `general.travelConfigId` | `default_travel_config_id` (numeric form) |

> **Recommendation:** Use Tiamat v2 (Option A) as the primary. The v1 DynamoDB endpoint is the fallback. Both provide the `travelConfigId` / `travelConfigUUID` needed for the config-api join.

---

### Call 3 — Config-API: Resolve Travel Config Details

> **When:** Phase 3 (Dumb Fetcher), once per unique `travel_config_id` / `travel_config_uuid` collected from Call 2 results.
> **Purpose:** Determine if the travel config is AmexGBT-owned and Complete-enabled (`castleEnabled`).

#### Endpoint

```
POST /config-api/graphql
```

This is a **GraphQL** API. All queries go to the same endpoint.

#### Base URLs

| Environment | URL |
|-------------|-----|
| Integration | `https://integration.api.concursolutions.com/config-api/graphql` |
| US | `https://us.api.concursolutions.com/config-api/graphql` |
| EU1 | `https://eu1.api.concursolutions.com/config-api/graphql` |
| EU2 | `https://eu2.api.concursolutions.com/config-api/graphql` |
| USPSCC | `https://usg.api.concursolutions.com/config-api/graphql` |

#### Authentication

```
Authorization: Bearer <YOUR_TOKEN_HERE>
```

The service CN must be registered with config-api team. Contact: `#ask-travel-admin-config` on Slack.

#### Required Headers

```
Authorization: Bearer <YOUR_TOKEN_HERE>
Content-Type: application/json
Accept: application/graphql-response+json
concur-correlationid: <UUID v4>
```

#### GraphQL Query — Resolve by Travel Config UUID

Use the `travelConfigs` query (accepts `uuid` or `id`):

> **Note:** The `travelConfigs` query is marked **Deprecated** in the schema doc. If deprecated, use `travelConfig` (singular, JWT-scoped) with a service-level JWT, or `travelConfigsByCompanyAndAgency` if the company UUID and agency UUID are known. See alternatives below.

**Primary Query — `travelConfigs` (by UUID):**

```graphql
query TravelConfigs($uuid: String) {
  travelConfigs(uuid: $uuid) {
    id
    uuid
    travelConfigName
    isActive
    castleEnabled
    gdsType
    agencyConfig {
      uuid
      agencyName
      agencyNumber
      vendorName
      isActive
    }
  }
}
```

**Variables:**

```json
{
  "uuid": "e465e150-bd9c-46b3-ad3c-2d6d1a3d1fa7"
}
```

**Response:**

```json
{
  "data": {
    "travelConfigs": {
      "id": "12345",
      "uuid": "e465e150-bd9c-46b3-ad3c-2d6d1a3d1fa7",
      "travelConfigName": "AmexGBT Standard",
      "isActive": true,
      "castleEnabled": true,
      "gdsType": 2,
      "agencyConfig": {
        "uuid": "a1b2c3d4-...",
        "agencyName": "American Express Global Business Travel",
        "agencyNumber": "AGBT001",
        "vendorName": "AmexGBT",
        "isActive": true
      }
    }
  }
}
```

**Fields to Extract → travel_configs.jsonl:**

| Response Field | Maps To | Usage |
|----------------|---------|-------|
| `uuid` | `travel_config_id` | Join key from users |
| `agencyConfig.agencyName` | `agency_name` | Human-readable label |
| `agencyConfig.vendorName` or `agencyConfig.agencyName` | `agency_type` | **Core discriminator** — check if this matches "AmexGBT" / "American Express Global Business Travel" |
| `castleEnabled` | `complete_enabled` | **Complete-enabled flag** — `true` means the config is CTE-enabled |

**Output — travel_configs.jsonl row:**

```json
{
  "travel_config_id": "e465e150-bd9c-46b3-ad3c-2d6d1a3d1fa7",
  "customer_id": "bdd640fb-0667-4ad1-9c80-317fa3b1799d",
  "agency_name": "American Express Global Business Travel",
  "agency_type": "AmexGBT",
  "complete_enabled": true
}
```

#### Deriving `agency_type` from Config-API Response

The config-api does **not** return a literal `"AmexGBT"` enum. You must derive `agency_type` by inspecting:

1. **`agencyConfig.agencyName`** — Match against known AmexGBT agency names (e.g., contains "AmexGBT", "American Express Global Business Travel", "GBT", "Egencia").
2. **`agencyConfig.vendorName`** — May contain the vendor identifier.
3. **`castleEnabled`** — If `true`, the config is CTE (Complete Travel & Expense) enabled, which strongly correlates with AmexGBT.

**Recommended logic for the Dumb Fetcher output:**

```python
def derive_agency_type(agency_config: dict, castle_enabled: bool) -> str:
    """Derive AmexGBT vs Other from config-api response fields."""
    agency_name = (agency_config.get("agencyName") or "").lower()
    vendor_name = (agency_config.get("vendorName") or "").lower()

    amex_indicators = ["amexgbt", "amex", "gbt", "egencia",
                       "american express global business travel"]

    for indicator in amex_indicators:
        if indicator in agency_name or indicator in vendor_name:
            return "AmexGBT"

    return "Other"
```

> **Open question:** The exact set of `agencyName` / `vendorName` string values that identify AmexGBT needs confirmation from the travel-admin-config team (`#ask-travel-admin-config`). This mapping should be maintained as a configurable allowlist in the Strategy file.

#### Alternative Query — `travelConfigsByCompanyAndAgency`

If you already know both the company UUID and the AmexGBT agency's company UUID, you can use this targeted query to check if a particular config belongs to AmexGBT:

```graphql
query TravelConfigsByCompanyAndAgency(
  $companyUuid: String!,
  $agencyCompanyUuid: String!
) {
  travelConfigsByCompanyAndAgency(
    companyUuid: $companyUuid,
    agencyCompanyUuid: $agencyCompanyUuid
  ) {
    uuid
    travelConfigName
  }
}
```

**Variables:**

```json
{
  "companyUuid": "bdd640fb-0667-4ad1-9c80-317fa3b1799d",
  "agencyCompanyUuid": "<amexgbt-agency-company-uuid>"
}
```

**Response:** Returns the list of travel configs for that company that belong to the specified agency. If a user's default travel config UUID appears in this list, the user is AmexGBT-managed.

> **Prerequisite:** You need the AmexGBT agency's company UUID, which can be obtained from `companiesByAgency` or hard-coded per environment.

---

### Call 4 — Config-API: Resolve Travel Config for a Booking

> **When:** Phase 3 (Dumb Fetcher), once per unique `bookingUuid` found in expense lines from Pass 1.
> **Purpose:** Determine if a booking was made through an AmexGBT agency or a competitor.

**The CDP expense report does NOT directly contain agency information on bookings.** The expense line provides `bookingUuid` and `tripUuid`, but not which agency handled the booking. You must resolve this through the travel config associated with the booking.

#### Approach: Booking → Trip → Travel Config → Agency

There is **no direct "get booking by ID" endpoint** in these three APIs. The linkage path is:

```
expense_line.bookingUuid
    → (Requires a booking/trip service lookup to get the travel_config_id on the booking)
    → travel_config_id
    → config-api travelConfigs query (Call 3)
    → agencyConfig.agencyName → agency_type
```

#### What the Dumb Fetcher Should Do

1. **Extract all unique `bookingUuid` values** from Pass 1 expense lines where `bookingUuid IS NOT NULL`.

2. **Look up booking details** to find the `travel_config_id` associated with each booking. This requires an API that can resolve a booking UUID to its travel config. The available options:

   **Option A — If booking data is available via CDP subscription:**
   
   Subscribe to the bookings/trips table in CDP (separate subscription). This is the preferred bulk approach:
   
   ```graphql
   query {
     tables {
       bookings {
         booking_id
         trip_id
         travel_config_id
         agency_name
         agency_type
       }
     }
   }
   ```
   
   > **Note:** The exact CDP table name and column names for bookings need confirmation from the DataPlatform team (`#ask-dataplatform`). This is the recommended approach for bulk data.

   **Option B — If booking data is NOT in CDP, derive from the user's profile context:**
   
   For each expense line with a `bookingUuid`, the `tripUuid` is typically also present. Use the trip-to-travel-config relationship:
   
   - The trip was booked under a specific travel config
   - The user who booked the trip has a `travelConfigId` on their profile
   - If the booking was made through the user's default travel config, the agency check from Call 3 applies
   
   > **Limitation:** This approach assumes the booking was made under the user's current default config. If the user switched configs between booking time and report submission, this may be inaccurate. The architecture doc acknowledges: *"This is checked based on the user's current configuration, may differ from the time of the report submission."*

3. **For each resolved `travel_config_id`**, use Call 3 (`travelConfigs` query) to determine `agency_type`.

#### Output — bookings.jsonl row

```json
{
  "booking_id": "11ce5dd2-b45e-41f0-b139-d32c93cd59bf",
  "trip_id": "5c941cf0-dc98-42c1-a2ac-f72f9e574f7a",
  "travel_config_id": "e465e150-bd9c-46b3-ad3c-2d6d1a3d1fa7",
  "agency_name": "American Express Global Business Travel",
  "agency_type": "AmexGBT",
  "is_amexgbt": true
}
```

---

## 5. Call Sequencing & Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: INITIALIZATION (One-time)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Call 1: CDP Subscription (POST /datasubscription/v2/schedule)      │
│    → Subscribe to expense_reports table                             │
│    → Filter by Complete-onboarded company UUIDs (from consent API)  │
│    → ORC data delivered to Raw S3 bucket on schedule                │
│                                                                     │
│  NOTE: Company list comes from the CTE Consent/Onboarding API,     │
│  NOT from companiesByAgency. A company's default agency may be a    │
│  competitor, but individual bookings can still go through AmexGBT.  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                PHASE 2: PASS 1 (Glue — Per Execution)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Load raw ORC from S3                                            │
│  2. Apply Tier 1 pre-filters:                                       │
│     - companyId IS NOT NULL                                         │
│     - submitTimestamp >= consentDate                                 │
│     - EXISTS expense with expenseType IN required set               │
│  3. Deduplicate by reportId (keep latest revisionTimestamp)         │
│  4. Extract unique UUIDs:                                           │
│     - reportOwner UUIDs (for user profile lookups)                  │
│     - bookingUuid values (for booking agency lookups)               │
│  5. Write Pass 1 parquet + UUID extract to Intermediary S3          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            PHASE 3: DUMB FETCHER (K8s — Per Execution)              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Input: UUID extract from Intermediary S3                           │
│                                                                     │
│  Step A: For each unique reportOwner UUID:                          │
│    Call 2: GET /api/v2/tiamat/profile?uuid=<reportOwner>            │
│      → Extract: user_id, customer_id, default_travel_config_id      │
│      → Write to: users.jsonl                                        │
│                                                                     │
│  Step B: Collect unique travel_config_ids from Step A results       │
│    Call 3: POST /config-api/graphql (travelConfigs query)           │
│      → For each unique travel_config_id:                            │
│        Extract: travel_config_id, agency_type, complete_enabled      │
│      → Write to: travel_configs.jsonl                                │
│                                                                     │
│  Step C: For each unique bookingUuid from Pass 1:                   │
│    Call 4: Resolve booking → travel_config_id → agency_type         │
│      → Write to: bookings.jsonl                                     │
│                                                                     │
│  Step D: Send Task Token callback to Step Functions                 │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              PHASE 4: PASS 2 (Glue — Per Execution)                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Input: Pass 1 parquet + users.jsonl + travel_configs.jsonl          │
│         + bookings.jsonl from Intermediary S3                        │
│                                                                     │
│  1. Broadcast join: users ⟕ travel_configs → user_cfg               │
│  2. Broadcast join: expense_lines ⟕ bookings → lines_with_bookings  │
│  3. Aggregate by reportId:                                           │
│     - has_required_category                                          │
│     - has_booking / has_amex_booking / has_non_amex_booking           │
│  4. Join report base + user_cfg + aggregated flags                   │
│  5. Evaluate should_export formula                                   │
│  6. Filter approved reports → write to Egress S3                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Field Mapping: API Response → Pass 2 Dataset

### users.jsonl

| Field | Source API | Source Path | Type |
|-------|-----------|-------------|------|
| `user_id` | TPS Tiamat v2 | `Internal.UUID` | string (UUID) |
| `customer_id` | TPS Tiamat v2 | `Internal.CUUID` | string (UUID) |
| `default_travel_config_id` | TPS Tiamat v2 | `General.TravelConfigID` | integer |

Or from TPS v1:

| Field | Source API | Source Path | Type |
|-------|-----------|-------------|------|
| `user_id` | TPS v1 | `uuid` | string (UUID) |
| `customer_id` | TPS v1 | `companyUUID` | string (UUID) |
| `default_travel_config_id` | TPS v1 | `general.travelConfigUUID` | string (UUID) |

### travel_configs.jsonl

| Field | Source API | Source Path | Type |
|-------|-----------|-------------|------|
| `travel_config_id` | config-api | `travelConfigs.uuid` | string (UUID) |
| `customer_id` | config-api | `travelConfigs.company.uuid` | string (UUID) |
| `agency_name` | config-api | `travelConfigs.agencyConfig.agencyName` | string |
| `agency_type` | config-api | Derived (see [section 4, Call 3](#deriving-agency_type-from-config-api-response)) | "AmexGBT" \| "Other" |
| `complete_enabled` | config-api | `travelConfigs.castleEnabled` | boolean |

### bookings.jsonl

| Field | Source API | Source Path | Type |
|-------|-----------|-------------|------|
| `booking_id` | CDP / booking service | booking UUID from expense line | string (UUID) |
| `trip_id` | CDP | `expenses[].tripUuid` from expense line | string (UUID) \| null |
| `travel_config_id` | CDP / booking service | travel config on the booking record | string (UUID) |
| `agency_name` | config-api | Resolved via travel_config_id → `agencyConfig.agencyName` | string |
| `agency_type` | config-api | Derived | "AmexGBT" \| "Other" |
| `is_amexgbt` | Derived | `agency_type == "AmexGBT"` | boolean |

### expense_lines.jsonl (Derived from Pass 1 — no API call)

| Field | Source | Type |
|-------|--------|------|
| `expense_line_id` | CDP `expenses[].id` | string |
| `reportId` | CDP `reportId` | string |
| `companyId` | CDP `companyId` | string (UUID) |
| `report_owner` | CDP `reportOwner` | string (UUID) |
| `expenseType` | CDP `expenses[].expenseType` | string |
| `is_required_travel_category` | Derived: `expenseType IN (ABFEE, AIRFE, AIRFR, CARRT, LODGA, LODGN, LODGT, LODGX, RAILX)` | boolean |
| `trip_id` | CDP `expenses[].tripUuid` | string (UUID) \| null |
| `booking_id` | CDP `expenses[].bookingUuid` | string (UUID) \| null |

---

## 7. Booking Agency vs. User Default Config — Independence

The architecture's filtering rules define **two independent qualification paths**:

```
Path 1 (Booking):  expense_line.bookingUuid → booking's own travel_config → agency_type
Path 2 (Fallback): reportOwner → user's default travel_config → agency_type + complete_enabled
```

**These paths use DIFFERENT travel configs.** The booking's agency comes from the travel config under which that specific booking was made. The user's default travel config is the config currently assigned to the user's profile. They can be different agencies.

### Why this matters

Consider a company where:
- The company's primary TMC is Expedia (competitor)
- A user's default `travelConfigId` points to the Expedia config
- But one specific booking was made through AmexGBT (e.g., via a secondary config, or an ad-hoc booking)

| Scenario | Booking agency | User default config | Qualifies? | Rule path |
|----------|---------------|---------------------|------------|----------|
| AmexGBT booking, competitor default config | AmexGBT | Expedia | **YES — EXPORT** | Path 1: booking is AmexGBT |
| No booking, competitor default config | N/A | Expedia | **NO — DROP** | Path 2: fallback fails |
| Competitor booking, AmexGBT default config | Expedia | AmexGBT + Complete | **NO — DROP** | Poison pill: non-AmexGBT booking overrides |
| No booking, AmexGBT default config | N/A | AmexGBT + Complete | **YES — EXPORT** | Path 2: fallback succeeds |

### Implication: Do NOT pre-filter companies by agency

The CDP subscription's `group.filter.values` (company UUIDs) should come from the **CTE Consent/Onboarding list** — i.e., all companies that have consented to Complete data sharing — NOT from `companiesByAgency`. Filtering by agency at the company level would miss reports where:
- The company's default/primary TMC is a competitor
- But individual bookings within that company were routed through AmexGBT

These are precisely the "expense leakage" cases AmexGBT wants to detect.

---

## 8. Decision Matrix

| Scenario | has_booking | booking agency | user default cfg | Result |
|----------|-------------|----------------|------------------|--------|
| **Perfect Match** — AmexGBT booking, travel category present, post-consent | Yes | AmexGBT | Any | **EXPORT** |
| **Cross-Agency Match** — AmexGBT booking, but user's default config is competitor | Yes | AmexGBT | Expedia / Other | **EXPORT** |
| **Config Fallback** — No booking, user's default config is AmexGBT + Complete-enabled | No | N/A | AmexGBT + `complete_enabled=true` | **EXPORT** |
| **Poison Pill** — Mix of AmexGBT + competitor bookings in same report | Yes | AmexGBT + Other | Any | **DROP** (entire report) |
| **Pre-Consent** — Submitted before customer consent date | Yes | AmexGBT | Any | **DROP** |
| **Invalid Categories** — No required travel expense types in report | Yes | AmexGBT | Any | **DROP** |
| **No Booking + Non-AmexGBT Config** — No booking, user config is competitor or not Complete-enabled | No | N/A | Other or `complete_enabled=false` | **DROP** |
| **Competitor Booking Only** — All bookings are non-AmexGBT | Yes | Other | Any | **DROP** |
| **Reverse Poison** — Competitor booking, AmexGBT default config | Yes | Other | AmexGBT + Complete | **DROP** (poison pill overrides) |

---

## 9. Edge Cases & Open Questions

### 8.1 Booking UUID Resolution Gap

**Problem:** The CDP expense report provides `bookingUuid` on expense lines, but none of the three APIs (CDP Subscription, TPS, config-api) provide a direct "get booking by booking_id" endpoint that returns the travel config / agency associated with that booking.

**Current assumption:** Booking-to-agency resolution requires either:
- A **separate CDP subscription** to a bookings table (preferred for bulk data)
- A **booking/trip microservice** not documented in the attached APIs

**Action needed:** Confirm with DataPlatform team (`#ask-dataplatform`) whether a bookings table exists in CDP, and what columns are available. Alternatively, confirm if there is a booking resolution API in the CTE service mesh.

### 8.2 Agency Name Matching

**Problem:** The config-api returns `agencyConfig.agencyName` as a free-text string. There is no enum or standardized agency type field.

**Mitigation:** Maintain a configurable allowlist in the Strategy file of all known AmexGBT agency name variations. Review with `#ask-travel-admin-config`.

### 8.3 `castleEnabled` as Proxy for Complete-Enabled

**Assumption:** The architecture uses `complete_enabled` as the flag name, which maps to `castleEnabled` in the config-api. "Castle" is the internal codename for the Complete (CTE) product. Confirm this mapping with the travel-admin-config team.

### 8.4 TPS Tiamat v2 `TravelConfigID` is Numeric

The Tiamat v2 response returns `General.TravelConfigID` as an **integer** (e.g., `12345`), while the config-api `travelConfigs` query accepts both `uuid` (string) and `id` (string, numeric). Ensure the join handles both types:
- If using TPS v1: join on `general.travelConfigUUID` (UUID) → config-api `travelConfigs(uuid: ...)`
- If using Tiamat v2: join on `General.TravelConfigID` (int) → config-api `travelConfigs(id: "12345")`

### 8.5 Rate Limiting & Concurrency

The Dumb Fetcher makes O(N) API calls where N = unique users + unique travel configs + unique bookings. Implement:
- Connection pooling with configurable concurrency limits
- Exponential backoff on 429/5xx responses
- Idempotency checks (skip if output already exists in intermediary S3)
- Batch requests where APIs support it (config-api GraphQL can batch multiple queries)

### 8.6 No Trip ID / No Booking ID Scenario

**This is the "config fallback" scenario** the architecture explicitly handles. When an expense report has NO `bookingUuid` or `tripUuid` on any of its lines:
- The Dumb Fetcher still fetches the user's profile (Call 2) to get their default travel config
- Pass 2 checks: `user_default_cfg_agency_type == "AmexGBT" AND user_default_cfg_complete_enabled == true`
- If true → **EXPORT** (the user is AmexGBT-managed even without a booking reference)
- If false → **DROP**

This is the primary mechanism for detecting expense leakage when trip/booking IDs are missing.
