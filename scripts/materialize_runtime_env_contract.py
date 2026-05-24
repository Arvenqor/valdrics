#!/usr/bin/env python3
"""Materialize GitHub managed-runtime JSON into an env file for deployment."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.preflight_runtime_env_contract import (
    DEFAULT_PLAIN_ENV_NAME,
    DEFAULT_SECRET_ENV_NAME,
    _load_payload_from_env,
    _render_env_payload,
    apply_paystack_secret_overlay,
    paystack_secret_overlay_from_env,
)
from scripts.managed_deployment_contract import runtime_json_classification_errors


def materialize_runtime_env_contract(
    *,
    plain: dict[str, str],
    secret: dict[str, str],
    output_path: Path,
    secret_overlay: dict[str, str] | None = None,
) -> Path:
    secret = apply_paystack_secret_overlay(secret, secret_overlay)
    overlap = sorted(set(plain) & set(secret))
    if overlap:
        raise ValueError(
            "RUNTIME_PLAIN_ENV_JSON and RUNTIME_SECRET_ENV_JSON must not share keys: "
            + ", ".join(overlap)
        )

    classification_errors = runtime_json_classification_errors(plain, secret)
    if classification_errors:
        raise ValueError("\n".join(classification_errors))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_env_payload({**plain, **secret}), encoding="utf-8")
    return output_path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--environment",
        required=True,
        choices=("staging", "production"),
        help="Managed release environment being materialized.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Destination env file path.",
    )
    parser.add_argument(
        "--runtime-plain-env-name",
        default=DEFAULT_PLAIN_ENV_NAME,
        help="Environment variable containing the plain managed runtime JSON.",
    )
    parser.add_argument(
        "--runtime-secret-env-name",
        default=DEFAULT_SECRET_ENV_NAME,
        help="Environment variable containing the secret managed runtime JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        output_path = materialize_runtime_env_contract(
            plain=_load_payload_from_env(args.runtime_plain_env_name),
            secret=_load_payload_from_env(args.runtime_secret_env_name),
            output_path=args.output_path,
            secret_overlay=paystack_secret_overlay_from_env(),
        )
    except (OSError, ValueError) as exc:
        print(f"::error title=Managed runtime env materialization failed::{exc}")
        return 1

    print(
        "[managed-runtime-env-materializer] ok "
        f"environment={args.environment} output_path={output_path.as_posix()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
