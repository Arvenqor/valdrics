from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.shared.orchestration.execution import (
    ManagedWorkExecutionPayload,
    execute_managed_work,
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.shared.orchestration.job_runner",
        description="Execute a managed Valdrics batch work item.",
    )
    parser.add_argument("--work-item", required=True)
    parser.add_argument("--payload", default="{}")
    return parser.parse_args(argv)


async def _run(argv: list[str]) -> int:
    args = _parse_args(argv)
    payload = json.loads(args.payload)
    request = ManagedWorkExecutionPayload(
        work_item=args.work_item,
        payload=payload,
    )
    result = await execute_managed_work(request)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(_run(list(sys.argv[1:] if argv is None else argv)))


if __name__ == "__main__":
    raise SystemExit(main())
