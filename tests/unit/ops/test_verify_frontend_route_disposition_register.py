from __future__ import annotations

import json
from pathlib import Path

from scripts.verify_frontend_route_disposition_register import main, verify_register


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_register(repo_root: Path, entries: list[dict]) -> Path:
    register_path = (
        repo_root / "docs/architecture/frontend_route_disposition_register.json"
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


def test_verify_register_accepts_migrated_pending_and_internal_routes(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "frontend/src/routes/+page.svelte", "<main />")
    _write(tmp_path / "frontend/src/routes/audit/+page.svelte", "<main />")
    _write(tmp_path / "frontend/src/routes/api/edge/[...path]/+server.ts", "")
    register_path = _write_register(
        tmp_path,
        [
            {
                "route_id": "/",
                "kind": "public_page",
                "status": "migrated",
                "decision": "Keep migrated public landing route.",
                "source_files": ["frontend/src/routes/+page.svelte"],
                "target_paths": ["frontend/src/routes/+page.svelte"],
                "evidence": ["browser QA /"],
                "next_action": "",
                "deletion_blocker": "",
            },
            {
                "route_id": "/audit",
                "kind": "authenticated_page",
                "status": "pending",
                "decision": "Modernize or prune during FME-010.",
                "source_files": ["frontend/src/routes/audit/+page.svelte"],
                "target_paths": [],
                "evidence": [],
                "next_action": "Audit visible controls and API contracts.",
                "deletion_blocker": "Requires FME-010 modernization disposition.",
            },
            {
                "route_id": "/api/edge/[...path]",
                "kind": "edge_proxy_endpoint",
                "status": "internal",
                "decision": "Keep as production edge proxy endpoint.",
                "source_files": [
                    "frontend/src/routes/api/edge/[...path]/+server.ts"
                ],
                "target_paths": [],
                "evidence": ["edge proxy tests"],
                "next_action": "",
                "deletion_blocker": "",
            },
        ],
    )

    assert verify_register(repo_root=tmp_path, register_path=register_path) == []


def test_verify_register_fails_when_route_module_is_missing_from_register(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "frontend/src/routes/audit/+page.svelte", "<main />")
    register_path = _write_register(tmp_path, [])

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert "entries must be a non-empty list" in errors


def test_verify_register_fails_when_source_route_id_does_not_match(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "frontend/src/routes/audit/+page.svelte", "<main />")
    register_path = _write_register(
        tmp_path,
        [
            {
                "route_id": "/billing",
                "kind": "authenticated_page",
                "status": "migrated",
                "decision": "Wrong route on purpose.",
                "source_files": ["frontend/src/routes/audit/+page.svelte"],
                "target_paths": [],
                "evidence": ["test"],
                "next_action": "",
                "deletion_blocker": "",
            }
        ],
    )

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert (
        "frontend/src/routes/audit/+page.svelte: route_id mismatch; register has /billing, computed /audit"
        in errors
    )


def test_verify_register_fails_when_pending_entry_has_no_next_action(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "frontend/src/routes/audit/+page.svelte", "<main />")
    register_path = _write_register(
        tmp_path,
        [
            {
                "route_id": "/audit",
                "kind": "authenticated_page",
                "status": "pending",
                "decision": "Modernize route.",
                "source_files": ["frontend/src/routes/audit/+page.svelte"],
                "target_paths": [],
                "evidence": [],
                "next_action": "",
                "deletion_blocker": "Requires FME-010 modernization disposition.",
            }
        ],
    )

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert "/audit: pending entries require next_action" in errors


def test_verify_register_fails_when_pending_entry_has_no_blocker(
    tmp_path: Path,
) -> None:
    _write(tmp_path / "frontend/src/routes/audit/+page.svelte", "<main />")
    register_path = _write_register(
        tmp_path,
        [
            {
                "route_id": "/audit",
                "kind": "authenticated_page",
                "status": "pending",
                "decision": "Modernize route.",
                "source_files": ["frontend/src/routes/audit/+page.svelte"],
                "target_paths": [],
                "evidence": [],
                "next_action": "Audit visible controls and API contracts.",
                "deletion_blocker": "",
            }
        ],
    )

    errors = verify_register(repo_root=tmp_path, register_path=register_path)

    assert "/audit: pending entries require deletion_blocker" in errors


def test_main_resolves_repo_relative_register_path() -> None:
    assert (
        main(["--register", "docs/architecture/frontend_route_disposition_register.json"])
        == 0
    )
