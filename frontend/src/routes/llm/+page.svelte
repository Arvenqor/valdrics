<!--
  LLM Usage Page - Premium SaaS Design
  
  Features:
  - Stats cards for LLM metrics with 3D cybernetic glows
  - Usage by model breakdown inside material cards
  - Recent API calls table with glassmorphism and model badges
-->

<script lang="ts">
	import './llm.app.css';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { bearerHeaders } from '$lib/http';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { TimeoutError, fetchWithTimeout } from '$lib/fetchWithTimeout';

	let { data } = $props();

	const LLM_USAGE_TIMEOUT_MS = 8000;

	type UsageRecord = {
		id?: string;
		created_at?: string;
		model?: string;
		input_tokens?: number;
		output_tokens?: number;
		total_tokens?: number;
		cost_usd?: number;
		request_type?: string;
	};

	let usage = $state<UsageRecord[]>([]);
	let summary = $state({
		total_cost: 0,
		total_tokens: 0,
		by_model: {} as Record<string, { tokens: number; cost: number; calls: number }>
	});
	let error = $state('');
	let loading = $state(false);
	let llmRequestId = 0;

	function resetUsageState() {
		usage = [];
		summary = {
			total_cost: 0,
			total_tokens: 0,
			by_model: {}
		};
	}

	async function loadLlmUsage(accessToken: string | undefined, hasUser: boolean) {
		const requestId = ++llmRequestId;

		if (!hasUser || !accessToken) {
			resetUsageState();
			error = '';
			loading = false;
			return;
		}

		loading = true;
		error = '';

		try {
			const res = await fetchWithTimeout(
				fetch,
				edgeApiPath('/usage'),
				{
					headers: bearerHeaders(accessToken)
				},
				LLM_USAGE_TIMEOUT_MS
			);

			if (requestId !== llmRequestId) return;

			if (!res.ok) {
				resetUsageState();
				error = `API error: ${res.status}`;
				return;
			}

			const result = await res.json();
			const fetchedUsage = Array.isArray(result.usage) ? (result.usage as UsageRecord[]) : [];
			const by_model: Record<string, { tokens: number; cost: number; calls: number }> = {};
			let total_cost = 0;
			let total_tokens = 0;

			for (const record of fetchedUsage) {
				total_cost += record.cost_usd || 0;
				total_tokens += record.total_tokens || 0;

				const model = record.model || 'unknown';
				if (!by_model[model]) by_model[model] = { tokens: 0, cost: 0, calls: 0 };
				by_model[model].tokens += record.total_tokens || 0;
				by_model[model].cost += record.cost_usd || 0;
				by_model[model].calls += 1;
			}

			usage = fetchedUsage;
			summary = { total_cost, total_tokens, by_model };
		} catch (err) {
			if (requestId !== llmRequestId) return;
			resetUsageState();
			error =
				err instanceof TimeoutError
					? 'LLM usage request timed out. Please try again.'
					: 'Network error loading LLM usage';
		} finally {
			if (requestId === llmRequestId) loading = false;
		}
	}

	$effect(() => {
		const accessToken = data.session?.access_token;
		const hasUser = !!data.user;
		void loadLlmUsage(accessToken, hasUser);
	});
</script>

<svelte:head>
	<title>LLM Usage | Valdrics</title>
</svelte:head>

<div class="space-y-8">
	<!-- Page Header -->
	<div>
		<h1 class="text-2xl font-bold mb-1">LLM Usage</h1>
		<p class="text-ink-400 text-sm">Track your AI model costs and token usage</p>
	</div>

	<AuthGate authenticated={!!data.user} action="view LLM usage">
		{#if loading}
			<!-- Loading Skeletons -->
			<div class="grid gap-5 md:grid-cols-3">
				{#each [1, 2, 3] as i (i)}
					<div class="material-perspective">
						<div class="card material-card-3d p-6">
							<div class="skeleton h-4 w-20 mb-3"></div>
							<div class="skeleton h-8 w-32"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if error}
			<div class="material-perspective">
				<div class="card material-card-3d border-danger-500/50 bg-danger-500/10 p-4">
					<p class="text-danger-400">{error}</p>
				</div>
			</div>
		{:else}
			<!-- Stats Grid -->
			<div class="grid gap-5 md:grid-cols-3">
				<div class="material-perspective">
					<div class="card card-stat cost-stat material-card-3d p-6 stagger-enter" style="animation-delay: 0ms;">
						<p class="text-sm text-ink-400 mb-1 font-semibold uppercase tracking-wider">Total LLM Cost</p>
						<p class="text-3xl font-bold" style="color: var(--color-accent-400);">
							${summary.total_cost.toFixed(4)}
						</p>
					</div>
				</div>

				<div class="material-perspective">
					<div class="card card-stat tokens-stat material-card-3d p-6 stagger-enter" style="animation-delay: 50ms;">
						<p class="text-sm text-ink-400 mb-1 font-semibold uppercase tracking-wider">Total Tokens</p>
						<p class="text-3xl font-bold" style="color: var(--color-success-400);">
							{summary.total_tokens.toLocaleString()}
						</p>
					</div>
				</div>

				<div class="material-perspective">
					<div class="card card-stat calls-stat material-card-3d p-6 stagger-enter" style="animation-delay: 100ms;">
						<p class="text-sm text-ink-400 mb-1 font-semibold uppercase tracking-wider">API Calls</p>
						<p class="text-3xl font-bold" style="color: var(--color-warning-400);">
							{usage.length}
						</p>
					</div>
				</div>
			</div>

			<!-- Usage by Model -->
			{#if Object.keys(summary.by_model).length > 0}
				<div class="material-perspective">
					<div class="card material-card-3d p-6 stagger-enter" style="animation-delay: 150ms;">
						<h2 class="text-lg font-bold mb-5 text-ink-50">Usage by Model</h2>
						<div class="overflow-x-auto table-container">
							<table class="table">
								<thead>
									<tr>
										<th>Model</th>
										<th>Calls</th>
										<th>Tokens</th>
										<th>Cost</th>
									</tr>
								</thead>
								<tbody>
									{#each Object.entries(summary.by_model) as [model, stats] (model)}
										<tr>
											<td>
												<span class="model-badge">{model}</span>
											</td>
											<td>{stats.calls}</td>
											<td>{stats.tokens.toLocaleString()}</td>
											<td class="text-accent-400">${stats.cost.toFixed(4)}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</div>
				</div>
			{/if}

			<!-- Recent Calls -->
			<div class="material-perspective">
				<div class="card material-card-3d p-6 stagger-enter" style="animation-delay: 200ms;">
					<div class="flex items-center justify-between mb-5">
						<h2 class="text-lg font-bold text-ink-50">Recent API Calls</h2>
						<span class="badge badge-default">{usage.length} total</span>
					</div>

					{#if usage.length === 0}
						<div class="text-center py-12">
							<span class="text-4xl mb-3 block">🤖</span>
							<h3 class="text-xl font-bold mb-2 text-ink-50">No LLM usage recorded yet</h3>
							<p class="text-ink-400">Usage will appear here when you use AI features.</p>
						</div>
					{:else}
						<div class="overflow-x-auto table-container">
							<table class="table">
								<thead>
									<tr>
										<th>Time</th>
										<th>Model</th>
										<th>Input</th>
										<th>Output</th>
										<th>Cost</th>
										<th>Type</th>
									</tr>
								</thead>
								<tbody>
									{#each usage.slice(0, 20) as record (record.id || record.created_at)}
										<tr>
											<td class="text-ink-400 text-xs">
												{record.created_at ? new Date(record.created_at).toLocaleString() : '-'}
											</td>
											<td>
												<span class="model-badge">{record.model}</span>
											</td>
											<td>{record.input_tokens?.toLocaleString() || 0}</td>
											<td>{record.output_tokens?.toLocaleString() || 0}</td>
											<td class="text-accent-400">${record.cost_usd?.toFixed(6) || 0}</td>
											<td>
												<span class="request-type-badge">{record.request_type || 'unknown'}</span>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</AuthGate>
</div>
