from __future__ import annotations

import json
from typing import Any

import pytest

from scripts import manage_supabase_auth_config


def _runtime_env() -> str:
    return json.dumps(
        {
            "SUPABASE_URL": "https://hnnksaolfbfkekgdxvpf.supabase.co",
            "FRONTEND_URL": "https://app.valdrics.com",
        }
    )


def test_build_patch_enables_signup_and_preserves_redirects() -> None:
    config = {
        "disable_signup": True,
        "site_url": "http://localhost:3000",
        "uri_allow_list": "https://old.example.com/auth/callback",
    }

    patch = manage_supabase_auth_config._build_patch(
        config,
        frontend_url="https://app.valdrics.com",
    )

    assert patch == {
        "disable_signup": False,
        "site_url": "https://app.valdrics.com",
        "uri_allow_list": (
            "https://old.example.com/auth/callback,"
            "https://app.valdrics.com/auth/callback"
        ),
    }


def test_build_patch_keeps_ready_config_empty() -> None:
    config = {
        "disable_signup": False,
        "site_url": "https://app.valdrics.com",
        "uri_allow_list": ["https://app.valdrics.com/auth/callback"],
    }

    assert (
        manage_supabase_auth_config._build_patch(
            config,
            frontend_url="https://app.valdrics.com",
        )
        == {}
    )


def test_redirect_allowed_supports_exact_and_wildcard_patterns() -> None:
    assert manage_supabase_auth_config._redirect_allowed(
        "https://app.valdrics.com/auth/callback",
        ["https://app.valdrics.com/auth/callback"],
    )
    assert manage_supabase_auth_config._redirect_allowed(
        "https://preview.valdrics.com/auth/callback",
        ["https://*.valdrics.com/auth/callback"],
    )
    assert not manage_supabase_auth_config._redirect_allowed(
        "https://evil.example.com/auth/callback",
        ["https://*.valdrics.com/auth/callback"],
    )


def test_inspect_or_repair_fails_ready_when_not_apply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request_json(
        url: str,
        *,
        access_token: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        calls.append((url, method, payload))
        assert access_token == "token"
        return {"disable_signup": True, "site_url": "", "uri_allow_list": []}

    monkeypatch.setattr(manage_supabase_auth_config, "_request_json", fake_request_json)

    report = manage_supabase_auth_config.inspect_or_repair_auth_config(
        runtime_plain_env_json=_runtime_env(),
        environment="production",
        supabase_access_token="token",
        apply=False,
    )

    assert report["ready"] is False
    assert report["pending_patch_keys"] == [
        "disable_signup",
        "site_url",
        "uri_allow_list",
    ]
    assert [call[1] for call in calls] == ["GET"]


def test_inspect_or_repair_applies_and_rechecks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, dict[str, Any] | None]] = []

    def fake_request_json(
        url: str,
        *,
        access_token: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        calls.append((url, method, payload))
        assert access_token == "token"
        if method == "PATCH":
            assert payload == {
                "disable_signup": False,
                "site_url": "https://app.valdrics.com",
                "uri_allow_list": ["https://app.valdrics.com/auth/callback"],
            }
            return {
                "disable_signup": False,
                "site_url": "https://app.valdrics.com",
                "uri_allow_list": ["https://app.valdrics.com/auth/callback"],
            }
        return {"disable_signup": True, "site_url": "", "uri_allow_list": []}

    monkeypatch.setattr(manage_supabase_auth_config, "_request_json", fake_request_json)

    report = manage_supabase_auth_config.inspect_or_repair_auth_config(
        runtime_plain_env_json=_runtime_env(),
        environment="production",
        supabase_access_token="token",
        apply=True,
    )

    assert report["ready"] is True
    assert report["changed"] is True
    assert [call[1] for call in calls] == ["GET", "PATCH"]
