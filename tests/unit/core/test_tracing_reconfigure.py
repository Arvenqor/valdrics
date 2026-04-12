from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.shared.core.tracing as tracing_module


def _settings(
    *,
    endpoint: str | None,
    insecure: bool = False,
    environment: str = "development",
    testing: bool = False,
    backend: str = "otlp",
) -> SimpleNamespace:
    return SimpleNamespace(
        OBSERVABILITY_BACKEND=backend,
        TESTING=testing,
        OTEL_EXPORTER_OTLP_ENDPOINT=endpoint,
        OTEL_EXPORTER_OTLP_INSECURE=insecure,
        ENVIRONMENT=environment,
    )


def setup_function() -> None:
    tracing_module._configured_tracer_provider = None
    tracing_module._configured_tracing_signature = None


def teardown_function() -> None:
    tracing_module._configured_tracer_provider = None
    tracing_module._configured_tracing_signature = None


def test_setup_tracing_reconfigures_existing_provider_when_otlp_changes() -> None:
    provider = MagicMock()

    with (
        patch("app.shared.core.tracing.get_settings") as get_settings,
        patch("app.shared.core.tracing.TracerProvider", return_value=provider) as provider_cls,
        patch("app.shared.core.tracing.trace.set_tracer_provider") as set_provider,
        patch("app.shared.core.tracing.OTLPSpanExporter") as otlp_exporter,
        patch(
            "app.shared.core.tracing.BatchSpanProcessor",
            side_effect=lambda exporter: ("processor", exporter),
        ) as batch_processor,
    ):
        get_settings.return_value = _settings(
            endpoint="http://otel-a:4317",
            insecure=False,
            environment="production",
        )
        tracing_module.setup_tracing()

        get_settings.return_value = _settings(
            endpoint="http://otel-b:4317",
            insecure=True,
            environment="production",
        )
        tracing_module.setup_tracing()

    provider_cls.assert_called_once()
    set_provider.assert_called_once_with(provider)
    assert provider.shutdown.call_count == 1
    assert provider.add_span_processor.call_count == 2
    assert otlp_exporter.call_args_list[0].kwargs == {
        "endpoint": "http://otel-a:4317",
        "insecure": False,
    }
    assert otlp_exporter.call_args_list[1].kwargs == {
        "endpoint": "http://otel-b:4317",
        "insecure": True,
    }
    assert batch_processor.call_count == 2
    assert tracing_module._configured_tracing_signature == (
        "otlp",
        "http://otel-b:4317",
        True,
        "production",
    )


def test_setup_tracing_instruments_fastapi_app_only_once() -> None:
    provider = MagicMock()
    app = MagicMock()
    app.state = SimpleNamespace()

    with (
        patch(
            "app.shared.core.tracing.get_settings",
            return_value=_settings(endpoint=None, environment="development"),
        ),
        patch("app.shared.core.tracing.TracerProvider", return_value=provider),
        patch("app.shared.core.tracing.trace.set_tracer_provider"),
        patch("app.shared.core.tracing.ConsoleSpanExporter"),
        patch(
            "app.shared.core.tracing.BatchSpanProcessor",
            side_effect=lambda exporter: ("processor", exporter),
        ),
        patch("app.shared.core.tracing.FastAPIInstrumentor.instrument_app") as instrument_app,
    ):
        tracing_module.setup_tracing(app=app)
        tracing_module.setup_tracing(app=app)

    instrument_app.assert_called_once_with(app)
