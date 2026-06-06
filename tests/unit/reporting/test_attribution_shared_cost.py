import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4
from unittest.mock import MagicMock

from app.models.attribution import AttributionRule
from app.models.cloud import CostRecord
from app.modules.reporting.domain.attribution_engine_allocation_ops import (
    match_conditions,
    apply_rules,
)


@pytest.mark.asyncio
async def test_match_conditions_service_pattern():
    # Test service pattern wildcard matchers
    record = MagicMock(spec=CostRecord)
    record.service = "AmazonEC2"
    record.provider = "aws"
    record.cost_usd = Decimal("10.00")
    record.region = "us-east-1"
    record.account_id = "123"

    assert match_conditions(record, {"service_pattern": "Amazon*"}) is True
    assert match_conditions(record, {"service_pattern": "*EC2"}) is True
    assert match_conditions(record, {"service_pattern": "*EC*"}) is True
    assert match_conditions(record, {"service_pattern": "Google*"}) is False


@pytest.mark.asyncio
async def test_match_conditions_provider():
    # Test direct provider matching without tags
    record = MagicMock(spec=CostRecord)
    record.service = "SaaS-Service"
    record.provider = "saas"
    record.cost_usd = Decimal("50.00")
    record.tags = None

    assert match_conditions(record, {"provider": "saas"}) is True
    assert match_conditions(record, {"provider": "aws"}) is False


@pytest.mark.asyncio
async def test_match_conditions_threshold():
    # Test cost threshold min usd
    record = MagicMock(spec=CostRecord)
    record.service = "S3"
    record.cost_usd = Decimal("1.25")

    assert match_conditions(record, {"cost_threshold_min_usd": 1.00}) is True
    assert match_conditions(record, {"cost_threshold_min_usd": 2.00}) is False


@pytest.mark.asyncio
async def test_match_conditions_catch_all():
    # Test catch-all condition matches anything
    record = MagicMock(spec=CostRecord)
    record.service = "Unknown"
    record.cost_usd = Decimal("0.05")
    record.tags = None
    record.ingestion_metadata = None

    assert match_conditions(record, {"catch_all": True}) is True
    # If other conditions are also present, catch_all skips tags check but evaluates them
    assert match_conditions(record, {"catch_all": True, "provider": "gcp"}) is False


@pytest.mark.asyncio
async def test_apply_rules_even_split_remainder():
    # Test EVEN_SPLIT divides cost and remainder goes to the first bucket
    record = MagicMock(spec=CostRecord)
    record.id = uuid4()
    record.cost_usd = Decimal("10.01")  # 10.01 / 3 = 3.33666667
    record.recorded_at = date(2026, 1, 1)

    rule = MagicMock(spec=AttributionRule)
    rule.id = uuid4()
    rule.rule_type = "EVEN_SPLIT"
    rule.conditions = {}
    rule.allocation = [
        {"bucket": "Engineering"},
        {"bucket": "Sales"},
        {"bucket": "Platform"},
    ]

    mock_logger = MagicMock()
    allocs = await apply_rules(
        record, [rule], match_conditions_fn=lambda *a: True, logger_obj=mock_logger
    )

    assert len(allocs) == 3
    # Check deterministic remainder assignment:
    # engineering (first bucket) gets remainder: 10.01 - 3.33666667 * 2 = 3.33666666
    # percentage base is 100.00 / 3 = 33.33, remainder 100.00 - 33.33 * 2 = 33.34
    allocs_by_bucket = {a.allocated_to: a for a in allocs}

    assert allocs_by_bucket["Engineering"].amount == Decimal("3.33666666")
    assert allocs_by_bucket["Engineering"].percentage == Decimal("33.34")
    assert allocs_by_bucket["Sales"].amount == Decimal("3.33666667")
    assert allocs_by_bucket["Sales"].percentage == Decimal("33.33")
    assert allocs_by_bucket["Platform"].amount == Decimal("3.33666667")
    assert allocs_by_bucket["Platform"].percentage == Decimal("33.33")


@pytest.mark.asyncio
async def test_apply_rules_proportional_weight_ratios():
    record = MagicMock(spec=CostRecord)
    record.id = uuid4()
    record.cost_usd = Decimal("100.00")
    record.recorded_at = date(2026, 1, 1)

    rule = MagicMock(spec=AttributionRule)
    rule.id = uuid4()
    rule.rule_type = "PROPORTIONAL"
    rule.conditions = {}
    rule.allocation = [
        {"bucket": "Engineering", "weight": 3},
        {"bucket": "Sales", "weight": 1},
    ]

    mock_logger = MagicMock()
    allocs = await apply_rules(
        record, [rule], match_conditions_fn=lambda *a: True, logger_obj=mock_logger
    )

    assert len(allocs) == 2
    allocs_by_bucket = {a.allocated_to: a for a in allocs}
    assert allocs_by_bucket["Engineering"].amount == Decimal("75.00000000")
    assert allocs_by_bucket["Engineering"].percentage == Decimal("75.00")
    assert allocs_by_bucket["Sales"].amount == Decimal("25.00000000")
    assert allocs_by_bucket["Sales"].percentage == Decimal("25.00")


@pytest.mark.asyncio
async def test_apply_rules_proportional_zero_weights():
    # Test PROPORTIONAL handles zero-weight buckets gracefully
    record = MagicMock(spec=CostRecord)
    record.id = uuid4()
    record.cost_usd = Decimal("100.00")
    record.recorded_at = date(2026, 1, 1)

    rule = MagicMock(spec=AttributionRule)
    rule.id = uuid4()
    rule.rule_type = "PROPORTIONAL"
    rule.conditions = {}
    rule.allocation = [
        {"bucket": "Engineering", "weight": 0},
        {"bucket": "Sales", "weight": 1},
        {"bucket": "Marketing", "weight": 0},
    ]

    mock_logger = MagicMock()
    allocs = await apply_rules(
        record, [rule], match_conditions_fn=lambda *a: True, logger_obj=mock_logger
    )

    assert len(allocs) == 3
    allocs_by_bucket = {a.allocated_to: a for a in allocs}
    assert allocs_by_bucket["Engineering"].amount == Decimal("0.00")
    assert allocs_by_bucket["Engineering"].percentage == Decimal("0.00")
    assert allocs_by_bucket["Sales"].amount == Decimal("100.00")
    assert allocs_by_bucket["Sales"].percentage == Decimal("100.00")
    assert allocs_by_bucket["Marketing"].amount == Decimal("0.00")
    assert allocs_by_bucket["Marketing"].percentage == Decimal("0.00")
