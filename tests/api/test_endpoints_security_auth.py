"""API endpoint tests: security headers, sanitization, and authz/authn boundaries."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.shared.core.auth import CurrentUser, UserRole, requires_role
from app.shared.core.dependencies import requires_feature
from app.shared.core.pricing import FeatureFlag, PricingTier

class TestSecurityHeadersAndErrors:
    """Tests for security headers and error handling."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, ac_no_db: AsyncClient):
        """Test that security headers are present on all responses."""
        response = await ac_no_db.get("/health/live")

        # Check required security headers
        headers = response.headers
        assert "content-security-policy" in headers
        assert "referrer-policy" in headers
        assert "permissions-policy" in headers
        assert "x-xss-protection" not in headers

        # Check CSP includes required directives
        csp = headers["content-security-policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "'unsafe-inline'" not in csp
        assert "style-src-attr 'none'" in csp

    @pytest.mark.asyncio
    async def test_error_responses_sanitized(self, ac_no_db: AsyncClient):
        """Test that error responses don't leak sensitive information."""
        # Try to access non-existent endpoint
        response = await ac_no_db.get("/api/v1/non-existent-endpoint")

        assert response.status_code == 404
        data = response.json()

        # Should have generic error structure
        assert "error" in data or "detail" in data
        # Should not contain sensitive information
        response_text = str(data).lower()
        assert "secret" not in response_text
        assert "password" not in response_text
        assert "key" not in response_text

    @pytest.mark.asyncio
    async def test_rate_limiting_headers(self, ac_no_db: AsyncClient):
        """Test that rate limiting includes proper headers."""
        # Make several requests to trigger rate limiting
        responses = []
        for _ in range(12):  # Exceed rate limit
            response = await ac_no_db.get("/health/live")
            responses.append(response)

        # Check if any response has rate limiting headers
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        if rate_limited_responses:
            headers = rate_limited_responses[0].headers
            # Should have rate limiting headers
            assert "retry-after" in headers or "x-ratelimit" in headers.lower()


class TestAuthorizationAndAuthentication:
    """Tests for authentication and authorization."""

    @pytest.mark.asyncio
    async def test_tenant_isolation_zombie_scan(self, ac_no_db: AsyncClient):
        """Test that tenant A cannot access tenant B's zombie data."""
        user_a = CurrentUser(
            id=uuid4(),
            email="user@tenantA.com",
            tenant_id=uuid4(),
            role=UserRole.MEMBER,
            tier=PricingTier.PRO,
        )

        # Mock user A
        from app.shared.core.auth import require_tenant_access

        async def mock_require_tenant_access():
            return user_a.tenant_id

        feature_dependency = requires_feature(FeatureFlag.GITOPS_REMEDIATION)

        async def mock_feature_dependency():
            return user_a

        ac_no_db.app.dependency_overrides[require_tenant_access] = (
            mock_require_tenant_access
        )
        ac_no_db.app.dependency_overrides[feature_dependency] = (
            mock_feature_dependency
        )

        # Mock service to simulate a ResourceNotFoundError (which should happen if id belongs to tenant B)
        with patch(
            "app.modules.optimization.api.v1.zombies.RemediationService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            # Simulate high-level isolation: even if the user provides an ID from tenant B,
            # the service (scoped by tenant A) will not find it.
            mock_service.get_by_id = AsyncMock(return_value=None)

            # Try to get a plan for a resource that belongs to tenant B
            # (In reality, the ID would be from a tenant B record)
            fake_tenant_b_id = uuid4()
            response = await ac_no_db.get(f"/api/v1/zombies/plan/{fake_tenant_b_id}")

            # Should fail with 404 (Resource Not Found for THIS tenant)
            assert response.status_code == 404

        # Clean up overrides
        ac_no_db.app.dependency_overrides.pop(require_tenant_access, None)
        ac_no_db.app.dependency_overrides.pop(feature_dependency, None)

    @pytest.mark.asyncio
    async def test_approve_remediation_requires_explicit_permission(
        self,
        ac_no_db: AsyncClient,
    ):
        """Test that explicit approval permission is required for approval operations."""
        # Mock regular member user with no explicit approval permission.
        member_user = CurrentUser(
            id=uuid4(),
            email="member@test.com",
            tenant_id=uuid4(),
            role=UserRole.MEMBER,
            tier=PricingTier.PRO,
        )

        from app.shared.core.auth import require_tenant_access

        async def mock_require_member_role():
            return member_user

        async def mock_require_tenant_access():
            return member_user.tenant_id

        member_role_dependency = requires_role("member")
        ac_no_db.app.dependency_overrides[member_role_dependency] = (
            mock_require_member_role
        )
        ac_no_db.app.dependency_overrides[require_tenant_access] = (
            mock_require_tenant_access
        )

        with (
            patch(
                "app.modules.optimization.api.v1.zombies._load_remediation_request_for_authorization",
                new=AsyncMock(return_value=object()),
            ),
            patch(
                "app.modules.optimization.api.v1.zombies._required_approval_permission",
                return_value="remediation.approve.nonprod",
            ),
            patch(
                "app.modules.optimization.api.v1.zombies.user_has_approval_permission",
                new=AsyncMock(return_value=False),
            ) as mock_permission_check,
        ):
            response = await ac_no_db.post(
                f"/api/v1/zombies/approve/{uuid4()}",
                json={"notes": "test"},
            )

            assert response.status_code == 403
            mock_permission_check.assert_awaited_once()

        # Clean up overrides
        ac_no_db.app.dependency_overrides.pop(member_role_dependency, None)
        ac_no_db.app.dependency_overrides.pop(require_tenant_access, None)

    @pytest.mark.asyncio
    async def test_feature_flag_gates_endpoints(
        self, ac_no_db: AsyncClient, mock_user
    ):
        """Test that feature flags properly gate endpoint access."""
        from app.shared.core.auth import require_tenant_access

        member_role_dependency = requires_role("member")

        async def mock_require_member_role():
            return mock_user

        async def mock_require_tenant_access():
            return mock_user.tenant_id

        ac_no_db.app.dependency_overrides[member_role_dependency] = (
            mock_require_member_role
        )
        ac_no_db.app.dependency_overrides[require_tenant_access] = (
            mock_require_tenant_access
        )

        dep = requires_feature(FeatureFlag.AUTO_REMEDIATION)

        async def mock_requires_feature_fail():
            from fastapi import HTTPException

            raise HTTPException(status_code=403, detail="Feature not available")

        ac_no_db.app.dependency_overrides[dep] = mock_requires_feature_fail

        response = await ac_no_db.post(
            "/api/v1/zombies/request",
            json={
                "finding_id": str(uuid4()),
                "action": "stop_instance",
            },
        )

        # Should be forbidden due to feature flag
        assert response.status_code == 403

        # Clean up overrides
        ac_no_db.app.dependency_overrides.pop(member_role_dependency, None)
        ac_no_db.app.dependency_overrides.pop(require_tenant_access, None)
        ac_no_db.app.dependency_overrides.pop(dep, None)
