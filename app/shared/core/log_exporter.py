"""Structured log mirroring to OTLP collectors."""

from __future__ import annotations

import json
import logging
from threading import Lock
from typing import Any

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

OTEL_LOG_EXPORT_RECOVERABLE_EXCEPTIONS = (
    RuntimeError,
    TypeError,
    ValueError,
    OSError,
)

_OTEL_LOGGER_NAME = "valdrics.otlp"
_otlp_lock = Lock()
_otlp_logger_provider: LoggerProvider | None = None
_otlp_logger_config: tuple[str, bool, str] | None = None


def _desired_otlp_logger_config(settings: Any) -> tuple[str, bool, str] | None:
    endpoint = str(getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "") or "").strip()
    if bool(getattr(settings, "TESTING", False)):
        return None
    if not bool(getattr(settings, "OTEL_LOGS_EXPORT_ENABLED", True)):
        return None
    if not endpoint:
        return None
    insecure = bool(getattr(settings, "OTEL_EXPORTER_OTLP_INSECURE", False))
    environment = str(getattr(settings, "ENVIRONMENT", "") or "development")
    return (endpoint, insecure, environment)


def _reset_otlp_logger(logger: logging.Logger) -> None:
    global _otlp_logger_provider, _otlp_logger_config

    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        close = getattr(handler, "close", None)
        if callable(close):
            close()

    provider = _otlp_logger_provider
    _otlp_logger_provider = None
    _otlp_logger_config = None

    if provider is None:
        return

    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()


def configure_otlp_log_export(settings: Any) -> logging.Logger | None:
    """Configure a dedicated stdlib logger that exports logs to OTLP."""
    global _otlp_logger_provider, _otlp_logger_config

    logger = logging.getLogger(_OTEL_LOGGER_NAME)
    desired_config = _desired_otlp_logger_config(settings)

    with _otlp_lock:
        if desired_config is None:
            if logger.handlers or _otlp_logger_provider is not None:
                _reset_otlp_logger(logger)
            return None

        if (
            _otlp_logger_config == desired_config
            and _otlp_logger_provider is not None
            and logger.handlers
        ):
            return logger

        if logger.handlers or _otlp_logger_provider is not None:
            _reset_otlp_logger(logger)

        endpoint, insecure, environment = desired_config
        resource = Resource(
            attributes={
                ResourceAttributes.SERVICE_NAME: "valdrics-api",
                "env": environment,
            }
        )
        _otlp_logger_provider = LoggerProvider(resource=resource)
        exporter = OTLPLogExporter(endpoint=endpoint, insecure=insecure)
        _otlp_logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(exporter)
        )
        handler = LoggingHandler(
            level=logging.INFO, logger_provider=_otlp_logger_provider
        )
        logger.handlers.clear()
        logger.setLevel(logging.INFO)
        logger.propagate = False
        logger.addHandler(handler)
        _otlp_logger_config = desired_config
        return logger


def mirror_event_to_otel(
    _logger: Any, _method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Mirror the rendered structured event to OTLP without affecting stderr output."""
    otlp_logger = logging.getLogger(_OTEL_LOGGER_NAME)
    if not otlp_logger.handlers:
        return event_dict

    level_name = str(event_dict.get("level", "info") or "info").strip().lower()
    level = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }.get(level_name, logging.INFO)

    try:
        otlp_logger.log(
            level,
            json.dumps(event_dict, default=str, separators=(",", ":"), sort_keys=True),
        )
    except OTEL_LOG_EXPORT_RECOVERABLE_EXCEPTIONS:
        return event_dict

    return event_dict


__all__ = ["configure_otlp_log_export", "mirror_event_to_otel"]
