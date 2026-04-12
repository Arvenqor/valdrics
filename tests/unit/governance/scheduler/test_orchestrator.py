import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timezone, timedelta
from app.modules.governance.domain.scheduler.orchestrator import SchedulerOrchestrator
from app.modules.governance.domain.scheduler.cohorts import TenantCohort
from app.models.background_job import BackgroundJob, JobStatus
from app.shared.orchestration.contracts import (
    ManagedWorkItem,
    ManagedWorkRequest,
    ManagedWorkResult,
)
import uuid


@pytest.fixture
def mock_session_maker():
    # session_maker() is called synchronously to return a session (which is async context manager)
    maker = MagicMock()
    return maker


@pytest.fixture
def orchestrator(mock_session_maker):
    return SchedulerOrchestrator(mock_session_maker)


@pytest.mark.asyncio
async def test_license_governance_sweep_job_dispatch(orchestrator) -> None:
    """Test license governance sweep dispatch."""
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
            )
        ),
    ) as dispatch:
        await orchestrator.license_governance_sweep_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(work_item=ManagedWorkItem.LICENSE_GOVERNANCE_SWEEP)
    )


@pytest.mark.asyncio
async def test_enforcement_reconciliation_sweep_job_dispatch(orchestrator) -> None:
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
            )
        ),
    ) as dispatch:
        await orchestrator.enforcement_reconciliation_sweep_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(
            work_item=ManagedWorkItem.SCHEDULER_ENFORCEMENT_RECONCILIATION_SWEEP
        )
    )


@pytest.mark.asyncio
async def test_cohort_analysis_job_dispatch(orchestrator) -> None:
    """Test dispatching cohort analysis through the orchestration dispatcher."""
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
            )
        ),
    ) as dispatch:
        await orchestrator.cohort_analysis_job(TenantCohort.HIGH_VALUE)
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(
            work_item=ManagedWorkItem.SCHEDULER_COHORT_ANALYSIS,
            payload={"cohort": "high_value"},
        )
    )
    assert orchestrator._last_run_success is True


@pytest.mark.asyncio
async def test_low_carbon_window(orchestrator: SchedulerOrchestrator) -> None:
    """Test Green Window logic."""
    # Test Green Window (e.g., 12:00 UTC)
    with patch(
        "app.modules.governance.domain.scheduler.orchestrator.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        is_green = await orchestrator.is_low_carbon_window("us-east-1")
        assert is_green is True

    # Test Non-Green Window (e.g., 18:00 UTC)
    with patch(
        "app.modules.governance.domain.scheduler.orchestrator.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc)
        is_green = await orchestrator.is_low_carbon_window("us-east-1")
        assert is_green is False


@pytest.mark.asyncio
async def test_detect_stuck_jobs(orchestrator, mock_session_maker):
    """Test detection of overdue pending jobs without mutating them."""
    # Setup mock DB session
    mock_db = AsyncMock()
    # session_maker() returns an object that can be used in 'async with'
    # So mock_session_maker.return_value should be the context manager
    mock_session_maker.return_value.__aenter__.return_value = mock_db
    mock_session_maker.return_value.__aexit__.return_value = None

    stuck_job = BackgroundJob(
        id=uuid.uuid4(),
        status=JobStatus.PENDING,
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [stuck_job]
    mock_db.execute.return_value = mock_result

    await orchestrator.detect_stuck_jobs()

    assert stuck_job.status == JobStatus.PENDING
    mock_db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_billing_sweep_job(orchestrator: SchedulerOrchestrator) -> None:
    """Test billing sweep dispatch."""
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
            )
        ),
    ) as dispatch:
        await orchestrator.billing_sweep_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(work_item=ManagedWorkItem.SCHEDULER_BILLING_SWEEP)
    )


@pytest.mark.asyncio
async def test_background_job_processing_dispatch(
    orchestrator: SchedulerOrchestrator,
) -> None:
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_tasks",
            )
        ),
    ) as dispatch:
        await orchestrator.background_job_processing_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(work_item=ManagedWorkItem.BACKGROUND_JOB_PROCESSING)
    )


@pytest.mark.asyncio
async def test_background_job_stuck_detection_dispatch(
    orchestrator: SchedulerOrchestrator,
) -> None:
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_tasks",
            )
        ),
    ) as dispatch:
        await orchestrator.background_job_stuck_detection_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(work_item=ManagedWorkItem.BACKGROUND_JOB_STUCK_DETECTION)
    )


@pytest.mark.asyncio
async def test_landing_funnel_health_refresh_dispatch(
    orchestrator: SchedulerOrchestrator,
) -> None:
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_tasks",
            )
        ),
    ) as dispatch:
        await orchestrator.landing_funnel_health_refresh_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(
            work_item=ManagedWorkItem.SCHEDULER_LANDING_FUNNEL_HEALTH_REFRESH
        )
    )

@pytest.mark.asyncio
async def test_acceptance_sweep_job(orchestrator: SchedulerOrchestrator) -> None:
    """Test acceptance sweep dispatch."""
    orchestrator._acquire_dispatch_lock = AsyncMock(return_value=True)  # type: ignore[method-assign]
    with patch.object(
        orchestrator.scheduled_trigger_dispatcher,
        "dispatch",
        new=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
            )
        ),
    ) as dispatch:
        await orchestrator.acceptance_sweep_job()
    dispatch.assert_awaited_once_with(
        ManagedWorkRequest(work_item=ManagedWorkItem.SCHEDULER_ACCEPTANCE_SWEEP)
    )
