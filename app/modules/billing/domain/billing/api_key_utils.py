"""API key lifecycle utilities for customer-facing scoped keys."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import CustomerApiKey
from app.shared.core.security import encrypt_string

KEY_PREFIX_LENGTH = 12
DEFAULT_RATE_LIMIT_TIER = "standard"


def generate_api_key() -> str:
    """Generate a new customer API key without persisting it."""
    return f"b2_{secrets.token_urlsafe(32)}"


def mask_api_key(raw_key: str, *, prefix: str | None = None) -> str:
    """Return a non-sensitive display value for an API key."""
    visible = prefix or raw_key[:KEY_PREFIX_LENGTH]
    return f"{visible}...****"


def key_prefix(raw_key: str) -> str:
    return raw_key[:KEY_PREFIX_LENGTH]


def key_fingerprint(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_tenant_id(value: Any) -> Any:
    return value


def _normalize_optional_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    return value or {}


def _expires_at_from_ttl(ttl_days: int | None, *, preserve: datetime | None = None) -> datetime | None:
    if ttl_days is None:
        return preserve
    if ttl_days <= 0:
        raise ValueError("ttl_days must be greater than 0")
    return _now_utc() + timedelta(days=ttl_days)


async def create_customer_api_key(
    db: AsyncSession,
    tenant_id: Any,
    name: str,
    *,
    scopes: dict[str, Any] | None = None,
    allowed_ips: dict[str, Any] | None = None,
    rate_limit_tier: str = DEFAULT_RATE_LIMIT_TIER,
    created_by: Any | None = None,
    ttl_days: int | None = None,
) -> tuple[CustomerApiKey, str]:
    """Create a new customer API key and return ``(entity, raw_key)``."""
    raw_key = generate_api_key()
    key = await _persist_customer_api_key(
        db=db,
        tenant_id=_resolve_tenant_id(tenant_id),
        name=name,
        raw_key=raw_key,
        scopes=scopes,
        allowed_ips=allowed_ips,
        rate_limit_tier=rate_limit_tier,
        created_by=created_by,
        ttl_days=ttl_days,
    )
    return key, raw_key


async def list_customer_api_keys(
    db: AsyncSession,
    tenant_id: Any,
) -> list[CustomerApiKey]:
    """List active API keys for a tenant ordered newest first."""
    result = await db.execute(
        select(CustomerApiKey)
        .where(
            CustomerApiKey.tenant_id == _resolve_tenant_id(tenant_id),
            CustomerApiKey.is_active.is_(True),
            CustomerApiKey.revoked_at.is_(None),
        )
        .order_by(CustomerApiKey.created_at.desc())
    )
    return list(result.scalars().all())


async def get_customer_api_key(
    db: AsyncSession,
    key_id: Any,
    tenant_id: Any,
) -> CustomerApiKey | None:
    """Fetch one active API key for a tenant."""
    result = await db.execute(
        select(CustomerApiKey).where(
            CustomerApiKey.id == key_id,
            CustomerApiKey.tenant_id == _resolve_tenant_id(tenant_id),
            CustomerApiKey.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()


async def revoke_customer_api_key(
    db: AsyncSession,
    key_id: Any,
    tenant_id: Any,
) -> CustomerApiKey | None:
    """Soft-revoke an API key without deleting audit history."""
    key = await get_customer_api_key(db, key_id, tenant_id)
    if key is None:
        return None

    now = _now_utc()
    key.is_active = False
    key.revoked_at = now
    await db.flush()
    await db.commit()
    return key


async def rotate_customer_api_key(
    db: AsyncSession,
    key_id: Any,
    tenant_id: Any,
    *,
    created_by: Any | None = None,
    ttl_days: int | None = None,
) -> tuple[CustomerApiKey, str] | None:
    """Replace an active API key value and return ``(entity, raw_key)``."""
    key = await get_customer_api_key(db, key_id, tenant_id)
    if key is None:
        return None

    raw_key = generate_api_key()
    encrypted = encrypt_string(raw_key, context="api_key")
    if not encrypted:
        raise RuntimeError("api_key_encryption_failed")

    key.key_prefix = key_prefix(raw_key)
    key.encrypted_value = encrypted
    key.key_fingerprint = key_fingerprint(raw_key)
    key.expires_at = _expires_at_from_ttl(ttl_days, preserve=key.expires_at)
    if created_by is not None:
        key.created_by = created_by
    key.updated_at = _now_utc()
    key.is_active = True
    key.revoked_at = None

    await db.flush()
    await db.refresh(key)
    await db.commit()
    return key, raw_key


async def resolve_customer_api_key(
    db: AsyncSession,
    raw_key: str,
) -> CustomerApiKey | None:
    """Resolve a raw API key by prefix and fingerprint without decrypting."""
    result = await db.execute(
        select(CustomerApiKey).where(
            CustomerApiKey.key_prefix == key_prefix(raw_key),
            CustomerApiKey.is_active.is_(True),
            CustomerApiKey.revoked_at.is_(None),
            CustomerApiKey.key_fingerprint == key_fingerprint(raw_key),
        )
    )
    return result.scalar_one_or_none()


async def _persist_customer_api_key(
    db: AsyncSession,
    *,
    tenant_id: Any,
    name: str,
    raw_key: str,
    scopes: dict[str, Any] | None,
    allowed_ips: dict[str, Any] | None,
    rate_limit_tier: str,
    created_by: Any | None,
    ttl_days: int | None,
) -> CustomerApiKey:
    encrypted = encrypt_string(raw_key, context="api_key")
    if not encrypted:
        raise RuntimeError("api_key_encryption_failed")

    key = CustomerApiKey(
        tenant_id=tenant_id,
        name=name,
        key_prefix=key_prefix(raw_key),
        encrypted_value=encrypted,
        key_fingerprint=key_fingerprint(raw_key),
        scopes=_normalize_optional_dict(scopes),
        allowed_ips=_normalize_optional_dict(allowed_ips),
        rate_limit_tier=rate_limit_tier or DEFAULT_RATE_LIMIT_TIER,
        expires_at=_expires_at_from_ttl(ttl_days),
        created_by=created_by,
        is_active=True,
    )
    db.add(key)
    await db.flush()
    await db.refresh(key)
    await db.commit()
    return key


list_customer_api_key = list_customer_api_keys
revoke_customer_api_key_by_id = revoke_customer_api_key
resolve_customer_api_key_by_raw = resolve_customer_api_key
