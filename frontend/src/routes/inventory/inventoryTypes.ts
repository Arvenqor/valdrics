export type InventoryResourceType = 'cloud' | 'software' | 'service';
export type InventoryTypeFilter = 'all' | InventoryResourceType;
export type InventoryStatusFilter =
	'all' | 'active' | 'pending' | 'error' | 'idle' | 'shadow' | 'expiring';
type InventorySourceKind = 'connection' | 'feed' | 'discovered_account';
type InventoryCostBasis = 'monthly_cost_usd' | 'reported_cost_usd' | 'not_reported';

export interface InventoryResource {
	id: string;
	name: string;
	resource_type: InventoryResourceType;
	provider: string;
	region?: string | null;
	owner_name?: string | null;
	owner_email?: string | null;
	team_name?: string | null;
	monthly_cost: number;
	cost_basis: InventoryCostBasis;
	status: Exclude<InventoryStatusFilter, 'all'>;
	last_seen_at?: string | null;
	tags: Record<string, string>;
	source_kind: InventorySourceKind;
	source_connection_id?: string | null;
	source_label?: string | null;
}

interface InventorySummary {
	total: number;
	cloud: number;
	software: number;
	service: number;
	active: number;
	pending: number;
	error: number;
	idle: number;
	shadow: number;
	expiring: number;
	unowned: number;
	source_count: number;
	reported_cost_usd: number;
}

export interface InventoryListResponse {
	items: InventoryResource[];
	total: number;
	page: number;
	per_page: number;
	type: InventoryTypeFilter;
	status: InventoryStatusFilter;
	search: string;
	summary: InventorySummary;
}

export interface InventoryQuery {
	type: InventoryTypeFilter;
	status: InventoryStatusFilter;
	search: string;
	page: number;
	perPage: number;
}
