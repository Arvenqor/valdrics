<script lang="ts">
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { canAccessAdminHealth } from '$lib/entitlements';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { bearerHeaders, extractApiErrorMessage } from '$lib/http';
	import { TimeoutError, fetchWithTimeout } from '$lib/fetchWithTimeout';

	import HealthDashboardPanel from './HealthDashboardPanel.svelte';
	import type { FairUseRuntime, HealthDashboard } from './healthTypes';
	import './health-page.css';

	let { data } = $props();
	const ADMIN_HEALTH_TIMEOUT_MS = 10000;
	let dashboard = $state<HealthDashboard | null>(null);
	let fairUse = $state<FairUseRuntime | null>(null);
	let fairUseError = $state('');
	let error = $state('');
	let forbidden = $state(false);
	let loading = $state(false);
	let refreshing = $state(false);
	let healthRequestId = 0;
	let hasPlatformAccess = $derived(
		canAccessAdminHealth(data.profile?.role ?? 'member', data.profile?.platform_operator)
	);

	async function loadHealthDashboard(accessToken: string | undefined, hasUser: boolean) {
		const requestId = ++healthRequestId;

		if (!hasUser || !accessToken || !hasPlatformAccess) {
			dashboard = null;
			fairUse = null;
			fairUseError = '';
			error =
				hasUser && !hasPlatformAccess
					? 'Platform operator access is required to view system health metrics.'
					: '';
			forbidden = hasUser && !hasPlatformAccess;
			loading = false;
			refreshing = false;
			return;
		}

		loading = true;
		error = '';
		fairUseError = '';

		try {
			const res = await fetchWithTimeout(
				fetch,
				edgeApiPath('/admin/health-dashboard'),
				{
					headers: bearerHeaders(accessToken)
				},
				ADMIN_HEALTH_TIMEOUT_MS
			);

			if (requestId !== healthRequestId) return;

			if (res.status === 403) {
				dashboard = null;
				fairUse = null;
				fairUseError = '';
				forbidden = true;
				error = 'Platform operator access is required to view system health metrics.';
				return;
			}

			if (res.status === 401) {
				dashboard = null;
				fairUse = null;
				fairUseError = '';
				forbidden = false;
				error = 'Session expired. Please sign in again.';
				return;
			}

			if (!res.ok) {
				const payload = await res.json().catch(() => ({}));
				dashboard = null;
				fairUse = null;
				fairUseError = '';
				forbidden = false;
				error = extractApiErrorMessage(
					payload,
					`Failed to load health metrics (HTTP ${res.status}).`
				);
				return;
			}

			dashboard = (await res.json()) as HealthDashboard;
			forbidden = false;
			error = '';

			try {
				const fairUseRes = await fetchWithTimeout(
					fetch,
					edgeApiPath('/admin/health-dashboard/fair-use'),
					{
						headers: bearerHeaders(accessToken)
					},
					ADMIN_HEALTH_TIMEOUT_MS
				);

				if (requestId !== healthRequestId) return;

				if (!fairUseRes.ok) {
					const payload = await fairUseRes.json().catch(() => ({}));
					fairUse = null;
					fairUseError = extractApiErrorMessage(
						payload,
						`Fair-use runtime status unavailable (HTTP ${fairUseRes.status}).`
					);
					return;
				}

				fairUse = (await fairUseRes.json()) as FairUseRuntime;
				fairUseError = '';
			} catch (fairUseErr) {
				if (requestId !== healthRequestId) return;
				fairUse = null;
				fairUseError =
					fairUseErr instanceof TimeoutError
						? 'Fair-use runtime request timed out. Please try again.'
						: (fairUseErr as Error).message || 'Fair-use runtime status unavailable.';
			}
		} catch (err) {
			if (requestId !== healthRequestId) return;
			dashboard = null;
			fairUse = null;
			fairUseError = '';
			forbidden = false;
			error =
				err instanceof TimeoutError
					? 'Health metrics request timed out. Please try again.'
					: (err as Error).message || 'Failed to load health metrics.';
		} finally {
			if (requestId === healthRequestId) {
				loading = false;
				refreshing = false;
			}
		}
	}

	async function refreshMetrics() {
		if (refreshing) return;
		refreshing = true;
		const accessToken = data.session?.access_token;
		const hasUser = !!data.user;
		await loadHealthDashboard(accessToken, hasUser);
	}

	$effect(() => {
		const accessToken = data.session?.access_token;
		const hasUser = !!data.user;
		void loadHealthDashboard(accessToken, hasUser);
	});
</script>

<svelte:head>
	<title>Internal System Health | Valdrics</title>
</svelte:head>

<AuthGate authenticated={!!data.user} action="view system health metrics">
	{#if forbidden}
		<div class="material-perspective">
			<div class="card border-warning-500/50 bg-warning-500/10 material-card-3d">
				<h2 class="text-lg font-semibold mb-2">Platform Operator Access Required</h2>
				<p class="text-ink-300 text-sm">
					This dashboard is restricted to platform-scoped internal operators. Workspace admins do
					not have access to platform-global health telemetry.
				</p>
			</div>
		</div>
	{:else if loading}
		<div class="material-perspective">
			<div class="card material-card-3d">
				<div class="skeleton h-8 w-48 mb-3"></div>
				<div class="skeleton h-5 w-full mb-2"></div>
				<div class="skeleton h-5 w-4/5"></div>
			</div>
		</div>
	{:else if error}
		<div class="material-perspective">
			<div class="card border-danger-500/50 bg-danger-500/10 material-card-3d">
				<p class="text-danger-400">{error}</p>
			</div>
		</div>
	{:else if !dashboard}
		<div class="material-perspective">
			<div class="card material-card-3d">
				<p class="text-ink-400">No health metrics available right now.</p>
			</div>
		</div>
	{:else}
		<HealthDashboardPanel
			{dashboard}
			{fairUse}
			{fairUseError}
			{refreshing}
			onRefresh={refreshMetrics}
		/>
	{/if}
</AuthGate>
