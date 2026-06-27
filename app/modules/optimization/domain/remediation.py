"""
Remediation Service - Approval Workflow for Zombie Resource Cleanup

Manages the remediation approval workflow:
1. create_request() - User requests remediation
2. list_pending() - Reviewer sees pending requests
3. approve() / reject() - Reviewer takes action
4. execute() - System executes approved requests
"""

import inspect
from typing import Any

import aioboto3
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.remediation import (
    RemediationAction,
    RemediationRequest,
)
from app.models.remediation_settings import RemediationSettings
from app.shared.core.aws_credentials import map_aws_credentials
from app.modules.governance.domain.security.audit_log import AuditLogger
from app.shared.core.safety_service import SafetyGuardrailService
from app.modules.optimization.domain.actions.factory import RemediationActionFactory
from app.shared.core.config import get_settings
from app.shared.core.connection_queries import get_connection_model
from app.shared.core.connection_state import resolve_connection_profile, resolve_connection_region
from app.modules.governance.domain.security.audit_log import AuditEventType
from app.shared.core.pricing import PricingTier
from app.shared.core.service import BaseService

logger = structlog.get_logger()


async def get_tenant_tier(tenant_id: Any, db: AsyncSession) -> PricingTier:
    """
    Resolve tenant tier via pricing module.

    Keeping this wrapper local ensures a single stable patch point for tests and
    service-layer callers, while still delegating to canonical pricing logic.
    """
    from app.shared.core.pricing import get_tenant_tier as resolve_tenant_tier

    return await resolve_tenant_tier(tenant_id, db)


class RemediationService(BaseService):
    """
    Manages the remediation approval workflow.

    Workflow:
    1. create_request() - User requests remediation
    2. list_pending() - Reviewer sees pending requests
    3. approve() / reject() - Reviewer takes action
    4. execute() - System executes approved requests
    """

    _SYSTEM_POLICY_CONTEXT_KEY = "_system_policy_context"

    def __init__(
        self,
        db: AsyncSession,
        region: str = "global",
        credentials: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(db)
        self.region = region
        self.credentials = credentials
        self.session = aioboto3.Session()
        self._remediation_settings_cache: dict[Any, RemediationSettings | None] = {}

    async def _get_client(self, service_name: str) -> Any:
        """Helper to get aioboto3 client with optional credentials and endpoint override."""
        settings = get_settings()

        kwargs = {"region_name": self.region}

        if settings.AWS_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

        if self.credentials:
            kwargs.update(map_aws_credentials(self.credentials))

        return self.session.client(service_name, **kwargs)

    @staticmethod
    async def _scalar_one_or_none(result: Any) -> Any:
        """
        Safe scalar extractor for SQLAlchemy results and async test doubles.

        Production SQLAlchemy result objects expose a synchronous
        `scalar_one_or_none()`, while AsyncMock-heavy tests can return awaitables.
        """
        extractor = getattr(result, "scalar_one_or_none", None)
        if not callable(extractor):
            return None
        value = extractor()
        if inspect.isawaitable(value):
            return await value
        return value

    async def _resolve_aws_region_hint(
        self,
        *,
        tenant_id: Any = None,
        connection_id: Any = None,
        connection: Any = None,
    ) -> str:
        from app.modules.optimization.domain.remediation_context import (
            resolve_aws_region_hint,
        )

        return await resolve_aws_region_hint(
            self,
            tenant_id=tenant_id,
            connection_id=connection_id,
            connection=connection,
        )

    async def _get_remediation_settings(
        self, tenant_id: Any
    ) -> RemediationSettings | None:
        from app.modules.optimization.domain.remediation_context import (
            get_remediation_settings,
        )

        return await get_remediation_settings(self, tenant_id)

    async def _build_policy_config(
        self, tenant_id: Any
    ) -> tuple[Any, RemediationSettings | None]:
        from app.modules.optimization.domain.remediation_context import (
            build_policy_config,
        )

        return await build_policy_config(self, tenant_id)

    async def _build_system_policy_context(
        self,
        *,
        tenant_id: Any,
        provider: str,
        connection_id: Any,
    ) -> dict[str, Any]:
        from app.modules.optimization.domain.remediation_context import (
            build_system_policy_context,
        )

        return await build_system_policy_context(
            self,
            tenant_id=tenant_id,
            provider=provider,
            connection_id=connection_id,
        )

    def _sanitize_action_parameters(
        self,
        parameters: dict[str, Any] | None,
        *,
        system_policy_context: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        safe_parameters: dict[str, Any] = (
            dict(parameters) if isinstance(parameters, dict) else {}
        )
        safe_parameters.pop(self._SYSTEM_POLICY_CONTEXT_KEY, None)

        if system_policy_context:
            safe_parameters[self._SYSTEM_POLICY_CONTEXT_KEY] = dict(
                system_policy_context
            )

        return safe_parameters or None

    def _strip_system_policy_context(
        self, parameters: dict[str, Any] | None
    ) -> dict[str, Any]:
        safe_parameters: dict[str, Any] = (
            dict(parameters) if isinstance(parameters, dict) else {}
        )
        safe_parameters.pop(self._SYSTEM_POLICY_CONTEXT_KEY, None)
        return safe_parameters

    async def _apply_system_policy_context(
        self,
        request: RemediationRequest,
        *,
        tenant_id: Any,
        provider: str,
        connection_id: Any,
    ) -> dict[str, Any]:
        system_context = await self._build_system_policy_context(
            tenant_id=tenant_id,
            provider=provider,
            connection_id=connection_id,
        )
        request.action_parameters = self._sanitize_action_parameters(
            getattr(request, "action_parameters", None),
            system_policy_context=system_context,
        )
        return system_context

    async def _resolve_credentials(self, request: RemediationRequest) -> dict[str, Any]:
        """Resolve provider credentials from the tenant connection bound to the request."""
        from app.modules.optimization.domain.remediation_credentials import (
            resolve_connection_credentials,
        )

        return await resolve_connection_credentials(self, request)

    async def preview_policy(
        self, request: RemediationRequest, tenant_id: Any
    ) -> dict[str, Any]:
        from app.modules.optimization.domain.remediation_workflow import (
            preview_policy_for_request,
        )

        return await preview_policy_for_request(self, request, tenant_id)

    async def preview_policy_input(
        self,
        *,
        tenant_id: Any,
        user_id: Any,
        resource_id: str,
        resource_type: str,
        action: RemediationAction,
        provider: str,
        confidence_score: float | None = None,
        explainability_notes: str | None = None,
        review_notes: str | None = None,
        parameters: dict[str, Any] | None = None,
        connection_id: Any = None,
    ) -> dict[str, Any]:
        from app.modules.optimization.domain.remediation_workflow import (
            preview_policy_input_payload,
        )

        return await preview_policy_input_payload(
            self,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action=action,
            provider=provider,
            confidence_score=confidence_score,
            explainability_notes=explainability_notes,
            review_notes=review_notes,
            parameters=parameters,
            connection_id=connection_id,
        )

    async def preview_policy_for_finding(
        self,
        *,
        tenant_id: Any,
        user_id: Any,
        finding_id: Any,
        action: RemediationAction,
        review_notes: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from app.modules.optimization.domain.remediation_workflow import (
            preview_policy_for_finding_payload,
        )

        return await preview_policy_for_finding_payload(
            self,
            tenant_id=tenant_id,
            user_id=user_id,
            finding_id=finding_id,
            action=action,
            review_notes=review_notes,
            parameters=parameters,
        )

    async def create_request(
        self,
        tenant_id: Any,
        user_id: Any,
        resource_id: str,
        resource_type: str,
        action: RemediationAction,
        estimated_savings: float,
        provider: str,
        create_backup: bool = False,
        backup_retention_days: int = 30,
        backup_cost_estimate: float = 0,
        confidence_score: float | None = None,
        explainability_notes: str | None = None,
        connection_id: Any = None,
        parameters: dict[str, Any] | None = None,
    ) -> RemediationRequest:
        from app.modules.optimization.domain.remediation_workflow import (
            create_remediation_request,
        )

        return await create_remediation_request(
            self,
            tenant_id=tenant_id,
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            action=action,
            estimated_savings=estimated_savings,
            provider=provider,
            create_backup=create_backup,
            backup_retention_days=backup_retention_days,
            backup_cost_estimate=backup_cost_estimate,
            confidence_score=confidence_score,
            explainability_notes=explainability_notes,
            connection_id=connection_id,
            parameters=parameters,
        )

    async def create_request_from_finding(
        self,
        *,
        tenant_id: Any,
        user_id: Any,
        finding_id: Any,
        action: RemediationAction,
        create_backup: bool = False,
        backup_retention_days: int = 30,
        backup_cost_estimate: float = 0,
        parameters: dict[str, Any] | None = None,
    ) -> RemediationRequest:
        from app.modules.optimization.domain.remediation_workflow import (
            create_remediation_request_from_finding,
        )

        return await create_remediation_request_from_finding(
            self,
            tenant_id=tenant_id,
            user_id=user_id,
            finding_id=finding_id,
            action=action,
            create_backup=create_backup,
            backup_retention_days=backup_retention_days,
            backup_cost_estimate=backup_cost_estimate,
            parameters=parameters,
        )

    async def list_pending(
        self, tenant_id: Any, limit: int = 50, offset: int = 0
    ) -> list[RemediationRequest]:
        from app.modules.optimization.domain.remediation_workflow import (
            list_pending_requests,
        )

        return await list_pending_requests(
            self,
            tenant_id,
            limit=limit,
            offset=offset,
        )

    async def list_history(
        self,
        tenant_id: Any,
        *,
        status: str = "completed",
        limit: int = 20,
        offset: int = 0,
    ) -> list[RemediationRequest]:
        from app.modules.optimization.domain.remediation_workflow import (
            list_request_history,
        )

        return await list_request_history(
            self,
            tenant_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def approve(
        self,
        request_id: Any,
        tenant_id: Any,
        reviewer_id: Any,
        notes: str | None = None,
        reviewer_role: str | None = None,
    ) -> RemediationRequest:
        from app.modules.optimization.domain.remediation_workflow import (
            approve_request,
        )

        return await approve_request(
            self,
            request_id=request_id,
            tenant_id=tenant_id,
            reviewer_id=reviewer_id,
            notes=notes,
            reviewer_role=reviewer_role,
        )

    async def reject(
        self,
        request_id: Any,
        tenant_id: Any,
        reviewer_id: Any,
        notes: str | None = None,
    ) -> RemediationRequest:
        from app.modules.optimization.domain.remediation_workflow import (
            reject_request,
        )

        return await reject_request(
            self,
            request_id=request_id,
            tenant_id=tenant_id,
            reviewer_id=reviewer_id,
            notes=notes,
        )

    async def execute(
        self, request_id: Any, tenant_id: Any, bypass_grace_period: bool = False
    ) -> RemediationRequest:
        """
        Execute an approved remediation request through the registered action strategy.
        """
        from app.modules.optimization.domain.remediation_execute import (
            execute_remediation_request,
        )

        return await execute_remediation_request(
            self,
            request_id,
            tenant_id,
            bypass_grace_period=bypass_grace_period,
        )

    async def enforce_hard_limit(self, tenant_id: Any) -> list[Any]:
        """
        Enforce hard limits for a tenant.
        1. Checks budget status via LLMBudgetManager.
        2. If HARD_LIMIT is reached:
           - Automatically executes only high-confidence, low-risk pending requests.
           - Uses AUTOPILOT_BYPASS_GRACE_PERIOD setting (default fail-safe is no bypass).
        """
        from app.modules.optimization.domain.remediation_hard_limit import (
            enforce_hard_limit_for_tenant,
        )

        return await enforce_hard_limit_for_tenant(self, tenant_id)

    async def generate_iac_plan(
        self,
        request: RemediationRequest,
        tenant_id: Any,
        *,
        tenant_tier: PricingTier | str | None = None,
    ) -> str:
        """
        Generates a Terraform decommissioning plan for the resource.
        Supports 'state rm' and 'removed' blocks for GitOps workflows.

        Phase 8: Gated by Pro tier.
        """
        from app.modules.optimization.domain.remediation_iac import (
            generate_iac_plan_for_request,
        )

        return await generate_iac_plan_for_request(
            self,
            request,
            tenant_id,
            tenant_tier=tenant_tier,
        )

    @staticmethod
    def _sanitize_tf_identifier(
        provider: str, resource_type: str, resource_id: str
    ) -> str:
        """
        Produce a Terraform-safe identifier with deterministic collision resistance.
        """
        from app.modules.optimization.domain.remediation_iac import sanitize_tf_identifier

        return sanitize_tf_identifier(provider, resource_type, resource_id)

    async def bulk_generate_iac_plan(
        self, requests: list[RemediationRequest], tenant_id: Any
    ) -> str:
        """Generates a combined IaC plan for multiple resources."""
        from app.modules.optimization.domain.remediation_iac import (
            bulk_generate_iac_plan_for_requests,
        )

        return await bulk_generate_iac_plan_for_requests(self, requests, tenant_id)