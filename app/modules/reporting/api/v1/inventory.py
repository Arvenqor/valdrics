"""Inventory API for cross-source cloud, software, and service assets."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.reporting.domain.inventory_service import (
    InventoryProjectionService,
    build_inventory_summary,
)
from app.schemas.inventory import InventoryListResponse, InventoryResource
from app.shared.core.auth import CurrentUser, requires_role_with_db_context
from app.shared.db.session import get_db

router = APIRouter(tags=["Inventory"])


InventoryTypeFilter = Literal["all", "cloud", "software", "service"]
InventoryStatusFilter = Literal[
    "all",
    "active",
    "pending",
    "error",
    "idle",
    "shadow",
    "expiring",
]


def _require_tenant_id(user: CurrentUser) -> UUID:
    if not user.tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context required.")
    return user.tenant_id


def _matches_search(resource: InventoryResource, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join(
        [
            resource.name,
            resource.provider,
            resource.region or "",
            resource.owner_name or "",
            resource.owner_email or "",
            resource.team_name or "",
            resource.source_label or "",
            *resource.tags.keys(),
            *resource.tags.values(),
        ]
    ).lower()
    return query.lower() in haystack


@router.get("", response_model=InventoryListResponse)
async def list_inventory(
    inventory_type: InventoryTypeFilter = Query(default="all", alias="type"),
    status: InventoryStatusFilter = Query(default="all"),
    q: str = Query(default="", max_length=120),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=40, ge=1, le=100),
    current_user: CurrentUser = Depends(requires_role_with_db_context("member")),
    db: AsyncSession = Depends(get_db),
) -> InventoryListResponse:
    tenant_id = _require_tenant_id(current_user)
    search = q.strip()
    service = InventoryProjectionService(db)
    resources = await service.list_resources(tenant_id)
    summary = build_inventory_summary(resources)

    filtered = [
        resource
        for resource in resources
        if (inventory_type == "all" or resource.resource_type == inventory_type)
        and (status == "all" or resource.status == status)
        and _matches_search(resource, search)
    ]
    start = (page - 1) * per_page
    end = start + per_page

    return InventoryListResponse(
        items=filtered[start:end],
        total=len(filtered),
        page=page,
        per_page=per_page,
        type=inventory_type,
        status=status,
        search=search,
        summary=summary,
    )
