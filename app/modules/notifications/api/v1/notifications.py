"""Notifications API routes for in-app feed and SSE stream."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncIterator, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
import structlog

from app.modules.notifications.domain.notifications import NotificationService
from app.shared.core.auth import CurrentUser, requires_role
from app.shared.core.config import get_settings
from app.shared.core.ops_metrics import (
    SSE_STREAM_CONNECTIONS_ACTIVE,
    SSE_STREAM_CONNECTIONS_TOTAL,
    SSE_STREAM_ERRORS_TOTAL,
    SSE_STREAM_POLL_DURATION,
)
from app.shared.core.rate_limit import auth_limit
from app.shared.db.session import get_db

router = APIRouter()
logger = structlog.get_logger()


async def _require_tenant_id(user: CurrentUser) -> Any:
    tenant_id = getattr(user, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="Tenant context is required")
    return tenant_id


_notification_stream_lock = asyncio.Lock()
_active_notification_streams: Dict[str, int] = {}


@router.get("/stream")
async def stream_notifications(
    user: CurrentUser = Depends(requires_role("member")),
    db: AsyncSession = Depends(get_db),
) -> EventSourceResponse:
    """Stream tenant notification events over SSE."""
    from app.shared.db.session import async_session_maker

    settings = get_settings()
    tenant_id = await _require_tenant_id(user)
    tenant_key = str(tenant_id)
    max_connections = max(1, int(settings.SSE_MAX_CONNECTIONS_PER_TENANT))
    poll_interval = max(1, int(settings.SSE_POLL_INTERVAL_SECONDS))

    async with _notification_stream_lock:
        current = _active_notification_streams.get(tenant_key, 0)
        if current >= max_connections:
            raise HTTPException(
                status_code=429,
                detail=f"Too many active notification streams for tenant. Max allowed: {max_connections}",
            )
        _active_notification_streams[tenant_key] = current + 1

    SSE_STREAM_CONNECTIONS_TOTAL.labels(tenant_id=tenant_key).inc()
    SSE_STREAM_CONNECTIONS_ACTIVE.labels(tenant_id=tenant_key).inc()

    async def event_generator() -> AsyncIterator[Dict[str, str]]:
        last_seen: Dict[Any, str] = {}
        idle_iterations = 0
        max_idle = max(poll_interval * 4, 60)
        try:
            while True:
                poll_start = time.perf_counter()
                try:
                    async with async_session_maker() as session:
                        scoped_service = NotificationService(session)
                        rows = await scoped_service.list_notifications(
                            tenant_id=tenant_id,
                            limit=50,
                            offset=0,
                            include_deleted=False,
                        )
                        updates = []
                        for notification in rows:
                            state = f"{notification.is_read}:{notification.updated_at.isoformat()}"
                            if last_seen.get(notification.id) != state:
                                last_seen[notification.id] = state
                                updates.append(
                                    {
                                        "id": str(notification.id),
                                        "type": notification.type,
                                        "title": notification.title,
                                        "is_read": notification.is_read,
                                        "created_at": notification.created_at.isoformat() if notification.created_at else None,
                                    }
                                )
                        if updates:
                            idle_iterations = 0
                            yield {"event": "notification_update", "data": json.dumps(updates)}
                        else:
                            idle_iterations += 1
                        yield {"event": "ping", "data": "heartbeat"}
                except Exception as exc:  # pragma: no cover - resilience path
                    SSE_STREAM_ERRORS_TOTAL.labels(
                        tenant_id=tenant_key, error_type=type(exc).__name__
                    ).inc()
                    logger.warning(
                        "notification_stream_poll_failed",
                        tenant_id=tenant_key,
                        error=str(exc),
                    )
                    yield {"event": "error", "data": json.dumps({"error": "Stream interrupted"})}
                poll_duration = time.perf_counter() - poll_start
                SSE_STREAM_POLL_DURATION.labels(tenant_id=tenant_key).observe(poll_duration)
                if idle_iterations >= max_idle:
                    break
                await asyncio.sleep(poll_interval)
        finally:
            SSE_STREAM_CONNECTIONS_ACTIVE.labels(tenant_id=tenant_key).dec()
            async with _notification_stream_lock:
                remaining = _active_notification_streams.get(tenant_key, 0) - 1
                if remaining > 0:
                    _active_notification_streams[tenant_key] = remaining
                else:
                    _active_notification_streams.pop(tenant_key, None)

    return EventSourceResponse(event_generator())


@router.get("")
async def list_notifications(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user: CurrentUser = Depends(requires_role("member")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List notifications for the current tenant."""
    tenant_id = await _require_tenant_id(user)
    service = NotificationService(db)
    rows = await service.list_notifications(
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
        include_deleted=False,
    )
    return {
        "items": [
            {
                "id": str(item.id),
                "type": item.type,
                "title": item.title,
                "body": item.body,
                "is_read": item.is_read,
                "read_at": item.read_at.isoformat() if item.read_at else None,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "metadata": item.metadata or {},
            }
            for item in rows
        ]
    }


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: Any,
    user: CurrentUser = Depends(requires_role("member")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Mark a single notification as read."""
    tenant_id = await _require_tenant_id(user)
    service = NotificationService(db)
    ok = await service.mark_read(notification_id=notification_id, tenant_id=tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "read", "notification_id": str(notification_id)}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: Any,
    user: CurrentUser = Depends(requires_role("member")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Soft-delete a notification."""
    tenant_id = await _require_tenant_id(user)
    service = NotificationService(db)
    ok = await service.soft_delete(notification_id=notification_id, tenant_id=tenant_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"status": "deleted", "notification_id": str(notification_id)}


@router.get("/unread-count")
async def unread_count(
    user: CurrentUser = Depends(requires_role("member")),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Return unread notification count for tenant."""
    tenant_id = await _require_tenant_id(user)
    service = NotificationService(db)
    count = await service.get_unread_count(tenant_id=tenant_id)
    return {"count": count, "tenant_id": str(tenant_id)}
