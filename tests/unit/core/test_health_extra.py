import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.shared.core.health import HealthService


@pytest.mark.asyncio
async def test_check_all_formats_expected_keys():
    service = HealthService()
    health = {
        "status": "healthy",
        "timestamp": "t",
        "checks": {
            "database": {"status": "up"},
            "cache": {"status": "healthy"},
            "external_services": {
                "status": "healthy",
                "services": {"upstream": {"status": "healthy"}},
            },
            "system_resources": {"status": "healthy"},
        },
    }
    with patch.object(
        service, "comprehensive_health_check", AsyncMock(return_value=health)
    ):
        result = await service.check_all()

    assert set(result) == {
        "status",
        "timestamp",
        "database",
        "cache",
        "external_services",
        "system_resources",
        "checks",
    }
    assert result["database"]["status"] == "up"
    assert result["cache"]["status"] == "healthy"
    assert result["external_services"]["status"] == "healthy"
    assert result["system_resources"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_handle_check_errors_wraps_exception():
    service = HealthService()

    async def fail():
        raise RuntimeError("boom")

    result = await service._handle_check_errors(fail())
    assert result["status"] == "error"
    assert "boom" in result["error"]


@pytest.mark.asyncio
async def test_check_external_services_disabled_without_probes():
    service = HealthService()

    result = await service._check_external_services()

    assert result["status"] == "disabled"
    assert result["services"] == {}


@pytest.mark.asyncio
async def test_check_external_services_status_codes():
    service = HealthService()

    class FakeResponse:
        def __init__(self, code):
            self.status_code = code

    class FakeClient:
        def __init__(self, code):
            self._code = code

        async def get(self, _url, *, timeout=None):
            assert timeout is not None
            return FakeResponse(self._code)

    with (
        patch.object(
            service,
            "_external_service_probes",
            return_value={"upstream": "https://status.example.com/health"},
        ),
        patch("app.shared.core.http.get_http_client", return_value=FakeClient(200)),
    ):
        result = await service._check_external_services()
        assert result["status"] == "healthy"

    with (
        patch.object(
            service,
            "_external_service_probes",
            return_value={"upstream": "https://status.example.com/health"},
        ),
        patch("app.shared.core.http.get_http_client", return_value=FakeClient(503)),
    ):
        result = await service._check_external_services()
        assert result["status"] == "degraded"
        assert result["services"]["upstream"]["response_code"] == 503


@pytest.mark.asyncio
async def test_check_database_includes_engine_for_injected_session():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=MagicMock())
    db.bind = MagicMock()
    db.bind.dialect.name = "sqlite"

    service = HealthService(db=db)
    ok, details = await service.check_database()

    assert ok is True
    assert details["engine"] == "sqlite"
