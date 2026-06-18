"""Analytics queries for attribution-engine allocations."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribution import CostAllocation
from app.models.cloud import CostRecord
from app.modules.reporting.domain.allocation_ledger import (
    cost_allocation_rollup_subquery,
    unallocated_amount_expr,
)
from app.shared.utils.data_coercion import coerce_finite_float
async def get_allocation_summary(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    bucket: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    """Get aggregated allocation summary by bucket for a tenant."""
    from sqlalchemy import func

    query = (
        select(
            CostAllocation.allocated_to,
            func.sum(CostAllocation.amount).label("total_amount"),
            func.count(CostAllocation.id).label("record_count"),
        )
        .join(
            CostRecord,
            (CostAllocation.cost_record_id == CostRecord.id)
            & (CostAllocation.recorded_at == CostRecord.recorded_at),
        )
        .where(CostRecord.tenant_id == tenant_id)
        .group_by(CostAllocation.allocated_to)
        .order_by(func.sum(CostAllocation.amount).desc())
        .limit(limit)
        .offset(offset)
    )

    if start_date:
        query = query.where(CostAllocation.timestamp >= start_date)
    if end_date:
        query = query.where(CostAllocation.timestamp <= end_date)
    if bucket:
        query = query.where(CostAllocation.allocated_to == bucket)

    result = await db.execute(query)
    rows = result.all()

    return {
        "buckets": [
            {
                "name": row.allocated_to,
                "total_amount": coerce_finite_float(
                    row.total_amount,
                    field_name="total_amount",
                ),
                "record_count": row.record_count,
            }
            for row in rows
        ],
        "total": sum(
            coerce_finite_float(row.total_amount, field_name="total_amount")
            for row in rows
        ),
    }


async def get_allocation_coverage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    target_percentage: float = 90.0,
) -> dict[str, Any]:
    """Compute allocation coverage KPI for a tenant and date window."""
    from sqlalchemy import func

    total_query = select(
        func.coalesce(func.sum(CostRecord.cost_usd), 0).label("total_cost"),
        func.count(CostRecord.id).label("total_records"),
    ).where(CostRecord.tenant_id == tenant_id)
    if start_date:
        total_query = total_query.where(CostRecord.recorded_at >= start_date)
    if end_date:
        total_query = total_query.where(CostRecord.recorded_at <= end_date)

    total_row = (await db.execute(total_query)).one()
    total_cost = coerce_finite_float(
        total_row.total_cost or 0,
        field_name="total_cost",
    )
    total_records = int(total_row.total_records or 0)

    allocated_query = (
        select(
            func.coalesce(func.sum(CostAllocation.amount), 0).label("allocated_cost"),
            func.count(CostAllocation.id).label("allocation_rows"),
            func.count(func.distinct(CostAllocation.cost_record_id)).label(
                "allocated_records"
            ),
        )
        .join(
            CostRecord,
            (CostAllocation.cost_record_id == CostRecord.id)
            & (CostAllocation.recorded_at == CostRecord.recorded_at),
        )
        .where(CostRecord.tenant_id == tenant_id)
    )
    if start_date:
        allocated_query = allocated_query.where(CostRecord.recorded_at >= start_date)
    if end_date:
        allocated_query = allocated_query.where(CostRecord.recorded_at <= end_date)

    allocated_row = (await db.execute(allocated_query)).one()
    raw_allocated_cost = coerce_finite_float(
        allocated_row.allocated_cost or 0,
        field_name="allocated_cost",
    )
    allocated_cost = min(raw_allocated_cost, total_cost) if total_cost > 0 else 0.0
    over_allocated_cost = max(raw_allocated_cost - total_cost, 0.0)
    coverage_percentage = (
        (allocated_cost / total_cost * 100.0) if total_cost > 0 else 0.0
    )

    return {
        "target_percentage": target_percentage,
        "coverage_percentage": round(coverage_percentage, 2),
        "meets_target": coverage_percentage >= target_percentage
        if total_cost > 0
        else False,
        "status": "no_data"
        if total_cost <= 0
        else ("ok" if coverage_percentage >= target_percentage else "warning"),
        "total_cost": round(total_cost, 6),
        "allocated_cost": round(allocated_cost, 6),
        "unallocated_cost": round(max(total_cost - allocated_cost, 0.0), 6),
        "over_allocated_cost": round(over_allocated_cost, 6),
        "total_records": total_records,
        "allocated_records": int(allocated_row.allocated_records or 0),
        "allocation_rows": int(allocated_row.allocation_rows or 0),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
    }


async def get_unallocated_analysis(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    start_date: date,
    end_date: date,
) -> list[dict[str, Any]]:
    """Identify top services contributing to unallocated spend."""
    from sqlalchemy import func

    allocation_rollup = cost_allocation_rollup_subquery(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
    )
    unallocated_amount = unallocated_amount_expr(
        origin_amount=CostRecord.cost_usd,
        allocated_amount=allocation_rollup.c.allocated_amount,
        allocation_count=allocation_rollup.c.allocation_count,
    )
    query = (
        select(
            CostRecord.service,
            func.sum(unallocated_amount).label("total_unallocated"),
            func.count(CostRecord.id).label("record_count"),
        )
        .outerjoin(
            allocation_rollup,
            (allocation_rollup.c.cost_record_id == CostRecord.id)
            & (allocation_rollup.c.recorded_at == CostRecord.recorded_at),
        )
        .where(CostRecord.tenant_id == tenant_id)
        .where(CostRecord.recorded_at >= start_date)
        .where(CostRecord.recorded_at <= end_date)
        .where(unallocated_amount > Decimal("0"))
        .group_by(CostRecord.service)
        .order_by(func.sum(unallocated_amount).desc())
        .limit(5)
    )

    rows = (await db.execute(query)).all()
    return [
        {
            "service": row.service,
            "amount": coerce_finite_float(
                row.total_unallocated,
                field_name="total_unallocated",
            ),
            "count": row.record_count,
            "recommendation": (
                f"Create a DIRECT rule for service '{row.service}' to a specific team bucket."
            ),
        }
        for row in rows
    ]
