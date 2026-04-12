from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from app.shared.orchestration.security import (
    _verify_google_identity_token,
    require_internal_platform_invocation,
)


@pytest.mark.asyncio
async def test_require_internal_platform_invocation_requires_google_identity_token() -> None:
    request = SimpleNamespace(headers={})
    settings = SimpleNamespace(PLATFORM_RUNTIME_PROFILE="gcp")

    with patch("app.shared.core.config.get_settings", return_value=settings):
        with pytest.raises(
            HTTPException,
            match="Google identity token is required for internal GCP invocation",
        ):
            await require_internal_platform_invocation(request=request)


@pytest.mark.asyncio
async def test_require_internal_platform_invocation_uses_google_token_for_gcp() -> None:
    request = SimpleNamespace(headers={"Authorization": "Bearer signed-google-token"})
    settings = SimpleNamespace(
        PLATFORM_RUNTIME_PROFILE="gcp",
        API_URL="https://api.valdrics.example",
        GCP_INTERNAL_ALLOWED_SERVICE_ACCOUNTS=[
            "tasks@valdrics.iam.gserviceaccount.com"
        ],
    )
    expected_invoker = SimpleNamespace(
        method="google_oidc",
        subject="service-account-subject",
        email="tasks@valdrics.iam.gserviceaccount.com",
    )

    with (
        patch("app.shared.core.config.get_settings", return_value=settings),
        patch(
            "app.shared.orchestration.security._verify_google_identity_token",
            return_value=expected_invoker,
        ) as verify_google_identity_token,
    ):
        invoker = await require_internal_platform_invocation(
            request=request,
        )

    verify_google_identity_token.assert_called_once_with(
        "signed-google-token",
        settings,
    )
    assert invoker is expected_invoker


def test_verify_google_identity_token_accepts_allowed_service_account() -> None:
    fake_requests_module = types.SimpleNamespace(Request=lambda: object())
    fake_id_token_module = types.SimpleNamespace(
        verify_token=lambda token, request, audience: {
            "sub": "service-account-subject",
            "email": "tasks@valdrics.iam.gserviceaccount.com",
            "email_verified": True,
        }
    )
    google_auth_module = types.ModuleType("google.auth")
    google_auth_transport_module = types.ModuleType("google.auth.transport")
    google_auth_transport_module.requests = fake_requests_module
    google_oauth2_module = types.ModuleType("google.oauth2")
    google_oauth2_module.id_token = fake_id_token_module

    settings = SimpleNamespace(
        GCP_INTERNAL_AUTH_AUDIENCE="https://api.valdrics.example",
        API_URL="https://api.valdrics.example",
        GCP_INTERNAL_ALLOWED_SERVICE_ACCOUNTS=[
            "tasks@valdrics.iam.gserviceaccount.com"
        ],
    )

    with patch.dict(
        sys.modules,
        {
            "google.auth": google_auth_module,
            "google.auth.transport": google_auth_transport_module,
            "google.auth.transport.requests": fake_requests_module,
            "google.oauth2": google_oauth2_module,
            "google.oauth2.id_token": fake_id_token_module,
        },
    ):
        invoker = _verify_google_identity_token("token", settings)

    assert invoker.method == "google_oidc"
    assert invoker.email == "tasks@valdrics.iam.gserviceaccount.com"


def test_verify_google_identity_token_rejects_unknown_service_account() -> None:
    fake_requests_module = types.SimpleNamespace(Request=lambda: object())
    fake_id_token_module = types.SimpleNamespace(
        verify_token=lambda token, request, audience: {
            "sub": "service-account-subject",
            "email": "other@valdrics.iam.gserviceaccount.com",
            "email_verified": True,
        }
    )
    google_auth_module = types.ModuleType("google.auth")
    google_auth_transport_module = types.ModuleType("google.auth.transport")
    google_auth_transport_module.requests = fake_requests_module
    google_oauth2_module = types.ModuleType("google.oauth2")
    google_oauth2_module.id_token = fake_id_token_module

    settings = SimpleNamespace(
        GCP_INTERNAL_AUTH_AUDIENCE="https://api.valdrics.example",
        API_URL="https://api.valdrics.example",
        GCP_INTERNAL_ALLOWED_SERVICE_ACCOUNTS=[
            "tasks@valdrics.iam.gserviceaccount.com"
        ],
    )

    with patch.dict(
        sys.modules,
        {
            "google.auth": google_auth_module,
            "google.auth.transport": google_auth_transport_module,
            "google.auth.transport.requests": fake_requests_module,
            "google.oauth2": google_oauth2_module,
            "google.oauth2.id_token": fake_id_token_module,
        },
    ):
        with pytest.raises(HTTPException, match="not allowed"):
            _verify_google_identity_token("token", settings)
