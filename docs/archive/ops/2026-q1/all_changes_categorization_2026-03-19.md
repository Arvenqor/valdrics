# All Changes Categorization (2026-03-19)

Snapshot:
- Captured at: `2026-03-19T00:00:00Z`
- Base commit: `e42d0578fa69f0d1da075d41d430f75aa892a368`
- Pending paths: `151`
- Branch at snapshot: `chore/all-changes-categorization-2026-03-19`

## Track BQ: Frontend Public Shell, Dashboard UX, and Browser Coverage
Scope:
- Consolidate the public shell, route wiring, auth callback, savings and ops surfaces, and shared dashboard components in one frontend review lane.
- Keep Playwright, browser, and component coverage with the UI and route changes they exercise.
- Include frontend runtime helpers such as chart loading, lazy loading, persona, and route protection behavior in the same track.

Paths:
- `dashboard/e2e/a11y.spec.ts`
- `dashboard/e2e/critical-paths.spec.ts`
- `dashboard/e2e/landing.test.ts`
- `dashboard/playwright.config.ts`
- `dashboard/scripts/check-bundle-size.mjs`
- `dashboard/src/app.html`
- `dashboard/src/hooks.server.test.ts`
- `dashboard/src/hooks.server.ts`
- `dashboard/src/lib/api.ts`
- `dashboard/src/lib/auth/publicAuthIntent.test.ts`
- `dashboard/src/lib/auth/publicAuthIntent.ts`
- `dashboard/src/lib/chartjs.ts`
- `dashboard/src/lib/components/CloudLogo.svelte`
- `dashboard/src/lib/components/CommandPalette.svelte`
- `dashboard/src/lib/components/FindingsTable.svelte`
- `dashboard/src/lib/components/LandingHero.motion.surface.shell.css`
- `dashboard/src/lib/persona.ts`
- `dashboard/src/lib/routeProtection.test.ts`
- `dashboard/src/routes/+layout.svelte`
- `dashboard/src/routes/+page.server.ts`
- `dashboard/src/routes/+page.svelte`
- `dashboard/src/routes/+page.ts`
- `dashboard/src/routes/admin/health/+page.svelte`
- `dashboard/src/routes/auth/callback/+server.ts`
- `dashboard/src/routes/auth/callback/callback-route.server.test.ts`
- `dashboard/src/routes/billing/billing-page.css`
- `dashboard/src/routes/billing/billingPage.test.ts`
- `dashboard/src/routes/dashboard.load.test.ts`
- `dashboard/src/routes/layout-public-menu.svelte.test.ts`
- `dashboard/src/routes/layout/AppAuthenticatedShell.svelte`
- `dashboard/src/routes/layout/PublicSiteShell.svelte`
- `dashboard/src/routes/onboarding/OnboardingPageViewContent.flow.css`
- `dashboard/src/routes/onboarding/OnboardingPageViewContent.provider.css`
- `dashboard/src/routes/onboarding/OnboardingVerifySuccessSection.svelte`
- `dashboard/src/routes/ops/OpsPageViewContent.svelte`
- `dashboard/src/routes/page.server.motion.test.ts`
- `dashboard/src/routes/page.svelte.browser.spec.ts`
- `dashboard/src/routes/savings/SavingsPageViewContent.svelte`
- `dashboard/src/routes/settings/SettingsWorkflowAutomationCard.svelte`
- `dashboard/static/azure-logo.png`
- `dashboard/static/favicon.png`
- `dashboard/static/valdrics_icon.png`
- `dashboard/tests/e2e/dashboard_sniper.test.ts`
- `dashboard/tests/e2e/scenarios.test.ts`
- `tests/integration/test_critical_paths.py`
- `dashboard/e2e/authenticated-shell.spec.ts`
- `dashboard/e2e/support/`
- `dashboard/src/lib/chartjsRuntime.test.ts`
- `dashboard/src/lib/chartjsRuntime.ts`
- `dashboard/src/lib/lazyComponent.test.ts`
- `dashboard/src/lib/lazyComponent.ts`
- `dashboard/src/lib/testing/`
- `dashboard/src/routes/dashboard/`
- `scripts/run_dashboard_playwright_backend.py`

Notes:
- This track is intentionally frontend-heavy and spans both public and authenticated browser surfaces.

## Track BR: Runtime Platform, Health, HTTP, and API Contract Hardening
Scope:
- Group backend runtime plumbing changes around health checks, HTTP helpers, dependency checks, and API security or validation coverage.
- Keep app-level and test harness changes that affect server bootstrap or request handling in the same platform review lane.
- Separate runtime contracts from deployment automation and documentation work so operational risk is easier to review.

Paths:
- `app/shared/core/health.py`
- `app/shared/core/http.py`
- `app/shared/core/runtime_dependencies.py`
- `tests/api/test_api_endpoints.py`
- `tests/api/test_endpoints_health_cors.py`
- `tests/api/test_endpoints_security_auth.py`
- `tests/api/test_endpoints_validation_jobs.py`
- `tests/api/test_endpoints_zombies_scan_requests.py`
- `tests/api/test_health.py`
- `tests/conftest.py`
- `tests/core/test_http.py`
- `tests/integration/test_edge_cases.py`
- `tests/unit/core/test_env_contract_templates.py`
- `tests/unit/core/test_health_deep.py`
- `tests/unit/core/test_health_extra.py`
- `tests/unit/core/test_health_missing_coverage.py`
- `tests/unit/core/test_runtime_dependencies.py`
- `tests/unit/governance/settings/conftest.py`
- `tests/unit/governance/settings/test_connections.py`
- `tests/unit/governance/settings/test_identity_settings_direct_branches.py`
- `tests/unit/notifications/test_workflow_dispatchers.py`

Notes:
- This track is the server-runtime and API-contract slice of the batch.

## Track BS: Release, Deployment, Managed Environment, and Supply-Chain Automation
Scope:
- Batch release image publishing, Koyeb/runtime environment templates, managed deployment generation, and supply-chain automation together.
- Keep build-system and dependency lock updates with the deployment and provenance scripts they affect.
- Carry the matching deployment-contract and supply-chain verification suites in the same release-engineering lane.

Paths:
- `.env.example`
- `Makefile`
- `koyeb-worker.yaml`
- `koyeb.yaml`
- `prod.env.template`
- `pyproject.toml`
- `scripts/generate_enforcement_stress_evidence.py`
- `scripts/generate_feature_enforceability_matrix.py`
- `scripts/generate_managed_deployment_artifacts.py`
- `scripts/generate_managed_migration_env.py`
- `scripts/generate_managed_runtime_env.py`
- `scripts/generate_pricing_benchmark_register.py`
- `scripts/generate_provenance_manifest.py`
- `scripts/validate_runtime_env.py`
- `scripts/verify_enforcement_stress_evidence.py`
- `scripts/verify_managed_deployment_bundle.py`
- `tests/unit/ops/test_generate_managed_deployment_artifacts.py`
- `tests/unit/ops/test_generate_managed_migration_env.py`
- `tests/unit/ops/test_generate_managed_runtime_env.py`
- `tests/unit/ops/test_production_deployment_contracts.py`
- `tests/unit/ops/test_release_artifact_templates_pack.py`
- `tests/unit/ops/test_validate_runtime_env.py`
- `tests/unit/ops/test_verify_enforcement_stress_evidence.py`
- `tests/unit/ops/test_verify_managed_deployment_bundle.py`
- `tests/unit/supply_chain/test_feature_enforceability_matrix.py`
- `tests/unit/supply_chain/test_generate_enforcement_stress_evidence.py`
- `tests/unit/supply_chain/test_supply_chain_provenance.py`
- `tests/unit/supply_chain/test_supply_chain_provenance_workflow.py`
- `uv.lock`
- `.github/workflows/publish-release-images.yml`
- `.python-version`

Notes:
- This track is release-engineering and deployment-tooling focused.

## Track BT: Documentation, Legal, Finance Evidence, and Operational Runbooks
Scope:
- Consolidate contributor, licensing, trademark, finance evidence, disposition, key rotation, and runbook updates together.
- Keep evidence generation and documentation verification scripts with the docs and templates they govern.
- Carry the matching ops and selector coverage for finance and evidence workflows in the same operational review lane.

Paths:
- `CLA.md`
- `CONTRIBUTING.md`
- `DEPLOYMENT.md`
- `README.md`
- `TRADEMARK_POLICY.md`
- `docs/CAPACITY_PLAN.md`
- `docs/DEPLOYMENT.md`
- `docs/ROLLBACK_PLAN.md`
- `docs/architecture/overview.md`
- `docs/guides/aws_scp_setup.md`
- `docs/licensing.md`
- `docs/ops/evidence/enforcement_failure_injection_TEMPLATE.json`
- `docs/ops/incident_response_runbook.md`
- `docs/ops/key-rotation-drill-2026-02-27.md`
- `docs/runbooks/disaster_recovery.md`
- `docs/runbooks/emergency_disconnect.md`
- `docs/runbooks/production_env_checklist.md`
- `scripts/finance_committee_packet_common.py`
- `scripts/generate_enforcement_failure_injection_evidence.py`
- `scripts/generate_finance_committee_packet.py`
- `scripts/generate_finance_committee_packet_assumptions.py`
- `scripts/generate_finance_telemetry_snapshot.py`
- `scripts/generate_key_rotation_drill_evidence.py`
- `scripts/generate_local_dev_env.py`
- `scripts/generate_pkg_fin_policy_decisions.py`
- `scripts/generate_valdrics_disposition_register.py`
- `scripts/verify_documentation_runtime_contracts.py`
- `scripts/verify_enforcement_failure_injection_evidence.py`
- `scripts/verify_monthly_finance_evidence_refresh.py`
- `scripts/verify_valdrics_disposition_freshness.py`
- `tests/unit/ops/test_documentation_runtime_contracts.py`
- `tests/unit/ops/test_generate_enforcement_failure_injection_evidence.py`
- `tests/unit/ops/test_generate_finance_committee_packet.py`
- `tests/unit/ops/test_generate_finance_committee_packet_assumptions.py`
- `tests/unit/ops/test_generate_key_rotation_drill_evidence.py`
- `tests/unit/ops/test_generate_local_dev_env.py`
- `tests/unit/ops/test_runtime_evidence_generators.py`
- `tests/unit/ops/test_verify_documentation_runtime_contracts.py`
- `tests/unit/ops/test_verify_enforcement_failure_injection_evidence.py`
- `tests/unit/ops/test_verify_key_rotation_drill_evidence.py`
- `tests/unit/ops/test_verify_monthly_finance_evidence_refresh.py`
- `tests/unit/ops/test_verify_valdrics_disposition_freshness.py`
- `docs/runbooks/koyeb_release_promotion.md`
- `tests/unit/enforcement/test_key_rotation_drill_selectors.py`
- `tests/unit/ops/test_generate_pkg_fin_policy_decisions.py`

Notes:
- This track is documentation and operational-evidence heavy rather than product-runtime heavy.

## Batching Decision
Decision:
- Merge as one consolidated PR.

Reasoning:
- The snapshot spans frontend shell changes, runtime contracts, deployment automation, and operational documentation or evidence work, but all of it is part of one live worktree batch.
- Splitting this state further would create artificial PR overhead while still crossing the same deployment, browser, health, and evidence contracts.
- The issue split keeps the review lanes explicit without fragmenting the delivery batch.
