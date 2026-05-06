#!/usr/bin/env python3
"""Fail-fast Google Cloud IAM checks for managed platform releases."""

from __future__ import annotations

import argparse
import json
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

GOOGLE_CLOUD_RESOURCE_MANAGER_API_BASE_URL = (
    "https://cloudresourcemanager.googleapis.com/v1"
)
GOOGLE_API_USER_AGENT = "CloudSentinel-AI-release-preflight/1.0"
DEFAULT_REQUIRED_PERMISSIONS = (
    "iam.serviceAccounts.create",
    "iam.serviceAccounts.get",
    "iam.serviceAccounts.getIamPolicy",
    "iam.serviceAccounts.setIamPolicy",
    "resourcemanager.projects.getIamPolicy",
    "resourcemanager.projects.setIamPolicy",
)


def _parse_granted_permissions(raw_payload: str) -> set[str]:
    try:
        payload = json.loads(raw_payload or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Google permissions response was not valid JSON: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError("Google permissions response must be a JSON object")
    permissions = payload.get("permissions", [])
    if permissions is None:
        permissions = []
    if not isinstance(permissions, list):
        raise ValueError(
            "Google permissions response field 'permissions' must be a list"
        )
    return {str(permission) for permission in permissions}


def _gcloud_access_token() -> str:
    completed = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RuntimeError(
            "gcloud auth print-access-token failed"
            + (f": {stderr}" if stderr else "")
        )
    token = completed.stdout.strip()
    if not token:
        raise RuntimeError("gcloud auth print-access-token returned an empty token")
    return token


def _test_project_permissions(
    *, project_id: str, required_permissions: tuple[str, ...]
) -> set[str]:
    access_token = _gcloud_access_token()
    request = Request(
        (
            f"{GOOGLE_CLOUD_RESOURCE_MANAGER_API_BASE_URL}/projects/"
            f"{quote(project_id)}:testIamPermissions"
        ),
        data=json.dumps({"permissions": list(required_permissions)}).encode("utf-8"),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "User-Agent": GOOGLE_API_USER_AGENT,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return _parse_granted_permissions(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Google testIamPermissions returned HTTP {exc.code} for "
            f"project {project_id}: {body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(
            f"Google testIamPermissions request failed for project {project_id}: {exc}"
        ) from exc


def validate_project_permissions(
    *, project_id: str, required_permissions: tuple[str, ...]
) -> dict[str, list[str]]:
    project = project_id.strip()
    if not project:
        raise ValueError("GCP project ID is required")
    if not required_permissions:
        raise ValueError("at least one required permission must be supplied")

    granted = _test_project_permissions(
        project_id=project,
        required_permissions=required_permissions,
    )
    missing = [
        permission
        for permission in required_permissions
        if permission not in granted
    ]
    if missing:
        raise RuntimeError(
            "GCP deployer is missing project IAM permissions required before "
            "Terraform can manage the unified platform: "
            + ", ".join(missing)
        )
    return {
        "granted_permissions": sorted(granted),
        "required_permissions": sorted(required_permissions),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate GCP deployer permissions before expensive release jobs."
    )
    parser.add_argument("--project-id", required=True)
    parser.add_argument(
        "--permission",
        action="append",
        dest="permissions",
        default=[],
        help=(
            "Required project IAM permission. May be provided more than once; "
            "defaults to the managed platform Terraform IAM prerequisites."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    required_permissions = tuple(args.permissions or DEFAULT_REQUIRED_PERMISSIONS)
    result = validate_project_permissions(
        project_id=str(args.project_id),
        required_permissions=required_permissions,
    )
    print(
        "[managed-platform-gcp-preflight] ok "
        f"project_id={args.project_id} "
        f"required_permissions={len(result['required_permissions'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
