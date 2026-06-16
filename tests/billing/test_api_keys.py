"""Tests for customer API key models and lifecycle helpers."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import hashlib

from app.models.api_key import CustomerApiKey
from app.modules.billing.domain.billing.api_key_utils import (
    create_customer_api_key,
    get_customer_api_key,
    list_customer_api_keys,
    mask_api_key,
    revoke_customer_api_key,
    resolve_customer_api_key,
    rotate_customer_api_key,
)
import app.modules.billing.domain.billing.api_key_utils as api_key_utils


class TestCustomerApiKeyModel:
    def test_required_fields_are_assigned(self) -> None:
        tenant_id = uuid4()
        key = CustomerApiKey(
            tenant_id=tenant_id,
            name="deploy",
            key_prefix="b2_deploykey",
            encrypted_value="encrypted-value",
            key_fingerprint="f" * 64,
        )

        assert key.tenant_id == tenant_id
        assert key.name == "deploy"
        assert key.key_prefix == "b2_deploykey"
        assert key.encrypted_value == "encrypted-value"
        assert key.key_fingerprint == "f" * 64
        assert key.is_active is None

    def test_defaults_for_optional_fields(self) -> None:
        key = CustomerApiKey(
            tenant_id=uuid4(),
            name="read-only",
            key_prefix="b2_readonly",
            encrypted_value="encrypted-value",
            key_fingerprint="f" * 64,
        )

        assert key.scopes is None
        assert key.allowed_ips is None
        assert key.rate_limit_tier is None
        assert key.expires_at is None
        assert key.last_used_at is None
        assert key.revoked_at is None
        assert key.key_metadata is None
        assert key.created_at is None
        assert key.updated_at is None


class TestApiKeyGenerationAndMasking:
    def test_generate_api_key_uses_customer_prefix(self) -> None:
        raw_key = api_key_utils.generate_api_key()

        assert raw_key.startswith("b2_")
        assert len(raw_key) > len("b2_")

    def test_mask_api_key_never_exposes_full_key(self) -> None:
        raw_key = "b2_secret-value"
        masked = mask_api_key(raw_key)

        assert masked == "b2_secret-va...****"
        assert raw_key not in masked
        assert "****" in masked

    def test_key_prefix_and_fingerprint_are_stable(self) -> None:
        raw_key = "b2_secret-value"

        assert api_key_utils.key_prefix(raw_key) == "b2_secret-va"
        assert api_key_utils.key_fingerprint(raw_key) == hashlib.sha256(raw_key.encode()).hexdigest()


class TestCustomerApiKeyService:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", uuid4()))
        db.commit = AsyncMock()
        return db

    @pytest.fixture
    def raw_key(self) -> str:
        return "b2_secret-value"

    @pytest.fixture
    def customer_key(self, raw_key: str) -> CustomerApiKey:
        return CustomerApiKey(
            id=uuid4(),
            tenant_id=uuid4(),
            name="deploy",
            key_prefix=api_key_utils.key_prefix(raw_key),
            encrypted_value="encrypted-value",
            key_fingerprint=api_key_utils.key_fingerprint(raw_key),
            scopes={"read": True},
            allowed_ips={"allow": ["127.0.0.1"]},
            rate_limit_tier="standard",
        )

    @pytest.mark.asyncio
    async def test_create_persists_masked_safe_values(
        self,
        mock_db: AsyncMock,
        raw_key: str,
    ) -> None:
        tenant_id = uuid4()
        with (
            patch.object(
                api_key_utils,
                "generate_api_key",
                return_value=raw_key,
            ),
            patch.object(
                api_key_utils,
                "encrypt_string",
                return_value="encrypted-value",
            ),
        ):
            key, returned_raw_key = await create_customer_api_key(
                mock_db,
                tenant_id,
                "deploy",
                scopes={"read": True},
                allowed_ips={"allow": ["127.0.0.1"]},
                ttl_days=30,
            )

        assert returned_raw_key == raw_key
        assert key.tenant_id == tenant_id
        assert key.name == "deploy"
        assert key.key_prefix == api_key_utils.key_prefix(raw_key)
        assert key.encrypted_value == "encrypted-value"
        assert key.key_fingerprint == api_key_utils.key_fingerprint(raw_key)
        assert key.scopes == {"read": True}
        assert key.allowed_ips == {"allow": ["127.0.0.1"]}
        assert key.expires_at is not None
        assert key.is_active is True
        mock_db.add.assert_called_once_with(key)
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(key)
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_returns_active_keys_ordered_by_created_at(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [customer_key]
        mock_db.execute.return_value = mock_result

        keys = await list_customer_api_keys(mock_db, customer_key.tenant_id)

        assert keys == [customer_key]
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_returns_matching_key_for_tenant(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer_key
        mock_db.execute.return_value = mock_result

        key = await get_customer_api_key(mock_db, customer_key.id, customer_key.tenant_id)

        assert key == customer_key
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revoke_soft_deletes_key(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer_key
        mock_db.execute.return_value = mock_result

        revoked = await revoke_customer_api_key(
            mock_db,
            customer_key.id,
            customer_key.tenant_id,
        )

        assert revoked == customer_key
        assert customer_key.is_active is False
        assert isinstance(customer_key.revoked_at, datetime)
        mock_db.flush.assert_awaited_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rotate_replaces_encrypted_value_and_raw_secret(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
        raw_key: str,
    ) -> None:
        raw_key = "b2_rotated-secret"
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer_key
        mock_db.execute.return_value = mock_result
        with (
            patch.object(
                api_key_utils,
                "generate_api_key",
                return_value=raw_key,
            ),
            patch.object(
                api_key_utils,
                "encrypt_string",
                return_value="encrypted-rotated-value",
            ),
        ):
            rotated, returned_raw_key = await rotate_customer_api_key(
                mock_db,
                customer_key.id,
                customer_key.tenant_id,
                ttl_days=14,
            )

        assert returned_raw_key == raw_key
        assert rotated == customer_key
        assert customer_key.key_prefix == api_key_utils.key_prefix(raw_key)
        assert customer_key.encrypted_value == "encrypted-rotated-value"
        assert customer_key.key_fingerprint == api_key_utils.key_fingerprint(raw_key)
        assert customer_key.is_active is True
        assert customer_key.revoked_at is None
        assert customer_key.expires_at is not None
        assert customer_key.expires_at >= datetime.now(timezone.utc)
        assert customer_key.expires_at <= datetime.now(timezone.utc) + timedelta(days=14)
        mock_db.flush.assert_awaited_once()
        mock_db.refresh.assert_awaited_once_with(customer_key)
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_resolve_uses_prefix_and_fingerprint_without_decrypting(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = customer_key
        mock_db.execute.return_value = mock_result

        key = await resolve_customer_api_key(mock_db, "b2_secret-value")

        assert key == customer_key
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rotate_returns_none_when_key_missing(
        self,
        mock_db: AsyncMock,
        customer_key: CustomerApiKey,
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        rotated = await rotate_customer_api_key(mock_db, customer_key.id, customer_key.tenant_id)

        assert rotated is None
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_raises_when_encryption_unavailable(
        self,
        mock_db: AsyncMock,
    ) -> None:
        with patch.object(api_key_utils, "encrypt_string", return_value=None):
            with pytest.raises(RuntimeError, match="api_key_encryption_failed"):
                await create_customer_api_key(mock_db, uuid4(), "deploy")

        mock_db.add.assert_not_called()
