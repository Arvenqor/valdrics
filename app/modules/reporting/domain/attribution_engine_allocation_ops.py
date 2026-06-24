"""Allocation orchestration operations for the attribution engine."""

from __future__ import annotations

import fnmatch
from datetime import date
from decimal import Decimal
from typing import Any, cast
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribution import AttributionRule, CostAllocation
from app.models.cloud import CostRecord
from app.modules.reporting.domain.attribution_engine_allocation_analytics import (
    get_allocation_coverage,
    get_allocation_summary,
    get_unallocated_analysis,
)
from app.modules.reporting.domain.attribution_engine_rule_application import (
    allocation_record_date,
    apply_matching_rule,
    build_unallocated_allocation,
)
from app.modules.reporting.domain.attribution_engine_simulation_ops import (
    simulate_rule,
)

__all__ = [
    "match_conditions",
    "apply_rules",
    "process_cost_record",
    "process_llm_usage_record",
    "apply_rules_to_tenant",
    "apply_rules_to_tenant_ai",
    "get_allocation_summary",
    "get_allocation_coverage",
    "get_unallocated_analysis",
    "simulate_rule",
]


def match_conditions(cost_record: Any, conditions: dict[str, Any]) -> bool:
    """
    Check if a cost record (or LLMUsage record) matches the rule conditions.

    Supports matching on: service, service_pattern, region, account_id, provider,
    cost_threshold_min_usd, tags, catch_all.
    """
    if not conditions:
        return True

    is_llm = hasattr(cost_record, "total_tokens")
    service = "LLM" if is_llm else getattr(cost_record, "service", None)
    region = None if is_llm else getattr(cost_record, "region", None)

    account_id: Any
    provider: Any
    if is_llm:
        raw_prov = getattr(cost_record, "provider", "unknown")
        account_id = f"ai:{raw_prov}"
        provider = "ai"
    else:
        account_id = getattr(cost_record, "account_id", None)
        if hasattr(cost_record, "provider"):
            provider = cost_record.provider
        elif hasattr(cost_record, "account") and cost_record.account is not None:
            provider = getattr(cost_record.account, "provider", None)
        else:
            provider = getattr(cost_record, "provider", None)

    cost_usd = getattr(cost_record, "cost_usd", Decimal("0"))
    if "service" in conditions and service != conditions["service"]:
        return False
    if "service_pattern" in conditions:
        pattern = conditions["service_pattern"]
        if not fnmatch.fnmatch(service or "", pattern):
            return False
    if "region" in conditions and region != conditions["region"]:
        return False
    if "account_id" in conditions and account_id != conditions["account_id"]:
        return False
    if "provider" in conditions and provider != conditions["provider"]:
        return False
    if "cost_threshold_min_usd" in conditions:
        min_cost = Decimal(str(conditions["cost_threshold_min_usd"]))
        if cost_usd < min_cost:
            return False

    if conditions.get("catch_all") is not True and "tags" in conditions:
        cost_tags = _cost_tags(cost_record, is_llm=is_llm)
        condition_tags = (
            conditions["tags"] if isinstance(conditions["tags"], dict) else {}
        )
        for tag_key, tag_value in condition_tags.items():
            if cost_tags.get(tag_key) != tag_value:
                return False

    return True


def _cost_tags(cost_record: Any, *, is_llm: bool) -> dict[str, Any]:
    if is_llm:
        raw_prov = getattr(cost_record, "provider", "unknown")
        return {
            "source": "llm_usage",
            "llm_provider": raw_prov.strip().lower() if raw_prov else "unknown",
            "model": getattr(cost_record, "model", "unknown"),
            "is_byok": getattr(cost_record, "is_byok", False),
            "request_type": getattr(cost_record, "request_type", "inference")
            or "inference",
        }

    direct_tags = getattr(cost_record, "tags", None)
    if isinstance(direct_tags, dict):
        return direct_tags
    metadata = getattr(cost_record, "ingestion_metadata", None)
    if not isinstance(metadata, dict):
        return {}
    raw_tags = metadata.get("tags", {})
    return raw_tags if isinstance(raw_tags, dict) else {}


async def apply_rules(
    cost_record: Any,
    rules: list[AttributionRule],
    *,
    match_conditions_fn: Any,
    logger_obj: Any,
) -> list[CostAllocation]:
    """
    Apply attribution rules to a cost record and return CostAllocation records.
    First matching rule wins (rules are pre-sorted by priority).
    """
    allocations: list[CostAllocation] = []
    is_llm = hasattr(cost_record, "total_tokens")
    rec_date = allocation_record_date(cost_record)

    for rule in rules:
        if not match_conditions_fn(cost_record, rule.conditions):
            continue
        allocations = apply_matching_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
            logger_obj=logger_obj,
        )
        break

    if not allocations:
        allocations.append(
            build_unallocated_allocation(
                cost_record,
                rec_date=rec_date,
                is_llm=is_llm,
            )
        )

    return allocations


async def process_cost_record(
    db: AsyncSession,
    cost_record: CostRecord,
    tenant_id: uuid.UUID,
    *,
    get_active_rules_fn: Any,
    apply_rules_fn: Any,
    logger_obj: Any,
) -> list[CostAllocation]:
    """Full pipeline: fetch rules, apply, and persist allocations."""
    rules = await get_active_rules_fn(tenant_id)
    allocations = cast(list[CostAllocation], await apply_rules_fn(cost_record, rules))

    for allocation in allocations:
        db.add(allocation)

    await db.commit()
    logger_obj.info(
        "attribution_applied",
        cost_record_id=str(cost_record.id),
        allocations_count=len(allocations),
    )
    return allocations


async def apply_rules_to_tenant(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start_date: date,
    end_date: date,
    *,
    get_active_rules_fn: Any,
    apply_rules_fn: Any,
    logger_obj: Any,
    commit: bool = True,
) -> dict[str, int]:
    """Batch apply attribution rules to all cost records in a date range."""
    query = (
        select(CostRecord)
        .where(CostRecord.tenant_id == tenant_id)
        .where(CostRecord.recorded_at >= start_date)
        .where(CostRecord.recorded_at <= end_date)
    )
    records = (await db.execute(query)).scalars().all()

    if not records:
        logger_obj.info(
            "no_cost_records_found_for_attribution", tenant_id=str(tenant_id)
        )
        return {"records_processed": 0, "allocations_created": 0}

    rules = await get_active_rules_fn(tenant_id)
    record_ids = [record.id for record in records]
    for i in range(0, len(record_ids), 1000):
        chunk = record_ids[i : i + 1000]
        await db.execute(
            delete(CostAllocation).where(CostAllocation.cost_record_id.in_(chunk))
        )

    all_allocations: list[CostAllocation] = []
    for record in records:
        allocations = await apply_rules_fn(record, rules)
        all_allocations.extend(allocations)

    if all_allocations:
        db.add_all(all_allocations)
    if commit:
        await db.commit()
    else:
        await db.flush()

    logger_obj.info(
        "batch_attribution_complete",
        tenant_id=str(tenant_id),
        records_processed=len(records),
        allocations_count=len(all_allocations),
    )
    return {
        "records_processed": len(records),
        "allocations_created": len(all_allocations),
    }


async def process_llm_usage_record(
    db: AsyncSession,
    llm_usage: Any,
    tenant_id: uuid.UUID,
    *,
    get_active_rules_fn: Any,
    apply_rules_fn: Any,
    logger_obj: Any,
) -> list[CostAllocation]:
    """Full pipeline: fetch rules, apply, and persist allocations for LLMUsage."""
    rules = await get_active_rules_fn(tenant_id)
    allocations = cast(list[CostAllocation], await apply_rules_fn(llm_usage, rules))

    for allocation in allocations:
        db.add(allocation)

    await db.commit()
    logger_obj.info(
        "ai_attribution_applied",
        llm_usage_id=str(llm_usage.id),
        allocations_count=len(allocations),
    )
    return allocations


async def apply_rules_to_tenant_ai(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    start_date: date,
    end_date: date,
    *,
    get_active_rules_fn: Any,
    apply_rules_fn: Any,
    logger_obj: Any,
    commit: bool = True,
) -> dict[str, int]:
    """Batch apply attribution rules to all LLM usage records in a date range."""
    from app.models.llm import LLMUsage
    from app.modules.reporting.domain.focus_export_rows import _date_window_bounds

    window_start, window_end = _date_window_bounds(start_date, end_date)
    query = (
        select(LLMUsage)
        .where(LLMUsage.tenant_id == tenant_id)
        .where(LLMUsage.created_at >= window_start)
        .where(LLMUsage.created_at < window_end)
    )
    records = (await db.execute(query)).scalars().all()

    if not records:
        logger_obj.info(
            "no_llm_records_found_for_attribution", tenant_id=str(tenant_id)
        )
        return {"records_processed": 0, "allocations_created": 0}

    rules = await get_active_rules_fn(tenant_id)
    record_ids = [record.id for record in records]
    for i in range(0, len(record_ids), 1000):
        chunk = record_ids[i : i + 1000]
        await db.execute(
            delete(CostAllocation).where(CostAllocation.llm_usage_id.in_(chunk))
        )

    all_allocations: list[CostAllocation] = []
    for record in records:
        allocations = await apply_rules_fn(record, rules)
        all_allocations.extend(allocations)

    if all_allocations:
        db.add_all(all_allocations)
    if commit:
        await db.commit()
    else:
        await db.flush()

    logger_obj.info(
        "batch_ai_attribution_complete",
        tenant_id=str(tenant_id),
        records_processed=len(records),
        allocations_count=len(all_allocations),
    )
    return {
        "records_processed": len(records),
        "allocations_created": len(all_allocations),
    }
