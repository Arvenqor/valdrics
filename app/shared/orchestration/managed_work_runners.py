from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, ContextManager
from uuid import UUID

import sqlalchemy as sa
import structlog
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.models.tenant import Tenant
from app.modules.governance.domain.jobs.processor import JobProcessor
from app.modules.governance.domain.scheduler.cohorts import TenantCohort
from app.modules.governance.domain.scheduler.metrics import (
    BACKGROUND_JOBS_ENQUEUED_SCHEDULER as BACKGROUND_JOBS_ENQUEUED,
    SCHEDULER_DEADLOCK_DETECTED,
    SCHEDULER_JOB_DURATION,
    SCHEDULER_JOB_RUNS,
)
from app.modules.reporting.domain.aggregator import CostAggregator
from app.modules.reporting.domain.persistence import CostPersistenceService
from app.shared.core.config import get_settings
from app.shared.core.connection_queries import list_active_connections_all_tenants
from app.shared.core.connection_state import (
    is_connection_active,
    resolve_connection_region,
)
from app.shared.core.ops_metrics import (
    STUCK_JOB_COUNT,
    set_background_jobs_overdue_pending,
)
from app.shared.core.provider import (
    normalize_provider,
    resolve_provider_from_connection,
)
from app.shared.core.tracing import get_tracer
from app.shared.db.session import async_session_maker, mark_session_system_context
from app.tasks.scheduler_funnel_ops import (
    refresh_landing_funnel_health_logic as _refresh_landing_funnel_health_logic_impl,
)
from app.tasks.scheduler_remediation_ops import (
    remediation_sweep_logic as _remediation_sweep_logic_impl,
)
from app.tasks.scheduler_runtime_ops import (
    cap_scope_items as _cap_scope_items_impl,
    coerce_positive_limit as _coerce_positive_limit_impl,
    open_db_session as _open_db_session_impl,
    scheduler_span as _scheduler_span_impl,
    system_sweep_connection_limit as _system_sweep_connection_limit_impl,
    system_sweep_tenant_limit as _system_sweep_tenant_limit_impl,
)
from app.tasks.scheduler_sweep_ops import (
    acceptance_sweep_logic as _acceptance_sweep_logic_impl,
    billing_sweep_logic as _billing_sweep_logic_impl,
    enforcement_reconciliation_sweep_logic as _enforcement_reconciliation_sweep_logic_impl,
    maintenance_sweep_logic as _maintenance_sweep_logic_impl,
)

logger = structlog.get_logger()
tracer = get_tracer(__name__)

SCHEDULER_RECOVERABLE_ERRORS = (
    RuntimeError,
    ValueError,
    TypeError,
    OSError,
    AttributeError,
    asyncio.TimeoutError,
    SQLAlchemyError,
)

LICENSE_SWEEP_RECOVERABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    sa.exc.DBAPIError,
    RuntimeError,
    TypeError,
    ValueError,
)


def _perf_counter() -> float:
    return time.perf_counter()


async def _load_active_remediation_connections(
    db: AsyncSession,
    *args: Any,
    **kwargs: Any,
) -> list[Any]:
    return await list_active_connections_all_tenants(db, *args, **kwargs)


def _coerce_positive_limit(value: Any, *, default: int) -> int:
    return _coerce_positive_limit_impl(value, default=default)


def _system_sweep_tenant_limit() -> int:
    return _system_sweep_tenant_limit_impl(
        get_settings_fn=get_settings,
        coerce_positive_limit_fn=_coerce_positive_limit,
    )


def _system_sweep_connection_limit() -> int:
    return _system_sweep_connection_limit_impl(
        get_settings_fn=get_settings,
        coerce_positive_limit_fn=_coerce_positive_limit,
    )


def _cap_scope_items(items: Sequence[Any], *, scope: str, limit: int) -> list[Any]:
    return _cap_scope_items_impl(
        items,
        scope=scope,
        limit=limit,
        logger=logger,
    )


def _scheduler_span(name: str, **attributes: object) -> ContextManager[None]:
    return _scheduler_span_impl(
        name,
        tracer=tracer,
        **attributes,
    )


@asynccontextmanager
async def _open_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with _open_db_session_impl(
        async_session_maker_fn=async_session_maker,
        mark_session_system_context_fn=mark_session_system_context,
        logger=logger,
        asyncio_module=asyncio,
    ) as session:
        yield session


def _resolve_insert_dialect_name(db: AsyncSession | None = None) -> str:
    bind = getattr(db, "bind", None)
    dialect_name = str(
        getattr(getattr(bind, "dialect", None), "name", "") or ""
    ).lower()
    return dialect_name or "postgresql"


def _background_job_insert_statement(
    db: AsyncSession | None,
    values: list[dict[str, Any]],
) -> Any:
    dialect_name = _resolve_insert_dialect_name(db)
    if dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        return (
            sqlite_insert(BackgroundJob)
            .values(values)
            .on_conflict_do_nothing(index_elements=["deduplication_key"])
        )

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    return (
        pg_insert(BackgroundJob)
        .values(values)
        .on_conflict_do_nothing(index_elements=["deduplication_key"])
    )


def _background_job_insert_fn(model: Any) -> Any:
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    return pg_insert(model)


async def run_background_job_processing(payload: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    requested_limit = payload.get("limit")
    batch_size = max(
        1,
        int(
            requested_limit
            if requested_limit is not None
            else getattr(settings, "BACKGROUND_JOB_PROCESS_BATCH_SIZE", 25)
        ),
    )
    max_batches = max(
        1,
        int(getattr(settings, "BACKGROUND_JOB_PROCESS_MAX_BATCHES_PER_TICK", 8)),
    )
    job_name = "background_job_processing"
    totals = {"processed": 0, "succeeded": 0, "failed": 0, "batches": 0}
    start_time = _perf_counter()

    with _scheduler_span("scheduler.process_background_jobs", job_name=job_name):
        try:
            for _ in range(max_batches):
                async with _open_db_session() as db:
                    processor = JobProcessor(db)
                    batch = await processor.process_pending_jobs(limit=batch_size)
                totals["batches"] += 1
                totals["processed"] += int(batch.get("processed", 0))
                totals["succeeded"] += int(batch.get("succeeded", 0))
                totals["failed"] += int(batch.get("failed", 0))
                if int(batch.get("processed", 0)) < batch_size:
                    break

            SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="success").inc()
            logger.info("background_job_processing_completed", **totals)
        except SCHEDULER_RECOVERABLE_ERRORS as exc:
            SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="failure").inc()
            logger.error("background_job_processing_failed", error=str(exc), **totals)
            raise
        finally:
            SCHEDULER_JOB_DURATION.labels(job_name=job_name).observe(
                _perf_counter() - start_time
            )

    return totals


async def run_background_job_stuck_detection(
    _payload: dict[str, Any],
) -> dict[str, Any]:
    settings = get_settings()
    alert_minutes = max(
        1,
        int(
            getattr(
                settings,
                "BACKGROUND_JOB_PENDING_OVERDUE_ALERT_MINUTES",
                60,
            )
        ),
    )
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=alert_minutes)

    async with _open_db_session() as db:
        stmt = sa.select(BackgroundJob).where(
            BackgroundJob.status == JobStatus.PENDING,
            BackgroundJob.scheduled_for <= cutoff,
            sa.not_(BackgroundJob.is_deleted),
        )
        result = await db.execute(stmt)
        overdue_jobs = result.scalars().all()

    STUCK_JOB_COUNT.set(len(overdue_jobs))
    set_background_jobs_overdue_pending(len(overdue_jobs))

    if overdue_jobs:
        logger.critical(
            "overdue_pending_jobs_detected",
            count=len(overdue_jobs),
            alert_minutes=alert_minutes,
            job_ids=[str(job.id) for job in overdue_jobs[:10]],
        )

    return {
        "stuck_jobs": len(overdue_jobs),
        "alert_minutes": alert_minutes,
    }


async def run_cohort_analysis(payload: dict[str, Any]) -> dict[str, Any]:
    raw_value = str(payload.get("cohort", "") or "").strip()
    if not raw_value:
        raise ValueError("payload.cohort is required for scheduler.cohort_analysis.")

    try:
        target_cohort = TenantCohort(raw_value)
    except ValueError:
        target_cohort = TenantCohort[raw_value]

    job_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        correlation_id=job_id,
        job_type="scheduler_cohort",
        cohort=target_cohort.value,
    )

    job_name = f"cohort_{target_cohort.value.lower()}_enqueue"
    start_time = _perf_counter()
    max_retries = 3
    retry_count = 0

    with _scheduler_span(
        "scheduler.cohort_analysis",
        job_name=job_name,
        cohort=target_cohort.value,
        correlation_id=job_id,
    ):
        while retry_count < max_retries:
            try:
                async with _open_db_session() as db:
                    begin_ctx = db.begin()
                    if (
                        asyncio.iscoroutine(begin_ctx) or inspect.isawaitable(begin_ctx)
                    ) and not hasattr(begin_ctx, "__aenter__"):
                        begin_ctx = await begin_ctx
                    async with begin_ctx:
                        with _scheduler_span(
                            "scheduler.cohort_analysis.load_tenants",
                            cohort=target_cohort.value,
                            retry_count=retry_count,
                        ):
                            tenant_limit = _system_sweep_tenant_limit()
                            query = (
                                sa.select(Tenant)
                                .limit(tenant_limit + 1)
                                .with_for_update(skip_locked=True)
                            )

                            if target_cohort == TenantCohort.HIGH_VALUE:
                                query = query.where(
                                    Tenant.plan.in_(["enterprise", "pro"])
                                )
                            elif target_cohort == TenantCohort.ACTIVE:
                                query = query.where(Tenant.plan == "growth")
                            else:
                                query = query.where(Tenant.plan == "starter")

                            result = await db.execute(query)
                            cohort_tenants = _cap_scope_items(
                                result.scalars().all(),
                                scope=f"cohort:{target_cohort.value}",
                                limit=tenant_limit,
                            )

                        if not cohort_tenants:
                            logger.info(
                                "scheduler_cohort_empty",
                                cohort=target_cohort.value,
                            )
                            return {"cohort": target_cohort.value, "jobs_enqueued": 0}

                        now = datetime.now(timezone.utc)
                        bucket = now.replace(minute=0, second=0, microsecond=0)
                        if target_cohort == TenantCohort.HIGH_VALUE:
                            bucket = bucket.replace(hour=(now.hour // 6) * 6)
                        elif target_cohort == TenantCohort.ACTIVE:
                            bucket = bucket.replace(hour=(now.hour // 3) * 3)

                        bucket_str = bucket.isoformat()
                        jobs_to_insert: list[dict[str, Any]] = []

                        with _scheduler_span(
                            "scheduler.cohort_analysis.build_jobs",
                            cohort=target_cohort.value,
                            tenant_count=len(cohort_tenants),
                        ):
                            from app.shared.core.pricing import (
                                FeatureFlag,
                                is_feature_enabled,
                            )

                            for tenant in cohort_tenants:
                                tenant_plan = getattr(tenant, "plan", "")
                                job_types = [JobType.ZOMBIE_SCAN]
                                if is_feature_enabled(
                                    tenant_plan,
                                    FeatureFlag.INGESTION_SLA,
                                ):
                                    job_types.append(JobType.COST_INGESTION)
                                if is_feature_enabled(
                                    tenant_plan,
                                    FeatureFlag.LLM_ANALYSIS,
                                ):
                                    job_types.append(JobType.FINOPS_ANALYSIS)
                                if is_feature_enabled(
                                    tenant_plan,
                                    FeatureFlag.ANOMALY_DETECTION,
                                ):
                                    job_types.append(JobType.COST_ANOMALY_DETECTION)

                                for job_type in job_types:
                                    dedup_key = (
                                        f"{tenant.id}:{job_type.value}:{bucket_str}"
                                    )
                                    jobs_to_insert.append(
                                        {
                                            "job_type": job_type.value,
                                            "tenant_id": tenant.id,
                                            "status": JobStatus.PENDING,
                                            "scheduled_for": now,
                                            "created_at": now,
                                            "deduplication_key": dedup_key,
                                        }
                                    )

                        jobs_enqueued = 0
                        if jobs_to_insert:
                            with _scheduler_span(
                                "scheduler.cohort_analysis.insert_jobs",
                                cohort=target_cohort.value,
                                job_count=len(jobs_to_insert),
                            ):
                                for index in range(0, len(jobs_to_insert), 500):
                                    chunk = jobs_to_insert[index : index + 500]
                                    result_proxy = await db.execute(
                                        _background_job_insert_statement(db, chunk)
                                    )
                                    if hasattr(result_proxy, "rowcount"):
                                        jobs_enqueued += int(result_proxy.rowcount or 0)

                        if jobs_enqueued > 0:
                            BACKGROUND_JOBS_ENQUEUED.labels(
                                job_type="cohort_scan",
                                cohort=target_cohort.value,
                            ).inc(jobs_enqueued)

                        logger.info(
                            "cohort_scan_enqueued",
                            cohort=target_cohort.value,
                            tenants=len(cohort_tenants),
                            jobs_enqueued=jobs_enqueued,
                        )

                SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="success").inc()
                break
            except SCHEDULER_RECOVERABLE_ERRORS as exc:
                retry_count += 1
                if "deadlock" in str(exc).lower() or "concurrent" in str(exc).lower():
                    SCHEDULER_DEADLOCK_DETECTED.labels(cohort=target_cohort.value).inc()
                    if retry_count < max_retries:
                        backoff = 2 ** (retry_count - 1)
                        logger.warning(
                            "scheduler_deadlock_retry",
                            cohort=target_cohort.value,
                            attempt=retry_count,
                            backoff=backoff,
                        )
                        await asyncio.sleep(backoff)
                        continue

                logger.error(
                    "scheduler_cohort_enqueue_failed",
                    job=job_name,
                    error=str(exc),
                    attempt=retry_count,
                )
                SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="failure").inc()
                break

        SCHEDULER_JOB_DURATION.labels(job_name=job_name).observe(
            _perf_counter() - start_time
        )

    return {"cohort": target_cohort.value}


async def run_remediation_sweep(_payload: dict[str, Any]) -> dict[str, Any]:
    from app.modules.governance.domain.scheduler.orchestrator import (
        SchedulerOrchestrator,
    )

    await _remediation_sweep_logic_impl(
        open_db_session_fn=_open_db_session,
        scheduler_span_fn=_scheduler_span,
        system_sweep_connection_limit_fn=_system_sweep_connection_limit,
        cap_scope_items_fn=_cap_scope_items,
        logger=logger,
        list_active_connections_all_tenants_fn=_load_active_remediation_connections,
        is_connection_active_fn=is_connection_active,
        scheduler_orchestrator_cls=SchedulerOrchestrator,
        async_session_maker_fn=async_session_maker,
        resolve_provider_from_connection_fn=resolve_provider_from_connection,
        normalize_provider_fn=normalize_provider,
        resolve_connection_region_fn=resolve_connection_region,
        background_job_model=BackgroundJob,
        job_type=JobType,
        job_status=JobStatus,
        insert_fn=_background_job_insert_fn,
        scheduler_job_runs=SCHEDULER_JOB_RUNS,
        scheduler_job_duration=SCHEDULER_JOB_DURATION,
        datetime_cls=datetime,
        timezone_obj=timezone,
        timedelta_cls=timedelta,
        uuid_cls=UUID,
        asyncio_module=asyncio,
        inspect_module=inspect,
        time_module=time,
        recoverable_errors=SCHEDULER_RECOVERABLE_ERRORS,
    )
    return {}


async def run_billing_sweep(_payload: dict[str, Any]) -> dict[str, Any]:
    await _billing_sweep_logic_impl(
        open_db_session_fn=_open_db_session,
        scheduler_span_fn=_scheduler_span,
        logger=logger,
        scheduler_job_runs=SCHEDULER_JOB_RUNS,
        scheduler_job_duration=SCHEDULER_JOB_DURATION,
        background_jobs_enqueued=BACKGROUND_JOBS_ENQUEUED,
        sa=sa,
        insert=_background_job_insert_fn,
        background_job_model=BackgroundJob,
        job_status=JobStatus,
        job_type=JobType,
        time_module=time,
        asyncio_module=asyncio,
    )
    return {}


async def run_acceptance_sweep(_payload: dict[str, Any]) -> dict[str, Any]:
    await _acceptance_sweep_logic_impl(
        open_db_session_fn=_open_db_session,
        scheduler_span_fn=_scheduler_span,
        logger=logger,
        scheduler_job_runs=SCHEDULER_JOB_RUNS,
        scheduler_job_duration=SCHEDULER_JOB_DURATION,
        background_jobs_enqueued=BACKGROUND_JOBS_ENQUEUED,
        sa=sa,
        insert=_background_job_insert_fn,
        tenant_model=Tenant,
        background_job_model=BackgroundJob,
        job_status=JobStatus,
        job_type=JobType,
        system_sweep_tenant_limit_fn=_system_sweep_tenant_limit,
        cap_scope_items_fn=_cap_scope_items,
        datetime_module=datetime,
        timezone_obj=timezone,
        asyncio_module=asyncio,
    )
    return {}


async def run_license_governance_sweep(_payload: dict[str, Any]) -> dict[str, Any]:
    async with _open_db_session() as db:
        begin_ctx = db.begin()
        if (
            asyncio.iscoroutine(begin_ctx) or inspect.isawaitable(begin_ctx)
        ) and not hasattr(begin_ctx, "__aenter__"):
            begin_ctx = await begin_ctx
        async with begin_ctx:
            tenant_limit = _system_sweep_tenant_limit()
            result = await db.execute(
                sa.select(Tenant.id)
                .limit(tenant_limit + 1)
                .with_for_update(skip_locked=True)
            )
            tenant_ids = _cap_scope_items(
                result.scalars().all(),
                scope="license_governance_tenants",
                limit=tenant_limit,
            )
            now = datetime.now(timezone.utc)
            bucket_str = now.strftime("%Y-%m-%d")
            jobs_enqueued = 0

            from sqlalchemy.dialects.postgresql import insert

            for tenant_id in tenant_ids:
                dedup_key = (
                    f"{tenant_id}:{JobType.LICENSE_GOVERNANCE.value}:{bucket_str}"
                )
                stmt = (
                    insert(BackgroundJob)
                    .values(
                        job_type=JobType.LICENSE_GOVERNANCE.value,
                        tenant_id=tenant_id,
                        status=JobStatus.PENDING.value,
                        scheduled_for=now,
                        created_at=now,
                        deduplication_key=dedup_key,
                        priority=0,
                    )
                    .on_conflict_do_nothing(index_elements=["deduplication_key"])
                )
                result_proxy = await db.execute(stmt)
                if hasattr(result_proxy, "rowcount") and result_proxy.rowcount > 0:
                    jobs_enqueued += 1
                    BACKGROUND_JOBS_ENQUEUED.labels(
                        job_type=JobType.LICENSE_GOVERNANCE.value,
                        cohort="LICENSE",
                    ).inc()

            logger.info(
                "license_governance_sweep_enqueued",
                tenants=len(tenant_ids),
                jobs_enqueued=jobs_enqueued,
                bucket=bucket_str,
            )

    return {"jobs_enqueued": jobs_enqueued}


async def run_enforcement_reconciliation_sweep(
    _payload: dict[str, Any],
) -> dict[str, Any]:
    await _enforcement_reconciliation_sweep_logic_impl(
        get_settings_fn=get_settings,
        open_db_session_fn=_open_db_session,
        scheduler_span_fn=_scheduler_span,
        logger=logger,
        scheduler_job_runs=SCHEDULER_JOB_RUNS,
        scheduler_job_duration=SCHEDULER_JOB_DURATION,
        background_jobs_enqueued=BACKGROUND_JOBS_ENQUEUED,
        sa=sa,
        insert=_background_job_insert_fn,
        tenant_model=Tenant,
        background_job_model=BackgroundJob,
        job_status=JobStatus,
        job_type=JobType,
        system_sweep_tenant_limit_fn=_system_sweep_tenant_limit,
        cap_scope_items_fn=_cap_scope_items,
        datetime_cls=datetime,
        timezone_obj=timezone,
        time_module=time,
        asyncio_module=asyncio,
    )
    return {}


async def run_maintenance_sweep(_payload: dict[str, Any]) -> dict[str, Any]:
    await _maintenance_sweep_logic_impl(
        open_db_session_fn=_open_db_session,
        scheduler_span_fn=_scheduler_span,
        logger=logger,
        cost_persistence_service_cls=CostPersistenceService,
        cost_aggregator_cls=CostAggregator,
        sa=sa,
        inspect_module=inspect,
        datetime_cls=datetime,
        timezone_obj=timezone,
        timedelta_cls=timedelta,
    )
    return {}


async def run_landing_funnel_health_refresh(_payload: dict[str, Any]) -> dict[str, Any]:
    job_name = "landing_funnel_health_refresh"
    start_time = _perf_counter()

    try:
        await _refresh_landing_funnel_health_logic_impl(
            open_db_session_fn=_open_db_session,
            scheduler_span_fn=_scheduler_span,
            logger=logger,
            datetime_cls=datetime,
            timezone_obj=timezone,
        )
        SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="success").inc()
    except SCHEDULER_RECOVERABLE_ERRORS as exc:
        SCHEDULER_JOB_RUNS.labels(job_name=job_name, status="failure").inc()
        logger.error(
            "landing_funnel_health_refresh_failed",
            error=str(exc),
            error_type=type(exc).__name__,
        )
        raise
    finally:
        SCHEDULER_JOB_DURATION.labels(job_name=job_name).observe(
            _perf_counter() - start_time
        )

    return {}
