from __future__ import annotations

import math
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Optional
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.models.cloud import CloudAccount, CostRecord
from app.models.license_connection import LicenseConnection
from app.models.unit_economics_settings import UnitEconomicsSettings
from app.shared.core.async_utils import maybe_await
from app.shared.core.connection_state import is_connection_active
from app.shared.core.datetime_ops import as_utc_datetime

from .costs_license_governance_metrics import (
    compute_license_governance_kpi as compute_license_governance_kpi,
)
from .costs_models import (
    AcceptanceKpiMetric as AcceptanceKpiMetric,
    IngestionSLAResponse,
    ProviderRecencyResponse,
    UnitEconomicsSettingsResponse,
)


def _coerce_finite_float(value: Any, *, field_name: str) -> float:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not amount.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return float(amount)


def settings_to_response(
    settings: UnitEconomicsSettings,
) -> UnitEconomicsSettingsResponse:
    return UnitEconomicsSettingsResponse(
        id=settings.id,
        default_request_volume=_coerce_finite_float(
            settings.default_request_volume, field_name="default_request_volume"
        ),
        default_workload_volume=_coerce_finite_float(
            settings.default_workload_volume, field_name="default_workload_volume"
        ),
        default_customer_volume=_coerce_finite_float(
            settings.default_customer_volume, field_name="default_customer_volume"
        ),
        anomaly_threshold_percent=_coerce_finite_float(
            settings.anomaly_threshold_percent,
            field_name="anomaly_threshold_percent",
        ),
        target_spend_reduction_pct=_coerce_finite_float(
            settings.target_spend_reduction_pct,
            field_name="target_spend_reduction_pct",
        ),
        target_rollout_days=int(settings.target_rollout_days),
        target_team_members=int(settings.target_team_members),
        target_blended_hourly_rate=_coerce_finite_float(
            settings.target_blended_hourly_rate,
            field_name="target_blended_hourly_rate",
        ),
    )


async def get_or_create_unit_settings(
    db: AsyncSession, tenant_id: UUID
) -> UnitEconomicsSettings:
    settings = await db.scalar(
        select(UnitEconomicsSettings).where(
            UnitEconomicsSettings.tenant_id == tenant_id
        )
    )
    if settings:
        return settings

    settings = UnitEconomicsSettings(tenant_id=tenant_id)
    db.add(settings)
    await db.commit()
    await db.refresh(settings)
    return settings


async def get_unit_settings_snapshot(
    db: AsyncSession, tenant_id: UUID
) -> UnitEconomicsSettings:
    settings = await db.scalar(
        select(UnitEconomicsSettings).where(
            UnitEconomicsSettings.tenant_id == tenant_id
        )
    )
    if settings is not None:
        return settings

    return UnitEconomicsSettings(
        id=uuid4(),
        tenant_id=tenant_id,
        default_request_volume=1000.0,
        default_workload_volume=100.0,
        default_customer_volume=50.0,
        anomaly_threshold_percent=20.0,
        target_spend_reduction_pct=15.0,
        target_rollout_days=30,
        target_team_members=10,
        target_blended_hourly_rate=75.0,
    )


async def window_total_cost(
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    provider: Optional[str] = None,
) -> Decimal:
    stmt = select(func.coalesce(func.sum(CostRecord.cost_usd), 0)).where(
        CostRecord.tenant_id == tenant_id,
        CostRecord.recorded_at >= start_date,
        CostRecord.recorded_at <= end_date,
    )
    if provider:
        stmt = stmt.join(CloudAccount, CostRecord.account_id == CloudAccount.id).where(
            CloudAccount.provider == provider.lower()
        )
    result = await db.execute(stmt)
    value = result.scalar_one_or_none()
    if value is None:
        return Decimal("0")
    return Decimal(value)


def is_connection_active_state(connection: Any) -> bool:
    return is_connection_active(connection)


def build_provider_recency_summary(
    provider: str,
    connections: list[Any],
    *,
    now: datetime,
    recency_target_hours: int,
) -> ProviderRecencyResponse:
    threshold = now - timedelta(hours=recency_target_hours)
    active_connections = [
        conn for conn in connections if is_connection_active_state(conn)
    ]

    recently_ingested = 0
    stale_connections = 0
    never_ingested = 0
    latest_ingested_at: Optional[datetime] = None

    for conn in active_connections:
        last_ingested_at = getattr(conn, "last_ingested_at", None)
        if isinstance(last_ingested_at, datetime):
            if last_ingested_at.tzinfo is None:
                last_ingested_at = last_ingested_at.replace(tzinfo=timezone.utc)
            if latest_ingested_at is None or last_ingested_at > latest_ingested_at:
                latest_ingested_at = last_ingested_at
            if last_ingested_at >= threshold:
                recently_ingested += 1
            else:
                stale_connections += 1
        else:
            never_ingested += 1

    meets_recency_target = (
        len(active_connections) > 0 and stale_connections == 0 and never_ingested == 0
    )

    return ProviderRecencyResponse(
        provider=provider,
        active_connections=len(active_connections),
        recently_ingested=recently_ingested,
        stale_connections=stale_connections,
        never_ingested=never_ingested,
        latest_ingested_at=latest_ingested_at.isoformat()
        if latest_ingested_at
        else None,
        recency_target_hours=recency_target_hours,
        meets_recency_target=meets_recency_target,
    )


async def compute_provider_recency_summaries(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    recency_target_hours: int,
) -> list[ProviderRecencyResponse]:
    from app.models.aws_connection import AWSConnection
    from app.models.azure_connection import AzureConnection
    from app.models.gcp_connection import GCPConnection
    from app.models.hybrid_connection import HybridConnection
    from app.models.platform_connection import PlatformConnection
    from app.models.saas_connection import SaaSConnection

    now = datetime.now(timezone.utc)
    provider_models: list[tuple[str, Any]] = [
        ("aws", AWSConnection),
        ("azure", AzureConnection),
        ("gcp", GCPConnection),
        ("saas", SaaSConnection),
        ("license", LicenseConnection),
        ("platform", PlatformConnection),
        ("hybrid", HybridConnection),
    ]
    summaries: list[ProviderRecencyResponse] = []
    for provider, model in provider_models:
        result = await db.execute(select(model).where(model.tenant_id == tenant_id))
        threshold = now - timedelta(hours=recency_target_hours)
        active_connections = 0
        recently_ingested = 0
        stale_connections = 0
        never_ingested = 0
        latest_ingested_at: Optional[datetime] = None

        for conn in result.scalars():
            if not is_connection_active_state(conn):
                continue
            active_connections += 1
            last_ingested_at = getattr(conn, "last_ingested_at", None)
            if isinstance(last_ingested_at, datetime):
                if last_ingested_at.tzinfo is None:
                    last_ingested_at = last_ingested_at.replace(tzinfo=timezone.utc)
                if latest_ingested_at is None or last_ingested_at > latest_ingested_at:
                    latest_ingested_at = last_ingested_at
                if last_ingested_at >= threshold:
                    recently_ingested += 1
                else:
                    stale_connections += 1
            else:
                never_ingested += 1

        summaries.append(
            ProviderRecencyResponse(
                provider=provider,
                active_connections=active_connections,
                recently_ingested=recently_ingested,
                stale_connections=stale_connections,
                never_ingested=never_ingested,
                latest_ingested_at=latest_ingested_at.isoformat()
                if latest_ingested_at
                else None,
                recency_target_hours=recency_target_hours,
                meets_recency_target=(
                    active_connections > 0
                    and stale_connections == 0
                    and never_ingested == 0
                ),
            )
        )
    return summaries


async def compute_ingestion_sla_metrics(
    db: AsyncSession,
    tenant_id: UUID,
    *,
    window_hours: int,
    target_success_rate_percent: float,
) -> IngestionSLAResponse:
    window_start = datetime.now(timezone.utc) - timedelta(hours=window_hours)

    result = await db.execute(
        select(BackgroundJob).where(
            BackgroundJob.tenant_id == tenant_id,
            BackgroundJob.job_type == JobType.COST_INGESTION.value,
            BackgroundJob.created_at >= window_start,
        )
    )
    jobs = list(await maybe_await(result.scalars().all()))
    total_jobs = 0
    successful_jobs = 0
    failed_jobs = 0
    latest_completed_at_dt: Optional[datetime] = None
    duration_samples: list[float] = []
    records_ingested = 0

    for job in jobs:
        total_jobs += 1
        completed_at = (
            as_utc_datetime(job.completed_at)
            if isinstance(job.completed_at, datetime)
            else None
        )
        started_at = (
            as_utc_datetime(job.started_at)
            if isinstance(job.started_at, datetime)
            else None
        )
        if job.status == JobStatus.COMPLETED.value:
            successful_jobs += 1
        if job.status in {JobStatus.FAILED.value, JobStatus.DEAD_LETTER.value}:
            failed_jobs += 1

        if completed_at and (
            latest_completed_at_dt is None or completed_at > latest_completed_at_dt
        ):
            latest_completed_at_dt = completed_at

        if started_at and completed_at:
            duration = (completed_at - started_at).total_seconds()
            if duration >= 0:
                duration_samples.append(duration)

        if job.status == JobStatus.COMPLETED.value and isinstance(job.result, dict):
            ingested_value = job.result.get("ingested")
            if isinstance(ingested_value, (int, float)):
                records_ingested += int(ingested_value)

    success_rate_percent = (
        round((successful_jobs / total_jobs) * 100, 2) if total_jobs else 0.0
    )
    meets_sla = total_jobs > 0 and success_rate_percent >= target_success_rate_percent

    avg_duration_seconds = (
        round(sum(duration_samples) / len(duration_samples), 2)
        if duration_samples
        else None
    )
    p95_duration_seconds: Optional[float] = None
    if duration_samples:
        sorted_durations = sorted(duration_samples)
        p95_index = max(0, math.ceil(len(sorted_durations) * 0.95) - 1)
        p95_duration_seconds = round(sorted_durations[p95_index], 2)

    return IngestionSLAResponse(
        window_hours=window_hours,
        target_success_rate_percent=round(target_success_rate_percent, 2),
        total_jobs=total_jobs,
        successful_jobs=successful_jobs,
        failed_jobs=failed_jobs,
        success_rate_percent=success_rate_percent,
        meets_sla=meets_sla,
        latest_completed_at=latest_completed_at_dt.isoformat()
        if latest_completed_at_dt
        else None,
        avg_duration_seconds=avg_duration_seconds,
        p95_duration_seconds=p95_duration_seconds,
        records_ingested=records_ingested,
    )
