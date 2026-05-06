from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from scripts import preflight_gcp_managed_platform


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


def test_validate_project_permissions_accepts_required_grants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout="access-token\n",
            stderr="",
        )

    def fake_urlopen(request: Any, *, timeout: int) -> _FakeResponse:
        captured["headers"] = dict(request.header_items())
        captured["url"] = request.full_url
        captured["body"] = request.data
        captured["timeout"] = timeout
        return _FakeResponse(b'{"permissions":["iam.serviceAccounts.create"]}')

    monkeypatch.setattr(preflight_gcp_managed_platform.subprocess, "run", fake_run)
    monkeypatch.setattr(preflight_gcp_managed_platform, "urlopen", fake_urlopen)

    result = preflight_gcp_managed_platform.validate_project_permissions(
        project_id="valdrics-staging-001",
        required_permissions=("iam.serviceAccounts.create",),
    )

    assert result == {
        "granted_permissions": ["iam.serviceAccounts.create"],
        "required_permissions": ["iam.serviceAccounts.create"],
    }
    assert captured["command"] == [
        "gcloud",
        "auth",
        "print-access-token",
    ]
    assert captured["kwargs"]["capture_output"] is True
    assert captured["kwargs"]["text"] is True
    assert captured["timeout"] == 20
    assert (
        captured["url"]
        == "https://cloudresourcemanager.googleapis.com/v1/projects/"
        "valdrics-staging-001:testIamPermissions"
    )
    assert json_loads(captured["body"]) == {
        "permissions": ["iam.serviceAccounts.create"]
    }
    assert captured["headers"]["Authorization"] == "Bearer access-token"
    assert (
        captured["headers"]["User-agent"]
        == preflight_gcp_managed_platform.GOOGLE_API_USER_AGENT
    )


def test_validate_project_permissions_rejects_missing_grants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        preflight_gcp_managed_platform.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(
            returncode=0,
            stdout="access-token\n",
            stderr="",
        ),
    )
    monkeypatch.setattr(
        preflight_gcp_managed_platform,
        "urlopen",
        lambda *_args, **_kwargs: _FakeResponse(b'{"permissions":[]}'),
    )

    with pytest.raises(RuntimeError, match="iam.serviceAccounts.create"):
        preflight_gcp_managed_platform.validate_project_permissions(
            project_id="valdrics-staging-001",
            required_permissions=("iam.serviceAccounts.create",),
        )


def test_default_required_permissions_include_service_account_and_project_iam() -> None:
    assert "iam.serviceAccounts.create" in (
        preflight_gcp_managed_platform.DEFAULT_REQUIRED_PERMISSIONS
    )
    assert "resourcemanager.projects.setIamPolicy" in (
        preflight_gcp_managed_platform.DEFAULT_REQUIRED_PERMISSIONS
    )


def json_loads(raw: bytes) -> object:
    return json.loads(raw.decode("utf-8"))
