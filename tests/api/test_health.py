from unittest.mock import AsyncMock, patch

import pytest

from app.shared.health import HealthService


@pytest.mark.asyncio
async def test_health_service_all_ok():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=object())
    service = HealthService(db)

    with patch.object(
        HealthService,
        "_check_background_jobs",
        AsyncMock(
            return_value={
                "status": "healthy",
                "queue_stats": {
                    "total_jobs": 0,
                    "pending_jobs": 0,
                    "running_jobs": 0,
                    "failed_jobs": 0,
                },
                "worker_health": {"status": "skipped"},
            }
        ),
    ):
        health = await service.check_all()

    assert health["status"] in ["healthy", "degraded"]
    assert health["database"]["status"] == "up"
    assert "latency_ms" in health["database"]
    assert "status" in health["redis"]
    assert "status" in health["aws"]


@pytest.mark.asyncio
async def test_health_endpoint(ac_no_db):
    payload = {
        "status": "healthy",
        "timestamp": "2026-03-18T00:00:00Z",
        "database": {"status": "up", "latency_ms": 1.0},
        "redis": {"status": "disabled"},
        "aws": {"status": "disabled"},
        "system": {"status": "healthy"},
        "checks": {},
    }

    with patch("app.shared.core.health.HealthService.check_all", AsyncMock(return_value=payload)):
        response = await ac_no_db.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["database"]["status"] == "up"


@pytest.mark.asyncio
async def test_health_db_failure(ac_no_db):
    payload = {
        "status": "unhealthy",
        "timestamp": "2026-03-18T00:00:00Z",
        "database": {"status": "down", "error": "DB Down"},
        "redis": {"status": "disabled"},
        "aws": {"status": "disabled"},
        "system": {"status": "healthy"},
        "checks": {},
    }

    with patch("app.shared.core.health.HealthService.check_all", AsyncMock(return_value=payload)):
        response = await ac_no_db.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["database"]["status"] == "down"
