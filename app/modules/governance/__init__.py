from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["AuditLogger", "AuditEventType", "SchedulerOrchestrator"]


if TYPE_CHECKING:
    from .domain.scheduler import SchedulerOrchestrator
    from .domain.security.audit_log import AuditEventType, AuditLogger


def __getattr__(name: str) -> Any:
    if name in {"AuditLogger", "AuditEventType"}:
        from .domain.security.audit_log import AuditEventType, AuditLogger

        exports = {
            "AuditLogger": AuditLogger,
            "AuditEventType": AuditEventType,
        }
        return exports[name]
    if name == "SchedulerOrchestrator":
        from .domain.scheduler import SchedulerOrchestrator

        return SchedulerOrchestrator
    raise AttributeError(name)
