# Failover and Availability Architecture

## Current State

The supported platform provides managed availability at the service layer and
uses manual restore/redeploy/reroute for full-environment recovery.

Repository-owned recovery expectations:

- Cloudflare remains the public edge and routing layer.
- Supabase remains the managed database/auth/storage dependency.
- Google Cloud Run and Cloud Run Jobs provide immutable, revision-based runtime recovery.
- `.github/workflows/deploy-unified-platform.yml` is the supported redeploy path.
- `/health/live` and dependency-aware `/health` remain the required cutover checks.
- the repository-owned regional recovery mode is `manual_restore_redeploy_reroute`
- recovery evidence should record `regional_recovery_mode=manual_restore_redeploy_reroute`

## Availability Building Blocks

- Edge/frontend: Cloudflare Pages
- API: Google Cloud Run
- Async queue: Cloud Tasks
- Scheduled control plane: Cloud Scheduler
- Batch work: Cloud Run Jobs
- Database/auth/storage: Supabase
- Backend artifact promotion: Artifact Registry

## Failure Handling Model

### In-Region Failures

- Cloud Run recovers by shifting traffic to a healthy revision.
- Cloud Tasks retries durable work under queue policy.
- Supabase remains the managed dependency for database continuity.

### Cross-Region / Full-Environment Failures

Cross-region recovery currently uses one supported path:

1. Restore data from Supabase backup/restore or point-in-time recovery.
2. Re-apply Terraform for the target environment.
3. Redeploy the exact tested Artifact Registry release through the unified deployment workflow.
4. Re-point Cloudflare traffic only after `/health/live` and `/health` both pass.

## What This Document Does Not Claim

- No AWS warm-standby cutover is part of the supported production contract.
- No AWS role-assumption or secondary database endpoint dependency exists in the active failover model.
- Autonomous provider-driven failover without operator-triggered restore and redeploy is not claimed here.
