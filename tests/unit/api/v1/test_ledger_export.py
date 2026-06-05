import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient

from app.models.attribution import CostAllocation
from app.models.cloud import CloudAccount, CostRecord
from app.models.tenant import Tenant
from app.shared.core.auth import CurrentUser, UserRole
from app.shared.core.pricing import PricingTier
from tests.unit.api.v1.test_costs_endpoints_core import (
    _override_reporting_auth,
    _clear_reporting_auth_overrides,
)


@pytest.mark.asyncio
async def test_export_spend_ledger_csv(
    async_client: AsyncClient,
    app,
    db,
) -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    account_id = uuid.uuid4()
    record_id = uuid.uuid4()

    db.add(Tenant(id=tenant_id, name="Export Tenant", plan=PricingTier.PRO.value))
    db.add(
        CloudAccount(
            id=account_id,
            tenant_id=tenant_id,
            provider="saas",
            name="SaaS Spend",
            is_active=True,
        )
    )
    db.add(
        CostRecord(
            id=record_id,
            tenant_id=tenant_id,
            account_id=account_id,
            service="Slack",
            region="global",
            usage_type="Seats",
            resource_id="workspace-1",
            usage_amount=Decimal("20"),
            usage_unit="Seat",
            cost_usd=Decimal("100.00"),
            amount_raw=Decimal("100.00"),
            currency="USD",
            cost_status="FINAL",
            is_preliminary=False,
            canonical_charge_category="saas",
            canonical_charge_subcategory="subscription",
            canonical_mapping_version="focus-1.3-v1",
            tags={"department": "shared"},
            recorded_at=date(2026, 1, 15),
            timestamp=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
        )
    )
    db.add(
        CostAllocation(
            cost_record_id=record_id,
            recorded_at=date(2026, 1, 15),
            allocated_to="Engineering",
            amount=Decimal("100.00"),
            percentage=Decimal("100.00"),
            timestamp=datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc),
        )
    )
    await db.commit()

    mock_user = CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        email="ledger-export@valdrics.io",
        role=UserRole.ADMIN,
        tier=PricingTier.PRO,
    )

    _override_reporting_auth(app, mock_user)
    try:
        response = await async_client.get(
            "/api/v1/costs/ledger/export",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
                "provider": "saas",
            },
        )
    finally:
        _clear_reporting_auth_overrides(app)

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in response.headers["content-disposition"]

    csv_content = response.text
    lines = csv_content.splitlines()
    assert len(lines) >= 2
    # Verify headers
    headers = lines[0].split(",")
    assert "id" in headers
    assert "provider" in headers
    assert "cost_usd" in headers
    assert "allocated_amount_usd" in headers
    assert "allocations" in headers

    # Verify first row data
    row = lines[1].split(",")
    # The provider should be saas
    provider_idx = headers.index("provider")
    assert row[provider_idx] == "saas"


@pytest.mark.asyncio
async def test_export_spend_ledger_requires_admin(
    async_client: AsyncClient,
    app,
    db,
) -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    db.add(Tenant(id=tenant_id, name="Export Tenant", plan=PricingTier.PRO.value))
    await db.commit()

    # User is not an admin
    mock_user = CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        email="user@valdrics.io",
        role=UserRole.MEMBER,
        tier=PricingTier.PRO,
    )

    _override_reporting_auth(app, mock_user)
    try:
        response = await async_client.get(
            "/api/v1/costs/ledger/export",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )
    finally:
        _clear_reporting_auth_overrides(app)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_export_spend_ledger_empty(
    async_client: AsyncClient,
    app,
    db,
) -> None:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()

    db.add(Tenant(id=tenant_id, name="Export Tenant", plan=PricingTier.PRO.value))
    await db.commit()

    mock_user = CurrentUser(
        id=user_id,
        tenant_id=tenant_id,
        email="ledger-export@valdrics.io",
        role=UserRole.ADMIN,
        tier=PricingTier.PRO,
    )

    _override_reporting_auth(app, mock_user)
    try:
        response = await async_client.get(
            "/api/v1/costs/ledger/export",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
        )
    finally:
        _clear_reporting_auth_overrides(app)

    assert response.status_code == 200
    csv_content = response.text
    lines = csv_content.splitlines()
    # Should only contain header line
    assert len(lines) == 1
    headers = lines[0].split(",")
    assert "id" in headers
