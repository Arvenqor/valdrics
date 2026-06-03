from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.aws_connection import AWSConnection
from app.models.azure_connection import AzureConnection
from app.models.discovered_account import DiscoveredAccount
from app.models.gcp_connection import GCPConnection
from app.models.hybrid_connection import HybridConnection
from app.models.license_connection import LicenseConnection
from app.models.platform_connection import PlatformConnection
from app.models.saas_connection import SaaSConnection
from app.models.tenant import Tenant, UserRole
from app.shared.core.pricing import PricingTier

pytest_plugins = ("tests.unit.governance.connections_api_fixtures",)


@pytest.mark.asyncio
async def test_inventory_empty_for_tenant_without_sources(ac, override_auth, auth_user):
    auth_user.role = UserRole.MEMBER
    response = await ac.get("/api/v1/inventory")

    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["total"] == 0
    assert payload["summary"]["total"] == 0


@pytest.mark.asyncio
async def test_inventory_projects_real_connections_and_feed_rows(
    ac, db, override_auth, auth_user
):
    now = datetime(2026, 6, 2, 8, 30, tzinfo=timezone.utc)
    aws = AWSConnection(
        tenant_id=auth_user.tenant_id,
        aws_account_id="123456789012",
        role_arn="arn:aws:iam::123456789012:role/Valdrics",
        external_id="vx-12345678901212345678901212345678",
        region="us-east-1",
        status="active",
        is_management_account=True,
        organization_id="o-valdrics",
        last_verified_at=now,
    )
    azure = AzureConnection(
        tenant_id=auth_user.tenant_id,
        name="Azure Production",
        azure_tenant_id="azure-tenant-1",
        client_id="client-1",
        subscription_id="sub-prod-1",
        is_active=False,
        error_message="credential expired",
        last_synced_at=now,
    )
    gcp = GCPConnection(
        tenant_id=auth_user.tenant_id,
        name="GCP FinOps",
        project_id="gcp-prod",
        is_active=True,
        auth_method="workload_identity",
        last_synced_at=now,
    )
    db.add_all([aws, azure, gcp])
    await db.commit()
    await db.refresh(aws)

    db.add(
        DiscoveredAccount(
            management_connection_id=aws.id,
            account_id="210987654321",
            name="Platform Sandbox",
            status="discovered",
            last_discovered_at=now,
        )
    )
    db.add_all(
        [
            SaaSConnection(
                tenant_id=auth_user.tenant_id,
                name="Stripe Billing",
                vendor="stripe",
                auth_method="api_key",
                is_active=True,
                spend_feed=[
                    {
                        "name": "Stripe API",
                        "monthly_cost_usd": 980.25,
                        "owner_name": "Finance Ops",
                        "owner_email": "finops@example.com",
                        "team_name": "Finance",
                        "status": "active",
                        "tags": {"cost_center": "fin"},
                        "last_seen_at": "2026-06-01T00:00:00Z",
                    }
                ],
            ),
            LicenseConnection(
                tenant_id=auth_user.tenant_id,
                name="Microsoft 365",
                vendor="microsoft_365",
                auth_method="oauth",
                is_active=True,
                license_feed=[
                    {
                        "product": "M365 E5",
                        "cost_usd": 450,
                        "status": "expiring",
                        "team": "Corporate IT",
                    }
                ],
            ),
            PlatformConnection(
                tenant_id=auth_user.tenant_id,
                name="Shared Platform Ledger",
                vendor="internal_platform",
                auth_method="manual",
                is_active=False,
                spend_feed=[],
            ),
            HybridConnection(
                tenant_id=auth_user.tenant_id,
                name="Colo Ledger",
                vendor="datacenter",
                auth_method="csv",
                is_active=True,
                spend_feed=[
                    {
                        "service": "DC Core",
                        "amount_usd": "1250.5",
                        "status": "active",
                        "region": "dc-lagos-1",
                    }
                ],
            ),
        ]
    )
    await db.commit()

    response = await ac.get("/api/v1/inventory")

    assert response.status_code == 200
    payload = response.json()
    names = {item["name"]: item for item in payload["items"]}
    assert "AWS account 123456789012" in names
    assert names["Azure Production"]["status"] == "error"
    assert names["GCP FinOps"]["tags"]["project_id"] == "gcp-prod"
    assert names["Platform Sandbox"]["source_kind"] == "discovered_account"
    assert names["Stripe API"]["monthly_cost"] == 980.25
    assert names["Stripe API"]["cost_basis"] == "monthly_cost_usd"
    assert names["M365 E5"]["cost_basis"] == "reported_cost_usd"
    assert names["M365 E5"]["status"] == "expiring"
    assert names["Shared Platform Ledger"]["cost_basis"] == "not_reported"
    assert names["DC Core"]["provider"] == "datacenter"
    assert payload["summary"]["cloud"] == 4
    assert payload["summary"]["software"] == 2
    assert payload["summary"]["service"] == 2
    assert payload["summary"]["source_count"] == 7
    assert payload["summary"]["reported_cost_usd"] == 2680.75


@pytest.mark.asyncio
async def test_inventory_filters_searches_and_paginates(ac, db, override_auth, auth_user):
    db.add_all(
        [
            SaaSConnection(
                tenant_id=auth_user.tenant_id,
                name="Okta Feed",
                vendor="okta",
                auth_method="api_key",
                is_active=True,
                spend_feed=[
                    {
                        "name": "Okta Workforce",
                        "monthly_cost_usd": 700,
                        "status": "shadow",
                        "team": "Identity",
                    },
                    {
                        "name": "Okta Sandbox",
                        "monthly_cost_usd": 100,
                        "status": "idle",
                        "team": "Identity",
                    },
                ],
            ),
            HybridConnection(
                tenant_id=auth_user.tenant_id,
                name="Datacenter",
                vendor="colo",
                auth_method="csv",
                is_active=True,
                spend_feed=[{"service": "Rack A", "monthly_cost_usd": 500}],
            ),
        ]
    )
    await db.commit()

    response = await ac.get(
        "/api/v1/inventory",
        params={"type": "software", "status": "shadow", "q": "workforce"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["name"] == "Okta Workforce"

    paged = await ac.get("/api/v1/inventory", params={"page": 2, "per_page": 1})
    assert paged.status_code == 200
    assert paged.json()["page"] == 2
    assert len(paged.json()["items"]) == 1


@pytest.mark.asyncio
async def test_inventory_is_tenant_scoped(ac, db, override_auth, auth_user):
    other_tenant = Tenant(id=uuid4(), name="Other", plan=PricingTier.PRO.value)
    db.add(other_tenant)
    await db.commit()
    db.add_all(
        [
            SaaSConnection(
                tenant_id=auth_user.tenant_id,
                name="Mine",
                vendor="mine",
                auth_method="manual",
                spend_feed=[{"name": "Tenant App", "monthly_cost_usd": 10}],
            ),
            SaaSConnection(
                tenant_id=other_tenant.id,
                name="Other",
                vendor="other",
                auth_method="manual",
                spend_feed=[{"name": "Foreign App", "monthly_cost_usd": 9999}],
            ),
        ]
    )
    await db.commit()

    response = await ac.get("/api/v1/inventory")

    assert response.status_code == 200
    text = str(response.json())
    assert "Tenant App" in text
    assert "Foreign App" not in text


@pytest.mark.asyncio
async def test_inventory_requires_tenant_context(ac, app, override_auth, auth_user):
    auth_user.tenant_id = None

    response = await ac.get("/api/v1/inventory")

    assert response.status_code == 403
    payload = response.json()
    detail = payload.get("detail")
    if detail is None and isinstance(payload.get("error"), dict):
        detail = payload["error"].get("message")
    if detail is None:
        detail = payload.get("error") or payload
    assert "Tenant context required" in str(detail)
