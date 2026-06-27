"""Recoverable exceptions for remediation actions."""

from app.shared.core.exceptions import ValdricsException


def remediation_action_recoverable_exceptions() -> tuple[type[Exception], ...]:
    """Return tuple of exceptions that should not crash remediation actions."""
    base_exceptions: list[type[Exception]] = [
        ValdricsException,
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