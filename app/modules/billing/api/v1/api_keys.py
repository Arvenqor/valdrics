"""Customer API key management routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.billing.domain.billing.api_key_utils import (
    create_customer_api_key,
    get_customer_api_key,
    list_customer_api_keys,
    mask_api_key,
    revoke_customer_api_key,
    rotate_customer_api_key,
)
from app.modules.enforcement.api.v1.common import require_feature_or_403
from app.shared.core.auth import CurrentUser, requires_role_with_db_context
from app.shared.core.pricing import FeatureFlag
from app.shared.core.rate_limit import auth_limit, standard_limit
from app.shared.db.session import get_db

router = APIRouter(tags=["Billing API Keys"])


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    scopes: dict[str, Any] = Field(default_factory=dict)
    allowed_ips: dict[str, Any] = Field(default_factory=dict)
    ttl_days: int | None = Field(default=None, ge=1, le=3650)


class ApiKeyRotateRequest(BaseModel):
    ttl_days: int | None = Field(default=None, ge=1, le=3650)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    masked_value: str
    rate_limit_tier: str
    expires_at: str | None = None
    is_active: bool


class ApiKeyCreateResponse(BaseModel):
    key: ApiKeyResponse
    raw_key: str


def _tenant_id(user: CurrentUser) -> Any:
    if user.tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant context required")
    return user.tenant_id


def _to_response(key: Any) -> ApiKeyResponse:
    return ApiKeyResponse(
        id=str(key.id),
        name=key.name,
        key_prefix=key.key_prefix,
        masked_value=mask_api_key("", prefix=key.key_prefix),
        rate_limit_tier=key.rate_limit_tier,
        expires_at=key.expires_at.isoformat() if key.expires_at else None,
        is_active=key.is_active,
    )


@router.post("", response_model=ApiKeyCreateResponse)
@standard_limit
async def create_api_key(
    request: Request,
    payload: ApiKeyCreateRequest,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    key, raw_key = await create_customer_api_key(
        db=db,
        tenant_id=_tenant_id(user),
        name=payload.name,
        scopes=payload.scopes,
        allowed_ips=payload.allowed_ips,
        created_by=user.id,
        ttl_days=payload.ttl_days,
    )
    return ApiKeyCreateResponse(
        key=_to_response(key),
        raw_key=raw_key,
    )


@router.get("", response_model=list[ApiKeyResponse])
@auth_limit
async def list_api_keys(
    request: Request,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    keys = await list_customer_api_keys(db, _tenant_id(user))
    return [_to_response(key) for key in keys]


@router.get("/{key_id}", response_model=ApiKeyResponse)
@auth_limit
async def get_api_key(
    request: Request,
    key_id: str,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    key = await get_customer_api_key(db, key_id, _tenant_id(user))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return _to_response(key)


@router.post("/{key_id}/rotate", response_model=ApiKeyCreateResponse)
@standard_limit
async def rotate_api_key(
    request: Request,
    key_id: str,
    payload: ApiKeyRotateRequest | None = None,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreateResponse:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    payload = payload or ApiKeyRotateRequest()
    rotated = await rotate_customer_api_key(
        db,
        key_id,
        _tenant_id(user),
        created_by=user.id,
        ttl_days=payload.ttl_days,
    )
    if rotated is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    key, raw_key = rotated
    return ApiKeyCreateResponse(key=_to_response(key), raw_key=raw_key)


@router.post("/{key_id}/revoke", response_model=dict[str, str])
@standard_limit
async def revoke_api_key(
    request: Request,
    key_id: str,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    key = await revoke_customer_api_key(db, key_id, _tenant_id(user))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"status": "revoked", "key_id": str(key.id)}


@router.delete("/{key_id}", response_model=dict[str, str])
@standard_limit
async def delete_api_key(
    request: Request,
    key_id: str,
    user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    del request
    await require_feature_or_403(
        user=user,
        db=db,
        feature=FeatureFlag.API_ACCESS,
    )
    key = await revoke_customer_api_key(db, key_id, _tenant_id(user))
    if not key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    return {"status": "revoked", "key_id": str(key.id)}
