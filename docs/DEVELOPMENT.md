# Valdrics Development Guide

This document provides detailed instructions for developers and contributors who wish to run Valdrics locally, contribute to the codebase, or deploy a self-hosted instance.

## Prerequisites

- Python 3.12.x
- `uv` (recommended for local backend workflows)
- Docker with Compose v2 (`docker compose`)
- An AWS account with:
  - AWS CUR configured to deliver Parquet reports to S3
  - Resource Explorer 2 enabled
- Cost Explorer is optional (Valdrics ingestion path is CUR + Resource Explorer 2)
- An LLM API key (OpenAI, Anthropic, Google, or Groq)

### Runtime Dependency Policy (Prod/Staging)

- `tiktoken` is required for accurate token accounting and LLM budget enforcement.
- The Cloud Trace exporter is required in staging/production.
- Cloud Run ingests structured JSON logs from `stdout`/`stderr`; no separate log-export client path is part of the supported runtime contract.
- `prophet` is required by default in staging/production.
- Temporary break-glass fallback is allowed only with:
  - `FORECASTER_ALLOW_HOLT_WINTERS_FALLBACK=true`
  - `FORECASTER_BREAK_GLASS_REASON` (auditable justification)
  - `FORECASTER_BREAK_GLASS_EXPIRES_AT` (ISO-8601 UTC expiry inside the configured max break-glass window)

## Getting Started (Local Development)

### 1. Clone & Configure

```bash
git clone https://github.com/Valdrics/valdrics.git
cd valdrics
uv sync --python 3.12 --dev
```

For fast local sqlite development, generate the local runtime profile and bootstrap the
current ORM schema instead of replaying the historical Alembic chain:

```bash
make env-dev
make bootstrap-local-db
```

`.env.dev` is local-only, runs with `TESTING=false`, and must not be used in staging/production.

Local development only: for the docker compose path with PostgreSQL, generate the compose-specific local env file:

```bash
make env-compose
```

`.env.compose.dev` is local-only, ignored by git, and is the expected input for the
checked-in `docker compose` workflow. The checked-in compose topology is cacheless by
default and is the only supported local compose path in this repository. If you need
provider keys locally, edit the generated file and add values such as `OPENAI_API_KEY`,
`GROQ_API_KEY`, or `SLACK_BOT_TOKEN`.

### 2. Start the Stack

Fast local sqlite path:

```bash
make dev
```

If `.env.dev` exists, `make dev` auto-loads it and bootstraps the local sqlite schema before
starting the API.

Local development only: default dockerized Postgres path with the checked-in cacheless compose topology:

```bash
make docker-up
```

Optional observability stack:

```bash
make observability
```

Local URLs:

- SQLite + Vite dev path: dashboard on `http://localhost:5174`
- Docker compose path: dashboard on `http://localhost:3000`
- Grafana when observability is enabled: `http://localhost:3005`

### 3. Open the Dashboard

- **API Docs:** http://localhost:8000/docs
- **Dashboard (sqlite + Vite dev):** http://localhost:5174
- **Dashboard (docker compose):** http://localhost:3000

### 4. Connect Your AWS Account

The dashboard will guide you through deploying our read-only IAM role via CloudFormation or Terraform. Takes 60 seconds.

## Contributing

Please refer to `CONTRIBUTING.md` for guidelines on how to contribute to Valdrics.
