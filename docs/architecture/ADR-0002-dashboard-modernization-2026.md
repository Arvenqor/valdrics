# ADR-0002: Dashboard Modernization (2026 Frontend Standards)

- Status: Accepted
- Date: February 14, 2026
- Owners: Frontend, Platform, Security

## Context

The Valdrics dashboard is a core product surface and must meet modern expectations for:

- performance (fast navigations, predictable budgets, good Core Web Vitals)
- security (strong headers/CSP, safe auth/session handling, dependency auditing)
- reliability (timeouts, resilient fetch, stable tests)
- maintainability (strict typing, component separation, consistent tooling)

The codebase must remain production-ready and work in both local development and CI.

## Decision

Modernize the `frontend/` SvelteKit application around an actively maintained, ESM-first toolchain:

- Framework/tooling:
  - SvelteKit + Svelte 5 (runes) with Vite as the bundler
  - `@sveltejs/adapter-cloudflare` for the SvelteKit build target
  - `frontend/server.node.mjs` as the explicit container runtime shim for managed Node deployments
  - Strict TypeScript (`strict: true`) and Svelte typechecking (`svelte-check`)
- Performance:
  - lazy-load heavy client-only libraries (for example Chart.js) via dynamic imports
  - enforce bundle-size performance budgets as a CI gate
  - avoid blocking navigations on slow API calls by moving non-critical hydration client-side
- Security:
  - baseline security headers in `frontend/src/hooks.server.ts`
  - CSP directives in `frontend/svelte.config.js`
  - dependency auditing in CI (`pnpm audit --audit-level=high`)
- Quality gates:
  - CI job to run frontend lint, typecheck, unit tests, build, and bundle budgets
  - Playwright E2E uses a reproducible backend webServer command (uv/uvicorn)

## Rationale

- SvelteKit/Vite provide maintained, fast builds with modern ESM output and good tree-shaking.
- Strict TS + linting + unit tests reduce regressions and epistemic debt.
- Lazy loading + performance budgets prevent gradual bundle bloat that harms Core Web Vitals.
- Security headers/CSP + dependency auditing provide practical protections against common web threats.

## 2026 Modernization Plan

This plan treats `new_frontend/` as the non-deployable design/product source of truth for the new
Valdrics frontend. The production application is `frontend/`: the goal is to carry the same visual
language, density, interactions, and product intent into production without copying brittle handoff code.
The old `dashboard/` tree must not return as a compatibility surface. Migration work must either move a
real production capability into `frontend/`, defer it behind a precise contract blocker, or delete the
obsolete surface. No route may ship with placeholder data, fake controls, unsupported links, or backend
contracts inferred from handoff notes.

The detailed execution plan is maintained in
[frontend-modernization-execution-plan-2026.md](frontend-modernization-execution-plan-2026.md).

### Research Baseline

As of June 1, 2026, the plan is aligned to primary project and security sources:

- Svelte 5 migration guidance: use runes and component callback props for new code; do not introduce
  legacy event-dispatch patterns from the handoff snippets.
  Reference: https://svelte.dev/docs/svelte/v5-migration-guide
- SvelteKit Cloudflare adapter guidance: keep the Cloudflare build target explicit and test the custom
  Node runtime shim separately.
  Reference: https://svelte.dev/docs/kit/adapter-cloudflare
- Vite production build guidance: rely on modern ESM builds, intentional code splitting, and measured
  production output instead of legacy browser bundles.
  Reference: https://vite.dev/guide/build
- Playwright testing guidance: browser gates must exercise user-visible workflows, not only component
  rendering.
  Reference: https://playwright.dev/docs/best-practices
- NIST SSDF SP 800-218: secure software work must be planned, protected, produced, and responded to
  through repeatable controls.
  Reference: https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA supply-chain framework: build provenance and dependency integrity must be part of release
  readiness, not an afterthought.
  Reference: https://slsa.dev/spec/v1.2/about

### Non-Negotiable Principles

1. `frontend/` is the single deployable app. `new_frontend/` remains the temporary design/product source
   of truth until every useful artifact is either migrated with visual fidelity, deliberately deferred
   behind a real blocker, or rejected with evidence, then it is removed.
2. No backward-compatible `dashboard/` alias, duplicate app root, or adapter shim is allowed after cutover.
3. User-facing controls must be backed by a real API, local deterministic state, or an explicit entitlement
   gate. Unsupported handoff actions are omitted until the backend contract exists.
4. New Svelte code uses Svelte 5 runes and typed props. Do not copy `createEventDispatcher`, transition
   directives, inline styles, or handoff stores into production.
5. Strict CSP is a release constraint. Svelte transitions, manual inline styles, unsafe HTML, and broad
   `unsafe-inline` CSP are blocked by hygiene checks.
6. Every migration slice must have production acceptance gates: typecheck, unit tests, build, bundle budget,
   module-size budget, runtime contract, and browser QA for desktop and mobile.
7. Enterprise readiness includes observability, rollback evidence, provenance, dependency auditing, and
   documented ownership.
8. Brand assets must preserve the current Valdrics logo geometry used by the public site. Color, lighting,
   depth, and 3D/material treatment may be adapted for the new frontend, but the mark itself must remain
   recognizably the same logo. Do not replace it with abstract diamonds, generic cloud marks, or temporary
   symbols.

### Phase 0: Freeze Topology and Ownership

Goal: make the repo topology unambiguous before more visual migration.

- Keep source ownership in `frontend/`, with route-local components under the route they serve and shared
  primitives only when reuse is proven.
- Finish the managed rename from `dashboard/` to `frontend/` across CI, scripts, Docker, docs, CODEOWNERS,
  evidence, and runbooks.
- Update any remaining dashboard-named commands to frontend-named commands.
- Add a repo hygiene check that fails if new production source appears under `dashboard/`.

Acceptance:

- `git ls-files` no longer shows deployable source under `dashboard/`.
- CI paths, Dockerfile, Wrangler config, docs, and scripts use `frontend/`.
- `scripts/verify_frontend_runtime_contract.py` and `scripts/check_frontend_hygiene.py` pass in CI.

### Phase 1: Codify the Valdrics Design System

Goal: migrate the `new_frontend/` look into production with fidelity, without copying brittle handoff
code.

- Extract tokens from the reference: dark shell, cyan/green/yellow/red semantic colors, compact badges,
  status rails, 8px or smaller radii, dense dashboard spacing, mono data labels, and lucide-style icons.
- Use `frontend/static/valdrics_icon.png` as the primary Valdrics logo source of truth.
  `frontend/static/valdrics_icon1.png` and `frontend/static/valdrics_wordmark.svg` stay as supporting
  shell assets. Any future 3D treatment must be a material/color treatment derived from the primary PNG,
  not a new logo.
- Create or consolidate production primitives only when they remove repeated implementation, for example:
  stat chips, filter tabs, status badges, action buttons, empty states, and detail rows.
- Keep visible text domain-specific and workflow-oriented. Do not add marketing hero copy inside app routes.
- Audit CSS for one-hue drift and mobile overflow after each slice.
- Record any visual or interaction deviation from `new_frontend/` as an intentional decision with the
  blocker that forced it, such as a missing backend contract, security constraint, or accessibility fix.

Acceptance:

- Shared tokens live in the existing app CSS/token system, not copied `new_frontend` variables.
- New components stay below preferred module budgets where practical.
- Browser screenshots show no text overlap, no horizontal overflow, and no giant mobile artifacts.
- Browser QA includes a visual fidelity check against the relevant `new_frontend` source.

### Phase 2: Migrate Authenticated App Surfaces by Risk

Goal: modernize high-value authenticated workflows first while preserving real contracts.

Order:

1. Authenticated shell: navigation, top bar, brand mark, mobile collapse, active-route state.
2. Approvals: queue stats, backed filters, expandable cards, approve/deny actions.
3. Dashboard overview: map `valdrics-dashboard-page.svelte`, `SpendTopologyChart`, `PolicyHealthRings`,
   `InventoryPanel`, and `SavingsPanel` into the real dashboard route and current loader contracts.
4. Onboarding: migrate `valdrics-onboarding-page.svelte` and `valdrics-onboarding.html` into the real
   provider setup flow without bypassing existing cloud/account validation.
5. Savings: migrate `valdrics-savings-page.svelte` into `frontend/src/routes/savings`.
6. Inventory/connections: reconcile `valdrics-inventory-page.svelte` with the existing connections and
   inventory data model. If a useful handoff capability has no backend support, create a real backend
   contract with tests before shipping the UI; do not fake resource fields in the frontend.
7. Policies/settings: migrated `valdrics-policies-page.svelte` into the existing `/settings`
   enforcement control plane while keeping `/enforcement/*` contracts and feature gates.
8. Audit, billing, public docs, and auxiliary routes: modernize only after the primary workflow routes are
   contract-safe and visually coherent.

Current status:

- Authenticated shell: migrated and verified.
- Approvals: migrated and verified.
- Dashboard overview: migrated and verified.
- Onboarding: migrated and verified.
- Savings: migrated and verified.
- Inventory/connections: migrated with a real backend inventory contract.
- Policies/settings: next recommended migration slice.

Acceptance per route:

- Data model is typed in a route-local model file or shared contract module.
- Every API path is a real production path or a documented edge proxy path.
- Tests cover loading, entitlement states, failed API responses, and primary user actions.
- Browser QA covers desktop, mobile, filter/expand/action states, and console/page errors.

### Phase 3: Backend Contract Alignment

Goal: make the frontend honest about backend capability.

- Treat `new_frontend/valdrics-backend-requirements.html` as product input, not implementation fact.
- For each migrated control, identify the current backend route, schema, auth role, timeout, rate limit,
  and error contract.
- If the backend contract is missing, either create the backend contract in the same slice with tests or
  omit the UI control.
- Maintain edge proxy discipline: browser code should not call private backend origins directly.

Acceptance:

- Frontend tests assert exact endpoint paths and payload shapes for mutating actions.
- Backend unit tests cover any newly created contract.
- OpenAPI/client contract checks pass.

### Phase 4: Security, Identity, and CSP Hardening

Goal: ship an app that can pass enterprise security review.

- Preserve existing auth/session guards and route protection.
- Continue enforcing strict CSP with nonce mode, no `unsafe-inline`, no Svelte transition directives, and
  no raw HTML without sanitization.
- Require explicit `button type`, safe external links, and edge proxy-only API origins.
- Keep dependency override policy intentional and documented.
- Add security-focused browser checks for login/logout, protected routes, entitlement denial, and stale
  session behavior.

Acceptance:

- `scripts/check_frontend_hygiene.py` passes.
- Security headers are asserted in tests.
- `pnpm audit --audit-level=high` is a CI gate.
- Threat-sensitive flows have negative tests, not only happy paths.

### Phase 5: Performance and Reliability Gates

Goal: keep the modern UI fast under enterprise scale.

- Continue bundle budgets and module-size budgets.
- Lazy-load charts and any heavy visualization libraries.
- Put slow, non-critical data behind resilient client hydration with timeouts and useful error states.
- Add route-specific Playwright performance coverage for dashboard, approvals, onboarding, and savings.
- Track Core Web Vitals on production traffic where available.

Acceptance:

- `frontend/scripts/check-bundle-size.mjs` passes.
- Route browser tests assert no blank canvas, no horizontal overflow, and no console/page errors.
- Each primary route has loading, empty, partial-error, and success states.

### Phase 6: Release, Provenance, and Rollback

Goal: make rollout auditable and reversible without keeping legacy code.

- Deploy one route slice at a time behind existing entitlement or release controls, not duplicate legacy
  routes.
- Generate release evidence: command outputs, screenshots, bundle metrics, audit output, and runtime
  contract output.
- Keep rollback at the artifact/deployment level, not by preserving old `dashboard/` source.
- Update runbooks and managed cutover artifacts with final `frontend/` paths.

Acceptance:

- Release checklist links to CI runs and evidence artifacts.
- Docker/Cloudflare deployment paths are both tested or explicitly scoped.
- Post-deploy smoke checks cover public app, authenticated shell, dashboard, and approvals.

### Phase 7: Delete Handoff and Legacy Surfaces

Goal: remove ambiguity once migration is complete.

- Delete migrated handoff files from `new_frontend/` after each file is either implemented or rejected in
  an evidence note.
- Delete `new_frontend/` entirely when the disposition register reaches zero remaining actionable files.
- Remove dashboard-named scripts/tests/docs after their frontend replacements are validated.
- Keep only production code, evidence, and architecture records.

Acceptance:

- No deployable or handoff-only source remains outside `frontend/`.
- ADR and runbooks agree on path names, adapter target, runtime target, and verification commands.
- CI fails on reintroduction of legacy app roots.

## Route Migration Definition of Done

Each migrated route must satisfy all of the following before it is marked complete:

1. Uses the production `frontend/` route and the real backend contract.
2. Uses Svelte 5-compatible patterns and typed data models.
3. Contains no unsupported controls, fake navigation, stubs, or placeholder data.
4. Passes lint, Svelte check, focused Vitest, production build, bundle budget, module budget, hygiene, and
   runtime contract checks.
5. Has Playwright or browser QA evidence for desktop and mobile.
6. Documents any intentionally rejected handoff behavior.

## Enforcement Controls

1. `pnpm -C frontend lint` must pass (format + ESLint).
2. `pnpm -C frontend check` must pass (SvelteKit sync + svelte-check).
3. `pnpm -C frontend test:unit -- --run` must pass (Vitest).
4. `pnpm -C frontend build` must succeed (Vite/SvelteKit).
5. `pnpm -C frontend check:bundle` must pass (bundle budgets).
6. CI runs `pnpm audit --audit-level=high` for frontend dependencies.

## Testable Assertions

1. Sidebar navigation is instantaneous (routes do not block on long API calls).
2. Heavy charting code does not inflate initial JS bundles (lazy-loaded).
3. Requests that exceed timeouts fail fast with user-friendly errors.
4. Security headers are present on server-rendered responses.

## Consequences

- Dependency upgrades require lockfile regeneration (and registry access) to keep CI `--frozen-lockfile` reliable.
- CSP may need iterative tuning if new integrations require additional `connect-src`/`img-src` domains.
- Performance budgets will force intentional decisions when introducing new large dependencies.
