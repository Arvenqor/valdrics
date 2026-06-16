"""Tests for approval SLA enforcement."""

import pytest
from datetime import datetime, timezone, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from app.modules.enforcement.domain import approval_sla


class MockPolicy:
    default_ttl_seconds = 3600


class MockApprovalStatus:
    def __init__(self, name: str = "PENDING"):
        self.name = name

PENDING = MockApprovalStatus("PENDING")
APPROVED = MockApprovalStatus("APPROVED")
DENIED = MockApprovalStatus("DENIED")
EXPIRED = MockApprovalStatus("EXPIRED")


class MockApproval:
    def __init__(self, expires_at: datetime | None, status: Any = PENDING):
        self.expires_at = expires_at
        self.status = status


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def test_detect_breach_when_expired():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    approval = MockApproval(expires_at=now - timedelta(minutes=5))
    breached, reason = approval_sla.detect_breach(approval, MockPolicy(), now)
    assert breached is True
    assert reason == "ttl_exceeded"


def test_detect_breach_when_not_expired():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    approval = MockApproval(expires_at=now + timedelta(minutes=10))
    breached, reason = approval_sla.detect_breach(approval, MockPolicy(), now)
    assert breached is False
    assert reason is None


def test_detect_breach_when_no_expiry():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    approval = MockApproval(expires_at=None)
    breached, reason = approval_sla.detect_breach(approval, MockPolicy(), now)
    assert breached is False
    assert reason is None


def test_sla_metrics_returns_seconds_remaining():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    approval = MockApproval(expires_at=now + timedelta(minutes=45))
    metrics = approval_sla.sla_metrics(approval, MockPolicy(), now)
    assert metrics["status"] == "active"
    assert metrics["seconds_remaining"] == 45 * 60
    assert metrics["breached"] is False
    assert metrics["breach_reason"] is None


def test_sla_metrics_marks_expired():
    now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    approval = MockApproval(expires_at=now - timedelta(seconds=1))
    metrics = approval_sla.sla_metrics(approval, MockPolicy(), now)
    assert metrics["status"] == "expired"
    assert metrics["seconds_remaining"] == -1.0
    assert metrics["breached"] is True
    assert metrics["breach_reason"] == "ttl_exceeded"
