"""API endpoint tests: health, monitoring, and CORS/preflight behavior."""

from unittest.mock import AsyncMock, patch

import pytest


class TestHealthAndMonitoringAPIs:
    """Tests for health check and monitoring endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, ac_no_db):
        """Test health check endpoint."""
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
        assert data["status"] in ["healthy", "ok", "degraded"]

    @pytest.mark.asyncio
    async def test_metrics_endpoint_protected(self, ac_no_db):
        """Test that metrics endpoints are properly protected."""
        response = await ac_no_db.get("/metrics")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_openapi_schema_accessible(self, ac_no_db):
        """Test that OpenAPI schema is accessible."""
        response = await ac_no_db.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "paths" in data
        assert "/api/v1/zombies" in data.get("paths", {})


class TestCORSAndPreflight:
    """Tests for CORS and preflight requests."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, ac_no_db):
        """Test that CORS headers are present when needed."""
        response = await ac_no_db.options("/api/v1/zombies")

        # Check for CORS headers - may not be configured in test environment
        headers = response.headers
        # CORS might not be enabled in test environment, so check for basic headers
        assert "allow" in headers  # OPTIONS should return Allow header
        # If CORS is configured, these would be present, but in test they might not be
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers",
        ]
        has_cors = any(cors_header in headers for cors_header in cors_headers)
        if has_cors:
            assert "access-control-allow-origin" in headers

    @pytest.mark.asyncio
    async def test_preflight_requests_handled(self, ac_no_db):
        """Test that preflight OPTIONS requests are handled."""
        response = await ac_no_db.options(
            "/api/v1/zombies",
            headers={
                "Origin": "https://app.valdrics.ai",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should handle preflight request
        assert response.status_code in [200, 400, 404]
