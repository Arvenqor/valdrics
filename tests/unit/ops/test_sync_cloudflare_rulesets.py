from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts import sync_cloudflare_rulesets


def test_desired_rules_match_valdrics_api_controls() -> None:
    rules = sync_cloudflare_rulesets._desired_rules(
        api_hostname="api.valdrics.com",
        rate_limit_requests_per_period=50,
        rate_limit_period_seconds=10,
        rate_limit_mitigation_timeout_seconds=10,
    )

    refs = {rule.ref for rule in rules}
    assert refs == {
        "valdrics-health-probe-skip",
        "valdrics-internal-api-block",
        "valdrics-public-api-rate-limit",
    }
    assert rules[0].payload["action"] == "skip"
    assert "/health/live" in rules[0].payload["expression"]
    assert rules[1].after_ref == "valdrics-health-probe-skip"
    assert "/api/v1/internal/" in rules[1].payload["expression"]
    assert rules[2].payload["ratelimit"] == {
        "characteristics": ["cf.colo.id", "ip.src"],
        "requests_per_period": 50,
        "period": 10,
        "mitigation_timeout": 10,
    }


def test_sync_rulesets_creates_missing_entrypoints(monkeypatch: pytest.MonkeyPatch) -> None:
    created: list[tuple[str, list[str]]] = []

    class FakeClient:
        def __init__(self, *, api_token: str) -> None:
            assert api_token == "token"

        def entrypoint_ruleset(
            self, *, zone_id: str, phase: str
        ) -> dict[str, Any] | None:
            assert zone_id == "zone-id"
            assert phase in sync_cloudflare_rulesets.TERRAFORM_RULESET_ADDRESSES
            return None

        def create_entrypoint_ruleset(
            self,
            *,
            zone_id: str,
            phase: str,
            rules: list[sync_cloudflare_rulesets.ManagedRule],
        ) -> dict[str, Any]:
            created.append((phase, [rule.ref for rule in rules]))
            return {"id": f"{phase}-ruleset"}

    monkeypatch.setattr(sync_cloudflare_rulesets, "CloudflareRulesetsClient", FakeClient)

    assert sync_cloudflare_rulesets.sync_rulesets(
        cloudflare_zone_id="zone-id",
        api_url="https://api.valdrics.com",
        rate_limit_requests_per_period=50,
        rate_limit_period_seconds=10,
        rate_limit_mitigation_timeout_seconds=10,
        cloudflare_api_token="token",
    ) == {
        "http_request_firewall_custom": "http_request_firewall_custom-ruleset",
        "http_ratelimit": "http_ratelimit-ruleset",
    }
    assert created == [
        (
            "http_request_firewall_custom",
            ["valdrics-health-probe-skip", "valdrics-internal-api-block"],
        ),
        ("http_ratelimit", ["valdrics-public-api-rate-limit"]),
    ]


def test_import_terraform_ruleset_state_uses_zone_scoped_import_ids(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[list[str]] = []

    monkeypatch.setattr(
        sync_cloudflare_rulesets,
        "_terraform_state_has_resource",
        lambda *, terraform_dir, address: False,
    )

    def fake_run(command: list[str], *, check: bool) -> None:
        assert check is True
        calls.append(command)

    monkeypatch.setattr(sync_cloudflare_rulesets.subprocess, "run", fake_run)

    var_file = tmp_path / "terraform.runtime.auto.tfvars.json"
    var_file.write_text("{}", encoding="utf-8")
    sync_cloudflare_rulesets.import_terraform_ruleset_state(
        terraform_dir=tmp_path / "terraform",
        terraform_var_file=var_file,
        cloudflare_zone_id="zone-id",
        rulesets_by_phase={
            "http_request_firewall_custom": "firewall-ruleset-id",
            "http_ratelimit": "rate-ruleset-id",
        },
    )

    assert calls[0][-2:] == [
        "cloudflare_ruleset.api_internal_block",
        "zones/zone-id/firewall-ruleset-id",
    ]
    assert calls[1][-2:] == [
        "cloudflare_ruleset.api_rate_limit",
        "zones/zone-id/rate-ruleset-id",
    ]


def test_sync_rulesets_rejects_non_https_api_url() -> None:
    with pytest.raises(ValueError, match="https"):
        sync_cloudflare_rulesets.sync_rulesets(
            cloudflare_zone_id="zone-id",
            api_url="http://localhost:8000",
            rate_limit_requests_per_period=50,
            rate_limit_period_seconds=10,
            rate_limit_mitigation_timeout_seconds=10,
            cloudflare_api_token="token",
        )
