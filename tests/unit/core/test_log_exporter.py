from __future__ import annotations

import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.shared.core.log_exporter as log_exporter


def _settings(
    *,
    endpoint: str = "http://otel-a:4317",
    insecure: bool = False,
    enabled: bool = True,
    testing: bool = False,
    environment: str = "staging",
) -> SimpleNamespace:
    return SimpleNamespace(
        OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,
        OTEL_EXPORTER_OTLP_INSECURE=insecure,
        OTEL_LOGS_EXPORT_ENABLED=enabled,
        TESTING=testing,
        ENVIRONMENT=environment,
    )


def _cleanup_otlp_logger_state() -> None:
    logger = logging.getLogger(log_exporter._OTEL_LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    log_exporter._otlp_logger_provider = None
    log_exporter._otlp_logger_config = None


def setup_function() -> None:
    _cleanup_otlp_logger_state()


def teardown_function() -> None:
    _cleanup_otlp_logger_state()


def test_configure_otlp_log_export_rebuilds_when_runtime_config_changes() -> None:
    provider_a = MagicMock()
    provider_b = MagicMock()
    handler_a = logging.NullHandler()
    handler_b = logging.NullHandler()

    with (
        patch(
            "app.shared.core.log_exporter.LoggerProvider",
            side_effect=[provider_a, provider_b],
        ),
        patch("app.shared.core.log_exporter.OTLPLogExporter"),
        patch("app.shared.core.log_exporter.BatchLogRecordProcessor"),
        patch(
            "app.shared.core.log_exporter.LoggingHandler",
            side_effect=[handler_a, handler_b],
        ),
    ):
        logger = log_exporter.configure_otlp_log_export(
            _settings(endpoint="http://otel-a:4317")
        )
        rebuilt_logger = log_exporter.configure_otlp_log_export(
            _settings(endpoint="http://otel-b:4317", insecure=True)
        )

    assert logger is rebuilt_logger
    assert provider_a.shutdown.call_count == 1
    assert logger.handlers == [handler_b]
    assert log_exporter._otlp_logger_config == (
        "http://otel-b:4317",
        True,
        "staging",
    )


def test_configure_otlp_log_export_clears_existing_logger_when_disabled() -> None:
    provider = MagicMock()
    handler = logging.NullHandler()

    with (
        patch("app.shared.core.log_exporter.LoggerProvider", return_value=provider),
        patch("app.shared.core.log_exporter.OTLPLogExporter"),
        patch("app.shared.core.log_exporter.BatchLogRecordProcessor"),
        patch("app.shared.core.log_exporter.LoggingHandler", return_value=handler),
    ):
        logger = log_exporter.configure_otlp_log_export(_settings())
        result = log_exporter.configure_otlp_log_export(_settings(enabled=False))

    assert logger is not None
    assert result is None
    assert provider.shutdown.call_count == 1
    assert logging.getLogger(log_exporter._OTEL_LOGGER_NAME).handlers == []
    assert log_exporter._otlp_logger_provider is None
    assert log_exporter._otlp_logger_config is None
