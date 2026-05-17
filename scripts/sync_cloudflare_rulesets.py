#!/usr/bin/env python3
"""Synchronize Valdrics-managed Cloudflare rulesets without clobbering existing rules."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

CLOUDFLARE_API_BASE_URL = "https://api.cloudflare.com/client/v4"
CLOUDFLARE_API_USER_AGENT = "CloudSentinel-AI-cloudflare-rulesets/1.0"


@dataclass(frozen=True)
class ManagedRule:
    phase: str
    ref: str
    payload: dict[str, Any]
    position: dict[str, str] | None = None
    after_ref: str | None = None


TERRAFORM_RULESET_ADDRESSES = {
    "http_request_firewall_custom": "cloudflare_ruleset.api_internal_block",
    "http_ratelimit": "cloudflare_ruleset.api_rate_limit",
}


def _api_hostname_from_url(api_url: str) -> str:
    parsed = urlparse(str(api_url or "").strip())
    hostname = str(parsed.hostname or "").strip().lower()
    if parsed.scheme != "https" or not hostname:
        raise ValueError("--api-url must be a concrete https:// API origin")
    return hostname


def _desired_rules(
    *,
    api_hostname: str,
    rate_limit_requests_per_period: int,
    rate_limit_period_seconds: int,
    rate_limit_mitigation_timeout_seconds: int,
) -> list[ManagedRule]:
    health_probe_skip = ManagedRule(
        phase="http_request_firewall_custom",
        ref="valdrics-health-probe-skip",
        position={"before": ""},
        payload={
            "ref": "valdrics-health-probe-skip",
            "action": "skip",
            "enabled": True,
            "description": "Health probes must bypass Cloudflare browser challenges.",
            "expression": (
                f'(http.host eq "{api_hostname}" and '
                '(http.request.uri.path eq "/health" or '
                'http.request.uri.path eq "/health/live"))'
            ),
            "action_parameters": {
                "phases": [
                    "http_ratelimit",
                    "http_request_firewall_managed",
                    "http_request_sbfm",
                ],
                "products": [
                    "bic",
                    "rateLimit",
                    "securityLevel",
                    "uaBlock",
                    "waf",
                    "zoneLockdown",
                ],
            },
        },
    )
    internal_api_block = ManagedRule(
        phase="http_request_firewall_custom",
        ref="valdrics-internal-api-block",
        after_ref=health_probe_skip.ref,
        payload={
            "ref": "valdrics-internal-api-block",
            "action": "block",
            "enabled": True,
            "description": (
                "Internal scheduler and task endpoints are not internet-facing."
            ),
            "expression": (
                f'(http.host eq "{api_hostname}" and '
                'starts_with(http.request.uri.path, "/api/v1/internal/"))'
            ),
        },
    )
    public_api_rate_limit = ManagedRule(
        phase="http_ratelimit",
        ref="valdrics-public-api-rate-limit",
        payload={
            "ref": "valdrics-public-api-rate-limit",
            "action": "block",
            "enabled": True,
            "description": "Public API burst protection at the Cloudflare edge.",
            "expression": f'(http.host eq "{api_hostname}")',
            "ratelimit": {
                "characteristics": ["cf.colo.id", "ip.src"],
                "requests_per_period": rate_limit_requests_per_period,
                "period": rate_limit_period_seconds,
                "mitigation_timeout": rate_limit_mitigation_timeout_seconds,
            },
        },
    )
    return [health_probe_skip, internal_api_block, public_api_rate_limit]


class CloudflareRulesetsClient:
    def __init__(self, *, api_token: str) -> None:
        normalized_token = str(api_token or "").strip()
        if not normalized_token:
            raise ValueError("CLOUDFLARE_API_TOKEN is required")
        self._api_token = normalized_token

    def request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        allow_404: bool = False,
    ) -> Any:
        data = None
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._api_token}",
            "User-Agent": CLOUDFLARE_API_USER_AGENT,
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        url = f"{CLOUDFLARE_API_BASE_URL}{path}"
        request = Request(url, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            if allow_404 and exc.code == 404:
                return None
            raise RuntimeError(
                f"Cloudflare API returned HTTP {exc.code} for {method} {path}: {body}"
            ) from exc
        except URLError as exc:
            raise RuntimeError(
                f"Cloudflare API request failed for {method} {path}: {exc}"
            ) from exc

        if not isinstance(body, dict) or not body.get("success", False):
            raise RuntimeError(
                "Cloudflare API returned an unsuccessful response for "
                f"{method} {path}: {json.dumps(body, sort_keys=True)}"
            )
        return body.get("result")

    def entrypoint_ruleset(self, *, zone_id: str, phase: str) -> dict[str, Any] | None:
        result = self.request(
            "GET",
            f"/zones/{quote(zone_id)}/rulesets/phases/{quote(phase)}/entrypoint",
            allow_404=True,
        )
        if result is None:
            return None
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected Cloudflare ruleset payload for {phase}")
        return result

    def create_entrypoint_ruleset(
        self,
        *,
        zone_id: str,
        phase: str,
        rules: list[ManagedRule],
    ) -> dict[str, Any]:
        payload = {
            "description": "Valdrics-managed zone entrypoint rules.",
            "rules": [rule.payload for rule in rules],
        }
        result = self.request(
            "PUT",
            f"/zones/{quote(zone_id)}/rulesets/phases/{quote(phase)}/entrypoint",
            payload=payload,
        )
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected Cloudflare create payload for {phase}")
        return result

    def upsert_rule(
        self,
        *,
        zone_id: str,
        ruleset: dict[str, Any],
        desired_rule: ManagedRule,
    ) -> dict[str, Any]:
        ruleset_id = str(ruleset.get("id") or "").strip()
        if not ruleset_id:
            raise RuntimeError(
                f"Cloudflare ruleset for {desired_rule.phase} has no ruleset id"
            )

        body = dict(desired_rule.payload)
        position = desired_rule.position
        if desired_rule.after_ref:
            after_id = _find_rule_id(ruleset, desired_rule.after_ref)
            if after_id:
                position = {"after": after_id}
        if position is not None:
            body["position"] = position

        existing_rule_id = _find_rule_id(
            ruleset,
            desired_rule.ref,
            description=str(desired_rule.payload.get("description") or ""),
        )
        if existing_rule_id:
            method = "PATCH"
            path = (
                f"/zones/{quote(zone_id)}"
                f"/rulesets/{quote(ruleset_id)}/rules/{quote(existing_rule_id)}"
            )
        else:
            method = "POST"
            path = (
                f"/zones/{quote(zone_id)}"
                f"/rulesets/{quote(ruleset_id)}/rules"
            )

        result = self.request(method, path, payload=body)
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Unexpected Cloudflare rule upsert payload for {desired_rule.ref}"
            )
        return result


def _rules_for_phase(rules: list[ManagedRule], phase: str) -> list[ManagedRule]:
    return [rule for rule in rules if rule.phase == phase]


def _find_rule_id(
    ruleset: dict[str, Any],
    ref: str,
    *,
    description: str = "",
) -> str:
    normalized_description = str(description or "").strip()
    for rule in ruleset.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        if str(rule.get("ref") or "").strip() == ref:
            return str(rule.get("id") or "").strip()
        if (
            normalized_description
            and str(rule.get("description") or "").strip() == normalized_description
        ):
            return str(rule.get("id") or "").strip()
    return ""


def sync_rulesets(
    *,
    cloudflare_zone_id: str,
    api_url: str,
    rate_limit_requests_per_period: int,
    rate_limit_period_seconds: int,
    rate_limit_mitigation_timeout_seconds: int,
    cloudflare_api_token: str,
) -> dict[str, str]:
    zone_id = str(cloudflare_zone_id or "").strip()
    if not zone_id:
        raise ValueError("--cloudflare-zone-id is required")
    api_hostname = _api_hostname_from_url(api_url)
    rules = _desired_rules(
        api_hostname=api_hostname,
        rate_limit_requests_per_period=rate_limit_requests_per_period,
        rate_limit_period_seconds=rate_limit_period_seconds,
        rate_limit_mitigation_timeout_seconds=rate_limit_mitigation_timeout_seconds,
    )
    client = CloudflareRulesetsClient(api_token=cloudflare_api_token)
    synced: dict[str, str] = {}

    for phase in TERRAFORM_RULESET_ADDRESSES:
        phase_rules = _rules_for_phase(rules, phase)
        ruleset = client.entrypoint_ruleset(zone_id=zone_id, phase=phase)
        if ruleset is None:
            ruleset = client.create_entrypoint_ruleset(
                zone_id=zone_id,
                phase=phase,
                rules=phase_rules,
            )
            print(
                "[cloudflare-rulesets] created "
                f"zone_id={zone_id} phase={phase} ruleset_id={ruleset.get('id')}"
            )
        else:
            for rule in phase_rules:
                ruleset = client.upsert_rule(
                    zone_id=zone_id,
                    ruleset=ruleset,
                    desired_rule=rule,
                )
            print(
                "[cloudflare-rulesets] synced "
                f"zone_id={zone_id} phase={phase} ruleset_id={ruleset.get('id')}"
            )
        ruleset_id = str(ruleset.get("id") or "").strip()
        if not ruleset_id:
            raise RuntimeError(f"Cloudflare ruleset for {phase} has no id")
        synced[phase] = ruleset_id

    return synced


def _terraform_state_has_resource(*, terraform_dir: Path, address: str) -> bool:
    completed = subprocess.run(
        ["terraform", f"-chdir={terraform_dir.as_posix()}", "state", "show", address],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def import_terraform_ruleset_state(
    *,
    terraform_dir: Path,
    terraform_var_file: Path,
    cloudflare_zone_id: str,
    rulesets_by_phase: dict[str, str],
) -> None:
    zone_id = str(cloudflare_zone_id or "").strip()
    var_file = terraform_var_file.resolve()
    for phase, address in TERRAFORM_RULESET_ADDRESSES.items():
        ruleset_id = str(rulesets_by_phase.get(phase) or "").strip()
        if not ruleset_id:
            raise RuntimeError(f"cannot import {address}: no ruleset id for {phase}")
        if _terraform_state_has_resource(terraform_dir=terraform_dir, address=address):
            print(f"[cloudflare-rulesets] terraform state already has {address}")
            continue
        import_id = f"zones/{zone_id}/{ruleset_id}"
        subprocess.run(
            [
                "terraform",
                f"-chdir={terraform_dir.as_posix()}",
                "import",
                f"-var-file={var_file.as_posix()}",
                address,
                import_id,
            ],
            check=True,
        )
        print(
            "[cloudflare-rulesets] imported "
            f"address={address} import_id={import_id}"
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Upsert Valdrics Cloudflare rules and optionally import Terraform state."
    )
    parser.add_argument("--cloudflare-zone-id", required=True)
    parser.add_argument("--api-url", required=True)
    parser.add_argument(
        "--rate-limit-requests-per-period",
        type=int,
        default=50,
    )
    parser.add_argument(
        "--rate-limit-period-seconds",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--rate-limit-mitigation-timeout-seconds",
        type=int,
        default=10,
    )
    parser.add_argument("--terraform-dir", type=Path)
    parser.add_argument("--terraform-var-file", type=Path)
    parser.add_argument("--import-terraform-state", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    synced = sync_rulesets(
        cloudflare_zone_id=str(args.cloudflare_zone_id),
        api_url=str(args.api_url),
        rate_limit_requests_per_period=int(args.rate_limit_requests_per_period),
        rate_limit_period_seconds=int(args.rate_limit_period_seconds),
        rate_limit_mitigation_timeout_seconds=int(
            args.rate_limit_mitigation_timeout_seconds
        ),
        cloudflare_api_token=os.environ.get("CLOUDFLARE_API_TOKEN", ""),
    )
    if args.import_terraform_state:
        if args.terraform_dir is None or args.terraform_var_file is None:
            raise ValueError(
                "--terraform-dir and --terraform-var-file are required with "
                "--import-terraform-state"
            )
        import_terraform_ruleset_state(
            terraform_dir=args.terraform_dir,
            terraform_var_file=args.terraform_var_file,
            cloudflare_zone_id=str(args.cloudflare_zone_id),
            rulesets_by_phase=synced,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
