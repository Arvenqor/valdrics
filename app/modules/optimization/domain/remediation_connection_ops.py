"""Connection validation utilities for remediation workflows."""

from typing import Any

import structlog
from sqlalchemy.exc import SQLAlchemyError

from app.models.remediation import RemediationStatus
from app.modules.governance.domain.security.remediation_policy import RemediationPolicyEngine
from app.modules.optimization.domain.remediation import get_tenant_tier
from app.shared.core.connection_state import is_connection_active
from app.shared.core.connection_queries import get_connection_model
from app.shared.core.exceptions import ResourceNotFoundError, ValdricsException
from app.shared.core.provider import normalize_provider

logger = structlog.get_logger()

REMEDIATION_CONNECTION_SCOPE_RECOVERABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    SQLAlchemyError,
    RuntimeError,
    OSError,
    TimeoutError,
    TypeError,
    KeyError,
    LookupError,
    AttributeError,
)

OPEN_FINDING_REQUEST_STATUSES = (
    RemediationStatus.PENDING,
    RemediationStatus.PENDING_APPROVAL,
    RemediationStatus.APPROVED,
    RemediationStatus.SCHEDULED,
    RemediationStatus.EXECUTING,
)

HISTORY_REQUEST_STATUSES = (
    RemediationStatus.COMPLETED,
    RemediationStatus.FAILED,
    RemediationStatus.REJECTED,
    RemediationStatus.CANCELLED,
)


def invalid_provider_error(provider: str, *, operation: str) -> ValdricsException:
    """Create an error for invalid provider in remediation operation."""
    return ValdricsException(
        message=f"Invalid provider for remediation {operation}.",
        code="invalid_provider",
        status_code=400,
        details={"provider": provider, "operation": operation},
    )


def missing_connection_error(*, provider: str, operation: str) -> ValdricsException:
    """Create an error for missing connection in remediation operation."""
    return ValdricsException(
        message=f"An explicit active connection_id is required for remediation {operation}.",
        code="remediation_connection_required",
        status_code=400,
        details={"provider": provider, "operation": operation},
    )


async def require_scoped_active_connection(
    service: Any,
    *,
    tenant_id: Any,
    provider: str,
    connection_id: Any,
    operation: str,
) -> Any:
    """Validate and fetch an active connection for remediation operations."""

    provider_norm = normalize_provider(provider)
    if not provider_norm:
        raise invalid_provider_error(provider, operation=operation)
    if connection_id is None:
        raise missing_connection_error(provider=provider_norm, operation=operation)

    connection_model = get_connection_model(provider_norm)
    if connection_model is None:
        raise invalid_provider_error(provider_norm, operation=operation)

    try:
        connection = await service.get_by_id(connection_model, connection_id, tenant_id)
    except ResourceNotFoundError as exc:
        raise ResourceNotFoundError(
            f"Connection {connection_id} not found for this tenant.",
            code="remediation_connection_not_found",
            details={"provider": provider_norm, "operation": operation},
        ) from exc
    except REMEDIATION_CONNECTION_SCOPE_RECOVERABLE_EXCEPTIONS as exc:
        logger.warning(
            "remediation_connection_scope_failed",
            tenant_id=str(tenant_id),
            provider=provider_norm,
            connection_id=str(connection_id),
            operation=operation,
            error=str(exc),
        )
        raise ValdricsException(
            message="Failed to validate remediation connection.",
            code="remediation_connection_validation_failed",
            status_code=500,
            details={
                "provider": provider_norm,
                "connection_id": str(connection_id),
                "operation": operation,
            },
        ) from exc

    if not is_connection_active(connection):
        raise ValdricsException(
            message="Remediation requires an active verified connection.",
            code="remediation_connection_inactive",
            status_code=400,
            details={
                "provider": provider_norm,
                "connection_id": str(connection_id),
                "operation": operation,
            },
        )

    return connection


async def preview_policy_for_request(
    service: Any,
    request: Any,
    tenant_id: Any,
) -> dict[str, Any]:
    """Preview policy evaluation for an existing remediation request."""

    provider = normalize_provider(getattr(request, "provider", None))
    connection_id = getattr(request, "connection_id", None)
    if provider:
        await service._apply_system_policy_context(
            request,
            tenant_id=tenant_id,
            provider=provider,
            connection_id=connection_id,
        )

    tier = await get_tenant_tier(tenant_id, service.db)
    policy_config, _ = await service._build_policy_config(tenant_id)
    evaluation = RemediationPolicyEngine().evaluate(
        request, policy_config
    )
    return {
        "decision": evaluation.decision.value,
        "summary": evaluation.summary,
        "rule_hits": [hit.to_dict() for hit in evaluation.rule_hits],
        "tier": tier.value,
        "config": {
            "enabled": policy_config.enabled,
            "block_production_destructive": policy_config.block_production_destructive,
            "require_gpu_override": policy_config.require_gpu_override,
            "low_confidence_warn_threshold": float(
                policy_config.low_confidence_warn_threshold
            ),
        },
    }