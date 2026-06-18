"""In-app notification domain service."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification

import structlog

logger = structlog.get_logger()


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_notification(
        self,
        tenant_id: Any,
        notification_type: str,
        title: str,
        body: str,
        payload: Optional[Dict[str, Any]] = None,
        actor_id: Optional[Any] = None,
        actor_email: Optional[str] = None,
    ) -> Any:
        notification = Notification(
            tenant_id=tenant_id,
            type=notification_type,
            title=title,
            body=body,
            payload_metadata=payload,
            actor_id=actor_id,
            actor_email=actor_email,
        )
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        logger.info(
            "notification_created",
            tenant_id=str(tenant_id),
            notification_id=str(notification.id),
            notification_type=notification_type,
        )
        return notification

    async def mark_read(
        self,
        notification_id: Any,
        tenant_id: Any,
    ) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.tenant_id == tenant_id,
                )
            )
        )
        notification = result.scalar_one_or_none()
        if not notification or notification.is_deleted:
            return False
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.db.flush()
            logger.info(
                "notification_marked_read",
                tenant_id=str(tenant_id),
                notification_id=str(notification_id),
            )
        return True

    async def list_notifications(
        self,
        tenant_id: Any,
        limit: int = 50,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> list[Any]:
        stmt = (
            select(Notification)
            .where(Notification.tenant_id == tenant_id)
            .order_by(Notification.created_at.desc())
            .limit(max(1, min(limit, 200)))
            .offset(max(0, offset))
        )
        if not include_deleted:
            stmt = stmt.where(Notification.is_deleted.is_(False))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, tenant_id: Any) -> int:
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.tenant_id == tenant_id,
                    Notification.is_read.is_(False),
                    Notification.is_deleted.is_(False),
                )
            )
        )
        return len(result.scalars().all())

    async def soft_delete(
        self,
        notification_id: Any,
        tenant_id: Any,
    ) -> bool:
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.tenant_id == tenant_id,
                )
            )
        )
        notification = result.scalar_one_or_none()
        if not notification or notification.is_deleted:
            return False
        notification.is_deleted = True
        await self.db.flush()
        logger.info(
            "notification_deleted",
            tenant_id=str(tenant_id),
            notification_id=str(notification_id),
        )
        return True
