from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

import scripts.verify_pkg015_launch_gate as pkg015_verifier
from scripts.verify_pkg015_launch_gate import main, verify_pkg015_launch_gate


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _contract_payload(
    *, ecp004_status: str = "DONE", include_doc_tokens: bool = True
) -> dict[str, object]:
    documentation_tokens: list[str] = []
    if include_doc_tokens:
        documentation_tokens = [
            "PKG-015",
            "analytics-led",
            "economic-control-plane",
            "Recommended decision gate",
        ]
    return {
        "pkg015_launch_gate": {
            "documentation_tokens": documentation_tokens,
            "required_item_status": {
                "ECP-002": "DONE",
                "ECP-003": "DONE",
                "ECP-004": ecp004_status,
                "ECP-005": "DONE",
                "ECP-012": "DONE",
                "PKG-003": "DONE",
                "PKG-006": "DONE",
                "PKG-007": "DONE",
            },
            "required_runtime_gated_features": [
                "auto_remediation",
                "api_access",
                "policy_configuration",
                "escalation_workflow",
                "incident_integrations",
            ],
        }
    }


def _matrix_payload(*, policy_configuration_status: str = "runtime_gated") -> dict[str, object]:
    return {
        "captured_at": "2026-02-28T12:00:00Z",
        "features": {
            "auto_remediation": {"status": "runtime_gated", "evidence": ["app/shared/core/pricing.py"]},
            "api_access": {"status": "runtime_gated", "evidence": ["app/shared/core/pricing.py"]},
            "policy_configuration": {
                "status": policy_configuration_status,
                "evidence": ["app/shared/core/pricing.py"],
            },
            "escalation_workflow": {
                "status": "runtime_gated",
                "evidence": ["app/shared/core/pricing.py"],
            },
            "incident_integrations": {
                "status": "runtime_gated",
                "evidence": ["app/shared/core/pricing.py"],
            },
        },
    }


def test_verify_pkg015_launch_gate_accepts_valid_inputs(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    matrix_path = tmp_path / "matrix.json"
    contract_path.write_text(json.dumps(_contract_payload()), encoding="utf-8")
    matrix_path.write_text(json.dumps(_matrix_payload()), encoding="utf-8")

    assert (
        verify_pkg015_launch_gate(
            contract_path=contract_path,
            matrix_path=matrix_path,
        )
        == 0
    )


def test_verify_pkg015_launch_gate_rejects_not_done_required_item(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    matrix_path = tmp_path / "matrix.json"
    contract_path.write_text(
        json.dumps(_contract_payload(ecp004_status="IN_PROGRESS")), encoding="utf-8"
    )
    matrix_path.write_text(json.dumps(_matrix_payload()), encoding="utf-8")

    with pytest.raises(ValueError, match="required items not DONE"):
        verify_pkg015_launch_gate(
            contract_path=contract_path,
            matrix_path=matrix_path,
        )


def test_verify_pkg015_launch_gate_rejects_missing_documentation_tokens(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "contract.json"
    matrix_path = tmp_path / "matrix.json"
    contract_path.write_text(
        json.dumps(_contract_payload(include_doc_tokens=False)), encoding="utf-8"
    )
    matrix_path.write_text(json.dumps(_matrix_payload()), encoding="utf-8")

    with pytest.raises(ValueError, match="documentation_tokens"):
        verify_pkg015_launch_gate(
            contract_path=contract_path,
            matrix_path=matrix_path,
        )


def test_verify_pkg015_launch_gate_rejects_non_runtime_gated_features(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "contract.json"
    matrix_path = tmp_path / "matrix.json"
    contract_path.write_text(json.dumps(_contract_payload()), encoding="utf-8")
    matrix_path.write_text(
        json.dumps(_matrix_payload(policy_configuration_status="catalog_only")),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="must be runtime_gated"):
        verify_pkg015_launch_gate(
            contract_path=contract_path,
            matrix_path=matrix_path,
        )


def test_main_accepts_valid_inputs(tmp_path: Path) -> None:
    contract_path = tmp_path / "contract.json"
    matrix_path = tmp_path / "matrix.json"
    contract_path.write_text(json.dumps(_contract_payload()), encoding="utf-8")
    matrix_path.write_text(json.dumps(_matrix_payload()), encoding="utf-8")

    assert (
        main(
            [
                "--contract-path",
                str(contract_path),
                "--matrix-path",
                str(matrix_path),
            ]
        )
        == 0
    )


def test_main_resolves_relative_paths_from_repo_root_when_run_outside_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    contract_path = repo_root / "docs" / "ops" / "contract.json"
    matrix_path = repo_root / "docs" / "ops" / "matrix.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(_contract_payload()), encoding="utf-8")
    matrix_path.write_text(json.dumps(_matrix_payload()), encoding="utf-8")

    monkeypatch.setattr(pkg015_verifier, "_repo_root", lambda: repo_root)

    old_cwd = Path.cwd()
    try:
        os.chdir(tmp_path)
        assert (
            main(
                [
                    "--contract-path",
                    "docs/ops/contract.json",
                    "--matrix-path",
                    "docs/ops/matrix.json",
                ]
            )
            == 0
        )
    finally:
        os.chdir(old_cwd)


def test_main_rejects_relative_repo_escape(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.setattr(pkg015_verifier, "_repo_root", lambda: repo_root)

    assert main(["--contract-path", "../escape/contract.json"]) == 2


def test_main_rejects_directory_inputs(
    tmp_path: Path,
) -> None:
    contract_dir = tmp_path / "contract-dir"
    contract_dir.mkdir()
    matrix_dir = tmp_path / "matrix-dir"
    matrix_dir.mkdir()

    assert (
        main(["--contract-path", str(contract_dir), "--matrix-path", str(matrix_dir)])
        == 2
    )
