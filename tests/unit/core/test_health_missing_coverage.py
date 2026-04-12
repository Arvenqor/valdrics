"""
Targeted tests for app/shared/core/health.py missing coverage lines
"""

import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.core.health import HealthService


class TestHealthServiceMissingCoverage:
    """Test health check service missing coverage lines."""

    @pytest_asyncio.fixture
    async def mock_db(self):
        """Create mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest_asyncio.fixture
    async def health_service(self, mock_db):
        """Create health service instance."""
        return HealthService(mock_db)

    @pytest.mark.asyncio
    async def test_check_all_external_services_degraded_only(
        self, health_service, mock_db
    ):
        """Test overall health check when only external services are degraded."""
        with (
            patch.object(
                health_service,
                "_testing_mode",
                return_value=False,
            ),
            patch.object(
                health_service,
                "_check_database",
                return_value={"status": "up", "latency_ms": 10.5},
            ),
            patch.object(
                health_service,
                "_check_cache",
                return_value={"status": "healthy", "latency_ms": 5.2},
            ),
            patch.object(
                health_service,
                "_check_external_services",
                return_value={
                    "status": "degraded",
                    "services": {"aws_sts": {"status": "unhealthy"}},
                },
            ),
            patch.object(
                health_service,
                "_check_circuit_breakers",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_system_resources",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_background_jobs",
                return_value={"status": "healthy"},
            ),
        ):
            result = await health_service.check_all()

            assert result["status"] == "degraded"
            assert result["database"]["status"] == "up"
            assert result["cache"]["status"] == "healthy"
            assert result["external_services"]["status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_all_cache_degraded_only(self, health_service, mock_db):
        """Test overall health check when only cache is degraded."""
        with (
            patch.object(
                health_service,
                "_testing_mode",
                return_value=False,
            ),
            patch.object(
                health_service,
                "_check_database",
                return_value={"status": "up", "latency_ms": 10.5},
            ),
            patch.object(
                health_service,
                "_check_cache",
                return_value={"status": "degraded", "message": "Redis down"},
            ),
            patch.object(
                health_service,
                "_check_external_services",
                return_value={
                    "status": "healthy",
                    "services": {"aws_sts": {"status": "healthy"}},
                },
            ),
            patch.object(
                health_service,
                "_check_circuit_breakers",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_system_resources",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_background_jobs",
                return_value={"status": "healthy"},
            ),
        ):
            result = await health_service.check_all()

            assert result["status"] == "degraded"
            assert result["database"]["status"] == "up"
            assert result["cache"]["status"] == "degraded"
            assert result["external_services"]["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_external_services_disabled_without_probes(
        self, health_service
    ):
        """Test external services health when no probes are configured."""
        result = await health_service._check_external_services()

        assert result["status"] == "disabled"
        assert result["services"] == {}

    @pytest.mark.asyncio
    async def test_check_external_services_unhealthy_probe(
        self, health_service
    ):
        """Test external service probe failure becomes degraded."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with (
            patch.object(
                health_service,
                "_external_service_probes",
                return_value={"status_page": "https://status.example.com/health"},
            ),
            patch("app.shared.core.http.get_http_client") as mock_get_client,
        ):
            mock_get_client.return_value.get = AsyncMock(return_value=mock_response)

            result = await health_service._check_external_services()

        assert result["status"] == "degraded"
        assert result["services"]["status_page"]["response_code"] == 500

    @pytest.mark.asyncio
    async def test_check_all_unhealthy_db_down(self, health_service):
        """Test overall health check when database is down (line 24)."""
        with (
            patch.object(
                health_service,
                "_testing_mode",
                return_value=False,
            ),
            patch.object(
                health_service,
                "_check_database",
                return_value={"status": "down", "error": "Connection failed"},
            ),
            patch.object(
                health_service,
                "_check_cache",
                return_value={"status": "healthy", "latency_ms": 5.2},
            ),
            patch.object(
                health_service,
                "_check_external_services",
                return_value={
                    "status": "healthy",
                    "services": {"status_page": {"status": "healthy"}},
                },
            ),
            patch.object(
                health_service,
                "_check_circuit_breakers",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_system_resources",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_background_jobs",
                return_value={"status": "healthy"},
            ),
        ):
            result = await health_service.check_all()

            assert result["status"] == "unhealthy"
            assert result["database"]["status"] == "down"

    @pytest.mark.asyncio
    async def test_check_database_exception(self, health_service, mock_db):
        """Test database check handling exception (lines 43-45)."""
        mock_db.execute.side_effect = RuntimeError("DB error")
        success, details = await health_service.check_database()

        assert success is False
        assert "DB error" in details["error"]

    @pytest.mark.asyncio
    async def test_check_database_success(self, health_service, mock_db):
        """Test database check success (lines 41-42)."""
        with patch(
            "app.shared.core.health.db_health_check",
            return_value={"status": "up", "latency_ms": 1.0},
        ):
            success, details = await health_service.check_database()

        assert success is True
        assert "latency_ms" in details

    @pytest.mark.asyncio
    async def test_check_all_healthy(self, health_service):
        """Test overall health check when all services are healthy (line 22)."""
        with (
            patch.object(
                health_service,
                "_testing_mode",
                return_value=False,
            ),
            patch.object(
                health_service,
                "_check_database",
                return_value={"status": "up", "latency_ms": 10.5},
            ),
            patch.object(
                health_service,
                "_check_cache",
                return_value={"status": "healthy", "latency_ms": 5.2},
            ),
            patch.object(
                health_service,
                "_check_external_services",
                return_value={
                    "status": "healthy",
                    "services": {"aws_sts": {"status": "healthy"}},
                },
            ),
            patch.object(
                health_service,
                "_check_circuit_breakers",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_system_resources",
                return_value={"status": "healthy"},
            ),
            patch.object(
                health_service,
                "_check_background_jobs",
                return_value={"status": "healthy"},
            ),
        ):
            result = await health_service.check_all()
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_check_external_services_exception(self, health_service):
        """Test external service probe exceptions become unhealthy service entries."""
        with (
            patch.object(
                health_service,
                "_external_service_probes",
                return_value={"status_page": "https://status.example.com/health"},
            ),
            patch("app.shared.core.http.get_http_client") as mock_get_client,
        ):
            mock_get_client.return_value.get = AsyncMock(
                side_effect=RuntimeError("Network fail")
            )

            result = await health_service._check_external_services()

        assert result["status"] == "degraded"
        assert "Network fail" in result["services"]["status_page"]["error"]
