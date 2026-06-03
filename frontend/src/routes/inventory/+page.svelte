<script lang="ts">
	import './inventory.app.css';
	import { goto } from '$app/navigation';
	import { base } from '$app/paths';
	import { onDestroy } from 'svelte';
	import { TimeoutError } from '$lib/fetchWithTimeout';
	import { clientLogger } from '$lib/logging/client';
	import { loadInventorySnapshot } from './inventoryDataApi';
	import InventoryPageViewContent from './InventoryPageViewContent.svelte';
	import type {
		InventoryListResponse,
		InventoryQuery,
		InventoryResource,
		InventoryStatusFilter,
		InventoryTypeFilter
	} from './inventoryTypes';

	let { data } = $props();

	const INVENTORY_REQUEST_TIMEOUT_MS = 8000;
	const INVENTORY_PER_PAGE = 40;

	let loading = $state(true);
	let refreshing = $state(false);
	let error = $state('');
	let inventory = $state<InventoryListResponse | null>(null);
	let searchValue = $state('');
	let query = $state<InventoryQuery>({
		type: 'all',
		status: 'all',
		search: '',
		page: 1,
		perPage: INVENTORY_PER_PAGE
	});
	let searchTimer: ReturnType<typeof setTimeout> | null = null;
	let initialLoadStarted = $state(false);

	function buildInventoryHref(next: InventoryQuery): string {
		const params = new URLSearchParams();
		if (next.type !== 'all') params.set('type', next.type);
		if (next.status !== 'all') params.set('status', next.status);
		if (next.search.trim()) params.set('q', next.search.trim());
		if (next.page > 1) params.set('page', String(next.page));
		const suffix = params.toString();
		return `${base}/inventory${suffix ? `?${suffix}` : ''}`;
	}

	function normalizeLoadError(caught: unknown): string {
		if (caught instanceof TimeoutError) {
			return 'Asset inventory request timed out. Refresh to retry.';
		}
		if (caught instanceof Error && caught.message) {
			return caught.message;
		}
		return 'Failed to load asset inventory.';
	}

	async function loadInventory(next: InventoryQuery = query, options: { silent?: boolean } = {}) {
		if (!data.user || !data.session?.access_token) {
			loading = false;
			refreshing = false;
			return;
		}
		if (options.silent) {
			refreshing = true;
		} else {
			loading = true;
		}
		error = '';
		try {
			inventory = await loadInventorySnapshot(
				data.session.access_token,
				next,
				INVENTORY_REQUEST_TIMEOUT_MS
			);
		} catch (caught) {
			clientLogger.error('Failed to load asset inventory:', caught);
			error = normalizeLoadError(caught);
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	function applyQuery(patch: Partial<InventoryQuery>, options: { debounce?: boolean } = {}) {
		const next: InventoryQuery = {
			...query,
			...patch,
			page: patch.page ?? 1,
			perPage: INVENTORY_PER_PAGE
		};
		query = next;
		void goto(buildInventoryHref(next), {
			keepFocus: true,
			noScroll: true,
			replaceState: true
		});
		const run = () => void loadInventory(next, { silent: true });
		if (searchTimer) {
			clearTimeout(searchTimer);
			searchTimer = null;
		}
		if (options.debounce) {
			searchTimer = setTimeout(run, 300);
			return;
		}
		run();
	}

	function setStatus(status: InventoryStatusFilter) {
		applyQuery({ status });
	}

	function setQuickFilter(type: InventoryTypeFilter, status: InventoryStatusFilter) {
		applyQuery({ type, status });
	}

	function setSearch(search: string) {
		searchValue = search;
		applyQuery({ search }, { debounce: true });
	}

	function nextPage() {
		applyQuery({ page: query.page + 1 });
	}

	function previousPage() {
		applyQuery({ page: Math.max(1, query.page - 1) });
	}

	function formatCost(resource: InventoryResource): string {
		const value = resource.monthly_cost;
		if (resource.cost_basis === 'not_reported' || !Number.isFinite(value) || value <= 0) {
			return 'Not reported';
		}
		const amount = new Intl.NumberFormat(undefined, {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: 0,
			maximumFractionDigits: value >= 1000 ? 0 : 2
		}).format(value);
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

	$effect(() => {
		if (initialLoadStarted) return;
		const initialQuery: InventoryQuery = {
			type: data.inventoryType ?? 'all',
			status: data.inventoryStatus ?? 'all',
			search: data.inventorySearch ?? '',
			page: data.inventoryPage ?? 1,
			perPage: INVENTORY_PER_PAGE
		};
		searchValue = initialQuery.search;
		query = initialQuery;
		initialLoadStarted = true;
		void loadInventory(initialQuery);
	});

	onDestroy(() => {
		if (searchTimer) {
			clearTimeout(searchTimer);
			searchTimer = null;
		}
	});
</script>

<svelte:head>
	<title>Asset Inventory | Valdrics</title>
</svelte:head>

<InventoryPageViewContent
	{data}
	{loading}
	{refreshing}
	{error}
	{inventory}
	{query}
	{searchValue}
	{setStatus}
	{setQuickFilter}
	{setSearch}
	refresh={() => loadInventory(query, { silent: true })}
	{nextPage}
	{previousPage}
	{formatCost}
	{formatDate}
/>
