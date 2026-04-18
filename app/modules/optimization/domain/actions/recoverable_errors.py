from __future__ import annotations

from app.shared.core.exceptions import AdapterError, ExternalAPIError


def remediation_action_recoverable_exceptions() -> tuple[type[Exception], ...]:
    base_exceptions: list[type[Exception]] = [
        ExternalAPIError,
        AdapterError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ]
    try:
        from botocore.exceptions import ClientError
    except ImportError:
        pass
    else:
        base_exceptions.insert(0, ClientError)
    return tuple(base_exceptions)
