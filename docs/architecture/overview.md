# Valdrics Architecture Overview

Valdrics is implemented as a modular Python web platform with a SvelteKit
dashboard, a FastAPI API, and a unified managed deployment profile built on
Google Cloud Run, Cloudflare Pages, and Supabase.

## Architectural Shape

- Backend: modular monolith organized under `app/modules/`
- Shared kernel: auth, config, logging, DB, rate-limit, tracing, metrics, and runtime services under `app/shared/`
- Frontend: SvelteKit dashboard under `dashboard/`
- Infrastructure source of truth: Terraform under `terraform/`

## Module Boundary Model

Each module generally follows:

| Component | Responsibility |
|---|---|
| `domain/` | Business logic and orchestration |
| `adapters/` | External providers, SDKs, and infrastructure integrations |
| `api/` | FastAPI routes, request/response models, and transport concerns |

The `domain -> adapters -> api` split is a boundary target, not a hard purity
guarantee today. Some domain packages still contain pragmatic cross-layer
imports, so this document describes the intended shape of the system, not a
claim of perfect isolation.

## Runtime Dependencies

- Database/auth/storage: Supabase + PostgreSQL
- Async orchestration: Cloud Tasks
- Scheduled orchestration: Cloud Scheduler
- Long-running managed work: Cloud Run Jobs
- Observability target: Google Cloud Operations
- Artifact promotion: Artifact Registry

## Supported Deployment Profile

The supported deployment surface is the unified platform:

- Google Cloud Run for the public API
- Cloudflare Pages for the frontend
- Supabase for data and auth
- Terraform for infrastructure control
- GitHub Actions for artifact publish and deployment orchestration

## Archived Future Scale Reference

Archived future-scale material is retained for reference only and is not part
of the supported operating contract or current production path.

## Security and Tenancy

- tenant-aware DB session controls are implemented in `app/shared/db/session.py`
- auth and request security controls live in `app/shared/core/auth.py` and related middleware
- internal metrics are exposed on `/_internal/metrics` and must remain non-public
- scheduler ownership is external; the in-process scheduler stays disabled in the supported deployment model

## Operational References

- deployment guidance: `docs/DEPLOYMENT.md`
- unified release runbook: `docs/runbooks/unified_platform_release.md`
- rollback guidance: `docs/ROLLBACK_PLAN.md`
- disaster recovery: `docs/runbooks/disaster_recovery.md`
