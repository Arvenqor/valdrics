<!--
  GreenOps Dashboard - Carbon Footprint & Sustainability

  Features:
  - Carbon footprint tracking (Scope 2 + Scope 3)
  - Carbon efficiency score
  - Green region recommendations
  - Graviton migration opportunities
  - Carbon budget monitoring
-->

<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve */
	import './greenops.app.css';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { TimeoutError, fetchWithTimeout } from '$lib/fetchWithTimeout';
	import './greenops-bento.css';
	import GreenOpsTierPreview from './GreenOpsTierPreview.svelte';
	import GreenOpsMetricsGrid from './GreenOpsMetricsGrid.svelte';
	import GreenOpsRecommendationsSchedule from './GreenOpsRecommendationsSchedule.svelte';
	import {
		GREENOPS_DEFAULT_REGION,
		buildCarbonBudgetPath,
		buildCarbonFootprintPath,
		buildCarbonIntensityPath,
		buildGravitonPath,
		buildGreenSchedulePath
	} from './greenopsApiPaths';
	import type {
		BudgetData,
		CarbonData,
		GravitonData,
		IntensityData,
		ScheduleResult
	} from './greenopsTypes';

	let { data } = $props();

	const GREENOPS_TIMEOUT_MS = 10000;
	let carbonData = $state<CarbonData | null>(null);
	let gravitonData = $state<GravitonData | null>(null);
	let budgetData = $state<BudgetData | null>(null);
	let intensityData = $state<IntensityData | null>(null);
	let selectedRegion = $derived(data.selectedRegion || GREENOPS_DEFAULT_REGION);
	let error = $state('');
	let loading = $state(false);
	let workloadDuration = $state(1);
	let scheduleResult = $state<ScheduleResult | null>(null);
	let greenopsRequestId = 0;

	function toAppPath(path: string): string {
		const normalizedPath = path.startsWith('/') ? path : `/${path}`;
		const normalizedBase = base === '/' ? '' : base;
		return `${normalizedBase}${normalizedPath}`;
	}

	async function loadGreenOpsData(
		region: string,
		accessToken: string | undefined,
		hasUser: boolean
	) {
		const requestId = ++greenopsRequestId;

		if (!hasUser || !accessToken) {
			carbonData = null;
			gravitonData = null;
			budgetData = null;
			intensityData = null;
			error = '';
			loading = false;
			return;
		}

		loading = true;
		error = '';

		try {
			const today = new Date();
			const thirtyDaysAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
			const startDate = thirtyDaysAgo.toISOString().split('T')[0];
			const endDate = today.toISOString().split('T')[0];
			const headers = { Authorization: `Bearer ${accessToken}` };

			const [carbonRes, gravitonRes, budgetRes, intensityRes] = await Promise.all([
				fetchWithTimeout(
					fetch,
					buildCarbonFootprintPath({ startDate, endDate, region }),
					{ headers },
					GREENOPS_TIMEOUT_MS
				),
				fetchWithTimeout(fetch, buildGravitonPath(region), { headers }, GREENOPS_TIMEOUT_MS),
				fetchWithTimeout(
					fetch,
					buildCarbonBudgetPath({ region }),
					{ headers },
					GREENOPS_TIMEOUT_MS
				),
				fetchWithTimeout(
					fetch,
					buildCarbonIntensityPath(region, 24),
					{ headers },
					GREENOPS_TIMEOUT_MS
				)
			]);

			if (requestId !== greenopsRequestId) return;

			carbonData = carbonRes.ok ? await carbonRes.json() : null;
			gravitonData = gravitonRes.ok ? await gravitonRes.json() : null;
			budgetData = budgetRes.ok ? await budgetRes.json() : null;
			intensityData = intensityRes.ok ? await intensityRes.json() : null;

			if (!carbonRes.ok && carbonRes.status === 401) {
				error = 'Session expired. Please refresh the page.';
			} else if (!carbonRes.ok) {
				error = `Failed to fetch carbon data (HTTP ${carbonRes.status}).`;
			} else {
				error = '';
			}
		} catch (err) {
			if (requestId !== greenopsRequestId) return;
			carbonData = null;
			gravitonData = null;
			budgetData = null;
			intensityData = null;
			error =
				err instanceof TimeoutError
					? 'GreenOps data request timed out. Please try again.'
					: 'Network error fetching sustainability data';
		} finally {
			if (requestId === greenopsRequestId) {
				loading = false;
			}
		}
	}

	async function getOptimalSchedule() {
		const res = await api.get(buildGreenSchedulePath(selectedRegion, workloadDuration));
		if (res.ok) {
			scheduleResult = await res.json();
		}
	}

	function handleRegionChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		goto(`${toAppPath('/greenops')}?region=${target.value}`, { keepFocus: true, noScroll: true });
	}

	function formatCO2(kg: number): string {
		if (kg < 1) return `${(kg * 1000).toFixed(1)} g`;
		if (kg < 1000) return `${kg.toFixed(2)} kg`;
		return `${(kg / 1000).toFixed(2)} t`;
	}

	$effect(() => {
		const accessToken = data.session?.access_token;
		const hasUser = !!data.user;
		void loadGreenOpsData(selectedRegion, accessToken, hasUser);
	});
</script>

<svelte:head>
	<title>GreenOps - Valdrics</title>
</svelte:head>

<div class="space-y-8 material-perspective">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="text-3xl font-extrabold text-white flex items-center gap-2 tracking-tight">
				<span class="text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)]">🌱</span> GreenOps Dashboard
			</h1>
			<p class="text-ink-400 text-sm mt-1.5 max-w-xl">
				Monitor AWS carbon footprint, workload intensity, and carbon-aware execution schedules.
			</p>
		</div>

		<div class="relative">
			<select
				value={selectedRegion}
				onchange={handleRegionChange}
				class="bg-ink-900 border border-ink-700 hover:border-ink-600 focus:border-accent-500 focus:ring-1 focus:ring-accent-500 rounded-lg px-4 py-2.5 text-sm text-white font-semibold transition-all shadow-lg cursor-pointer outline-none min-w-[200px]"
				aria-label="Select AWS region for carbon analysis"
			>
				<option value="us-east-1">US East (N. Virginia)</option>
				<option value="us-west-2">US West (Oregon)</option>
				<option value="eu-west-1">EU (Ireland)</option>
				<option value="eu-north-1">EU (Stockholm)</option>
				<option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
			</select>
		</div>
	</div>

	<AuthGate authenticated={!!data.user} action="view GreenOps">
		{#if loading}
			<div class="flex flex-col items-center justify-center py-28 space-y-4">
				<div class="relative w-12 h-12">
					<div class="absolute inset-0 rounded-full border-2 border-accent-500/10"></div>
					<div class="absolute inset-0 rounded-full border-t-2 border-emerald-400 animate-spin"></div>
				</div>
				<p class="text-ink-400 text-sm font-medium animate-pulse">Hydrating telemetry data...</p>
			</div>
		{:else if !['growth', 'pro', 'enterprise', 'free'].includes(data.subscription?.tier)}
			<GreenOpsTierPreview {toAppPath} />
		{:else if error}
			<div class="material-card-3d bg-red-950/20 border-red-500/30 p-6 flex items-start gap-4">
				<div class="text-2xl text-red-500">⚠️</div>
				<div>
					<h3 class="text-white font-bold mb-1">Data Fetch Failed</h3>
					<p class="text-red-300 text-sm leading-relaxed">{error}</p>
				</div>
			</div>
		{:else}
			<GreenOpsMetricsGrid {carbonData} {gravitonData} {budgetData} {formatCO2} />
			<GreenOpsRecommendationsSchedule
				{carbonData}
				{intensityData}
				bind:workloadDuration
				{scheduleResult}
				onGetOptimalSchedule={getOptimalSchedule}
			/>
		{/if}
	</AuthGate>
</div>

