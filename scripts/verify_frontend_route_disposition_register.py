#!/usr/bin/env python3
"""Verify the production frontend route disposition register.

Every SvelteKit route module under `frontend/src/routes` must have an explicit
modernization disposition before the migration can honestly claim there are no
legacy, bloated, or unsupported production islands left behind.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.env_generation_common import (
    repo_root_for as _repo_root_for,
    resolve_cli_path_from_root,
)


DEFAULT_REGISTER_PATH = Path("docs/architecture/frontend_route_disposition_register.json")
ROUTE_MODULE_NAMES = {"+page.svelte", "+page.ts", "+page.server.ts", "+server.ts"}
VALID_STATUSES = {"pending", "migrated", "internal", "rejected"}


def _repo_root() -> Path:
    return _repo_root_for(__file__)


def _resolve_repo_root(path: Path) -> Path:
    return resolve_cli_path_from_root(_repo_root(), path, field_name="repo_root")


def _resolve_register_path(repo_root: Path, path: Path) -> Path:
    return resolve_cli_path_from_root(repo_root, path, field_name="register")


def _is_safe_relative_path(value: str) -> bool:
    if not value or value.startswith("/"):
        return False
    return ".." not in Path(value).parts


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"register must be valid JSON: {exc}") from exc


def _frontend_route_module_files(repo_root: Path) -> set[str]:
    route_root = repo_root / "frontend" / "src" / "routes"
    if not route_root.is_dir():
        return set()
    return {
        path.relative_to(repo_root).as_posix()
        for path in route_root.rglob("*")
        if path.is_file() and path.name in ROUTE_MODULE_NAMES
    }


def _route_id_for_module(relative_path: str) -> str:
    path = Path(relative_path)
    parts = path.parts
    if len(parts) < 4 or parts[:3] != ("frontend", "src", "routes"):
        raise ValueError(f"route module must live under frontend/src/routes: {relative_path}")
    if parts[-1] not in ROUTE_MODULE_NAMES:
        raise ValueError(f"not a SvelteKit route module: {relative_path}")

    route_parts = parts[3:-1]
    if not route_parts:
        return "/"
    return "/" + "/".join(route_parts)


def _validate_string_list(value: Any, *, label: str, errors: list[str]) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a list of strings")
        return []
    return value


def verify_register(*, repo_root: Path, register_path: Path) -> list[str]:
    errors: list[str] = []
    if not register_path.is_file():
        return [f"missing register: {register_path.relative_to(repo_root).as_posix()}"]

    raw = _load_json(register_path)
    if not isinstance(raw, dict):
        return ["register root must be a JSON object"]

    if raw.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    entries = raw.get("entries")
    if not isinstance(entries, list) or not entries:
        errors.append("entries must be a non-empty list")
        return errors

    actual_sources = _frontend_route_module_files(repo_root)
    registered_sources: list[str] = []
    registered_routes: list[str] = []

    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue

        route_id = entry.get("route_id")
        if not isinstance(route_id, str) or not route_id.startswith("/"):
            errors.append(f"{label}.route_id must be an absolute route id")
            route_id = ""
        elif route_id != "/" and route_id.endswith("/"):
            errors.append(f"{route_id}: route_id must not have a trailing slash")
        elif "//" in route_id:
            errors.append(f"{route_id}: route_id must not contain duplicate slashes")
        registered_routes.append(route_id)

        kind = entry.get("kind")
        if not isinstance(kind, str) or not kind.strip():
            errors.append(f"{route_id or label}: kind must be non-empty")

        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"{route_id or label}: status must be one of {sorted(VALID_STATUSES)}")

        decision = entry.get("decision")
        if not isinstance(decision, str) or not decision.strip():
            errors.append(f"{route_id or label}: decision must be non-empty")

        source_files = _validate_string_list(
            entry.get("source_files"),
            label=f"{route_id or label}.source_files",
            errors=errors,
        )
        if not source_files:
            errors.append(f"{route_id or label}: source_files must be non-empty")

        for source_file in source_files:
            if not _is_safe_relative_path(source_file):
                errors.append(f"{route_id or label}: unsafe source path {source_file!r}")
                continue
            if source_file not in actual_sources:
                errors.append(f"{route_id or label}: source file is not a route module: {source_file}")
                continue
            try:
                computed_route_id = _route_id_for_module(source_file)
            except ValueError as exc:
                errors.append(str(exc))
                continue
            if route_id and computed_route_id != route_id:
                errors.append(
                    f"{source_file}: route_id mismatch; register has {route_id}, "
                    f"computed {computed_route_id}"
                )
            registered_sources.append(source_file)

        target_paths = _validate_string_list(
            entry.get("target_paths", []),
            label=f"{route_id or label}.target_paths",
            errors=errors,
        )
        for target_path in target_paths:
            if not _is_safe_relative_path(target_path):
                errors.append(f"{route_id or label}: unsafe target path {target_path!r}")
                continue
            if not (repo_root / target_path).exists():
                errors.append(f"{route_id or label}: target path does not exist: {target_path}")

        evidence = _validate_string_list(
            entry.get("evidence", []),
            label=f"{route_id or label}.evidence",
            errors=errors,
        )

        next_action = entry.get("next_action", "")
        deletion_blocker = entry.get("deletion_blocker", "")
        if next_action is not None and not isinstance(next_action, str):
            errors.append(f"{route_id or label}: next_action must be a string")
        if deletion_blocker is not None and not isinstance(deletion_blocker, str):
            errors.append(f"{route_id or label}: deletion_blocker must be a string")

        if status == "migrated" and not evidence:
            errors.append(f"{route_id or label}: migrated entries require evidence")
        if status == "internal" and not evidence and not deletion_blocker:
            errors.append(
                f"{route_id or label}: internal entries require evidence or a deletion blocker"
            )
        if status == "pending":
            if not isinstance(next_action, str) or not next_action.strip():
                errors.append(f"{route_id or label}: pending entries require next_action")
            if not isinstance(deletion_blocker, str) or not deletion_blocker.strip():
                errors.append(f"{route_id or label}: pending entries require deletion_blocker")
        if status == "rejected" and not evidence:
            errors.append(f"{route_id or label}: rejected entries require evidence")

    duplicate_sources = sorted(
        source for source, count in Counter(registered_sources).items() if count > 1
    )
    for duplicate_source in duplicate_sources:
        errors.append(f"{duplicate_source}: duplicate route disposition source")

    duplicate_routes = sorted(route for route, count in Counter(registered_routes).items() if count > 1)
    for duplicate_route in duplicate_routes:
        errors.append(f"{duplicate_route}: duplicate route disposition entry")

    missing_sources = sorted(actual_sources - set(registered_sources))
    extra_sources = sorted(set(registered_sources) - actual_sources)
    for source in missing_sources:
        errors.append(f"{source}: missing route disposition entry")
    for source in extra_sources:
        errors.append(f"{source}: registered route source is not present")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root", default=str(_repo_root()), help="Repository root path"
    )
    parser.add_argument(
        "--register",
        default=str(DEFAULT_REGISTER_PATH),
        help="Disposition register path, relative to repo root by default",
    )
    args = parser.parse_args(argv)
    try:
        repo_root = _resolve_repo_root(Path(str(args.repo_root)))
        register_path = _resolve_register_path(repo_root, Path(str(args.register)))
        errors = verify_register(repo_root=repo_root, register_path=register_path)
    except ValueError as exc:
        print(f"[frontend-route-disposition] failed: {exc}")
        return 2

    if errors:
        print("[frontend-route-disposition] FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[frontend-route-disposition] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
