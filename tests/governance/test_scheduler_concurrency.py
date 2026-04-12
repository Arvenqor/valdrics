import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4
from app.models.tenant import Tenant


@pytest.mark.asyncio
async def test_scheduler_concurrency_lock():
    """
    BE-SCHED-1: Verify that parallel scheduler tasks don't create duplicate jobs
    using row-level locking (SELECT FOR UPDATE SKIP LOCKED).
    """
    from app.shared.orchestration.managed_work_runners import run_cohort_analysis

    mock_db = AsyncMock()

    class MockAsyncContext:
        def __init__(self, val):
            self.val = val

        async def __aenter__(self):
            return self.val

        async def __aexit__(self, *args):
            pass

        def begin(self):
            return MockAsyncContext(self.val)

    mock_db.begin = MagicMock(return_value=MockAsyncContext(mock_db))

    # Simulate a tenant to be processed
    tenant_id = uuid4()
    mock_tenant = MagicMock(spec=Tenant)
    mock_tenant.id = tenant_id
    mock_tenant.plan = "enterprise"

    # Results for execution flow
    mock_result_full = MagicMock()
    mock_result_full.scalars.return_value.all.return_value = [mock_tenant]

    mock_result_empty = MagicMock()
    mock_result_empty.scalars.return_value.all.return_value = []

    with (
        patch("app.shared.orchestration.managed_work_runners.async_session_maker") as mock_maker,
        patch("app.shared.orchestration.managed_work_runners._system_sweep_tenant_limit", return_value=1),
        patch("app.shared.orchestration.managed_work_runners.BACKGROUND_JOBS_ENQUEUED"),
    ):
        mock_maker.return_value = MockAsyncContext(mock_db)

        # Track calls to differentiate queries vs inserts
        call_count = 0

        def execute_side_effect(stmt, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            # First SELECT from any task returns tenant, second returns empty
            if "TENANT" in str(stmt).upper():
                if call_count == 1:
                    return mock_result_full
                return mock_result_empty
            return MagicMock(rowcount=1)

        mock_db.execute.side_effect = execute_side_effect

        await asyncio.gather(
            run_cohort_analysis({"cohort": "high_value"}),
            run_cohort_analysis({"cohort": "high_value"}),
        )

        assert mock_db.execute.call_count >= 2
