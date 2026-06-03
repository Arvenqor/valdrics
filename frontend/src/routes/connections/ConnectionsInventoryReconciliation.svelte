<script lang="ts">
	import { base } from '$app/paths';
	import { getUpgradePrompt } from '$lib/pricing/upgradePrompt';
	import type { CloudConnection, DiscoveredAccount } from './connectionsDataApi';

	type SourceFilter = 'all' | 'cloud' | 'saas' | 'license' | 'platform' | 'hybrid' | 'org';
	type SourceStatusKind = 'active' | 'pending' | 'warning';

	interface SourceRow {
		id: string;
		filter: SourceFilter;
		source: string;
		scope: string;
		detail: string;
		status: string;
		statusKind: SourceStatusKind;
		searchText: string;
	}

	interface Props {
		loadingAWS: boolean;
		loadingAzure: boolean;
		loadingGCP: boolean;
		loadingSaaS: boolean;
		loadingLicense: boolean;
		loadingPlatform: boolean;
		loadingHybrid: boolean;
		loadingDiscovered: boolean;
		awsConnections: CloudConnection[];
		azureConnections: CloudConnection[];
		gcpConnections: CloudConnection[];
		saasConnections: CloudConnection[];
		licenseConnections: CloudConnection[];
		platformConnections: CloudConnection[];
		hybridConnections: CloudConnection[];
		discoveredAccounts: DiscoveredAccount[];
		canUseCloudPlusFeatures: () => boolean;
	}

	let {
		loadingAWS,
		loadingAzure,
		loadingGCP,
		loadingSaaS,
		loadingLicense,
		loadingPlatform,
		loadingHybrid,
		loadingDiscovered,
		awsConnections,
		azureConnections,
		gcpConnections,
		saasConnections,
		licenseConnections,
		platformConnections,
		hybridConnections,
		discoveredAccounts,
		canUseCloudPlusFeatures
	}: Props = $props();

	const FILTERS: { id: SourceFilter; label: string }[] = [
		{ id: 'all', label: 'All' },
		{ id: 'cloud', label: 'Cloud' },
		{ id: 'saas', label: 'SaaS' },
		{ id: 'license', label: 'License' },
		{ id: 'platform', label: 'Platform' },
		{ id: 'hybrid', label: 'Hybrid' },
		{ id: 'org', label: 'Org' }
	];

	let activeFilter = $state<SourceFilter>('all');
	let searchValue = $state('');

	const cloudPlusUpgradePrompt = getUpgradePrompt('pro', 'Cloud+ connectors');
	const loaded = $derived(
		!loadingAWS &&
			!loadingAzure &&
			!loadingGCP &&
			!loadingSaaS &&
			!loadingLicense &&
			!loadingPlatform &&
			!loadingHybrid
	);
	const cloudPlusAllowed = $derived(canUseCloudPlusFeatures());
	const publicCloudCount = $derived(
		awsConnections.length + azureConnections.length + gcpConnections.length
	);
	const softwareLicenseCount = $derived(saasConnections.length + licenseConnections.length);
	const platformHybridCount = $derived(platformConnections.length + hybridConnections.length);
	const linkedOrgAccounts = $derived(
		discoveredAccounts.filter((account) => account.status === 'linked').length
	);
	const pendingOrgAccounts = $derived(
		discoveredAccounts.filter((account) => account.status === 'discovered').length
	);
	const rows = $derived(buildRows());
	const filteredRows = $derived(filterRows(rows, activeFilter, searchValue));

	function normalizeStatus(value: string | undefined): string {
		const status = value?.trim().toLowerCase();
		if (!status) return '';
		return status.replace(/_/g, ' ');
	}

	function sourceStatus(conn: CloudConnection): { label: string; kind: SourceStatusKind } {
		const status = normalizeStatus(conn.status);
		if (status === 'active' || conn.is_active === true) {
			return { label: 'Verified', kind: 'active' };
		}
		if (status === 'error' || status === 'failed') {
			return { label: 'Needs attention', kind: 'warning' };
		}
		if (conn.is_active === false || status === 'pending') {
			return { label: 'Pending verification', kind: 'pending' };
		}
		return { label: status || 'Connected', kind: 'active' };
	}

	function pushRow(rows: SourceRow[], row: Omit<SourceRow, 'searchText'>): void {
		rows.push({
			...row,
			searchText: [row.source, row.scope, row.detail, row.status].join(' ').toLowerCase()
		});
	}

	function buildRows(): SourceRow[] {
		const next: SourceRow[] = [];

		for (const conn of awsConnections) {
			const status = sourceStatus(conn);
			const accountId = conn.aws_account_id ?? 'unknown account';
			pushRow(next, {
				id: `aws-${conn.id}`,
				filter: 'cloud',
				source: `AWS account ${accountId}`,
				scope: conn.is_management_account ? 'Management account' : 'Member account',
				detail: conn.organization_id
					? `Organization ${conn.organization_id}`
					: 'Global resource scope',
				status: status.label,
				statusKind: status.kind
			});
		}

		for (const conn of azureConnections) {
			const status = sourceStatus(conn);
			pushRow(next, {
				id: `azure-${conn.id}`,
				filter: 'cloud',
				source: conn.name || 'Azure subscription',
				scope: conn.subscription_id ? `Subscription ${conn.subscription_id}` : 'Azure tenant',
				detail: conn.azure_tenant_id ? `Tenant ${conn.azure_tenant_id}` : 'Identity federation',
				status: status.label,
				statusKind: status.kind
			});
		}

		for (const conn of gcpConnections) {
			const status = sourceStatus(conn);
			const billingDetail =
				conn.billing_project_id && conn.billing_dataset
					? `Billing export ${conn.billing_project_id}.${conn.billing_dataset}`
					: 'Workload identity or service account';
			pushRow(next, {
				id: `gcp-${conn.id}`,
				filter: 'cloud',
				source: conn.name || 'GCP project',
				scope: conn.project_id ? `Project ${conn.project_id}` : 'GCP project',
				detail: billingDetail,
				status: status.label,
				statusKind: status.kind
			});
		}

		addCloudPlusRows(next, 'saas', 'SaaS spend feed', saasConnections);
		addCloudPlusRows(next, 'license', 'License seat feed', licenseConnections);
		addCloudPlusRows(next, 'platform', 'Internal platform feed', platformConnections);
		addCloudPlusRows(next, 'hybrid', 'Private infrastructure feed', hybridConnections);

		for (const account of discoveredAccounts) {
			pushRow(next, {
				id: `org-${account.id}`,
				filter: 'org',
				source: account.name || `AWS account ${account.account_id}`,
				scope: `AWS Organizations account ${account.account_id}`,
				detail: account.email || 'No account email reported',
				status: account.status === 'linked' ? 'Linked' : 'Discovered',
				statusKind: account.status === 'linked' ? 'active' : 'pending'
			});
		}

		return next;
	}

	function addCloudPlusRows(
		rows: SourceRow[],
		filter: Exclude<SourceFilter, 'all' | 'cloud' | 'org'>,
		fallbackSource: string,
		connections: CloudConnection[]
	): void {
		for (const conn of connections) {
			const status = sourceStatus(conn);
			pushRow(rows, {
				id: `${filter}-${conn.id}`,
				filter,
				source: conn.name || fallbackSource,
				scope: conn.vendor ? `Vendor ${conn.vendor}` : fallbackSource,
				detail: conn.auth_method ? `Auth method ${conn.auth_method}` : 'Manual or native connector',
				status: status.label,
				statusKind: status.kind
			});
		}
	}

	function filterRows(
		rowsToFilter: SourceRow[],
		filter: SourceFilter,
		search: string
	): SourceRow[] {
		const needle = search.trim().toLowerCase();
		return rowsToFilter.filter((row) => {
			const matchesFilter = filter === 'all' || row.filter === filter;
			const matchesSearch = !needle || row.searchText.includes(needle);
			return matchesFilter && matchesSearch;
		});
	}
</script>

<section class="connections-inventory" aria-labelledby="connections-inventory-title">
	<div class="connections-inventory__header">
		<div>
			<h2 id="connections-inventory-title" class="connections-inventory__title">
				Inventory source registry
			</h2>
			<p class="connections-inventory__subtitle">
				Connection-backed source coverage for cloud, software, license, platform, and private
				infrastructure inventory.
			</p>
		</div>
		<a href={`${base}/onboarding`} class="btn btn-secondary connections-inventory__cta">
			Connect source
		</a>
	</div>

	<div class="connections-inventory__metrics" aria-label="Inventory source coverage">
		<div class="connections-inventory__metric">
			<span class="connections-inventory__metric-icon connections-inventory__metric-icon--cloud"
			></span>
			<p class="connections-inventory__metric-value">{publicCloudCount}</p>
			<p class="connections-inventory__metric-label">Public cloud accounts</p>
			<p class="connections-inventory__metric-sub">
				AWS {awsConnections.length} · Azure {azureConnections.length} · GCP {gcpConnections.length}
			</p>
		</div>

		<div class="connections-inventory__metric">
			<span class="connections-inventory__metric-icon connections-inventory__metric-icon--software"
			></span>
			<p class="connections-inventory__metric-value">{softwareLicenseCount}</p>
			<p class="connections-inventory__metric-label">Software and license feeds</p>
			<p class="connections-inventory__metric-sub">
				SaaS {saasConnections.length} · License {licenseConnections.length}
			</p>
		</div>

		<div class="connections-inventory__metric">
			<span class="connections-inventory__metric-icon connections-inventory__metric-icon--platform"
			></span>
			<p class="connections-inventory__metric-value">{platformHybridCount}</p>
			<p class="connections-inventory__metric-label">Platform and hybrid feeds</p>
			<p class="connections-inventory__metric-sub">
				Platform {platformConnections.length} · Hybrid {hybridConnections.length}
			</p>
		</div>

		<div class="connections-inventory__metric">
			<span class="connections-inventory__metric-icon connections-inventory__metric-icon--org"
			></span>
			<p class="connections-inventory__metric-value">
				{loadingDiscovered ? 'Syncing' : `${linkedOrgAccounts} / ${discoveredAccounts.length}`}
			</p>
			<p class="connections-inventory__metric-label">AWS org accounts linked</p>
			<p class="connections-inventory__metric-sub">
				{pendingOrgAccounts} pending account{pendingOrgAccounts === 1 ? '' : 's'}
			</p>
		</div>
	</div>

	<div class="connections-inventory__toolbar">
		<label class="connections-inventory__search">
			<span class="sr-only">Search inventory sources</span>
			<svg
				class="connections-inventory__search-icon"
				width="15"
				height="15"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				aria-hidden="true"
			>
				<circle cx="11" cy="11" r="8" />
				<path d="m21 21-4.35-4.35" />
			</svg>
			<input
				class="connections-inventory__search-input"
				type="search"
				placeholder="Search sources, vendors, scopes"
				bind:value={searchValue}
			/>
		</label>

		<div class="connections-inventory__filters" role="tablist" aria-label="Filter source registry">
			{#each FILTERS as filter}
				<button
					type="button"
					role="tab"
					class="connections-inventory__filter"
					class:connections-inventory__filter--active={activeFilter === filter.id}
					aria-selected={activeFilter === filter.id}
					onclick={() => (activeFilter = filter.id)}
				>
					{filter.label}
				</button>
			{/each}
		</div>
	</div>

	{#if !cloudPlusAllowed}
		<div class="connections-inventory__entitlement">
			<div>
				<p class="connections-inventory__entitlement-title">
					Cloud+ source feeds require Pro tier or higher
				</p>
				<p class="connections-inventory__entitlement-copy">{cloudPlusUpgradePrompt.body}</p>
			</div>
			<a href={`${base}/billing`} class="btn btn-secondary connections-inventory__entitlement-cta">
				{cloudPlusUpgradePrompt.cta}
			</a>
		</div>
	{/if}

	{#if loaded && rows.length === 0}
		<div class="connections-inventory__empty">
			<h3 class="connections-inventory__empty-title">No inventory sources connected</h3>
			<p class="connections-inventory__empty-copy">
				Connect AWS, Azure, GCP, SaaS, license, platform, or hybrid feeds to populate the source
				registry.
			</p>
			<a href={`${base}/onboarding`} class="btn btn-primary connections-inventory__empty-cta">
				Connect an inventory source
			</a>
		</div>
	{:else}
		<div class="connections-inventory__table" role="table" aria-label="Inventory source registry">
			<div class="connections-inventory__table-head" role="row">
				<div role="columnheader">Source</div>
				<div role="columnheader">Scope</div>
				<div role="columnheader">Detail</div>
				<div role="columnheader">Status</div>
			</div>
			<div class="connections-inventory__table-body">
				{#if !loaded}
					<div class="connections-inventory__skeleton" aria-label="Loading inventory sources"></div>
					<div class="connections-inventory__skeleton" aria-hidden="true"></div>
					<div class="connections-inventory__skeleton" aria-hidden="true"></div>
				{:else if filteredRows.length === 0}
					<div class="connections-inventory__no-results">
						No source registry rows match the current filter.
					</div>
				{:else}
					{#each filteredRows as row (row.id)}
						<div class="connections-inventory__row" role="row">
							<div
								class="connections-inventory__cell connections-inventory__cell--source"
								role="cell"
							>
								<span
									class="connections-inventory__source-dot"
									class:connections-inventory__source-dot--saas={row.filter === 'saas'}
									class:connections-inventory__source-dot--license={row.filter === 'license'}
									class:connections-inventory__source-dot--platform={row.filter === 'platform'}
									class:connections-inventory__source-dot--hybrid={row.filter === 'hybrid'}
									class:connections-inventory__source-dot--org={row.filter === 'org'}
								></span>
								<span>{row.source}</span>
							</div>
							<div class="connections-inventory__cell" role="cell">{row.scope}</div>
							<div class="connections-inventory__cell" role="cell">{row.detail}</div>
							<div class="connections-inventory__cell" role="cell">
								<span
									class="connections-inventory__status"
									class:connections-inventory__status--pending={row.statusKind === 'pending'}
									class:connections-inventory__status--warning={row.statusKind === 'warning'}
								>
									{row.status}
								</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</section>
