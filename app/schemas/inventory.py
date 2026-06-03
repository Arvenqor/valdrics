"""Inventory schemas for tenant-owned cloud, software, and service assets."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class DiscoveredResource(BaseModel):
    """Normalized representation of a discovered cloud resource."""

    id: str
    arn: Optional[str] = None
    service: str
    resource_type: str
    region: str
    provider: str
    tags: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CloudInventory(BaseModel):
    """Account-level inventory of discovered resources."""

    tenant_id: str
    provider: str
    resources: List[DiscoveredResource] = Field(default_factory=list)
    total_count: int = 0
    discovery_method: str  # e.g., "resource-explorer-2", "native-api", "tagging-api"
    discovered_at: str


InventoryResourceType = Literal["cloud", "software", "service"]
InventoryResourceStatus = Literal[
    "active",
    "pending",
    "error",
    "idle",
    "shadow",
    "expiring",
]
InventorySourceKind = Literal["connection", "feed", "discovered_account"]
InventoryCostBasis = Literal["monthly_cost_usd", "reported_cost_usd", "not_reported"]


class InventoryResource(BaseModel):
    """Normalized asset inventory row derived from real Valdrics sources."""

    id: str
    name: str
    resource_type: InventoryResourceType
    provider: str
    region: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    team_name: str | None = None
    monthly_cost: float = 0.0
    cost_basis: InventoryCostBasis = "not_reported"
    status: InventoryResourceStatus = "pending"
    last_seen_at: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    source_kind: InventorySourceKind
    source_connection_id: str | None = None
    source_label: str | None = None


class InventorySummary(BaseModel):
    """Counts and reported-cost totals for the complete tenant inventory view."""

    total: int = 0
    cloud: int = 0
    software: int = 0
    service: int = 0
    active: int = 0
    pending: int = 0
    error: int = 0
    idle: int = 0
    shadow: int = 0
    expiring: int = 0
    unowned: int = 0
    source_count: int = 0
    reported_cost_usd: float = 0.0


class InventoryListResponse(BaseModel):
    """Paginated inventory response."""

    items: list[InventoryResource]
    total: int
    page: int
    per_page: int
    type: Literal["all", "cloud", "software", "service"]
    status: Literal[
        "all",
        "active",
        "pending",
        "error",
        "idle",
        "shadow",
        "expiring",
    ]
    search: str = ""
    summary: InventorySummary = Field(default_factory=InventorySummary)
