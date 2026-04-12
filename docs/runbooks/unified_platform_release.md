# Unified Platform Release Runbook

This runbook defines the target operating model for the unified platform:

- backend runtime on Google Cloud Run
- async work on Cloud Tasks
- scheduled work on Cloud Scheduler
- long-running work on Cloud Run Jobs
- backend images in Artifact Registry
- frontend deploys on Cloudflare Pages
- database, auth, and storage on Supabase

## 1. Run the single release pipeline

Use:

- `.github/workflows/release-unified-platform.yml`

Required workflow inputs:

- `release_tag`
- optional `git_ref`
- `promote_production`

Required repository/environment variables:

- `ARTIFACT_REGISTRY_PROJECT_ID`
- `ARTIFACT_REGISTRY_REGION`
- `ARTIFACT_REGISTRY_REPOSITORY`

The release pipeline validates the release contract, publishes one digest-pinned
backend image, deploys staging first, and promotes production only when
`promote_production=true`. Production receives the same `api_promotion_ref` that
passed staging.

Implementation detail:

- `.github/workflows/publish-artifact-registry-images.yml` is reusable and records
  `release/artifact-registry-release.json` plus `release/artifact-registry-release.env`
- `.github/workflows/deploy-unified-platform.yml` is reusable and applies one
  environment at a time with the digest-pinned `api_promotion_ref`, explicit
  `batch_promotion_ref`, and the immutable `release_tag`

## 2. Prepare the GitHub environment contract

For each environment (`staging`, `production`) define:

- repository/environment variables for non-secret platform control-plane values
- repository/environment secrets for provider credentials plus the runtime secret payload

At minimum the deployment workflow expects:

- `vars.GCP_PROJECT_ID`
- `vars.GCP_REGION`
- `vars.CLOUDFLARE_ACCOUNT_ID`
- `vars.CLOUDFLARE_ZONE_ID`
- `vars.CLOUDFLARE_PAGES_PROJECT_NAME`
- `vars.CLOUDFLARE_PAGES_PRODUCTION_BRANCH`
- `vars.SUPABASE_ORGANIZATION_ID`
- `vars.SUPABASE_PROJECT_NAME`
- `vars.SUPABASE_REGION`
- `vars.RUNTIME_PLAIN_ENV_JSON`
- `secrets.CLOUDFLARE_API_TOKEN`
- `secrets.SUPABASE_ACCESS_TOKEN`
- `secrets.SUPABASE_DATABASE_PASSWORD`
- `secrets.RUNTIME_SECRET_ENV_JSON`

`RUNTIME_PLAIN_ENV_JSON` and `RUNTIME_SECRET_ENV_JSON` must be JSON objects with
string values. The reusable deploy workflow materializes `.runtime/<environment>.env`
from those two inputs, derives `.runtime/<environment>.migrate.env` from the
materialized `DATABASE_URL`, then generates and verifies the managed deployment
bundle before Terraform or Alembic run.

## 3. Apply infrastructure and deploy the app

Reusable implementation:

- `.github/workflows/deploy-unified-platform.yml`

Required workflow inputs:

- `environment`
- `release_tag`
- `api_promotion_ref`
- `batch_promotion_ref`
- optional `git_ref`

The release pipeline performs:

1. Google Cloud authentication with Workload Identity Federation
2. Materialize `.runtime/<environment>.env`, `.runtime/<environment>.migrate.env`, and `.runtime/deploy/<environment>/...`
3. Verify the managed deployment bundle
4. Upload the non-secret deployment evidence bundle as an artifact for operator auditability
5. Terraform apply for GCP runtime + API load balancer, Cloudflare Pages/DNS/WAF, and Supabase project/settings
6. Alembic migration from `.runtime/<environment>.migrate.env`
7. Dashboard build from `.runtime/deploy/<environment>/cloudflare-pages-env.json`
8. Cloudflare Pages direct upload deploy
9. API liveness smoke check

## 4. Terraform source of truth

The Terraform root in `terraform/` owns:

- Artifact Registry repository
- Secret Manager secrets
- Cloud Run API service
- GCP external HTTPS load balancer for the public API
- Cloud Armor origin guard for Cloudflare-only API load balancer ingress
- Cloud Run batch job
- Cloud Tasks queue
- Cloud Scheduler jobs
- Cloudflare API DNS record, strict origin TLS posture, and edge rate limiting rules
- Pages project shell in Cloudflare
- Supabase project and managed settings

Terraform inputs are environment-specific and should be supplied through
the generated `.runtime/deploy/<environment>/terraform.runtime.auto.tfvars.json`
plus provider credentials that remain in GitHub environment secrets.

## 5. Release rules

- Do not rebuild a second backend image for production.
- Promote the same `api_promotion_ref` that passed staging.
- Prefer `.github/workflows/release-unified-platform.yml` for operator-triggered
  releases; direct reusable workflow dispatch is for incident repair only.
- Keep Cloud Run scheduler ownership external. Do not re-enable the in-process scheduler in the API.
- Keep internal task and scheduler endpoints authenticated with Google-signed identity tokens.
- Treat this runbook as the only supported release path for staging and production.

## 6. Post-release checks

After each deploy confirm:

- `${API_URL}/health/live` returns `200`
- Cloud Scheduler jobs show successful recent executions
- Cloud Tasks queue dispatches successfully
- Cloud Run Job executions are launching and emitting logs
- Cloudflare Pages serves the new frontend deployment
- Supabase auth site URL matches the public frontend URL
