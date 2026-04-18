from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.modules.governance.api.v1.settings.notification_diagnostics_ops import (
    to_notification_response,
    to_slack_policy_diagnostics,
)
from app.modules.governance.api.v1.settings.notification_settings_ops import (
    apply_notification_settings_update,
    enforce_jira_integration_access,
    enforce_slack_integration_access,
)


class _CapturedHttpError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _raise_http_error(status_code: int, detail: str) -> None:
    raise _CapturedHttpError(status_code, detail)


def test_enforce_slack_integration_access_requires_growth_or_higher() -> None:
    with pytest.raises(_CapturedHttpError) as exc_info:
        enforce_slack_integration_access(
            data=SimpleNamespace(slack_enabled=True, slack_channel_override=None),
            current_tier=SimpleNamespace(value="starter"),
            normalize_tier_fn=lambda tier: tier,
            is_feature_enabled_fn=lambda tier, feature: False,
            slack_integration_feature=SimpleNamespace(value="slack_integration"),
            raise_http_exception_fn=_raise_http_error,
        )

    assert exc_info.value.status_code == 403
    assert "slack_integration" in exc_info.value.detail
    assert "starter" in exc_info.value.detail


def test_enforce_slack_integration_access_allows_growth_when_enabled() -> None:
    enforce_slack_integration_access(
        data=SimpleNamespace(slack_enabled=True, slack_channel_override="#alerts"),
        current_tier=SimpleNamespace(value="growth"),
        normalize_tier_fn=lambda tier: tier,
        is_feature_enabled_fn=lambda tier, feature: True,
        slack_integration_feature=SimpleNamespace(value="slack_integration"),
        raise_http_exception_fn=_raise_http_error,
    )


def test_enforce_jira_integration_access_requires_growth_or_higher() -> None:
    with pytest.raises(_CapturedHttpError) as exc_info:
        enforce_jira_integration_access(
            data=SimpleNamespace(jira_enabled=True),
            current_tier=SimpleNamespace(value="starter"),
            normalize_tier_fn=lambda tier: tier,
            is_feature_enabled_fn=lambda tier, feature: False,
            jira_integration_feature=SimpleNamespace(value="jira_integration"),
            raise_http_exception_fn=_raise_http_error,
        )

    assert exc_info.value.status_code == 403
    assert "jira_integration" in exc_info.value.detail
    assert "starter" in exc_info.value.detail


def test_enforce_jira_integration_access_allows_growth_when_enabled() -> None:
    enforce_jira_integration_access(
        data=SimpleNamespace(jira_enabled=True),
        current_tier=SimpleNamespace(value="growth"),
        normalize_tier_fn=lambda tier: tier,
        is_feature_enabled_fn=lambda tier, feature: True,
        jira_integration_feature=SimpleNamespace(value="jira_integration"),
        raise_http_exception_fn=_raise_http_error,
    )


def test_to_notification_response_masks_slack_fields_when_tier_disallows_feature() -> None:
    response = to_notification_response(
        SimpleNamespace(
            slack_enabled=True,
            slack_channel_override="#alerts",
            jira_enabled=False,
            teams_enabled=False,
            digest_schedule="daily",
            digest_hour=9,
            digest_minute=0,
            alert_on_budget_warning=True,
            alert_on_budget_exceeded=True,
            alert_on_zombie_detected=True,
        ),
        slack_feature_allowed_by_tier=False,
    )

    assert response.slack_enabled is False
    assert response.slack_channel_override is None


def test_to_slack_policy_diagnostics_flags_tier_block_and_masks_readiness() -> None:
    diagnostics = to_slack_policy_diagnostics(
        remediation_settings=SimpleNamespace(
            policy_enabled=True,
            policy_violation_notify_slack=True,
        ),
        notification_settings=SimpleNamespace(
            slack_enabled=True,
            slack_channel_override="#alerts",
        ),
        feature_allowed_by_tier=False,
        has_bot_token=True,
        has_default_channel=True,
    )

    assert diagnostics.feature_allowed_by_tier is False
    assert diagnostics.ready is False
    assert "tier_missing_slack_integration_feature" in diagnostics.reasons
    assert diagnostics.selected_channel == "#alerts"
    assert diagnostics.channel_source == "tenant_override"


def test_to_slack_policy_diagnostics_missing_rows_fail_closed() -> None:
    diagnostics = to_slack_policy_diagnostics(
        remediation_settings=None,
        notification_settings=None,
        feature_allowed_by_tier=True,
        has_bot_token=True,
        has_default_channel=True,
    )

    assert diagnostics.ready is False
    assert diagnostics.enabled_for_policy is False
    assert diagnostics.enabled_in_notifications is False
    assert "missing_remediation_settings" in diagnostics.reasons
    assert "missing_notification_settings" in diagnostics.reasons


def test_apply_notification_settings_update_handles_secret_set_clear_and_normalization() -> None:
    settings = SimpleNamespace(
        slack_enabled=False,
        slack_channel_override=None,
        jira_enabled=False,
        jira_base_url=None,
        jira_email="old@example.com",
        jira_project_key=None,
        jira_issue_type=None,
        jira_api_token="old-token",
        teams_enabled=False,
        teams_webhook_url="old-webhook",
        digest_schedule="daily",
        digest_hour=9,
        digest_minute=0,
        alert_on_budget_warning=False,
        alert_on_budget_exceeded=False,
        alert_on_zombie_detected=False,
        workflow_github_enabled=False,
        workflow_github_owner=None,
        workflow_github_repo=None,
        workflow_github_workflow_id=None,
        workflow_github_ref=None,
        workflow_github_token="old-gh-token",
        workflow_gitlab_enabled=False,
        workflow_gitlab_base_url=None,
        workflow_gitlab_project_id=None,
        workflow_gitlab_ref=None,
        workflow_gitlab_trigger_token="old-gl-token",
        workflow_webhook_enabled=False,
        workflow_webhook_url=None,
        workflow_webhook_bearer_token="old-webhook-token",
    )

    apply_notification_settings_update(
        settings=settings,
        updates={
            "slack_enabled": True,
            "jira_email": None,
            "clear_jira_api_token": True,
            "teams_webhook_url": "https://teams.example.test/webhook",
            "workflow_github_token": "new-gh-token",
            "clear_workflow_gitlab_trigger_token": True,
            "clear_workflow_webhook_bearer_token": True,
        },
    )

    assert settings.slack_enabled is True
    assert settings.jira_email is None
    assert settings.jira_api_token is None
    assert settings.teams_webhook_url == "https://teams.example.test/webhook"
    assert settings.workflow_github_token == "new-gh-token"
    assert settings.workflow_gitlab_trigger_token is None
    assert settings.workflow_webhook_bearer_token is None
