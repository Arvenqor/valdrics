"""Route integration tests for customer API key endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.shared.core.auth import CurrentUser, UserRole, get_current_user
from app.shared.core.pricing import PricingTier


def _mock_user(*, tenant_id=None, role=UserRole.MEMBER):
    return CurrentUser(
        id=uuid4(),
        tenant_id=tenant_id or uuid4(),
        email="api-key-test@example.com",
        role=role,
        tier=PricingTier.PRO,
    )


@pytest.mark.asyncio
async def test_create_api_key_returns_masked_response_and_raw_key(async_client: AsyncClient, app):
    tenant_id = uuid4()
    mock_user = _mock_user(tenant_id=tenant_id)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_key = MagicMock()
        mock_key.id = uuid4()
        mock_key.name = "deploy"
        mock_key.key_prefix = "b2_testkey"
        mock_key.rate_limit_tier = "standard"
        mock_key.expires_at = None
        mock_key.is_active = True
        raw_key = "b2_secret-value"

        with patch(
            "app.modules.billing.api.v1.api_keys.create_customer_api_key",
            new=AsyncMock(return_value=(mock_key, raw_key)),
        ):
            response = await async_client.post(
                "/api/v1/billing/api-keys",
                json={"name": "deploy", "ttl_days": 30},
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["key"]["id"] == str(mock_key.id)
        assert payload["key"]["masked_value"] == "b2_testk...****"
        assert payload["raw_key"] == raw_key
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_list_api_keys_returns_masked_list(async_client: AsyncClient, app):
    tenant_id = uuid4()
    mock_user = _mock_user(tenant_id=tenant_id)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_key = MagicMock()
        mock_key.id = uuid4()
        mock_key.name = "deploy"
        mock_key.key_prefix = "b2_listkey"
        mock_key.rate_limit_tier = "standard"
        mock_key.expires_at = None
        mock_key.is_active = True

        with patch(
            "app.modules.billing.api.v1.api_keys.list_customer_api_keys",
            new=AsyncMock(return_value=[mock_key]),
        ):
            response = await async_client.get("/api/v1/billing/api-keys")
        assert response.status_code == 200
        payload = response.json()
        assert len(payload) == 1
        assert payload[0]["masked_value"] == "b2_listk...****"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_revoke_api_key_returns_status(async_client: AsyncClient, app):
    tenant_id = uuid4()
    mock_user = _mock_user(tenant_id=tenant_id)
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        mock_key = MagicMock()
        mock_key.id = uuid4()
        mock_key.is_active = False
        mock_key.revoked_at = "2026-01-01T00:00:00+00:00"

        with patch(
            "app.modules.billing.api.v1.api_keys.revoke_customer_api_key",
            new=AsyncMock(return_value=mock_key),
        ):
            response = await async_client.post(
                "/api/v1/billing/api-keys/b2_revoke",
            )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "revoked"
        assert payload["key_id"] == str(mock_key.id)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_feature_gate_blocks_api_access_when_disabled(async_client: AsyncClient, app):
    tenant_id = uuid4()
    mock_user = _mock_user(tenant_id=tenant_id)
    mock_user.tier = PricingTier.STARTER
    app.dependency_overrides[get_current_user] = lambda: mock_user
    try:
        with patch(
            "app.modules.billing.api.v1.api_keys.require_feature_or_403",
            side_effect=HTTPException(status_code=403, detail="Feature not enabled"),
        ):
            response = await async_client.post(
                "/api/v1/billing/api-keys",
                json={"name": "deploy"},
            )
        assert response.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)
