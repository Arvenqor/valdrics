<!--
  Leaderboards Page - Team Savings Rankings
  
  Features:
  - "Who Saved the Most?" gamification
  - Period filter (7d, 30d, 90d, all)
  - Medal rankings with animations
-->

<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve */
	import './leaderboards.app.css';
	import { base } from '$app/paths';
	import { goto } from '$app/navigation';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { bearerHeaders } from '$lib/http';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { TimeoutError, fetchWithTimeout } from '$lib/fetchWithTimeout';

	let { data } = $props();

	const LEADERBOARD_TIMEOUT_MS = 8000;

	type LeaderboardEntry = {
		rank: number;
		user_email: string;
		savings_usd: number;
		remediation_count: number;
	};

	type LeaderboardPayload = {
		period: string;
		entries: LeaderboardEntry[];
		total_team_savings: number;
	};

	let period = $derived(data.period || '30d');
	let leaderboard = $state<LeaderboardPayload>({
		period: 'Last 30 Days',
		entries: [],
		total_team_savings: 0
	});
	let error = $state('');
	let loading = $state(false);
	let leaderboardRequestId = 0;

	function toAppPath(path: string): string {
		const normalizedPath = path.startsWith('/') ? path : `/${path}`;
		const normalizedBase = base === '/' ? '' : base;
		return `${normalizedBase}${normalizedPath}`;
	}

	function resetLeaderboardState() {
		leaderboard = {
			period: 'Last 30 Days',
			entries: [],
			total_team_savings: 0
		};
	}

	async function loadLeaderboard(
		accessToken: string | undefined,
		hasUser: boolean,
		currentPeriod: string
	) {
		const requestId = ++leaderboardRequestId;
		if (!hasUser || !accessToken) {
			resetLeaderboardState();
			error = '';
			loading = false;
			return;
		}

		loading = true;
		error = '';

		try {
			const res = await fetchWithTimeout(
				fetch,
				edgeApiPath(`/leaderboards?period=${currentPeriod}`),
				{
			headers: bearerHeaders(accessToken)
				},
				LEADERBOARD_TIMEOUT_MS
			);

			if (requestId !== leaderboardRequestId) return;

			if (!res.ok) {
				resetLeaderboardState();
				error = `Failed to load leaderboard (HTTP ${res.status})`;
				return;
			}

			leaderboard = (await res.json()) as LeaderboardPayload;
		} catch (err) {
			if (requestId !== leaderboardRequestId) return;
			resetLeaderboardState();
			error =
				err instanceof TimeoutError
					? 'Leaderboard request timed out. Please try again.'
					: 'Network error loading leaderboard';
		} finally {
			if (requestId === leaderboardRequestId) loading = false;
		}
	}

	function handlePeriodChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		goto(`${toAppPath('/leaderboards')}?period=${target.value}`, {
			keepFocus: true,
			noScroll: true
		});
	}

	function getMedal(rank: number): string {
		if (rank === 1) return '🥇';
		if (rank === 2) return '🥈';
		if (rank === 3) return '🥉';
		return `#${rank}`;
	}

	function formatEmail(email: string): string {
		const [name] = email.split('@');
		return name;
	}

	$effect(() => {
		const accessToken = data.session?.access_token;
		const hasUser = !!data.user;
		void loadLeaderboard(accessToken, hasUser, period);
	});
</script>

<svelte:head>
	<title>Leaderboards | Valdrics</title>
</svelte:head>

<div class="space-y-8">
	<!-- Page Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold mb-1">🏆 Savings Leaderboard</h1>
			<p class="text-ink-400 text-sm">Who saved the most? Compete with your team!</p>
		</div>

		{#if data.user}
			<select
				class="period-select"
				value={period}
				onchange={handlePeriodChange}
				aria-label="Select leaderboard period"
			>
				<option value="7d">Last 7 Days</option>
				<option value="30d">Last 30 Days</option>
				<option value="90d">Last 90 Days</option>
				<option value="all">All Time</option>
			</select>
		{/if}
	</div>

	<AuthGate authenticated={!!data.user} action="view leaderboards">
		{#if loading}
			<div class="material-perspective">
				<div class="card material-card-3d p-6">
					<div class="skeleton h-8 w-48 mb-4"></div>
					{#each [1, 2, 3] as i (i)}
						<div class="skeleton h-16 w-full mb-2"></div>
					{/each}
				</div>
			</div>
		{:else if error}
			<div class="material-perspective">
				<div class="card material-card-3d border-danger-500/50 bg-danger-500/10 p-4">
					<p class="text-danger-400">{error}</p>
				</div>
			</div>
		{:else}
			<!-- Total Team Savings Card -->
			<div class="material-perspective">
				<div class="card material-card-3d total-savings-box p-6 mb-6">
					<div class="text-center">
						<p class="text-sm text-ink-300 mb-1">{leaderboard.period}</p>
						<p class="text-4xl font-bold text-success-400">
							${leaderboard.total_team_savings.toLocaleString(undefined, {
								minimumFractionDigits: 2,
								maximumFractionDigits: 2
							})}
						</p>
						<p class="text-ink-400 mt-1">Total Team Savings</p>
					</div>
				</div>
			</div>

			<!-- Leaderboard -->
			{#if leaderboard.entries.length === 0}
				<div class="material-perspective">
					<div class="card material-card-3d text-center py-12 px-6">
						<span class="text-5xl mb-4 block">🚀</span>
						<h3 class="text-xl font-bold mb-2 text-ink-50">No savings yet!</h3>
						<p class="text-ink-400">
							Start approving remediation actions to see your team on the leaderboard.
						</p>
						<p class="text-ink-500 text-sm mt-2">
							Tip: Check the Dashboard for zombie resources to clean up.
						</p>
					</div>
				</div>
			{:else}
				<div class="material-perspective">
					<div class="card material-card-3d p-6 mb-6">
						<h2 class="text-lg font-bold mb-5 text-ink-50">Top Savers</h2>

						<div class="leaderboard-list">
							{#each leaderboard.entries as entry, i (entry.user_email)}
								<div
									class="leaderboard-entry"
									class:top-1={entry.rank === 1}
									class:top-2={entry.rank === 2}
									class:top-3={entry.rank === 3}
									style="animation-delay: {i * 50}ms;"
								>
									<div class="rank">
										<span class="medal">{getMedal(entry.rank)}</span>
									</div>

									<div class="user-info">
										<span class="username">{formatEmail(entry.user_email)}</span>
										<span class="remediation-count">{entry.remediation_count} actions</span>
									</div>

									<div class="savings">
										<span class="savings-amount"
											>${entry.savings_usd.toLocaleString(undefined, {
												minimumFractionDigits: 2,
												maximumFractionDigits: 2
											})}</span
										>
										<span class="savings-label">saved</span>
									</div>
								</div>
							{/each}
						</div>
					</div>
				</div>
			{/if}

			<!-- Encouragement Section -->
			<div class="material-perspective">
				<div class="card material-card-3d text-center p-6">
					<h3 class="text-lg font-bold mb-2 text-ink-50">💡 Pro Tip</h3>
					<p class="text-ink-400">
						Approve zombie cleanup recommendations to climb the leaderboard and save your company
						money!
					</p>
				</div>
			</div>
		{/if}
	</AuthGate>
</div>
