"""Tests for pricing packaging models and services."""
from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

from app.models.pricing import (
    ManagedSpendSnapshot,
    OptimizationCreditLedger,
    AddOnCatalog,
    EnterpriseContractOverride,
    SavingsShareCalculation,
)
from app.modules.billing.domain.billing.packaging_services import (
    ManagedSpendService,
    OptimizationCreditService,
    SavingsShareService,
)


class TestManagedSpendSnapshotModel:
    def test_instantiation_with_required_fields(self) -> None:
        snapshot = ManagedSpendSnapshot(
            tenant_id=uuid4(),
            provider="aws",
            account_identifier="123456789012",
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
            currency="USD",
            gross_amount=1000.0,
            provider_discounts=100.0,
            net_amount=900.0,
        )
        assert snapshot.provider == "aws"
        assert snapshot.account_identifier == "123456789012"
        assert snapshot.currency == "USD"
        assert snapshot.gross_amount == 1000.0
        assert snapshot.net_amount == 900.0

    def test_unset_fields_are_none(self) -> None:
        snapshot = ManagedSpendSnapshot(
            tenant_id=uuid4(),
            provider="azure",
            account_identifier="tenant-abc",
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
        )
        assert snapshot.currency is None
        assert snapshot.gross_amount is None
        assert snapshot.net_amount is None
        assert snapshot.provider_discounts is None
        assert snapshot.inclusion_flags is None


class TestOptimizationCreditLedgerModel:
    def test_instantiation_with_required_fields(self) -> None:
        entry = OptimizationCreditLedger(
            tenant_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            starting_balance=100,
            action_type="ai_analysis",
            action_id=uuid4(),
            credits_consumed=5,
            action_weight=2.5,
            idempotency_key="unique-key-123",
            status="completed",
        )
        assert entry.action_type == "ai_analysis"
        assert entry.credits_consumed == 5
        assert entry.action_weight == 2.5
        assert entry.status == "completed"

    def test_unset_fields_are_none(self) -> None:
        entry = OptimizationCreditLedger(
            tenant_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            starting_balance=50,
            action_type="greenops_recommendation",
            credits_consumed=3,
            idempotency_key="key-456",
        )
        assert entry.status is None
        assert entry.metadata_json is None


class TestAddOnCatalogModel:
    def test_instantiation(self) -> None:
        addon = AddOnCatalog(
            slug="credit-pack-100",
            name="100 Credits",
            addon_type="credit_pack",
            price_usd=50.0,
            credit_amount=100,
        )
        assert addon.addon_type == "credit_pack"
        assert addon.credit_amount == 100

    def test_is_active_defaults(self) -> None:
        addon = AddOnCatalog(
            slug="inactive-addon",
            name="Inactive Addon",
            addon_type="private_deployment",
        )
        assert addon.is_active is None


class TestEnterpriseContractOverrideModel:
    def test_instantiation_with_custom_commitments(self) -> None:
        override = EnterpriseContractOverride(
            tenant_id=uuid4(),
            custom_managed_spend_commitment=1000000.0,
            custom_credit_commitment=5000,
            custom_retention_days=730,
            deployment_model="private",
            data_residency="US",
            support_sla="24x7",
            custom_addons={"connectors": "unlimited"},
            contract_status="active",
        )
        assert override.custom_managed_spend_commitment == 1000000.0
        assert override.custom_credit_commitment == 5000
        assert override.deployment_model == "private"
        assert override.contract_status == "active"

    def test_fields_default_to_none_when_unset(self) -> None:
        override = EnterpriseContractOverride(
            tenant_id=uuid4(),
            contract_status="active",
        )
        assert override.deployment_model is None
        assert override.data_residency is None
        assert override.support_sla is None
        assert override.custom_addons is None


class TestSavingsShareCalculationModel:
    def test_basic_calculation_record(self) -> None:
        now = datetime.now(timezone.utc)
        record = SavingsShareCalculation(
            tenant_id=uuid4(),
            baseline_window_start=now - timedelta(days=60),
            baseline_window_end=now - timedelta(days=30),
            actual_window_start=now - timedelta(days=30),
            actual_window_end=now,
            recommendation_id=uuid4(),
            opted_in_scope="account-123",
            normalized_baseline_spend=50000.0,
            normalized_actual_spend=45000.0,
            excluded_adjustments=1000.0,
            validated_savings=4000.0,
            share_percentage=0.15,
            cap_amount=1000.0,
            calculated_share=600.0,
            dispute_status="pending",
        )
        assert record.validated_savings == 4000.0
        assert record.share_percentage == 0.15
        assert record.dispute_status == "pending"

    def test_fields_default_to_none_when_unset(self) -> None:
        record = SavingsShareCalculation(
            tenant_id=uuid4(),
            baseline_window_start=datetime.now(timezone.utc) - timedelta(days=60),
            baseline_window_end=datetime.now(timezone.utc) - timedelta(days=30),
            actual_window_start=datetime.now(timezone.utc) - timedelta(days=30),
            actual_window_end=datetime.now(timezone.utc),
            opted_in_scope="all",
            normalized_baseline_spend=10000.0,
            normalized_actual_spend=9000.0,
        )
        assert record.dispute_status is None
        assert record.cap_amount is None


class TestManagedSpendService:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db: AsyncMock) -> ManagedSpendService:
        return ManagedSpendService(mock_db)

    @pytest.mark.asyncio
    async def test_get_trailing_spend_aggregates_snapshots(
        self, service: ManagedSpendService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        snapshots = [
            ManagedSpendSnapshot(
                tenant_id=uuid4(),
                provider="aws",
                account_identifier="acc-1",
                period_start=now - timedelta(days=15),
                period_end=now - timedelta(days=14),
                net_amount=1000.0,
            ),
            ManagedSpendSnapshot(
                tenant_id=uuid4(),
                provider="azure",
                account_identifier="acc-2",
                period_start=now - timedelta(days=10),
                period_end=now - timedelta(days=9),
                net_amount=500.0,
            ),
        ]
        mock_result = MagicMock()
        mock_scalar = MagicMock(return_value=snapshots)
        mock_result.scalars.return_value.all = mock_scalar
        mock_db.execute.return_value = mock_result

        total = await service.get_trailing_spend(uuid4())
        assert total == 1500.0

    @pytest.mark.asyncio
    async def test_check_threshold_alert_returns_when_near_cap(
        self, service: ManagedSpendService, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        alert = await service.check_threshold_alert(uuid4(), "starter")
        assert alert is None

    @pytest.mark.asyncio
    async def test_get_upgrade_signal_returns_next_tier(
        self, service: ManagedSpendService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        snapshots = [
            ManagedSpendSnapshot(
                tenant_id=uuid4(),
                provider="aws",
                account_identifier="acc-1",
                period_start=now - timedelta(days=5),
                period_end=now - timedelta(days=4),
                net_amount=9600.0,
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = snapshots
        mock_db.execute.return_value = mock_result

        signal = await service.get_upgrade_signal(uuid4(), "starter")
        assert signal is not None
        assert signal["reason"] == "spend_near_cap"
        assert signal["upgrade_to"] == "growth"


class TestOptimizationCreditService:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db: AsyncMock) -> OptimizationCreditService:
        return OptimizationCreditService(mock_db)

    @pytest.mark.asyncio
    async def test_get_balance_returns_remaining(
        self, service: OptimizationCreditService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        consumed_entries = [
            OptimizationCreditLedger(
                tenant_id=uuid4(),
                period_start=now.replace(day=1),
                period_end=now + timedelta(days=30),
                starting_balance=20,
                action_type="ai_analysis",
                credits_consumed=15,
                idempotency_key="key-1",
                status="completed",
            ),
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = consumed_entries
        mock_db.execute.return_value = mock_result

        balance = await service.get_balance(uuid4(), "starter")
        assert balance == 5

    @pytest.mark.asyncio
    async def test_consume_credits_idempotent(
        self, service: OptimizationCreditService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        existing_entry = OptimizationCreditLedger(
            tenant_id=uuid4(),
            period_start=now.replace(day=1),
            period_end=now + timedelta(days=30),
            starting_balance=20,
            action_type="ai_analysis",
            credits_consumed=5,
            idempotency_key="same-key",
            status="completed",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_entry
        mock_db.execute.return_value = mock_result

        result = await service.consume_credits(
            tenant_id=uuid4(),
            action_type="ai_analysis",
            action_id=uuid4(),
            credits=5,
            weight=1.0,
            idempotency_key="same-key",
            tier="starter",
        )
        assert result["status"] == "duplicate"
        assert result["credits_consumed"] == 5

    @pytest.mark.asyncio
    async def test_consume_credits_blocks_when_insufficient(
        self, service: OptimizationCreditService, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        result = await service.consume_credits(
            tenant_id=uuid4(),
            action_type="deep_ai_analysis",
            action_id=uuid4(),
            credits=50,
            weight=10.0,
            idempotency_key="new-key",
            tier="starter",
        )
        assert result["status"] == "blocked"
        assert "insufficient" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_reverse_failed_consumption(
        self, service: OptimizationCreditService, mock_db: AsyncMock
    ) -> None:
        entry = OptimizationCreditLedger(
            tenant_id=uuid4(),
            period_start=datetime.now(timezone.utc),
            period_end=datetime.now(timezone.utc) + timedelta(days=30),
            starting_balance=20,
            action_type="ai_analysis",
            credits_consumed=5,
            idempotency_key="reverse-key",
            status="completed",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = entry
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        success = await service.reverse_failed_consumption(
            "reverse-key", "action_failed"
        )
        assert success is True
        assert entry.status == "reversed"

    @pytest.mark.asyncio
    async def test_forecast_burn_estimates_exhaustion(
        self, service: OptimizationCreditService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        entries = [
            OptimizationCreditLedger(
                tenant_id=uuid4(),
                period_start=now.replace(day=1),
                period_end=now + timedelta(days=30),
                starting_balance=20,
                action_type="daily_analysis",
                credits_consumed=2,
                idempotency_key=f"key-{i}",
                status="completed",
            )
            for i in range(5)
        ]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = entries
        mock_db.execute.return_value = mock_result
        service.get_balance = AsyncMock(return_value=20)

        forecast = await service.forecast_burn(uuid4(), "free")
        assert forecast["daily_average"] > 0
        assert "days_until_exhausted" in forecast


class TestSavingsShareService:
    @pytest.fixture
    def mock_db(self) -> AsyncMock:
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_db: AsyncMock) -> SavingsShareService:
        return SavingsShareService(mock_db)

    @pytest.mark.asyncio
    async def test_calculate_validated_savings(
        self, service: SavingsShareService
    ) -> None:
        savings = await service.calculate_validated_savings(
            baseline_spend=100000.0, actual_spend=90000.0, exclusions={"one_time": 5000.0}
        )
        assert savings == 5000.0

    @pytest.mark.asyncio
    async def test_calculate_validated_savings_does_not_go_negative(
        self, service: SavingsShareService
    ) -> None:
        savings = await service.calculate_validated_savings(
            baseline_spend=50000.0, actual_spend=55000.0, exclusions=None
        )
        assert savings == 0.0

    @pytest.mark.asyncio
    async def test_calculate_cap_self_serve(
        self, service: SavingsShareService, mock_db: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        cap = await service.calculate_cap(uuid4(), 0.15, 100.0)
        assert cap == 300.0

    @pytest.mark.asyncio
    async def test_create_calculation_record_persists_values(
        self, service: SavingsShareService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        captured = []
        mock_db.add = MagicMock(side_effect=lambda record: captured.append(record))
        mock_db.flush = AsyncMock()

        record_id = await service.create_calculation_record(
            tenant_id=uuid4(),
            baseline_window=(now - timedelta(days=60), now - timedelta(days=30)),
            actual_window=(now - timedelta(days=30), now),
            recommendation_id=uuid4(),
            opted_in_scope="all",
            baseline_spend=100000.0,
            actual_spend=90000.0,
            exclusions=0.0,
            share_percentage=0.15,
            subscription_fee=100.0,
        )
        assert record_id is None
        assert captured[0].share_percentage == 0.15

    @pytest.mark.asyncio
    async def test_freeze_for_dispute(
        self, service: SavingsShareService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        record = SavingsShareCalculation(
            tenant_id=uuid4(),
            baseline_window_start=now - timedelta(days=60),
            baseline_window_end=now - timedelta(days=30),
            actual_window_start=now - timedelta(days=30),
            actual_window_end=now,
            opted_in_scope="all",
            normalized_baseline_spend=100000.0,
            normalized_actual_spend=90000.0,
            dispute_status="pending",
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        success = await service.freeze_for_dispute(record.id)
        assert success is True
        assert record.dispute_status == "frozen"

    @pytest.mark.asyncio
    async def test_resolve_dispute(
        self, service: SavingsShareService, mock_db: AsyncMock
    ) -> None:
        now = datetime.now(timezone.utc)
        record = SavingsShareCalculation(
            tenant_id=uuid4(),
            baseline_window_start=now - timedelta(days=60),
            baseline_window_end=now - timedelta(days=30),
            actual_window_start=now - timedelta(days=30),
            actual_window_end=now,
            opted_in_scope="all",
            normalized_baseline_spend=100000.0,
            normalized_actual_spend=90000.0,
            validated_savings=10000.0,
            share_percentage=0.15,
            cap_amount=300.0,
            dispute_status="frozen",
            metadata={},
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute.return_value = mock_result
        mock_db.flush = AsyncMock()

        success = await service.resolve_dispute(
            record.id, new_cap=5000.0, adjustment=1000.0
        )
        assert success is True
        assert record.dispute_status == "resolved"
        assert record.cap_amount == 5000.0
