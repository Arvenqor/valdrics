# Disaster Recovery Runbook

This runbook reflects the supported unified platform:

- Google Cloud Run for the backend API
- Cloud Run Jobs for long-running managed work
- Cloud Tasks for async dispatch
- Cloudflare Pages for the dashboard edge
- Supabase for PostgreSQL, Auth, and Storage

## Recovery Posture

- Cloudflare remains the public edge and DNS control plane.
- Supabase backup/restore and point-in-time recovery remain the database recovery dependency.
- Artifact Registry provides immutable release artifacts for backend rollback and rebuild.
- `.github/workflows/deploy-unified-platform.yml` is the supported redeploy path.
- Repository-owned regional recovery is still a manual restore/redeploy/reroute procedure.
- Recovery evidence must record `regional_recovery_mode=manual_restore_redeploy_reroute`.
- Repository-owned recovery success requires `/health/live` and dependency-aware `/health` to pass before traffic is reopened.

## 1. Supabase / Database Failure

### Detection

- `/health` returns `503`
- application logs show database connectivity failures
- Cloud Tasks dispatch succeeds but application work cannot persist state

### Recovery Steps

1. Confirm the failing profile is using the expected Supabase project.
2. Check Supabase project status, database availability, and point-in-time recovery options.
3. Restore from the latest compatible backup/restore point when fail-forward is unsafe.
4. Re-run migrations only after validating the restored schema baseline.
5. Validate tenant-scoped auth and query paths after recovery.

## 2. Backend Runtime Failure

### Detection

- Cloud Run revision health degrades
- Cloud Run Jobs fail to launch or complete
- Cloud Tasks queue backlog grows unexpectedly

### Recovery Steps

1. Roll back the Cloud Run API service to the prior known-good immutable release artifact.
2. Roll back the matching Cloud Run Job image when batch behavior changed in the failing release.
3. Confirm Cloud Tasks delivery resumes successfully.
4. Validate `/health/live`, `/health`, and internal scheduler dispatch endpoints before reopening traffic.

## 3. Frontend Edge Failure

### Detection

- dashboard fails to render from Cloudflare Pages
- dashboard-to-API traffic fails while backend health remains green

### Recovery Steps

1. Roll back to the prior known-good Cloudflare Pages deployment.
2. Confirm `PRIVATE_API_ORIGIN`, `PUBLIC_API_URL`, `PUBLIC_SUPABASE_URL`, and `PUBLIC_SUPABASE_ANON_KEY` still match the active environment contract.
3. Re-validate core dashboard login, navigation, and operator views.

## 4. Full-Environment Restore / Reroute

Use this path when the active environment must be rebuilt from clean infrastructure.

1. Restore or recreate the Supabase project and database from the latest compatible recovery point.
2. Re-apply Terraform for the environment.
3. Redeploy the exact tested Artifact Registry promotion ref through `.github/workflows/deploy-unified-platform.yml`.
4. Rebuild or redeploy the Cloudflare Pages frontend for the same environment contract.
5. Verify `/health/live`, `/health`, Cloud Tasks dispatch, Cloud Run Job launch, and dashboard-to-API connectivity before reopening traffic.

## 5. Secret Exposure or Rotation Event

If recovery is triggered by secret compromise rather than infrastructure loss:

1. Rotate the affected values in Secret Manager, GitHub environment secrets, Cloudflare, or Supabase as applicable.
2. Redeploy or recycle affected runtime revisions.
3. Validate that old credentials are rejected and new ones are in effect.

## Post-Recovery Validation

1. `/health/live` returns `200`.
2. `/health` returns dependency details without new critical failures.
3. Cloud Tasks dispatch resumes only when intended.
4. Cloud Run Jobs launch and emit healthy logs.
5. Cloudflare Pages serves the expected frontend and authenticates against the restored Supabase/Auth contract.
