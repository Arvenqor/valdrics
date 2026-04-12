from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.shared.orchestration.contracts import ManagedWorkRequest
from app.shared.orchestration.execution import (
    ManagedWorkExecutionPayload,
    execute_managed_work,
)
from app.shared.orchestration.security import (
    require_internal_platform_invocation,
)

router = APIRouter(tags=["Internal Orchestration"])


@router.post("/tasks/dispatch")
async def dispatch_internal_task(
    request: ManagedWorkExecutionPayload,
    _auth: Any = Depends(require_internal_platform_invocation),
) -> dict[str, Any]:
    return await execute_managed_work(request)


@router.post("/scheduler/dispatch")
async def dispatch_internal_scheduler_work(
    request: ManagedWorkExecutionPayload,
    _auth: Any = Depends(require_internal_platform_invocation),
) -> dict[str, Any]:
    from app.shared.orchestration.runtime import get_scheduled_trigger_dispatcher

    result = await get_scheduled_trigger_dispatcher().dispatch(
        ManagedWorkRequest(
            work_item=request.work_item,
            payload=dict(request.payload),
        )
    )
    return {
        "status": "accepted" if result.accepted else "rejected",
        "work_item": request.work_item.value,
        "transport": result.transport,
        "reference": result.reference,
    }
