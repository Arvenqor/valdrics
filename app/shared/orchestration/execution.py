from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.shared.orchestration.contracts import ManagedWorkItem, ManagedWorkRequest
from app.shared.orchestration.managed_work_runners import (
    run_acceptance_sweep,
    run_background_job_processing,
    run_background_job_stuck_detection,
    run_billing_sweep,
    run_cohort_analysis,
    run_enforcement_reconciliation_sweep,
    run_landing_funnel_health_refresh,
    run_license_governance_sweep,
    run_maintenance_sweep,
    run_remediation_sweep,
)


class ManagedWorkExecutionPayload(BaseModel):
    work_item: ManagedWorkItem
    payload: dict[str, object] = Field(default_factory=dict)


_WORK_EXECUTORS = {
    ManagedWorkItem.BACKGROUND_JOB_PROCESSING: run_background_job_processing,
    ManagedWorkItem.BACKGROUND_JOB_STUCK_DETECTION: run_background_job_stuck_detection,
    ManagedWorkItem.SCHEDULER_COHORT_ANALYSIS: run_cohort_analysis,
    ManagedWorkItem.SCHEDULER_REMEDIATION_SWEEP: run_remediation_sweep,
    ManagedWorkItem.SCHEDULER_BILLING_SWEEP: run_billing_sweep,
    ManagedWorkItem.SCHEDULER_ACCEPTANCE_SWEEP: run_acceptance_sweep,
    ManagedWorkItem.LICENSE_GOVERNANCE_SWEEP: run_license_governance_sweep,
    ManagedWorkItem.SCHEDULER_ENFORCEMENT_RECONCILIATION_SWEEP: (
        run_enforcement_reconciliation_sweep
    ),
    ManagedWorkItem.SCHEDULER_MAINTENANCE_SWEEP: run_maintenance_sweep,
    ManagedWorkItem.SCHEDULER_LANDING_FUNNEL_HEALTH_REFRESH: (
        run_landing_funnel_health_refresh
    ),
}


async def execute_managed_work(
    request: ManagedWorkExecutionPayload,
) -> dict[str, Any]:
    return await execute_managed_work_request(
        ManagedWorkRequest(
            work_item=request.work_item,
            payload=dict(request.payload),
        )
    )


async def execute_managed_work_request(
    request: ManagedWorkRequest,
) -> dict[str, Any]:
    executor = _WORK_EXECUTORS[request.work_item]
    details = await executor(dict(request.payload))
    return {
        "status": "completed",
        "work_item": request.work_item.value,
        "details": details,
    }
