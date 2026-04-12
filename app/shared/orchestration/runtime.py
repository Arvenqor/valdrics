from __future__ import annotations

import asyncio
import functools
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, cast

from app.shared.core.config import get_settings
from app.shared.orchestration.contracts import (
    AsyncTaskDispatcher,
    BatchJobLauncher,
    DispatchUnavailableError,
    ManagedWorkRequest,
    ManagedWorkResult,
    ScheduledTriggerDispatcher,
    WorkExecutionMode,
    get_work_spec,
)


_GCP_TASK_ENDPOINT_PATH = "/api/v1/internal/tasks/dispatch"


def _configured_internal_base_url(settings_obj: object) -> str:
    return str(getattr(settings_obj, "GCP_INTERNAL_BASE_URL", "") or "").strip().rstrip("/")


def _absolute_internal_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}{path}"


def _resolve_cloud_run_service_url(settings_obj: object) -> str:
    try:
        from google.cloud import run_v2
    except ImportError as exc:
        raise DispatchUnavailableError(
            "google-cloud-run dependency is required to resolve the internal Cloud Run service URL."
        ) from exc

    project_id = str(getattr(settings_obj, "GCP_PROJECT_ID", "") or "").strip()
    region = str(getattr(settings_obj, "GCP_REGION", "") or "").strip()
    service_name = str(
        getattr(settings_obj, "GCP_CLOUD_RUN_SERVICE_NAME", "") or ""
    ).strip()
    if not project_id or not region or not service_name:
        raise DispatchUnavailableError(
            "GCP_CLOUD_RUN_SERVICE_NAME, GCP_PROJECT_ID, and GCP_REGION are required for internal GCP dispatch."
        )

    client = run_v2.ServicesClient()
    service_path = client.service_path(project_id, region, service_name)
    service = client.get_service(name=service_path)
    service_uri = str(getattr(service, "uri", "") or "").strip().rstrip("/")
    if not service_uri:
        raise DispatchUnavailableError(
            "Cloud Run service URI could not be resolved for internal GCP dispatch."
        )
    return service_uri


def _gcp_audience(settings_obj: object) -> str:
    explicit_audience = str(
        getattr(settings_obj, "GCP_INTERNAL_AUTH_AUDIENCE", "") or ""
    ).strip()
    if explicit_audience:
        return explicit_audience

    api_url = str(getattr(settings_obj, "API_URL", "") or "").strip()
    if api_url:
        return api_url

    internal_base_url = _configured_internal_base_url(settings_obj)
    if internal_base_url:
        return internal_base_url

    raise DispatchUnavailableError(
        "GCP internal auth audience could not be resolved from API_URL, "
        "GCP_INTERNAL_BASE_URL, or GCP_INTERNAL_AUTH_AUDIENCE."
    )


def _hashed_task_id(work_item: str, deduplication_key: str) -> str:
    digest = hashlib.sha256(f"{work_item}:{deduplication_key}".encode("utf-8")).hexdigest()
    return f"task-{digest[:48]}"


class CloudTasksAsyncTaskDispatcher:
    async def dispatch(self, request: ManagedWorkRequest) -> ManagedWorkResult:
        settings = get_settings()
        try:
            from google.cloud import tasks_v2
            from google.protobuf import timestamp_pb2
        except ImportError as exc:
            raise DispatchUnavailableError(
                "google-cloud-tasks dependency is not installed."
            ) from exc

        project_id = str(getattr(settings, "GCP_PROJECT_ID", "") or "").strip()
        region = str(getattr(settings, "GCP_REGION", "") or "").strip()
        queue_name = str(getattr(settings, "GCP_CLOUD_TASKS_QUEUE", "") or "").strip()
        service_account_email = str(
            getattr(settings, "GCP_CLOUD_TASKS_INVOKER_SERVICE_ACCOUNT_EMAIL", "") or ""
        ).strip()
        audience = _gcp_audience(settings)
        if not project_id or not region or not queue_name or not service_account_email:
            raise DispatchUnavailableError(
                "GCP Cloud Tasks dispatcher is not fully configured."
            )
        internal_base_url = _configured_internal_base_url(settings)
        if not internal_base_url:
            internal_base_url = await asyncio.to_thread(
                _resolve_cloud_run_service_url,
                settings,
            )

        body = json.dumps(
            {
                "work_item": request.work_item.value,
                "payload": dict(request.payload),
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

        client = tasks_v2.CloudTasksClient()
        parent = client.queue_path(project_id, region, queue_name)
        task: dict[str, object] = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": _absolute_internal_url(
                    internal_base_url,
                    _GCP_TASK_ENDPOINT_PATH,
                ),
                "headers": {"Content-Type": "application/json"},
                "body": body,
                "oidc_token": {
                    "service_account_email": service_account_email,
                    "audience": audience,
                },
            }
        }
        if request.deduplication_key:
            task["name"] = client.task_path(
                project_id,
                region,
                queue_name,
                _hashed_task_id(request.work_item.value, request.deduplication_key),
            )
        if request.delay_seconds and request.delay_seconds > 0:
            scheduled_time = timestamp_pb2.Timestamp()
            scheduled_time.FromDatetime(
                datetime.now(timezone.utc)
                + timedelta(seconds=int(request.delay_seconds))
            )
            task["schedule_time"] = scheduled_time

        create_task = functools.partial(
            client.create_task,
            parent=parent,
            task=cast(Any, task),
        )
        response = await asyncio.to_thread(create_task)
        return ManagedWorkResult(
            accepted=True,
            transport="gcp_cloud_tasks",
            reference=str(getattr(response, "name", None) or ""),
        )


class CloudRunBatchJobLauncher:
    async def launch(self, request: ManagedWorkRequest) -> ManagedWorkResult:
        settings = get_settings()
        try:
            from google.cloud import run_v2
        except ImportError as exc:
            raise DispatchUnavailableError(
                "google-cloud-run dependency is not installed."
            ) from exc

        project_id = str(getattr(settings, "GCP_PROJECT_ID", "") or "").strip()
        region = str(getattr(settings, "GCP_REGION", "") or "").strip()
        job_name = str(
            getattr(settings, "GCP_CLOUD_RUN_BATCH_JOB_NAME", "") or ""
        ).strip()
        if not project_id or not region or not job_name:
            raise DispatchUnavailableError(
                "GCP Cloud Run batch launcher is not fully configured."
            )

        client = run_v2.JobsClient()
        request_payload = json.dumps(
            dict(request.payload),
            separators=(",", ":"),
            sort_keys=True,
        )
        run_request = run_v2.RunJobRequest(
            name=client.job_path(project_id, region, job_name),
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        args=[
                            "--work-item",
                            request.work_item.value,
                            "--payload",
                            request_payload,
                        ]
                    )
                ]
            ),
        )
        operation = await asyncio.to_thread(client.run_job, request=run_request)
        metadata = getattr(operation, "metadata", None)
        execution_name = str(getattr(metadata, "target", "") or "")
        return ManagedWorkResult(
            accepted=True,
            transport="gcp_cloud_run_jobs",
            reference=execution_name,
        )


class ManagedScheduledTriggerDispatcher:
    def __init__(
        self,
        *,
        task_dispatcher: AsyncTaskDispatcher,
        batch_launcher: BatchJobLauncher,
    ) -> None:
        self._task_dispatcher = task_dispatcher
        self._batch_launcher = batch_launcher

    async def dispatch(self, request: ManagedWorkRequest) -> ManagedWorkResult:
        spec = get_work_spec(request.work_item)
        if spec.execution_mode is WorkExecutionMode.TASK:
            return await self._task_dispatcher.dispatch(request)
        return await self._batch_launcher.launch(request)


def get_async_task_dispatcher() -> AsyncTaskDispatcher:
    return CloudTasksAsyncTaskDispatcher()


def get_batch_job_launcher() -> BatchJobLauncher:
    return CloudRunBatchJobLauncher()


def get_scheduled_trigger_dispatcher() -> ScheduledTriggerDispatcher:
    return ManagedScheduledTriggerDispatcher(
        task_dispatcher=get_async_task_dispatcher(),
        batch_launcher=get_batch_job_launcher(),
    )
