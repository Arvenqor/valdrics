# Frontend Modernization Execution Plan 2026+

- Status: Active execution plan
- Date: June 1, 2026
- Owners: Frontend, Platform, Security, Product
- Parent ADR: [ADR-0002](ADR-0002-dashboard-modernization-2026.md)

## Purpose

This plan turns the `new_frontend/` handoff into a production-grade Valdrics frontend without
creating a second app, preserving legacy compatibility paths, or shipping unsupported UI. The only
deployable frontend application is `frontend/`. The `new_frontend/` directory is the temporary
non-deployable design/product source of truth for visual direction, interaction ideas, and product
intent.

The work is complete only when every useful `new_frontend/` artifact has either been migrated into
`frontend/` with visual fidelity, real contracts, and tests; deferred behind a precise product/backend
blocker; or rejected with documented evidence, every production-only route has been audited for the
same Valdrics design system, and then obsolete handoff artifacts are removed.

## Current Repo Facts

- `frontend/` is the active SvelteKit app.
- `frontend/package.json` pins Svelte 5, SvelteKit 2, Vite 7, Playwright, Vitest, Wrangler, and pnpm.
- `frontend/` already has release gates for lint, Svelte check, unit tests, e2e, build, visual, bundle,
  and performance checks.
- Current public pricing lives in `frontend/src/lib/pricing/publicPlans.ts` and is surfaced through
  `frontend/src/routes/pricing`; pricing values from `new_frontend/` are not authoritative.
- `scripts/verify_frontend_runtime_contract.py` verifies the managed Node runtime shim around the
  SvelteKit Cloudflare build output.
- `scripts/check_frontend_hygiene.py` enforces frontend hygiene constraints.
- `scripts/verify_frontend_module_size_budget.py` enforces module size discipline.
- `docs/architecture/frontend_route_disposition_register.json` and
  `scripts/verify_frontend_route_disposition_register.py` track every production SvelteKit route
  module under `frontend/src/routes` so production-only routes cannot drift outside the migration.
- `new_frontend/` contains the new Valdrics design/product source files for shell, dashboard,
  onboarding, approvals, policies, savings, inventory, auth, and backend requirements.
- Authenticated shell and approvals have already been migrated and verified as the first slices.
- Several production routes are not represented directly in `new_frontend/` and still require design
  modernization: audit, billing, docs/resources/proof content, enterprise, GreenOps, leaderboards,
  LLM, ops, pricing, ROI planner, status, legal pages, admin routes, and sales/contact flows.

## Research Baseline

As of June 1, 2026, the plan follows primary sources and the current repo state:

- Svelte 5: new production code uses runes, typed props, and callback props instead of legacy event
  dispatcher patterns. Reference: https://svelte.dev/docs/svelte/v5-migration-guide
- SvelteKit Cloudflare adapter: keep the Cloudflare build target explicit and verify the separate
  managed Node runtime shim. Reference: https://svelte.dev/docs/kit/adapter-cloudflare
- Vite production builds: use modern ESM output, measured chunking, and explicit production builds.
  Reference: https://vite.dev/guide/build
- Playwright: browser tests must exercise user-visible workflows and avoid implementation-coupled
  selectors where possible. Reference: https://playwright.dev/docs/best-practices
- OWASP Top 10 2025 and ASVS 5.0.0: use current web risk and verification guidance for security
  controls. References: https://owasp.org/Top10/2025/ and https://owasp.org/www-project-application-security-verification-standard/
- NIST SSDF SP 800-218: secure software work is planned, protected, produced, and responded to through
  repeatable controls. Reference: https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA v1.2: provenance, build integrity, and dependency trust are release requirements.
  Reference: https://slsa.dev/spec/v1.2/about
- OpenTelemetry browser guidance: frontend observability should capture useful user-experience signals
  without leaking tenant or secret data. Reference: https://opentelemetry.io/docs/languages/js/getting-started/browser/

## Non-Negotiable Rules

1. No legacy deployable root. `dashboard/` must not return as a compatibility app or alias.
2. No stubs. Empty placeholders, fake API payloads, fake charts, and unsupported buttons are rejected.
3. No blind copy from `new_frontend/`. The visual design and product intent are production targets; the
   handoff code, paths, stores, and inferred backend contracts are not production truth until verified.
4. No guessed contracts. Every API path, payload, entitlement, and error shape must be verified locally.
5. No broad backward compatibility. Cutover happens by replacing the active frontend path and deleting
   old surfaces after evidence passes.
6. No pricing drift. Keep the current Free, Starter, Growth, and Pro pricing contract from
   `frontend/src/lib/pricing/publicPlans.ts`; the handoff may influence presentation only after tests
   prove the production pricing values, billing cycle behavior, and signup intent are unchanged.
7. No one-off visual drift. Route slices must use shared tokens or route-local styles that match the
   Valdrics design system.
   Deliberate deviations from `new_frontend/` must be recorded with the blocker that forced them.
8. No logo replacement. Use `frontend/static/valdrics_icon.png` as the primary Valdrics mark.
   `frontend/static/valdrics_icon1.png` and `frontend/static/valdrics_wordmark.svg` remain supporting
   shell assets, but color, material, lighting, or 3D treatment must derive from the primary PNG and
   preserve its geometry.
9. No unmodernized production islands. A route that exists only in current `frontend/` still belongs to
   this modernization. If `new_frontend/` has no matching file, use the established Valdrics shell,
   tokens, density, logo, entitlement, and API-contract rules as the design source.
10. No route bloat by default. Existing routes are not automatically retained. Each route must prove a
    distinct user/job-to-be-done, real contract support, and a coherent place in the Valdrics IA; weak
    or duplicative routes are merged or retired with tests, SEO/legal checks where relevant, and
    disposition evidence.

## Execution Model

Each migration slice follows the same factory:

1. Inventory the handoff file and existing production route.
2. Classify every visible control as backed by API, local deterministic state, entitlement gate, or reject.
3. Map production contracts: endpoint, method, schema, auth role, entitlement, timeout, rate limit, and
   error state.
4. Implement in `frontend/` only, using Svelte 5-compatible patterns.
5. Add or update focused unit tests and contract tests.
6. Run release gates and browser QA on desktop and mobile.
7. Record rejected handoff ideas in a disposition note.
8. Delete migrated handoff files when their disposition is complete.

Production-only route slices follow the same factory, except step 1 inventories the existing production
route and the closest migrated Valdrics pattern instead of a handoff file. The slice is not done until
the route is visually coherent with the migrated app, preserves its current contracts, and has tests or
rendered QA covering the main user flow.

## Phase Plan

### Phase 0: Freeze Topology

Objective: make repository ownership impossible to misunderstand.

Work:

- Finish any remaining rename references from `dashboard` to `frontend` in CI, docs, scripts, Docker,
  runbooks, evidence, and CODEOWNERS.
- Add or extend hygiene checks so deployable source cannot reappear under `dashboard/`.
- Create a machine-readable `new_frontend` disposition register.

Acceptance:

- `git ls-files` shows no deployable dashboard source.
- CI, Docker, runtime scripts, release runbooks, and quality gates reference `frontend/`.
- `scripts/check_frontend_hygiene.py` blocks legacy app-root reintroduction.

### Phase 1: Design System Foundation

Objective: codify the Valdrics look before migrating more routes.

Work:

- Extract shared tokens from the reference: dark operational shell, cyan/green/yellow/red semantic
  signals, compact badges, 8px-or-smaller cards, dense table spacing, mono data labels, and lucide-style
  icons.
- Keep app routes operational and scan-friendly. Avoid landing-page hero patterns inside authenticated
  workflows.
- Preserve the public Valdrics logo geometry, with optional material/3D treatment around the asset.
- Consolidate only proven primitives: status badges, filter tabs, stat chips, action buttons, empty
  states, detail rows, and shell affordances.

Acceptance:

- New UI uses existing CSS/token architecture instead of copied handoff variables.
- Text does not overlap on mobile or desktop.
- Palette does not collapse into a single hue family.
- Logo usage is real asset usage, not an approximated SVG replacement.
- Browser QA includes a visual fidelity check against the corresponding `new_frontend` source.

### Phase 2: Route-by-Route Migration

Objective: migrate highest-value authenticated workflows first.

| Order | Route                                 | Reference Inputs                                                                                                                          | Production Target                                                              | Notes                                                                          |
| ----- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| 1     | Authenticated shell                   | `Sidebar.svelte`, `TopBar.svelte`, `valdrics-app-layout.svelte`                                                                           | `frontend/src/routes/layout/*`, `frontend/static/authenticated-shell.css`      | Done. Preserve current logo mark.                                              |
| 2     | Approvals                             | `valdrics-approvals-page.svelte`, `ApprovalCard.svelte`                                                                                   | `frontend/src/routes/approvals/*`                                              | Done. Keep entitlement states honest.                                          |
| 3     | Dashboard overview                    | `valdrics-dashboard-page.svelte`, `SpendTopologyChart.svelte`, `PolicyHealthRings.svelte`, `InventoryPanel.svelte`, `SavingsPanel.svelte` | `frontend/src/routes/dashboard/*`                                              | Done. Reuses current loader and real reporting contracts.                      |
| 4     | Onboarding                            | `valdrics-onboarding-page.svelte`, `valdrics-onboarding.html`                                                                             | `frontend/src/routes/onboarding/*`                                             | Keep real provider validation and cloud account setup.                         |
| 5     | Savings                               | `valdrics-savings-page.svelte`, `SavingsPanel.svelte`                                                                                     | `frontend/src/routes/savings/*`                                                | No invented savings fields. Tie to current reporting outputs.                  |
| 6     | Inventory/connections                 | `valdrics-inventory-page.svelte`, `InventoryPanel.svelte`                                                                                 | `frontend/src/routes/connections/*` and any real inventory surface             | Reconcile naming before implementation.                                        |
| 7     | Policies/settings                     | `valdrics-policies-page.svelte`                                                                                                           | `frontend/src/routes/settings/*` and enforcement components                    | Done. Keeps entitlement gates and `/enforcement/*` backend policy model.       |
| 8     | Auth and ownership/identity           | auth/marketing/handoff support files, `valdrics-ownership-page.svelte`                                                                    | `/auth/login`, `/settings`, existing route groups                              | Continue from auth visual alignment and ownership/identity disposition.        |
| 9     | Production-only operational routes    | current `frontend/` route inventory                                                                                                       | audit, billing, GreenOps, LLM, ops, leaderboards, admin, status                | Modernize even where no handoff file exists. Preserve backend contracts first. |
| 10    | Production-only public/content routes | current `frontend/` route inventory                                                                                                       | docs, resources, proof, enterprise, pricing, ROI planner, legal, sales/contact | Keep current pricing, SEO, and content contracts while aligning visual system. |

Acceptance per route:

- Route-local typed model or shared contract module.
- Real API paths or documented edge proxy paths only.
- Loading, empty, partial-error, entitlement-denied, and success states.
- Focused Vitest coverage for primary actions.
- Browser QA for desktop, mobile, active control states, console errors, and horizontal overflow.

### Phase 3: Backend Contract Closure

Objective: make every frontend control truthful.

Work:

- Treat `new_frontend/valdrics-backend-requirements.html` as a requirements note, not evidence.
- For every migrated action, write down endpoint, method, payload, response, auth, entitlement, timeout,
  and error contract.
- If a contract is missing, either build it with backend tests in the same slice or omit the UI.
- Keep browser code behind the edge proxy. Do not call private backend origins directly from client code.

Acceptance:

- Frontend tests assert endpoint paths and mutating payload shapes.
- Backend tests cover newly added routes.
- Contract checks pass.
- No disabled fake controls remain.

### Phase 4: Enterprise Security and Identity

Objective: pass serious enterprise security review.

Work:

- Align frontend controls with OWASP Top 10 2025, ASVS 5.0.0, and NIST SSDF intent.
- Preserve fail-closed auth/session behavior.
- Continue strict CSP: no broad `unsafe-inline`, no raw HTML without sanitization, no Svelte transition
  directives that force weak CSP.
- Require explicit `button type`, safe external links, CSRF-aware mutations, secure cookies, and
  protected-route negative tests.
- Keep dependency exceptions dated, owned, and removable.

Acceptance:

- Security headers are tested.
- `pnpm audit --audit-level=high` runs in CI.
- `scripts/check_frontend_hygiene.py` passes.
- Negative tests cover unauthenticated, unauthorized, stale-session, and entitlement-denied flows.

### Phase 5: Performance, Reliability, and Observability

Objective: keep the UI fast and diagnosable under enterprise scale.

Work:

- Continue bundle and module-size budgets.
- Lazy-load charting, maps, and heavy visualization libraries.
- Use timeouts and partial-error UI for slow non-critical data.
- Add route-level browser performance gates for dashboard, onboarding, savings, and approvals.
- Add privacy-aware frontend telemetry for navigation timing, rendering health, API failure classes, and
  critical interaction latency.

Acceptance:

- `frontend/scripts/check-bundle-size.mjs` passes.
- Initial route bundles stay inside budget.
- Browser tests assert no blank state, no horizontal overflow, and no framework overlay.
- Telemetry excludes tenant secrets, tokens, raw cloud account identifiers, and customer payloads.

### Phase 6: Release, Provenance, and Rollback

Objective: ship auditable production changes without keeping legacy source alive.

Work:

- Roll out one route slice at a time behind existing entitlement or release controls.
- Generate evidence for each route: command output, screenshots, bundle metrics, runtime contract output,
  and disposition notes.
- Keep rollback at artifact/deployment level. Do not preserve old app roots as fallback code.
- Maintain SBOM, provenance, and container scan workflows.

Acceptance:

- Release evidence links to exact CI run or local evidence bundle.
- Docker and Cloudflare paths are both tested or explicitly scoped.
- Post-deploy smoke covers public app, authenticated shell, dashboard, approvals, and auth.

### Phase 7: Delete Handoff and Legacy Surfaces

Objective: remove ambiguity after migration.

Work:

- Delete each `new_frontend/` reference file after its migration or rejection is documented.
- Delete `new_frontend/` entirely when the disposition register is empty.
- Remove dashboard-named scripts, workflow labels, docs, and evidence references after frontend
  replacements pass.
- Keep architecture docs and runbooks aligned.

Acceptance:

- No handoff-only source remains.
- No deployable source exists outside `frontend/`.
- CI fails on legacy root reintroduction.

## Required Gates

Every substantial frontend migration slice must run:

```bash
corepack pnpm@10.32.1 --dir frontend lint
corepack pnpm@10.32.1 --dir frontend check
corepack pnpm@10.32.1 --dir frontend test:unit -- --run
corepack pnpm@10.32.1 --dir frontend build
corepack pnpm@10.32.1 --dir frontend run check:bundle
uv run python3 scripts/check_frontend_hygiene.py
uv run python3 scripts/verify_new_frontend_disposition_register.py
uv run python3 scripts/verify_frontend_route_disposition_register.py
uv run python3 scripts/verify_frontend_module_size_budget.py
uv run python3 scripts/verify_frontend_runtime_contract.py
```

Route migrations must also run a focused browser QA pass. The target flow is:

```text
authenticated route loads -> primary state renders -> user action changes visible state -> console/page
errors are checked -> desktop and mobile screenshots show no overlap or overflow
```

## Immediate Work Queue

The detailed work packages are tracked in
[frontend-modernization-implementation-backlog-2026.md](frontend-modernization-implementation-backlog-2026.md).

1. Keep the `new_frontend` and production route disposition registers at zero drift.
2. Complete FME-009 auth visual alignment while preserving `/auth/login`, `/auth/flow`,
   `/auth/callback`, `/auth/session`, logout behavior, and current pricing plan intent.
3. Modernize or merge production-only operational routes: `/audit`, `/billing`, `/greenops`,
   `/leaderboards`, `/llm`, `/ops`, `/admin/*`, and `/status`.
4. Modernize or consolidate production-only public/content routes: `/about`, `/blog`, `/docs`,
   `/enterprise`, `/pricing`, `/privacy`, `/proof`, `/resources`, `/insights`, `/roi-planner`,
   `/talk-to-sales`, and `/terms`.
5. Close backend gaps from `new_frontend/valdrics-backend-requirements.html` by building real backend
   contracts with tests or omitting unsupported UI.
6. Produce FME-011 evidence bundles and remove handoff/internal QA files only after disposition,
   route tests, browser QA, and release gates pass.

## Route Slice Definition of Done

A route is complete only when all statements are true:

1. The route lives under `frontend/`.
2. It uses real data contracts or explicit entitlement gates.
3. It has no fake controls, placeholder data, unsupported links, or copied legacy snippets.
4. It has typed models and focused tests.
5. It passes all required gates.
6. Browser QA covers desktop and mobile.
7. Rejected handoff behavior is recorded.
8. Any corresponding handoff file is deleted or marked pending with a precise blocker.

## Risk Register

| Risk                                                     | Impact                                        | Control                                                             |
| -------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------- |
| Handoff UI implies backend features that do not exist    | Fake product behavior                         | Contract map before implementation; omit or build backend contract. |
| Route migration creates shared abstractions too early    | Brittle UI framework inside the app           | Keep components route-local until reuse is proven.                  |
| Dark dashboard palette becomes one-note                  | Poor readability and generic feel             | Token audit after each slice; use semantic accents intentionally.   |
| Mobile rail or dense panels overlap content              | Enterprise users lose trust quickly           | Browser QA at 390px and desktop for each slice.                     |
| Svelte handoff snippets use legacy patterns              | Future migration debt                         | New code uses Svelte 5 runes and typed props.                       |
| Runtime target drift between Cloudflare and managed Node | Deploy failures                               | Keep adapter and runtime shim verified separately.                  |
| Security exceptions become permanent                     | Audit risk                                    | Dated owner, expiry, and removal trigger for every exception.       |
| Legacy roots remain as fallback                          | Confusing ownership and stale vulnerabilities | Artifact rollback only; no compatibility app root.                  |

## Innovation Track

These are allowed only when they are tied to real contracts and acceptance gates:

- Adaptive operational dashboards that prioritize anomalies by cost, risk, and enforcement urgency.
- Privacy-safe frontend telemetry that flags broken tenant workflows before customers report them.
- Contract-derived UI state machines for loading, partial data, failed actions, and entitlement denial.
- Evidence-first release bundles that include route screenshots, command outputs, provenance, and
  disposition status.
- Material/3D brand treatment around the real Valdrics mark, preserving logo geometry.

## Stop Conditions

Pause a slice instead of shipping if any of these occur:

- Required backend contract is missing and cannot be implemented in the same slice.
- A control would need fake data or a disabled placeholder.
- Browser QA shows mobile overlap, unreadable text, blank rendering, or horizontal overflow.
- CSP must be weakened beyond the documented policy.
- Bundle, module-size, runtime, hygiene, or security gates fail.
- The implementation depends on preserving `dashboard/` or another legacy root.
