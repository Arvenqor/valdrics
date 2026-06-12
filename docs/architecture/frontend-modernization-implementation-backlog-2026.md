# Frontend Modernization Implementation Backlog 2026+

- Status: Active backlog
- Date: June 1, 2026
- Parent plan: [Frontend Modernization Execution Plan 2026+](frontend-modernization-execution-plan-2026.md)
- Scope: `frontend/` production app, `new_frontend/` design-source disposition, frontend/backend route contracts

## Operating Rule

This backlog is executable only under the non-negotiable rules in the parent plan: one deployable
frontend app, no legacy `dashboard/` compatibility root, no stubs, no fake data, no guessed contracts, no
blind handoff copying, and no replacement of the current Valdrics logo geometry.

Using `new_frontend/` means every handoff file receives an explicit disposition and the production UI
must carry the same Valdrics visual direction, density, and interaction intent wherever the product
contract supports it. A handoff file may be migrated directly, deferred behind a real backend/product
blocker, or rejected with evidence. Existing production frontend features remain first-class: they must
be preserved unless a replacement is tested, contract-backed, visually faithful to the new Valdrics
system, and better for the user. The modernization target is one uniform `frontend/` experience that
carries forward the current working product while adopting the new Valdrics design route by route.
Routes that exist only in the current production app are in scope too. They should be modernized from
the closest completed Valdrics pattern, not left behind because `new_frontend/` lacks a matching file.

## Current Baseline

- Production app root: `frontend/`
- Reference folder: `new_frontend/`
- Completed slices: authenticated shell, approvals, dashboard overview, onboarding, savings,
  inventory/connections reconciliation, public landing/marketing, policies/settings
- Next route slice: auth visual alignment, ownership/identity disposition, then production-only route
  modernization audit
- Production route disposition register:
  `docs/architecture/frontend_route_disposition_register.json`
- Primary gates:
  - `corepack pnpm@10.32.1 --dir frontend lint`
  - `corepack pnpm@10.32.1 --dir frontend check`
  - `corepack pnpm@10.32.1 --dir frontend test:unit -- --run`
  - `corepack pnpm@10.32.1 --dir frontend build`
  - `corepack pnpm@10.32.1 --dir frontend run check:bundle`
  - `uv run python3 scripts/check_frontend_hygiene.py`
  - `uv run python3 scripts/verify_new_frontend_disposition_register.py`
  - `uv run python3 scripts/verify_frontend_route_disposition_register.py`
  - `uv run python3 scripts/verify_frontend_module_size_budget.py`
  - `uv run python3 scripts/verify_frontend_runtime_contract.py`

## Source-Guided Constraints

- Svelte 5 production code must prefer runes and typed props. Do not add new legacy event-dispatch
  patterns from handoff files.
- Cloudflare remains the explicit SvelteKit adapter target; managed Node remains a separately verified
  runtime shim.
- Browser validation must verify user-visible behavior, not implementation internals only.
- Security verification aligns to OWASP ASVS 5.0.0 and OWASP Top 10 2025, with fail-closed auth and
  strict CSP as release constraints.
- Browser telemetry is allowed only when privacy-safe. OpenTelemetry browser instrumentation is still
  experimental, so any adoption must be small, opt-in, and validated for bundle and privacy impact.

## Work Packages

### FME-000: Freeze Source Topology

Objective: make `frontend/` the only app root and prevent accidental legacy drift.

Tasks:

1. Audit remaining `dashboard` references in CI, scripts, Docker, docs, runbooks, and evidence.
2. Classify each reference as historical text, product term, or stale path.
3. Replace stale paths with `frontend`.
4. Extend `scripts/check_frontend_hygiene.py` to fail on new deployable source under `dashboard/`.
5. Add unit coverage for the hygiene rule.

Acceptance:

- No stale deployable path references remain.
- Historical references are clearly historical, not operational.
- Hygiene check blocks legacy app root reintroduction.

### FME-001: Create Handoff Disposition Register

Objective: track every `new_frontend/` file to migration or rejection.

Tasks:

1. Generate a machine-readable register for every file in `new_frontend/`.
2. Fields: source file, target route/module, status, decision, contract evidence, owner, deletion blocker.
3. Seed completed statuses for authenticated shell and approvals.
4. Fail CI if a reference file is deleted without disposition or a disposition references a missing target.
5. Use `docs/architecture/new_frontend_disposition_register.json` as the register and
   `scripts/verify_new_frontend_disposition_register.py` as the verifier.

Acceptance:

- Every `new_frontend/` file has a disposition row.
- Completed rows include target files and verification evidence.
- Pending rows identify a precise blocker.

### FME-002: Dashboard Overview Migration

Status: Implemented on June 1, 2026. The production route now uses handoff-style
summary metrics, spend topology, policy health, operational signals, and savings
panels backed by current loader/model contracts. Handoff-only inventory, policy,
and savings fields without backend evidence were not copied.

Objective: migrate dashboard overview visual direction into the real dashboard route without changing
contracts by guesswork.

Reference inputs:

- `new_frontend/valdrics-dashboard-page.svelte`
- `new_frontend/SpendTopologyChart.svelte`
- `new_frontend/PolicyHealthRings.svelte`
- `new_frontend/InventoryPanel.svelte`
- `new_frontend/SavingsPanel.svelte`

Production targets:

- `frontend/src/routes/dashboard/+page.svelte`
- `frontend/src/routes/dashboard/+page.ts`
- `frontend/src/routes/dashboard/dashboardOverviewModel.ts`
- Route-local Svelte components only where the dashboard route proves reuse.

Tasks:

1. Inventory visible dashboard widgets from handoff and current route.
2. Map each widget to current reporting API fields.
3. Reject or defer widgets without real backend fields.
4. Preserve current date/provider/persona behavior.
5. Add route-local presentation components only where file size or testability requires it.
6. Add tests for success, loading, partial API failure, empty data, and entitlement state.
7. Run desktop and mobile browser QA for dashboard load, provider/date controls, refresh, and overflow.

Acceptance:

- Dashboard renders production data only.
- No fake inventory, savings, policy, or topology metrics.
- Route keeps module-size budget discipline.
- Browser QA shows no text overlap or horizontal overflow at desktop and 390px mobile.

### FME-003: Dashboard Contract Tests

Objective: make dashboard API assumptions executable.

Tasks:

1. Add tests that assert exact edge proxy paths used by dashboard loaders/actions.
2. Add fixture tests for partial failures and timeout fallbacks.
3. Confirm backend unit tests cover any newly exposed reporting contract.
4. Document rejected handoff fields in the disposition register.

Acceptance:

- Mutating or refresh actions use verified paths and payloads.
- Unknown handoff fields cannot silently enter UI models.

### FME-004: Design Token Consolidation

Objective: keep new UI visually coherent without premature abstraction.

Tasks:

1. Compare shell, approvals, and dashboard styles for repeated tokens.
2. Move only stable repeated tokens into existing app CSS/token files.
3. Keep route-specific composition local.
4. Audit color balance so the interface does not become one hue family.
5. Preserve Valdrics logo asset usage and material treatment rules.

Acceptance:

- Shared tokens reduce duplication without creating a generic UI framework.
- No route imports handoff CSS variables directly.
- Logo use remains asset-based.

### FME-005: Onboarding Migration

Status: Implemented on June 1, 2026. The production route now carries the
handoff-inspired wizard shell, progress rail, provider card treatment, discovery
panel styling, and success/action controls while preserving existing provider
setup validation and connector payload contracts. Handoff-only SaaS tool,
policy-default, team-invite, and completion actions were not copied because they
are not backed by the current onboarding route modules.

Objective: modernize onboarding visuals while preserving real provider setup contracts.

Reference inputs:

- `new_frontend/valdrics-onboarding-page.svelte`
- `new_frontend/valdrics-onboarding.html`

Production targets:

- `frontend/src/routes/onboarding/*`

Tasks:

1. Inventory provider cards, setup states, validation steps, and success states.
2. Map AWS, Azure, GCP, and Cloud+ controls to existing onboarding action modules.
3. Keep required field validation and connector config behavior intact.
4. Add tests for provider selection, required fields, OAuth/native connector branches, and verify success.
5. Run browser QA for desktop/mobile setup flow.

Acceptance:

- No onboarding control bypasses account validation.
- Setup payloads match current backend expectations.
- Existing onboarding tests still pass.

### FME-006: Savings Migration

Status: Implemented on June 2, 2026. The production savings route now uses
the Valdrics handoff-inspired KPI, provider breakdown, drilldown, evidence,
and export control treatment while preserving the existing `/savings/proof`,
`/savings/proof/drilldown`, and `/savings/realized/events` reporting
contracts. Handoff-only `/savings/summary`, `/savings/events`, saving-type,
team-name, description, and total-annual fields were not copied because they
are not in the current backend contract.

Objective: migrate savings visual direction only where reporting contracts exist.

Reference inputs:

- `new_frontend/valdrics-savings-page.svelte`
- `new_frontend/SavingsPanel.svelte`

Production targets:

- `frontend/src/routes/savings/*`
- Shared reporting model only if reused by dashboard.

Tasks:

1. Confirm all savings fields from handoff against reporting APIs.
2. Reject invented fields or create backend contracts with tests.
3. Add partial failure and empty recommendation states.
4. Browser QA for savings cards, filters, and mobile layout.

Acceptance:

- Savings page contains no invented opportunity, payback, or recommendation data.
- Tests cover failed and empty reporting responses.

### FME-007: Inventory and Connections Reconciliation

Status: Implemented on June 2, 2026. The production app now has a first-class
`/inventory` route backed by a real backend `/api/v1/inventory` contract that
projects tenant-scoped AWS, Azure, GCP, AWS Organizations discovery, SaaS,
license, platform, and hybrid connector/feed rows. The existing `/connections`
route also keeps an inventory source registry so source setup and inventory
coverage stay reconciled. Handoff-only `/inventory/add`, `/inventory/{id}`,
`/ownership`, `/approvals/new`, and unsupported owner workflow actions were not
copied because they need separate backend/product contracts.

Objective: create a standalone inventory view only after making the backend
model explicit, while keeping connections as the source-of-truth setup surface.

Reference inputs:

- `new_frontend/valdrics-inventory-page.svelte`
- `new_frontend/InventoryPanel.svelte`

Production targets:

- `frontend/src/routes/connections/*`
- `frontend/src/routes/inventory/*`
- `app/modules/reporting/api/v1/inventory.py`
- `app/modules/reporting/domain/inventory_service.py`
- `app/schemas/inventory.py`

Tasks:

1. Decide whether inventory is a standalone product route or a connections subview.
2. Map handoff fields to existing connector/license/cloud inventory models.
3. Reject fields with no backend model.
4. Add route tests for empty, connected, failed, and entitlement-denied states.

Acceptance:

- `/inventory` ships only because the backend route and source projection now exist.
- Inventory rows identify source kind and cost basis so reported feed costs are not presented as monthly
  costs unless the backend says they are monthly.
- Existing connections workflows remain intact.

### FME-008: Policies and Settings Migration

Status: migrated in the production `/settings` enforcement control plane.

Objective: reconcile policy UI with enforcement/settings contracts.

Reference inputs:

- `new_frontend/valdrics-policies-page.svelte`

Production targets:

- `frontend/src/routes/settings/*`
- `frontend/src/lib/components/Enforcement*`

Tasks:

1. Map policy controls to existing enforcement settings APIs.
2. Keep tier gates and admin/role behavior.
3. Add tests for save, reset, failed reads, failed writes, and entitlement denial.
4. Browser QA for policy settings on desktop/mobile.

Acceptance:

- Every policy control reads/writes a real settings or enforcement contract.
- Lower-tier users see honest upgrade/entitlement states.
- The handoff standalone `/policies` route and unsupported trigger counters are not copied into
  production; trigger history requires a dedicated backend events contract before it becomes UI.

### FME-009: Auth and Public Surface Alignment

Status: auth login/signup visual alignment implemented on June 6, 2026. The production
`/auth/login` route now carries the Valdrics dark auth-card treatment while preserving the
current `/auth/flow`, `/auth/callback`, `/auth/session`, public auth intent, and signup-mode
contract. Logout route coverage is now explicit. Ownership/identity disposition was resolved on
June 12, 2026 by migrating the handoff ownership-routing intent into Identity settings through the
real SSO, federation, and SCIM group-mapping contract. No standalone `/ownership` route was added.

Objective: migrate useful auth/marketing references without weakening existing public app behavior.

Reference inputs:

- `new_frontend/valdrics-login-page.svelte`
- `new_frontend/valdrics-signup-page.svelte`
- `new_frontend/valdrics-landing-page.svelte`
- `new_frontend/valdrics-marketing-layout.svelte`
- `new_frontend/valdrics-app-html.html`

Production targets:

- Existing public/auth route groups under `frontend/src/routes`
- `frontend/src/app.html` only if shell metadata needs a verified change.

Tasks:

1. Compare reference copy and visual treatments with current public app.
2. Preserve SEO, legal, pricing, auth intent, and public navigation tests.
3. Do not introduce app-route marketing hero patterns.
4. Browser QA public routes and auth entry.
5. Preserve the current pricing source of truth from `frontend/src/lib/pricing/publicPlans.ts`
   through `frontend/src/routes/pricing`; pricing amounts, plan names, billing cadence, and signup
   intent from `new_frontend/` must be rejected unless Product deliberately updates the production
   pricing contract and its tests.

App shell disposition:

- `new_frontend/valdrics-app-html.html` is resolved by the production `frontend/src/app.html`
  shell and hygiene gates. Keep Valdrics metadata, first-party icons, manifest, and SvelteKit
  placeholders; reject handoff Google Fonts, inline FOUC styles, inline no-JS scripts, and inline
  wrapper styles under the production strict-CSP policy.
- Pricing source of truth: keep the current production Free, Starter, Growth, and Pro plan contract
  from `frontend/src/lib/pricing/publicPlans.ts`. `new_frontend` can inform pricing page visual
  treatment, layout density, and interaction polish, but not pricing values or plan availability.
- Landing/marketing disposition: the production landing now uses the current pricing module for public
  pricing cards and structured data, keeps public auth-intent URLs under `/auth/login`, and renders the
  primary Valdrics mark from `frontend/static/valdrics_icon.png`. Handoff-only `/login`, `/signup`,
  trial/no-card language, custom SVG logo marks, and stale `$299 Starter` / `$799 Team` pricing are
  rejected.

Acceptance:

- Public/auth changes preserve existing tests and metadata behavior.
- No unverified auth flows are introduced.

### FME-010: Production-Only Route Modernization

Status: route disposition register created on June 6, 2026. Route-by-route modernization,
merge, and retire decisions remain pending for routes marked `pending` in
`docs/architecture/frontend_route_disposition_register.json`.

Objective: upgrade current production routes that have no direct `new_frontend/` source so the final
application is visually and operationally uniform.

Reference inputs:

- Current `frontend/src/routes/**` inventory
- Completed Valdrics patterns from shell, dashboard, onboarding, savings, inventory, landing, and
  policies/settings
- Existing route tests and backend/edge-proxy contracts
- `docs/architecture/frontend_route_disposition_register.json`

Initial production-only route groups:

- Authenticated operational: `/audit`, `/billing`, `/greenops`, `/leaderboards`, `/llm`, `/ops`,
  `/admin/*`, `/status`
- Public/content: `/about`, `/blog`, `/docs`, `/enterprise`, `/pricing`, `/privacy`, `/proof`,
  `/resources`, `/insights`, `/roi-planner`, `/talk-to-sales`, `/terms`
- Internal/API: `/api/*`, auth endpoints, SEO endpoints, download endpoints, and `__capture/*`
  fixtures must stay documented even when they have no visual migration work.

Tasks:

1. Maintain a route inventory that marks every production route as migrated, pending, internal, or
   rejected from modernization scope.
2. For each route, map visible controls to current API/edge-proxy contracts before changing UI.
3. Decide whether each pending route should be kept, merged, retired, or rebuilt as a stronger
   Valdrics workflow.
4. Apply the migrated Valdrics tokens, card density, typography, status badges, and logo rules.
5. Preserve current pricing, legal, SEO, admin, and entitlement contracts.
6. Add focused tests and rendered QA for each upgraded route.

Acceptance:

- No current production route remains visually disconnected from the migrated Valdrics app.
- Routes with no handoff reference still have a documented modernization disposition.
- No route remains only because it already existed; bloated routes are merged or retired with evidence.
- No route introduces fake controls, guessed API fields, or stale pricing/content claims.

### FME-011: Observability and Evidence Bundle

Objective: make frontend releases diagnosable and auditable.

Tasks:

1. Define privacy-safe frontend events: route load, critical API failure class, route render error,
   primary interaction latency, and browser QA evidence.
2. Avoid recording tokens, tenant secrets, raw cloud account IDs, provider credentials, or user-entered
   sensitive data.
3. Keep telemetry optional until bundle and privacy checks pass.
4. Produce a release evidence bundle per migrated route.

Acceptance:

- Evidence includes commands, route screenshots, bundle metrics, runtime checks, and disposition status.
- Telemetry has a privacy review note before shipping.

## Dependency Order

1. FME-000
2. FME-001
3. FME-002 and FME-003
4. FME-004 after dashboard proves repeated tokens
5. FME-005
6. FME-006
7. FME-007
8. FME-008
9. FME-009
10. FME-010
11. FME-011 runs alongside every migrated route after FME-001

## Per-Slice Browser QA Matrix

| Viewport            | Required Checks                                                                                       |
| ------------------- | ----------------------------------------------------------------------------------------------------- |
| 1440 x 900          | Page identity, no blank render, no framework overlay, real logo asset, primary action, console errors |
| 390 x 844           | No horizontal overflow, no text overlap, nav state, primary content visible, controls fit             |
| Reduced motion      | No required information hidden behind motion-only behavior                                            |
| Entitlement denied  | Honest upgrade or blocked state without loading protected data                                        |
| Partial API failure | Useful partial content or error state without broken layout                                           |

## Ship Criteria

A slice can merge only when:

1. It passes all required gates.
2. Browser QA evidence exists for desktop and mobile.
3. Handoff disposition is updated.
4. Any newly discovered backend gap is either fixed with tests or the UI is omitted.
5. No legacy root, stub, placeholder, or fake action is introduced.

## Stop Criteria

Stop and revise the slice if:

1. A handoff requirement cannot be mapped to a real API or product decision.
2. The implementation requires weakening CSP.
3. The UI needs fake data to look complete.
4. Mobile browser QA shows overlap or horizontal overflow.
5. Runtime, bundle, security, or hygiene gates fail.
