import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.modules.governance.domain.scheduler.orchestrator import SchedulerOrchestrator
from app.modules.governance.domain.scheduler.cohorts import TenantCohort
from app.shared.orchestration.contracts import ManagedWorkResult


@pytest.fixture
def mock_session_maker():
    return MagicMock()


@pytest.mark.asyncio
async def test_orchestrator_dispatches_managed_work_requests(mock_session_maker):
    """Verify Orchestrator dispatches through the orchestration contract."""

    orchestrator = SchedulerOrchestrator(mock_session_maker)
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
        # Test Cohort Dispatch
        await orchestrator.cohort_analysis_job(TenantCohort.HIGH_VALUE)

        # Test Remediation Dispatch
        await orchestrator.auto_remediation_job()

        # Test Billing Dispatch
        await orchestrator.billing_sweep_job()

        # Test Maintenance Dispatch
        await orchestrator.maintenance_sweep_job()

        # Test License Governance Dispatch
        await orchestrator.license_governance_sweep_job()

        # Test Enforcement Reconciliation Dispatch
        await orchestrator.enforcement_reconciliation_sweep_job()
    assert dispatch.await_count == 6


@pytest.mark.asyncio
async def test_managed_work_runner_logic_execution():
    """Verify the managed cohort runner still performs the database selection flow."""
    from app.shared.orchestration.managed_work_runners import run_cohort_analysis

    mock_db = AsyncMock()
    mock_db.begin = MagicMock(
        return_value=AsyncMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())
    )
    mock_db.execute = AsyncMock(
        return_value=MagicMock(scalars=lambda: MagicMock(all=lambda: []))
    )

    with (
        patch("app.shared.orchestration.managed_work_runners.async_session_maker") as mock_maker,
        patch("app.shared.orchestration.managed_work_runners._system_sweep_tenant_limit", return_value=1),
        patch("app.shared.orchestration.managed_work_runners.BACKGROUND_JOBS_ENQUEUED"),
    ):
        mock_maker.return_value.__aenter__.return_value = mock_db

        await run_cohort_analysis({"cohort": TenantCohort.ACTIVE.value})

        assert mock_db.execute.called
        args, _ = mock_db.execute.call_args
        assert "Select" in str(type(args[0])) or "Select" in str(args[0])
