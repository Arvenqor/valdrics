from __future__ import annotations

from pathlib import Path

from app.shared.orchestration.contracts import ManagedWorkItem
from app.shared.orchestration.execution import _WORK_EXECUTORS


def test_managed_work_execution_registry_covers_stuck_detection() -> None:
    assert ManagedWorkItem.BACKGROUND_JOB_STUCK_DETECTION in _WORK_EXECUTORS


def test_managed_work_execution_no_longer_imports_celery_task_modules() -> None:
    execution_path = (
        Path(__file__).resolve().parents[4] / "app/shared/orchestration/execution.py"
    )
    execution_source = execution_path.read_text(encoding="utf-8")

    assert "app.tasks." not in execution_source
