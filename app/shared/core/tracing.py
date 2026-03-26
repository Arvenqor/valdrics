import structlog
from opentelemetry import trace
from opentelemetry.trace import Tracer
from opentelemetry.sdk.trace import SynchronousMultiSpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from fastapi import FastAPI
from app.shared.core.config import get_settings

logger = structlog.get_logger()
STRICT_TRACING_ENVIRONMENTS = frozenset({"production", "staging"})
_configured_tracer_provider: TracerProvider | None = None
_configured_tracing_signature: tuple[str | None, bool, str] | None = None


def _build_tracing_resource(environment: str) -> Resource:
    return Resource(
        attributes={
            ResourceAttributes.SERVICE_NAME: "valdrics-api",
            "env": environment,
        }
    )


def _reset_tracer_provider(
    provider: TracerProvider,
    *,
    resource: Resource,
) -> None:
    provider.shutdown()
    provider._resource = resource  # type: ignore[attr-defined]
    provider._active_span_processor = SynchronousMultiSpanProcessor()  # type: ignore[attr-defined]


def _instrument_fastapi_once(app: FastAPI) -> None:
    if getattr(app.state, "_valdrics_tracing_instrumented", False) is True:
        return
    FastAPIInstrumentor.instrument_app(app)
    app.state._valdrics_tracing_instrumented = True
    logger.info("fastapi_instrumented")


def setup_tracing(app: FastAPI | None = None) -> None:
    """
    Sets up OpenTelemetry tracing for the application.
    """
    settings = get_settings()

    if settings.TESTING:
        logger.info("setup_tracing_skipped_in_test")
        return

    environment = str(getattr(settings, "ENVIRONMENT", "") or "development")
    otlp_endpoint = str(getattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "") or "").strip()
    if otlp_endpoint:
        insecure = bool(getattr(settings, "OTEL_EXPORTER_OTLP_INSECURE", False))
    elif environment.strip().lower() in STRICT_TRACING_ENVIRONMENTS:
        raise RuntimeError(
            "OTEL_EXPORTER_OTLP_ENDPOINT must be configured in staging/production."
        )
    else:
        insecure = False

    signature = (otlp_endpoint or None, insecure, environment)
    resource = _build_tracing_resource(environment)

    global _configured_tracer_provider, _configured_tracing_signature
    provider = _configured_tracer_provider
    if provider is None:
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        _configured_tracer_provider = provider

    if _configured_tracing_signature != signature:
        if _configured_tracing_signature is not None:
            _reset_tracer_provider(provider, resource=resource)
        if otlp_endpoint:
            logger.info("setup_tracing_otlp", endpoint=otlp_endpoint, insecure=insecure)
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=insecure)
            provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        else:
            logger.info("setup_tracing_console")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        _configured_tracing_signature = signature

    # 4. Instrument FastAPI if provided
    if app:
        _instrument_fastapi_once(app)


def get_tracer(name: str) -> Tracer:
    """Returns a tracer instance for manual instrumentation."""
    return trace.get_tracer(name)


def set_correlation_id(correlation_id: str) -> None:
    """Sets a correlation ID for the current span."""
    current_span = trace.get_current_span()
    if current_span:
        current_span.set_attribute("correlation_id", correlation_id)


def get_current_trace_id() -> str | None:
    """
    Returns the current trace ID in hex format.
    Used for correlating logs and Sentry events.
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return None
