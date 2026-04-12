import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.background_job import BackgroundJob
from app.modules.governance.domain.jobs.errors import PermanentJobError
from app.modules.governance.domain.jobs.handlers.analysis import (
    ReportGenerationHandler,
    ZombieAnalysisHandler,
)


@pytest.mark.asyncio
async def test_zombie_analysis_requires_zombies_payload(db):
    handler = ZombieAnalysisHandler()
    job = BackgroundJob(tenant_id=uuid4(), payload={})

    with pytest.raises(PermanentJobError, match="zombies payload required"):
        await handler.execute(job, db)


@pytest.mark.asyncio
async def test_report_generation_rejects_invalid_end_date(db):
    handler = ReportGenerationHandler()
    job = BackgroundJob(
        tenant_id=uuid4(),
        payload={"report_type": "close_package", "end_date": "not-a-date"},
    )

    with pytest.raises(PermanentJobError, match="Expected ISO date string"):
        await handler.execute(job, db)


@pytest.mark.asyncio
async def test_report_generation_rejects_unsupported_report_type(db):
    handler = ReportGenerationHandler()
    job = BackgroundJob(tenant_id=uuid4(), payload={"report_type": "mystery"})

    with pytest.raises(PermanentJobError, match="Unsupported report_type"):
        await handler.execute(job, db)


@pytest.mark.asyncio
async def test_report_generation_leadership_kpis_success(db):
    handler = ReportGenerationHandler()
    tenant_id = uuid4()
    job = BackgroundJob(
        tenant_id=tenant_id,
        payload={
            "report_type": "leadership_kpis",
            "start_date": "2026-01-01",
            "end_date": "2026-01-31",
        },
    )

    payload = MagicMock()
    payload.model_dump.return_value = {"ok": True}

    with (
        patch(
            "app.shared.core.pricing.get_tenant_tier",
            new=AsyncMock(return_value=MagicMock(value="growth")),
        ),
        patch(
            "app.modules.reporting.domain.leadership_kpis.LeadershipKpiService"
        ) as service_cls,
    ):
        service_cls.return_value.compute = AsyncMock(return_value=payload)

        result = await handler.execute(job, db)

    assert result["status"] == "completed"
    assert result["report_type"] == "leadership_kpis"
    assert result["report"] == {"ok": True}
