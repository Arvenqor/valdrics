from __future__ import annotations

from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm import LLMUsage
from app.models.attribution import CostAllocation
from app.shared.core.config import get_settings
from app.modules.reporting.domain.focus_export_rows import _date_window_bounds
from app.modules.reporting.domain.spend_ledger_decimal import (
    _decimal_string,
    _optional_decimal_string,
)

AI_LEDGER_PROVIDER = "ai"


async def ai_spend_summary(
    *,
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
) -> dict[str, Decimal | int]:
    window_start, window_end = _date_window_bounds(start_date, end_date)
    # First, query all LLMUsage records in the window
    usage_stmt = select(LLMUsage.id, LLMUsage.cost_usd).where(
        LLMUsage.tenant_id == tenant_id,
        LLMUsage.created_at >= window_start,
        LLMUsage.created_at < window_end,
    )
    usage_rows = (await db.execute(usage_stmt)).all()

    if not usage_rows:
        return {
            "record_count": 0,
            "total_cost": Decimal("0"),
            "total_allocated": Decimal("0"),
            "total_unallocated": Decimal("0"),
        }

    usage_ids = [row.id for row in usage_rows]
    total_cost = sum((row.cost_usd for row in usage_rows), Decimal("0"))

    # Query all allocations for these records
    allocations: list[CostAllocation] = []
    chunk_size = int(getattr(get_settings(), "BATCH_PROCESSING_CHUNK_SIZE", 1000))
    for i in range(0, len(usage_ids), chunk_size):
        chunk = usage_ids[i : i + chunk_size]
        alloc_stmt = select(CostAllocation).where(
            CostAllocation.llm_usage_id.in_(chunk)
        )
        allocations.extend((await db.execute(alloc_stmt)).scalars().all())

    # Map allocations by llm_usage_id
    alloc_map: defaultdict[UUID | None, list[CostAllocation]] = defaultdict(list)
    for alloc in allocations:
        alloc_map[alloc.llm_usage_id].append(alloc)

    total_allocated = Decimal("0")
    total_unallocated = Decimal("0")

    for row in usage_rows:
        row_cost = row.cost_usd
        row_allocs = alloc_map.get(row.id, [])

        if not row_allocs:
            total_unallocated += row_cost
        else:
            row_allocated = sum(
                (
                    a.amount
                    for a in row_allocs
                    if a.allocated_to.strip().lower() != "unallocated"
                ),
                Decimal("0"),
            )
            total_allocated += row_allocated
            total_unallocated += max(row_cost - row_allocated, Decimal("0"))

    return {
        "record_count": len(usage_rows),
        "total_cost": total_cost,
        "total_allocated": total_allocated,
        "total_unallocated": total_unallocated,
    }


async def ai_spend_entries(
    *,
    db: AsyncSession,
    tenant_id: UUID,
    start_date: date,
    end_date: date,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    window_start, window_end = _date_window_bounds(start_date, end_date)
    stmt = (
        select(LLMUsage)
        .where(
            LLMUsage.tenant_id == tenant_id,
            LLMUsage.created_at >= window_start,
            LLMUsage.created_at < window_end,
        )
        .order_by(LLMUsage.created_at.asc(), LLMUsage.id.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).scalars().all()

    if not rows:
        return []

    # Load all allocations for the loaded rows in bulk
    usage_ids = [row.id for row in rows]
    alloc_stmt = (
        select(CostAllocation)
        .where(CostAllocation.llm_usage_id.in_(usage_ids))
        .order_by(
            CostAllocation.recorded_at.asc(),
            CostAllocation.timestamp.asc(),
            CostAllocation.allocated_to.asc(),
            CostAllocation.id.asc(),
        )
    )
    allocations = (await db.execute(alloc_stmt)).scalars().all()

    grouped_allocations: defaultdict[UUID | None, list[CostAllocation]] = defaultdict(
        list
    )
    for alloc in allocations:
        grouped_allocations[alloc.llm_usage_id].append(alloc)

    return [_serialize_llm_usage_row(row, grouped_allocations[row.id]) for row in rows]


def _serialize_llm_usage_row(
    usage: LLMUsage, allocations: list[CostAllocation]
) -> dict[str, Any]:
    provider = (usage.provider or "unknown").strip().lower() or "unknown"
    request_type = usage.request_type or "inference"
    created_at = usage.created_at

    cost_usd = usage.cost_usd

    allocated_amount = sum(
        (
            a.amount
            for a in allocations
            if a.allocated_to.strip().lower() != "unallocated"
        ),
        Decimal("0"),
    )
    unallocated_amount = max(cost_usd - allocated_amount, Decimal("0"))

    allocated_decimal = Decimal(_decimal_string(allocated_amount))
    unallocated_decimal = Decimal(_decimal_string(unallocated_amount))

    if len(allocations) <= 0:
        allocation_status = "unallocated"
    elif unallocated_decimal > Decimal("0") and allocated_decimal > Decimal("0"):
        allocation_status = "partially_allocated"
    elif unallocated_decimal > Decimal("0"):
        allocation_status = "unallocated"
    else:
        allocation_status = "allocated"

    return {
        "id": str(usage.id),
        "recorded_at": created_at.date().isoformat(),
        "timestamp": created_at.isoformat(),
        "provider": AI_LEDGER_PROVIDER,
        "account_id": f"ai:{provider}",
        "account_name": f"AI Spend ({provider})",
        "service": "LLM",
        "region": None,
        "usage_type": request_type,
        "resource_id": usage.operation_id or None,
        "usage_amount": _decimal_string(usage.total_tokens),
        "usage_unit": "tokens",
        "cost_usd": _decimal_string(cost_usd),
        "amount_raw": _decimal_string(cost_usd),
        "currency": "USD",
        "cost_status": "FINAL",
        "canonical_charge_category": "ai",
        "canonical_charge_subcategory": "llm_inference",
        "canonical_mapping_version": "valdrics-ai-spend-v1",
        "allocation_status": allocation_status,
        "allocated_amount_usd": _decimal_string(allocated_amount),
        "unallocated_amount_usd": _decimal_string(unallocated_amount),
        "allocation_count": len(allocations),
        "tags": {
            "source": "llm_usage",
            "llm_provider": provider,
            "model": usage.model,
            "is_byok": usage.is_byok,
            "request_type": request_type,
        },
        "allocations": [
            _serialize_allocation(allocation) for allocation in allocations
        ],
    }


def _serialize_allocation(allocation: CostAllocation) -> dict[str, Any]:
    return {
        "id": str(allocation.id),
        "rule_id": str(allocation.rule_id) if allocation.rule_id else None,
        "allocated_to": allocation.allocated_to,
        "amount_usd": _decimal_string(allocation.amount),
        "percentage": _optional_decimal_string(allocation.percentage, places=2),
        "recorded_at": allocation.recorded_at.isoformat(),
        "timestamp": allocation.timestamp.isoformat(),
    }
