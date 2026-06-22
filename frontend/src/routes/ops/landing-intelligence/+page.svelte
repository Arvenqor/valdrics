<script lang="ts">
	import { browser } from '$app/environment';
	import { onMount } from 'svelte';
	import { BarChart3, RefreshCw, Layers, TrendingUp } from '@lucide/svelte';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { TimeoutError, fetchWithTimeout } from '$lib/fetchWithTimeout';
	import {
		buildLandingWeeklyTrendChecks,
		readLandingCtaValueReport,
		readLandingFunnelReport,
		readLandingWeeklyFunnelReport,
		type LandingCtaValueSummary,
		type LandingFunnelSummary,
		type LandingWeeklyFunnelSummary,
		type LandingWeeklyTrendCheck
	} from '$lib/landing/landingFunnel';
	import {
		buildLandingCampaignApiPath,
		extractLandingCampaignApiError,
		formatCampaignDate,
		formatCampaignDelta,
		formatCampaignPercent,
		formatCampaignRateDelta,
		getFunnelAlertTone,
		LANDING_CAMPAIGN_REQUEST_TIMEOUT_MS,
		type CampaignMetricsResponse
	} from './landingCampaignAnalytics';

	let { data }: { data: any } = $props();

	// Tab state
	let activeTab = $state<'funnel' | 'campaigns'>('funnel');

	// Local Funnel Telemetry State
	const REFRESH_INTERVAL_MS = 30000;
	const EMPTY_SUMMARY: LandingFunnelSummary = {
		counts: {
			view: 0,
			engaged: 0,
			cta: 0,
			signup_intent: 0
		},
		conversion: {
			engagementRate: 0,
			ctaRate: 0,
			signupIntentRate: 0
		}
	};

	const EMPTY_WEEKLY: LandingWeeklyFunnelSummary[] = [];
	const EMPTY_TRENDS: LandingWeeklyTrendCheck[] = buildLandingWeeklyTrendChecks([]);

	let allTimeSummary = $state<LandingFunnelSummary>(EMPTY_SUMMARY);
	let weeklySummaries = $state<LandingWeeklyFunnelSummary[]>(EMPTY_WEEKLY);
	let trendChecks = $state<LandingWeeklyTrendCheck[]>(EMPTY_TRENDS);
	let ctaValueSummary = $state<LandingCtaValueSummary[]>([]);
	let capturedAt = $state<string>('');

	function formatPercent(rate: number): string {
		return `${(rate * 100).toFixed(1)}%`;
	}

	function formatTrendLabel(trend: LandingWeeklyTrendCheck): string {
		if (trend.direction === 'flat') return 'Flat';
		return trend.direction === 'up' ? 'Up' : 'Down';
	}

	function refreshFromStorage(): void {
		if (!browser) return;
		const weekly = readLandingWeeklyFunnelReport(window.localStorage, 8);
		weeklySummaries = weekly;
		allTimeSummary = readLandingFunnelReport(window.localStorage);
		trendChecks = buildLandingWeeklyTrendChecks(weekly);
		ctaValueSummary = readLandingCtaValueReport(window.localStorage, 10);
		capturedAt = new Date().toISOString();
	}

	// Backend Campaign Analytics State
	let days = $state(30);
	let loadingCampaigns = $state(false);
	let refreshingCampaigns = $state(false);
	let forbidden = $state(false);
	let errorCampaigns = $state('');
	let metrics = $state<CampaignMetricsResponse | null>(null);
	let requestToken = 0;

	async function loadMetrics(windowDays: number): Promise<void> {
		const accessToken = data.session?.access_token;
		if (!data.user || !accessToken) {
			errorCampaigns = '';
			forbidden = false;
			metrics = null;
			loadingCampaigns = false;
			refreshingCampaigns = false;
			return;
		}

		const currentToken = ++requestToken;
		loadingCampaigns = true;
		errorCampaigns = '';
		forbidden = false;

		try {
			const response = await fetchWithTimeout(
				fetch,
				buildLandingCampaignApiPath(windowDays),
				{
					headers: {
						Authorization: `Bearer ${accessToken}`
					}
				},
				LANDING_CAMPAIGN_REQUEST_TIMEOUT_MS
			);

			if (currentToken !== requestToken) return;

			if (response.status === 403) {
				forbidden = true;
				metrics = null;
				errorCampaigns = 'Admin role required to view campaign attribution analytics.';
				return;
			}

			if (response.status === 401) {
				metrics = null;
				errorCampaigns = 'Session expired. Please sign in again.';
				return;
			}

			if (!response.ok) {
				const payload = await response.json().catch(() => ({}));
				metrics = null;
				errorCampaigns =
					extractLandingCampaignApiError(payload) ||
					`Failed to load campaign analytics (HTTP ${response.status}).`;
				return;
			}

			metrics = (await response.json()) as CampaignMetricsResponse;
		} catch (exc) {
			if (currentToken !== requestToken) return;
			metrics = null;
			errorCampaigns =
				exc instanceof TimeoutError
					? 'Campaign analytics request timed out. Try again.'
					: (exc as Error).message || 'Failed to load campaign analytics.';
		} finally {
			if (currentToken === requestToken) {
				loadingCampaigns = false;
				refreshingCampaigns = false;
			}
		}
	}

	async function refreshCampaigns(): Promise<void> {
		if (refreshingCampaigns) return;
		refreshingCampaigns = true;
		await loadMetrics(days);
	}

	function updateDays(windowDays: number): void {
		if (windowDays === days || loadingCampaigns) return;
		days = windowDays;
		void loadMetrics(windowDays);
	}

	onMount(() => {
		refreshFromStorage();
		const intervalId = window.setInterval(refreshFromStorage, REFRESH_INTERVAL_MS);
		return () => window.clearInterval(intervalId);
	});

	// Trigger campaign loading when tab switches to campaigns
	$effect(() => {
		if (activeTab === 'campaigns' && data.user && !metrics) {
			void loadMetrics(days);
		}
	});
</script>

<svelte:head>
	<title>Landing & Growth Intelligence | Valdrics</title>
	<meta name="description" content="Landing conversion and campaign attribution metrics panel." />
</svelte:head>

<section class="space-y-6">
	<header class="card border border-ink-800">
		<p class="text-xs uppercase tracking-[0.14em] text-accent-300 font-bold">Growth Intelligence</p>
		<h1 class="text-2xl font-bold mt-1">Growth & Conversion Analytics</h1>
		<p class="text-sm text-ink-400 mt-2">
			Review weekly conversion rates and campaign channel attribution under a unified operations
			console.
		</p>
	</header>

	<!-- Unified Navigation Tabs -->
	<div class="flex items-center gap-6 border-b border-ink-800 pb-1 mb-4">
		<button
			type="button"
			class="flex items-center gap-2 pb-2 px-1 border-b-2 text-sm font-semibold transition-all bg-transparent border-transparent"
			class:border-accent-300={activeTab === 'funnel'}
			class:text-ink-100={activeTab === 'funnel'}
			class:text-ink-400={activeTab !== 'funnel'}
			onclick={() => (activeTab = 'funnel')}
		>
			<Layers class="h-4 w-4" />
			<span>Funnel Telemetry</span>
		</button>
		<button
			type="button"
			class="flex items-center gap-2 pb-2 px-1 border-b-2 text-sm font-semibold transition-all bg-transparent border-transparent"
			class:border-accent-300={activeTab === 'campaigns'}
			class:text-ink-100={activeTab === 'campaigns'}
			class:text-ink-400={activeTab !== 'campaigns'}
			onclick={() => (activeTab = 'campaigns')}
		>
			<TrendingUp class="h-4 w-4" />
			<span>Campaign Attribution</span>
		</button>
	</div>

	<!-- Funnel Telemetry Tab -->
	{#if activeTab === 'funnel'}
		<div class="space-y-6">
			<div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
				<article class="card">
					<p class="text-xs uppercase tracking-[0.08em] text-ink-500">All-time views</p>
					<p class="text-2xl font-bold mt-1">{allTimeSummary.counts.view}</p>
				</article>
				<article class="card">
					<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Engagement rate</p>
					<p class="text-2xl font-bold mt-1">
						{formatPercent(allTimeSummary.conversion.engagementRate)}
					</p>
				</article>
				<article class="card">
					<p class="text-xs uppercase tracking-[0.08em] text-ink-500">CTA rate</p>
					<p class="text-2xl font-bold mt-1">{formatPercent(allTimeSummary.conversion.ctaRate)}</p>
				</article>
				<article class="card">
					<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Signup intent rate</p>
					<p class="text-2xl font-bold mt-1">
						{formatPercent(allTimeSummary.conversion.signupIntentRate)}
					</p>
				</article>
			</div>

			<div class="grid gap-4 lg:grid-cols-3">
				{#each trendChecks as trend (trend.metric)}
					<article class="card">
						<p class="text-xs uppercase tracking-[0.08em] text-ink-500">{trend.metric}</p>
						<p class="text-lg font-semibold mt-1">{formatTrendLabel(trend)}</p>
						<p class="text-sm text-ink-400 mt-2">
							Latest {formatPercent(trend.latest)} vs previous {formatPercent(trend.previous)}
						</p>
					</article>
				{/each}
			</div>

			<section class="card">
				<h2 class="text-lg font-semibold">CTA intent breakdown</h2>
				{#if ctaValueSummary.length === 0}
					<p class="text-sm text-ink-400 mt-3">
						No CTA value telemetry has been recorded in this browser context yet.
					</p>
				{:else}
					<ul class="mt-4 space-y-2">
						{#each ctaValueSummary as entry (entry.value)}
							<li class="flex items-center justify-between gap-3 border-b border-ink-800/70 pb-2">
								<span class="text-sm text-ink-300">{entry.label}</span>
								<span class="text-sm font-semibold text-ink-100">{entry.count}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</section>

			<section class="card overflow-x-auto">
				<h2 class="text-lg font-semibold">Weekly funnel detail</h2>
				{#if weeklySummaries.length === 0}
					<p class="text-sm text-ink-400 mt-3">
						No weekly landing telemetry is currently stored in this browser context.
					</p>
				{:else}
					<table class="w-full text-sm mt-4">
						<thead>
							<tr class="text-left text-ink-500">
								<th class="py-2 pr-4 font-medium">Week Start (UTC)</th>
								<th class="py-2 pr-4 font-medium">Views</th>
								<th class="py-2 pr-4 font-medium">Engaged</th>
								<th class="py-2 pr-4 font-medium">CTA</th>
								<th class="py-2 pr-4 font-medium">Signup Intent</th>
								<th class="py-2 pr-4 font-medium">Engagement Rate</th>
								<th class="py-2 pr-4 font-medium">CTA Rate</th>
								<th class="py-2 font-medium">Signup Intent Rate</th>
							</tr>
						</thead>
						<tbody>
							{#each weeklySummaries as week (week.weekStart)}
								<tr class="border-t border-ink-800">
									<td class="py-2 pr-4 font-medium text-ink-200">{week.weekStart}</td>
									<td class="py-2 pr-4">{week.counts.view}</td>
									<td class="py-2 pr-4">{week.counts.engaged}</td>
									<td class="py-2 pr-4">{week.counts.cta}</td>
									<td class="py-2 pr-4">{week.counts.signup_intent}</td>
									<td class="py-2 pr-4">{formatPercent(week.conversion.engagementRate)}</td>
									<td class="py-2 pr-4">{formatPercent(week.conversion.ctaRate)}</td>
									<td class="py-2">{formatPercent(week.conversion.signupIntentRate)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}
			</section>
		</div>
	{/if}

	<!-- Campaigns Attribution Tab -->
	{#if activeTab === 'campaigns'}
		<AuthGate authenticated={!!data.user} action="view landing campaign analytics">
			<div class="space-y-6">
				<section class="card border border-ink-800">
					<div class="flex flex-wrap items-center justify-between gap-3">
						<div>
							<h2 class="text-lg font-semibold text-ink-100">UTM campaign attributions</h2>
							<p class="text-sm text-ink-400 mt-1">
								Select review window to reload backend campaign rollups.
							</p>
						</div>
						<div class="flex items-center gap-2">
							<button
								type="button"
								class="btn btn-secondary"
								onclick={() => updateDays(7)}
								aria-pressed={days === 7}
							>
								7d
							</button>
							<button
								type="button"
								class="btn btn-secondary"
								onclick={() => updateDays(30)}
								aria-pressed={days === 30}
							>
								30d
							</button>
							<button
								type="button"
								class="btn btn-secondary"
								onclick={() => updateDays(90)}
								aria-pressed={days === 90}
							>
								90d
							</button>
							<button
								type="button"
								class="btn btn-secondary"
								onclick={refreshCampaigns}
								disabled={refreshingCampaigns}
							>
								<RefreshCw class={`h-4 w-4 ${refreshingCampaigns ? 'animate-spin' : ''}`} />
								<span>{refreshingCampaigns ? 'Refreshing' : 'Refresh'}</span>
							</button>
						</div>
					</div>
				</section>

				{#if loadingCampaigns && !metrics}
					<section class="card border border-ink-800">
						<p class="text-sm text-ink-400">Loading campaign analytics...</p>
					</section>
				{:else if forbidden}
					<section class="card border border-danger-500/40 bg-danger-500/10">
						<p class="text-sm text-danger-300">{errorCampaigns}</p>
					</section>
				{:else if errorCampaigns}
					<section class="card border border-danger-500/40 bg-danger-500/10">
						<p class="text-sm text-danger-300">{errorCampaigns}</p>
					</section>
				{:else if metrics}
					<section class="grid gap-4 md:grid-cols-4">
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Window</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">{metrics.days} days</p>
							<p class="text-xs text-ink-500 mt-1">
								{metrics.window_start} to {metrics.window_end}
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Total events</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">{metrics.total_events}</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Campaigns returned</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">{metrics.items.length}</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Paid activations</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">{metrics.total_paid_tenants}</p>
							<p class="text-xs text-ink-500 mt-1">
								{metrics.total_pql_tenants} product-qualified tenants
							</p>
						</article>
					</section>

					<section class="grid gap-4 md:grid-cols-4">
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Onboarded</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{metrics.total_onboarded_tenants}
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Connected</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{metrics.total_connected_tenants}
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">First value</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{metrics.total_first_value_tenants}
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">Checkout started</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{metrics.total_checkout_started_tenants}
							</p>
							<p class="text-xs text-ink-500 mt-1">
								{metrics.total_pricing_view_tenants} pricing views
							</p>
						</article>
					</section>

					<section class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">7d signup → connection</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{formatCampaignPercent(metrics.weekly_current.signup_to_connection_rate)}
							</p>
							<p class="text-xs text-ink-500 mt-1">
								{formatCampaignRateDelta(metrics.weekly_delta.signup_to_connection_rate)} vs previous
								7d
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">
								7d connection → first value
							</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{formatCampaignPercent(metrics.weekly_current.connection_to_first_value_rate)}
							</p>
							<p class="text-xs text-ink-500 mt-1">
								{formatCampaignRateDelta(metrics.weekly_delta.connection_to_first_value_rate)} vs previous
								7d
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">7d PQL delta</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{formatCampaignDelta(metrics.weekly_delta.pql_tenants)}
							</p>
							<p class="text-xs text-ink-500 mt-1">
								Current {metrics.weekly_current.pql_tenants} vs previous {metrics.weekly_previous
									.pql_tenants}
							</p>
						</article>
						<article class="card border border-ink-800">
							<p class="text-xs uppercase tracking-[0.08em] text-ink-500">7d paid delta</p>
							<p class="text-lg font-semibold text-ink-100 mt-1">
								{formatCampaignDelta(metrics.weekly_delta.paid_tenants)}
							</p>
							<p class="text-xs text-ink-500 mt-1">
								Current {metrics.weekly_current.paid_tenants} vs previous {metrics.weekly_previous
									.paid_tenants}
							</p>
						</article>
					</section>

					<section class="card border border-ink-800">
						<h2 class="text-lg font-semibold text-ink-100">Weekly funnel health alerts</h2>
						<div class="mt-4 grid gap-3 lg:grid-cols-2">
							{#each metrics.funnel_alerts as alert (alert.key)}
								<article class={`rounded-2xl border p-4 ${getFunnelAlertTone(alert.status)}`}>
									<div class="flex items-start justify-between gap-3">
										<div>
											<p class="text-xs uppercase tracking-[0.08em] font-semibold opacity-80">
												{alert.label}
											</p>
											<p class="mt-1 text-lg font-semibold">
												{formatCampaignPercent(alert.current_rate)}
											</p>
										</div>
										<span class="text-xs uppercase tracking-[0.08em] font-semibold">
											{alert.status.replace('_', ' ')}
										</span>
									</div>
									<p class="mt-3 text-sm opacity-90">{alert.message}</p>
									<p class="mt-3 text-xs opacity-80">
										Threshold {formatCampaignPercent(alert.threshold_rate)} · Previous {formatCampaignPercent(
											alert.previous_rate
										)}
										· Delta {formatCampaignRateDelta(alert.weekly_delta)}
									</p>
									<p class="mt-1 text-xs opacity-80">
										{alert.current_numerator}/{alert.current_denominator} tenants this week
									</p>
								</article>
							{/each}
						</div>
					</section>

					<section class="card border border-ink-800 overflow-x-auto">
						<div class="flex items-center gap-2">
							<BarChart3 class="h-4 w-4 text-accent-300" />
							<h2 class="text-lg font-semibold text-ink-100">Campaign rollup</h2>
						</div>

						{#if metrics.items.length === 0}
							<p class="text-sm text-ink-400 mt-3">
								No campaign telemetry has been ingested for this window yet.
							</p>
						{:else}
							<table class="w-full text-sm mt-4">
								<thead>
									<tr class="text-left text-ink-500 border-b border-ink-800">
										<th class="py-2 pr-3 font-medium">Source</th>
										<th class="py-2 pr-3 font-medium">Medium</th>
										<th class="py-2 pr-3 font-medium">Campaign</th>
										<th class="py-2 pr-3 font-medium">Total</th>
										<th class="py-2 pr-3 font-medium">CTA</th>
										<th class="py-2 pr-3 font-medium">Signup Intent</th>
										<th class="py-2 pr-3 font-medium">Onboarded</th>
										<th class="py-2 pr-3 font-medium">Connected</th>
										<th class="py-2 pr-3 font-medium">First Value</th>
										<th class="py-2 pr-3 font-medium">PQL</th>
										<th class="py-2 pr-3 font-medium">Checkout</th>
										<th class="py-2 pr-3 font-medium">Paid</th>
										<th class="py-2 font-medium">Last Seen</th>
									</tr>
								</thead>
								<tbody>
									{#each metrics.items as item (`${item.utm_source}-${item.utm_medium}-${item.utm_campaign}`)}
										<tr class="border-b border-ink-900/80">
											<td class="py-2 pr-3 text-ink-200">{item.utm_source}</td>
											<td class="py-2 pr-3 text-ink-300">{item.utm_medium}</td>
											<td class="py-2 pr-3 text-ink-100 font-medium">{item.utm_campaign}</td>
											<td class="py-2 pr-3 text-ink-100">{item.total_events}</td>
											<td class="py-2 pr-3 text-ink-100">{item.cta_events}</td>
											<td class="py-2 pr-3 text-ink-100">{item.signup_intent_events}</td>
											<td class="py-2 pr-3 text-ink-100">{item.onboarded_tenants}</td>
											<td class="py-2 pr-3 text-ink-100">{item.connected_tenants}</td>
											<td class="py-2 pr-3 text-ink-100">{item.first_value_tenants}</td>
											<td class="py-2 pr-3 text-ink-100">{item.pql_tenants}</td>
											<td class="py-2 pr-3 text-ink-100">{item.checkout_started_tenants}</td>
											<td class="py-2 pr-3 text-ink-100">{item.paid_tenants}</td>
											<td class="py-2 text-ink-400">{formatCampaignDate(item.last_seen_at)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						{/if}
					</section>
				{/if}
			</div>
		</AuthGate>
	{/if}
</section>
