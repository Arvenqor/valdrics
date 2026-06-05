#!/usr/bin/env python3
"""Verify the `new_frontend/` handoff disposition register.

The register must account for every file in `new_frontend/` before handoff files
can be deleted or migrated. Completed migrations must point at real production
targets under `frontend/`, and pending entries must name a concrete blocker.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.env_generation_common import (
    repo_root_for as _repo_root_for,
    resolve_cli_path_from_root,
)


DEFAULT_REGISTER_PATH = Path("docs/architecture/new_frontend_disposition_register.json")
VALID_STATUSES = {"pending", "migrated", "rejected"}


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


def _new_frontend_files(repo_root: Path) -> set[str]:
    handoff_root = repo_root / "new_frontend"
    if not handoff_root.is_dir():
        return set()
    return {
        path.relative_to(repo_root).as_posix()
        for path in handoff_root.iterdir()
        if path.is_file()
    }


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

    handoff_root_exists = (repo_root / "new_frontend").is_dir()
    actual_sources = _new_frontend_files(repo_root)
    registered_sources: list[str] = []

    for index, entry in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue

        source_file = entry.get("source_file")
        if not isinstance(source_file, str) or not _is_safe_relative_path(source_file):
            errors.append(f"{label}.source_file must be a safe repo-relative path")
            continue
        if not source_file.startswith("new_frontend/"):
            errors.append(f"{label}.source_file must live under new_frontend/")
        registered_sources.append(source_file)
        if handoff_root_exists and source_file not in actual_sources:
            errors.append(f"{source_file}: source file does not exist")

        status = entry.get("status")
        if status not in VALID_STATUSES:
            errors.append(
                f"{source_file}: status must be one of {sorted(VALID_STATUSES)}"
            )
            continue

        decision = entry.get("decision")
        if not isinstance(decision, str) or not decision.strip():
            errors.append(f"{source_file}: decision must be non-empty")

        target_paths = entry.get("target_paths", [])
        if target_paths is None:
            target_paths = []
        if not isinstance(target_paths, list) or not all(
            isinstance(value, str) for value in target_paths
        ):
            errors.append(f"{source_file}: target_paths must be a list of strings")
            target_paths = []

        for target_path in target_paths:
            if not _is_safe_relative_path(target_path):
                errors.append(f"{source_file}: unsafe target path {target_path!r}")
                continue
            if not (repo_root / target_path).exists():
                errors.append(
                    f"{source_file}: target path does not exist: {target_path}"
                )

        evidence = entry.get("evidence", [])
        if evidence is None:
            evidence = []
        if not isinstance(evidence, list) or not all(
            isinstance(value, str) for value in evidence
        ):
            errors.append(f"{source_file}: evidence must be a list of strings")
            evidence = []

        deletion_blocker = entry.get("deletion_blocker")
        if status == "migrated":
            if not target_paths:
                errors.append(f"{source_file}: migrated entries require target_paths")
            if not evidence:
                errors.append(f"{source_file}: migrated entries require evidence")
        elif status == "pending":
            if not isinstance(deletion_blocker, str) or not deletion_blocker.strip():
                errors.append(
                    f"{source_file}: pending entries require deletion_blocker"
                )
        elif status == "rejected" and not evidence:
            errors.append(f"{source_file}: rejected entries require evidence")

    duplicates = sorted(
        source
        for source in set(registered_sources)
        if registered_sources.count(source) > 1
    )
    for duplicate in duplicates:
        errors.append(f"{duplicate}: duplicate register entry")

    missing_sources = sorted(actual_sources - set(registered_sources))
    extra_sources = (
        sorted(set(registered_sources) - actual_sources) if handoff_root_exists else []
    )
    for source in missing_sources:
        errors.append(f"{source}: missing register entry")
    for source in extra_sources:
        errors.append(f"{source}: registered source is not present in new_frontend/")

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
        print(f"[new-frontend-disposition] failed: {exc}")
        return 2

    if errors:
        print("[new-frontend-disposition] FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[new-frontend-disposition] ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
