"""
Carbon Budget Alerts Service

Allows users to set monthly carbon (CO2) limits and receive
alerts when approaching or exceeding their budget.

Valdrics Innovation: Brings carbon accountability to
cloud teams with measurable targets and automated notifications.
"""

from typing import List, Dict, Any
from datetime import date, datetime, timezone
from uuid import UUID
import smtplib
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.shared.core.async_utils import maybe_await

logger = structlog.get_logger()

CARBON_SLACK_ALERT_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ImportError,
    SQLAlchemyError,
    RuntimeError,
    TypeError,
    ValueError,
    AttributeError,
)

CARBON_EMAIL_ALERT_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ImportError,
    smtplib.SMTPException,
    OSError,
    RuntimeError,
    TypeError,
    ValueError,
    AttributeError,
)


class CarbonBudgetService:
    """
    Manages carbon budgets and alerts for tenants.

    Features:
    - Set monthly CO2 limits (in kg)
    - Track current usage against budget
    - Send alerts at configurable thresholds (e.g., 80%, 100%)
    - Slack/email notifications with rate limiting
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_budget_status(
        self,
        tenant_id: UUID,
        month_start: date,
        current_co2_kg: float,
    ) -> Dict[str, Any]:
        """
        Get the current budget status for a tenant.

        Args:
            tenant_id: The tenant's UUID
            month_start: Start of the month to check
            current_co2_kg: Current CO2 emissions for the month

        Returns:
            Dict with budget info, usage, and alert status
        """
        from app.models.carbon_settings import CarbonSettings

        # Get tenant's carbon settings from database
        result = await self.db.execute(
            select(CarbonSettings).where(CarbonSettings.tenant_id == tenant_id)
        )
        settings = result.scalar_one_or_none()

        # Use settings from DB or defaults
        if settings:
            budget_kg = float(settings.carbon_budget_kg)
            alert_threshold_percent = int(settings.alert_threshold_percent)
        else:
            # Fallback defaults if no settings saved yet
            budget_kg = 100.0  # Default 100 kg CO2/month
            alert_threshold_percent = 80

        # Calculate usage percentage
        usage_percent = (current_co2_kg / budget_kg * 100) if budget_kg > 0 else 0

        # Determine alert status
        alert_status = "ok"
        if usage_percent >= 100:
            alert_status = "exceeded"
        elif usage_percent >= alert_threshold_percent:
            alert_status = "warning"

        return {
            "month": month_start.isoformat(),
            "budget_kg": budget_kg,
            "current_usage_kg": round(current_co2_kg, 3),
            "usage_percent": round(usage_percent, 1),
            "remaining_kg": round(max(0, budget_kg - current_co2_kg), 3),
            "alert_threshold_percent": alert_threshold_percent,
            "alert_status": alert_status,
            "recommendations": self._get_recommendations(usage_percent, alert_status),
        }

    def _get_recommendations(self, usage_percent: float, status: str) -> List[str]:
        """Generate contextual recommendations based on usage."""
        if status == "exceeded":
            return [
                "🚨 Carbon budget exceeded! Consider immediate optimization.",
                "Review Graviton migration opportunities for 40-60% energy savings.",
                "Check for zombie resources that may be wasting energy.",
                "Consider migrating workloads to lower-carbon regions.",
            ]
        elif status == "warning":
            return [
                "⚠️ Approaching carbon budget limit.",
                "Review resource utilization for optimization opportunities.",
                "Schedule non-urgent workloads for off-peak hours.",
            ]
        else:
            return [
                "✅ Carbon usage within budget.",
                "Continue monitoring to maintain efficiency.",
            ]

    async def should_send_alert(self, tenant_id: UUID, alert_status: str) -> bool:
        """
        Check if we should send an alert (rate limiting).

        Prevents alert spam by only sending once per status per day.
        """
        from app.models.carbon_settings import CarbonSettings

        result = await self.db.execute(
            select(CarbonSettings).where(CarbonSettings.tenant_id == tenant_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            return True  # First time, allow alert

        # Check if last_alert_sent exists and was today for THIS status
        # BE-CARBON-12: Status-aware rate limiting
        last_alert = getattr(settings, "last_alert_sent", None)
        last_status = getattr(settings, "last_alert_status", None)

        if last_alert and last_status == alert_status:
            # Normalize to UTC date to avoid local-time boundary drift.
            if getattr(last_alert, "tzinfo", None) is not None:
                last_alert_date = last_alert.astimezone(timezone.utc).date()
            else:
                last_alert_date = last_alert.date()
            today_utc = datetime.now(timezone.utc).date()
            if last_alert_date == today_utc:
                logger.info(
                    "carbon_alert_rate_limited",
                    tenant_id=str(tenant_id),
                    status=alert_status,
                )
                return False

        return True

    async def mark_alert_sent(self, tenant_id: UUID, alert_status: str) -> None:
        """Public API to mark that an alert was sent."""
        await self._mark_alert_sent(tenant_id, alert_status)

    async def _mark_alert_sent(self, tenant_id: UUID, alert_status: str) -> None:
        """Mark that an alert was sent today."""
        from app.models.carbon_settings import CarbonSettings
    
        await self.db.execute(
            update(CarbonSettings)
            .where(CarbonSettings.tenant_id == tenant_id)
            .values(
                last_alert_sent=datetime.now(timezone.utc),
                last_alert_status=alert_status,
            )
        )
        await self.db.flush() # Flush to ensure the update is visible for subsequent operations

    async def _send_slack_alert(
        self,
        tenant_id: UUID,
        budget_status: Dict[str, Any],
        notif_settings: Any,  # NotificationSettings model
    ) -> bool:
        """Helper to send Slack carbon budget alert."""
        is_exceeded = budget_status["alert_status"] == "exceeded"
        is_warning = budget_status["alert_status"] == "warning"

        allowed = True
        if notif_settings:
            if is_exceeded and not notif_settings.alert_on_carbon_budget_exceeded:
                allowed = False
            elif is_warning and not notif_settings.alert_on_carbon_budget_warning:
                allowed = False
            if not notif_settings.slack_enabled:
                allowed = False

        if not allowed:
            logger.info(
                "carbon_slack_alert_skipped_by_settings",
                tenant_id=str(tenant_id),
                alert_status=budget_status["alert_status"],
            )
            return False

        try:
            from app.modules.notifications.domain import get_tenant_slack_service

            slack = await get_tenant_slack_service(self.db, tenant_id)
            if slack:
                status = budget_status["alert_status"]
                severity = "critical" if status == "exceeded" else "warning"

                await slack.send_alert(
                    title=f"Carbon Budget {'Exceeded' if status == 'exceeded' else 'Warning'}!",
                    message=(
                        f"*Monthly Carbon Report*\n\n"
                        f"📊 Usage: *{budget_status['current_usage_kg']:.2f} kg* / "
                        f"{budget_status['budget_kg']:.2f} kg ({budget_status['usage_percent']:.1f}%)\n\n"
                        f"💡 *Recommendations:*\n"
                        + "\n".join(
                            f"• {r}" for r in budget_status["recommendations"][:3]
                        )
                    ),
                    severity=severity,
                )
                logger.info("carbon_slack_alert_sent", tenant_id=str(tenant_id))
                return True
            else:
                logger.info(
                    "carbon_slack_alert_skipped_not_configured",
                    tenant_id=str(tenant_id),
                )
                return False
        except CARBON_SLACK_ALERT_RECOVERABLE_EXCEPTIONS as e:
            logger.error("carbon_slack_alert_failed", error=str(e))
            return False

    async def _send_email_alert(
        self,
        tenant_id: UUID,
        budget_status: Dict[str, Any],
        carbon_settings: Any,  # CarbonSettings model
        notif_settings: Any,  # NotificationSettings model
    ) -> bool:
        """Helper to send email carbon budget alert."""
        if not (carbon_settings and carbon_settings.email_enabled and carbon_settings.email_recipients):
            return False

        is_exceeded = budget_status["alert_status"] == "exceeded"
        is_warning = budget_status["alert_status"] == "warning"

        email_allowed = True
        if notif_settings:
            if is_exceeded and not notif_settings.alert_on_carbon_budget_exceeded:
                email_allowed = False
            elif is_warning and not notif_settings.alert_on_carbon_budget_warning:
                email_allowed = False
        if not email_allowed:
            return False

        from app.shared.core.config import get_settings
        app_settings = get_settings()
        if not hasattr(app_settings, "SMTP_HOST") or not app_settings.SMTP_HOST:
            logger.warning("email_alert_skipped", reason="SMTP not configured")
            return False

        try:
            from app.modules.notifications.domain.email_service import EmailService

            email_service = EmailService(
                smtp_host=app_settings.SMTP_HOST,
                smtp_port=getattr(app_settings, "SMTP_PORT", 587),
                smtp_user=getattr(app_settings, "SMTP_USER", ""),
                smtp_password=getattr(app_settings, "SMTP_PASSWORD", ""),
                from_email=getattr(
                    app_settings, "SMTP_FROM", "alerts@valdrics.com"
                ),
            )

            recipients = [
                e.strip()
                for e in carbon_settings.email_recipients.split(",")
                if e.strip()
            ]
            if not recipients:
                logger.warning("email_alert_skipped", reason="No email recipients configured")
                return False

            await email_service.send_carbon_alert(recipients, budget_status)
            logger.info(
                "carbon_email_alert_sent",
                tenant_id=str(tenant_id),
                recipients=recipients,
            )
            return True
        except CARBON_EMAIL_ALERT_RECOVERABLE_EXCEPTIONS as e:
            logger.error("carbon_email_alert_failed", error=str(e))
            return False

    async def send_carbon_alert(
        self,
        tenant_id: UUID,
        budget_status: Dict[str, Any],
    ) -> bool:
        """
        Send carbon budget alert via configured channels (Slack and/or email).

        Returns True if any alert was sent successfully.
        """
        # Rate limiting check
        if not await self.should_send_alert(tenant_id, budget_status["alert_status"]):
            return False

        # Audit log for budget alert
        from app.shared.core.logging import audit_log_async as audit_log

        await maybe_await(
            audit_log(
                event="carbon_budget_alert",
                user_id="system",
                tenant_id=str(tenant_id),
                details={
                    "status": budget_status["alert_status"],
                    "usage_kg": budget_status["current_usage_kg"],
                    "budget_kg": budget_status["budget_kg"],
                },
                db=self.db,
                isolated=True,
            )
        )

        # Fetch notification settings
        from app.models.notification_settings import NotificationSettings

        notif_result = await self.db.execute(
            select(NotificationSettings).where(
                NotificationSettings.tenant_id == tenant_id
            )
        )
        notif_settings = notif_result.scalar_one_or_none()

        # Fetch carbon settings for email recipients
        from app.models.carbon_settings import CarbonSettings

        carbon_settings_result = await self.db.execute(
            select(CarbonSettings).where(CarbonSettings.tenant_id == tenant_id)
        )
        carbon_settings = carbon_settings_result.scalar_one_or_none()

        sent_slack = await self._send_slack_alert(tenant_id, budget_status, notif_settings)
        sent_email = await self._send_email_alert(tenant_id, budget_status, carbon_settings, notif_settings)

        sent_any = sent_slack or sent_email

        # Mark alert as sent to prevent spam
        if sent_any:
            await self._mark_alert_sent(tenant_id, budget_status["alert_status"])

        await self.db.commit()
        return sent_any
