#!/usr/bin/env python3
"""Inspect or repair Supabase Auth settings needed for production signup."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.generate_managed_deployment_artifacts import supabase_project_ref_from_url

SUPABASE_API_BASE_URL = "https://api.supabase.com"
SUPABASE_API_USER_AGENT = "CloudSentinel-AI-supabase-auth-config/1.0"


def _load_runtime_plain_env(raw_payload: str) -> dict[str, str]:
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"runtime plain env JSON is invalid: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("runtime plain env JSON must be an object")
    return {str(key): str(value) for key, value in payload.items()}


def _request_json(
    url: str,
    *,
    access_token: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}",
        "User-Agent": SUPABASE_API_USER_AGENT,
    }
    if payload is not None:
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, headers=headers, method=method, data=data)
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8").strip()
            return json.loads(body) if body else {}
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Supabase API returned HTTP {exc.code} for {url}: {body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Supabase API request failed for {url}: {exc}") from exc


def _normalize_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _callback_url(frontend_url: str) -> str:
    return f"{_normalize_url(frontend_url)}/auth/callback"


def _parse_redirect_allow_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _render_redirect_allow_list(value: Any, entries: list[str]) -> Any:
    deduped = list(dict.fromkeys(entry.strip() for entry in entries if entry.strip()))
    if isinstance(value, str):
        return ",".join(deduped)
    return deduped


def _redirect_allowed(target_url: str, allow_list: list[str]) -> bool:
    normalized_target = _normalize_url(target_url)
    for pattern in allow_list:
        normalized_pattern = _normalize_url(pattern)
        if normalized_pattern == normalized_target:
            return True
        if any(token in normalized_pattern for token in ("*", "?", "[")):
            if fnmatch.fnmatchcase(normalized_target, normalized_pattern):
                return True
    return False


def _auth_config_url(project_ref: str) -> str:
    return f"{SUPABASE_API_BASE_URL}/v1/projects/{quote(project_ref)}/config/auth"


def _build_patch(config: dict[str, Any], *, frontend_url: str) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    if config.get("disable_signup") is not False:
        patch["disable_signup"] = False

    normalized_frontend = _normalize_url(frontend_url)
    if normalized_frontend and _normalize_url(str(config.get("site_url") or "")) != normalized_frontend:
        patch["site_url"] = normalized_frontend

    redirect_key = "uri_allow_list"
    current_allow_list_raw = config.get(redirect_key)
    current_allow_list = _parse_redirect_allow_list(current_allow_list_raw)
    expected_callback_url = _callback_url(normalized_frontend)
    if normalized_frontend and not _redirect_allowed(expected_callback_url, current_allow_list):
        patch[redirect_key] = _render_redirect_allow_list(
            current_allow_list_raw,
            [*current_allow_list, expected_callback_url],
        )
    return patch


def _build_report(
    *,
    environment: str,
    project_ref: str,
    frontend_url: str,
    config: dict[str, Any],
    patch: dict[str, Any],
    changed: bool,
) -> dict[str, Any]:
    redirect_allow_list = _parse_redirect_allow_list(config.get("uri_allow_list"))
    expected_callback_url = _callback_url(frontend_url)
    return {
        "environment": environment,
        "project_ref": project_ref,
        "frontend_url": _normalize_url(frontend_url),
        "expected_callback_url": expected_callback_url,
        "allow_new_users": config.get("disable_signup") is False,
        "disable_signup": config.get("disable_signup"),
        "site_url": str(config.get("site_url") or "").strip(),
        "site_url_matches_frontend": _normalize_url(str(config.get("site_url") or ""))
        == _normalize_url(frontend_url),
        "callback_url_allowed": _redirect_allowed(expected_callback_url, redirect_allow_list),
        "redirect_allow_list_count": len(redirect_allow_list),
        "changed": changed,
        "pending_patch_keys": sorted(patch),
    }


def inspect_or_repair_auth_config(
    *,
    runtime_plain_env_json: str,
    environment: str,
    supabase_access_token: str,
    apply: bool,
) -> dict[str, Any]:
    runtime_plain_env = _load_runtime_plain_env(runtime_plain_env_json)
    project_ref = supabase_project_ref_from_url(runtime_plain_env.get("SUPABASE_URL", ""))
    if not project_ref:
        raise ValueError("SUPABASE_URL must be a concrete Supabase project URL")
    frontend_url = _normalize_url(runtime_plain_env.get("FRONTEND_URL", ""))
    if not frontend_url:
        raise ValueError("FRONTEND_URL is required")
    access_token = supabase_access_token.strip()
    if not access_token:
        raise ValueError("SUPABASE_ACCESS_TOKEN is required")

    url = _auth_config_url(project_ref)
    config = _request_json(url, access_token=access_token)
    if not isinstance(config, dict):
        raise ValueError("Supabase auth config lookup returned an unexpected payload")

    patch = _build_patch(config, frontend_url=frontend_url)
    changed = False
    if apply and patch:
        updated = _request_json(url, access_token=access_token, method="PATCH", payload=patch)
        if not isinstance(updated, dict):
            raise ValueError("Supabase auth config update returned an unexpected payload")
        config = updated
        patch = _build_patch(config, frontend_url=frontend_url)
        changed = True

    report = _build_report(
        environment=environment,
        project_ref=project_ref,
        frontend_url=frontend_url,
        config=config,
        patch=patch,
        changed=changed,
    )
    if patch:
        report["ready"] = False
        report["message"] = "Supabase Auth config still has pending required changes."
    else:
        report["ready"] = True
        report["message"] = "Supabase Auth config allows production signup and callback redirect."
    return report


def _write_report(path: str, report: dict[str, Any]) -> None:
    if not path:
        return
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_github_summary(report: dict[str, Any]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not summary_path:
        return
    rows = "\n".join(
        f"| `{key}` | `{value}` |" for key, value in sorted(report.items()) if key != "message"
    )
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write("## Supabase Auth Config\n\n")
        handle.write(f"{report['message']}\n\n")
        handle.write("| Field | Value |\n| --- | --- |\n")
        handle.write(rows)
        handle.write("\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect or repair Supabase Auth settings for Valdrics signup."
    )
    parser.add_argument("--runtime-plain-env-json", required=True)
    parser.add_argument("--environment", required=True, choices=("staging", "production"))
    parser.add_argument("--apply", action="store_true", help="Patch required signup settings.")
    parser.add_argument("--report-path", default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = inspect_or_repair_auth_config(
        runtime_plain_env_json=str(args.runtime_plain_env_json),
        environment=str(args.environment),
        supabase_access_token=os.environ.get("SUPABASE_ACCESS_TOKEN", ""),
        apply=bool(args.apply),
    )
    _write_report(str(args.report_path), report)
    _write_github_summary(report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
