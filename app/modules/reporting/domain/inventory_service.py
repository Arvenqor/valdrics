"""Tenant inventory projection from first-class connection and feed sources."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.aws_connection import AWSConnection
from app.models.azure_connection import AzureConnection
from app.models.discovered_account import DiscoveredAccount
from app.models.gcp_connection import GCPConnection
from app.models.hybrid_connection import HybridConnection
from app.models.license_connection import LicenseConnection
from app.models.platform_connection import PlatformConnection
from app.models.saas_connection import SaaSConnection
from app.schemas.inventory import (
    InventoryCostBasis,
    InventoryResource,
    InventoryResourceStatus,
    InventoryResourceType,
    InventorySummary,
)

VALID_STATUSES: set[InventoryResourceStatus] = {
    "active",
    "pending",
    "error",
    "idle",
    "shadow",
    "expiring",
}
CloudPlusConnection = (
    SaaSConnection | LicenseConnection | PlatformConnection | HybridConnection
)


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _first_text(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = row.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None


def _finite_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not amount.is_finite():
        return None
    return float(amount)


def _feed_cost(row: dict[str, Any]) -> tuple[float, InventoryCostBasis]:
    monthly_cost = _finite_float(row.get("monthly_cost_usd") or row.get("monthly_cost"))
    if monthly_cost is not None:
        return monthly_cost, "monthly_cost_usd"

    reported_cost = _finite_float(
        row.get("cost_usd") or row.get("amount_usd") or row.get("amount_raw")
    )
    if reported_cost is not None:
        return reported_cost, "reported_cost_usd"

    return 0.0, "not_reported"


def _tags(row: dict[str, Any]) -> dict[str, str]:
    raw_tags = row.get("tags")
    if not isinstance(raw_tags, dict):
        return {}

    normalized: dict[str, str] = {}
    for key, value in raw_tags.items():
        key_text = str(key).strip()
        value_text = str(value).strip()
        if key_text and value_text:
            normalized[key_text] = value_text
    return normalized


def _status_from_row(row: dict[str, Any]) -> InventoryResourceStatus:
    status = str(row.get("status") or "active").strip().lower()
    return (
        cast(InventoryResourceStatus, status) if status in VALID_STATUSES else "active"
    )


def _status_from_connection(
    *, is_active: bool, error_message: object
) -> InventoryResourceStatus:
    if error_message:
        return "error"
    return "active" if is_active else "pending"


def _connection_last_seen(connection: object) -> str | None:
    for attribute in (
        "last_ingested_at",
        "last_synced_at",
        "last_verified_at",
        "updated_at",
        "created_at",
    ):
        seen = _iso(getattr(connection, attribute, None))
        if seen:
            return seen
    return None


def _source_tags(**values: object) -> dict[str, str]:
    tags: dict[str, str] = {}
    for key, value in values.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            tags[key] = text
    return tags


class InventoryProjectionService:
    """Build a normalized inventory from existing tenant-owned data."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_resources(self, tenant_id: UUID) -> list[InventoryResource]:
        resources: list[InventoryResource] = []
        resources.extend(await self._cloud_connections(tenant_id))
        resources.extend(await self._aws_discovered_accounts(tenant_id))
        resources.extend(await self._cloud_plus_connections(tenant_id))
        return sorted(
            resources,
            key=lambda item: (item.last_seen_at or "", item.name.lower()),
            reverse=True,
        )

    async def _cloud_connections(self, tenant_id: UUID) -> list[InventoryResource]:
        resources: list[InventoryResource] = []

        aws_result = await self.db.execute(
            select(AWSConnection).where(AWSConnection.tenant_id == tenant_id)
        )
        for aws_connection in aws_result.scalars().all():
            resources.append(
                InventoryResource(
                    id=f"conn:aws:{aws_connection.id}",
                    name=f"AWS account {aws_connection.aws_account_id}",
                    resource_type="cloud",
                    provider="aws",
                    region=aws_connection.region,
                    monthly_cost=0.0,
                    cost_basis="not_reported",
                    status=cast(InventoryResourceStatus, aws_connection.status)
                    if aws_connection.status in VALID_STATUSES
                    else "pending",
                    last_seen_at=_connection_last_seen(aws_connection),
                    tags=_source_tags(
                        aws_account_id=aws_connection.aws_account_id,
                        organization_id=aws_connection.organization_id,
                        cur_status=aws_connection.cur_status,
                    ),
                    source_kind="connection",
                    source_connection_id=str(aws_connection.id),
                    source_label="AWS connection",
                )
            )

        azure_result = await self.db.execute(
            select(AzureConnection).where(AzureConnection.tenant_id == tenant_id)
        )
        for azure_connection in azure_result.scalars().all():
            resources.append(
                InventoryResource(
                    id=f"conn:azure:{azure_connection.id}",
                    name=azure_connection.name,
                    resource_type="cloud",
                    provider="azure",
                    monthly_cost=0.0,
                    cost_basis="not_reported",
                    status=_status_from_connection(
                        is_active=azure_connection.is_active,
                        error_message=azure_connection.error_message,
                    ),
                    last_seen_at=_connection_last_seen(azure_connection),
                    tags=_source_tags(
                        subscription_id=azure_connection.subscription_id,
                        azure_tenant_id=azure_connection.azure_tenant_id,
                        auth_method=azure_connection.auth_method,
                    ),
                    source_kind="connection",
                    source_connection_id=str(azure_connection.id),
                    source_label="Azure connection",
                )
            )

        gcp_result = await self.db.execute(
            select(GCPConnection).where(GCPConnection.tenant_id == tenant_id)
        )
        for gcp_connection in gcp_result.scalars().all():
            resources.append(
                InventoryResource(
                    id=f"conn:gcp:{gcp_connection.id}",
                    name=gcp_connection.name,
                    resource_type="cloud",
                    provider="gcp",
                    monthly_cost=0.0,
                    cost_basis="not_reported",
                    status=_status_from_connection(
                        is_active=gcp_connection.is_active,
                        error_message=gcp_connection.error_message,
                    ),
                    last_seen_at=_connection_last_seen(gcp_connection),
                    tags=_source_tags(
                        project_id=gcp_connection.project_id,
                        billing_project_id=gcp_connection.billing_project_id,
                        billing_dataset=gcp_connection.billing_dataset,
                        billing_table=gcp_connection.billing_table,
                        auth_method=gcp_connection.auth_method,
                    ),
                    source_kind="connection",
                    source_connection_id=str(gcp_connection.id),
                    source_label="GCP connection",
                )
            )

        return resources

    async def _aws_discovered_accounts(
        self, tenant_id: UUID
    ) -> list[InventoryResource]:
        result = await self.db.execute(
            select(DiscoveredAccount, AWSConnection)
            .join(
                AWSConnection,
                DiscoveredAccount.management_connection_id == AWSConnection.id,
            )
            .where(
                AWSConnection.tenant_id == tenant_id,
                DiscoveredAccount.status.notin_(["ignored", "stale"]),
            )
        )

        resources: list[InventoryResource] = []
        for account, management_connection in result.all():
            status: InventoryResourceStatus = (
                "active" if account.status == "linked" else "pending"
            )
            resources.append(
                InventoryResource(
                    id=f"disc:aws:{account.id}",
                    name=account.name or f"AWS account {account.account_id}",
                    resource_type="cloud",
                    provider="aws",
                    region=management_connection.region,
                    monthly_cost=0.0,
                    cost_basis="not_reported",
                    status=status,
                    last_seen_at=_iso(account.last_discovered_at),
                    tags=_source_tags(
                        account_id=account.account_id,
                        discovery_status=account.status,
                        management_account=management_connection.aws_account_id,
                    ),
                    source_kind="discovered_account",
                    source_connection_id=str(management_connection.id),
                    source_label="AWS Organizations discovery",
                )
            )
        return resources

    async def _cloud_plus_connections(self, tenant_id: UUID) -> list[InventoryResource]:
        resources: list[InventoryResource] = []

        resources.extend(
            await self._feed_backed_resources(
                tenant_id=tenant_id,
                model=SaaSConnection,
                kind="saas",
                feed_attribute="spend_feed",
                resource_type="software",
                source_label="SaaS spend feed",
            )
        )
        resources.extend(
            await self._feed_backed_resources(
                tenant_id=tenant_id,
                model=LicenseConnection,
                kind="license",
                feed_attribute="license_feed",
                resource_type="software",
                source_label="License feed",
            )
        )
        resources.extend(
            await self._feed_backed_resources(
                tenant_id=tenant_id,
                model=PlatformConnection,
                kind="platform",
                feed_attribute="spend_feed",
                resource_type="service",
                source_label="Platform spend feed",
            )
        )
        resources.extend(
            await self._feed_backed_resources(
                tenant_id=tenant_id,
                model=HybridConnection,
                kind="hybrid",
                feed_attribute="spend_feed",
                resource_type="service",
                source_label="Hybrid infrastructure feed",
            )
        )
        return resources

    async def _feed_backed_resources(
        self,
        *,
        tenant_id: UUID,
        model: type[CloudPlusConnection],
        kind: str,
        feed_attribute: str,
        resource_type: str,
        source_label: str,
    ) -> list[InventoryResource]:
        result = await self.db.execute(
            select(model).where(model.tenant_id == tenant_id)
        )
        resources: list[InventoryResource] = []

        for raw_connection in result.scalars().all():
            connection = cast(CloudPlusConnection, raw_connection)
            feed = getattr(connection, feed_attribute, None)
            if not isinstance(feed, list) or not feed:
                resources.append(
                    self._connection_placeholder(
                        connection=connection,
                        kind=kind,
                        resource_type=resource_type,
                        source_label=source_label,
                    )
                )
                continue

            for index, row in enumerate(feed):
                if not isinstance(row, dict):
                    continue
                resources.append(
                    self._feed_resource(
                        connection=connection,
                        kind=kind,
                        row=row,
                        index=index,
                        resource_type=resource_type,
                        source_label=source_label,
                    )
                )

        return resources

    def _connection_placeholder(
        self,
        *,
        connection: CloudPlusConnection,
        kind: str,
        resource_type: str,
        source_label: str,
    ) -> InventoryResource:
        return InventoryResource(
            id=f"conn:{kind}:{connection.id}",
            name=connection.name,
            resource_type=cast(InventoryResourceType, resource_type),
            provider=connection.vendor,
            monthly_cost=0.0,
            cost_basis="not_reported",
            status=_status_from_connection(
                is_active=connection.is_active,
                error_message=connection.error_message,
            ),
            last_seen_at=_connection_last_seen(connection),
            tags=_source_tags(auth_method=connection.auth_method, source=kind),
            source_kind="connection",
            source_connection_id=str(connection.id),
            source_label=source_label,
        )

    def _feed_resource(
        self,
        *,
        connection: CloudPlusConnection,
        kind: str,
        row: dict[str, Any],
        index: int,
        resource_type: str,
        source_label: str,
    ) -> InventoryResource:
        monthly_cost, cost_basis = _feed_cost(row)
        name = (
            _first_text(
                row,
                (
                    "resource_name",
                    "name",
                    "service",
                    "product",
                    "sku_description",
                    "resource_id",
                    "id",
                ),
            )
            or connection.name
        )
        provider = (
            _first_text(row, ("provider", "cloud_provider", "vendor"))
            or connection.vendor
        )
        region = _first_text(row, ("region", "location", "zone"))
        last_seen = _first_text(
            row,
            (
                "last_seen_at",
                "timestamp",
                "recorded_at",
                "usage_start_time",
                "date",
                "month",
            ),
        )

        return InventoryResource(
            id=f"feed:{kind}:{connection.id}:{index}",
            name=name,
            resource_type=cast(InventoryResourceType, resource_type),
            provider=provider,
            region=region,
            owner_name=_first_text(row, ("owner_name", "owner", "business_owner")),
            owner_email=_first_text(row, ("owner_email", "owner_mail", "email")),
            team_name=_first_text(row, ("team_name", "team", "cost_center")),
            monthly_cost=monthly_cost,
            cost_basis=cost_basis,
            status=_status_from_row(row),
            last_seen_at=last_seen,
            tags=_tags(row),
            source_kind="feed",
            source_connection_id=str(connection.id),
            source_label=source_label,
        )


def build_inventory_summary(resources: list[InventoryResource]) -> InventorySummary:
    type_counts = Counter(resource.resource_type for resource in resources)
    status_counts = Counter(resource.status for resource in resources)
    source_ids = {
        resource.source_connection_id
        for resource in resources
        if resource.source_connection_id
    }
    reported_cost_usd = sum(
        resource.monthly_cost
        for resource in resources
        if resource.cost_basis != "not_reported"
    )

    return InventorySummary(
        total=len(resources),
        cloud=type_counts["cloud"],
        software=type_counts["software"],
        service=type_counts["service"],
        active=status_counts["active"],
        pending=status_counts["pending"],
        error=status_counts["error"],
        idle=status_counts["idle"],
        shadow=status_counts["shadow"],
        expiring=status_counts["expiring"],
        unowned=sum(
            1
            for resource in resources
            if not resource.owner_name and not resource.owner_email
        ),
        source_count=len(source_ids),
        reported_cost_usd=round(reported_cost_usd, 2),
    )
