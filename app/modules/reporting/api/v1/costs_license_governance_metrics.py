"""License-governance KPI calculations for costs acceptance evidence."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.license_connection import LicenseConnection
from app.models.remediation import (
    RemediationAction,
    RemediationRequest,
    RemediationStatus,
)

from .costs_models import AcceptanceKpiMetric


async def compute_license_governance_kpi(
    *,
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> AcceptanceKpiMetric:
    """Compute deterministic license-governance reliability KPI for acceptance evidence."""
    active_connections = int(
        await db.scalar(
            select(func.count(LicenseConnection.id)).where(
                LicenseConnection.tenant_id == tenant_id,
                LicenseConnection.is_active,
            )
        )
        or 0
    )

    if active_connections <= 0:
        return AcceptanceKpiMetric(
            key="license_governance_reliability",
            label="License Governance Reliability",
            available=False,
            target="At least one active license connection",
            actual="No active license connections",
            meets_target=False,
            details={
                "active_license_connections": 0,
                "total_requests": 0,
                "completed_requests": 0,
                "failed_requests": 0,
                "in_flight_requests": 0,
            },
        )

    start_dt = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
    end_dt_exclusive = datetime.combine(end_date + timedelta(days=1), time.min).replace(
        tzinfo=timezone.utc
    )
    activity_at = func.coalesce(
        RemediationRequest.executed_at,
        RemediationRequest.updated_at,
        RemediationRequest.created_at,
    )
    in_flight_statuses = (
        RemediationStatus.PENDING,
        RemediationStatus.PENDING_APPROVAL,
        RemediationStatus.APPROVED,
        RemediationStatus.SCHEDULED,
        RemediationStatus.EXECUTING,
    )

    counts_stmt = select(
        func.count(RemediationRequest.id).label("total_requests"),
        func.count(RemediationRequest.id)
        .filter(RemediationRequest.status == RemediationStatus.COMPLETED)
        .label("completed_requests"),
        func.count(RemediationRequest.id)
        .filter(RemediationRequest.status == RemediationStatus.FAILED)
        .label("failed_requests"),
        func.count(RemediationRequest.id)
        .filter(RemediationRequest.status.in_(in_flight_statuses))
        .label("in_flight_requests"),
    ).where(
        RemediationRequest.tenant_id == tenant_id,
        RemediationRequest.action == RemediationAction.RECLAIM_LICENSE_SEAT,
        activity_at >= start_dt,
        activity_at < end_dt_exclusive,
    )
    counts_row = (await db.execute(counts_stmt)).one()

    total_requests = int(getattr(counts_row, "total_requests", 0) or 0)
    completed_requests = int(getattr(counts_row, "completed_requests", 0) or 0)
    failed_requests = int(getattr(counts_row, "failed_requests", 0) or 0)
    in_flight_requests = int(getattr(counts_row, "in_flight_requests", 0) or 0)
    completion_rate = _rate(completed_requests, total_requests, default=100.0)
    failure_rate = _rate(failed_requests, total_requests, default=0.0)
    in_flight_ratio = _rate(in_flight_requests, total_requests, default=0.0)

    completed_rows = await db.execute(
        select(RemediationRequest.created_at, RemediationRequest.executed_at).where(
            RemediationRequest.tenant_id == tenant_id,
            RemediationRequest.action == RemediationAction.RECLAIM_LICENSE_SEAT,
            RemediationRequest.status == RemediationStatus.COMPLETED,
            activity_at >= start_dt,
            activity_at < end_dt_exclusive,
            RemediationRequest.executed_at.is_not(None),
        )
    )
    cycle_hours = _completion_cycle_hours(completed_rows)
    avg_time_to_complete_hours = (
        round(sum(cycle_hours) / len(cycle_hours), 2) if cycle_hours else None
    )

    completion_target = 70.0
    failure_target = 20.0
    in_flight_target = 50.0
    meets_target = (
        completion_rate >= completion_target
        and failure_rate <= failure_target
        and in_flight_ratio <= in_flight_target
    )

    return AcceptanceKpiMetric(
        key="license_governance_reliability",
        label="License Governance Reliability",
        available=True,
        target=(
            f">={completion_target:.0f}% completion, "
            f"<={failure_target:.0f}% failures, <= {in_flight_target:.0f}% in-flight"
        ),
        actual=(
            f"{completion_rate:.2f}% completion, {failure_rate:.2f}% failed, "
            f"{in_flight_requests}/{total_requests} in-flight"
        ),
        meets_target=meets_target,
        details={
            "active_license_connections": active_connections,
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "in_flight_requests": in_flight_requests,
            "completion_rate_percent": completion_rate,
            "failure_rate_percent": failure_rate,
            "in_flight_ratio_percent": in_flight_ratio,
            "avg_time_to_complete_hours": avg_time_to_complete_hours,
            "window": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        },
    )


def _rate(numerator: int, denominator: int, *, default: float) -> float:
    return round((numerator / denominator) * 100.0, 2) if denominator > 0 else default


def _completion_cycle_hours(completed_rows: Any) -> list[float]:
    cycle_hours: list[float] = []
    for created_at, executed_at in completed_rows:
        if created_at is None or executed_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if executed_at.tzinfo is None:
            executed_at = executed_at.replace(tzinfo=timezone.utc)
        if executed_at >= created_at:
            cycle_hours.append((executed_at - created_at).total_seconds() / 3600.0)
    return cycle_hours
