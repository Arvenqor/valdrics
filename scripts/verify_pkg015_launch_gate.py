#!/usr/bin/env python3
"""Verify PKG-015 B-launch readiness gate criteria."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.env_generation_common import repo_root_for as _repo_root_for

REQUIRED_CONTRACT_SECTION = "pkg015_launch_gate"


def _repo_root() -> Path:
    return _repo_root_for(__file__)


def _resolve_repo_relative_file(*, repo_root: Path, path: Path, label: str) -> Path:
    raw = Path(path).expanduser()
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (repo_root / raw).resolve()
        try:
            resolved.relative_to(repo_root.resolve())
        except ValueError as exc:
            raise ValueError(f"{label} must stay within repo root when relative") from exc
    if resolved.exists() and not resolved.is_file():
        raise ValueError(f"{label} must be a file: {resolved}")
    return resolved


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required file does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Required file path must be a file: {path}")
    return path.read_text(encoding="utf-8")


def _load_contract_section(path: Path) -> dict[str, Any]:
    payload = json.loads(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError("Release gate contract payload must be an object")
    section = payload.get(REQUIRED_CONTRACT_SECTION)
    if not isinstance(section, dict):
        raise ValueError(
            f"Release gate contract must include object section: {REQUIRED_CONTRACT_SECTION}"
        )
    return section


def _load_matrix(path: Path) -> dict[str, Any]:
    payload = json.loads(_read_text(path))
    if not isinstance(payload, dict):
        raise ValueError("Feature enforceability matrix payload must be an object")
    return payload


def _verify_required_item_statuses(statuses: dict[str, str]) -> None:
    missing = [item_id for item_id, status in statuses.items() if not status]
    if missing:
        raise ValueError(f"Release gate contract missing PKG-015 statuses for: {missing}")
    not_done = [item_id for item_id, status in statuses.items() if status != "DONE"]
    if not_done:
        raise ValueError(f"PKG-015 launch gate blocked; required items not DONE: {not_done}")


def _verify_runtime_gated_features(
    matrix_payload: dict[str, Any], *, required_features: tuple[str, ...]
) -> None:
    features = matrix_payload.get("features")
    if not isinstance(features, dict):
        raise ValueError("Feature enforceability matrix must contain features object")
    missing: list[str] = []
    not_runtime_gated: list[str] = []
    for feature in required_features:
        feature_payload = features.get(feature)
        if not isinstance(feature_payload, dict):
            missing.append(feature)
            continue
        status = str(feature_payload.get("status", "")).strip().lower()
        if status != "runtime_gated":
            not_runtime_gated.append(feature)
    if missing:
        raise ValueError(
            "Feature enforceability matrix missing required control-plane features: "
            f"{missing}"
        )
    if not_runtime_gated:
        raise ValueError(
            "PKG-015 launch gate blocked; control-plane features must be runtime_gated: "
            f"{not_runtime_gated}"
        )


def verify_pkg015_launch_gate(*, contract_path: Path, matrix_path: Path) -> int:
    contract = _load_contract_section(contract_path)

    documentation_tokens = contract.get("documentation_tokens")
    if not isinstance(documentation_tokens, list) or not documentation_tokens:
        raise ValueError("Release gate contract missing PKG-015 documentation_tokens")
    for token in documentation_tokens:
        if not isinstance(token, str) or not token.strip():
            raise ValueError("Release gate contract contains invalid PKG-015 documentation token")

    statuses_raw = contract.get("required_item_status")
    if not isinstance(statuses_raw, dict) or not statuses_raw:
        raise ValueError("Release gate contract missing PKG-015 required_item_status")
    statuses = {
        str(item_id).strip().upper(): str(status).strip().upper()
        for item_id, status in statuses_raw.items()
    }
    _verify_required_item_statuses(statuses)

    required_features_raw = contract.get("required_runtime_gated_features")
    if not isinstance(required_features_raw, list) or not required_features_raw:
        raise ValueError(
            "Release gate contract missing PKG-015 required_runtime_gated_features"
        )
    required_features = tuple(str(feature).strip() for feature in required_features_raw)
    if any(not feature for feature in required_features):
        raise ValueError(
            "Release gate contract contains invalid PKG-015 runtime-gated feature"
        )
    _verify_runtime_gated_features(
        _load_matrix(matrix_path), required_features=required_features
    )

    print(
        "PKG-015 launch gate verified: "
        f"items={len(statuses)} runtime_gated_features={len(required_features)}"
    )
    return 0


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify PKG-015 B-launch readiness gate criteria."
    )
    parser.add_argument(
        "--contract-path",
        default="docs/ops/enforcement_release_gate_contract.json",
        help="Release gate contract JSON path.",
    )
    parser.add_argument(
        "--matrix-path",
        default="docs/ops/feature_enforceability_matrix.json",
        help="Feature enforceability matrix JSON path.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    repo_root = _repo_root()
    try:
        contract_path = _resolve_repo_relative_file(
            repo_root=repo_root,
            path=Path(args.contract_path),
            label="contract_path",
        )
        matrix_path = _resolve_repo_relative_file(
            repo_root=repo_root,
            path=Path(args.matrix_path),
            label="matrix_path",
        )
        return verify_pkg015_launch_gate(
            contract_path=contract_path,
            matrix_path=matrix_path,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"[pkg015-launch-gate] failed: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
