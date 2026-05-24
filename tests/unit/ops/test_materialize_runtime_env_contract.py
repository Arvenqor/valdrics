from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.materialize_runtime_env_contract import (
    main,
    materialize_runtime_env_contract,
)


def _plain_payload() -> dict[str, str]:
    return {
        "ENVIRONMENT": "production",
        "API_URL": "https://api.example.com",
        "FRONTEND_URL": "https://app.example.com",
        "PAYSTACK_ACTIVATION_PENDING": "false",
    }


def _secret_payload() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@db.example.com/postgres",
        "PAYSTACK_SECRET_KEY": "",
        "PAYSTACK_PUBLIC_KEY": "",
    }


def test_materialize_runtime_env_contract_applies_paystack_secret_overlay(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "production.env"

    materialize_runtime_env_contract(
        plain=_plain_payload(),
        secret=_secret_payload(),
        output_path=output_path,
        secret_overlay={
            "PAYSTACK_SECRET_KEY": "sk_live_overlay_paystack_secret",
            "PAYSTACK_PUBLIC_KEY": "pk_live_overlay_paystack_public",
        },
    )

    rendered = output_path.read_text(encoding="utf-8")
    assert "PAYSTACK_SECRET_KEY=sk_live_overlay_paystack_secret" in rendered
    assert "PAYSTACK_PUBLIC_KEY=pk_live_overlay_paystack_public" in rendered
    assert "PAYSTACK_ACTIVATION_PENDING=false" in rendered


def test_materialize_runtime_env_contract_rejects_classification_errors(
    tmp_path: Path,
) -> None:
    plain = _plain_payload()
    plain["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db.example.com/postgres"
    secret = _secret_payload()
    secret.pop("DATABASE_URL")

    with pytest.raises(ValueError, match="secret-classified keys"):
        materialize_runtime_env_contract(
            plain=plain,
            secret=secret,
            output_path=tmp_path / "production.env",
        )


def test_materialize_runtime_env_contract_cli_uses_github_annotation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plain = _plain_payload()
    plain["DATABASE_URL"] = "postgresql+asyncpg://user:pass@db.example.com/postgres"
    secret = _secret_payload()
    secret.pop("DATABASE_URL")
    monkeypatch.setenv("RUNTIME_PLAIN_ENV_JSON", json.dumps(plain))
    monkeypatch.setenv("RUNTIME_SECRET_ENV_JSON", json.dumps(secret))

    exit_code = main(
        [
            "--environment",
            "production",
            "--output-path",
            (tmp_path / "production.env").as_posix(),
        ]
    )

    assert exit_code == 1
    assert (
        "::error title=Managed runtime env materialization failed::"
        in capsys.readouterr().out
    )


def test_materialize_runtime_env_contract_cli_applies_environment_paystack_overlay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("RUNTIME_PLAIN_ENV_JSON", json.dumps(_plain_payload()))
    monkeypatch.setenv("RUNTIME_SECRET_ENV_JSON", json.dumps(_secret_payload()))
    monkeypatch.setenv("PAYSTACK_SECRET_KEY", "sk_live_overlay_paystack_secret")
    monkeypatch.setenv("PAYSTACK_PUBLIC_KEY", "pk_live_overlay_paystack_public")

    exit_code = main(
        [
            "--environment",
            "staging",
            "--output-path",
            (tmp_path / "staging.env").as_posix(),
        ]
    )

    assert exit_code == 0
    rendered = (tmp_path / "staging.env").read_text(encoding="utf-8")
    assert "PAYSTACK_SECRET_KEY=sk_live_overlay_paystack_secret" in rendered
    assert "PAYSTACK_PUBLIC_KEY=pk_live_overlay_paystack_public" in rendered
    assert "[managed-runtime-env-materializer] ok" in capsys.readouterr().out
