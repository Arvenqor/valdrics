# Valdrics Capacity Plan (2026)

This plan tracks the scaling assumptions for the supported operating model.

The current supported operating profile is the unified platform:

- Google Cloud Run for the public API
- Cloud Tasks for durable async dispatch
- Cloud Run Jobs for long-running managed work
- Cloudflare Pages for the dashboard edge
- Supabase for PostgreSQL, Auth, and Storage

Archived reference material may still exist in-repo for historical or design
context, but there is no parallel capacity track outside the supported runtime
contract and the canonical phase sequence in `PLAN.md`.

## 1. Metric Targets

| Tier | Users | DB Size | Req/sec | Provider Connections |
| --- | --- | --- | --- | --- |
| **Startup** | 100 - 1k | 10GB | 50 | 1k |
| **Growth** | 1k - 10k | 100GB | 500 | 10k |
| **Enterprise** | 10k - 100k | 1TB | 5k | 100k |

## 2. Scaling Strategies

### Database (Supabase / PostgreSQL)

- **Current**: Supabase-managed PostgreSQL with application-side connection budgeting and query hygiene.
- **10k Users**: tighten index discipline, archive old data aggressively, and move heavy reporting reads off the interactive path.
- **100k Users**: split analytical workloads from the core OLTP path and use dedicated reporting pipelines.

### Compute Workloads (API + Async + Batch)

- **Current**: Google Cloud Run API, Cloud Tasks dispatch, Cloud Run Jobs for long-running sweeps, Cloud Scheduler for cron ownership.
- **1k+ Users**: scale API concurrency and max instances independently of batch job resources.
- **Auto-scaling**: Cloud Run instance scaling for interactive traffic, queue-based backpressure via Cloud Tasks, and explicit resource sizing for Cloud Run Jobs.

### Frontend Edge

- **Current**: Cloudflare Pages serves the SvelteKit dashboard globally.
- **Growth**: preserve static asset caching at the edge and keep API traffic origin-bound.

### LLM Consumption

- **Strategy**: leverage provider selection and fairness controls before increasing hard infrastructure spend.
- **Guardrails**: use per-tenant and global abuse protections before widening concurrency.
