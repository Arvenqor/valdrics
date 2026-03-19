# Koyeb Release Promotion Runbook

Use this runbook for both staging and production when Valdrics is deployed on
Koyeb-managed services.

## Deployment Model

- API service on Koyeb
- worker service on Koyeb
- dashboard service on Koyeb
- immutable container image promotion
- separate staging and production apps or service groups

## Release Inputs

Before promotion, generate the managed bundle:

```bash
uv run python scripts/generate_managed_runtime_env.py --environment staging
uv run python scripts/generate_managed_migration_env.py --environment staging
uv run python scripts/generate_managed_deployment_artifacts.py --environment staging --runtime-env-file .runtime/staging.env --release-tag <release-tag> --api-image-digest <sha256:...> --dashboard-image-digest <sha256:...>
uv run python scripts/verify_managed_deployment_bundle.py --environment staging
```

Do the same for production when promoting the same release tag and the same
published image digests.

Before generating the deployment bundle, publish the images with:

- `.github/workflows/publish-release-images.yml`

That workflow uploads:

- `release/ghcr-release.json`
- `release/ghcr-release.env`

Recommended GitHub repository or organization variable:

- `GHCR_NAMESPACE=valdrics`

Set that variable if the repository owner differs from the GHCR package namespace
you want to publish into.

Use `API_IMAGE_DIGEST` and `DASHBOARD_IMAGE_DIGEST` from that artifact when
generating the Koyeb release bundle.

Example:

```bash
set -a
source release/ghcr-release.env
set +a

make deploy \
  ENVIRONMENT=staging \
  VERSION="${RELEASE_TAG}" \
  API_IMAGE_DIGEST="${API_IMAGE_DIGEST}" \
  DASHBOARD_IMAGE_DIGEST="${DASHBOARD_IMAGE_DIGEST}"
```

Artifacts used during promotion:

- `.runtime/deploy/<environment>/koyeb-api.yaml`
- `.runtime/deploy/<environment>/koyeb-worker.yaml`
- `.runtime/deploy/<environment>/koyeb-dashboard-env.json`
- `.runtime/deploy/<environment>/koyeb-secrets.json`
- `.runtime/deploy/<environment>/koyeb-release.json`

## Promotion Rules

1. Build immutable API and dashboard images once in GHCR.
2. Promote the same tested API/dashboard digests from staging to production.
3. Do not rebuild a different image for production after staging signoff.
4. Apply migrations before promoting the release if the release requires a new schema head.
5. Roll back by redeploying the previous known-good digest-pinned `promotion_ref`.

## Required Koyeb Checks

For the target environment:

1. API service healthy on `/health/live`
2. Dashboard healthy on `/`
3. Worker started cleanly and consuming from Redis
4. API can reach PostgreSQL and Redis
5. Dashboard can reach `PUBLIC_API_URL`
6. `/_internal/metrics` stays internal-only or token-gated

## Staging Signoff

Staging is ready to promote only if:

1. migrations succeeded
2. API, worker, and dashboard use the same release tag family and digest-pinned `promotion_ref` values from `koyeb-release.json`
3. the AWS-first operator flow passes from `docs/runbooks/aws_first_operator_flow.md`
4. rollback was verified for the previous release tag

## Production Promotion

1. verify `.runtime/deploy/production/koyeb-release.json`
2. apply `.runtime/deploy/production/koyeb-secrets.json`
3. apply `.runtime/deploy/production/koyeb-dashboard-env.json`
4. run migrations with `.runtime/production.migrate.env`
5. deploy API using `services.api.promotion_ref`
6. deploy worker using `services.worker.promotion_ref`
7. deploy dashboard using `services.dashboard.promotion_ref`
8. run production smoke checks

## Post-Deploy Smoke

- `GET /health/live`
- `GET /health`
- dashboard login/onboarding path
- one tenant-scoped authenticated API request
- `/_internal/metrics` access contract
- one background-job execution path
- one savings or reporting read path

## Rollback Trigger

Roll back immediately if:

- `/health/live` fails after deploy
- queue consumption stops
- dashboard cannot reach API
- migration leaves the app on a broken schema/app combination
- tenant-scoped authenticated requests regress
