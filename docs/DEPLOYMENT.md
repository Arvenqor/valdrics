# Valdrics Deployment Guide

Last verified: **2026-04-10**

## Current supported production deployment profile

The current supported production deployment profile is:

`Google Cloud Run + Cloudflare Pages + Supabase`

This is the active operating model for both staging and production.

Current runtime note:

- the supported GCP profile delegates public API throttling to Cloudflare edge rate limiting and keeps `RATELIMIT_ENABLED=false` inside the API runtime
- the public API path is `Cloudflare proxied hostname -> GCP external HTTPS load balancer -> Cloud Run`
- Cloud Armor allows only Cloudflare origin CIDRs to reach the API load balancer backend
- the API container binds `0.0.0.0:$PORT` and runs one Uvicorn process per Cloud Run instance
- scale is owned by Cloud Run request concurrency and instance counts, not a runtime `WEB_CONCURRENCY` knob

## Archived Future Scale Reference

Historical future-scale references may remain in explicitly archived or
reference-only material, but they are not part of the supported day-to-day
runtime profile.

## Shared Runtime Contract

All supported environments must satisfy these checks:

- `ENVIRONMENT=<staging|production>`
- explicit public URLs: `API_URL=https://...` and `FRONTEND_URL=https://...`
- `PLATFORM_RUNTIME_PROFILE=gcp`
- `OBSERVABILITY_BACKEND=gcp`
- `PUBLIC_API_RATE_LIMITING_BACKEND=cloudflare`
- `RATELIMIT_ENABLED=false`
- `CIRCUIT_BREAKER_DISTRIBUTED_STATE=false`
- `API_URL` must be the Cloudflare-proxied custom hostname, not the raw `run.app` URL
- `GCP_CLOUD_RUN_SERVICE_NAME` must identify the Cloud Run API service used for internal Cloud Tasks delivery
- Cloud Run custom audiences must include `API_URL` so Cloud Tasks and Cloud Scheduler can authenticate directly to the internal `run.app` service URL while preserving the public API audience contract
- liveness probe: `/health/live`
- dependency health: `/health`
- internal metrics: `/_internal/metrics`
- immutable backend artifact promotion
- any forecasting or TLS break-glass expiry must remain within the configured max break-glass window

Machine-readable source of truth:

- `scripts/managed_deployment_contract.py`
- `.runtime/<environment>.report.json`
- `.runtime/<environment>.migrate.report.json`
- `.runtime/deploy/<environment>/deployment.report.json`
- `.runtime/deploy/<environment>/operator-handoff.md`
- `.runtime/deploy/managed-release-blockers.md`

## Supported Release Surface

Repository evidence:

- runtime and deployment generators:
  - `scripts/generate_managed_runtime_env.py`
  - `scripts/generate_managed_migration_env.py`
  - `scripts/generate_managed_deployment_artifacts.py`
  - `scripts/verify_managed_deployment_bundle.py`
  - `scripts/verify_codebase_audit_report.py`
- single operator release workflow:
  - `.github/workflows/release-unified-platform.yml`
- reusable immutable backend artifact workflow:
  - `.github/workflows/publish-artifact-registry-images.yml`
- reusable unified deployment workflow:
  - `.github/workflows/deploy-unified-platform.yml`
- dashboard runtime verifier:
  - `scripts/verify_dashboard_runtime_contract.py`
- generated deployment artifacts:
  - `.runtime/deploy/<environment>/unified-platform-manifest.json`
  - `.runtime/deploy/<environment>/secret-manager-runtime-secrets.json`
  - `.runtime/deploy/<environment>/cloudflare-pages-env.json`
  - `.runtime/deploy/<environment>/artifact-registry-release.json`
  - `.runtime/deploy/<environment>/terraform.runtime.auto.tfvars.json`

Expected posture:

- backend API runs on Google Cloud Run
- public API ingress is terminated at a Google external HTTPS load balancer
- Cloudflare owns the public API DNS record, origin TLS mode, and edge rate limiting
- Cloud Armor blocks direct origin access that does not come from Cloudflare origin CIDRs
- request-adjacent async work runs through Cloud Tasks
- scheduled triggers are owned by Cloud Scheduler
- long-running jobs execute on Cloud Run Jobs
- frontend deploys to Cloudflare Pages
- database, auth, and storage run on Supabase
- backend artifacts are promoted from Artifact Registry using digest-pinned refs
- production promotion reuses the same tested backend artifact that passed staging

## Core Operator Flow

1. Generate or refresh the runtime and migration bundles.
2. Run `.github/workflows/release-unified-platform.yml` for staging first.
3. Publish one immutable backend artifact and keep the digest-pinned `artifact-registry-release.json` / `artifact-registry-release.env` as release evidence.
4. Let `.github/workflows/deploy-unified-platform.yml` materialize `.runtime/<environment>.env`, `.runtime/<environment>.migrate.env`, and `.runtime/deploy/<environment>/...` from the GitHub environment contract plus the promoted digest refs.
5. Let the reusable deploy workflow run `scripts/generate_managed_deployment_artifacts.py` and `scripts/verify_managed_deployment_bundle.py` before any Terraform apply.
6. Upload the non-secret managed deployment evidence bundle from the deploy workflow as the operator audit artifact for the environment.
7. Verify the dashboard runtime contract with `scripts/verify_dashboard_runtime_contract.py` and render the cross-environment blocker rollup with `scripts/render_managed_release_blocker_summary.py` when doing preflight or incident-repair review.
8. Let the release workflow apply infrastructure and run Alembic from the generated `.runtime/<environment>.migrate.env`.
9. Deploy the dashboard from the generated `cloudflare-pages-env.json`.
10. Validate `/health/live`, `/health`, internal scheduler dispatch, Cloud Tasks delivery, and Cloudflare Pages to API connectivity.

## Verification Checklist

- `/health/live` returns `200`
- `/health` reflects dependency state accurately
- `/_internal/metrics` is reachable only by internal callers
- Cloud Scheduler remains the only owner of scheduled trigger delivery
- rollback path is documented for the unified profile
- release promotion uses digest-pinned Artifact Registry refs only

## Related Runbooks

- `docs/runbooks/unified_platform_release.md`
- `docs/runbooks/production_env_checklist.md`
- `docs/ROLLBACK_PLAN.md`
- `docs/runbooks/disaster_recovery.md`
- `docs/runbooks/tenant_data_lifecycle.md`
