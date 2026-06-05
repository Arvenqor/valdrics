"""Rule application strategies for attribution-engine allocations."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models.attribution import AttributionRule, CostAllocation


def allocation_record_date(cost_record: Any) -> Any:
    rec_date = getattr(cost_record, "recorded_at", None)
    if rec_date is not None:
        return rec_date
    return getattr(cost_record, "created_at").date()


def build_unallocated_allocation(
    cost_record: Any,
    *,
    rec_date: Any,
    is_llm: bool,
) -> CostAllocation:
    return _build_allocation(
        cost_record,
        None,
        rec_date=rec_date,
        is_llm=is_llm,
        bucket="Unallocated",
        amount=cost_record.cost_usd,
        percentage=Decimal("100.00"),
    )


def apply_matching_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
    logger_obj: Any,
) -> list[CostAllocation]:
    if rule.rule_type == "DIRECT":
        return _apply_direct_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
        )
    if rule.rule_type == "PERCENTAGE":
        return _apply_percentage_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
            logger_obj=logger_obj,
        )
    if rule.rule_type == "FIXED":
        return _apply_fixed_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
        )
    if rule.rule_type == "EVEN_SPLIT":
        return _apply_even_split_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
        )
    if rule.rule_type == "PROPORTIONAL":
        return _apply_proportional_rule(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
        )
    return []


def _build_allocation(
    cost_record: Any,
    rule: AttributionRule | None,
    *,
    rec_date: Any,
    is_llm: bool,
    bucket: Any,
    amount: Decimal,
    percentage: Decimal | None,
) -> CostAllocation:
    return CostAllocation(
        cost_record_id=None if is_llm else cost_record.id,
        llm_usage_id=cost_record.id if is_llm else None,
        recorded_at=rec_date,
        rule_id=rule.id if rule is not None else None,
        allocated_to=bucket,
        amount=amount,
        percentage=percentage,
        timestamp=datetime.now(timezone.utc),
    )


def _dict_splits(raw_allocation: Any) -> list[dict[str, Any]]:
    if isinstance(raw_allocation, list):
        return [item for item in raw_allocation if isinstance(item, dict)]
    if isinstance(raw_allocation, dict):
        return [raw_allocation]
    return []


def _apply_direct_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
) -> list[CostAllocation]:
    raw_allocation: Any = rule.allocation
    if isinstance(raw_allocation, list) and raw_allocation:
        first_entry = raw_allocation[0]
        bucket = (
            first_entry.get("bucket", "Unallocated")
            if isinstance(first_entry, dict)
            else "Unallocated"
        )
    elif isinstance(raw_allocation, dict):
        bucket = raw_allocation.get("bucket", "Unallocated")
    else:
        bucket = "Unallocated"

    return [
        _build_allocation(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
            bucket=bucket,
            amount=cost_record.cost_usd,
            percentage=Decimal("100.00"),
        )
    ]


def _apply_percentage_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
    logger_obj: Any,
) -> list[CostAllocation]:
    allocations: list[CostAllocation] = []
    total_percentage = Decimal("0")

    for split in _dict_splits(rule.allocation):
        bucket = split.get("bucket", "Unallocated")
        pct = Decimal(str(split.get("percentage", 0)))
        total_percentage += pct
        allocations.append(
            _build_allocation(
                cost_record,
                rule,
                rec_date=rec_date,
                is_llm=is_llm,
                bucket=bucket,
                amount=(cost_record.cost_usd * pct) / Decimal("100"),
                percentage=pct,
            )
        )

    if total_percentage != Decimal("100"):
        logger_obj.warning(
            "attribution_percentage_mismatch",
            rule_id=str(rule.id),
            total=float(total_percentage),
        )

    return allocations


def _apply_fixed_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
) -> list[CostAllocation]:
    allocations: list[CostAllocation] = []
    allocated_total = Decimal("0")

    for split in _dict_splits(rule.allocation):
        bucket = split.get("bucket", "Unallocated")
        fixed_amount = Decimal(str(split.get("amount", 0)))
        allocated_total += fixed_amount
        allocations.append(
            _build_allocation(
                cost_record,
                rule,
                rec_date=rec_date,
                is_llm=is_llm,
                bucket=bucket,
                amount=fixed_amount,
                percentage=None,
            )
        )

    remaining = cost_record.cost_usd - allocated_total
    if remaining > Decimal("0"):
        allocations.append(
            _build_allocation(
                cost_record,
                rule,
                rec_date=rec_date,
                is_llm=is_llm,
                bucket="Unallocated",
                amount=remaining,
                percentage=None,
            )
        )

    return allocations


def _even_split_buckets(raw_allocation: Any) -> list[Any]:
    buckets: list[Any] = []
    if isinstance(raw_allocation, list):
        for item in raw_allocation:
            if isinstance(item, dict) and "bucket" in item:
                buckets.append(item["bucket"])
    elif isinstance(raw_allocation, dict) and "bucket" in raw_allocation:
        buckets.append(raw_allocation["bucket"])
    return buckets or ["Unallocated"]


def _apply_even_split_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
) -> list[CostAllocation]:
    buckets = _even_split_buckets(rule.allocation)
    split_count = len(buckets)
    total_amount = cost_record.cost_usd
    base_amount = (total_amount / Decimal(split_count)).quantize(Decimal("1.00000000"))
    pct_base = (Decimal("100.00") / Decimal(split_count)).quantize(Decimal("1.00"))
    allocations: list[CostAllocation] = []

    for idx, bucket in enumerate(buckets):
        if idx == 0:
            bucket_amount = total_amount - base_amount * Decimal(split_count - 1)
            pct = Decimal("100.00") - pct_base * Decimal(split_count - 1)
        else:
            bucket_amount = base_amount
            pct = pct_base
        allocations.append(
            _build_allocation(
                cost_record,
                rule,
                rec_date=rec_date,
                is_llm=is_llm,
                bucket=bucket,
                amount=bucket_amount,
                percentage=pct,
            )
        )

    return allocations


def _proportional_splits(raw_allocation: Any) -> list[dict[str, Any]]:
    if isinstance(raw_allocation, list):
        splits = [
            item
            for item in raw_allocation
            if isinstance(item, dict) and "bucket" in item
        ]
    elif isinstance(raw_allocation, dict):
        splits = [raw_allocation]
    else:
        splits = []
    return splits or [{"bucket": "Unallocated", "weight": 1}]


def _parse_proportional_splits(
    raw_splits: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], Decimal]:
    parsed_splits: list[dict[str, Any]] = []
    total_weight = Decimal("0")
    for split in raw_splits:
        weight = Decimal(str(split.get("weight", 0)))
        if weight < Decimal("0"):
            weight = Decimal("0")
        total_weight += weight
        parsed_splits.append(
            {"bucket": split.get("bucket", "Unallocated"), "weight": weight}
        )
    return parsed_splits, total_weight


def _proportional_weighted_allocations(
    parsed_splits: list[dict[str, Any]],
    total_amount: Decimal,
    total_weight: Decimal,
) -> list[dict[str, Any]]:
    first_positive_idx = next(
        (
            idx
            for idx, split in enumerate(parsed_splits)
            if split["weight"] > Decimal("0")
        ),
        0,
    )
    allocated_amount_sum = Decimal("0")
    allocated_pct_sum = Decimal("0")
    temp_allocs: list[dict[str, Any]] = []

    for idx, split in enumerate(parsed_splits):
        weight = split["weight"]
        amount: Decimal | None
        pct: Decimal | None
        if weight == Decimal("0"):
            amount = Decimal("0.00000000")
            pct = Decimal("0.00")
        elif idx == first_positive_idx:
            amount = None
            pct = None
        else:
            amount = (total_amount * weight / total_weight).quantize(
                Decimal("1.00000000")
            )
            pct = (Decimal("100.00") * weight / total_weight).quantize(Decimal("1.00"))
            allocated_amount_sum += amount
            allocated_pct_sum += pct
        temp_allocs.append(
            {"bucket": split["bucket"], "amount": amount, "percentage": pct}
        )

    first_positive_split = temp_allocs[first_positive_idx]
    first_positive_split["amount"] = total_amount - allocated_amount_sum
    first_positive_split["percentage"] = Decimal("100.00") - allocated_pct_sum
    return temp_allocs


def _proportional_even_allocations(
    parsed_splits: list[dict[str, Any]],
    total_amount: Decimal,
) -> list[dict[str, Any]]:
    split_count = len(parsed_splits)
    base_amount = (total_amount / Decimal(split_count)).quantize(Decimal("1.00000000"))
    pct_base = (Decimal("100.00") / Decimal(split_count)).quantize(Decimal("1.00"))
    allocations: list[dict[str, Any]] = []

    for idx, split in enumerate(parsed_splits):
        if idx == 0:
            amount = total_amount - base_amount * Decimal(split_count - 1)
            pct = Decimal("100.00") - pct_base * Decimal(split_count - 1)
        else:
            amount = base_amount
            pct = pct_base
        allocations.append(
            {"bucket": split["bucket"], "amount": amount, "percentage": pct}
        )

    return allocations


def _apply_proportional_rule(
    cost_record: Any,
    rule: AttributionRule,
    *,
    rec_date: Any,
    is_llm: bool,
) -> list[CostAllocation]:
    parsed_splits, total_weight = _parse_proportional_splits(
        _proportional_splits(rule.allocation)
    )
    total_amount = cost_record.cost_usd
    split_allocations = (
        _proportional_weighted_allocations(
            parsed_splits,
            total_amount,
            total_weight,
        )
        if total_weight > Decimal("0")
        else _proportional_even_allocations(parsed_splits, total_amount)
    )

    return [
        _build_allocation(
            cost_record,
            rule,
            rec_date=rec_date,
            is_llm=is_llm,
            bucket=split["bucket"],
            amount=split["amount"],
            percentage=split["percentage"],
        )
        for split in split_allocations
    ]
