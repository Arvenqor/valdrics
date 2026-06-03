<script lang="ts">
	import '../../inventory/inventory.app.css';
	import InventoryPageViewContent from '../../inventory/InventoryPageViewContent.svelte';
	import { inventoryCaptureResponse } from '../../inventory/inventoryCaptureFixture';
	import type {
		InventoryListResponse,
		InventoryQuery,
		InventoryResource,
		InventoryStatusFilter,
		InventoryTypeFilter
	} from '../../inventory/inventoryTypes';

	const data = {
		user: {
			id: 'user-inventory-capture',
			email: 'platform@valdrics.com',
			tenant_id: 'tenant-inventory-capture'
		},
		session: { access_token: 'capture-token' },
		subscription: { tier: 'pro', status: 'active' },
		profile: {
			persona: 'platform',
			role: 'admin',
			platform_operator: false
		}
	};

	let query = $state<InventoryQuery>({
		type: 'all',
		status: 'all',
		search: '',
		page: 1,
		perPage: 40
	});
	let searchValue = $state('');
	let filteredInventory = $derived.by(() => buildFilteredInventory(query));

	function buildFilteredInventory(currentQuery: InventoryQuery): InventoryListResponse {
		const search = currentQuery.search.trim().toLowerCase();
		const items = inventoryCaptureResponse.items.filter((resource) => {
			const matchesType =
				currentQuery.type === 'all' || resource.resource_type === currentQuery.type;
			const matchesStatus =
				currentQuery.status === 'all' || resource.status === currentQuery.status;
			const searchable = [
				resource.name,
				resource.provider,
				resource.region,
				resource.owner_name,
				resource.owner_email,
				resource.team_name,
				resource.source_label,
				...Object.entries(resource.tags).flat()
			]
				.filter(Boolean)
				.join(' ')
				.toLowerCase();
			return matchesType && matchesStatus && (!search || searchable.includes(search));
		});
		const sourceIds = new Set(
			items.map((resource) => resource.source_connection_id ?? resource.id)
		);
		return {
			...inventoryCaptureResponse,
			items,
			total: items.length,
			type: currentQuery.type,
			status: currentQuery.status,
			search: currentQuery.search,
			summary: {
				total: items.length,
				cloud: items.filter((resource) => resource.resource_type === 'cloud').length,
				software: items.filter((resource) => resource.resource_type === 'software').length,
				service: items.filter((resource) => resource.resource_type === 'service').length,
				active: items.filter((resource) => resource.status === 'active').length,
				pending: items.filter((resource) => resource.status === 'pending').length,
				error: items.filter((resource) => resource.status === 'error').length,
				idle: items.filter((resource) => resource.status === 'idle').length,
				shadow: items.filter((resource) => resource.status === 'shadow').length,
				expiring: items.filter((resource) => resource.status === 'expiring').length,
				unowned: items.filter(
					(resource) => !resource.owner_name && !resource.owner_email && !resource.team_name
				).length,
				source_count: sourceIds.size,
				reported_cost_usd: items.reduce((total, resource) => total + resource.monthly_cost, 0)
			}
		};
	}

	function setStatus(status: InventoryStatusFilter) {
		query = { ...query, status, page: 1 };
	}

	function setQuickFilter(type: InventoryTypeFilter, status: InventoryStatusFilter) {
		query = { ...query, type, status, page: 1 };
	}

	function setSearch(search: string) {
		searchValue = search;
		query = { ...query, search, page: 1 };
	}

	async function noop(): Promise<void> {
		return undefined;
	}

	function formatCost(resource: InventoryResource): string {
		if (resource.cost_basis === 'not_reported' || resource.monthly_cost <= 0) {
			return 'Not reported';
		}
		const amount = new Intl.NumberFormat(undefined, {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: resource.monthly_cost >= 1000 ? 0 : 2
		}).format(resource.monthly_cost);
		return resource.cost_basis === 'monthly_cost_usd' ? `${amount}/mo` : `${amount} reported`;
	}

	function formatDate(value: string | null | undefined): string {
		if (!value) return 'No sync yet';
		const parsed = new Date(value);
		if (Number.isNaN(parsed.getTime())) return value;
		return parsed.toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Inventory Capture</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="inventory-capture-shell">
	<div class="inventory-capture" data-inventory-capture>
		<InventoryPageViewContent
			{data}
			loading={false}
			refreshing={false}
			error=""
			inventory={filteredInventory}
			{query}
			{searchValue}
			{setStatus}
			{setQuickFilter}
			{setSearch}
			refresh={noop}
			nextPage={() => undefined}
			previousPage={() => undefined}
			{formatCost}
			{formatDate}
		/>
	</div>
</div>

<style>
	.inventory-capture-shell {
		min-height: 100vh;
		padding: 1rem;
		background: #030912;
	}

	.inventory-capture {
		width: min(100%, 1440px);
		margin: 0 auto;
	}

	:global(.public-site-header),
	:global(.public-site-footer) {
		display: none !important;
	}

	@media (max-width: 760px) {
		.inventory-capture-shell {
			padding: 0;
		}
	}
</style>
