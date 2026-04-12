from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI

from app.modules.governance.api.v1.internal_orchestration import (
    dispatch_internal_scheduler_work,
    dispatch_internal_task,
    router,
)
from app.shared.orchestration.contracts import (
    ManagedWorkItem,
    ManagedWorkResult,
)
from app.shared.orchestration.execution import ManagedWorkExecutionPayload
from tests.shared.asgi_client import SyncASGIClient


@pytest.fixture
def internal_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/internal")
    return app


@pytest.mark.asyncio
async def test_dispatch_internal_task_executes_inline_work() -> None:
    request = ManagedWorkExecutionPayload(
        work_item=ManagedWorkItem.BACKGROUND_JOB_PROCESSING,
        payload={"tenant_id": "tenant-123"},
    )

    with patch(
        "app.modules.governance.api.v1.internal_orchestration.execute_managed_work",
        new_callable=AsyncMock,
    ) as execute_managed_work:
        execute_managed_work.return_value = {
            "status": "completed",
            "work_item": ManagedWorkItem.BACKGROUND_JOB_PROCESSING.value,
        }

        result = await dispatch_internal_task(request, _auth=object())

    assert result["status"] == "completed"
    execute_managed_work.assert_awaited_once_with(request)


@pytest.mark.asyncio
async def test_dispatch_internal_scheduler_work_uses_managed_dispatcher() -> None:
    request = ManagedWorkExecutionPayload(
        work_item=ManagedWorkItem.SCHEDULER_REMEDIATION_SWEEP,
        payload={"scope": "weekly"},
    )
    dispatcher = SimpleNamespace(
        dispatch=AsyncMock(
            return_value=ManagedWorkResult(
                accepted=True,
                transport="gcp_cloud_run_jobs",
                reference="projects/demo/locations/us-central1/jobs/valdrics",
            )
        )
    )

    with patch(
        "app.shared.orchestration.runtime.get_scheduled_trigger_dispatcher",
        return_value=dispatcher,
    ):
        result = await dispatch_internal_scheduler_work(request, _auth=object())

    assert result == {
        "status": "accepted",
        "work_item": ManagedWorkItem.SCHEDULER_REMEDIATION_SWEEP.value,
        "transport": "gcp_cloud_run_jobs",
        "reference": "projects/demo/locations/us-central1/jobs/valdrics",
    }
    dispatcher.dispatch.assert_awaited_once()


def test_scheduler_dispatch_route_requires_gcp_identity_token(
    internal_app: FastAPI,
) -> None:
    settings = SimpleNamespace(
        PLATFORM_RUNTIME_PROFILE="gcp",
        API_URL="https://api.valdrics.example",
        GCP_INTERNAL_ALLOWED_SERVICE_ACCOUNTS=[
            "scheduler@valdrics.iam.gserviceaccount.com"
        ],
    )

    with (
        patch("app.shared.core.config.get_settings", return_value=settings),
        SyncASGIClient(internal_app, raise_app_exceptions=False) as client,
    ):
        response = client.post(
            "/api/v1/internal/scheduler/dispatch",
            json={
                "work_item": ManagedWorkItem.SCHEDULER_REMEDIATION_SWEEP.value,
                "payload": {},
            },
        )

    assert response.status_code == 403
    assert "Google identity token is required" in response.json()["detail"]
