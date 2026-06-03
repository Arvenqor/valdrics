# Phased Shipping Helper

The canonical phase sequence now lives in `PLAN.md`.

This file is not a second roadmap. It only maps the active delivery work to
local and release execution helpers.

## Working Rule

- use `PLAN.md` for scope, sequencing, and exit gates
- use this file for command-level shortcuts
- use `docs/runbooks/unified_platform_release.md` for staging and production
  cutover operations

## Local Helper Commands

### Repo baseline

```bash
make ship-baseline
```

Use for:

- contract changes
- workflow changes
- docs and runbook updates
- repo-wide cleanup

### Changed backend surface

```bash
make ship-backend-slice \
  PY_PATHS="app/... scripts/... tests/..." \
  PYTEST_TARGETS="tests/unit/... tests/unit/..."
```

### Changed frontend/public surface

```bash
make ship-frontend-slice
```

Or:

```bash
make ship-frontend-slice FRONTEND_URL=http://localhost:5174
```

### Managed deployment bundle preflight

```bash
make ship-managed-bundle \
  ENVIRONMENT=staging \
  VERSION=<release-tag> \
  API_PROMOTION_REF=<repo@sha256:...> \
  BATCH_PROMOTION_REF=<repo@sha256:...>
```

## Release Rule

- do not treat local helper commands as a replacement for the release workflow
- staging and production releases still go through
  `.github/workflows/release-unified-platform.yml`
