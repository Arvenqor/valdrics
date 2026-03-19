from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

import scripts.generate_pkg_fin_policy_decisions as generator
from scripts.generate_pkg_fin_policy_decisions import main


def _telemetry_payload() -> dict[str, object]:
    return {
        "window": {
            "start": "2026-02-01T00:00:00Z",
            "end": "2026-02-28T23:59:59Z",
            "label": "2026-02",
        },
        "pricing_reference": {
            "starter": {"annual_monthly_factor": 0.9},
            "growth": {"annual_monthly_factor": 0.9},
            "pro": {"annual_monthly_factor": 0.9},
            "enterprise": {"annual_monthly_factor": 0.9},
        },
        "tier_revenue_inputs": [
            {"tier": "starter", "gross_mrr_usd": 1000.0},
            {"tier": "growth", "gross_mrr_usd": 2000.0},
            {"tier": "pro", "gross_mrr_usd": 3000.0},
            {"tier": "enterprise", "gross_mrr_usd": 4000.0},
        ],
        "tier_llm_usage": [
            {"tier": "starter", "total_cost_usd": 100.0},
            {"tier": "growth", "total_cost_usd": 150.0},
            {"tier": "pro", "total_cost_usd": 200.0},
            {"tier": "enterprise", "total_cost_usd": 250.0},
        ],
        "tier_subscription_snapshot": [
            {"tier": "starter", "active_subscriptions": 10},
            {"tier": "growth", "active_subscriptions": 20},
            {"tier": "pro", "active_subscriptions": 30},
            {"tier": "enterprise", "active_subscriptions": 40},
        ],
    }


def test_generate_pkg_fin_policy_decisions_rejects_input_output_collision(
    tmp_path: Path,
) -> None:
    telemetry = tmp_path / "telemetry.json"
    telemetry.write_text(json.dumps(_telemetry_payload()), encoding="utf-8")

    with pytest.raises(ValueError, match="telemetry_snapshot_path and output must be different files"):
        main(
            [
                "--output",
                str(telemetry),
                "--telemetry-snapshot-path",
                str(telemetry),
            ]
        )


def test_generate_pkg_fin_policy_decisions_verifies_telemetry_snapshot_first(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    telemetry = tmp_path / "telemetry.json"
    output = tmp_path / "pkg_fin_policy_decisions.json"
    telemetry.write_text(json.dumps(_telemetry_payload()), encoding="utf-8")

    verify_snapshot_calls: list[dict[str, object]] = []
    verify_evidence_calls: list[dict[str, object]] = []

    def _fake_verify_snapshot(**kwargs: object) -> int:
        verify_snapshot_calls.append(kwargs)
        return 0

    def _fake_verify_evidence(**kwargs: object) -> int:
        verify_evidence_calls.append(kwargs)
        return 0

    monkeypatch.setattr(generator, "verify_snapshot", _fake_verify_snapshot)
    monkeypatch.setattr(generator, "verify_evidence", _fake_verify_evidence)

    assert (
        main(
            [
                "--output",
                str(output),
                "--telemetry-snapshot-path",
                str(telemetry),
            ]
        )
        == 0
    )

    assert verify_snapshot_calls == [
        {
            "snapshot_path": telemetry,
            "max_artifact_age_hours": 24.0,
        }
    ]
    assert verify_evidence_calls == [
        {
            "evidence_path": output,
            "max_artifact_age_hours": 4.0,
        }
    ]


@pytest.mark.parametrize(
    ("field_path", "value", "expected_message"),
    [
        (("tier_revenue_inputs", 0, "gross_mrr_usd"), math.nan, "tier_revenue_inputs.starter.gross_mrr_usd must be finite"),
        (("tier_llm_usage", 1, "total_cost_usd"), math.inf, "tier_llm_usage.growth.total_cost_usd must be finite"),
        (
            ("pricing_reference", "pro", "annual_monthly_factor"),
            -math.inf,
            "pricing_reference.pro.annual_monthly_factor must be finite",
        ),
    ],
)
def test_generate_pkg_fin_policy_decisions_rejects_non_finite_finance_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field_path: tuple[object, ...],
    value: float,
    expected_message: str,
) -> None:
    telemetry_payload = _telemetry_payload()
    mutated: object = telemetry_payload
    for path_part in field_path[:-1]:
        mutated = mutated[path_part]  # type: ignore[index]
    mutated[field_path[-1]] = value  # type: ignore[index]

    telemetry = tmp_path / "telemetry.json"
    output = tmp_path / "pkg_fin_policy_decisions.json"
    telemetry.write_text(json.dumps(telemetry_payload), encoding="utf-8")

    monkeypatch.setattr(generator, "verify_snapshot", lambda **_: 0)
    monkeypatch.setattr(generator, "verify_evidence", lambda **_: 0)

    with pytest.raises(ValueError, match=expected_message):
        main(
            [
                "--output",
                str(output),
                "--telemetry-snapshot-path",
                str(telemetry),
            ]
        )
