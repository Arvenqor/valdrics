from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_codeowners_exists_and_assigns_default_owner() -> None:
    codeowners = (REPO_ROOT / "CODEOWNERS").read_text(encoding="utf-8")
    assert "* @daretechie" in codeowners


def test_readme_avoids_stale_hardcoded_platform_counts() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Valdrics" in text
    assert "Optimize Cloud Value, Not Just Cost" in text
    assert "Python 3.12" in text
    assert "11 zombie-detection plugins" not in text
    assert "11 zombie detection plugins" not in text


def test_readme_frames_supported_managed_platform_and_archived_references() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "Supported Managed Platform" in text
    assert "Archived Future-Scale Reference" in text
    assert "Helm Chart (archived, not part of the supported deployment)" in text
    assert "Local development only:" in text
    assert "Unified Platform Migration Target" not in text
    assert "Future Scale Path" not in text


def test_readme_does_not_overclaim_raw_k8s_manifests() -> None:
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "| **K8s Manifests** | `k8s/` |" not in text


def test_soc2_controls_reference_current_artifacts() -> None:
    text = (REPO_ROOT / "docs/SOC2_CONTROLS.md").read_text(encoding="utf-8")
    assert "CODEOWNERS" in text
    assert "`app/shared/core/logging.py`" in text
    assert "`docs/runbooks/disaster_recovery.md`" in text
    assert "`docs/ROLLBACK_PLAN.md`" in text
    assert "`docs/FULL_CODEBASE_AUDIT.md`" in text
    assert "Infrastructure: Helm chart" not in text
    assert "`terraform/modules/db/main.tf`" not in text
    assert "AWS RDS backup retention and HA posture" not in text
    assert "`app/core/logging.py`" not in text
    assert "`docs/DR_RUNBOOK.md`" not in text
    assert "`technical_due_diligence.md`" not in text


def test_full_codebase_audit_doc_is_time_bound_and_does_not_overclaim() -> None:
    text = (REPO_ROOT / "docs/FULL_CODEBASE_AUDIT.md").read_text(encoding="utf-8")
    assert "time-bound snapshot" in text
    assert "first-party Python, TypeScript, and Svelte source" in text
    assert "live verification scripts remain the source of truth" in text
    assert "mixed secret model" in text
    assert "RLS enforcement plus documented exemptions" in text
    assert "5358 tests collected" not in text
    assert "No TODO/FIXME/XXX/HACK in app" not in text
    assert "No issues." not in text


def test_retention_policy_matches_supported_erasure_controls() -> None:
    text = (REPO_ROOT / "docs/policies/data_retention.md").read_text(encoding="utf-8")
    assert "/api/v1/audit/data-erasure-request" in text
    assert "background job retention" in text.lower()
    assert "Audit logs | Automated retention purge" in text
    assert "AUDIT_LOG_RETENTION_DAYS" in text
    assert "plan-aware retention purge" in text
    assert "resource_type=cost_records_retention" in text
    assert "resource_type=audit_logs_retention" in text
    assert "Supabase-managed backups and point-in-time recovery" in text
    assert "Provider-managed retention outside repository automation" in text
    assert "AWS RDS backups (Terraform profile)" not in text
    assert "`terraform/modules/db/main.tf`" not in text


def test_rollback_and_recovery_docs_match_supported_platforms() -> None:
    rollback = (REPO_ROOT / "docs/ROLLBACK_PLAN.md").read_text(encoding="utf-8")
    recovery = (REPO_ROOT / "docs/runbooks/disaster_recovery.md").read_text(
        encoding="utf-8"
    )
    failover = (REPO_ROOT / "docs/architecture/failover.md").read_text(encoding="utf-8")
    deployment = (REPO_ROOT / "docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    capacity = (REPO_ROOT / "docs/CAPACITY_PLAN.md").read_text(encoding="utf-8")
    roadmap = (REPO_ROOT / "docs/roadmap.md").read_text(encoding="utf-8")
    tiering = (REPO_ROOT / "docs/architecture/tiering-2026.md").read_text(
        encoding="utf-8"
    )
    db_overview = (
        REPO_ROOT / "docs/architecture/database_schema_overview.md"
    ).read_text(encoding="utf-8")

    assert "backup/restore" in rollback.lower()
    assert "Cloud Run Rollback" in rollback
    assert "Artifact Registry" in rollback
    assert "Cloud Scheduler job" in rollback
    assert "Cloud Run custom audiences" in rollback

    assert "Google Cloud Run" in recovery
    assert "Cloud Run Jobs" in recovery
    assert "Cloudflare Pages" in recovery
    assert "Supabase" in recovery
    assert "Artifact Registry" in recovery
    assert "aws_role_to_assume" not in recovery
    assert "secondary_db_endpoint" not in recovery
    assert "regional-failover" not in recovery
    assert "regional_failover" not in recovery
    assert "automated_secondary_region_failover" not in recovery
    assert "FAILOVER_AWS_ROLE_TO_ASSUME" not in recovery

    assert "Cloudflare" in failover
    assert "Supabase" in failover
    assert "Google Cloud Run" in failover
    assert "Artifact Registry" in failover
    assert "manual_restore_redeploy_reroute" in failover
    assert "aws_role_to_assume" not in failover
    assert "secondary_db_endpoint" not in failover
    assert "regional-failover" not in failover
    assert "regional_failover" not in failover
    assert "automated_secondary_region_failover" not in failover
    assert "FAILOVER_AWS_ROLE_TO_ASSUME" not in failover

    assert "Current supported production deployment profile" in deployment
    assert "Google Cloud Run + Cloudflare Pages + Supabase" in deployment
    assert "Cloudflare edge rate limiting" in deployment
    assert "GCP external HTTPS load balancer" in deployment
    assert "Cloud Run custom audiences" in deployment
    assert "release-unified-platform.yml" in deployment
    assert "publish-artifact-registry-images.yml" in deployment
    assert "deploy-unified-platform.yml" in deployment
    assert "artifact-registry-release.json" in deployment
    assert "cloudflare-pages-env.json" in deployment

    assert "current supported operating profile is the unified platform" in capacity
    assert "Google Cloud Run" in capacity
    assert "Cloud Tasks" in capacity
    assert "Cloud Run Jobs" in capacity
    assert "Cloudflare Pages" in capacity
    assert "Supabase" in capacity

    assert "active planning document" in roadmap
    assert "reports/roadmap/" in roadmap
    assert "Current Focus" in roadmap
    assert "bootstrap-only sqlite dev" in roadmap
    assert "managed bundle verification" in roadmap

    assert "Permanent public proof lane" in tiering
    assert "dashboard/src/lib/pricing/publicPlans.ts" in tiering
    assert "app/shared/core/pricing.py" in tiering
    assert "One-step forward/rollback smoke" in db_overview
    assert "backup/restore is the primary rollback path" in db_overview


def test_architecture_overview_does_not_overclaim_domain_purity_or_raw_k8s() -> None:
    text = (REPO_ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
    assert "Zero external dependencies" not in text
    assert "`k8s/`" not in text
    assert "boundary target" in text
    assert "Google Cloud Run" in text
    assert "Cloudflare Pages" in text
    assert "Supabase" in text
    assert "Artifact Registry" in text
    assert "retained for reference only" in text


def test_ci_no_longer_treats_helm_as_supported_release_surface() -> None:
    ci_text = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    precommit_text = (REPO_ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")

    assert "Validate Helm Chart" not in ci_text
    assert "helm-lint:" not in makefile_text
    assert "helm-template:" not in makefile_text
    assert "helm-install:" not in makefile_text
    assert "helm-upgrade:" not in makefile_text
    assert "helm-uninstall:" not in makefile_text
    assert "helmlint" not in precommit_text
    assert "files: ^helm/" not in precommit_text


def test_enforcement_preprovision_runbook_scopes_helm_as_archived_reference() -> None:
    text = (
        REPO_ROOT / "docs/runbooks/enforcement_preprovision_integrations.md"
    ).read_text(encoding="utf-8")

    assert "failurePolicy: Fail" in text
    assert "`failurePolicy: Fail` requires API HA" in text
    assert "Archived self-managed Helm reference" in text
    assert "Helm deployment profile (recommended)" not in text


def test_benchmark_alignment_profile_uses_active_admission_review_evidence() -> None:
    text = (
        REPO_ROOT / "docs/ops/benchmark_alignment_profiles_2026-02-27.md"
    ).read_text(encoding="utf-8")

    assert "Kubernetes AdmissionReview guidance profile" in text
    assert (
        "Archived self-managed Helm reference remains outside the supported deployment contract."
        in text
    )
    assert "tests/unit/enforcement/enforcement_api_cases_part01.py" in text
    assert "tests/unit/enforcement/enforcement_api_cases_part02.py" in text
    assert "test_enforcement_endpoint_wrappers_cover_preflight_and_k8s_review_branches" in text
    assert "Runtime/Helm contract in repository" not in text
    assert "tests/unit/ops/" not in text


def test_incident_and_production_runbooks_match_unified_platform_contract() -> None:
    incident = (REPO_ROOT / "docs/runbooks/incident_response.md").read_text(
        encoding="utf-8"
    )
    production = (REPO_ROOT / "docs/runbooks/production_env_checklist.md").read_text(
        encoding="utf-8"
    )
    workflow = (REPO_ROOT / "docs/integrations/workflow_automation.md").read_text(
        encoding="utf-8"
    )
    soc2 = (REPO_ROOT / "docs/SOC2_CONTROLS.md").read_text(encoding="utf-8")

    assert "Settings -> Notifications" in incident
    assert "strict SaaS mode" in incident
    assert "Cloudflare edge rate limiting is healthy" in incident
    assert "local drill or explicit break-glass shared-state cache backend" in incident
    assert "specified in `SLACK_CHANNEL_ID`" not in incident
    assert "optional cache backends are either healthy or falling back cleanly" not in incident

    assert "Python 3.12.x" in production
    assert ".python-version" in production
    assert "API_URL=https://" in production
    assert "FRONTEND_URL=https://" in production
    assert "PUBLIC_API_RATE_LIMITING_BACKEND=cloudflare" in production
    assert "RATELIMIT_ENABLED=false" in production
    assert "CIRCUIT_BREAKER_DISTRIBUTED_STATE=false" in production
    assert "SUPABASE_ANON_KEY=..." in production
    assert "PLATFORM_RUNTIME_PROFILE=gcp" in production
    assert "OBSERVABILITY_BACKEND=gcp" in production
    assert "OBSERVABILITY_BACKEND=otlp" not in production
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in production
    assert "SENTRY_DSN" not in production
    assert "CLOUDFLARE_ZONE_ID" in production
    assert "INTERNAL_METRICS_AUTH_TOKEN=<32+ char secret>" in production
    assert "EXPOSE_API_DOCUMENTATION_PUBLICLY=false" in production
    assert "generate_managed_runtime_env.py" in production
    assert "generate_managed_migration_env.py" in production
    assert "generate_managed_deployment_artifacts.py" in production
    assert "verify_managed_deployment_bundle.py" in production
    assert "release-unified-platform.yml" in production
    assert "publish-artifact-registry-images.yml" in production
    assert "deploy-unified-platform.yml" in production
    assert "artifact-registry-release.json" in production
    assert "cloudflare-pages-env.json" in production
    assert "unified-platform-manifest.json" in production
    assert "Cloud Run custom audiences" in production
    assert (
        "reusable deploy workflow migration step succeeds from `.runtime/production.migrate.env`"
        in production
    )

    assert "env channel routing (`SLACK_CHANNEL_ID`) is blocked" in workflow
    assert "self-host or break-glass-only paths" in workflow
    assert "`app/modules/governance/api/v1/settings/account.py`" in soc2
    assert "| CC6.4 |" in soc2 and "Implemented" in soc2


def test_secret_rotation_runbook_keeps_redis_break_glass_only() -> None:
    text = (REPO_ROOT / "docs/runbooks/secret_rotation_emergency.md").read_text(
        encoding="utf-8"
    )

    assert "ENFORCEMENT_APPROVAL_TOKEN_SECRET" in text
    assert "PAYSTACK_SECRET_KEY" in text
    assert (
        "`REDIS_URL` credentials only if an explicit local drill or break-glass shared-state backend is enabled"
        in text
    )
    assert (
        "optional local-only or break-glass `REDIS_URL` credentials, if explicitly configured"
        not in text
    )


def test_partition_archival_helpers_match_runtime_maintenance_path() -> None:
    sql_text = (REPO_ROOT / "scripts/archive_partitions.sql").read_text(
        encoding="utf-8"
    )
    script_text = (REPO_ROOT / "scripts/run_archival_setup.py").read_text(
        encoding="utf-8"
    )
    assert "PartitionMaintenanceService" in script_text
    assert "archive_old_partitions" in script_text
    assert "cost_records_archive" in sql_text
    assert "ux_cost_records_archive_id_recorded_at" in sql_text
    assert "RAISE NOTICE" not in sql_text


def test_runbooks_with_high_operational_risk_are_covered_by_contract_guard() -> None:
    script_text = (
        REPO_ROOT / "scripts/verify_documentation_runtime_contracts.py"
    ).read_text(encoding="utf-8")
    assert "docs/FULL_CODEBASE_AUDIT.md" in script_text
    assert "docs/SOC2_CONTROLS.md" in script_text
    assert "docs/policies/data_retention.md" in script_text
    assert "docs/ops/benchmark_alignment_profiles_2026-02-27.md" in script_text
    assert "docs/runbooks/enforcement_preprovision_integrations.md" in script_text
    assert "docs/runbooks/partition_maintenance.md" in script_text
    assert "docs/runbooks/secret_rotation_emergency.md" in script_text
    assert "docs/roadmap.md" in script_text
    assert "docs/architecture/tiering-2026.md" in script_text
