from __future__ import annotations

import sys
import types
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.shared.orchestration.contracts import ManagedWorkItem, ManagedWorkRequest
from app.shared.orchestration.runtime import (
    CloudRunBatchJobLauncher,
    CloudTasksAsyncTaskDispatcher,
    get_async_task_dispatcher,
    get_batch_job_launcher,
)


def test_dispatcher_selection_returns_managed_gcp_dispatchers() -> None:
    assert isinstance(get_async_task_dispatcher(), CloudTasksAsyncTaskDispatcher)
    assert isinstance(get_batch_job_launcher(), CloudRunBatchJobLauncher)


@pytest.mark.asyncio
async def test_cloud_tasks_dispatcher_builds_oidc_task_request() -> None:
    created: dict[str, object] = {}

    class FakeTimestamp:
        def __init__(self) -> None:
            self.value: datetime | None = None

        def FromDatetime(self, value: datetime) -> None:
            self.value = value

    class FakeTasksClient:
        def queue_path(self, project: str, region: str, queue: str) -> str:
            return f"projects/{project}/locations/{region}/queues/{queue}"

        def task_path(
            self,
            project: str,
            region: str,
            queue: str,
            task_id: str,
        ) -> str:
            return f"projects/{project}/locations/{region}/queues/{queue}/tasks/{task_id}"

        def create_task(self, *, parent: str, task: dict[str, object]) -> SimpleNamespace:
            created["parent"] = parent
            created["task"] = task
            return SimpleNamespace(name="task-123")

    fake_client = FakeTasksClient()
    fake_tasks_v2 = types.SimpleNamespace(
        CloudTasksClient=lambda: fake_client,
        HttpMethod=types.SimpleNamespace(POST="POST"),
    )

    class FakeRunServicesClient:
        def service_path(self, project: str, region: str, service: str) -> str:
            return f"projects/{project}/locations/{region}/services/{service}"

        def get_service(self, *, name: str) -> SimpleNamespace:
            created["service_name"] = name
            return SimpleNamespace(uri="https://valdrics-api-xyz.run.app")

    fake_run_v2 = types.SimpleNamespace(ServicesClient=FakeRunServicesClient)
    fake_timestamp_module = types.SimpleNamespace(Timestamp=FakeTimestamp)
    google_cloud_module = types.ModuleType("google.cloud")
    google_cloud_module.tasks_v2 = fake_tasks_v2
    google_cloud_module.run_v2 = fake_run_v2
    google_protobuf_module = types.ModuleType("google.protobuf")
    google_protobuf_module.timestamp_pb2 = fake_timestamp_module

    settings = SimpleNamespace(
        PLATFORM_RUNTIME_PROFILE="gcp",
        GCP_PROJECT_ID="valdrics-staging",
        GCP_REGION="us-central1",
        GCP_CLOUD_TASKS_QUEUE="valdrics-default",
        GCP_CLOUD_TASKS_INVOKER_SERVICE_ACCOUNT_EMAIL="tasks@valdrics.iam.gserviceaccount.com",
        GCP_CLOUD_RUN_SERVICE_NAME="valdrics-api",
        GCP_INTERNAL_AUTH_AUDIENCE="https://api.valdrics.example",
        API_URL="https://api.valdrics.example",
    )

    with (
        patch("app.shared.orchestration.runtime.get_settings", return_value=settings),
        patch.dict(
            sys.modules,
            {
                "google.cloud": google_cloud_module,
                "google.cloud.tasks_v2": fake_tasks_v2,
                "google.cloud.run_v2": fake_run_v2,
                "google.protobuf": google_protobuf_module,
                "google.protobuf.timestamp_pb2": fake_timestamp_module,
            },
        ),
    ):
        result = await CloudTasksAsyncTaskDispatcher().dispatch(
            ManagedWorkRequest(
                work_item=ManagedWorkItem.BACKGROUND_JOB_PROCESSING,
                payload={"limit": 10},
                deduplication_key="tenant-1:background-drain",
                delay_seconds=5,
            )
        )

    assert result.transport == "gcp_cloud_tasks"
    assert result.reference == "task-123"
    assert created["parent"] == "projects/valdrics-staging/locations/us-central1/queues/valdrics-default"
    assert created["service_name"] == "projects/valdrics-staging/locations/us-central1/services/valdrics-api"
    task = created["task"]
    assert isinstance(task, dict)
    http_request = task["http_request"]
    assert http_request["url"] == "https://valdrics-api-xyz.run.app/api/v1/internal/tasks/dispatch"
    assert http_request["oidc_token"]["service_account_email"] == "tasks@valdrics.iam.gserviceaccount.com"
    assert http_request["oidc_token"]["audience"] == "https://api.valdrics.example"
