"""API endpoint tests: input validation and background job endpoint contracts."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.shared.core.auth import require_tenant_access, requires_role
from app.shared.core.dependencies import requires_feature
from app.shared.core.pricing import FeatureFlag


def _set_member_tenant_access(client: AsyncClient, user) -> object:
    member_role_dependency = requires_role("member")

    async def mock_require_member_role():
        return user

    async def mock_require_tenant_access():
        return user.tenant_id

    client.app.dependency_overrides[member_role_dependency] = mock_require_member_role
    client.app.dependency_overrides[require_tenant_access] = mock_require_tenant_access
    return member_role_dependency


def _set_admin_access(client: AsyncClient, user) -> object:
    admin_role_dependency = requires_role("admin")

    async def mock_require_admin_role():
        return user

    client.app.dependency_overrides[admin_role_dependency] = mock_require_admin_role
    return admin_role_dependency


def _set_feature_tenant_access(client: AsyncClient, feature: FeatureFlag, user) -> object:
    feature_dependency = requires_feature(feature)

    async def mock_feature_dependency():
        return user

    async def mock_require_tenant_access():
        return user.tenant_id

    client.app.dependency_overrides[feature_dependency] = mock_feature_dependency
    client.app.dependency_overrides[require_tenant_access] = mock_require_tenant_access
    return feature_dependency


def _clear_overrides(client: AsyncClient, *dependencies: object) -> None:
    for dependency in dependencies:
        client.app.dependency_overrides.pop(dependency, None)


class TestInputValidation:
    """Tests for API input validation."""

    @pytest.mark.asyncio
    async def test_invalid_json_handling(self, ac_no_db: AsyncClient):
        response = await ac_no_db.post(
            "/api/v1/zombies/request",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_required_fields(
        self, ac_no_db: AsyncClient, mock_user
    ) -> None:
        feature_dependency = _set_feature_tenant_access(
            ac_no_db, FeatureFlag.AUTO_REMEDIATION, mock_user
        )

        response = await ac_no_db.post(
            "/api/v1/zombies/request", json={"action": "stop_instance"}
        )

        assert response.status_code == 422
        _clear_overrides(ac_no_db, feature_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_invalid_enum_values(self, ac_no_db: AsyncClient, mock_user) -> None:
        feature_dependency = _set_feature_tenant_access(
            ac_no_db, FeatureFlag.AUTO_REMEDIATION, mock_user
        )

        response = await ac_no_db.post(
            "/api/v1/zombies/request",
            json={
                "finding_id": str(uuid4()),
                "action": "invalid_action_name",
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "invalid_remediation_action" in data.get("error", {}).get("code", "")
        _clear_overrides(ac_no_db, feature_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_uuid_validation(self, ac_no_db: AsyncClient, mock_user) -> None:
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        response = await ac_no_db.post(
            "/api/v1/zombies/approve/invalid-uuid", json={"notes": "test"}
        )

        assert response.status_code == 422
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)


class TestBackgroundJobsAPI:
    """Tests for background jobs API endpoints."""

    @pytest.mark.asyncio
    async def test_job_status_endpoint(self, ac_no_db: AsyncClient, mock_user) -> None:
        admin_role_dependency = _set_admin_access(ac_no_db, mock_user)

        response = await ac_no_db.get("/api/v1/jobs/status")

        assert response.status_code == 200
        _clear_overrides(ac_no_db, admin_role_dependency)

    @pytest.mark.asyncio
    async def test_job_cancellation_endpoint(
        self, ac_no_db: AsyncClient, mock_user
    ) -> None:
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        response = await ac_no_db.post(f"/api/v1/jobs/cancel/{uuid4()}")

        assert response.status_code == 404
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)
