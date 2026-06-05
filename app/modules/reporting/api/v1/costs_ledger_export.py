import csv
import io
import json
from datetime import date
from typing import Any, AsyncGenerator, Optional
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.core.auth import CurrentUser
from app.modules.reporting.domain.spend_ledger import list_spend_ledger_entries
from app.modules.reporting.api.v1.costs_provider_filters import (
    normalize_spend_ledger_provider_filter,
)


async def generate_csv_rows(
    db: AsyncSession,
    tenant_id: Any,
    start_date: date,
    end_date: date,
    normalized_provider: Optional[str],
    include_preliminary: bool,
) -> AsyncGenerator[str, None]:
    headers = [
        "id",
        "recorded_at",
        "timestamp",
        "provider",
        "account_id",
        "account_name",
        "service",
        "region",
        "usage_type",
        "resource_id",
        "usage_amount",
        "usage_unit",
        "cost_usd",
        "amount_raw",
        "currency",
        "cost_status",
        "canonical_charge_category",
        "canonical_charge_subcategory",
        "canonical_mapping_version",
        "allocation_status",
        "allocated_amount_usd",
        "unallocated_amount_usd",
        "allocation_count",
        "tags",
        "allocations",
    ]

    # Yield header
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    yield buffer.getvalue()

    limit = 500
    offset = 0
    while True:
        payload = await list_spend_ledger_entries(
            db=db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            provider=normalized_provider,
            include_preliminary=include_preliminary,
            limit=limit,
            offset=offset,
        )
        entries = payload.get("entries", [])
        if not entries:
            break

        buffer = io.StringIO()
        writer = csv.writer(buffer)

        for entry in entries:
            tags_json = json.dumps(entry.get("tags", {}))
            allocations_json = json.dumps(entry.get("allocations", []))

            row = [
                entry.get("id"),
                entry.get("recorded_at"),
                entry.get("timestamp"),
                entry.get("provider"),
                entry.get("account_id"),
                entry.get("account_name"),
                entry.get("service"),
                entry.get("region"),
                entry.get("usage_type"),
                entry.get("resource_id"),
                entry.get("usage_amount"),
                entry.get("usage_unit"),
                entry.get("cost_usd"),
                entry.get("amount_raw"),
                entry.get("currency"),
                entry.get("cost_status"),
                entry.get("canonical_charge_category"),
                entry.get("canonical_charge_subcategory"),
                entry.get("canonical_mapping_version"),
                entry.get("allocation_status"),
                entry.get("allocated_amount_usd"),
                entry.get("unallocated_amount_usd"),
                entry.get("allocation_count"),
                tags_json,
                allocations_json,
            ]
            writer.writerow(row)

        yield buffer.getvalue()

        if len(entries) < limit:
            break

        offset += limit


async def export_spend_ledger_impl(
    *,
    start_date: date,
    end_date: date,
    provider: Optional[str],
    include_preliminary: bool,
    db: AsyncSession,
    current_user: CurrentUser,
) -> StreamingResponse:
    from app.modules.reporting.api.v1 import costs as costs_module

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")

    tenant_id = costs_module._require_tenant_id(current_user)
    normalized_provider = normalize_spend_ledger_provider_filter(provider)

    filename = f"spend_ledger_{tenant_id}_{start_date}_to_{end_date}.csv"

    return StreamingResponse(
        generate_csv_rows(
            db=db,
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            normalized_provider=normalized_provider,
            include_preliminary=include_preliminary,
        ),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
