from __future__ import annotations

import logging
import sys
import types
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from google.auth.exceptions import DefaultCredentialsError

import app.shared.core.log_exporter as log_exporter
import app.shared.core.tracing as tracing_module
from app.shared.core.health_check_ops import _default_worker_probe
from app.shared.core.runtime_dependencies import validate_runtime_dependencies
from app.shared.core.tracing import setup_tracing


def _gcp_settings() -> SimpleNamespace:
    return SimpleNamespace(
        ENVIRONMENT="production",
        TESTING=False,
        PLATFORM_RUNTIME_PROFILE="gcp",
        OBSERVABILITY_BACKEND="gcp",
        PUBLIC_API_RATE_LIMITING_BACKEND="cloudflare",
        RATELIMIT_ENABLED=False,
        CIRCUIT_BREAKER_DISTRIBUTED_STATE=False,
        GCP_PROJECT_ID="valdrics-prod",
        GCP_REGION="us-central1",
        GCP_CLOUD_TASKS_QUEUE="valdrics-default",
        GCP_CLOUD_TASKS_INVOKER_SERVICE_ACCOUNT_EMAIL="tasks@valdrics.iam.gserviceaccount.com",
        GCP_CLOUD_RUN_SERVICE_NAME="valdrics-api",
        GCP_CLOUD_RUN_BATCH_JOB_NAME="valdrics-scheduler-batch",
        GCP_INTERNAL_ALLOWED_SERVICE_ACCOUNTS=[
            "tasks@valdrics.iam.gserviceaccount.com"
        ],
        API_URL="https://api.valdrics.example",
        FRONTEND_URL="https://app.valdrics.example",
        OTEL_EXPORTER_OTLP_ENDPOINT="",
        OTEL_EXPORTER_OTLP_INSECURE=False,
        OTEL_LOGS_EXPORT_ENABLED=True,
        SENTRY_DSN="",
        FORECASTER_ALLOW_HOLT_WINTERS_FALLBACK=True,
        FORECASTER_BREAK_GLASS_REASON="Temporary dependency incident",
        FORECASTER_BREAK_GLASS_EXPIRES_AT="2099-01-01T00:00:00+00:00",
        FORECASTER_BREAK_GLASS_MAX_DURATION_HOURS=999999,
    )


def _reset_log_exporter_state() -> None:
    logger = logging.getLogger(log_exporter._OTEL_LOGGER_NAME)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    log_exporter._otlp_logger_provider = None
    log_exporter._otlp_logger_config = None


def test_validate_runtime_dependencies_accepts_gcp_observability_profile() -> None:
    settings = _gcp_settings()

    def available(module_name: str) -> bool:
        return module_name in {
            "tiktoken",
            "opentelemetry.exporter.cloud_trace",
            "google.cloud.logging_v2.handlers.handlers",
        }

    with (
        patch(
            "app.shared.core.runtime_dependencies._is_supported_python_runtime",
            return_value=True,
        ),
        patch(
            "app.shared.core.runtime_dependencies._module_available",
            side_effect=available,
        ),
    ):
        validate_runtime_dependencies(settings)  # type: ignore[arg-type]


def test_setup_tracing_uses_gcp_cloud_trace_exporter() -> None:
    tracing_module._configured_tracer_provider = None
    tracing_module._configured_tracing_signature = None
    fake_cloud_trace_module = types.SimpleNamespace(
        CloudTraceSpanExporter=MagicMock(return_value=MagicMock())
    )

    with (
        patch("app.shared.core.tracing.get_settings", return_value=_gcp_settings()),
        patch.dict(
            sys.modules,
            {"opentelemetry.exporter.cloud_trace": fake_cloud_trace_module},
        ),
        patch("app.shared.core.tracing.TracerProvider") as mock_provider,
        patch("app.shared.core.tracing.trace.set_tracer_provider"),
        patch("app.shared.core.tracing.BatchSpanProcessor"),
    ):
        setup_tracing()

    fake_cloud_trace_module.CloudTraceSpanExporter.assert_called_once_with(
        project_id="valdrics-prod"
    )
    assert mock_provider.called


def test_configure_otlp_log_export_uses_cloud_logging_handler_for_gcp() -> None:
    _reset_log_exporter_state()
    client = MagicMock()
    handler = logging.NullHandler()
    fake_google_logging_module = types.SimpleNamespace(Client=MagicMock(return_value=client))
    fake_handlers_module = types.SimpleNamespace(CloudLoggingHandler=MagicMock(return_value=handler))
    google_cloud_module = types.ModuleType("google.cloud")
    google_cloud_module.logging = fake_google_logging_module

    with (
        patch.dict(
            sys.modules,
            {
                "google.cloud": google_cloud_module,
                "google.cloud.logging": fake_google_logging_module,
                "google.cloud.logging_v2.handlers.handlers": fake_handlers_module,
            },
        ),
        patch(
            "app.shared.core.log_exporter.LoggerProvider",
            return_value=MagicMock(),
        ),
    ):
        logger = log_exporter.configure_otlp_log_export(_gcp_settings())

    assert logger is not None
    fake_google_logging_module.Client.assert_called_once_with(project="valdrics-prod")
    fake_handlers_module.CloudLoggingHandler.assert_called_once_with(
        client,
        name="valdrics-api",
    )
    _reset_log_exporter_state()


def test_setup_tracing_falls_back_to_console_when_gcp_credentials_missing() -> None:
    tracing_module._configured_tracer_provider = None
    tracing_module._configured_tracing_signature = None
    provider = MagicMock()
    fake_cloud_trace_module = types.SimpleNamespace(
        CloudTraceSpanExporter=MagicMock(
            side_effect=DefaultCredentialsError("adc missing")
        )
    )

    with (
        patch("app.shared.core.tracing.get_settings", return_value=_gcp_settings()),
        patch.dict(
            sys.modules,
            {"opentelemetry.exporter.cloud_trace": fake_cloud_trace_module},
        ),
        patch("app.shared.core.tracing.TracerProvider", return_value=provider),
        patch("app.shared.core.tracing.trace.set_tracer_provider"),
        patch("app.shared.core.tracing.BatchSpanProcessor") as mock_batch,
        patch("app.shared.core.tracing.ConsoleSpanExporter") as mock_console,
    ):
        setup_tracing()

    fake_cloud_trace_module.CloudTraceSpanExporter.assert_called_once_with(
        project_id="valdrics-prod"
    )
    mock_console.assert_called_once()
    mock_batch.assert_called_once_with(mock_console.return_value)


def test_configure_otlp_log_export_skips_cloud_logging_when_gcp_credentials_missing() -> None:
    _reset_log_exporter_state()
    fake_google_logging_module = types.SimpleNamespace(
        Client=MagicMock(side_effect=DefaultCredentialsError("adc missing"))
    )
    fake_handlers_module = types.SimpleNamespace(
        CloudLoggingHandler=MagicMock(return_value=logging.NullHandler())
    )
    google_cloud_module = types.ModuleType("google.cloud")
    google_cloud_module.logging = fake_google_logging_module

    with patch.dict(
        sys.modules,
        {
            "google.cloud": google_cloud_module,
            "google.cloud.logging": fake_google_logging_module,
            "google.cloud.logging_v2.handlers.handlers": fake_handlers_module,
        },
    ):
        logger = log_exporter.configure_otlp_log_export(_gcp_settings())

    assert logger is None
    fake_google_logging_module.Client.assert_called_once_with(project="valdrics-prod")
    fake_handlers_module.CloudLoggingHandler.assert_not_called()
    assert logging.getLogger(log_exporter._OTEL_LOGGER_NAME).handlers == []
    _reset_log_exporter_state()


def test_default_worker_probe_reports_managed_execution_for_gcp() -> None:
    with patch("app.shared.core.health_check_ops.get_settings", return_value=_gcp_settings()):
        result = _default_worker_probe()

    assert result["status"] == "healthy"
    assert "Cloud Tasks" in result["message"]
    assert "Cloud Scheduler" in result["message"]
    assert result["runtime"] == "gcp_managed"
    assert result["task_queue"] == "valdrics-default"
    assert result["batch_job"] == "valdrics-scheduler-batch"
    assert result["service_name"] == "valdrics-api"
