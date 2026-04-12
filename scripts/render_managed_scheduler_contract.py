#!/usr/bin/env python3
"""Render the shared managed scheduler contract consumed by Terraform."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.shared.orchestration.schedules import cloud_scheduler_jobs_payload


DEFAULT_OUTPUT = Path("terraform/managed_scheduler_jobs.json")


def render_managed_scheduler_contract(*, output_path: Path) -> dict[str, object]:
    payload = cloud_scheduler_jobs_payload()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render the Terraform managed scheduler contract from the shared Python schedule registry."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output JSON path (default: terraform/managed_scheduler_jobs.json).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    render_managed_scheduler_contract(output_path=args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
