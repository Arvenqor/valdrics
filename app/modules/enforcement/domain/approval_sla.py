"""Approval SLA detection and metrics."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger()


def detect_breach(
    approval: Any,
    policy: Any,
    now: datetime,
) -> tuple[bool, str | None]:
    """Return whether an approval has breached its SLA and the reason."""
    expires_at = approval.expires_at
    if expires_at is None:
        return False, None

    try:
        if expires_at <= now:
            return True, "ttl_exceeded"
    except TypeError:
        return False, None

    return False, None


def sla_metrics(approval: Any, policy: Any, now: datetime) -> dict[str, Any]:
    """Return SLA observability metrics for an approval."""
    expires_at = approval.expires_at

    if expires_at is None:
        return {
            "status": "unknown",
            "seconds_remaining": None,
            "breached": False,
            "breach_reason": None,
        }

    seconds_remaining = (expires_at - now).total_seconds()
    breached, reason = detect_breach(approval, policy, now)

    status = "expired" if breached else "active"
    if approval.status.name == "APPROVED":
        status = "approved"
    elif approval.status.name == "DENIED":
        status = "denied"

    return {
        "status": status,
        "seconds_remaining": seconds_remaining,
        "breached": breached,
        "breach_reason": reason,
    }
