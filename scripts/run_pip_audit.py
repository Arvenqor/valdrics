"""Run pip-audit with centrally governed vulnerability exceptions."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import TypedDict


class VulnerabilityException(TypedDict):
    package: str
    alias: str
    review_by: date


DEFAULT_EXCEPTION_DOC_PATH = Path("docs/security/dependency_vulnerability_exceptions.md")
PIP_AUDIT_IGNORED_VULNERABILITIES: dict[str, VulnerabilityException] = {
    "PYSEC-2025-183": {
        "package": "pyjwt",
        "alias": "CVE-2025-45768",
        "review_by": date(2026, 6, 19),
    },
    "PYSEC-2026-161": {
        "package": "starlette",
        "alias": "CVE-2026-48710",
        "review_by": date(2026, 6, 7),
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_doc_path(repo_root: Path, doc_path: Path) -> Path:
    if doc_path.is_absolute():
        return doc_path
    return repo_root / doc_path


def validate_exception_documentation(
    *,
    repo_root: Path,
    doc_path: Path = DEFAULT_EXCEPTION_DOC_PATH,
    today: date | None = None,
) -> tuple[str, ...]:
    """Ensure every ignored advisory has traceable, unexpired documentation."""
    resolved_doc_path = _resolve_doc_path(repo_root, doc_path)
    if not resolved_doc_path.is_file():
        return (f"pip-audit exception register is missing: {resolved_doc_path}",)

    current_date = today or date.today()
    text = resolved_doc_path.read_text(encoding="utf-8")
    errors: list[str] = []

    for advisory_id, metadata in sorted(PIP_AUDIT_IGNORED_VULNERABILITIES.items()):
        review_by = metadata["review_by"]
        required_fragments = (
            advisory_id,
            metadata["alias"],
            metadata["package"],
            review_by.isoformat(),
        )
        for fragment in required_fragments:
            if fragment not in text:
                errors.append(
                    f"{resolved_doc_path}: missing `{fragment}` for {advisory_id}."
                )
        if current_date > review_by:
            errors.append(
                f"{advisory_id} exception expired on {review_by.isoformat()}; "
                "review the advisory and remove or extend the exception."
            )

    return tuple(errors)


def build_pip_audit_command(passthrough_args: tuple[str, ...]) -> tuple[str, ...]:
    command: list[str] = [sys.executable, "-m", "pip_audit"]
    for advisory_id in sorted(PIP_AUDIT_IGNORED_VULNERABILITIES):
        command.extend(("--ignore-vuln", advisory_id))
    command.extend(passthrough_args)
    return tuple(command)


def parse_args(argv: tuple[str, ...]) -> tuple[argparse.Namespace, tuple[str, ...]]:
    parser = argparse.ArgumentParser(
        description="Run pip-audit with documented, expiring Valdrics exceptions."
    )
    parser.add_argument(
        "--exception-doc",
        type=Path,
        default=DEFAULT_EXCEPTION_DOC_PATH,
        help="Path to the markdown register for active pip-audit exceptions.",
    )
    parser.add_argument(
        "--today",
        default=None,
        help=argparse.SUPPRESS,
    )
    parsed, passthrough_args = parser.parse_known_args(argv)
    if passthrough_args[:1] == ["--"]:
        passthrough_args = passthrough_args[1:]
    return parsed, tuple(passthrough_args)


def main(argv: tuple[str, ...] | None = None) -> int:
    parsed, passthrough_args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    today = date.fromisoformat(parsed.today) if parsed.today else None
    errors = validate_exception_documentation(
        repo_root=_repo_root(),
        doc_path=parsed.exception_doc,
        today=today,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 2

    command = build_pip_audit_command(passthrough_args)
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
