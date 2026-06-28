<script lang="ts">
	import './approvals-page.css';
	import { base } from '$app/paths';
	import { onDestroy, onMount } from 'svelte';
	import { AlertTriangle, Check, Clock, RefreshCw, Route, ShieldCheck } from '@lucide/svelte';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import { api } from '$lib/api';
	import { bearerHeaders, extractApiErrorMessage } from '$lib/http';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { TimeoutError } from '$lib/fetchWithTimeout';
	import ApprovalQueueCard from './ApprovalQueueCard.svelte';
	import {
		APPROVAL_FILTERS,
		countApprovalsByFilter,
		emptyBodyForFilter,
		emptyTitleForFilter,
		filterApprovals,
		formatDate,
		formatMoney,
		getEarliestExpiry,
		getPendingMonthlyDelta,
		sortApprovalsByExpiry
	} from './approvalQueueModel';
	import type { ApprovalFilterId, ApprovalQueueItem } from './approvalQueueModel';

	let { data } = $props();

	const APPROVALS_REQUEST_TIMEOUT_MS = 8000;
	const APPROVALS_POLL_INTERVAL_MS = 30000;

	let loading = $state(true);
	let refreshing = $state(false);
	let decidingApprovalId = $state<string | null>(null);
	let error = $state('');
	let success = $state('');
	let activeFilter = $state<ApprovalFilterId>('all');
	let approvals = $state<ApprovalQueueItem[]>([]);
	let pollTimer = $state<ReturnType<typeof setInterval> | null>(null);

	let canAccessApprovals = $derived(
		['pro', 'enterprise'].includes(String(data.subscription?.tier ?? '').toLowerCase())
	);
	let visibleApprovals = $derived(filterApprovals(approvals, activeFilter));
	let filterCounts = $derived(countApprovalsByFilter(approvals));
	let pendingMonthlyDelta = $derived(getPendingMonthlyDelta(approvals));
	let earliestExpiry = $derived(getEarliestExpiry(approvals));

	async function loadApprovals(options: { silent?: boolean } = {}) {
		if (!data.user || !data.session?.access_token || !canAccessApprovals) {
			loading = false;
			return;
		}

		if (options.silent) {
			refreshing = true;
		} else {
			loading = true;
		}
		error = '';

		try {
			const response = await api.get(edgeApiPath('/enforcement/approvals/queue?limit=50'), {
				headers: bearerHeaders(data.session?.access_token),
				timeoutMs: APPROVALS_REQUEST_TIMEOUT_MS
			});
			if (!response.ok) {
				const payload = await response.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, 'Failed to load approval queue.'));
			}
			approvals = sortApprovalsByExpiry((await response.json()) as ApprovalQueueItem[]);
		} catch (caught) {
			error =
				caught instanceof TimeoutError
					? 'Approval queue request timed out. Refresh to retry.'
					: (caught as Error).message;
		} finally {
			loading = false;
			refreshing = false;
		}
	}

	async function decide(approval: ApprovalQueueItem, decision: 'approve' | 'deny') {
		decidingApprovalId = `${decision}:${approval.approval_id}`;
		error = '';
		success = '';
		try {
			const response = await api.post(
				edgeApiPath(`/enforcement/approvals/${approval.approval_id}/${decision}`),
				{ notes: `frontend_${decision}` },
				{
					headers: bearerHeaders(data.session?.access_token),
					timeoutMs: APPROVALS_REQUEST_TIMEOUT_MS
				}
			);
			if (!response.ok) {
				const payload = await response.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, `Failed to ${decision} approval.`));
			}
			approvals = approvals.filter((item) => item.approval_id !== approval.approval_id);
			success = `Approval ${decision === 'approve' ? 'approved' : 'denied'} for ${approval.resource_reference}.`;
			void loadApprovals({ silent: true });
		} catch (caught) {
			error =
				caught instanceof TimeoutError
					? `Approval ${decision} request timed out. Retry from the queue.`
					: (caught as Error).message;
		} finally {
			decidingApprovalId = null;
		}
	}

	onMount(() => {
		void loadApprovals();
		if (canAccessApprovals) {
			pollTimer = setInterval(() => {
				void loadApprovals({ silent: true });
			}, APPROVALS_POLL_INTERVAL_MS);
		}
	});

	onDestroy(() => {
		if (pollTimer) {
			clearInterval(pollTimer);
			pollTimer = null;
		}
	});
</script>

<svelte:head>
	<title>Approvals | Valdrics</title>
</svelte:head>

<AuthGate authenticated={!!data.user} action="review approval requests">
	<section class="approvals-page" aria-labelledby="approvals-title">
		<div class="page-header">
			<div>
				<p class="page-kicker">Policy execution</p>
				<h1 id="approvals-title">Approval Queue</h1>
				<p>
					Review policy-gated enforcement decisions with cost impact, routing context, and expiry
					ordering.
				</p>
			</div>
			<button
				type="button"
				class="icon-button"
				disabled={refreshing || !canAccessApprovals}
				aria-label="Refresh approval queue"
				onclick={() => void loadApprovals({ silent: true })}
			>
				<RefreshCw size={18} />
			</button>
		</div>

		{#if !canAccessApprovals}
			<div class="upgrade-panel">
				<ShieldCheck size={24} />
				<div>
					<h2>Policy approvals require Pro or Enterprise</h2>
					<p>Approval routing is gated by the policy configuration entitlement.</p>
				</div>
				<a href={`${base}/billing`}>Review plan</a>
			</div>
		{:else}
			<div class="queue-stats" role="list" aria-label="Approval queue statistics">
				<div class="stat-chip" role="listitem">
					<Route size={18} />
					<span class="stat-chip__value">{approvals.length}</span>
					<small>pending requests</small>
				</div>
				<div class="stat-chip" role="listitem">
					<AlertTriangle size={18} />
					<span class="stat-chip__value stat-chip__value--warning">
						{formatMoney(pendingMonthlyDelta)}
					</span>
					<small>monthly delta awaiting review</small>
				</div>
				<div class="stat-chip" role="listitem">
					<Clock size={18} />
					<span class="stat-chip__value">{formatDate(earliestExpiry)}</span>
					<small>next expiry</small>
				</div>
			</div>

			{#if error}
				<div role="alert" class="status-panel status-panel--error">{error}</div>
			{/if}

			{#if success}
				<div role="status" class="status-panel status-panel--success">{success}</div>
			{/if}

			<nav class="filter-tabs" aria-label="Filter approvals">
				{#each APPROVAL_FILTERS as filter}
					<button
						type="button"
						class="filter-tab"
						class:filter-tab--active={activeFilter === filter.id}
						aria-pressed={activeFilter === filter.id}
						onclick={() => (activeFilter = filter.id)}
					>
						{filter.label}
						<span>{filterCounts[filter.id]}</span>
					</button>
				{/each}
			</nav>

			{#if loading}
				<div class="queue-panel" aria-busy="true">
					<p>Loading approval queue...</p>
				</div>
			{:else if visibleApprovals.length === 0}
				<div class="queue-panel queue-panel--empty">
					<Check size={24} />
					<h2>{emptyTitleForFilter(activeFilter)}</h2>
					<p>{emptyBodyForFilter(activeFilter)}</p>
				</div>
			{:else}
				<div class="approval-list" aria-label="Pending approval requests">
					{#each visibleApprovals as approval (approval.approval_id)}
						<ApprovalQueueCard
							{approval}
							{decidingApprovalId}
							onApprove={(item) => void decide(item, 'approve')}
							onDeny={(item) => void decide(item, 'deny')}
						/>
					{/each}
				</div>
			{/if}
		{/if}
	</section>
</AuthGate>
