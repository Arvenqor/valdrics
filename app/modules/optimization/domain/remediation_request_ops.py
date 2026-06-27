"""Request lifecycle operations: create, preview, list, approve, reject."""

from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

import structlog
from sqlalchemy import case, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.models.remediation import (
    RemediationAction,
    RemediationRequest,
    RemediationStatus,
)
from app.modules.optimization.domain.findings import (
    build_request_finding_snapshot,
    get_open_finding_for_tenant,
)
from app.modules.optimization.domain.remediation_connection_ops import (
    invalid_provider_error,
    require_scoped_active_connection,
)
from app.shared.core.exceptions import ResourceNotFoundError, ValdricsException

logger = structlog.get_logger()

_OPEN_FINDING_REQUEST_STATUSES = (
    RemediationStatus.PENDING,
    RemediationStatus.PENDING_APPROVAL,
    RemediationStatus.APPROVED,
    RemediationStatus.SCHEDULED,
    RemediationStatus.EXECUTING,
)
_HISTORY_REQUEST_STATUSES = (
    RemediationStatus.COMPLETED,
    RemediationStatus.FAILED,
    RemediationStatus.REJECTED,
    RemediationStatus.CANCELLED,
)


async def preview_policy_input_payload(
    service: Any,
    *,
    tenant_id: UUID,
    user_id: UUID,
    resource_id: str,
    resource_type: str,
    action: RemediationAction,
    provider: str,
    confidence_score: float | None = None,
    explainability_notes: str | None = None,
    review_notes: str | None = None,
    parameters: dict[str, Any] | None = None,
    connection_id: UUID | None = None,
) -> dict[str, Any]:
    """Evaluate policy for an in-memory remediation payload (dry-run)."""
    from app.shared.core.provider import normalize_provider

    provider_norm = normalize_provider(provider)
    if not provider_norm:
        raise invalid_provider_error(provider, operation="policy preview")
    scoped_connection = await require_scoped_active_connection(
        service,
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=connection_id,
        operation="policy preview",
    )
    preview_region = (
        await service._resolve_aws_region_hint(
            tenant_id=tenant_id,
            connection_id=connection_id,
            connection=scoped_connection,
        )
        if provider_norm == "aws"
        else "global"
    )
    system_context = await service._build_system_policy_context(
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=connection_id,
    )
    synthetic_request = RemediationRequest(
        id=uuid4(),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=resource_type,
        provider=provider_norm,
        connection_id=connection_id,
        region=preview_region,
        action=action,
        status=RemediationStatus.PENDING,
        estimated_monthly_savings=Decimal("0"),
        confidence_score=(
            Decimal(str(confidence_score)) if confidence_score is not None else None
        ),
        explainability_notes=explainability_notes,
        requested_by_user_id=user_id,
        review_notes=review_notes,
        action_parameters=service._sanitize_action_parameters(
            parameters, system_policy_context=system_context
        ),
    )
    return cast(
        dict[str, Any],
        await service.preview_policy(synthetic_request, tenant_id),
    )


async def preview_policy_for_finding_payload(
    service: Any,
    *,
    tenant_id: UUID,
    user_id: UUID,
    finding_id: UUID,
    action: RemediationAction,
    review_notes: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate policy for a finding-based remediation payload (dry-run)."""
    from app.shared.core.provider import normalize_provider

    finding = await get_open_finding_for_tenant(
        service,
        tenant_id=tenant_id,
        finding_id=finding_id,
    )
    provider_norm = normalize_provider(finding.provider)
    if not provider_norm:
        raise invalid_provider_error(str(finding.provider or ""), operation="policy preview")
    await require_scoped_active_connection(
        service,
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=finding.connection_id,
        operation="policy preview",
    )

    system_context = await service._build_system_policy_context(
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=finding.connection_id,
    )
    synthetic_request = RemediationRequest(
        id=uuid4(),
        tenant_id=tenant_id,
        resource_id=str(finding.resource_id or ""),
        resource_type=str(finding.resource_type or ""),
        provider=provider_norm,
        connection_id=finding.connection_id,
        finding_id=finding.id,
        finding_snapshot=build_request_finding_snapshot(finding),
        region=str(finding.region or "global"),
        action=action,
        status=RemediationStatus.PENDING,
        estimated_monthly_savings=finding.estimated_monthly_savings or Decimal("0"),
        confidence_score=finding.confidence_score,
        explainability_notes=finding.explainability_notes,
        requested_by_user_id=user_id,
        review_notes=review_notes,
        action_parameters=service._sanitize_action_parameters(
            parameters, system_policy_context=system_context
        ),
    )
    return cast(
        dict[str, Any],
        await service.preview_policy(synthetic_request, tenant_id),
    )


async def create_remediation_request(
    service: Any,
    *,
    tenant_id: UUID,
    user_id: UUID,
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
    connection_id: UUID | None = None,
    parameters: dict[str, Any] | None = None,
) -> RemediationRequest:
    """Create a new remediation request (pending approval)."""
    from app.shared.core.provider import normalize_provider

    provider_norm = normalize_provider(provider)
    if not provider_norm:
        raise invalid_provider_error(provider, operation="request creation")
    scoped_connection = await require_scoped_active_connection(
        service,
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=connection_id,
        operation="request creation",
    )

    request_region = (
        await service._resolve_aws_region_hint(
            tenant_id=tenant_id,
            connection_id=connection_id,
            connection=scoped_connection,
        )
        if provider_norm == "aws"
        else "global"
    )

    system_context = await service._build_system_policy_context(
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=connection_id,
    )

    request = RemediationRequest(
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=resource_type,
        region=request_region,
        action=action,
        status=RemediationStatus.PENDING,
        estimated_monthly_savings=Decimal(str(estimated_savings)),
        confidence_score=(
            Decimal(str(confidence_score)) if confidence_score is not None else None
        ),
        explainability_notes=explainability_notes,
        create_backup=create_backup,
        backup_retention_days=backup_retention_days,
        backup_cost_estimate=Decimal(str(backup_cost_estimate))
        if backup_cost_estimate
        else None,
        requested_by_user_id=user_id,
        provider=provider_norm,
        connection_id=connection_id,
        action_parameters=service._sanitize_action_parameters(
            parameters, system_policy_context=system_context
        ),
    )

    service.db.add(request)
    await service.db.commit()
    await service.db.refresh(request)

    logger.info(
        "remediation_request_created",
        request_id=str(request.id),
        resource=resource_id,
        action=action.value,
        backup=create_backup,
    )

    return request


async def create_remediation_request_from_finding(
    service: Any,
    *,
    tenant_id: UUID,
    user_id: UUID,
    finding_id: UUID,
    action: RemediationAction,
    create_backup: bool = False,
    backup_retention_days: int = 30,
    backup_cost_estimate: float = 0,
    parameters: dict[str, Any] | None = None,
) -> RemediationRequest:
    """Create a remediation request bound to a persisted actionable finding."""
    from app.shared.core.provider import normalize_provider

    finding = await get_open_finding_for_tenant(
        service,
        tenant_id=tenant_id,
        finding_id=finding_id,
    )
    provider_norm = normalize_provider(finding.provider)
    if not provider_norm:
        raise invalid_provider_error(
            str(finding.provider or ""),
            operation="request creation",
        )
    await require_scoped_active_connection(
        service,
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=finding.connection_id,
        operation="request creation",
    )

    system_context = await service._build_system_policy_context(
        tenant_id=tenant_id,
        provider=provider_norm,
        connection_id=finding.connection_id,
    )
    existing_request = await service.db.scalar(
        select(RemediationRequest).where(
            RemediationRequest.tenant_id == tenant_id,
            RemediationRequest.finding_id == finding.id,
            RemediationRequest.action == action,
            RemediationRequest.status.in_(_OPEN_FINDING_REQUEST_STATUSES),
        )
    )
    if isinstance(existing_request, RemediationRequest):
        raise ValdricsException(
            message="An open remediation request already exists for this finding.",
            code="remediation_request_duplicate_open_finding",
            status_code=409,
            details={
                "request_id": str(existing_request.id),
                "finding_id": str(finding.id),
                "action": action.value,
            },
        )

    request = RemediationRequest(
        tenant_id=tenant_id,
        resource_id=str(finding.resource_id or ""),
        resource_type=str(finding.resource_type or ""),
        provider=provider_norm,
        connection_id=finding.connection_id,
        finding_id=finding.id,
        finding_snapshot=build_request_finding_snapshot(finding),
        region=str(finding.region or "global"),
        action=action,
        status=RemediationStatus.PENDING,
        estimated_monthly_savings=finding.estimated_monthly_savings or Decimal("0"),
        confidence_score=finding.confidence_score,
        explainability_notes=finding.explainability_notes,
        create_backup=create_backup,
        backup_retention_days=backup_retention_days,
        backup_cost_estimate=Decimal(str(backup_cost_estimate))
        if backup_cost_estimate
        else None,
        requested_by_user_id=user_id,
        action_parameters=service._sanitize_action_parameters(
            parameters, system_policy_context=system_context
        ),
    )

    service.db.add(request)
    try:
        await service.db.commit()
    except IntegrityError as exc:
        await service.db.rollback()
        raise ValdricsException(
            message="An open remediation request already exists for this finding.",
            code="remediation_request_duplicate_open_finding",
            status_code=409,
            details={
                "finding_id": str(finding.id),
                "action": action.value,
            },
        ) from exc
    await service.db.refresh(request)

    logger.info(
        "remediation_request_created_from_finding",
        request_id=str(request.id),
        finding_id=str(finding.id),
        resource=str(request.resource_id or ""),
        action=action.value,
    )

    return request


async def list_pending_requests(
    service: Any,
    tenant_id: UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[RemediationRequest]:
    """List open remediation requests for a tenant (actionable queue)."""
    max_page_size = 200
    bounded_limit = min(limit, max_page_size)
    stmt = (
        service._scoped_query(RemediationRequest, tenant_id)
        .options(selectinload(RemediationRequest.finding))
        .where(
            RemediationRequest.status.in_(_OPEN_FINDING_REQUEST_STATUSES)
        )
        .order_by(RemediationRequest.created_at.desc())
        .offset(offset)
        .limit(bounded_limit)
    )
    result = await service.db.execute(stmt)
    return list(result.scalars().all())


async def list_request_history(
    service: Any,
    tenant_id: UUID,
    *,
    status: str = "completed",
    limit: int = 20,
    offset: int = 0,
) -> list[RemediationRequest]:
    """List recent completed/failed/rejected/cancelled remediation requests."""
    normalized_status = str(status or "completed").strip().lower()
    history_statuses_by_filter: dict[str, tuple[RemediationStatus, ...]] = {
        "completed": (RemediationStatus.COMPLETED,),
        "failed": (RemediationStatus.FAILED,),
        "rejected": (RemediationStatus.REJECTED,),
        "cancelled": (RemediationStatus.CANCELLED,),
        "all": _HISTORY_REQUEST_STATUSES,
    }
    selected_statuses = history_statuses_by_filter.get(normalized_status)
    if selected_statuses is None:
        supported = ", ".join(sorted(history_statuses_by_filter))
        raise ValueError(
            f"Unsupported remediation history status '{status}'. Use one of: {supported}"
        )

    max_page_size = 200
    bounded_limit = min(limit, max_page_size)
    executed_at_missing = case((RemediationRequest.executed_at.is_(None), 1), else_=0)
    stmt = (
        service._scoped_query(RemediationRequest, tenant_id)
        .options(selectinload(RemediationRequest.finding))
        .where(RemediationRequest.status.in_(selected_statuses))
        .order_by(
            executed_at_missing.asc(),
            RemediationRequest.executed_at.desc(),
            RemediationRequest.updated_at.desc(),
            RemediationRequest.created_at.desc(),
        )
        .offset(offset)
        .limit(bounded_limit)
    )
    result = await service.db.execute(stmt)
    return list(result.scalars().all())


async def approve_request(
    service: Any,
    *,
    request_id: UUID,
    tenant_id: UUID,
    reviewer_id: UUID,
    notes: str | None = None,
    reviewer_role: str | None = None,
) -> RemediationRequest:
    """Approve a remediation request. Does NOT execute yet - that's a separate step."""
    result = await service.db.execute(
        select(RemediationRequest)
        .where(RemediationRequest.id == request_id)
        .where(RemediationRequest.tenant_id == tenant_id)
        .with_for_update()
    )
    request_value = await service._scalar_one_or_none(result)

    if request_value is None:
        raise ResourceNotFoundError(
            message=f"Request {request_id} not found",
            code="request_not_found",
        )
    request = cast(RemediationRequest, request_value)

    if request.status not in {
        RemediationStatus.PENDING,
        RemediationStatus.PENDING_APPROVAL,
    }:
        raise ValueError(f"Request is {request.status.value}, not pending approval")

    # Handle escalation requirement
    if getattr(request, "escalation_required", False) is True:
        normalized_role = (reviewer_role or "").strip().lower()
        settings = await service._get_remediation_settings(tenant_id)
        required_role = (
            (
                getattr(settings, "policy_escalation_required_role", "owner")
                if settings
                else "owner"
            )
            or "owner"
        ).strip().lower()

        if required_role not in {"owner", "admin"}:
            required_role = "owner"

        role_allowed = normalized_role == "owner" or normalized_role == required_role
        if not role_allowed:
            raise ValueError(
                f"Escalated remediation requests require {required_role} approval."
            )

        marker = "gpu-approved"
        if notes:
            if marker not in notes.lower():
                notes = f"{notes}\n[{marker}]"
        else:
            notes = f"Owner escalation approval [{marker}]"

        request.escalation_required = False
        request.escalation_reason = None

    request.status = RemediationStatus.APPROVED
    request.reviewed_by_user_id = reviewer_id
    request.review_notes = notes
    request.escalation_required = False
    request.escalation_reason = None

    await service.db.commit()
    await service.db.refresh(request)

    logger.info(
        "remediation_approved",
        request_id=str(request_id),
        reviewer=str(reviewer_id),
    )

    return request


async def reject_request(
    service: Any,
    *,
    request_id: UUID,
    tenant_id: UUID,
    reviewer_id: UUID,
    notes: str | None = None,
) -> RemediationRequest:
    """Reject a remediation request."""
    result = await service.db.execute(
        select(RemediationRequest)
        .where(RemediationRequest.id == request_id)
        .where(RemediationRequest.tenant_id == tenant_id)
        .with_for_update()
    )
    request_value = await service._scalar_one_or_none(result)

    if request_value is None:
        raise ResourceNotFoundError(
            message=f"Request {request_id} not found",
            code="request_not_found",
        )
    request = cast(RemediationRequest, request_value)

    if request.status not in {
        RemediationStatus.PENDING,
        RemediationStatus.PENDING_APPROVAL,
    }:
        raise ValueError(f"Request is {request.status.value}, not pending approval")

    request.status = RemediationStatus.REJECTED
    request.reviewed_by_user_id = reviewer_id
    request.review_notes = notes
    request.escalation_required = False
    request.escalation_reason = None

    await service.db.commit()
    await service.db.refresh(request)

    logger.info(
        "remediation_rejected",
        request_id=str(request_id),
        reviewer=str(reviewer_id),
    )

    return request