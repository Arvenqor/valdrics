"""
Billing Job Handlers
"""

from typing import Dict, Any
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.background_job import BackgroundJob
from app.modules.governance.domain.jobs.handlers.base import BaseJobHandler
from app.modules.governance.domain.jobs.errors import JobExecutionError, PermanentJobError


class RecurringBillingHandler(BaseJobHandler):
    """Processes an individual recurring billing charge for a tenant."""

    async def execute(self, job: BackgroundJob, db: AsyncSession) -> Dict[str, Any]:
        from app.modules.billing.domain.billing.paystack_billing import (
            BillingService,
            TenantSubscription,
        )
        from app.modules.billing.domain.billing.paystack_service_impl import (
            RenewalOperationalError,
        )

        payload = job.payload or {}
        sub_id = payload.get("subscription_id")
        charge_reference = payload.get("charge_reference")

        if not sub_id:
            raise PermanentJobError("subscription_id required for recurring_billing")
        try:
            subscription_uuid = UUID(str(sub_id))
        except (TypeError, ValueError) as exc:
            raise PermanentJobError(
                "subscription_id must be a valid UUID for recurring_billing"
            ) from exc

        # Get subscription - P1: Enforce tenant isolation
        result = await db.execute(
            select(TenantSubscription).where(
                TenantSubscription.id == subscription_uuid,
                TenantSubscription.tenant_id == job.tenant_id,
            ).with_for_update()
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise PermanentJobError("Recurring billing subscription not found")

        if subscription.status != "active":
            return {
                "status": "skipped",
                "reason": f"subscription_status_is_{subscription.status}",
            }

        # Execute charge
        billing_service = BillingService(db)
        try:
            success = await billing_service.charge_renewal(
                subscription,
                reference=str(charge_reference) if charge_reference else None,
                commit=False,
            )
        except RenewalOperationalError as exc:
            raise JobExecutionError(str(exc)) from exc

        if success:
            # Fetch actual price for result reporting
            from app.models.pricing import PricingPlan

            plan_res = await db.execute(
                select(PricingPlan).where(PricingPlan.id == subscription.tier)
            )
            plan_obj = plan_res.scalar_one_or_none()
            price = float(plan_obj.price_usd) if plan_obj else 0.0

            return {"status": "completed", "amount_billed_usd": price}
        else:
            raise JobExecutionError("Paystack charge failed or authorization missing")
