# Scripts Inventory

This directory is intentionally mixed: some files are command-line entrypoints,
and some are internal helper modules imported by those entrypoints.

`PLAN.md` is the canonical product and shipping plan. This directory is an
execution surface for that plan, not a second roadmap.

## What Belongs Here

- `verify_*`: repo contracts, admission checks, and quality gates wired into
  CI, pre-commit, evidence packs, or regression tests.
- `generate_*`, `render_*`, `validate_*`: managed deployment, release-bundle,
  and runtime-contract tooling.
- `run_*`, `load_*`, `smoke_test_*`, `capture_*`: controlled operational or
  evidence runners used by workflows, runbooks, or test-backed evidence packs.
- Helper modules such as `env_generation_common.py`,
  `managed_deployment_contract.py`, `plugin_registry_verification.py`, and
  `async_heartbeat.py`: these may have few direct path references because they
  are imported by other active scripts.

## What Does Not Belong Here

- Unsupported delivery-path tooling for retired platforms.
- Retired compatibility stubs whose only job is to preserve an old entrypoint.
- One-off scripts with no active owner, no current supported runbook/workflow
  path, and no test-backed operational contract.
- Ad hoc refactor helpers, migration graph scratch tools, and local debugging
  probes that were useful for one cleanup or incident but are not part of the
  supported managed-platform operating model.

## Current Cleanup Rule

Keep a script in the repo only if at least one of these is true:

1. It is called by a live workflow, `Makefile` target, pre-commit hook, or
   documented supported runbook.
2. It is imported by another active script as a helper module.
3. It is part of an evidence/verification contract covered by tests.
4. It is a current break-glass or operational tool for the supported managed
   platform or the active product runtime.

Otherwise, archive or remove it instead of carrying dead entrypoints forward.

## Retention Notes For Low-Reference Scripts

Some scripts have intentionally low path-reference counts because they are
manual maintenance or break-glass tools rather than CI entrypoints. They stay
only when they still have one of the contracts above.

- Break-glass and incident controls:
  `deactivate_aws.py`, `emergency_disconnect.py`, `purge_simulation_data.py`.
- Database and partition maintenance:
  `manage_partitions.py`, `run_archival_setup.py`, `archive_partitions.sql`.
- Local/dev data and pricing bootstrap:
  no extra legacy seed helpers remain; local bootstrap uses
  `bootstrap_local_sqlite_schema.py`.

If one of these scripts loses both tests and supported operational context, it
should be archived or removed in the next cleanup pass.
