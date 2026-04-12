from __future__ import annotations

from app.shared.orchestration.contracts import ManagedWorkItem
from app.shared.orchestration.schedules import (
    cloud_scheduler_jobs_payload,
    managed_schedule_specs,
)


def test_managed_schedule_specs_cover_full_managed_scheduler_surface() -> None:
    specs = managed_schedule_specs()
    job_ids = {spec.job_id for spec in specs}

    assert "background_job_processor" in job_ids
    assert "stuck_job_detector" in job_ids
    assert "cohort_high_value_scan" in job_ids
    assert "cohort_active_scan" in job_ids
    assert "cohort_dormant_scan" in job_ids
    assert "daily_acceptance_sweep" in job_ids
    assert "daily_billing_sweep" in job_ids
    assert "daily_license_governance_sweep" in job_ids
    assert "hourly_enforcement_reconciliation_sweep" in job_ids
    assert "hourly_landing_funnel_health_refresh" in job_ids
    assert "daily_maintenance_sweep" in job_ids
    assert "weekly_remediation_sweep" in job_ids


def test_cloud_scheduler_payload_uses_known_work_items() -> None:
    payload = cloud_scheduler_jobs_payload()
    allowed = {item.value for item in ManagedWorkItem}

    assert payload["stuck_job_detector"]["work_item"] == (
        ManagedWorkItem.BACKGROUND_JOB_STUCK_DETECTION.value
    )
    assert payload["background_job_processor"]["schedule"] == "* * * * *"
    assert payload["cohort_high_value_scan"]["payload"] == {"cohort": "high_value"}
    assert set(item["work_item"] for item in payload.values()).issubset(allowed)
