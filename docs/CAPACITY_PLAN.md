# Valdrics Capacity Plan (2026)

This plan outlines the infrastructure targets for scaling the platform.

This remains an active planning and documentation-contract artifact. Keep it
aligned with the supported deployment model and current runtime assumptions.
Commercial tier scope and the public plan ladder live in
`docs/architecture/tiering-2026.md` and must stay aligned with runtime
entitlements.

The current supported operating profile is Koyeb-managed services for staging
and production. The Helm + Terraform (AWS/EKS) material remains the future
scale path for when managed-platform limits or cost structure no longer fit the
platform.
This capacity plan keeps the phrase `future scale path` explicit because the
Helm/EKS profile is not the current operating default.

## 1. Metric Targets

| Tier | Users | DB Size | Req/sec | AWS Adapters |
| --- | --- | --- | --- | --- |
| **Startup** | 100 - 1k | 10GB | 50 | 1k |
| **Growth** | 1k - 10k | 100GB | 500 | 10k |
| **Enterprise**| 10k - 100k| 1TB | 5k | 100k |

## 2. Scaling Strategies

### Database (PostgreSQL / AWS RDS profile)
- **Current**: Managed PostgreSQL with connection-pool budgeting enforced at the application layer.
- **10k Users**: Introduce read scaling for analytics/reporting and continue partition/index governance for high-volume tables.
- **100k Users**: Move large analytical workloads off the primary OLTP path or introduce a horizontally scalable analytical store.

### Compute Workloads (API + Workers)
- **Current**: Koyeb-managed API, worker, and dashboard services with Redis-backed coordination.
- **Current production topology**: Koyeb API and worker services must be promoted together from the same immutable release tag, and the dashboard must be promoted from the matching dashboard image tag.
- **1k+ Users**: Scale API and worker pools independently and keep scheduler-driven sweeps bounded.
- **Auto-Scaling**: Koyeb service autoscaling by CPU today; Horizontal Pod Autoscaling (HPA) based on CPU and queue depth when the future Helm profile is activated.

### LLM Consumption
- **Strategy**: Leverage the **LLM Provider Waterfall** to prevent 429 errors.
- **Cache**: Increase Redis cache TTL for repeated analysis results.
