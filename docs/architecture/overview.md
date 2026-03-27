# Valdrics Architecture Overview

Valdrics is implemented as a modular Python web platform with a SvelteKit
dashboard, a FastAPI API, shared infrastructure services, and deployment
profiles for both Koyeb-managed services today and Kubernetes as a future scale
path.

## Architectural Shape

- Backend: modular monolith organized under `app/modules/`
- Shared kernel: common auth, config, logging, DB, rate-limit, tracing, metrics, and runtime services under `app/shared/`
- Frontend: SvelteKit dashboard under `dashboard/`
- Infrastructure: Helm chart under `helm/valdrics/` and Terraform modules under `terraform/`

## Module Boundary Model

Each module generally follows:

| Component | Responsibility |
|---|---|
| `domain/` | Business logic and orchestration |
| `adapters/` | External providers, SDKs, and infrastructure integrations |
| `api/` | FastAPI routes, request/response models, and transport concerns |

The `domain -> adapters -> api` split is a boundary target, not a hard purity
guarantee today. Some domain packages still contain pragmatic cross-layer
imports, so this document should be read as the intended shape of the system,
not a claim that every module has perfect isolation.

## Runtime Dependencies

- Database/auth context: PostgreSQL plus application auth/token validation
- Cache/distributed coordination: Redis
- Observability: structured logging, Prometheus metrics, OpenTelemetry tracing
- Workers: Celery-based background execution with scheduler controls

## Supported Deployment Profiles

### Koyeb-Managed Services

The current supported deployment surface is Koyeb-managed services promoted from
immutable container images. The managed bundle under `.runtime/deploy/` defines:

- API service runtime contract
- worker service runtime contract
- dashboard public env contract
- release metadata for image promotion

### Helm Chart

The repository also retains a Helm chart in `helm/valdrics/` as a future scale
path. It defines:

- multi-replica API deployment
- worker deployment
- ingress and internal metrics protections
- production defaults for security context and anti-affinity

### Managed Koyeb Bundle

The supported Koyeb release surface is the generated managed bundle under
`.runtime/deploy/<environment>/`. That path captures environment-specific
secrets, dashboard public env, and immutable release metadata together.

## Security and Tenancy

- tenant-aware DB session controls are implemented in `app/shared/db/session.py`
- auth and request security controls live in `app/shared/core/auth.py` and related middleware
- internal metrics are exposed on `/_internal/metrics` and blocked from public ingress in the Helm profile

## Operational References

- deployment guidance: `docs/DEPLOYMENT.md`
- rollback guidance: `docs/ROLLBACK_PLAN.md`
- disaster recovery: `docs/runbooks/disaster_recovery.md`
