"""
Remediation Workflow Operations - Backward-Compatible API

This module re-exports functions from focused submodules for backward compatibility.
New code should import directly from:
- remediation_connection_ops.py: connection validation helpers
- remediation_request_ops.py: request lifecycle (create, preview, list, approve, reject)
"""

from app.modules.optimization.domain.remediation_connection_ops import (
    REMEDIATION_CONNECTION_SCOPE_RECOVERABLE_EXCEPTIONS,
    OPEN_FINDING_REQUEST_STATUSES,
    HISTORY_REQUEST_STATUSES,
    invalid_provider_error,
    missing_connection_error,
    require_scoped_active_connection,
    preview_policy_for_request,
)
from app.modules.optimization.domain.remediation_request_ops import (
    preview_policy_input_payload,
    preview_policy_for_finding_payload,
    create_remediation_request,
    create_remediation_request_from_finding,
    list_pending_requests,
    list_request_history,
    approve_request,
    reject_request,
)

__all__ = [
    "preview_policy_for_request",
    "preview_policy_input_payload",
    "preview_policy_for_finding_payload",
    "create_remediation_request",
    "create_remediation_request_from_finding",
    "list_pending_requests",
    "list_request_history",
    "approve_request",
    "reject_request",
    "require_scoped_active_connection",
    "invalid_provider_error",
    "missing_connection_error",
    "REMEDIATION_CONNECTION_SCOPE_RECOVERABLE_EXCEPTIONS",
    "OPEN_FINDING_REQUEST_STATUSES",
    "HISTORY_REQUEST_STATUSES",
]