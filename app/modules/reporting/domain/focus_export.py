from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, AsyncIterator
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribution import CostAllocation
from app.models.aws_connection import AWSConnection
from app.models.azure_connection import AzureConnection
from app.models.cloud import CloudAccount, CostRecord
from app.models.gcp_connection import GCPConnection
from app.models.hybrid_connection import HybridConnection
from app.models.license_connection import LicenseConnection
from app.models.llm import LLMUsage
from app.models.platform_connection import PlatformConnection
from app.models.saas_connection import SaaSConnection
from app.modules.reporting.domain.focus_export_helpers import (
    _CLOUD_PROVIDER_DISPLAY,
    _focus_charge_category,
    _focus_charge_frequency,
    _focus_service_category,
    _focus_service_subcategory,
    _humanize_vendor,
    _service_provider_display,
)

logger = structlog.get_logger()
FOCUS_EXPORT_STREAM_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    SQLAlchemyError,
    RuntimeError,
    OSError,
    TimeoutError,
    TypeError,
    ValueError,
    AttributeError,
)
FOCUS_EXPORT_COST_PARSE_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    InvalidOperation,
    TypeError,
    ValueError,
)
FOCUS_EXPORT_TAG_SERIALIZATION_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    TypeError,
    ValueError,
)
AI_FOCUS_PROVIDER = "ai"
AI_FOCUS_SERVICE_CATEGORY = "AI and Machine Learning"
AI_FOCUS_SERVICE_SUBCATEGORY = "Generative AI"

# FOCUS 1.3 core export: high-value columns that are fully derivable from our
# normalized ledger without pretending to include SKU or unit-price fields we do
# not store yet.
FOCUS_V13_CORE_COLUMNS: list[str] = [
    "AllocatedMethodDetails",
    "AllocatedMethodId",
    "AllocatedResourceId",
    "AllocatedResourceName",
    "AllocatedTags",
    "BilledCost",
    "BillingAccountId",
    "BillingAccountName",
    "BillingCurrency",
    "BillingPeriodStart",
    "BillingPeriodEnd",
    "ChargeCategory",
    "ChargeClass",
    "ChargeDescription",
    "ChargeFrequency",
    "ChargePeriodStart",
    "ChargePeriodEnd",
    "ConsumedQuantity",
    "ConsumedUnit",
    "ContractedCost",
    "EffectiveCost",
    "HostProviderName",
    "InvoiceIssuerName",
    "ListCost",
    "PricingCurrency",
    "PricingQuantity",
    "PricingUnit",
    "ProviderName",
    "PublisherName",
    "RegionId",
    "RegionName",
    "ResourceId",
    "ServiceProviderName",
    "ServiceCategory",
    "ServiceSubcategory",
    "ServiceName",
    "Tags",
]

__all__ = (
    "FOCUS_V13_CORE_COLUMNS",
    "FocusV13ExportService",
    "_humanize_vendor",
    "_service_provider_display",
    "_focus_charge_category",
)


@dataclass(frozen=True)
class FocusAccountContext:
    provider_key: str
    billing_account_id: str
    billing_account_name: str
    provider_name: str
    publisher_name: str
    service_provider_name: str
    invoice_issuer_name: str


@dataclass(frozen=True)
class FocusSyntheticAllocation:
    id: str
    rule_id: None
    allocated_to: str
    amount: Decimal
    percentage: Decimal | None


FocusAllocation = CostAllocation | FocusSyntheticAllocation
FocusAllocationKey = tuple[UUID, date]


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _focus_datetime(dt: datetime) -> str:
    # RFC 3339 / ISO 8601 with Z suffix (timezone-agnostic and stable in CSV).
    return _as_utc(dt).strftime("%Y-%m-%dT%H:%M:%SZ")


def _month_start(day: date) -> datetime:
    return datetime(day.year, day.month, 1, tzinfo=timezone.utc)


def _next_month_start(day: date) -> datetime:
    if day.month == 12:
        return datetime(day.year + 1, 1, 1, tzinfo=timezone.utc)
    return datetime(day.year, day.month + 1, 1, tzinfo=timezone.utc)


def _format_cost(value: Any) -> str:
    if value is None:
        return "0"
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except FOCUS_EXPORT_COST_PARSE_RECOVERABLE_EXCEPTIONS as exc:
        raise ValueError("FOCUS export cost must be numeric") from exc
    if not amount.is_finite():
        raise ValueError("FOCUS export cost must be finite")
    return format(amount, "f")


def _to_decimal(value: Any, *, field_name: str) -> Decimal:
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except FOCUS_EXPORT_COST_PARSE_RECOVERABLE_EXCEPTIONS as exc:
        raise ValueError(f"FOCUS export {field_name} must be numeric") from exc
    if not amount.is_finite():
        raise ValueError(f"FOCUS export {field_name} must be finite")
    return amount


def _format_optional_decimal(value: Any) -> str:
    if value is None:
        return ""
    return format(_to_decimal(value, field_name="numeric value"), "f")


def _format_currency(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "USD"
    return value.strip().upper()


def _tags_json(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    # Stable JSON for diffs and deterministic exports.
    try:
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    except FOCUS_EXPORT_TAG_SERIALIZATION_RECOVERABLE_EXCEPTIONS:
        return ""


def _stable_json(value: dict[str, Any] | None) -> str:
    if not value:
        return ""
    try:
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    except FOCUS_EXPORT_TAG_SERIALIZATION_RECOVERABLE_EXCEPTIONS:
        return ""


def _allocation_bucket(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _date_window_bounds(start_date: date, end_date: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start_date, time.min, tzinfo=timezone.utc),
        datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc),
    )


class FocusV13ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def export_rows(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        provider: str | None = None,
        include_preliminary: bool = False,
    ) -> AsyncIterator[dict[str, str]]:
        include_origin_spend = provider != AI_FOCUS_PROVIDER
        include_ai_spend = provider in (None, AI_FOCUS_PROVIDER)

        if include_origin_spend:
            async for row in self._export_origin_rows(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                provider=provider,
                include_preliminary=include_preliminary,
            ):
                yield row
        if include_ai_spend:
            async for row in self._export_ai_rows(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
            ):
                yield row

    async def _export_origin_rows(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        provider: str | None,
        include_preliminary: bool,
    ) -> AsyncIterator[dict[str, str]]:
        contexts = await self._load_account_contexts(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            provider=provider,
            include_preliminary=include_preliminary,
        )
        filters: list[Any] = [
            CostRecord.tenant_id == tenant_id,
            CostRecord.recorded_at >= start_date,
            CostRecord.recorded_at <= end_date,
        ]
        if not include_preliminary:
            filters.append(CostRecord.cost_status == "FINAL")
        if provider:
            filters.append(CloudAccount.provider == provider)

        stmt = (
            select(CostRecord, CloudAccount, CostAllocation)
            .join(CloudAccount, CostRecord.account_id == CloudAccount.id)
            .outerjoin(
                CostAllocation,
                (CostAllocation.cost_record_id == CostRecord.id)
                & (CostAllocation.recorded_at == CostRecord.recorded_at),
            )
            .where(*filters)
            .order_by(
                CostRecord.recorded_at.asc(),
                CostRecord.timestamp.asc(),
                CostRecord.id.asc(),
                CostAllocation.timestamp.asc(),
                CostAllocation.id.asc(),
            )
            .execution_options(yield_per=500)
        )

        # Use streaming where supported; SQLite in tests still works with execute().
        try:
            result = await self.db.stream(stmt)
            current_key: FocusAllocationKey | None = None
            current_record: CostRecord | None = None
            current_account: CloudAccount | None = None
            current_allocations: list[CostAllocation] = []
            async for cost_record, account, allocation in result:
                record_key = self._allocation_key_for_record(cost_record)
                if current_key is not None and record_key != current_key:
                    if current_record is not None and current_account is not None:
                        for focus_row in self._rows_for_cost_record(
                            current_record,
                            current_account,
                            contexts,
                            {current_key: current_allocations},
                        ):
                            yield focus_row
                    current_allocations = []
                current_key = record_key
                current_record = cost_record
                current_account = account
                if allocation is not None:
                    current_allocations.append(allocation)

            if (
                current_key is not None
                and current_record is not None
                and current_account is not None
            ):
                for focus_row in self._rows_for_cost_record(
                    current_record,
                    current_account,
                    contexts,
                    {current_key: current_allocations},
                ):
                    yield focus_row
            return
        except FOCUS_EXPORT_STREAM_RECOVERABLE_EXCEPTIONS:
            logger.debug("focus_export_stream_fallback_to_execute")

        sync_result = await self.db.execute(stmt)
        for cost_record, account, allocations in self._group_origin_rows(sync_result):
            record_key = self._allocation_key_for_record(cost_record)
            for focus_row in self._rows_for_cost_record(
                cost_record,
                account,
                contexts,
                {record_key: allocations},
            ):
                yield focus_row

    async def _export_ai_rows(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
    ) -> AsyncIterator[dict[str, str]]:
        window_start, window_end = _date_window_bounds(start_date, end_date)
        stmt = (
            select(LLMUsage)
            .where(
                LLMUsage.tenant_id == tenant_id,
                LLMUsage.created_at >= window_start,
                LLMUsage.created_at < window_end,
            )
            .order_by(LLMUsage.created_at.asc(), LLMUsage.id.asc())
            .execution_options(stream_results=True)
        )
        try:
            result = await self.db.stream(stmt)
            async for usage in result.scalars():
                yield self._llm_usage_to_focus(usage)
            return
        except FOCUS_EXPORT_STREAM_RECOVERABLE_EXCEPTIONS:
            logger.debug("focus_export_ai_stream_fallback_to_execute")

        rows = (await self.db.execute(stmt)).scalars().all()
        for usage in rows:
            yield self._llm_usage_to_focus(usage)

    async def _load_account_contexts(
        self,
        tenant_id: UUID,
        start_date: date,
        end_date: date,
        provider: str | None,
        include_preliminary: bool,
    ) -> dict[UUID, FocusAccountContext]:
        filters: list[Any] = [
            CostRecord.tenant_id == tenant_id,
            CostRecord.recorded_at >= start_date,
            CostRecord.recorded_at <= end_date,
        ]
        if not include_preliminary:
            filters.append(CostRecord.cost_status == "FINAL")
        if provider:
            filters.append(CloudAccount.provider == provider)

        stmt = (
            select(CloudAccount.id, CloudAccount.provider, CloudAccount.name)
            .join(CostRecord, CostRecord.account_id == CloudAccount.id)
            .where(*filters)
            .distinct()
        )
        rows = (await self.db.execute(stmt)).all()

        contexts: dict[UUID, FocusAccountContext] = {}
        ids_by_provider: dict[str, list[UUID]] = {}
        for account_id, provider_key, name in rows:
            provider_key = str(provider_key or "").strip().lower()
            display = _service_provider_display(provider_key)
            contexts[account_id] = FocusAccountContext(
                provider_key=provider_key,
                billing_account_id=str(account_id),
                billing_account_name=str(name or ""),
                provider_name=display,
                publisher_name=display,
                service_provider_name=display,
                invoice_issuer_name=display,
            )
            ids_by_provider.setdefault(provider_key, []).append(account_id)

        # Enrich with provider-native identifiers and Cloud+ vendor names.
        await self._enrich_cloud_accounts(contexts, ids_by_provider.get("aws", []))
        await self._enrich_cloud_accounts(contexts, ids_by_provider.get("azure", []))
        await self._enrich_cloud_accounts(contexts, ids_by_provider.get("gcp", []))
        await self._enrich_cloud_plus_accounts(
            contexts, "saas", ids_by_provider.get("saas", [])
        )
        await self._enrich_cloud_plus_accounts(
            contexts, "license", ids_by_provider.get("license", [])
        )
        await self._enrich_cloud_plus_accounts(
            contexts, "platform", ids_by_provider.get("platform", [])
        )
        await self._enrich_cloud_plus_accounts(
            contexts, "hybrid", ids_by_provider.get("hybrid", [])
        )

        return contexts

    def _rows_for_cost_record(
        self,
        cost_record: CostRecord,
        account: CloudAccount,
        contexts: dict[UUID, FocusAccountContext],
        allocations_by_record_key: dict[FocusAllocationKey, list[CostAllocation]],
    ) -> list[dict[str, str]]:
        allocations = allocations_by_record_key.get(
            self._allocation_key_for_record(cost_record), []
        )
        if not allocations:
            return [self._row_to_focus(cost_record, account, contexts)]

        # A single synthetic Unallocated row from the attribution engine is not
        # a split allocation, so keep the export at the origin-charge level.
        if (
            len(allocations) == 1
            and allocations[0].rule_id is None
            and _allocation_bucket(allocations[0].allocated_to).lower()
            == "unallocated"
        ):
            return [self._row_to_focus(cost_record, account, contexts)]

        allocations_for_export: list[FocusAllocation] = [*allocations]
        origin_cost = _to_decimal(getattr(cost_record, "cost_usd", None), field_name="origin cost")
        allocated_cost = sum(
            (
                _to_decimal(allocation.amount, field_name="allocation amount")
                for allocation in allocations
            ),
            Decimal("0"),
        )
        unallocated_cost = origin_cost - allocated_cost
        if unallocated_cost > Decimal("0"):
            percentage = (
                Decimal("0")
                if origin_cost == Decimal("0")
                else (unallocated_cost / origin_cost) * Decimal("100")
            )
            allocations_for_export.append(
                FocusSyntheticAllocation(
                    id=(
                        f"{getattr(cost_record, 'id', 'unknown')}:"
                        f"{getattr(cost_record, 'recorded_at', 'unknown')}:"
                        "unallocated-remainder"
                    ),
                    rule_id=None,
                    allocated_to="Unallocated",
                    amount=unallocated_cost,
                    percentage=percentage,
                )
            )

        return [
            self._row_to_focus(cost_record, account, contexts, allocation=allocation)
            for allocation in allocations_for_export
        ]

    def _allocation_key_for_record(self, cost_record: CostRecord) -> FocusAllocationKey:
        record_id = getattr(cost_record, "id", None)
        recorded_at = getattr(cost_record, "recorded_at", None)
        if not isinstance(record_id, UUID) or not isinstance(recorded_at, date):
            raise ValueError("FOCUS export cost records require id and recorded_at")
        return (record_id, recorded_at)

    def _group_origin_rows(
        self,
        rows: Any,
    ) -> list[tuple[CostRecord, CloudAccount, list[CostAllocation]]]:
        grouped: list[tuple[CostRecord, CloudAccount, list[CostAllocation]]] = []
        current_key: FocusAllocationKey | None = None
        current_record: CostRecord | None = None
        current_account: CloudAccount | None = None
        current_allocations: list[CostAllocation] = []

        for cost_record, account, allocation in rows:
            record_key = self._allocation_key_for_record(cost_record)
            if current_key is not None and record_key != current_key:
                if current_record is not None and current_account is not None:
                    grouped.append((current_record, current_account, current_allocations))
                current_allocations = []
            current_key = record_key
            current_record = cost_record
            current_account = account
            if allocation is not None:
                current_allocations.append(allocation)

        if (
            current_key is not None
            and current_record is not None
            and current_account is not None
        ):
            grouped.append((current_record, current_account, current_allocations))
        return grouped

    async def _enrich_cloud_accounts(
        self,
        contexts: dict[UUID, FocusAccountContext],
        account_ids: list[UUID],
    ) -> None:
        if not account_ids:
            return

        # Note: each connection model stores its provider-native identifier in a different field.
        # We update BillingAccountId so exports can round-trip to provider invoices.
        aws_rows = (
            await self.db.execute(
                select(AWSConnection.id, AWSConnection.aws_account_id).where(
                    AWSConnection.id.in_(account_ids)
                )
            )
        ).all()
        for conn_id, aws_account_id in aws_rows:
            ctx = contexts.get(conn_id)
            if not ctx:
                continue
            display = _CLOUD_PROVIDER_DISPLAY["aws"]
            contexts[conn_id] = FocusAccountContext(
                provider_key=ctx.provider_key,
                billing_account_id=str(aws_account_id),
                billing_account_name=f"AWS {aws_account_id}",
                provider_name=display,
                publisher_name=display,
                service_provider_name=display,
                invoice_issuer_name=display,
            )

        azure_rows = (
            await self.db.execute(
                select(AzureConnection.id, AzureConnection.subscription_id).where(
                    AzureConnection.id.in_(account_ids)
                )
            )
        ).all()
        for conn_id, subscription_id in azure_rows:
            ctx = contexts.get(conn_id)
            if not ctx:
                continue
            display = _CLOUD_PROVIDER_DISPLAY["azure"]
            contexts[conn_id] = FocusAccountContext(
                provider_key=ctx.provider_key,
                billing_account_id=str(subscription_id),
                billing_account_name=ctx.billing_account_name or str(subscription_id),
                provider_name=display,
                publisher_name=display,
                service_provider_name=display,
                invoice_issuer_name=display,
            )

        gcp_rows = (
            await self.db.execute(
                select(GCPConnection.id, GCPConnection.project_id).where(
                    GCPConnection.id.in_(account_ids)
                )
            )
        ).all()
        for conn_id, project_id in gcp_rows:
            ctx = contexts.get(conn_id)
            if not ctx:
                continue
            display = _CLOUD_PROVIDER_DISPLAY["gcp"]
            contexts[conn_id] = FocusAccountContext(
                provider_key=ctx.provider_key,
                billing_account_id=str(project_id),
                billing_account_name=ctx.billing_account_name or str(project_id),
                provider_name=display,
                publisher_name=display,
                service_provider_name=display,
                invoice_issuer_name=display,
            )

    async def _enrich_cloud_plus_accounts(
        self,
        contexts: dict[UUID, FocusAccountContext],
        provider_key: str,
        account_ids: list[UUID],
    ) -> None:
        if not account_ids:
            return

        model = {
            "saas": SaaSConnection,
            "license": LicenseConnection,
            "platform": PlatformConnection,
            "hybrid": HybridConnection,
        }.get(provider_key)
        if model is None:
            return

        sync_result = await self.db.execute(
            select(getattr(model, "id"), getattr(model, "vendor")).where(
                getattr(model, "id").in_(account_ids)
            )
        )
        for conn_id, vendor in sync_result.all():
            ctx = contexts.get(conn_id)
            if not ctx:
                continue
            issuer = _service_provider_display(
                provider_key, str(vendor) if vendor else None
            )
            contexts[conn_id] = FocusAccountContext(
                provider_key=ctx.provider_key,
                billing_account_id=str(conn_id),
                billing_account_name=ctx.billing_account_name,
                provider_name=issuer,
                publisher_name=issuer,
                service_provider_name=issuer,
                invoice_issuer_name=issuer,
            )

    def _row_to_focus(
        self,
        cost_record: CostRecord,
        account: CloudAccount,
        contexts: dict[UUID, FocusAccountContext],
        allocation: FocusAllocation | None = None,
    ) -> dict[str, str]:
        recorded_day = getattr(cost_record, "recorded_at", None) or date.today()
        billing_start = _month_start(recorded_day)
        billing_end = _next_month_start(recorded_day)

        provider_key = str(getattr(account, "provider", "") or "").strip().lower()
        charge_start: datetime
        charge_end: datetime
        ts = getattr(cost_record, "timestamp", None)
        if isinstance(ts, datetime):
            ts = _as_utc(ts)
        if provider_key in {"aws", "azure", "gcp"} and isinstance(ts, datetime):
            charge_start = ts
            charge_end = ts + timedelta(hours=1)
        else:
            charge_start = datetime.combine(recorded_day, time.min, tzinfo=timezone.utc)
            charge_end = charge_start + timedelta(days=1)

        service = getattr(cost_record, "service", None)
        usage_type = getattr(cost_record, "usage_type", None)
        charge_category = _focus_charge_category(service, usage_type)
        service_category = _focus_service_category(
            getattr(cost_record, "canonical_charge_category", None)
        )
        service_subcategory = _focus_service_subcategory(service_category)

        raw_tags = getattr(cost_record, "tags", None)
        if not isinstance(raw_tags, dict) or not raw_tags:
            meta = getattr(cost_record, "ingestion_metadata", None)
            if isinstance(meta, dict):
                raw_tags = meta.get("tags")

        ctx = contexts.get(account.id)
        if ctx is None:
            display = _service_provider_display(provider_key)
            ctx = FocusAccountContext(
                provider_key=provider_key,
                billing_account_id=str(account.id),
                billing_account_name=str(getattr(account, "name", "") or ""),
                provider_name=display,
                publisher_name=display,
                service_provider_name=display,
                invoice_issuer_name=display,
            )

        region_value = str(getattr(cost_record, "region", "") or "").strip()
        cost_value = _format_cost(
            getattr(allocation, "amount", None)
            if allocation is not None
            else getattr(cost_record, "cost_usd", None)
        )
        # Our ledger stores `cost_usd` in USD. For exports, keep currency aligned with the cost value.
        currency_value = "USD"
        usage_quantity = _format_optional_decimal(
            getattr(cost_record, "usage_amount", None)
        )
        usage_unit = str(getattr(cost_record, "usage_unit", "") or "").strip()
        resource_id = str(getattr(cost_record, "resource_id", "") or "").strip()
        pricing_currency = _format_currency(getattr(cost_record, "currency", None))
        allocation_fields = self._allocation_fields(cost_record, allocation)

        focus_row = {
            **allocation_fields,
            "BilledCost": cost_value,
            "BillingAccountId": ctx.billing_account_id,
            "BillingAccountName": ctx.billing_account_name,
            "BillingCurrency": currency_value,
            "BillingPeriodStart": _focus_datetime(billing_start),
            "BillingPeriodEnd": _focus_datetime(billing_end),
            "ChargeCategory": charge_category,
            "ChargeClass": "Regular",
            "ChargeDescription": str(usage_type or service or "").strip(),
            "ChargeFrequency": _focus_charge_frequency(charge_category),
            "ChargePeriodStart": _focus_datetime(charge_start),
            "ChargePeriodEnd": _focus_datetime(charge_end),
            "ConsumedQuantity": usage_quantity,
            "ConsumedUnit": usage_unit,
            "ContractedCost": cost_value,
            "EffectiveCost": cost_value,
            "HostProviderName": ctx.service_provider_name,
            "InvoiceIssuerName": ctx.invoice_issuer_name,
            "ListCost": cost_value,
            "PricingCurrency": pricing_currency,
            "PricingQuantity": usage_quantity,
            "PricingUnit": usage_unit,
            "ProviderName": ctx.provider_name,
            "PublisherName": ctx.publisher_name,
            "RegionId": region_value,
            "RegionName": region_value,
            "ResourceId": resource_id,
            "ServiceProviderName": ctx.service_provider_name,
            "ServiceCategory": service_category,
            "ServiceSubcategory": service_subcategory,
            "ServiceName": str(service or "Unknown").strip() or "Unknown",
            "Tags": _tags_json(raw_tags),
        }

        # Ensure stable presence for all expected columns (avoid accidental KeyError).
        return {col: str(focus_row.get(col, "")) for col in FOCUS_V13_CORE_COLUMNS}

    def _llm_usage_to_focus(self, usage: LLMUsage) -> dict[str, str]:
        created_at = _as_utc(getattr(usage, "created_at", datetime.now(timezone.utc)))
        provider_key = (getattr(usage, "provider", None) or "unknown").strip().lower()
        provider_display = _humanize_vendor(provider_key) or provider_key.upper()
        model = str(getattr(usage, "model", "") or "LLM").strip() or "LLM"
        request_type = str(getattr(usage, "request_type", "") or "inference").strip()
        cost_value = _format_cost(getattr(usage, "cost_usd", None))
        tokens = _format_optional_decimal(getattr(usage, "total_tokens", None))
        charge_end = created_at + timedelta(seconds=1)
        tags = {
            "source": "llm_usage",
            "llm_provider": provider_key,
            "model": model,
            "request_type": request_type,
            "is_byok": bool(getattr(usage, "is_byok", False)),
        }
        focus_row = {
            "AllocatedMethodDetails": "",
            "AllocatedMethodId": "",
            "AllocatedResourceId": "",
            "AllocatedResourceName": "",
            "AllocatedTags": "",
            "BilledCost": cost_value,
            "BillingAccountId": f"ai:{provider_key}",
            "BillingAccountName": f"AI Spend ({provider_display})",
            "BillingCurrency": "USD",
            "BillingPeriodStart": _focus_datetime(_month_start(created_at.date())),
            "BillingPeriodEnd": _focus_datetime(_next_month_start(created_at.date())),
            "ChargeCategory": "Usage",
            "ChargeClass": "Regular",
            "ChargeDescription": request_type,
            "ChargeFrequency": "Usage-Based",
            "ChargePeriodStart": _focus_datetime(created_at),
            "ChargePeriodEnd": _focus_datetime(charge_end),
            "ConsumedQuantity": tokens,
            "ConsumedUnit": "tokens",
            "ContractedCost": cost_value,
            "EffectiveCost": cost_value,
            "HostProviderName": provider_display,
            "InvoiceIssuerName": provider_display,
            "ListCost": cost_value,
            "PricingCurrency": "USD",
            "PricingQuantity": tokens,
            "PricingUnit": "tokens",
            "ProviderName": provider_display,
            "PublisherName": provider_display,
            "RegionId": "",
            "RegionName": "",
            "ResourceId": str(getattr(usage, "operation_id", "") or "").strip(),
            "ServiceProviderName": provider_display,
            "ServiceCategory": AI_FOCUS_SERVICE_CATEGORY,
            "ServiceSubcategory": AI_FOCUS_SERVICE_SUBCATEGORY,
            "ServiceName": model,
            "Tags": _tags_json(tags),
        }
        return {col: str(focus_row.get(col, "")) for col in FOCUS_V13_CORE_COLUMNS}

    def _allocation_fields(
        self,
        cost_record: CostRecord,
        allocation: FocusAllocation | None,
    ) -> dict[str, str]:
        empty = {
            "AllocatedMethodDetails": "",
            "AllocatedMethodId": "",
            "AllocatedResourceId": "",
            "AllocatedResourceName": "",
            "AllocatedTags": "",
        }
        if allocation is None:
            return empty

        bucket = _allocation_bucket(allocation.allocated_to)
        is_unallocated_remainder = bucket.lower() == "unallocated"
        method_id = "valdrics-rule-based-allocation-v1"
        origin_cost = _to_decimal(
            getattr(cost_record, "cost_usd", None),
            field_name="origin cost",
        )
        allocation_amount = _to_decimal(
            getattr(allocation, "amount", None),
            field_name="allocation amount",
        )
        percentage = getattr(allocation, "percentage", None)
        if percentage is not None:
            ratio = _to_decimal(percentage, field_name="allocation percentage") / Decimal(
                "100"
            )
        elif origin_cost == Decimal("0"):
            ratio = Decimal("0")
        else:
            ratio = allocation_amount / origin_cost

        details: dict[str, Any] = {
            "Elements": [
                {
                    "AllocatedRatio": float(ratio),
                }
            ],
            "x_ValdricsAllocationId": str(allocation.id),
        }
        if allocation.rule_id is not None:
            details["x_ValdricsRuleId"] = str(allocation.rule_id)

        return {
            **empty,
            "AllocatedMethodDetails": _stable_json(details),
            "AllocatedMethodId": method_id,
            "AllocatedResourceId": "" if is_unallocated_remainder else bucket,
            "AllocatedResourceName": "" if is_unallocated_remainder else bucket,
        }
