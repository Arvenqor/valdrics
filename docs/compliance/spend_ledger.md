# Canonical Spend Ledger API

Valdrics exposes a canonical, tenant-scoped technology spend ledger for detailed
finance and FinOps review.

## Ledger Endpoint

`GET /api/v1/costs/ledger`

Query parameters:

- `start_date` (required): `YYYY-MM-DD` inclusive
- `end_date` (required): `YYYY-MM-DD` inclusive
- `provider` (optional): one of `aws|azure|gcp|saas|license|platform|hybrid|ai`
- `include_preliminary` (optional, default `false`): include `PRELIMINARY` records
- `limit` (optional, default `100`, max `500`)
- `offset` (optional, default `0`, max `10000`)

Auth / tier:

- Requires role: `admin` or `owner`
- Requires feature: `compliance_exports`

## Ledger Export Endpoint

`GET /api/v1/costs/ledger/export`

Returns a streaming CSV file of the canonical spend ledger.

Query parameters:

- `start_date` (required): `YYYY-MM-DD` inclusive
- `end_date` (required): `YYYY-MM-DD` inclusive
- `provider` (optional): one of `aws|azure|gcp|saas|license|platform|hybrid|ai`
- `include_preliminary` (optional, default `false`): include `PRELIMINARY` records

Response:

- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: `attachment; filename=spend_ledger_{tenant_id}_{start}_{end}.csv`
- Streams pages of 500 records internally for memory efficiency

Auth / tier:

- Requires role: `admin`
- Requires feature: `compliance_exports`

### CSV Column Schema

| Column                        | Type    | Description                                       |
|-------------------------------|---------|---------------------------------------------------|
| `id`                          | UUID    | Record identifier                                 |
| `recorded_at`                 | date    | Date the charge was recorded                      |
| `timestamp`                   | ISO8601 | Full timestamp of the charge                      |
| `provider`                    | string  | One of `aws|azure|gcp|saas|license|platform|hybrid|ai` |
| `account_id`                  | string  | Cloud account or `ai:{provider}` for AI spend     |
| `account_name`                | string  | Human-readable account name                       |
| `service`                     | string  | Service name (e.g. `AmazonEC2`, `LLM`)            |
| `region`                      | string  | Cloud region or `null` for AI                     |
| `usage_type`                  | string  | Usage type or request type                        |
| `resource_id`                 | string  | Resource identifier or operation ID               |
| `usage_amount`                | decimal | Quantity consumed                                 |
| `usage_unit`                  | string  | Unit of consumption (e.g. `Hours`, `tokens`)      |
| `cost_usd`                    | decimal | Normalized cost in USD                            |
| `amount_raw`                  | decimal | Original charge amount                            |
| `currency`                    | string  | Currency code                                     |
| `cost_status`                 | string  | `FINAL` or `PRELIMINARY`                          |
| `canonical_charge_category`   | string  | Canonical charge category                         |
| `canonical_charge_subcategory`| string  | Canonical charge subcategory                      |
| `canonical_mapping_version`   | string  | Mapping version identifier                        |
| `allocation_status`           | string  | `allocated`, `partially_allocated`, or `unallocated` |
| `allocated_amount_usd`        | decimal | Total amount attributed to named buckets          |
| `unallocated_amount_usd`     | decimal | Remaining unattributed amount                     |
| `allocation_count`            | integer | Number of allocation splits                       |
| `tags`                        | JSON    | Record tags or AI metadata                        |
| `allocations`                 | JSON    | Array of allocation splits with amounts           |

## Semantics

- `CostRecord` is the origin-charge ledger row.
- `CostAllocation` is the canonical split-allocation source.
- `LLMUsage` is projected into the same API contract as provider `ai`.
- Money and quantity fields are returned as fixed decimal strings, not floats.
- The endpoint is date-bounded, tenant-scoped, provider-filterable, and paginated.
- `allocation_status` is derived from canonical allocation rows:
  `allocated`, `partially_allocated`, or `unallocated`.
- `include_preliminary=false` exports only finalized ledger rows.
- Acceptance KPI ledger-quality evidence counts both normalized origin
  `CostRecord` rows and AI `LLMUsage` rows.

## Attribution Rule Types

The attribution engine supports the following rule types for cost allocation:

| Rule Type       | Description                                                        |
|-----------------|--------------------------------------------------------------------|
| `DIRECT`        | Assigns entire cost to a single named bucket                       |
| `PERCENTAGE`    | Splits cost across buckets by explicit percentage                  |
| `FIXED`         | Assigns fixed dollar amounts; remainder goes to `Unallocated`      |
| `EVEN_SPLIT`    | Divides cost evenly across N buckets; remainder to first bucket    |
| `PROPORTIONAL`  | Distributes cost by weight ratios; remainder to first positive     |

### Rule Condition Matching

Rules are matched against cost records using the following condition fields:

| Condition              | Description                                                   |
|------------------------|---------------------------------------------------------------|
| `service`              | Exact service name match                                      |
| `service_pattern`      | Glob-style pattern match (e.g. `Amazon*`, `*EC2`)             |
| `region`               | Exact region match                                            |
| `account_id`           | Exact account ID match                                        |
| `provider`             | Direct provider string match (e.g. `saas`, `ai`)              |
| `cost_threshold_min_usd` | Only match records above this USD amount                   |
| `tags`                 | Key-value tag matching                                        |
| `catch_all`            | When `true`, matches any record regardless of tags            |

Tag-less conditions (`service_pattern`, `provider`, `cost_threshold_min_usd`,
`catch_all`) enable allocation of costs that have no tags, enabling fallback and
default attribution rules.

## AI Spend Allocation

AI spend (`LLMUsage` records) can be allocated through the same rule engine as
cloud cost records:

- `CostAllocation.llm_usage_id` links allocations to `LLMUsage` records
- Exactly one of `cost_record_id` or `llm_usage_id` is non-null per allocation
- AI records use `provider=ai`, `service=LLM`, and model-derived attributes
- Allocation status is computed dynamically from real allocation data

## FOCUS Export Relationship

- The canonical ledger export (`/api/v1/costs/ledger/export`) provides a
  flat CSV of the unified spend view including allocations.
- The FOCUS v1.3 CSV export provides a standards-compliant export following
  the FOCUS specification schema.
- Both exports include AI/LLM spend as provider `ai`.
- SKU/unit-price details are not emitted until provider adapters persist them.
