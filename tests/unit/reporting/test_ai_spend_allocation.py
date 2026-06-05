import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attribution import AttributionRule, CostAllocation
from app.models.llm import LLMUsage
from app.modules.reporting.domain.attribution_engine_allocation_ops import (
    process_llm_usage_record,
    apply_rules,
)
from app.modules.reporting.domain.spend_ledger_ai import (
    ai_spend_summary,
    ai_spend_entries,
)


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def tenant_id():
    return uuid4()


@pytest.mark.asyncio
async def test_process_llm_usage_record(mock_db, tenant_id):
    # Test that process_llm_usage_record correctly calls get_active_rules, applies them and commits
    llm_usage = MagicMock(spec=LLMUsage)
    llm_usage.id = uuid4()
    llm_usage.cost_usd = Decimal("0.05")
    llm_usage.created_at = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    llm_usage.provider = "openai"
    llm_usage.model = "gpt-4o"
    llm_usage.is_byok = False
    llm_usage.request_type = "inference"
    llm_usage.total_tokens = 1000

    rule = MagicMock(spec=AttributionRule)
    rule.id = uuid4()
    rule.rule_type = "DIRECT"
    rule.conditions = {}
    rule.allocation = {"bucket": "Engineering"}

    mock_logger = MagicMock()

    get_rules = AsyncMock(return_value=[rule])

    # Wrap apply_rules to supply keyword-only args during test
    def wrapped_apply(record, rules):
        return apply_rules(
            record, rules, match_conditions_fn=lambda *a: True, logger_obj=mock_logger
        )

    allocations = await process_llm_usage_record(
        db=mock_db,
        llm_usage=llm_usage,
        tenant_id=tenant_id,
        get_active_rules_fn=get_rules,
        apply_rules_fn=wrapped_apply,
        logger_obj=mock_logger,
    )

    assert len(allocations) == 1
    assert allocations[0].llm_usage_id == llm_usage.id
    assert allocations[0].cost_record_id is None
    assert allocations[0].allocated_to == "Engineering"
    assert allocations[0].amount == Decimal("0.05")
    mock_db.add.assert_called_once_with(allocations[0])
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_ai_spend_summary_and_entries_with_allocations(mock_db, tenant_id):
    # Set up some dummy LLMUsage records
    usage1 = MagicMock(spec=LLMUsage)
    usage1.id = uuid4()
    usage1.cost_usd = Decimal("0.10")
    usage1.created_at = datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    usage1.provider = "openai"
    usage1.model = "gpt-4o"
    usage1.is_byok = False
    usage1.request_type = "inference"
    usage1.total_tokens = 2000

    usage2 = MagicMock(spec=LLMUsage)
    usage2.id = uuid4()
    usage2.cost_usd = Decimal("0.20")
    usage2.created_at = datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
    usage2.provider = "anthropic"
    usage2.model = "claude-3"
    usage2.is_byok = False
    usage2.request_type = "inference"
    usage2.total_tokens = 4000

    # Mock DB query for LLMUsage
    mock_usage_result = MagicMock()
    mock_usage_result.all.return_value = [usage1, usage2]

    # Mock DB query for ai_spend_entries scalar()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [usage1, usage2]
    mock_usage_result.scalars.return_value = mock_scalars

    # Allocations for usage1 (allocated to Engineering) and usage2 (unallocated/split)
    alloc1 = CostAllocation(
        id=uuid4(),
        llm_usage_id=usage1.id,
        recorded_at=date(2026, 1, 1),
        allocated_to="Engineering",
        amount=Decimal("0.10"),
        percentage=Decimal("100.00"),
        timestamp=datetime.now(timezone.utc),
    )
    # allocs for usage2 (partially allocated)
    alloc2 = CostAllocation(
        id=uuid4(),
        llm_usage_id=usage2.id,
        recorded_at=date(2026, 1, 1),
        allocated_to="Sales",
        amount=Decimal("0.15"),
        percentage=Decimal("75.00"),
        timestamp=datetime.now(timezone.utc),
    )
    alloc3 = CostAllocation(
        id=uuid4(),
        llm_usage_id=usage2.id,
        recorded_at=date(2026, 1, 1),
        allocated_to="Unallocated",
        amount=Decimal("0.05"),
        percentage=None,
        timestamp=datetime.now(timezone.utc),
    )

    mock_alloc_result = MagicMock()
    mock_alloc_result.scalars.return_value.all.return_value = [alloc1, alloc2, alloc3]

    # Configure mock db behavior
    async def side_effect(stmt, *args, **kwargs):
        # Determine if it's the usage query or the allocation query
        stmt_str = str(stmt).lower()
        if "cost_allocations" in stmt_str:
            return mock_alloc_result
        else:
            return mock_usage_result

    mock_db.execute.side_effect = side_effect

    # Run ai_spend_summary
    summary = await ai_spend_summary(
        db=mock_db,
        tenant_id=tenant_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
    )

    assert summary["record_count"] == 2
    assert summary["total_cost"] == Decimal("0.30")
    assert summary["total_allocated"] == Decimal(
        "0.25"
    )  # 0.10 from alloc1 + 0.15 from alloc2
    assert summary["total_unallocated"] == Decimal("0.05")  # usage2 unallocated portion

    # Run ai_spend_entries
    entries = await ai_spend_entries(
        db=mock_db,
        tenant_id=tenant_id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 1),
        limit=10,
        offset=0,
    )

    assert len(entries) == 2
    entries_by_id = {e["id"]: e for e in entries}

    entry1 = entries_by_id[str(usage1.id)]
    assert entry1["allocation_status"] == "allocated"
    assert entry1["allocated_amount_usd"] == "0.10000000"
    assert entry1["unallocated_amount_usd"] == "0.00000000"
    assert len(entry1["allocations"]) == 1
    assert entry1["allocations"][0]["allocated_to"] == "Engineering"

    entry2 = entries_by_id[str(usage2.id)]
    assert entry2["allocation_status"] == "partially_allocated"
    assert entry2["allocated_amount_usd"] == "0.15000000"
    assert entry2["unallocated_amount_usd"] == "0.05000000"
    assert len(entry2["allocations"]) == 2
