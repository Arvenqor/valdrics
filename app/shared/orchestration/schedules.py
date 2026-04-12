from __future__ import annotations

from dataclasses import dataclass, field

from app.shared.orchestration.contracts import ManagedWorkItem


@dataclass(frozen=True)
class ManagedScheduleSpec:
    job_id: str
    description: str
    schedule: str
    time_zone: str
    work_item: ManagedWorkItem
    payload: dict[str, str] = field(default_factory=dict)


_UTC = "Etc/UTC"


MANAGED_SCHEDULE_SPECS: tuple[ManagedScheduleSpec, ...] = (
    ManagedScheduleSpec(
        job_id="cohort_high_value_scan",
        description="Dispatch the high-value tenant cohort scan every 6 hours.",
        schedule="0 */6 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_COHORT_ANALYSIS,
        payload={"cohort": "high_value"},
    ),
    ManagedScheduleSpec(
        job_id="cohort_active_scan",
        description="Dispatch the active tenant cohort scan daily.",
        schedule="0 2 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_COHORT_ANALYSIS,
        payload={"cohort": "active"},
    ),
    ManagedScheduleSpec(
        job_id="cohort_dormant_scan",
        description="Dispatch the dormant tenant cohort scan weekly.",
        schedule="0 3 * * 0",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_COHORT_ANALYSIS,
        payload={"cohort": "dormant"},
    ),
    ManagedScheduleSpec(
        job_id="weekly_remediation_sweep",
        description="Dispatch the weekly remediation lifecycle sweep.",
        schedule="0 20 * * 5",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_REMEDIATION_SWEEP,
    ),
    ManagedScheduleSpec(
        job_id="daily_billing_sweep",
        description="Dispatch the daily billing and ledger sweep.",
        schedule="0 4 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_BILLING_SWEEP,
    ),
    ManagedScheduleSpec(
        job_id="daily_acceptance_sweep",
        description="Dispatch the daily acceptance evidence capture sweep.",
        schedule="0 5 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_ACCEPTANCE_SWEEP,
    ),
    ManagedScheduleSpec(
        job_id="daily_license_governance_sweep",
        description="Dispatch the daily license governance sweep.",
        schedule="0 6 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.LICENSE_GOVERNANCE_SWEEP,
    ),
    ManagedScheduleSpec(
        job_id="hourly_enforcement_reconciliation_sweep",
        description="Dispatch the hourly enforcement reconciliation sweep.",
        schedule="20 * * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_ENFORCEMENT_RECONCILIATION_SWEEP,
    ),
    ManagedScheduleSpec(
        job_id="background_job_processor",
        description="Continuously drain durable background work.",
        schedule="* * * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.BACKGROUND_JOB_PROCESSING,
    ),
    ManagedScheduleSpec(
        job_id="stuck_job_detector",
        description="Detect overdue pending jobs and update stuck-job metrics.",
        schedule="0 * * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.BACKGROUND_JOB_STUCK_DETECTION,
    ),
    ManagedScheduleSpec(
        job_id="hourly_landing_funnel_health_refresh",
        description="Refresh landing funnel health telemetry.",
        schedule="10 * * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_LANDING_FUNNEL_HEALTH_REFRESH,
    ),
    ManagedScheduleSpec(
        job_id="daily_maintenance_sweep",
        description="Dispatch the nightly maintenance sweep.",
        schedule="0 3 * * *",
        time_zone=_UTC,
        work_item=ManagedWorkItem.SCHEDULER_MAINTENANCE_SWEEP,
    ),
)


def managed_schedule_specs() -> tuple[ManagedScheduleSpec, ...]:
    return MANAGED_SCHEDULE_SPECS


def cloud_scheduler_jobs_payload() -> dict[str, dict[str, object]]:
    return {
        spec.job_id: {
            "description": spec.description,
            "schedule": spec.schedule,
            "time_zone": spec.time_zone,
            "work_item": spec.work_item.value,
            "payload": dict(spec.payload),
        }
        for spec in MANAGED_SCHEDULE_SPECS
    }
