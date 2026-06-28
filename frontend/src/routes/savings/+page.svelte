<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve */
	import './savings.app.css';
	import { onMount } from 'svelte';
	import { SvelteURLSearchParams } from 'svelte/reactivity';
	import { api } from '$lib/api';
	import { bearerHeaders, extractApiErrorMessage } from '$lib/http';
	import { formatDate, formatUsd } from '$lib/format';
	import { tierAtLeast } from '$lib/tier';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { TimeoutError } from '$lib/fetchWithTimeout';
	import { clientLogger } from '$lib/logging/client';
	import { filenameFromContentDispositionHeader } from '$lib/utils';
	import SavingsPageViewContent from './SavingsPageViewContent.svelte';
	import type {
		RealizedSavingsEvent,
		SavingsProofDrilldownResponse,
		SavingsProofResponse
	} from './savingsTypes';

	let { data } = $props();

	const SAVINGS_REQUEST_TIMEOUT_MS = 8000;

	let loading = $state(true);
	let downloading = $state(false);
	let error = $state('');
	let success = $state('');
	let drilldownError = $state('');
	let realizedEventsError = $state('');

	let report = $state<SavingsProofResponse | null>(null);
	let drilldown = $state<SavingsProofDrilldownResponse | null>(null);
	let realizedEvents = $state<RealizedSavingsEvent[]>([]);
	let drilldownDimension = $state<'strategy_type' | 'remediation_action' | 'finding_category'>(
		'strategy_type'
	);
	let provider = $state<string>('');
	let datePreset = $state('30d');
	let dateRange = $state(buildDefaultDateRange());

	function toDateOnly(value: Date): string {
		return value.toISOString().split('T')[0] ?? '';
	}

	function buildDefaultDateRange(): { startDate: string; endDate: string } {
		const end = new Date();
		const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
		return {
			startDate: toDateOnly(start),
			endDate: toDateOnly(end)
		};
	}

	function buildSavingsParams(): SvelteURLSearchParams {
		const params = new SvelteURLSearchParams();
		if (dateRange.startDate) params.set('start_date', dateRange.startDate);
		if (dateRange.endDate) params.set('end_date', dateRange.endDate);
		if (provider) params.set('provider', provider);
		return params;
	}

	async function getWithTimeout(url: string, headers: Record<string, string>) {
		return api.get(url, { headers, timeoutMs: SAVINGS_REQUEST_TIMEOUT_MS });
	}

	function normalizeLoadError(e: unknown, timeoutMessage: string, fallbackMessage: string): string {
		if (e instanceof TimeoutError) return timeoutMessage;
		if (e instanceof Error && e.message) return e.message;
		return fallbackMessage;
	}

	function handleDateChange(dates: { startDate: string; endDate: string }) {
		const unchanged =
			dateRange.startDate === dates.startDate && dateRange.endDate === dates.endDate;
		dateRange = dates;
		if (unchanged && (loading || report !== null)) return;
		void loadReport();
	}

	async function loadReport() {
		if (!data.user || !data.session?.access_token) {
			loading = false;
			return;
		}
		if (!tierAtLeast(data.subscription?.tier, 'pro')) {
			loading = false;
			return;
		}

		loading = true;
		error = '';
		success = '';
		drilldownError = '';
		realizedEventsError = '';
		drilldown = null;
		realizedEvents = [];
		try {
			const headers = bearerHeaders(data.session?.access_token);
			const params = buildSavingsParams();
			params.set('response_format', 'json');

			const res = await getWithTimeout(edgeApiPath(`/savings/proof?${params.toString()}`), headers);
			if (!res.ok) {
				const payload = await res.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, 'Failed to load savings proof report.'));
			}
			report = (await res.json()) as SavingsProofResponse;
			await Promise.allSettled([loadDrilldown(), loadRealizedEvents()]);
		} catch (e) {
			clientLogger.error('Failed to load savings proof:', e);
			error = normalizeLoadError(
				e,
				'Savings report request timed out. Try again.',
				'Failed to load savings proof report.'
			);
		} finally {
			loading = false;
		}
	}

	async function loadDrilldown() {
		if (!data.user || !data.session?.access_token) return;
		if (!tierAtLeast(data.subscription?.tier, 'pro')) return;

		drilldownError = '';
		drilldown = null;
		try {
			const headers = bearerHeaders(data.session?.access_token);
			const params = buildSavingsParams();
			params.set('dimension', drilldownDimension);
			params.set('response_format', 'json');

			const res = await getWithTimeout(
				edgeApiPath(`/savings/proof/drilldown?${params.toString()}`),
				headers
			);
			if (!res.ok) {
				const payload = await res.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, 'Failed to load drilldown.'));
			}
			drilldown = (await res.json()) as SavingsProofDrilldownResponse;
		} catch (e) {
			clientLogger.error('Failed to load savings drilldown:', e);
			drilldownError = normalizeLoadError(
				e,
				'Savings drilldown request timed out. Try again.',
				'Failed to load savings drilldown.'
			);
		}
	}

	async function loadRealizedEvents() {
		if (!data.user || !data.session?.access_token) return;
		if (!tierAtLeast(data.subscription?.tier, 'pro')) return;

		realizedEventsError = '';
		realizedEvents = [];
		try {
			const headers = bearerHeaders(data.session?.access_token);
			const params = buildSavingsParams();
			params.set('response_format', 'json');
			params.set('limit', '25');
			const res = await getWithTimeout(
				edgeApiPath(`/savings/realized/events?${params.toString()}`),
				headers
			);
			if (!res.ok) {
				const payload = await res.json().catch(() => ({}));
				throw new Error(
					extractApiErrorMessage(payload, 'Failed to load realized savings evidence.')
				);
			}
			realizedEvents = (await res.json()) as RealizedSavingsEvent[];
		} catch (e) {
			clientLogger.error('Failed to load realized savings evidence:', e);
			realizedEvents = [];
			realizedEventsError = normalizeLoadError(
				e,
				'Realized savings evidence request timed out. Try again.',
				'Failed to load realized savings evidence.'
			);
		}
	}

	async function downloadCsv() {
		if (!data.user || !data.session?.access_token) return;
		downloading = true;
		error = '';
		success = '';
		try {
			const headers = bearerHeaders(data.session?.access_token);
			const params = new SvelteURLSearchParams();
			if (dateRange.startDate) params.set('start_date', dateRange.startDate);
			if (dateRange.endDate) params.set('end_date', dateRange.endDate);
			if (provider) params.set('provider', provider);
			params.set('response_format', 'csv');

			const res = await getWithTimeout(edgeApiPath(`/savings/proof?${params.toString()}`), headers);
			if (!res.ok) {
				const payload = await res.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, 'Failed to export savings report.'));
			}
			const csv = await res.text();
			const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
			const url = URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			link.download = filenameFromContentDispositionHeader(
				res.headers.get('content-disposition'),
				`savings_proof_${new Date().toISOString().slice(0, 10)}.csv`
			);
			link.click();
			URL.revokeObjectURL(url);
			success = 'Savings proof export downloaded.';
		} catch (e) {
			error = (e as Error).message;
		} finally {
			downloading = false;
		}
	}

	onMount(() => {
		void loadReport();
	});
</script>

<svelte:head>
	<title>Savings Proof | Valdrics</title>
</svelte:head>

<SavingsPageViewContent
	{data}
	{loading}
	{downloading}
	{error}
	{success}
	{drilldownError}
	{realizedEventsError}
	{report}
	{drilldown}
	{realizedEvents}
	bind:drilldownDimension
	bind:provider
	bind:datePreset
	{dateRange}
	isProPlus={(tierValue) => tierAtLeast(tierValue, 'pro')}
	{formatUsd}
	{formatDate}
	{loadReport}
	{loadDrilldown}
	{downloadCsv}
	{handleDateChange}
/>
