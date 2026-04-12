"""
Notification Dispatcher - Unified Event-Driven Notifications

Bridges services (ZombieService, RemediationService) to actual providers (Slack, etc.).
This allows adding new channels (Teams, Discord, Email) without modifying domain logic.
"""

import structlog
from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING
from app.modules.notifications.domain import (
    get_jira_service,
    get_slack_service,
    get_tenant_teams_service,
    get_workflow_dispatchers,
    get_tenant_workflow_dispatchers,
    get_tenant_jira_service,
    get_tenant_slack_service,
)
from app.shared.core.config import get_settings
from app.shared.core.pricing import FeatureFlag, get_tenant_tier, is_feature_enabled

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class NotificationDispatcher:
    """
    Dispatcher responsible for routing alerts to appropriate providers.
    Currently focuses on Slack as the primary channel.
    """

    @staticmethod
    async def _resolve_slack_service(
        tenant_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> Any:
        if tenant_id:
            if db is None:
                logger.warning(
                    "notification_slack_skipped_missing_tenant_db_context",
                    tenant_id=tenant_id,
                )
                return None
            return await get_tenant_slack_service(db, tenant_id)
        return get_slack_service()

    @staticmethod
    async def _tenant_has_feature(
        *,
        tenant_id: str | None,
        db: "AsyncSession | None",
        feature: FeatureFlag,
    ) -> bool:
        if not tenant_id or db is None:
            return False
        tier = await get_tenant_tier(tenant_id, db)
        return bool(is_feature_enabled(tier, feature))

    @staticmethod
    async def _resolve_teams_service(
        tenant_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> Any:
        if not tenant_id:
            return None
        if db is None:
            logger.warning(
                "notification_teams_skipped_missing_tenant_db_context",
                tenant_id=tenant_id,
            )
            return None
        if not await NotificationDispatcher._tenant_has_feature(
            tenant_id=tenant_id,
            db=db,
            feature=FeatureFlag.INCIDENT_INTEGRATIONS,
        ):
            return None
        return await get_tenant_teams_service(db, tenant_id)

    @staticmethod
    async def _attempt_channel(
        *,
        service: Any,
        channel: str,
        method_name: str,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[str]]:
        if service is None:
            return [], []
        ok = await getattr(service, method_name)(*args, **(kwargs or {}))
        attempted = [channel]
        if ok:
            return attempted, attempted
        return attempted, []

    @staticmethod
    def _log_dispatch_outcome(
        *,
        success_event: str,
        failed_event: str,
        skipped_event: str,
        attempted_channels: list[str],
        successful_channels: list[str],
        **context: Any,
    ) -> None:
        if successful_channels:
            logger.info(
                success_event,
                channels=successful_channels,
                attempted_channels=attempted_channels,
                **context,
            )
            return
        if attempted_channels:
            logger.warning(
                failed_event,
                channels=attempted_channels,
                **context,
            )
            return
        logger.warning(skipped_event, **context)

    @staticmethod
    async def send_alert(
        title: str,
        message: str,
        severity: str = "warning",
        tenant_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Sends a generic alert to configured channels."""
        attempted_channels: list[str] = []
        successful_channels: list[str] = []

        slack = await NotificationDispatcher._resolve_slack_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=slack,
            channel="slack",
            method_name="send_alert",
            args=(title, message, severity),
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        teams = await NotificationDispatcher._resolve_teams_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=teams,
            channel="teams",
            method_name="send_alert",
            kwargs={"title": title, "message": message, "severity": severity},
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        NotificationDispatcher._log_dispatch_outcome(
            success_event="notification_dispatched",
            failed_event="notification_dispatch_failed",
            skipped_event="notification_dispatch_skipped_no_channels",
            attempted_channels=attempted_channels,
            successful_channels=successful_channels,
            title=title,
            severity=severity,
            tenant_id=tenant_id,
        )

    @staticmethod
    async def notify_zombies(
        zombies: Dict[str, Any],
        estimated_savings: float = 0.0,
        tenant_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Dispatches zombie resource detection alerts."""
        attempted_channels: list[str] = []
        successful_channels: list[str] = []
        slack = await NotificationDispatcher._resolve_slack_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=slack,
            channel="slack",
            method_name="notify_zombies",
            args=(zombies, estimated_savings),
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        teams = await NotificationDispatcher._resolve_teams_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=teams,
            channel="teams",
            method_name="notify_zombies",
            args=(zombies, estimated_savings),
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        NotificationDispatcher._log_dispatch_outcome(
            success_event="zombie_notification_dispatched",
            failed_event="zombie_notification_failed",
            skipped_event="zombie_notification_skipped_no_channels",
            attempted_channels=attempted_channels,
            successful_channels=successful_channels,
            tenant_id=tenant_id,
            estimated_savings=estimated_savings,
        )

    @staticmethod
    async def notify_budget_alert(
        current_spend: float,
        budget_limit: float,
        percent_used: float,
        tenant_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Dispatches budget threshold alerts."""
        attempted_channels: list[str] = []
        successful_channels: list[str] = []
        slack = await NotificationDispatcher._resolve_slack_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=slack,
            channel="slack",
            method_name="notify_budget_alert",
            args=(current_spend, budget_limit, percent_used),
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        teams = await NotificationDispatcher._resolve_teams_service(
            tenant_id=tenant_id,
            db=db,
        )
        attempted, successful = await NotificationDispatcher._attempt_channel(
            service=teams,
            channel="teams",
            method_name="notify_budget_alert",
            args=(current_spend, budget_limit, percent_used),
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        NotificationDispatcher._log_dispatch_outcome(
            success_event="budget_notification_dispatched",
            failed_event="budget_notification_failed",
            skipped_event="budget_notification_skipped_no_channels",
            attempted_channels=attempted_channels,
            successful_channels=successful_channels,
            tenant_id=tenant_id,
            current_spend=current_spend,
            budget_limit=budget_limit,
            percent_used=percent_used,
        )

    @staticmethod
    async def notify_remediation_completed(
        tenant_id: str,
        resource_id: str,
        action: str,
        savings: float,
        request_id: str | None = None,
        provider: str | None = None,
        notify_workflow: bool = False,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Dispatches remediation completion alerts."""
        title = f"Remediation Successful: {action.title()} {resource_id}"
        message = f"Tenant: {tenant_id}\nResource: {resource_id}\nAction: {action}\nMonthly Savings: ${savings:.2f}"

        await NotificationDispatcher.send_alert(
            title,
            message,
            severity="info",
            tenant_id=tenant_id,
            db=db,
        )
        if notify_workflow:
            await NotificationDispatcher._dispatch_workflow_event(
                event_type="remediation.completed",
                payload={
                    "tenant_id": tenant_id,
                    "request_id": request_id,
                    "resource_id": resource_id,
                    "action": action,
                    "provider": provider,
                    "status": "completed",
                    "monthly_savings_usd": savings,
                    "evidence_links": NotificationDispatcher._build_remediation_evidence_links(
                        request_id=request_id
                    ),
                },
                db=db,
                tenant_id=tenant_id,
            )

    @staticmethod
    def _build_remediation_evidence_links(request_id: str | None) -> dict[str, str]:
        settings = get_settings()
        api_base_url = (settings.WORKFLOW_EVIDENCE_BASE_URL or settings.API_URL).rstrip(
            "/"
        )
        frontend_base_url = (settings.FRONTEND_URL or api_base_url).rstrip("/")
        links = {
            "ops_dashboard": f"{frontend_base_url}/ops",
            "pending_requests_api": f"{api_base_url}/api/v1/zombies/pending",
        }
        if request_id:
            links.update(
                {
                    "policy_preview_api": f"{api_base_url}/api/v1/zombies/policy-preview/{request_id}",
                    "remediation_plan_api": f"{api_base_url}/api/v1/zombies/plan/{request_id}",
                    "approve_api": f"{api_base_url}/api/v1/zombies/approve/{request_id}",
                    "execute_api": f"{api_base_url}/api/v1/zombies/execute/{request_id}",
                }
            )
        return links

    @staticmethod
    async def _dispatch_workflow_event(
        event_type: str,
        payload: dict[str, Any],
        db: "AsyncSession | None" = None,
        tenant_id: str | None = None,
    ) -> tuple[list[str], list[str]]:
        dispatchers: list[Any] = []
        if tenant_id:
            if db is None:
                logger.warning(
                    "workflow_dispatch_skipped_missing_tenant_db_context",
                    event_type=event_type,
                    tenant_id=tenant_id,
                )
                return [], []
            if not await NotificationDispatcher._tenant_has_feature(
                tenant_id=tenant_id,
                db=db,
                feature=FeatureFlag.INCIDENT_INTEGRATIONS,
            ):
                return [], []
            dispatchers = await get_tenant_workflow_dispatchers(db, tenant_id)
            if not dispatchers:
                logger.info(
                    "workflow_dispatch_skipped_no_tenant_dispatchers",
                    event_type=event_type,
                    tenant_id=tenant_id,
                )
                return [], []
        else:
            dispatchers = get_workflow_dispatchers()
        if not dispatchers:
            logger.info(
                "workflow_dispatch_skipped_no_dispatchers", event_type=event_type
            )
            return [], []
        attempted_channels: list[str] = []
        successful_channels: list[str] = []
        for dispatcher in dispatchers:
            channel = f"workflow:{getattr(dispatcher, 'provider', 'unknown')}"
            attempted_channels.append(channel)
            ok = await dispatcher.dispatch(event_type, payload)
            if not ok:
                logger.warning(
                    "workflow_dispatch_failed",
                    event_type=event_type,
                    provider=getattr(dispatcher, "provider", "unknown"),
                    tenant_id=payload.get("tenant_id"),
                    request_id=payload.get("request_id"),
                )
                continue
            successful_channels.append(channel)
            logger.info(
                "workflow_dispatch_succeeded",
                event_type=event_type,
                provider=getattr(dispatcher, "provider", "unknown"),
                tenant_id=payload.get("tenant_id"),
                request_id=payload.get("request_id"),
            )
        return attempted_channels, successful_channels

    @staticmethod
    async def notify_policy_event(
        tenant_id: str,
        decision: str,
        summary: str,
        resource_id: str,
        action: str,
        notify_slack: bool = True,
        notify_jira: bool = False,
        notify_teams: bool = False,
        notify_workflow: bool = False,
        request_id: str | None = None,
        db: "AsyncSession | None" = None,
    ) -> None:
        """Dispatches remediation policy violation/escalation alerts."""
        title = f"Policy {decision.title()}: {action}"
        message = (
            f"Tenant: {tenant_id}\n"
            f"Resource: {resource_id}\n"
            f"Action: {action}\n"
            f"Policy Decision: {decision}\n"
            f"Summary: {summary}"
        )
        severity = "critical" if decision in {"block", "escalate"} else "warning"
        attempted_channels: list[str] = []
        successful_channels: list[str] = []
        if notify_slack:
            slack = None
            if db is not None:
                slack = await get_tenant_slack_service(db, tenant_id)
            else:
                slack = get_slack_service()

            if slack:
                attempted, successful = await NotificationDispatcher._attempt_channel(
                    service=slack,
                    channel="slack",
                    method_name="send_alert",
                    args=(title, message, severity),
                )
                attempted_channels.extend(attempted)
                successful_channels.extend(successful)
            else:
                logger.warning(
                    "policy_notification_slack_not_configured",
                    tenant_id=tenant_id,
                    decision=decision,
                )

        if notify_teams:
            teams = None
            if db is not None:
                teams = await get_tenant_teams_service(db, tenant_id)
            if teams:
                attempted, successful = await NotificationDispatcher._attempt_channel(
                    service=teams,
                    channel="teams",
                    method_name="send_alert",
                    kwargs={
                        "title": title,
                        "message": message,
                        "severity": severity,
                        "actions": NotificationDispatcher._build_remediation_evidence_links(
                            request_id=request_id
                        ),
                    },
                )
                attempted_channels.extend(attempted)
                successful_channels.extend(successful)
            else:
                logger.warning(
                    "policy_notification_teams_not_configured",
                    tenant_id=tenant_id,
                    decision=decision,
                )

        if notify_jira:
            jira = None
            if db is not None:
                jira = await get_tenant_jira_service(db, tenant_id)
            else:
                jira = get_jira_service()
            if jira:
                attempted, successful = await NotificationDispatcher._attempt_channel(
                    service=jira,
                    channel="jira",
                    method_name="create_policy_issue",
                    kwargs={
                        "tenant_id": tenant_id,
                        "decision": decision,
                        "policy_summary": summary,
                        "resource_id": resource_id,
                        "action": action,
                        "severity": severity,
                    },
                )
                attempted_channels.extend(attempted)
                successful_channels.extend(successful)
            else:
                logger.warning(
                    "policy_notification_jira_not_configured",
                    tenant_id=tenant_id,
                    decision=decision,
                )
        if notify_workflow:
            attempted, successful = await NotificationDispatcher._dispatch_workflow_event(
                event_type=f"policy.{decision}",
                payload={
                    "tenant_id": tenant_id,
                    "request_id": request_id,
                    "decision": decision,
                    "summary": summary,
                    "resource_id": resource_id,
                    "action": action,
                    "severity": severity,
                    "evidence_links": NotificationDispatcher._build_remediation_evidence_links(
                        request_id=request_id
                    ),
                },
                db=db,
                tenant_id=tenant_id,
            )
            attempted_channels.extend(attempted)
            successful_channels.extend(successful)

        NotificationDispatcher._log_dispatch_outcome(
            success_event="policy_notification_dispatched",
            failed_event="policy_notification_failed",
            skipped_event="policy_notification_skipped_no_channels",
            attempted_channels=attempted_channels,
            successful_channels=successful_channels,
            tenant_id=tenant_id,
            decision=decision,
            notify_slack=notify_slack,
            notify_jira=notify_jira,
            notify_teams=notify_teams,
            notify_workflow=notify_workflow,
        )

    @staticmethod
    async def notify_license_reclamation(
        tenant_id: str,
        user_email: str,
        last_active_at: datetime | None,
        savings: float,
        grace_period_days: int,
        request_id: str,
        db: "AsyncSession",
    ) -> None:
        """
        Notify that a license seat has been flagged for reclamation due to inactivity.
        """
        title = "🛡️ License Reclamation Warning"
        inactive_phrase = (
            f"inactive since {last_active_at.strftime('%Y-%m-%d')}"
            if last_active_at is not None
            else "inactive with no recorded sign-in activity"
        )
        message = (
            f"User *{user_email}* has been {inactive_phrase}.\n"
            f"This seat is scheduled for reclamation in *{grace_period_days} days* to save *${savings:.2f}/mo*.\n"
            f"If this is an error, please cancel the scheduled action in the dashboard."
        )
        
        # 1. Notify via Slack
        attempted_channels: list[str] = []
        successful_channels: list[str] = []

        slack = await NotificationDispatcher._resolve_slack_service(
            tenant_id=tenant_id,
            db=db,
        )
        if slack:
            attempted, successful = await NotificationDispatcher._attempt_channel(
                service=slack,
                channel="slack",
                method_name="send_alert",
                kwargs={"title": title, "message": message, "severity": "warning"},
            )
            attempted_channels.extend(attempted)
            successful_channels.extend(successful)
            
        # 2. Notify via Teams
        teams = await NotificationDispatcher._resolve_teams_service(
            tenant_id=tenant_id,
            db=db,
        )
        if teams:
            attempted, successful = await NotificationDispatcher._attempt_channel(
                service=teams,
                channel="teams",
                method_name="send_alert",
                kwargs={"title": title, "message": message, "severity": "warning"},
            )
            attempted_channels.extend(attempted)
            successful_channels.extend(successful)

        # 3. Notify via Workflow (if configured)
        attempted, successful = await NotificationDispatcher._dispatch_workflow_event(
            event_type="license.reclamation_flagged",
            payload={
                "tenant_id": tenant_id,
                "request_id": request_id,
                "user_email": user_email,
                "last_active_at": last_active_at.isoformat() if last_active_at else None,
                "estimated_monthly_savings_usd": savings,
                "grace_period_days": grace_period_days,
                "evidence_links": NotificationDispatcher._build_remediation_evidence_links(
                    request_id
                ),
            },
            db=db,
            tenant_id=tenant_id,
        )
        attempted_channels.extend(attempted)
        successful_channels.extend(successful)

        NotificationDispatcher._log_dispatch_outcome(
            success_event="license_reclamation_notification_dispatched",
            failed_event="license_reclamation_notification_failed",
            skipped_event="license_reclamation_notification_skipped_no_channels",
            attempted_channels=attempted_channels,
            successful_channels=successful_channels,
            tenant_id=tenant_id,
            user_email=user_email,
        )
