<script lang="ts">
	import { base } from '$app/paths';
	import {
		AlertTriangle,
		Boxes,
		Building2,
		Cloud,
		FileQuestion,
		RefreshCw,
		Search,
		Server,
		ShieldCheck,
		Tags
	} from '@lucide/svelte';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import type {
		InventoryListResponse,
		InventoryQuery,
		InventoryResource,
		InventoryResourceType,
		InventoryStatusFilter,
		InventoryTypeFilter
	} from './inventoryTypes';

	interface Props {
		data: {
			user?: unknown;
		};
		loading: boolean;
		refreshing: boolean;
		error: string;
		inventory: InventoryListResponse | null;
		query: InventoryQuery;
		searchValue: string;
		setStatus: (status: InventoryStatusFilter) => void;
		setQuickFilter: (type: InventoryTypeFilter, status: InventoryStatusFilter) => void;
		setSearch: (search: string) => void;
		refresh: () => Promise<void>;
		nextPage: () => void;
		previousPage: () => void;
		formatCost: (resource: InventoryResource) => string;
		formatDate: (value: string | null | undefined) => string;
	}

	let {
		data,
		loading,
		refreshing,
		error,
		inventory,
		query,
		searchValue,
		setStatus,
		setQuickFilter,
		setSearch,
		refresh,
		nextPage,
		previousPage,
		formatCost,
		formatDate
	}: Props = $props();

	const quickFilters: {
		id: string;
		label: string;
		type: InventoryTypeFilter;
		status: InventoryStatusFilter;
	}[] = [
		{ id: 'all', label: 'All', type: 'all', status: 'all' },
		{ id: 'cloud', label: 'Cloud', type: 'cloud', status: 'all' },
		{ id: 'software', label: 'Software', type: 'software', status: 'all' },
		{ id: 'shadow', label: 'Shadow IT', type: 'all', status: 'shadow' },
		{ id: 'expiring', label: 'Expiring Soon', type: 'all', status: 'expiring' }
	];
	const statusFilters: { id: InventoryStatusFilter; label: string }[] = [
		{ id: 'all', label: 'All status' },
		{ id: 'active', label: 'Active' },
		{ id: 'pending', label: 'Pending' },
		{ id: 'error', label: 'Error' },
		{ id: 'idle', label: 'Idle' },
		{ id: 'shadow', label: 'Shadow' },
		{ id: 'expiring', label: 'Expiring' }
	];

	let summary = $derived(
		inventory?.summary ?? {
			total: 0,
			cloud: 0,
			software: 0,
			service: 0,
			active: 0,
			pending: 0,
			error: 0,
			idle: 0,
			shadow: 0,
			expiring: 0,
			unowned: 0,
			source_count: 0,
			reported_cost_usd: 0
		}
	);
	let items = $derived(inventory?.items ?? []);
	let total = $derived(inventory?.total ?? 0);
	let totalPages = $derived(Math.max(1, Math.ceil(total / query.perPage)));
	let canPageBackward = $derived(query.page > 1);
	let canPageForward = $derived(query.page < totalPages);
	let hasFilters = $derived(query.type !== 'all' || query.status !== 'all' || query.search !== '');

	function metricFormatter(value: number): string {
		return new Intl.NumberFormat(undefined, { notation: 'compact' }).format(value);
	}

	function typeLabel(type: InventoryResourceType): string {
		if (type === 'cloud') return 'Cloud';
		if (type === 'software') return 'Software';
		return 'Service';
	}

	function statusLabel(value: string): string {
		return value
			.split(/[_-]+/)
			.filter(Boolean)
			.map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
			.join(' ');
	}

	function isQuickFilterActive(filter: (typeof quickFilters)[number]): boolean {
		if (filter.id === 'shadow' || filter.id === 'expiring') {
			return query.type === 'all' && query.status === filter.status;
		}
		return query.type === filter.type && query.status !== 'shadow' && query.status !== 'expiring';
	}

	function providerLabel(provider: string): string {
		return provider.replace(/[_-]+/g, ' ').toUpperCase();
	}

	function ownerInitials(resource: InventoryResource): string {
		const label = resource.owner_name ?? resource.team_name ?? 'Owner';
		return label
			.split(/\s+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((part) => part.charAt(0).toUpperCase())
			.join('');
	}

	function costDetail(resource: InventoryResource): string {
		if (resource.cost_basis === 'monthly_cost_usd' && resource.monthly_cost > 0) {
			return `${formatAnnualCost(resource.monthly_cost * 12)}/yr`;
		}
		if (resource.cost_basis === 'reported_cost_usd') {
			return 'reported cost';
		}
		return 'not reported';
	}

	function formatAnnualCost(value: number): string {
		if (!Number.isFinite(value) || value <= 0) return '$0';
		return new Intl.NumberFormat(undefined, {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: value >= 1000 ? 0 : 2
		}).format(value);
	}
</script>

<div class="inventory-page">
	<header class="inventory-page-header">
		<div>
			<h1>Asset Inventory</h1>
			<p>
				{metricFormatter(summary.total)} resources · cloud + software + services · {summary.source_count}
				connected source{summary.source_count === 1 ? '' : 's'}
			</p>
		</div>
		<div class="inventory-page-header__actions">
			<button
				type="button"
				class="inventory-icon-button"
				aria-label="Refresh asset inventory"
				disabled={refreshing || loading}
				onclick={() => void refresh()}
			>
				<RefreshCw size={18} />
			</button>
			<a href={`${base}/connections`} class="inventory-primary-link">
				<Boxes size={16} />
				<span>Connect sources</span>
			</a>
		</div>
	</header>

	<AuthGate
		authenticated={!!data.user}
		action="view asset inventory"
		className="inventory-auth-empty"
	>
		<section class="inventory-toolbar" aria-label="Inventory filters">
			<label class="inventory-search" for="inventory-search">
				<Search size={16} class="inventory-search__icon" />
				<input
					id="inventory-search"
					type="search"
					value={searchValue}
					placeholder="Search resources, owners, teams, tags"
					aria-label="Search asset inventory"
					oninput={(event) => setSearch((event.currentTarget as HTMLInputElement).value)}
				/>
			</label>
			<div class="inventory-segment" role="tablist" aria-label="Quick inventory filters">
				{#each quickFilters as filter}
					<button
						type="button"
						role="tab"
						class="inventory-segment__button"
						class:inventory-segment__button--active={isQuickFilterActive(filter)}
						aria-selected={isQuickFilterActive(filter)}
						onclick={() => setQuickFilter(filter.type, filter.status)}
					>
						{filter.label}
					</button>
				{/each}
			</div>
			<label class="inventory-select-field" for="inventory-status">
				<span>Status</span>
				<select
					id="inventory-status"
					value={query.status}
					onchange={(event) =>
						setStatus((event.currentTarget as HTMLSelectElement).value as InventoryStatusFilter)}
				>
					{#each statusFilters as filter}
						<option value={filter.id}>{filter.label}</option>
					{/each}
				</select>
			</label>
		</section>

		{#if error}
			<div role="alert" class="inventory-alert">
				<AlertTriangle size={18} />
				<p>{error}</p>
			</div>
		{/if}

		{#if loading && !inventory}
			<section class="inventory-table inventory-table--loading" aria-busy="true">
				<div class="inventory-skeleton inventory-skeleton--toolbar"></div>
				{#each [1, 2, 3, 4] as row (row)}
					<div class="inventory-skeleton inventory-skeleton--row"></div>
				{/each}
			</section>
		{:else if items.length === 0}
			<section class="inventory-empty">
				<FileQuestion size={30} />
				<h2>{hasFilters ? 'No matching resources' : 'No inventory resources yet'}</h2>
				<p>
					{hasFilters
						? 'No real source row matches the current filters.'
						: 'Connect cloud, SaaS, license, platform, or hybrid sources to populate inventory.'}
				</p>
				<a href={`${base}/connections`} class="inventory-primary-link">Connect sources</a>
			</section>
		{:else}
			<section class="inventory-table" role="table" aria-label="Asset inventory results">
				<div class="inventory-table__header" role="row">
					<span role="columnheader">Resource</span>
					<span role="columnheader">Owner</span>
					<span role="columnheader">Cost</span>
					<span role="columnheader">Status</span>
					<span role="columnheader">Source</span>
				</div>
				<div class="inventory-table__body" role="rowgroup">
					{#each items as resource (resource.id)}
						<div class="inventory-row" data-resource-id={resource.id} role="row">
							<div class="inventory-row__resource" role="cell">
								<div
									class="inventory-row__icon"
									class:inventory-row__icon--cloud={resource.resource_type === 'cloud'}
									class:inventory-row__icon--software={resource.resource_type === 'software'}
									class:inventory-row__icon--service={resource.resource_type === 'service'}
								>
									{#if resource.resource_type === 'cloud'}
										<Cloud size={17} />
									{:else if resource.resource_type === 'software'}
										<Building2 size={17} />
									{:else}
										<Server size={17} />
									{/if}
								</div>
								<div>
									<h2>{resource.name}</h2>
									<p>
										{providerLabel(resource.provider)}
										<span aria-hidden="true">/</span>
										{typeLabel(resource.resource_type)}
										{#if resource.region}
											<span aria-hidden="true">/</span>
											{resource.region}
										{/if}
									</p>
								</div>
							</div>
							<div class="inventory-row__owner" role="cell">
								{#if resource.owner_name || resource.owner_email || resource.team_name}
									<div class="inventory-owner-chip">
										<div class="inventory-owner-avatar" aria-hidden="true">
											{ownerInitials(resource)}
										</div>
										<div class="inventory-owner">
											<span>{resource.owner_name ?? resource.team_name ?? 'Assigned owner'}</span>
											<small>{resource.owner_email ?? resource.team_name ?? 'Team owner'}</small>
										</div>
									</div>
								{:else}
									<span class="inventory-unowned">Unowned</span>
								{/if}
							</div>
							<div class="inventory-row__cost" role="cell">
								<strong>{formatCost(resource)}</strong>
								<small>{costDetail(resource)}</small>
							</div>
							<div class="inventory-row__status" role="cell">
								<span
									class="inventory-status"
									class:inventory-status--pending={resource.status === 'pending'}
									class:inventory-status--error={resource.status === 'error'}
									class:inventory-status--idle={resource.status === 'idle'}
									class:inventory-status--shadow={resource.status === 'shadow'}
									class:inventory-status--expiring={resource.status === 'expiring'}
								>
									{statusLabel(resource.status)}
								</span>
								<small>{formatDate(resource.last_seen_at)}</small>
							</div>
							<div class="inventory-row__source" role="cell">
								<span>
									{#if resource.source_kind === 'feed'}
										<Tags size={14} />
									{:else}
										<ShieldCheck size={14} />
									{/if}
									{resource.source_label ?? statusLabel(resource.source_kind)}
								</span>
								<a href={`${base}/connections`}>Source</a>
							</div>
						</div>
					{/each}
				</div>
			</section>

			<footer class="inventory-pagination" aria-label="Inventory pagination">
				<span>Page {query.page} of {totalPages} · {total.toLocaleString()} results</span>
				<div>
					<button type="button" disabled={!canPageBackward} onclick={previousPage}>Previous</button>
					<button type="button" disabled={!canPageForward} onclick={nextPage}>Next</button>
				</div>
			</footer>
		{/if}
	</AuthGate>
</div>
