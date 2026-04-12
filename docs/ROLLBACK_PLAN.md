# Rollback Plan

This plan covers the supported unified platform deployment surface.

## Rollback Principles

- Application rollback uses immutable Artifact Registry promotion refs or prior known-good Cloud Run revisions.
- Database rollback is not assumed to be universally reversible.
- For destructive or forward-only schema changes, backup/restore is the primary recovery path.

## 1. Database Schema Recovery

Use `alembic downgrade -1` only after confirming the specific migration is
reversible and covered by the one-step downgrade smoke test in CI.

For destructive or uncertain migrations:

1. Restore from the most recent compatible backup/restore point.
2. Redeploy an application revision that matches that schema state.
3. Re-run validation on `/health/live` and `/health`.

## 2. Cloud Run Rollback

For the supported production profile:

1. Redeploy the prior known-good digest-pinned Artifact Registry release for the API.
2. Re-run the matching Cloud Run Job image when batch parity matters.
3. Confirm `/health/live`, `/health`, and key dashboard/API flows after rollback.
4. Re-check internal metrics scraping via `/_internal/metrics`.
5. Confirm the rollback used immutable release artifacts rather than an ad hoc rebuild.

## 3. Infrastructure Rollback

For Terraform-managed infrastructure:

1. Review the last known-good revision in Git.
2. Apply that reviewed Terraform state intentionally; do not assume blind reversibility.
3. Validate Cloud Run, Cloud Tasks, Cloud Scheduler, Cloudflare Pages, and Supabase connectivity before reopening traffic.

## 4. Emergency Soft Kill

To stop scheduler-driven background processing without tearing down the whole API:

1. Disable or pause the relevant Cloud Scheduler job instead of re-enabling any in-process scheduler path.
2. Keep Cloud Run custom audiences aligned with `API_URL` so internal OIDC delivery remains valid after rollback.
3. Verify logs show scheduler ownership remains external.
