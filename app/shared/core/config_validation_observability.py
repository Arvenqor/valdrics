"""Observability-specific settings validation helpers."""

from __future__ import annotations

from app.shared.core.config_validation_placeholders import require_no_managed_placeholder
from app.shared.orchestration.contracts import observability_backend


def _normalize_environment(value: object) -> str:
    return str(value or "").strip().lower()


def validate_observability_config(
    settings_obj: object,
    *,
    env_production: str,
    env_staging: str,
) -> None:
    """Require enterprise telemetry sinks and forbid public schema exposure."""
    environment = _normalize_environment(getattr(settings_obj, "ENVIRONMENT", ""))
    strict_env = environment in {env_production, env_staging}
    if not strict_env:
        return

    selected_backend = observability_backend(settings_obj)

    otlp_endpoint = str(
        getattr(settings_obj, "OTEL_EXPORTER_OTLP_ENDPOINT", "") or ""
    ).strip()
    sentry_dsn = str(getattr(settings_obj, "SENTRY_DSN", "") or "").strip()
    if selected_backend.value == "otlp":
        require_no_managed_placeholder(
            otlp_endpoint, name="OTEL_EXPORTER_OTLP_ENDPOINT"
        )
        if not otlp_endpoint:
            raise ValueError(
                "OTEL_EXPORTER_OTLP_ENDPOINT must be configured when OBSERVABILITY_BACKEND=otlp in staging/production."
            )
        if not otlp_endpoint.startswith(("http://", "https://")):
            raise ValueError(
                "OTEL_EXPORTER_OTLP_ENDPOINT must use an explicit http:// or https:// URL."
            )

        if not bool(getattr(settings_obj, "OTEL_LOGS_EXPORT_ENABLED", True)):
            raise ValueError(
                "OTEL_LOGS_EXPORT_ENABLED must remain true when OTLP export is configured."
            )

        require_no_managed_placeholder(sentry_dsn, name="SENTRY_DSN")
        if not sentry_dsn:
            raise ValueError(
                "SENTRY_DSN must be configured when OBSERVABILITY_BACKEND=otlp in staging/production."
            )
        if not sentry_dsn.startswith(("http://", "https://")):
            raise ValueError("SENTRY_DSN must use an explicit http:// or https:// URL.")
    else:
        project_id = str(getattr(settings_obj, "GCP_PROJECT_ID", "") or "").strip()
        if not project_id:
            raise ValueError(
                "GCP_PROJECT_ID must be configured when OBSERVABILITY_BACKEND=gcp in staging/production."
            )
        if otlp_endpoint:
            require_no_managed_placeholder(
                otlp_endpoint, name="OTEL_EXPORTER_OTLP_ENDPOINT"
            )
        if sentry_dsn:
            require_no_managed_placeholder(sentry_dsn, name="SENTRY_DSN")

    if bool(getattr(settings_obj, "EXPOSE_API_DOCUMENTATION_PUBLICLY", False)):
        raise ValueError(
            "EXPOSE_API_DOCUMENTATION_PUBLICLY must be false in staging/production."
        )


__all__ = ["validate_observability_config"]
