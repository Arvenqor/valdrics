from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from scripts import manage_partitions, run_archival_setup


class _AsyncContextManager:
    def __init__(self, value: object) -> None:
        self._value = value

    async def __aenter__(self) -> object:
        return self._value

    async def __aexit__(self, exc_type, exc, tb) -> None:
        del exc_type, exc, tb
        return None


@pytest.mark.asyncio
async def test_manage_partitions_create_uses_partition_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = SimpleNamespace(commit=AsyncMock())
    service = SimpleNamespace(create_future_partitions=AsyncMock(return_value=2))

    monkeypatch.setattr(
        manage_partitions,
        "async_session_maker",
        lambda: _AsyncContextManager(session),
    )
    monkeypatch.setattr(
        manage_partitions,
        "PartitionMaintenanceService",
        lambda _: service,
    )

    await manage_partitions.create_partitions(4)

    service.create_future_partitions.assert_awaited_once_with(months_ahead=4)
    session.commit.assert_awaited_once()
    assert "Partitions created: 2" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_manage_partitions_validate_reports_missing_partition(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = SimpleNamespace(scalar=AsyncMock(side_effect=[True, False]))

    monkeypatch.setattr(
        manage_partitions,
        "async_session_maker",
        lambda: _AsyncContextManager(session),
    )
    monkeypatch.setattr(
        manage_partitions.PartitionMaintenanceService,
        "SUPPORTED_TABLES",
        ("cost_records", "audit_logs"),
    )

    await manage_partitions.validate_partitions(0)

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["missing"]["audit_logs"]


def test_manage_partitions_main_returns_two_when_command_missing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert manage_partitions.main([]) == 2
    assert "Manage Postgres partitions" in capsys.readouterr().out


def test_manage_partitions_main_rejects_negative_months_ahead() -> None:
    with pytest.raises(SystemExit, match="--months-ahead must be >= 0"):
        manage_partitions.main(["create", "--months-ahead", "-1"])


@pytest.mark.asyncio
async def test_run_archival_setup_invokes_partition_maintenance_service(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = SimpleNamespace(commit=AsyncMock())
    service = SimpleNamespace(
        create_future_partitions=AsyncMock(return_value=2),
        archive_old_partitions=AsyncMock(return_value=5),
    )

    monkeypatch.setattr(
        run_archival_setup,
        "_parse_args",
        lambda _argv=None: SimpleNamespace(months_old=13, months_ahead=3),
    )
    monkeypatch.setattr(
        run_archival_setup,
        "async_session_maker",
        lambda: _AsyncContextManager(session),
    )
    monkeypatch.setattr(
        run_archival_setup,
        "PartitionMaintenanceService",
        lambda _: service,
    )

    assert await run_archival_setup.main() == 0

    service.create_future_partitions.assert_awaited_once_with(months_ahead=3)
    service.archive_old_partitions.assert_awaited_once_with(months_old=13)
    session.commit.assert_awaited_once()
    assert "created=2 archived=5" in capsys.readouterr().out


@pytest.mark.asyncio
async def test_run_archival_setup_rejects_non_positive_months_old() -> None:
    with pytest.raises(SystemExit, match="--months-old must be > 0"):
        await run_archival_setup.main(["--months-old", "0"])


@pytest.mark.asyncio
async def test_run_archival_setup_rejects_negative_months_ahead() -> None:
    with pytest.raises(SystemExit, match="--months-ahead must be >= 0"):
        await run_archival_setup.main(["--months-ahead", "-1"])
