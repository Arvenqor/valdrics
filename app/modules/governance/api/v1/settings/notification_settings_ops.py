from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


def _setting_value(data: Any, key: str, default: Any = None) -> Any:
    if isinstance(data, Mapping):
        return data.get(key, default)
    return getattr(data, key, default)


def enforce_incident_integrations_access(
    *,
    data: Any,
    current_tier: Any,
    normalize_tier_fn: Callable[[Any], Any],
    is_feature_enabled_fn: Callable[[Any, Any], bool],
    incident_integrations_feature: Any,
    raise_http_exception_fn: Callable[[int, str], None],
) -> None:
    needs_incident_integrations = bool(
        _setting_value(data, "teams_enabled", False)
        or _setting_value(data, "workflow_github_enabled", False)
        or _setting_value(data, "workflow_gitlab_enabled", False)
        or _setting_value(data, "workflow_webhook_enabled", False)
    )
    if not needs_incident_integrations:
        return

    tier = normalize_tier_fn(current_tier)
    if is_feature_enabled_fn(tier, incident_integrations_feature):
        return

    raise_http_exception_fn(
        403,
        (
            f"Feature '{incident_integrations_feature.value}' requires an upgrade. "
            f"Current tier: {tier.value}"
        ),
    )


def enforce_jira_integration_access(
    *,
    data: Any,
    current_tier: Any,
    normalize_tier_fn: Callable[[Any], Any],
    is_feature_enabled_fn: Callable[[Any, Any], bool],
    jira_integration_feature: Any,
    raise_http_exception_fn: Callable[[int, str], None],
) -> None:
    if not bool(_setting_value(data, "jira_enabled", False)):
        return

    tier = normalize_tier_fn(current_tier)
    if is_feature_enabled_fn(tier, jira_integration_feature):
        return

    raise_http_exception_fn(
        403,
        (
            f"Feature '{jira_integration_feature.value}' requires an upgrade. "
            f"Current tier: {tier.value}"
        ),
    )


def enforce_slack_integration_access(
    *,
    data: Any,
    current_tier: Any,
    normalize_tier_fn: Callable[[Any], Any],
    is_feature_enabled_fn: Callable[[Any, Any], bool],
    slack_integration_feature: Any,
    raise_http_exception_fn: Callable[[int, str], None],
) -> None:
    needs_slack_integration = bool(
        _setting_value(data, "slack_enabled", False)
        or _setting_value(data, "slack_channel_override", None)
    )
    if not needs_slack_integration:
        return

    tier = normalize_tier_fn(current_tier)
    if is_feature_enabled_fn(tier, slack_integration_feature):
        return

    raise_http_exception_fn(
        403,
        (
            f"Feature '{slack_integration_feature.value}' requires an upgrade. "
            f"Current tier: {tier.value}"
        ),
    )


def build_notification_settings_create_kwargs(
    *,
    data: Any,
    tenant_id: Any,
) -> dict[str, Any]:
    return {
        "tenant_id": tenant_id,
        "slack_enabled": data.slack_enabled,
        "slack_channel_override": data.slack_channel_override,
        "jira_enabled": data.jira_enabled,
        "jira_base_url": data.jira_base_url,
        "jira_email": str(data.jira_email) if data.jira_email else None,
        "jira_project_key": data.jira_project_key,
        "jira_issue_type": data.jira_issue_type,
        "jira_api_token": data.jira_api_token,
        "teams_enabled": data.teams_enabled,
        "teams_webhook_url": data.teams_webhook_url,
        "digest_schedule": data.digest_schedule,
        "digest_hour": data.digest_hour,
        "digest_minute": data.digest_minute,
        "alert_on_budget_warning": data.alert_on_budget_warning,
        "alert_on_budget_exceeded": data.alert_on_budget_exceeded,
        "alert_on_zombie_detected": data.alert_on_zombie_detected,
        "workflow_github_enabled": data.workflow_github_enabled,
        "workflow_github_owner": data.workflow_github_owner,
        "workflow_github_repo": data.workflow_github_repo,
        "workflow_github_workflow_id": data.workflow_github_workflow_id,
        "workflow_github_ref": data.workflow_github_ref,
        "workflow_github_token": data.workflow_github_token,
        "workflow_gitlab_enabled": data.workflow_gitlab_enabled,
        "workflow_gitlab_base_url": data.workflow_gitlab_base_url,
        "workflow_gitlab_project_id": data.workflow_gitlab_project_id,
        "workflow_gitlab_ref": data.workflow_gitlab_ref,
        "workflow_gitlab_trigger_token": data.workflow_gitlab_trigger_token,
        "workflow_webhook_enabled": data.workflow_webhook_enabled,
        "workflow_webhook_url": data.workflow_webhook_url,
        "workflow_webhook_bearer_token": data.workflow_webhook_bearer_token,
    }


def _apply_plain_updates(
    *,
    settings: Any,
    updates: Mapping[str, Any],
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        if field_name in updates:
            setattr(settings, field_name, updates[field_name])


def _apply_optional_string_update(
    *,
    settings: Any,
    updates: Mapping[str, Any],
    field_name: str,
) -> None:
    if field_name not in updates:
        return
    value = updates[field_name]
    setattr(settings, field_name, str(value) if value else None)


def _apply_secret_update(
    *,
    settings: Any,
    updates: Mapping[str, Any],
    field_name: str,
    clear_flag_name: str,
    initialize_if_missing: bool = False,
) -> None:
    if updates.get(field_name):
        setattr(settings, field_name, updates[field_name])
        return
    if updates.get(clear_flag_name):
        setattr(settings, field_name, None)
        return
    if initialize_if_missing and not hasattr(settings, field_name):
        setattr(settings, field_name, None)


def apply_notification_settings_update(
    *,
    settings: Any,
    updates: dict[str, Any],
) -> None:
    _apply_plain_updates(
        settings=settings,
        updates=updates,
        field_names=(
            "slack_enabled",
            "slack_channel_override",
            "jira_enabled",
            "jira_base_url",
            "jira_project_key",
            "jira_issue_type",
            "teams_enabled",
            "teams_webhook_url",
            "digest_schedule",
            "digest_hour",
            "digest_minute",
            "alert_on_budget_warning",
            "alert_on_budget_exceeded",
            "alert_on_zombie_detected",
            "workflow_github_enabled",
            "workflow_github_owner",
            "workflow_github_repo",
            "workflow_github_workflow_id",
            "workflow_github_ref",
            "workflow_gitlab_enabled",
            "workflow_gitlab_base_url",
            "workflow_gitlab_project_id",
            "workflow_gitlab_ref",
            "workflow_webhook_enabled",
            "workflow_webhook_url",
        ),
    )
    _apply_optional_string_update(
        settings=settings,
        updates=updates,
        field_name="jira_email",
    )
    _apply_secret_update(
        settings=settings,
        updates=updates,
        field_name="jira_api_token",
        clear_flag_name="clear_jira_api_token",
        initialize_if_missing=True,
    )
    _apply_secret_update(
        settings=settings,
        updates=updates,
        field_name="teams_webhook_url",
        clear_flag_name="clear_teams_webhook_url",
        initialize_if_missing=True,
    )
    _apply_secret_update(
        settings=settings,
        updates=updates,
        field_name="workflow_github_token",
        clear_flag_name="clear_workflow_github_token",
    )
    _apply_secret_update(
        settings=settings,
        updates=updates,
        field_name="workflow_gitlab_trigger_token",
        clear_flag_name="clear_workflow_gitlab_trigger_token",
    )
    _apply_secret_update(
        settings=settings,
        updates=updates,
        field_name="workflow_webhook_bearer_token",
        clear_flag_name="clear_workflow_webhook_bearer_token",
    )


def validate_notification_settings_requirements(
    *,
    settings: Any,
    raise_http_exception_fn: Callable[[int, str], None],
) -> None:
    if settings.jira_enabled:
        from app.modules.notifications.domain.jira import validate_jira_base_url

        jira_requirements = [
            ("jira_base_url", settings.jira_base_url),
            ("jira_email", settings.jira_email),
            ("jira_project_key", settings.jira_project_key),
            ("jira_api_token", settings.jira_api_token),
        ]
        missing = [name for name, value in jira_requirements if not value]
        if missing:
            raise_http_exception_fn(
                422,
                "Jira is enabled but missing required fields: " + ", ".join(missing),
            )
        try:
            validate_jira_base_url(str(settings.jira_base_url))
        except ValueError as exc:
            raise_http_exception_fn(422, f"jira_base_url is invalid: {exc}")
    if settings.teams_enabled and not settings.teams_webhook_url:
        raise_http_exception_fn(
            422,
            "Teams is enabled but missing required field: teams_webhook_url",
        )
    if settings.workflow_github_enabled:
        github_requirements = [
            ("workflow_github_owner", settings.workflow_github_owner),
            ("workflow_github_repo", settings.workflow_github_repo),
            ("workflow_github_workflow_id", settings.workflow_github_workflow_id),
            ("workflow_github_token", settings.workflow_github_token),
        ]
        missing = [name for name, value in github_requirements if not value]
        if missing:
            raise_http_exception_fn(
                422,
                "GitHub workflow dispatch is enabled but missing required fields: "
                + ", ".join(missing),
            )

    if settings.workflow_gitlab_enabled:
        gitlab_requirements = [
            ("workflow_gitlab_base_url", settings.workflow_gitlab_base_url),
            ("workflow_gitlab_project_id", settings.workflow_gitlab_project_id),
            ("workflow_gitlab_trigger_token", settings.workflow_gitlab_trigger_token),
        ]
        missing = [name for name, value in gitlab_requirements if not value]
        if missing:
            raise_http_exception_fn(
                422,
                "GitLab workflow dispatch is enabled but missing required fields: "
                + ", ".join(missing),
            )

    if settings.workflow_webhook_enabled and not settings.workflow_webhook_url:
        raise_http_exception_fn(
            422,
            "Webhook workflow dispatch is enabled but missing required field: "
            "workflow_webhook_url",
        )


def build_notification_settings_audit_payload(settings: Any) -> dict[str, Any]:
    return {
        "slack_enabled": settings.slack_enabled,
        "digest": settings.digest_schedule,
        "slack_override": bool(settings.slack_channel_override),
        "jira_enabled": bool(getattr(settings, "jira_enabled", False)),
        "jira_base_url": bool(getattr(settings, "jira_base_url", None)),
        "jira_project_key": getattr(settings, "jira_project_key", None),
        "has_jira_api_token": bool(getattr(settings, "jira_api_token", None)),
        "teams_enabled": bool(getattr(settings, "teams_enabled", False)),
        "has_teams_webhook_url": bool(getattr(settings, "teams_webhook_url", None)),
        "workflow_github_enabled": bool(
            getattr(settings, "workflow_github_enabled", False)
        ),
        "workflow_has_github_token": bool(
            getattr(settings, "workflow_github_token", None)
        ),
        "workflow_gitlab_enabled": bool(
            getattr(settings, "workflow_gitlab_enabled", False)
        ),
        "workflow_has_gitlab_trigger_token": bool(
            getattr(settings, "workflow_gitlab_trigger_token", None)
        ),
        "workflow_webhook_enabled": bool(
            getattr(settings, "workflow_webhook_enabled", False)
        ),
        "workflow_has_webhook_bearer_token": bool(
            getattr(settings, "workflow_webhook_bearer_token", None)
        ),
    }
