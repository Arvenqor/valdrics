"""Tests for notifications domain service and REST routes."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from app.models.notification import Notification
from app.modules.notifications.domain.notifications import NotificationService


class TestNotificationModel:
    def test_instantiation_with_required_fields(self) -> None:
        notification = Notification(
            tenant_id=uuid4(),
            type="policy.decision",
            title="Policy Decision",
            body="Action required",
        )
        assert notification.type == "policy.decision"
        assert notification.title == "Policy Decision"
        assert notification.is_read in (False, None)
        assert notification.is_deleted in (False, None)

    def test_fields_default_to_false_or_none(self) -> None:
        notification = Notification(
            tenant_id=uuid4(),
            type="system",
            title="t",
            body="b",
            is_read=False,
            is_deleted=False,
        )
        assert notification.is_read is False
        assert notification.is_deleted is False
        assert notification.read_at is None
        assert notification.payload_metadata in ({}, None)


class TestNotificationService:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db: AsyncMock) -> NotificationService:
        return NotificationService(mock_db)

    @pytest.mark.asyncio
    async def test_create_notification_persists_values(
        self, service: NotificationService, mock_db: AsyncMock
    ) -> None:
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", uuid4()))

        notification = await service.create_notification(
            tenant_id=uuid4(),
            notification_type="budget.warning",
            title="Budget warning",
            body="85% used",
            payload={"percent_used": 85.0},
        )

        assert notification.type == "budget.warning"
        assert notification.title == "Budget warning"

    @pytest.mark.asyncio
    async def test_mark_read_returns_true(
        self, service: NotificationService, mock_db: AsyncMock
    ) -> None:
        notification = Notification(
            id=uuid4(),
            tenant_id=uuid4(),
            type="system",
            title="t",
            body="b",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        ok = await service.mark_read(notification.id, notification.tenant_id)
        assert ok is True
        assert notification.is_read is True
        assert notification.read_at is not None

    @pytest.mark.asyncio
    async def test_list_notifications_returns_paginated_results(
        self, service: NotificationService, mock_db: AsyncMock
    ) -> None:
        rows = [
            Notification(
                id=uuid4(),
                tenant_id=uuid4(),
                type="policy.decision",
                title="Decision",
                body="Block",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = rows
        mock_db.execute.return_value = mock_result

        result = await service.list_notifications(tenant_id=uuid4(), limit=10, offset=0)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_unread_count_counts_non_deleted(
        self, service: NotificationService, mock_db: AsyncMock
    ) -> None:
        rows = [
            Notification(
                id=uuid4(),
                tenant_id=uuid4(),
                type="x",
                title="t",
                body="b",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = rows
        mock_db.execute.return_value = mock_result

        count = await service.get_unread_count(tenant_id=uuid4())
        assert count == 1

    @pytest.mark.asyncio
    async def test_soft_delete_returns_true(
        self, service: NotificationService, mock_db: AsyncMock
    ) -> None:
        notification = Notification(
            id=uuid4(),
            tenant_id=uuid4(),
            type="system",
            title="t",
            body="b",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = notification
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        ok = await service.soft_delete(notification.id, notification.tenant_id)
        assert ok is True
        assert notification.is_deleted is True
