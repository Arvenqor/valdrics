"""Zombie API endpoint tests: scan, request creation, and pending/history flows."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.models.remediation import (
    RemediationAction,
    RemediationRequest,
    RemediationStatus,
)
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


def _build_remediation_request(*, tenant_id, status: RemediationStatus) -> RemediationRequest:
    request = RemediationRequest(
        tenant_id=tenant_id,
        resource_id="i-test123",
        resource_type="ec2_instance",
        action=RemediationAction.STOP_INSTANCE,
        status=status,
        requested_by_user_id=uuid4(),
        estimated_monthly_savings=Decimal("50.00"),
    )
    request.finding_id = uuid4()
    return request


class TestZombieAPIScanAndRequests:
    """Tests for zombie scan and remediation request/list flows."""

    @pytest.mark.asyncio
    async def test_scan_zombies_unauthenticated(self, ac_no_db: AsyncClient):
        response = await ac_no_db.get("/api/v1/zombies")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_scan_zombies_foreground_success(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch("app.modules.optimization.api.v1.zombies.ZombieService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.scan_for_tenant = AsyncMock(
                return_value={
                    "zombies_found": 2,
                    "total_potential_savings": 150.0,
                    "zombies": [
                        {
                            "resource_id": "i-unused1",
                            "resource_type": "ec2_instance",
                            "monthly_cost": 75.0,
                        },
                        {
                            "resource_id": "vol-unused1",
                            "resource_type": "ebs_volume",
                            "monthly_cost": 75.0,
                        },
                    ],
                }
            )

            response = await ac_no_db.get(
                "/api/v1/zombies", params={"region": "us-east-1"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["zombies_found"] == 2
        assert data["total_potential_savings"] == 150.0
        assert len(data["zombies"]) == 2
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_scan_zombies_background_enqueue(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch("app.modules.optimization.api.v1.zombies.enqueue_job") as mock_enqueue:
            mock_job = MagicMock()
            mock_job.id = uuid4()
            mock_enqueue.return_value = mock_job

            response = await ac_no_db.get(
                "/api/v1/zombies",
                params={"background": True, "region": "us-east-1"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "job_id" in data
        mock_enqueue.assert_called_once()
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_scan_zombies_rate_limiting(self, ac_no_db: AsyncClient, mock_user):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch("app.modules.optimization.api.v1.zombies.ZombieService") as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.scan_for_tenant = AsyncMock(
                return_value={
                    "zombies_found": 0,
                    "total_potential_savings": 0.0,
                    "zombies": [],
                }
            )

            responses = []
            for _ in range(15):
                responses.append(
                    await ac_no_db.get(
                        "/api/v1/zombies", params={"region": "us-east-1"}
                    )
                )

        assert all(response.status_code == 200 for response in responses)
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_create_remediation_request_success(
        self, ac_no_db: AsyncClient, mock_user
    ):
        feature_dependency = _set_feature_tenant_access(
            ac_no_db, FeatureFlag.AUTO_REMEDIATION, mock_user
        )
        request_data = {
            "finding_id": str(uuid4()),
            "action": "stop_instance",
        }

        with patch(
            "app.modules.optimization.api.v1.zombies.RemediationService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_result = MagicMock()
            mock_result.id = uuid4()
            mock_service.create_request_from_finding = AsyncMock(return_value=mock_result)

            response = await ac_no_db.post("/api/v1/zombies/request", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert "request_id" in data
        _clear_overrides(ac_no_db, feature_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_create_remediation_request_invalid_action(
        self, ac_no_db: AsyncClient, mock_user
    ):
        feature_dependency = _set_feature_tenant_access(
            ac_no_db, FeatureFlag.AUTO_REMEDIATION, mock_user
        )
        request_data = {
            "finding_id": str(uuid4()),
            "action": "invalid_action",
        }

        response = await ac_no_db.post("/api/v1/zombies/request", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert "invalid_remediation_action" in data.get("error", {}).get("code", "")
        _clear_overrides(ac_no_db, feature_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_list_pending_requests_success(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch(
            "app.modules.optimization.api.v1.zombies.RemediationService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            pending_request = _build_remediation_request(
                tenant_id=mock_user.tenant_id,
                status=RemediationStatus.PENDING,
            )
            pending_request.finding_snapshot = {
                "status": "open",
                "category": "idle_instances",
            }
            mock_service.list_pending = AsyncMock(return_value=[pending_request])

            response = await ac_no_db.get("/api/v1/zombies/pending")

        assert response.status_code == 200
        data = response.json()
        assert data["pending_count"] == 1
        assert len(data["requests"]) == 1
        assert data["requests"][0]["resource_id"] == "i-test123"
        assert data["requests"][0]["status"] == "pending"
        assert data["requests"][0]["finding_status"] == "open"
        assert data["requests"][0]["finding_category"] == "idle_instances"
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_list_pending_requests_pagination(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch(
            "app.modules.optimization.api.v1.zombies.RemediationService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            mock_service.list_pending = AsyncMock(return_value=[])

            response = await ac_no_db.get(
                "/api/v1/zombies/pending", params={"limit": 10, "offset": 5}
            )

        assert response.status_code == 200
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_list_pending_requests_invalid_pagination(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        response = await ac_no_db.get("/api/v1/zombies/pending", params={"limit": 101})

        assert response.status_code == 422
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)

    @pytest.mark.asyncio
    async def test_list_remediation_history_success(
        self, ac_no_db: AsyncClient, mock_user
    ):
        member_role_dependency = _set_member_tenant_access(ac_no_db, mock_user)

        with patch(
            "app.modules.optimization.api.v1.zombies.RemediationService"
        ) as mock_service_cls:
            mock_service = mock_service_cls.return_value
            completed_request = _build_remediation_request(
                tenant_id=mock_user.tenant_id,
                status=RemediationStatus.COMPLETED,
            )
            completed_request.executed_at = datetime.now(timezone.utc)
            completed_request.finding_snapshot = {
                "status": "resolved",
                "category": "idle_instances",
            }
            mock_service.list_history = AsyncMock(return_value=[completed_request])

            response = await ac_no_db.get("/api/v1/zombies/history")

        assert response.status_code == 200
        data = response.json()
        assert data["history_count"] == 1
        assert data["status"] == "completed"
        assert len(data["requests"]) == 1
        assert data["requests"][0]["status"] == "completed"
        assert data["requests"][0]["finding_status"] == "resolved"
        assert data["requests"][0]["finding_category"] == "idle_instances"
        assert data["requests"][0]["executed_at"] is not None
        _clear_overrides(ac_no_db, member_role_dependency, require_tenant_access)
