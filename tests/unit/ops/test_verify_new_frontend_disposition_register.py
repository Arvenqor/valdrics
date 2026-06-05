from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_new_frontend_disposition_register import main, verify_register


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_register(repo_root: Path, entries: list[dict]) -> Path:
    register_path = (
        repo_root / "docs/architecture/new_frontend_disposition_register.json"
    )
    _write(
        register_path,
        json.dumps(
            {
                "schema_version": 1,
                "entries": entries,
            }
        ),
    )
    return register_path


def test_verify_register_accepts_complete_pending_and_migrated_entries(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "new_frontend/Sidebar.svelte", "<nav />")
    _write(tmp_path / "new_frontend/Future.svelte", "<section />")
    _write(
        tmp_path / "frontend/src/routes/layout/AppAuthenticatedShell.svelte",
        "<aside />",
    )
    register_path = _write_register(
        tmp_path,
        [
            {
                "source_file": "new_frontend/Sidebar.svelte",
                "status": "migrated",
                "decision": "Migrated into the authenticated shell.",
                "target_paths": [
                    "frontend/src/routes/layout/AppAuthenticatedShell.svelte"
                ],
                "evidence": ["browser QA"],
                "deletion_blocker": "",
            },
            {
                "source_file": "new_frontend/Future.svelte",
                "status": "pending",
                "decision": "Pending contract mapping.",
                "target_paths": [],
                "evidence": [],
                "deletion_blocker": "Requires backend contract mapping.",
            },
        ],
    )

    assert verify_register(repo_root=tmp_path, register_path=register_path) == []


def test_verify_register_fails_when_new_frontend_file_is_missing_from_register(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "new_frontend/Sidebar.svelte", "<nav />")
    register_path = _write_register(tmp_path, [])

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert "entries must be a non-empty list" in errors


def test_verify_register_fails_when_migrated_target_does_not_exist(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "new_frontend/Sidebar.svelte", "<nav />")
    register_path = _write_register(
        tmp_path,
        [
            {
                "source_file": "new_frontend/Sidebar.svelte",
                "status": "migrated",
                "decision": "Migrated into the authenticated shell.",
                "target_paths": ["frontend/src/routes/layout/Missing.svelte"],
                "evidence": ["browser QA"],
                "deletion_blocker": "",
            }
        ],
    )

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert (
        "new_frontend/Sidebar.svelte: target path does not exist: frontend/src/routes/layout/Missing.svelte"
        in errors
    )


def test_verify_register_fails_when_pending_entry_has_no_blocker(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "new_frontend/Future.svelte", "<section />")
    register_path = _write_register(
        tmp_path,
        [
            {
                "source_file": "new_frontend/Future.svelte",
                "status": "pending",
                "decision": "Pending contract mapping.",
                "target_paths": [],
                "evidence": [],
                "deletion_blocker": "",
            }
        ],
    )

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert (
        "new_frontend/Future.svelte: pending entries require deletion_blocker" in errors
    )


def test_verify_register_accepts_archived_sources_when_handoff_root_is_absent(
    tmp_path: Path,
) -> None:
    _write(
        tmp_path / "frontend/src/routes/layout/AppAuthenticatedShell.svelte",
        "<aside />",
    )
    register_path = _write_register(
        tmp_path,
        [
            {
                "source_file": "new_frontend/Sidebar.svelte",
                "status": "migrated",
                "decision": "Archived handoff source after migration.",
                "target_paths": [
                    "frontend/src/routes/layout/AppAuthenticatedShell.svelte"
                ],
                "evidence": ["browser QA"],
                "deletion_blocker": "",
            }
        ],
    )

    assert verify_register(repo_root=tmp_path, register_path=register_path) == []


def test_main_resolves_repo_relative_register_path() -> None:
    assert (
        main(["--register", "docs/architecture/new_frontend_disposition_register.json"])
        == 0
    )
