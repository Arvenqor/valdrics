"""Inventory summary projection helpers."""

from __future__ import annotations

from collections import Counter

from app.schemas.inventory import InventoryResource, InventorySummary


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
