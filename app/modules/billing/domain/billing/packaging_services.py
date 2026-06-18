"""Backend pricing and entitlement services for packaging modernization."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()

__all__ = [
    "ManagedSpendService",
    "OptimizationCreditService",
    "SavingsShareService",
]


MANAGED_SPEND_TIER_CAPS: dict[str, float] = {
    "free": 2500.0,
    "starter": 10000.0,
    "growth": 50000.0,
    "pro": 250000.0,
    "enterprise": float("inf"),
}

OPTIMIZATION_CREDIT_ALLOWANCE: dict[str, int] = {
    "free": 5,
    "starter": 20,
    "growth": 100,
    "pro": 500,
    "enterprise": 0,
}


class ManagedSpendService:
    """Service for Managed Cloud Spend tier gating and forecasts."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trailing_spend(self, tenant_id: UUID) -> float:
        """
        Get trailing 30-day normalized net spend for a tenant.

        Returns the sum of net_amount from the last 30 days of spend snapshots.
        """
        from app.models.pricing import ManagedSpendSnapshot

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        result = await self.db.execute(
            select(ManagedSpendSnapshot).where(
                and_(
                    ManagedSpendSnapshot.tenant_id == tenant_id,
                    ManagedSpendSnapshot.period_end >= cutoff,
                )
            )
        )
        snapshots = result.scalars().all()
        total = sum(snap.net_amount for snap in snapshots if snap.net_amount)
        logger.info(
            "managed_spend_lookup",
            tenant_id=str(tenant_id),
            total_spend=float(total),
            snapshot_count=len(snapshots),
        )
        return float(total)

    async def get_month_forecast(self, tenant_id: UUID) -> float:
        """
        Get current-month spend forecast for a tenant.

        Uses incomplete current month snapshots to project final spend.
        """
        from app.models.pricing import ManagedSpendSnapshot

        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        next_month = period_start.replace(month=period_start.month % 12 + 1)
        days_in_month = (next_month - period_start).days
        days_passed = now.day
        if days_passed == 0:
            days_passed = 1

        result = await self.db.execute(
            select(ManagedSpendSnapshot).where(
                and_(
                    ManagedSpendSnapshot.tenant_id == tenant_id,
                    ManagedSpendSnapshot.period_start >= period_start,
                )
            )
        )
        snapshots = result.scalars().all()
        current_spend = sum(snap.net_amount for snap in snapshots if snap.net_amount)
        projected = (current_spend / days_passed) * days_in_month if days_passed > 0 else 0
        logger.info(
            "spend_forecast_calculated",
            tenant_id=str(tenant_id),
            projected_spend=float(projected),
            days_passed=days_passed,
        )
        return float(projected)

    async def check_threshold_alert(
        self, tenant_id: UUID, tier: str
    ) -> Optional[dict[str, Any]]:
        """
        Check if tenant is approaching managed spend threshold.

        Returns alert data if within 80% of tier cap, None otherwise.
        """
        spent = await self.get_trailing_spend(tenant_id)
        tier_cap = MANAGED_SPEND_TIER_CAPS.get(tier, 0)
        if tier_cap == 0 or tier_cap == float("inf"):
            return None

        utilization = spent / tier_cap
        if utilization >= 0.8:
            alert = {
                "threshold_type": "managed_spend",
                "tier": tier,
                "spent": spent,
                "cap": tier_cap,
                "utilization_percent": round(utilization * 100, 1),
                "alert_level": "warning" if utilization < 0.95 else "critical",
            }
            logger.warning(
                "managed_spend_threshold_alert",
                tenant_id=str(tenant_id),
                **alert,
            )
            return alert
        return None

    async def get_upgrade_signal(
        self, tenant_id: UUID, tier: str
    ) -> Optional[dict[str, Any]]:
        """
        Determine if tenant should receive upgrade prompt.

        Signals include spending near cap or savings exceeding 3x plan price.
        """
        from app.shared.core.pricing import TIER_CONFIG, PricingTier

        spent = await self.get_trailing_spend(tenant_id)
        tier_cap = MANAGED_SPEND_TIER_CAPS.get(tier)

        signal = None
        if tier_cap and tier_cap != float("inf"):
            if spent >= tier_cap * 0.95:
                config = TIER_CONFIG.get(PricingTier(tier), {})
                price = config.get("price_usd", 0)
                if isinstance(price, dict):
                    price = price.get("monthly", 0)
                signal = {
                    "reason": "spend_near_cap",
                    "spent": spent,
                    "cap": tier_cap,
                    "upgrade_to": self._get_next_tier(tier),
                }
        await self.db.commit()
        if signal:
            logger.info("upgrade_signal_generated", tenant_id=str(tenant_id), **signal)
        return signal

    def _get_next_tier(self, current_tier: str) -> Optional[str]:
        """Get next higher tier for upgrade recommendation."""
        tier_order = ["free", "starter", "growth", "pro", "enterprise"]
        try:
            idx = tier_order.index(current_tier)
            if idx < len(tier_order) - 1:
                return tier_order[idx + 1]
        except ValueError:
            pass
        return None


class OptimizationCreditService:
    """Service for optimization credit balance management and consumption."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, tenant_id: UUID, tier: str) -> int:
        """
        Get current credit balance for tenant.

        For self-serve tiers, returns credits from current period ledger.
        For enterprise, returns committed credit pool balance.
        """
        from app.models.pricing import OptimizationCreditLedger

        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        result = await self.db.execute(
            select(OptimizationCreditLedger).where(
                and_(
                    OptimizationCreditLedger.tenant_id == tenant_id,
                    OptimizationCreditLedger.period_start == period_start,
                    OptimizationCreditLedger.status == "completed",
                )
            )
        )
        ledger_entries = result.scalars().all()
        consumed = sum(entry.credits_consumed for entry in ledger_entries)

        allowance = OPTIMIZATION_CREDIT_ALLOWANCE.get(tier, 0)
        if tier == "enterprise":
            allowance = await self._get_enterprise_commitment(tenant_id)

        balance = allowance - consumed
        logger.info(
            "credit_balance_lookup",
            tenant_id=str(tenant_id),
            allowance=allowance,
            consumed=consumed,
            balance=balance,
        )
        return max(0, balance)

    async def _get_enterprise_commitment(self, tenant_id: UUID) -> int:
        """Get enterprise committed credit pool."""
        from app.models.pricing import EnterpriseContractOverride

        result = await self.db.execute(
            select(EnterpriseContractOverride).where(
                EnterpriseContractOverride.tenant_id == tenant_id
            )
        )
        override = result.scalar_one_or_none()
        return override.custom_credit_commitment or 0 if override else 0

    async def consume_credits(
        self,
        tenant_id: UUID,
        action_type: str,
        action_id: Optional[UUID],
        credits: int,
        weight: float,
        idempotency_key: str,
        tier: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Consume credits idempotently for an action.

        Returns consumption result with remaining balance.
        """
        from app.models.pricing import OptimizationCreditLedger

        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        result = await self.db.execute(
            select(OptimizationCreditLedger).where(
                OptimizationCreditLedger.idempotency_key == idempotency_key
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            logger.info("credit_consumption_duplicate", idempotency_key=idempotency_key)
            return {
                "status": "duplicate",
                "credits_consumed": existing.credits_consumed,
                "balance": await self.get_balance(tenant_id, tier),
            }

        effective_tier = tier
        balance = await self.get_balance(tenant_id, effective_tier)
        if balance < credits:
            logger.warning(
                "credit_consumption_blocked",
                tenant_id=str(tenant_id),
                requested=credits,
                balance=balance,
            )
            entry = OptimizationCreditLedger(
                tenant_id=tenant_id,
                period_start=period_start,
                period_end=period_end,
                starting_balance=balance,
                action_type=action_type,
                action_id=action_id,
                credits_consumed=credits,
                action_weight=weight,
                metadata=metadata or {},
                idempotency_key=idempotency_key,
                status="blocked",
            )
            self.db.add(entry)
            await self.db.flush()
            return {
                "status": "blocked",
                "credits_requested": credits,
                "balance": balance,
                "message": "Insufficient credits",
            }

        entry = OptimizationCreditLedger(
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            starting_balance=balance,
            action_type=action_type,
            action_id=action_id,
            credits_consumed=credits,
            action_weight=weight,
            metadata=metadata or {},
            idempotency_key=idempotency_key,
            status="completed",
        )
        self.db.add(entry)
        await self.db.flush()

        logger.info(
            "credits_consumed",
            tenant_id=str(tenant_id),
            action_type=action_type,
            credits=credits,
            idempotency_key=idempotency_key,
        )
        return {
            "status": "completed",
            "credits_consumed": credits,
            "balance": balance - credits,
        }

    async def reverse_failed_consumption(
        self, idempotency_key: str, reason: str
    ) -> bool:
        """
        Reverse a credit consumption for failed actions.

        Marks the ledger entry as reversed instead of deleting.
        """
        from app.models.pricing import OptimizationCreditLedger

        result = await self.db.execute(
            select(OptimizationCreditLedger).where(
                OptimizationCreditLedger.idempotency_key == idempotency_key
            )
        )
        entry = result.scalar_one_or_none()
        if not entry or entry.status != "completed":
            return False

        entry.status = "reversed"
        if entry.metadata_json:
            entry.metadata_json["reversal_reason"] = reason
        await self.db.flush()

        logger.info(
            "credit_reversal_processed",
            tenant_id=str(entry.tenant_id),
            idempotency_key=idempotency_key,
            reason=reason,
        )
        return True

    async def forecast_burn(self, tenant_id: UUID, tier: str) -> dict[str, Any]:
        """
        Forecast credit burn rate and exhaustion date.

        Analyzes recent consumption patterns to predict depletion.
        """
        from app.models.pricing import OptimizationCreditLedger

        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        result = await self.db.execute(
            select(OptimizationCreditLedger).where(
                and_(
                    OptimizationCreditLedger.tenant_id == tenant_id,
                    OptimizationCreditLedger.period_start == period_start,
                    OptimizationCreditLedger.status == "completed",
                )
            )
        )
        entries = result.scalars().all()
        daily_avg = sum(e.credits_consumed for e in entries) / max(1, now.day)

        balance = await self.get_balance(tenant_id, tier)
        days_until_exhausted = int(balance / daily_avg) if daily_avg > 0 else 999

        forecast = {
            "daily_average": round(daily_avg, 2),
            "balance": balance,
            "days_until_exhausted": days_until_exhausted,
            "exhaustion_date": (
                now + timedelta(days=days_until_exhausted)
                if days_until_exhausted < 30
                else None
            ),
        }
        logger.info("credit_burn_forecast", tenant_id=str(tenant_id), **forecast)
        return forecast


class SavingsShareService:
    """Service for validated savings share calculations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_baseline(
        self, tenant_id: UUID, window_start: datetime, window_end: datetime
    ) -> float:
        """Calculate baseline spend for savings share attribution."""
        from app.models.pricing import ManagedSpendSnapshot

        result = await self.db.execute(
            select(ManagedSpendSnapshot).where(
                and_(
                    ManagedSpendSnapshot.tenant_id == tenant_id,
                    ManagedSpendSnapshot.period_end >= window_start,
                    ManagedSpendSnapshot.period_end <= window_end,
                )
            )
        )
        snapshots = result.scalars().all()
        total = sum(s.net_amount for s in snapshots if s.net_amount)
        logger.info(
            "savings_share_baseline_calculated",
            tenant_id=str(tenant_id),
            baseline_spend=float(total),
            window_days=(window_end - window_start).days,
        )
        return float(total)

    async def calculate_actual(
        self, tenant_id: UUID, window_start: datetime, window_end: datetime
    ) -> float:
        """Calculate actual spend for savings share attribution."""
        return await self.calculate_baseline(tenant_id, window_start, window_end)

    async def calculate_validated_savings(
        self,
        baseline_spend: float,
        actual_spend: float,
        exclusions: Optional[dict[str, float]] = None,
    ) -> float:
        """
        Calculate validated savings after exclusions.

        Exclusions adjust for one-time expenses, provisioning changes, etc.
        """
        total_exclusions = sum(exclusions.values()) if exclusions else 0
        validated_savings = baseline_spend - actual_spend - total_exclusions
        validated_savings = max(0, validated_savings)
        logger.info(
            "savings_share_calculated",
            baseline=baseline_spend,
            actual=actual_spend,
            exclusions=total_exclusions,
            validated_savings=validated_savings,
        )
        return validated_savings

    async def calculate_cap(
        self, tenant_id: UUID, share_percentage: float, subscription_fee: float
    ) -> float:
        """
        Calculate savings share cap.

        Self-serve: 3x monthly subscription fee.
        Enterprise: Custom cap from contract override.
        """
        from app.models.pricing import EnterpriseContractOverride

        result = await self.db.execute(
            select(EnterpriseContractOverride).where(
                EnterpriseContractOverride.tenant_id == tenant_id
            )
        )
        override = result.scalar_one_or_none()

        if override and override.custom_cap_amount:
            return float(override.custom_cap_amount)
        return subscription_fee * 3

    async def create_calculation_record(
        self,
        tenant_id: UUID,
        baseline_window: tuple[datetime, datetime],
        actual_window: tuple[datetime, datetime],
        recommendation_id: Optional[UUID],
        opted_in_scope: str,
        baseline_spend: float,
        actual_spend: float,
        exclusions: float,
        share_percentage: float,
        subscription_fee: float,
    ) -> Optional[UUID]:
        """
        Create a savings share calculation record.

        Returns the record ID for audit and dispute reference.
        """
        from app.models.pricing import SavingsShareCalculation

        validated_savings = await self.calculate_validated_savings(
            baseline_spend, actual_spend, None
        )
        cap = await self.calculate_cap(tenant_id, share_percentage, subscription_fee)
        calculated_share = min(validated_savings * share_percentage, cap)

        record = SavingsShareCalculation(
            tenant_id=tenant_id,
            baseline_window_start=baseline_window[0],
            baseline_window_end=baseline_window[1],
            actual_window_start=actual_window[0],
            actual_window_end=actual_window[1],
            recommendation_id=recommendation_id,
            opted_in_scope=opted_in_scope,
            normalized_baseline_spend=baseline_spend,
            normalized_actual_spend=actual_spend,
            excluded_adjustments=exclusions,
            validated_savings=validated_savings,
            share_percentage=share_percentage,
            cap_amount=cap,
            calculated_share=calculated_share,
            dispute_status="pending",
            metadata={"subscription_fee": subscription_fee},
        )
        self.db.add(record)
        await self.db.flush()

        logger.info(
            "savings_share_record_created",
            tenant_id=str(tenant_id),
            record_id=str(record.id),
            validated_savings=validated_savings,
            calculated_share=calculated_share,
        )
        return record.id

    async def freeze_for_dispute(self, calculation_id: UUID) -> bool:
        """Freeze a calculation record during dispute review."""
        from app.models.pricing import SavingsShareCalculation

        result = await self.db.execute(
            select(SavingsShareCalculation).where(
                SavingsShareCalculation.id == calculation_id
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return False

        record.dispute_status = "frozen"
        await self.db.flush()

        logger.info("savings_share_frozen", calculation_id=str(calculation_id))
        return True

    async def resolve_dispute(
        self,
        calculation_id: UUID,
        new_cap: Optional[float] = None,
        adjustment: Optional[float] = None,
    ) -> bool:
        """
        Resolve a disputed calculation.

        Applies adjustments and updates the record.
        """
        from app.models.pricing import SavingsShareCalculation

        result = await self.db.execute(
            select(SavingsShareCalculation).where(
                SavingsShareCalculation.id == calculation_id
            )
        )
        record = result.scalar_one_or_none()
        if not record or record.dispute_status != "frozen":
            return False

        if new_cap is not None:
            record.cap_amount = new_cap
            record.calculated_share = min(
                record.validated_savings * record.share_percentage, new_cap
            )

        if adjustment is not None and record.metadata_json:
            record.metadata_json["dispute_adjustment"] = adjustment

        record.dispute_status = "resolved"
        await self.db.flush()

        logger.info("savings_share_dispute_resolved", calculation_id=str(calculation_id))
        return True
