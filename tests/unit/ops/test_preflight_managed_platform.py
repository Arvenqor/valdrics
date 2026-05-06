from __future__ import annotations

import json

import pytest

from scripts.generate_managed_deployment_artifacts import supabase_project_ref_from_url
from scripts import preflight_managed_platform


def test_supabase_project_ref_from_url_derives_existing_project_ref() -> None:
    assert (
        supabase_project_ref_from_url("https://hnnksaolfbfkekgdxvpf.supabase.co")
        == "hnnksaolfbfkekgdxvpf"
    )
    assert (
        supabase_project_ref_from_url("https://REPLACE_WITH_SUPABASE_PROJECT.supabase.co")
        == ""
    )
    assert supabase_project_ref_from_url("https://example.com") == ""


def test_validate_supabase_project_binding_checks_ref_org_and_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_request_json(url: str, *, access_token: str) -> dict[str, str]:
        assert url.endswith("/v1/projects/hnnksaolfbfkekgdxvpf")
        assert access_token == "token"
        return {
            "ref": "hnnksaolfbfkekgdxvpf",
            "organization_id": "yxmvrweoyqfysmuazbxw",
            "organization_slug": "valdrics",
            "name": "valdrics-staging",
            "status": "ACTIVE_HEALTHY",
        }

    monkeypatch.setattr(preflight_managed_platform, "_request_json", fake_request_json)

    result = preflight_managed_platform.validate_supabase_project_binding(
        runtime_plain_env_json=json.dumps(
            {"SUPABASE_URL": "https://hnnksaolfbfkekgdxvpf.supabase.co"}
        ),
        supabase_organization_id="yxmvrweoyqfysmuazbxw",
        supabase_project_name="valdrics-staging",
        supabase_access_token="token",
    )

    assert result == {
        "project_ref": "hnnksaolfbfkekgdxvpf",
        "project_name": "valdrics-staging",
        "project_status": "ACTIVE_HEALTHY",
    }


def test_validate_supabase_project_binding_rejects_wrong_project_name(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        preflight_managed_platform,
        "_request_json",
        lambda _url, *, access_token: {
            "ref": "hnnksaolfbfkekgdxvpf",
            "organization_id": "yxmvrweoyqfysmuazbxw",
            "name": "wrong-name",
        },
    )

    with pytest.raises(ValueError, match="SUPABASE_PROJECT_NAME"):
        preflight_managed_platform.validate_supabase_project_binding(
            runtime_plain_env_json=json.dumps(
                {"SUPABASE_URL": "https://hnnksaolfbfkekgdxvpf.supabase.co"}
            ),
            supabase_organization_id="yxmvrweoyqfysmuazbxw",
            supabase_project_name="valdrics-staging",
            supabase_access_token="token",
        )
