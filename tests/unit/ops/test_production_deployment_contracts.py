from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_release_artifacts_are_immutable_and_workflows_target_unified_platform() -> (
    None
):
    makefile_text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    publish_workflow = (
        REPO_ROOT / ".github/workflows/publish-artifact-registry-images.yml"
    ).read_text(encoding="utf-8")
    deploy_workflow = (
        REPO_ROOT / ".github/workflows/deploy-unified-platform.yml"
    ).read_text(encoding="utf-8")
    release_workflow = (
        REPO_ROOT / ".github/workflows/release-unified-platform.yml"
    ).read_text(encoding="utf-8")

    assert "VERSION must be set to an immutable release tag" in makefile_text
    assert (
        "scripts/generate_managed_deployment_artifacts.py --environment $(ENVIRONMENT)"
        in makefile_text
    )
    assert "docs/runbooks/unified_platform_release.md" in makefile_text
    assert "workflow_call:" in publish_workflow
    assert "google-github-actions/auth@" in publish_workflow
    assert "artifact-registry-release.json" in publish_workflow
    assert "immutable_artifact_registry_promotion" in publish_workflow
    assert "workflow_call:" in deploy_workflow
    assert "release_tag:" in deploy_workflow
    assert "batch_promotion_ref:" in deploy_workflow
    assert "generate_managed_runtime_env.py" in deploy_workflow
    assert "generate_managed_migration_env.py" in deploy_workflow
    assert "generate_managed_deployment_artifacts.py" in deploy_workflow
    assert "verify_managed_deployment_bundle.py" in deploy_workflow
    assert "actions/upload-artifact@" in deploy_workflow
    assert "terraform -chdir=terraform apply -auto-approve tfplan" in deploy_workflow
    assert "terraform.runtime.auto.tfvars.json" in deploy_workflow
    assert "secrets.DATABASE_URL" not in deploy_workflow
    assert "secrets.SUPABASE_ANON_KEY" not in deploy_workflow
    assert "wrangler pages deploy" in deploy_workflow
    assert "/health/live" in deploy_workflow
    assert "needs.publish.outputs.api_promotion_ref" in release_workflow
    assert "needs.publish.outputs.batch_promotion_ref" in release_workflow
    assert "deploy-production:" in release_workflow


def test_dashboard_runtime_requires_explicit_origin_configuration() -> None:
    server_text = (REPO_ROOT / "dashboard" / "server.node.mjs").read_text(
        encoding="utf-8"
    )
    dockerfile_text = (REPO_ROOT / "Dockerfile.dashboard").read_text(encoding="utf-8")

    assert "process.env.ORIGIN" in server_text
    assert "process.env.HOST_HEADER" in server_text
    assert "process.env.PROTOCOL_HEADER" in server_text
    assert "req.headers.host ||" not in server_text
    assert 'CMD ["node", "server.node.mjs"]' in dockerfile_text


def test_backend_dockerfile_healthcheck_uses_curl_liveness_probe() -> None:
    dockerfile_text = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8").lower()
    entrypoint_text = (
        (REPO_ROOT / "scripts/docker-entrypoint.sh").read_text(encoding="utf-8").lower()
    )

    assert "healthcheck" in dockerfile_text
    assert "/health/live" in dockerfile_text
    assert "curl --fail --silent --show-error" in dockerfile_text
    assert "${port:-8000}/health/live" in dockerfile_text
    assert "urllib.request" not in dockerfile_text
    assert "procps" in dockerfile_text
    assert 'cmd ["/bin/sh", "/app/scripts/docker-entrypoint.sh"]' in dockerfile_text
    assert "validate_runtime_dependencies" in entrypoint_text
    assert 'port="${port:-8000}"' in entrypoint_text
    assert "uvicorn app.main:app" in entrypoint_text
    assert "--workers" not in entrypoint_text


def test_deployment_docs_match_unified_platform_contracts() -> None:
    ops_doc = (REPO_ROOT / "docs/DEPLOYMENT.md").read_text(encoding="utf-8")
    release_runbook = (
        REPO_ROOT / "docs/runbooks/unified_platform_release.md"
    ).read_text(encoding="utf-8")
    production_checklist = (
        REPO_ROOT / "docs/runbooks/production_env_checklist.md"
    ).read_text(encoding="utf-8")

    assert "/health/live" in ops_doc
    assert "configured max break-glass window" in ops_doc
    assert "Google Cloud Run + Cloudflare Pages + Supabase" in ops_doc
    assert "Cloudflare edge rate limiting" in ops_doc
    assert "GCP external HTTPS load balancer" in ops_doc
    assert ".github/workflows/release-unified-platform.yml" in ops_doc
    assert ".github/workflows/publish-artifact-registry-images.yml" in ops_doc
    assert ".github/workflows/deploy-unified-platform.yml" in ops_doc
    assert "release-unified-platform.yml" in release_runbook
    assert "Artifact Registry" in release_runbook
    assert "Cloudflare Pages" in release_runbook
    assert "Supabase" in release_runbook
    assert "release-unified-platform.yml" in production_checklist
    assert "publish-artifact-registry-images.yml" in production_checklist
    assert "deploy-unified-platform.yml" in production_checklist
    assert "PUBLIC_API_RATE_LIMITING_BACKEND=cloudflare" in production_checklist
    assert "CLOUDFLARE_ZONE_ID" in production_checklist


def test_root_legacy_deployment_files_are_removed() -> None:
    assert not (REPO_ROOT / "DEPLOYMENT.md").exists()
    assert not (REPO_ROOT / "koyeb.yaml").exists()
    assert not (REPO_ROOT / "koyeb-worker.yaml").exists()
    assert not (REPO_ROOT / "prod.env.template").exists()
    assert not (REPO_ROOT / "docker-compose.prod.yml").exists()


def test_unsupported_regional_failover_operator_artifacts_are_removed() -> None:
    assert not (REPO_ROOT / ".github/workflows/regional-failover.yml").exists()
    assert not (REPO_ROOT / "scripts/run_regional_failover.py").exists()
    assert not (REPO_ROOT / "scripts/configure_github_oidc_aws_credentials.py").exists()


def test_archived_helm_contract_test_is_removed_from_active_ops_surface() -> None:
    assert not (REPO_ROOT / "tests/unit/ops/test_enforcement_webhook_helm_contract.py").exists()


def test_frontend_ci_node_version_matches_dashboard_container() -> None:
    ci_text = (REPO_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    sbom_text = (REPO_ROOT / ".github/workflows/sbom.yml").read_text(encoding="utf-8")
    dockerfile_text = (REPO_ROOT / "Dockerfile.dashboard").read_text(encoding="utf-8")

    assert 'NODE_VERSION: "24.14.0"' in ci_text
    assert 'NODE_VERSION: "24.14.0"' in sbom_text
    assert "ARG NODE_BASE_IMAGE=node:24.14.0-slim" in dockerfile_text


def test_dead_legacy_landing_component_is_removed() -> None:
    assert not (REPO_ROOT / "dashboard/LandingHero_legacy.svelte").exists()
