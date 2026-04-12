from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.modules.governance.domain.jobs.cur_ingestion import CURIngestionJob


class _FatalTestSignal(BaseException):
    """Sentinel fatal error used to assert broad Exception handlers do not swallow BaseException."""


def _scalars_result(rows: list[object]) -> MagicMock:
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = rows
    result.scalars.return_value = scalars
    return result


def _conn(**overrides: object) -> SimpleNamespace:
    base = {
        "id": "conn-1",
        "region": "us-east-1",
        "cur_prefix": "cur",
        "cur_report_name": "valdrics-cur",
        "aws_account_id": "123456789012",
        "cur_bucket_name": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.mark.asyncio
async def test_execute_raises_when_no_db_session_available() -> None:
    job = CURIngestionJob()
    with pytest.raises(RuntimeError, match="Database session is required"):
        await job._execute(tenant_id="tenant-1")


@pytest.mark.asyncio
async def test_execute_with_connection_id_filter_path_calls_ingest_once() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=_scalars_result([_conn(id="conn-9")]))
    job = CURIngestionJob(db=db)

    with patch.object(job, "ingest_for_connection", new=AsyncMock()) as ingest_mock:
        await job._execute(connection_id="conn-9", tenant_id="tenant-1")

    db.execute.assert_awaited_once()
    ingest_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_with_explicit_db_override_establishes_ingest_context() -> None:
    db_override = MagicMock()
    db_override.execute = AsyncMock(
        return_value=_scalars_result(
            [
                _conn(
                    id="conn-override",
                    tenant_id="tenant-1",
                    last_ingested_at=None,
                )
            ]
        )
    )
    db_override.add = MagicMock()
    job = CURIngestionJob()
    adapter = MagicMock()

    async def _stream_costs(**kwargs):
        del kwargs
        yield {
            "timestamp": "2026-03-01T00:00:00Z",
            "cost_usd": "1.25",
        }

    adapter.stream_cost_and_usage = _stream_costs
    persistence = AsyncMock()
    persistence.save_records_stream = AsyncMock(return_value={"records_saved": 1})

    with (
        patch.object(job, "_build_cur_adapter", return_value=adapter),
        patch.object(job, "_build_persistence_service", return_value=persistence),
    ):
        await job._execute(tenant_id="tenant-1", db=db_override)

    db_override.execute.assert_awaited_once()
    db_override.add.assert_called_once()
    persistence.save_records_stream.assert_awaited_once()
    assert job.db is None


@pytest.mark.asyncio
async def test_ingest_for_connection_rejects_invalid_adapter_timestamp() -> None:
    conn = _conn(id="bad-ts", tenant_id="tenant-1", last_ingested_at=None)
    db = MagicMock()
    db.add = MagicMock()
    job = CURIngestionJob(db=db)
    adapter = MagicMock()

    async def _stream_costs(**kwargs):
        del kwargs
        yield {"timestamp": "bad-ts", "cost_usd": "1.25"}

    adapter.stream_cost_and_usage = _stream_costs
    persistence = AsyncMock()

    async def _consume(records, **kwargs):
        del kwargs
        async for _ in records:
            pass
        return {"records_saved": 0}

    persistence.save_records_stream = AsyncMock(side_effect=_consume)

    with (
        patch.object(job, "_build_cur_adapter", return_value=adapter),
        patch.object(job, "_build_persistence_service", return_value=persistence),
    ):
        with pytest.raises(ValueError, match="ISO 8601"):
            await job.ingest_for_connection(conn)


@pytest.mark.asyncio
async def test_ingest_for_connection_rejects_invalid_adapter_cost() -> None:
    conn = _conn(id="bad-cost", tenant_id="tenant-1", last_ingested_at=None)
    db = MagicMock()
    db.add = MagicMock()
    job = CURIngestionJob(db=db)
    adapter = MagicMock()

    async def _stream_costs(**kwargs):
        del kwargs
        yield {"timestamp": "2026-03-01T00:00:00Z", "cost_usd": "bad-cost"}

    adapter.stream_cost_and_usage = _stream_costs
    persistence = AsyncMock()

    async def _consume(records, **kwargs):
        del kwargs
        async for _ in records:
            pass
        return {"records_saved": 0}

    persistence.save_records_stream = AsyncMock(side_effect=_consume)

    with (
        patch.object(job, "_build_cur_adapter", return_value=adapter),
        patch.object(job, "_build_persistence_service", return_value=persistence),
    ):
        with pytest.raises(ValueError, match="cost_usd must be numeric"):
            await job.ingest_for_connection(conn)


@pytest.mark.asyncio
async def test_find_latest_cur_key_warns_when_no_manifest_files_exist() -> None:
    job = CURIngestionJob()
    conn = _conn()
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {
                "Key": "cur/valdrics-cur/2026-02-01/data.parquet",
                "LastModified": datetime(2026, 2, 1, tzinfo=timezone.utc),
            }
        ]
    }

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-east-1",
        ),
        patch("boto3.client", return_value=mock_s3),
        patch("app.modules.governance.domain.jobs.cur_ingestion.logger") as logger_mock,
    ):
        key = await job._find_latest_cur_key(conn, "cur-bucket")

    assert key is None
    logger_mock.warning.assert_called_once_with(
        "cur_manifest_not_found", bucket="cur-bucket", report="valdrics-cur"
    )


@pytest.mark.asyncio
async def test_find_latest_cur_key_warns_when_manifest_has_no_report_keys() -> None:
    job = CURIngestionJob()
    conn = _conn()
    mock_s3 = MagicMock()
    manifest_key = "cur/valdrics-cur/2026-02-01/valdrics-cur-Manifest.json"
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {
                "Key": manifest_key,
                "LastModified": datetime(2026, 2, 1, tzinfo=timezone.utc),
            }
        ]
    }
    body = MagicMock()
    body.read.return_value = b'{"reportKeys": []}'
    mock_s3.get_object.return_value = {"Body": body}

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-east-1",
        ),
        patch("boto3.client", return_value=mock_s3),
        patch("app.modules.governance.domain.jobs.cur_ingestion.logger") as logger_mock,
    ):
        key = await job._find_latest_cur_key(conn, "cur-bucket")

    assert key is None
    logger_mock.warning.assert_called_once_with(
        "cur_manifest_empty_files", manifest=manifest_key
    )


@pytest.mark.asyncio
async def test_find_latest_cur_key_returns_first_report_key_from_latest_manifest() -> None:
    job = CURIngestionJob()
    conn = _conn(cur_prefix="", cur_report_name="cost-report")
    mock_s3 = MagicMock()
    older = "cost-report/2026-01-01/cost-report-Manifest.json"
    newer = "cost-report/2026-02-01/cost-report-Manifest.json"
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {"Key": older, "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc)},
            {"Key": newer, "LastModified": datetime(2026, 2, 1, tzinfo=timezone.utc)},
        ]
    }
    body = MagicMock()
    body.read.return_value = (
        b'{"reportKeys": ["cost-report/2026-02-01/part-000.parquet", "other.parquet"]}'
    )
    mock_s3.get_object.return_value = {"Body": body}

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-west-2",
        ),
        patch("boto3.client", return_value=mock_s3) as client_mock,
    ):
        key = await job._find_latest_cur_key(conn, "cur-bucket")

    assert key == "cost-report/2026-02-01/part-000.parquet"
    client_mock.assert_called_once()
    mock_s3.get_object.assert_called_once_with(Bucket="cur-bucket", Key=newer)


@pytest.mark.asyncio
async def test_find_latest_cur_key_logs_and_reraises_unexpected_error() -> None:
    job = CURIngestionJob()
    conn = _conn()
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.side_effect = RuntimeError("s3 unavailable")

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-east-1",
        ),
        patch("boto3.client", return_value=mock_s3),
        patch("app.modules.governance.domain.jobs.cur_ingestion.logger") as logger_mock,
    ):
        with pytest.raises(RuntimeError, match="s3 unavailable"):
            await job._find_latest_cur_key(conn, "cur-bucket")

    logger_mock.error.assert_called_once()


@pytest.mark.asyncio
async def test_execute_does_not_swallow_fatal_connection_ingest_exceptions() -> None:
    db = MagicMock()
    db.execute = AsyncMock(return_value=_scalars_result([_conn(id="fatal-conn")]))
    job = CURIngestionJob(db=db)

    with patch.object(
        job,
        "ingest_for_connection",
        new=AsyncMock(side_effect=_FatalTestSignal()),
    ):
        with pytest.raises(_FatalTestSignal):
            await job._execute(tenant_id="tenant-1")


@pytest.mark.asyncio
async def test_execute_does_not_swallow_value_error_connection_ingest_contract_defects() -> (
    None
):
    db = MagicMock()
    db.execute = AsyncMock(return_value=_scalars_result([_conn(id="bad-shape")]))
    job = CURIngestionJob(db=db)

    with patch.object(
        job,
        "ingest_for_connection",
        new=AsyncMock(side_effect=ValueError("bad cur record shape")),
    ):
        with pytest.raises(ValueError, match="bad cur record shape"):
            await job._execute(tenant_id="tenant-1")


@pytest.mark.asyncio
async def test_run_without_db_commits_standalone_session() -> None:
    session = MagicMock()
    session.commit = AsyncMock()

    @asynccontextmanager
    async def fake_session_maker():
        yield session

    with patch(
        "app.modules.governance.domain.jobs.cur_ingestion.async_session_maker",
        fake_session_maker,
    ):
        job = CURIngestionJob()
        with patch.object(job, "_execute", new_callable=AsyncMock) as mock_execute:
            await job.run(connection_id="conn-2", tenant_id="tenant-2")

    mock_execute.assert_awaited_once_with("conn-2", "tenant-2")
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_latest_cur_key_does_not_swallow_fatal_errors() -> None:
    job = CURIngestionJob()
    conn = _conn()
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.side_effect = _FatalTestSignal()

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-east-1",
        ),
        patch("boto3.client", return_value=mock_s3),
    ):
        with pytest.raises(_FatalTestSignal):
            await job._find_latest_cur_key(conn, "cur-bucket")


@pytest.mark.asyncio
async def test_find_latest_cur_key_does_not_swallow_manifest_key_errors() -> None:
    job = CURIngestionJob()
    conn = _conn()
    mock_s3 = MagicMock()
    mock_s3.list_objects_v2.return_value = {
        "Contents": [
            {
                "Key": "cur/valdrics-cur/2026-02-01/valdrics-cur-Manifest.json",
                "LastModified": datetime(2026, 2, 1, tzinfo=timezone.utc),
            }
        ]
    }
    body = MagicMock()
    body.read.return_value = b'{"wrongKey": ["part-000.parquet"]}'
    mock_s3.get_object.return_value = {"Body": body}

    with (
        patch(
            "app.modules.governance.domain.jobs.cur_ingestion.resolve_aws_region_hint",
            return_value="us-east-1",
        ),
        patch("boto3.client", return_value=mock_s3),
    ):
        with pytest.raises(KeyError, match="reportKeys"):
            await job._find_latest_cur_key(conn, "cur-bucket")
