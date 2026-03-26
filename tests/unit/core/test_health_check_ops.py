from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.shared.core import health_check_ops


@pytest.mark.asyncio
async def test_probe_worker_health_runs_default_probe_inline_when_thread_not_required() -> None:
    expected = {
        "status": "skipped",
        "message": "no broker configured",
        "worker_count": 0,
        "workers": [],
    }

    with (
        patch.object(
            health_check_ops,
            "_default_worker_probe_requires_thread",
            return_value=False,
        ),
        patch.object(health_check_ops, "_default_worker_probe", return_value=expected),
        patch("app.shared.core.health_check_ops.asyncio.to_thread", new_callable=AsyncMock) as to_thread,
    ):
        result = await health_check_ops._probe_worker_health(worker_probe=None)

    assert result == expected
    to_thread.assert_not_awaited()


@pytest.mark.asyncio
async def test_probe_worker_health_offloads_default_probe_when_runtime_broker_is_configured() -> None:
    expected = {
        "status": "healthy",
        "message": "workers responded",
        "worker_count": 1,
        "workers": ["worker-1"],
    }

    with (
        patch.object(
            health_check_ops,
            "_default_worker_probe_requires_thread",
            return_value=True,
        ),
        patch("app.shared.core.health_check_ops.asyncio.to_thread", new_callable=AsyncMock, return_value=expected) as to_thread,
    ):
        result = await health_check_ops._probe_worker_health(worker_probe=None)

    assert result == expected
    to_thread.assert_awaited_once_with(health_check_ops._default_worker_probe)
