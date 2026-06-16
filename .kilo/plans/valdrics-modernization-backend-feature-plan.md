# CloudSentinel Valdrics Modernization Backend Feature Plan

## Goal
Continue Valdrics modernization with evidence-backed production and enterprise readiness while using `PLAN.md` as the canonical source of truth when planning conflicts exist.

## Current State
- `PLAN.md` is canonical and says Phase 2 is the active engineering phase.
- Phase 1 is not closed because release-ops sign-off and real production-use validation are still pending.
- The active implementation focus is Phase 2 cleanup/validation plus production-safety fixes that are required for the active phase.
- `frontend/` is the deployable frontend.
- `new_frontend/` is migration input, not code to copy blindly.

## Non-Negotiable Rules
1. One active phase at a time.
2. Do not mark a phase complete until it is live in production and usable by real users.
3. Do not start new phase work unless it directly serves the active phase or fixes a production/security/release blocker.
4. Cleanup is evidence-gated: inventory references, run tests, update registers, then delete.
5. No fake data, stubs, unsupported controls, guessed contracts, legacy `dashboard/` compatibility roots, or replacement Valdrics logo geometry.
6. Backend source of truth comes before frontend UI.
7. Pricing values must not silently change; preserve `frontend/src/lib/pricing/publicPlans.ts` unless a pricing decision is explicitly recorded.

## Track A: Route Modernization and Legacy Cleanup
### A0 Housekeeping
- Fix lint/whitespace issues only when they block verification or release gates.
- Keep verification scripts in place.
- Re-run hygiene, route, API contract, and frontend gates after cleanup batches.

### A1 Identity/Routing Modernization
- Keep login identity modernization only where already implemented and tested.
- Do not add new auth routes unless required by Phase 2 or a production blocker.

### A2 Billing and GreenOps Route Corrections
- Keep billing entitlement summaries aligned with backend pricing/tiering.
- Keep GreenOps access gating aligned with backend entitlements.
- Do not advertise Starter GreenOps access.

### A3 Public/Content Route Disposition
- Maintain disposition evidence for public/content routes before any deletion.
- Do not delete public/content routes without register proof.

## Track B: Backend Feature Backlog
### B1 Improved Audit Evidence Capture
- Add structured, sanitized event logging with emit/audit/service_feedback/kpi flows.
- Redact PII and secrets.
- Add schema stability and sanitization tests.

### B2 Customer-Facing Scoped API Keys
- Add `CustomerApiKey` with encrypted storage, fingerprint, prefix, scopes, and rate tier.
- Add create/list/update-status/rotate/revoke endpoints.
- Add tenant isolation, authorization, rotation, and idempotency tests.

### B3 Outbound Webhooks + Retry Scheduler
- Fix retry scheduler drift, retention, repeated wake-up cycles, and urgent trigger omission first.
- Add deterministic retry contracts, idempotent sends, and maintenance-mode semantics.
- Add regression tests with deterministic simulated clocks.

### B4 Approval SLA Enforcement
- Add approval SLA breach detection and resolution workflow.
- Add tests for breach triggers and renewal edge cases.

### B5 In-App Notifications and SSE Feed
- Add tenant-scoped `Notification` and `NotificationSettings`.
- Add notification routing, read/unread state, pagination, and polling/SSE feed.
- Add unread count, pagination, preference, and stream tests.

### B6 Ownership Reminder Digests
- Add reminder payloads, scheduling, deduplication, and persona routing.
- Add cost-aware suppression and routing.

### B7 Email Template System
- Add composable templates for notifications and billing.
- Add safe HTML/text rendering and variable escaping.

### B8 Sentry Production Error Tracking
- Add privacy-safe Sentry integration with environment gating.
- Redact Authorization headers, email, and secrets.
- Add redaction and environment tests.

### B9 Admin Panel Domain Models
- Add admin audit and permission policy domain models before UI.
- Separate org admin from platform operator access.
- Never trust client-supplied org IDs.

### B10 GDPR Personal Data Export and Erasure
- Add export/delete APIs with user verification and cancellation.
- Add audit logs, redaction, and tenant-scoped access checks.

## Track C: Contract, Security, and Release Gates
For every new backend feature:
1. Add OpenAPI/schema or explicit schema tests.
2. Add auth/role/entitlement tests.
3. Add idempotency where mutations can be retried.
4. Add audit logs for admin/security-sensitive actions.
5. Add rate limiting where public or API-key-authenticated.
6. Update frontend API contract verifier when frontend paths are added.
7. Update `docs/security/ssdf_traceability_matrix.json` where relevant.

Acceptance:
- No frontend control depends on an untested backend contract.
- Backend tests cover success, auth failure, authorization failure, validation failure, and idempotency where applicable.

## Track D: Pricing Packaging Modernization
### D1 Packaging Centralisation
Update `docs/architecture/tiering-2026.md` to define:
- Managed Cloud Spend model.
- Optimization Credits policy.
- Validated Savings Share guardrails.
- Enterprise contract layer differentiation.

Keep public prices unchanged unless explicitly approved.

### D2 Pricing Model
Use a hybrid tier + usage + outcome model:
- Fixed tier for access and governance maturity.
- Managed cloud spend as primary expansion meter.
- Optimization credits as execution-capacity meter.
- Add-ons as orthogonal capabilities.
- Enterprise as custom contract layer.

Managed cloud spend should use trailing 30-day normalized net spend from connected cloud accounts.

Optimization credits must be enforced through a formal ledger, not an informal counter.

Validated savings share must be optional, auditable, capped, and dispute-safe.

### D3 Managed Spend Tiers
| Tier | Managed Spend Cap |
| --- | ---: |
| Free | $2,500 |
| Starter | $10,000 |
| Growth | $50,000 |
| Pro | $250,000 |
| Enterprise | Custom committed spend |

### D4 Optimization Credit Allowances
| Tier | Credits |
| --- | ---: |
| Free | 5/month |
| Starter | 20/month |
| Growth | 100/month |
| Pro | 500/month |
| Enterprise | Committed credit pool |

### D5 Credit Action Weights
- Standard AI analysis: 1-3 credits.
- Deep AI analysis with backfill: 5-10 credits.
- GreenOps carbon-aware schedule recommendation: 3 credits.
- Graviton migration analysis: 5 credits.
- Policy simulation: 1 credit per 100 resources.
- Non-production remediation dry run: 2 credits.
- Non-production remediation execution: 5 credits.
- Compliance/savings proof export: 2 credits each.
- Deep backfill scan: 10 credits.
- Custom connector analysis: add-on or enterprise-only.

### D6 Savings Share
- Optional add-on for opted-in accounts/resources only.
- 10-15% of validated savings.
- First 6 months after opt-in unless contract says otherwise.
- Billed monthly in arrears.
- Capped, for example at 3x monthly subscription fee or enterprise fixed cap.

### D7 Backend Implementation
Add or complete:
- `ManagedSpendSnapshot`.
- `OptimizationCreditLedger`.
- `AddOnCatalog`.
- `EnterpriseContractOverride`.
- `SavingsShareCalculation`.
- `ManagedSpendService`.
- `OptimizationCreditService`.
- `SavingsShareService`.

Backend responsibilities:
- trailing spend lookup.
- current-month forecast.
- threshold alerts.
- upgrade signals.
- credit balance lookup.
- idempotent credit consumption.
- reverse failed actions.
- burn forecast.
- savings baseline/actual calculation.
- exclusion handling.
- cap calculation.
- dispute-safe audit records.

Validation:
- Run pricing packaging tests.
- Run billing tests if billing paths change.
- Run `uv run python3 scripts/check_frontend_api_contracts.py`.
- Run `uv run python3 scripts/verify_repo_root_hygiene.py`.

### D8 Managed Cloud Spend Definition
Managed Cloud Spend is the primary expansion meter.

Definition:
- trailing 30-day normalized net cloud spend from connected cloud accounts that Valdrics can ingest, attribute, and monitor.
- net spend after provider-applied discounts and credits visible in the cloud bill.
- excludes Valdrics-generated savings from the spend meter.
- counts only connected accounts; discovered but unconnected accounts remain coverage gaps.
- uses current-month forecast for alerts, not billing or tier enforcement.
- excludes taxes and support contracts unless explicitly added later.
- includes cloud marketplace charges when present in the cloud bill.

Tier gating:
- Free: up to $2,500.
- Starter: up to $10,000.
- Growth: up to $50,000.
- Pro: up to $250,000.
- Enterprise: custom committed spend.

Alert and upgrade policy:
- 70% of managed spend limit: show warning.
- 90% of managed spend limit: show upgrade recommendation.
- 100% for one billing period: allow grace or soft overage if supported.
- forecast exceeds 125% of limit for 7 days: prompt upgrade before next billing cycle.
- trailing 30-day average exceeds limit for 2 cycles: require upgrade or enterprise review.

### D9 Optimization Credit Policy
Optimization credits are the secondary value metric for high-cost or high-value workflows.

Policy:
- monthly reset for self-serve tiers.
- no rollover by default for Free/Starter/Growth/Pro.
- unused self-serve credits expire at period end.
- no silent overages unless pre-authorized.
- credit packs and connector packs are add-ons, not hidden tier changes.
- Enterprise may use a committed credit pool or optional rollover.

Credit ledger requirements:
- tenant-scoped ledger entries.
- period start/end.
- action type and action id.
- credits consumed and action weight.
- metadata.
- idempotency key.
- created timestamp.
- status for completed, blocked, reversed, and failed.
- reversal support for failed actions.
- auditability for billing disputes.
- forecast hooks for burn rate and exhaustion date.

Credit weights:
- Standard AI analysis: 1-3 credits.
- Deep AI analysis with backfill: 5-10 credits.
- GreenOps carbon-aware schedule recommendation: 3 credits.
- Graviton migration analysis: 5 credits.
- Policy simulation: 1 credit per 100 resources.
- Non-production remediation dry run: 2 credits.
- Non-production remediation execution: 5 credits.
- Compliance export: 2 credits.
- Savings proof export: 2 credits.
- Deep backfill scan: 10 credits.
- Custom connector analysis: add-on or enterprise-only.

### D10 Validated Savings Share Methodology
Validated Savings Share is an optional ROI-aligned add-on.

Policy:
- 10-15% of validated savings.
- first 6 months after opt-in unless contract says otherwise.
- billed monthly in arrears.
- capped at 3x monthly subscription fee or enterprise fixed cap.
- applies only to opted-in accounts/resources.
- requires connected billing and resource telemetry.
- no retroactive claims.

Baseline and attribution:
- use a 30-day baseline window before the optimization action.
- require connected account, billing data, and resource telemetry.
- attribute savings only when Valdrics produced the recommendation or controlled the automation.
- compare baseline normalized spend against actual normalized spend after stabilization.
- exclude provider price reductions, unrelated refunds/credits, taxes/support changes, manual customer changes outside Valdrics workflow, missing billing data, resources outside opted-in scope, and noise below measurement threshold.

Dispute handling:
- disputed line items are frozen.
- Valdrics provides evidence package:
  - baseline window.
  - recommendation/action log.
  - before/after normalized spend.
  - excluded adjustments.
  - affected resources.
- undisputed portion remains billable.
- invalid disputed portion is credited or removed.

### D11 Enterprise Differentiation
Enterprise is a custom contract layer, not a larger self-serve tier.

Enterprise entitlements:
- SCIM.
- SSO.
- advanced RBAC.
- audit evidence.
- private deployment option.
- data residency.
- custom retention.
- advanced forecasting.
- commitment planning.
- custom connectors.
- SLA-backed support.
- procurement/security artifacts.
- dedicated rollout governance.
- custom commercial terms.
- committed managed spend.
- committed optimization credits.
- optional savings-share.
- optional private deployment/data residency.

Enterprise packaging model:
- Enterprise platform fee.
- committed managed cloud spend.
- committed optimization credits.
- optional add-ons.
- optional savings-share.
- optional private deployment/data residency.

Enterprise should require contract review, security/procurement review, deployment planning, and usage commitment negotiation.

### D12 Product Model Changes
Replace the current feature-heavy tiering model with a hybrid packaging model.

Current effective model:
- tier -> feature flags -> limits.

Target model:
- plan -> managed spend limit.
- plan -> optimization credits.
- plan -> feature entitlements.
- add-ons -> orthogonal capabilities.
- enterprise contract -> overrides and custom layers.

Backend requirements:
- managed cloud spend meter ingestion.
- spend normalization.
- tier gating based on spend meter, not only feature flags.
- optimization credit ledger.
- credit consumption middleware/service.
- savings-share calculation service.
- usage forecast service.
- enterprise contract override layer.

Billing requirements:
- base subscription.
- add-ons.
- credit packs.
- managed spend overage or upgrade prompts.
- savings-share invoice line items.
- dispute/credit adjustment workflow.

Frontend requirements:
- pricing calculator.
- managed spend progress.
- credit balance and burn rate.
- savings-share opt-in.
- upgrade prompts based on real usage.
- enterprise contract request path.
- clear distinction between base tier, add-ons, and enterprise contract.

Test requirements:
- managed spend tier gating.
- connected vs discovered account inclusion.
- credit ledger idempotency.
- credit reset/expiry.
- savings-share baseline calculation.
- savings-share exclusions.
- dispute handling.
- enterprise contract overrides.
- pricing page copy consistency.

## Track E: Engineering Standards, Legacy Removal, and Cleanup Gates
### E1 2026+ Engineering Baseline
- Require backend-first contracts for new features.
- Require auth, role, entitlement, validation, and idempotency tests.
- Require audit logs for admin/security-sensitive actions.
- Require OWASP API Security Top 10 controls for new APIs.
- Require SLSA-aligned supply-chain controls for build/release work.
- Require SRE controls for production-sensitive work.

### E2 Legacy, Stub, and Compatibility Inventory
Inventory before deletion:
- `dashboard/`.
- `new_frontend/`.
- stale route directories.
- compatibility shims.
- disabled placeholders.
- fake data factories.
- mocked production controls.
- unused backend modules.
- unused frontend routes/components.

For each candidate removal, record:
- file or directory.
- last known purpose.
- current references.
- tests covering removal.
- register disposition where applicable.
- deletion blocker.

Do not delete based on filename alone.

### E3 Remove Stubs, Fake Data, and Unsupported Controls
- Remove fake data, fake metrics, fake credentials, fake controls, disabled placeholders, and unsupported links.
- Replace removed controls with backend-backed implementation, documented blocker, or no UI/control.
- Remove compatibility layers only after consumers are migrated and contract tests pass.
- Update tests to cover no-stub behavior.

### E4 Remove Unnecessary Directories and Files
- Delete only files/directories with empty deletion blockers.
- Prefer staged batch deletion.
- Re-run hygiene and register verifiers after each batch.
- Keep root-owned/environment-managed cleanup separate from source cleanup.
- Do not remove files solely because they are large.

### E5 Performance, Scalability, and Maintainability
- Add pagination, limits, and query bounds to list/export APIs.
- Add indexes for high-cardinality tenant/workspace lookups.
- Use async-safe patterns for backend routes and jobs.
- Add caching only where invalidation is explicit and safe.
- Add idempotency keys for retryable mutations.
- Keep frontend modules within hard size budgets.

### E6 Security and Enterprise Readiness
- Enforce tenant isolation in all data access paths.
- Add audit logs for admin, billing, entitlement, data export, data erasure, API-key, webhook, and enterprise override actions.
- Redact secrets from logs, metrics, traces, and error reports.
- Add SSRF protection for user-supplied URLs and webhook destinations.
- Add rate limiting for public, billing, API-key, and admin-sensitive endpoints.
- Add privacy-safe exports for GDPR, savings-share disputes, and audit evidence.
- Add Enterprise controls for SCIM, SSO, private deployment, data residency, custom retention, SLAs, and procurement artifacts where product scope requires them.

### E7 Legacy Cleanup Validation Gates
After each cleanup batch, run:
```bash
git diff --check
uv run python3 scripts/verify_new_frontend_disposition_register.py
uv run python3 scripts/verify_frontend_route_disposition_register.py
uv run python3 scripts/verify_repo_root_hygiene.py
```

When backend files are removed, run relevant targeted backend tests.

When frontend files are removed, run:
```bash
corepack pnpm@10.32.1 --dir frontend lint
corepack pnpm@10.32.1 --dir frontend check
corepack pnpm@10.32.1 --dir frontend test:unit -- --run
corepack pnpm@10.32.1 --dir frontend build
corepack pnpm@10.32.1 --dir frontend run check:bundle
uv run python3 scripts/verify_frontend_runtime_contract.py
uv run python3 scripts/verify_frontend_module_size_budget.py
```

## Recommended Execution Order
1. Keep Phase 1 open until all Phase 1 requirements are met.
2. Continue Phase 2 cleanup and validation as the active engineering phase.
3. Fix production/security/release blockers immediately.
4. Finish pricing packaging backend before exposing pricing UI changes.
5. Apply Track E engineering baseline to all new backend/frontend work.
6. Inventory legacy components before deletion.
7. Remove legacy artifacts only in evidence-gated batches.
8. Modernize `/pricing` only after pricing backend decisions are implemented.
9. Modernize `/greenops`, `/ops`, `/llm`, then `/audit` and `/admin/*`.
10. Delete `new_frontend/` files only after explicit user approval and register verification.

## Definition of Done
- Active phase scope is implemented and validated.
- Phase 1 remains open until release-ops sign-off and real production-use validation are complete.
- Pricing/usage/credit calculations are reproducible, auditable, and dispute-safe where billing is affected.
- Legacy cleanup is evidence-gated with register and verifier proof.
- API, security, supply-chain, observability, and SRE controls are applied where relevant.
- No fake data, stubs, disabled placeholders, or unsupported controls remain.

## Relevant Files
- `PLAN.md`
- `.kilo/plans/valdrics-modernization-backend-feature-plan.md`
- `docs/architecture/tiering-2026.md`
- `app/models/pricing.py`
- `app/modules/billing/domain/billing/packaging_services.py`
- `app/modules/reporting/api/v1/costs*.py`
- `app/modules/reporting/domain/spend_ledger*.py`
- `frontend/src/lib/pricing/publicPlans.ts`
- `frontend/src/routes/pricing/+page.svelte`
- `docs/architecture/frontend_route_disposition_register.json`
- `docs/architecture/new_frontend_disposition_register.json`
