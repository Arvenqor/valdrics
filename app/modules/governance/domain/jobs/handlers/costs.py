"""Cost Management Job Handlers."""

import base64
import csv
import hashlib
import io
import structlog
from typing import Any, AsyncGenerator, AsyncIterator, Dict
from datetime import datetime, timezone, timedelta, date, time
from decimal import Decimal, InvalidOperation
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.background_job import BackgroundJob
from app.modules.governance.domain.jobs.errors import PermanentJobError
from app.modules.governance.domain.jobs.handlers.base import BaseJobHandler
from app.shared.core.async_utils import maybe_await
from app.shared.core.connection_queries import list_tenant_connections
from app.shared.core.connection_state import resolve_connection_profile

logger = structlog.get_logger()
COST_INGESTION_CONNECTION_RECOVERABLE_EXCEPTIONS = (
    RuntimeError,
    ConnectionError,
    TimeoutError,
    OSError,
)
ATTRIBUTION_TRIGGER_RECOVERABLE_EXCEPTIONS = (
    RuntimeError,
    ImportError,
    OSError,
)
COST_EXPORT_PROVIDER_FILTERS = {
    "ai",
    "aws",
    "azure",
    "gcp",
    "saas",
    "license",
    "platform",
    "hybrid",
}
COST_EXPORT_INLINE_DEFAULT_MAX_BYTES = 1_000_000
COST_EXPORT_INLINE_HARD_MAX_BYTES = 5_000_000


def _normalize_record_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise ValueError("timestamp must not be empty")
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError("timestamp must be an ISO 8601 datetime string") from exc
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    raise ValueError("timestamp must be a datetime or ISO 8601 string")


def _normalize_cost_amount(value: Any) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("cost_usd must be numeric") from exc


def _require_tenant_id(job: BackgroundJob) -> UUID:
    if job.tenant_id is None:
        raise PermanentJobError("tenant_id required")
    return job.tenant_id


def _require_iso_date(payload: dict[str, Any], key: str) -> date:
    raw_value = payload.get(key)
    if not isinstance(raw_value, str):
        raise PermanentJobError(f"{key} must be an ISO date string")
    try:
        return date.fromisoformat(raw_value)
    except ValueError as exc:
        raise PermanentJobError(f"{key} must be an ISO date string") from exc


def _normalize_checkpoint(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    raw_checkpoint = payload.get("checkpoint", {})
    checkpoint = dict(raw_checkpoint) if isinstance(raw_checkpoint, dict) else {}
    raw_completed = checkpoint.get("completed_connections", [])
    completed_connections = [
        str(connection_id).strip()
        for connection_id in raw_completed
        if str(connection_id).strip()
    ]
    checkpoint["completed_connections"] = completed_connections
    return checkpoint, completed_connections


def _serialize_anomaly(item: Any) -> dict[str, Any]:
    return {
        "day": item.day.isoformat(),
        "provider": item.provider,
        "account_id": str(item.account_id),
        "account_name": item.account_name,
        "service": item.service,
        "actual_cost_usd": float(item.actual_cost_usd),
        "expected_cost_usd": float(item.expected_cost_usd),
        "delta_cost_usd": float(item.delta_cost_usd),
        "percent_change": item.percent_change,
        "kind": item.kind,
        "probable_cause": item.probable_cause,
        "confidence": item.confidence,
        "severity": item.severity,
    }


def _normalize_cost_export_format(value: Any) -> str:
    normalized = str(value or "focus_v13_csv").strip().lower()
    if normalized in {"csv", "focus_csv", "focus_v13", "focus_v13_csv"}:
        return "focus_v13_csv"
    raise PermanentJobError("format must be one of: focus_v13_csv")


def _normalize_cost_export_provider(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip().lower()
    if not normalized:
        return None
    if normalized not in COST_EXPORT_PROVIDER_FILTERS:
        supported = ", ".join(sorted(COST_EXPORT_PROVIDER_FILTERS))
        raise PermanentJobError(f"provider must be one of: {supported}")
    return normalized


def _payload_bool(payload: dict[str, Any], key: str, *, default: bool = False) -> bool:
    value = payload.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    raise PermanentJobError(f"{key} must be a boolean")


def _payload_positive_int(
    payload: dict[str, Any],
    key: str,
    *,
    default: int,
    maximum: int,
) -> int:
    raw_value = payload.get(key, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise PermanentJobError(f"{key} must be a positive integer") from exc
    if value <= 0 or value > maximum:
        raise PermanentJobError(f"{key} must be between 1 and {maximum}")
    return value


class CostIngestionHandler(BaseJobHandler):
    """Processes high-fidelity cost ingestion for cloud accounts (Multi-Cloud)."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.shared.adapters.factory import AdapterFactory
        from app.modules.reporting.domain.persistence import CostPersistenceService
        from app.models.cloud import CloudAccount
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        tenant_id = _require_tenant_id(job)
        payload = job.payload or {}
        payload_start = payload.get("start_date")
        payload_end = payload.get("end_date")
        if (payload_start is None) ^ (payload_end is None):
            raise PermanentJobError(
                "Both start_date and end_date must be provided for backfill windows"
            )
        custom_window = payload_start is not None and payload_end is not None
        if custom_window:
            range_start = _require_iso_date(payload, "start_date")
            range_end = _require_iso_date(payload, "end_date")
            start_date = datetime.combine(range_start, time.min, tzinfo=timezone.utc)
            end_date = datetime.combine(range_end, time.max, tzinfo=timezone.utc)
        else:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=7)
        if start_date > end_date:
            raise PermanentJobError("start_date must be <= end_date")

        # 1. Load active connections across all providers (provider-neutral path).
        connections: list[Any] = await list_tenant_connections(
            db,
            tenant_id=tenant_id,
            active_only=True,
        )

        if not connections:
            return {"status": "skipped", "reason": "no_active_connections"}

        persistence = CostPersistenceService(db)
        results = []
        total_records_ingested = 0

        for conn in connections:
            profile = resolve_connection_profile(conn)
            profile_is_production = profile.get("is_production")
            is_production = (
                bool(profile_is_production)
                if isinstance(profile_is_production, bool)
                else False
            )
            criticality = profile.get("criticality")
            stmt = (
                pg_insert(CloudAccount)
                .values(
                    id=conn.id,
                    tenant_id=conn.tenant_id,
                    provider=conn.provider,
                    name=getattr(conn, "name", f"{conn.provider.upper()} Connection"),
                    is_production=is_production,
                    criticality=criticality if isinstance(criticality, str) else None,
                    is_active=True,
                )
                .on_conflict_do_update(
                    index_elements=["id"],
                    set_={
                        "provider": conn.provider,
                        "name": getattr(
                            conn, "name", f"{conn.provider.upper()} Connection"
                        ),
                        "is_production": is_production,
                        "criticality": (
                            criticality if isinstance(criticality, str) else None
                        ),
                    },
                )
            )
            await db.execute(stmt)
        # Removed redundant commit here as JobProcessor handles it (BE-TRANS-1)

        # 2. Process each connection via its appropriate adapter
        checkpoint, completed_conns = _normalize_checkpoint(payload)

        for conn in connections:
            conn_id_str = str(conn.id)
            if conn_id_str in completed_conns:
                logger.info(
                    "skipping_already_ingested_connection", connection_id=conn_id_str
                )
                continue

            try:
                adapter = AdapterFactory.get_adapter(conn)

                # Stream costs using normalized interface
                cost_stream_or_awaitable = adapter.stream_cost_and_usage(
                    start_date=start_date, end_date=end_date, granularity="HOURLY"
                )
                cost_stream = await maybe_await(cost_stream_or_awaitable)

                records_ingested = 0
                total_cost_acc = 0.0

                async def tracking_wrapper(
                    stream: AsyncIterator[dict[str, Any]],
                ) -> AsyncGenerator[dict[str, Any], None]:
                    nonlocal records_ingested, total_cost_acc
                    provider_key = (
                        str(getattr(conn, "provider", "") or "").strip().lower()
                    )
                    async for raw in stream:
                        if not isinstance(raw, dict):
                            continue
                        r = dict(raw)
                        # Enforce a stable normalized ingestion shape. Adapters may omit optional
                        # fields; we fill defaults here so persistence is consistent across providers.
                        if provider_key:
                            r.setdefault("provider", provider_key)
                        r.setdefault("service", "Unknown")
                        r.setdefault("region", "global")
                        r.setdefault("usage_type", "Usage")
                        r.setdefault("currency", "USD")
                        r.setdefault("resource_id", None)
                        r.setdefault("usage_amount", None)
                        r.setdefault("usage_unit", None)
                        r.setdefault(
                            "source_adapter",
                            f"{r.get('provider') or provider_key or 'unknown'}_adapter",
                        )
                        if not isinstance(r.get("tags"), dict):
                            r["tags"] = {}
                        r["timestamp"] = _normalize_record_timestamp(r.get("timestamp"))
                        normalized_cost = _normalize_cost_amount(r.get("cost_usd", 0))
                        r["cost_usd"] = normalized_cost

                        records_ingested += 1
                        total_cost_acc += float(normalized_cost)
                        yield r

                save_result = await persistence.save_records_stream(
                    records=tracking_wrapper(cost_stream),
                    tenant_id=str(tenant_id),
                    account_id=conn.id,  # Use UUID object (BE-UUID-1)
                    reconciliation_run_id=job.id,
                    is_preliminary=True,
                )

                conn.last_ingested_at = datetime.now(timezone.utc)
                db.add(conn)

                results.append(
                    {
                        "connection_id": str(conn.id),
                        "provider": conn.provider,
                        "records_ingested": save_result.get("records_saved", 0),
                        "total_cost": total_cost_acc,
                    }
                )
                total_records_ingested += int(save_result.get("records_saved", 0) or 0)
                if conn_id_str not in completed_conns:
                    completed_conns.append(conn_id_str)
                    checkpoint["completed_connections"] = completed_conns
                    job.payload = {**payload, "checkpoint": checkpoint}

            except COST_INGESTION_CONNECTION_RECOVERABLE_EXCEPTIONS as e:
                logger.error(
                    "cost_ingestion_connection_failed",
                    connection_id=str(conn.id),
                    error=str(e),
                )
                if hasattr(conn, "error_message"):
                    conn.error_message = str(e)[:255]
                    db.add(conn)
                results.append(
                    {
                        "connection_id": str(conn.id),
                        "status": "failed",
                        "error": str(e),
                        "total_cost": 0.0,
                    }
                )

        # 3. Trigger Attribution Engine (FinOps Audit 2)
        try:
            from app.modules.reporting.domain.attribution_engine import (
                AttributionEngine,
            )

            engine = AttributionEngine(db)
            if custom_window:
                attr_start = start_date.date()
                attr_end = end_date.date()
            else:
                # Use last 30 days for non-backfill ingestion.
                attr_end = datetime.now(timezone.utc).date()
                attr_start = attr_end - timedelta(days=30)
            await engine.apply_rules_to_tenant(
                tenant_id,
                start_date=attr_start,
                end_date=attr_end,
                commit=False,
            )
            logger.info("attribution_applied_post_ingestion", tenant_id=str(tenant_id))
        except ATTRIBUTION_TRIGGER_RECOVERABLE_EXCEPTIONS as e:
            logger.error(
                "attribution_trigger_failed", tenant_id=str(tenant_id), error=str(e)
            )

        return {
            "status": "completed",
            "connections_processed": len(connections),
            "ingested": total_records_ingested,
            "details": results,
            "window": {
                "start_date": start_date.date().isoformat(),
                "end_date": end_date.date().isoformat(),
                "backfill": custom_window,
            },
        }


class CostForecastHandler(BaseJobHandler):
    """Handle multi-tenant cost forecasting as a background job."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.modules.reporting.domain.aggregator import CostAggregator
        from app.shared.analysis.forecaster import SymbolicForecaster

        payload = job.payload or {}
        tenant_id = _require_tenant_id(job)
        start_date = _require_iso_date(payload, "start_date")
        end_date = _require_iso_date(payload, "end_date")
        days = payload.get("days", 30)
        provider = payload.get("provider")

        # 1. Fetch full summary for forecasting
        summary = await CostAggregator.get_summary(
            db, tenant_id, start_date, end_date, provider
        )

        if not summary.records:
            return {"status": "skipped", "reason": "no_data"}

        # 2. Run deterministic forecast
        # Phase 3: Symbolic Forecast
        result = await SymbolicForecaster.forecast(
            summary.records, days=days, db=db, tenant_id=tenant_id
        )

        return {"status": "completed", "forecast": result, "tenant_id": str(tenant_id)}


class CostAnomalyDetectionHandler(BaseJobHandler):
    """Deterministic daily cost anomaly detection with optional alert dispatch."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.modules.reporting.domain.anomaly_detection import (
            CostAnomalyDetectionService,
            dispatch_cost_anomaly_alerts,
        )
        from app.shared.core.pricing import (
            FeatureFlag,
            get_tenant_tier,
            is_feature_enabled,
        )

        tenant_id = _require_tenant_id(job)
        payload = job.payload or {}

        tier = await get_tenant_tier(tenant_id, db)
        if not is_feature_enabled(tier, FeatureFlag.ANOMALY_DETECTION):
            return {
                "status": "skipped",
                "reason": "feature_not_enabled_for_tier",
                "tier": tier.value,
            }

        target_date = (
            _require_iso_date(payload, "target_date")
            if payload.get("target_date")
            else datetime.now(timezone.utc).date()
        )
        lookback_days = int(payload.get("lookback_days", 28))
        min_abs_usd = Decimal(str(payload.get("min_abs_usd", "25")))
        min_percent = float(payload.get("min_percent", 30.0))
        min_severity = str(payload.get("min_severity", "medium")).strip().lower()
        provider = payload.get("provider")
        should_alert = bool(payload.get("alert", True)) and is_feature_enabled(
            tier, FeatureFlag.ALERTS
        )
        suppression_hours = int(payload.get("suppression_hours", 24))

        detector = CostAnomalyDetectionService(db)
        anomalies = await detector.detect(
            tenant_id=tenant_id,
            target_date=target_date,
            provider=provider,
            lookback_days=lookback_days,
            min_abs_usd=min_abs_usd,
            min_percent=min_percent,
            min_severity=min_severity,
        )

        alerted_count = 0
        if should_alert and anomalies:
            alerted_count = await dispatch_cost_anomaly_alerts(
                tenant_id=tenant_id,
                anomalies=anomalies,
                suppression_hours=suppression_hours,
                db=db,
            )

        return {
            "status": "completed",
            "tier": tier.value,
            "target_date": target_date.isoformat(),
            "lookback_days": lookback_days,
            "provider": provider,
            "count": len(anomalies),
            "alerted_count": alerted_count,
            "anomalies": [_serialize_anomaly(item) for item in anomalies[:50]],
        }


class CostExportHandler(BaseJobHandler):
    """Create bounded canonical cost export artifacts asynchronously."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.modules.reporting.api.v1.costs_helpers import sanitize_csv_cell
        from app.modules.reporting.domain.focus_export import (
            FOCUS_V13_CORE_COLUMNS,
            FocusV13ExportService,
        )

        payload = job.payload or {}
        tenant_id = _require_tenant_id(job)
        start_date = _require_iso_date(payload, "start_date")
        end_date = _require_iso_date(payload, "end_date")
        if start_date > end_date:
            raise PermanentJobError("start_date must be <= end_date")
        export_format = _normalize_cost_export_format(payload.get("format"))
        provider = _normalize_cost_export_provider(payload.get("provider"))
        include_preliminary = _payload_bool(
            payload, "include_preliminary", default=False
        )
        max_inline_bytes = _payload_positive_int(
            payload,
            "max_inline_bytes",
            default=COST_EXPORT_INLINE_DEFAULT_MAX_BYTES,
            maximum=COST_EXPORT_INLINE_HARD_MAX_BYTES,
        )

        logger.info(
            "cost_export_started",
            tenant_id=str(tenant_id),
            start_date=str(start_date),
            end_date=str(end_date),
            provider=provider,
            format=export_format,
        )

        service = FocusV13ExportService(db)
        out = io.StringIO(newline="")
        writer = csv.writer(out)
        writer.writerow(FOCUS_V13_CORE_COLUMNS)
        record_count = 0

        async for row in service.export_rows(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            include_preliminary=include_preliminary,
        ):
            writer.writerow(
                [sanitize_csv_cell(row.get(col, "")) for col in FOCUS_V13_CORE_COLUMNS]
            )
            record_count += 1
            if out.tell() > max_inline_bytes:
                raise PermanentJobError(
                    "Cost export exceeded max_inline_bytes; configure durable object "
                    "storage before queuing larger async exports."
                )

        content = out.getvalue().encode("utf-8")
        if len(content) > max_inline_bytes:
            raise PermanentJobError(
                "Cost export exceeded max_inline_bytes; configure durable object "
                "storage before queuing larger async exports."
            )
        digest = hashlib.sha256(content).hexdigest()
        filename = (
            f"focus-v1.3-core-{start_date.isoformat()}-{end_date.isoformat()}"
            f"-{provider or 'all'}.csv"
        )

        logger.info(
            "cost_export_completed",
            tenant_id=str(tenant_id),
            records_exported=record_count,
            byte_size=len(content),
            sha256=digest,
        )

        return {
            "status": "completed",
            "export_format": export_format,
            "artifact": {
                "storage": "background_job.result.inline_base64",
                "filename": filename,
                "content_type": "text/csv",
                "sha256": digest,
                "byte_size": len(content),
                "content_base64": base64.b64encode(content).decode("ascii"),
            },
            "records_exported": record_count,
            "provider": provider,
            "include_preliminary": include_preliminary,
        }


class CostAggregationHandler(BaseJobHandler):
    """Handle large cost data aggregations asynchronously."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.modules.reporting.domain.aggregator import CostAggregator

        payload = job.payload or {}
        tenant_id = _require_tenant_id(job)
        start_date = _require_iso_date(payload, "start_date")
        end_date = _require_iso_date(payload, "end_date")
        provider = payload.get("provider")

        logger.info(
            "cost_aggregation_job_started",
            tenant_id=str(tenant_id),
            start_date=str(start_date),
            end_date=str(end_date),
        )

        # 1. Run the intensive aggregation (which is now protected by timeout/limits)
        # In a background job, we might relax the timeout slightly if needed,
        # but here we follow the same production rules.
        result = await CostAggregator.get_summary(
            db, tenant_id, start_date, end_date, provider
        )

        # 2. Store the result in the job's result field (serialized)
        # Note: Summary includes a list of potentially many records.
        # For very large results, we'd normally store in object storage or a cache tier.
        # But for this implementation, we store a summary.

        return {
            "status": "completed",
            "total_cost_usd": float(result.total_cost),
            "record_count": len(result.records),
            "by_service": {k: float(v) for k, v in result.by_service.items()},
        }
