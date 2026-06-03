<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { createLazyComponent } from '$lib/lazyComponent';
	import GreenOpsWidget from '$lib/components/GreenOpsWidget.svelte';
	import UnitEconomicsCards from '$lib/components/UnitEconomicsCards.svelte';
	import UpgradeNotice from '$lib/components/UpgradeNotice.svelte';
	import { tierAtLeast } from '$lib/tier';

	type AllocationBucket = {
		name?: string;
		value?: number;
	};

	type AllocationData = {
		buckets?: AllocationBucket[];
	};

	type CloudDistributionMatrixProps = {
		data?: Array<{
			label: string;
			value: number;
			color: string;
		}>;
	};

	type AllocationBreakdownProps = {
		data: {
			buckets: Array<{
				name: string;
				total_amount: number;
				record_count: number;
				color?: string;
			}>;
			total: number;
		} | null;
		loading?: boolean;
		error?: string | null;
	};

	const loadCloudDistributionMatrix = createLazyComponent<CloudDistributionMatrixProps>(
		() => import('$lib/components/CloudDistributionMatrix.svelte')
	);
	const loadRoaChart = createLazyComponent<Record<string, never>>(
		() => import('$lib/components/ROAChart.svelte')
	);
	const loadAllocationBreakdown = createLazyComponent<AllocationBreakdownProps>(
		() => import('$lib/components/AllocationBreakdown.svelte')
	);

	type UnitEconomicsSettings = {
		target_spend_reduction_pct?: number;
		target_rollout_days?: number;
		target_team_members?: number;
		target_blended_hourly_rate?: number;
	};

	let { allocation, tier, unitEconomics, unitEconomicsSettings } = $props<{
		allocation: AllocationData | null | undefined;
		tier: string;
		unitEconomics: Record<string, unknown> | null | undefined;
		unitEconomicsSettings: UnitEconomicsSettings | null | undefined;
	}>();

	let financeDetailAnchor: HTMLDivElement | null = $state(null);
	let financeDetailsVisible = $state(false);

	onMount(() => {
		if (import.meta.env.MODE === 'test' || typeof IntersectionObserver === 'undefined') {
			financeDetailsVisible = true;
			return;
		}

		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting)) {
					financeDetailsVisible = true;
					observer.disconnect();
				}
			},
			{ rootMargin: '220px 0px' }
		);

		if (financeDetailAnchor) {
			observer.observe(financeDetailAnchor);
		}

		return () => observer.disconnect();
	});
</script>

<UnitEconomicsCards {unitEconomics} />

<!-- ROI Planner CTA — surfaces the planning tool for finance/leadership -->
<div class="roi-planner-cta">
	<div class="roi-planner-cta__content">
		<div class="roi-planner-cta__icon" aria-hidden="true">📊</div>
		<div>
			<p class="roi-planner-cta__title">Need the full model?</p>
			<p class="roi-planner-cta__sub">
				Open the 12-month planner when you need rollout effort, implementation cost, and payback
				assumptions using your own numbers.
			</p>

			{#if unitEconomicsSettings && (unitEconomicsSettings.target_spend_reduction_pct || unitEconomicsSettings.target_rollout_days || unitEconomicsSettings.target_team_members || unitEconomicsSettings.target_blended_hourly_rate)}
				<div class="roi-targets-summary">
					<span class="roi-targets-summary__badge">Active Targets</span>
					{#if unitEconomicsSettings.target_spend_reduction_pct}
						<span class="roi-targets-summary__item"
							>📉 <strong>{unitEconomicsSettings.target_spend_reduction_pct}%</strong> Reduction</span
						>
					{/if}
					{#if unitEconomicsSettings.target_rollout_days}
						<span class="roi-targets-summary__item"
							>⏱️ <strong>{unitEconomicsSettings.target_rollout_days}d</strong> Rollout</span
						>
					{/if}
					{#if unitEconomicsSettings.target_team_members}
						<span class="roi-targets-summary__item"
							>👥 <strong>{unitEconomicsSettings.target_team_members}</strong> Engineers</span
						>
					{/if}
					{#if unitEconomicsSettings.target_blended_hourly_rate}
						<span class="roi-targets-summary__item"
							>💵 <strong>${unitEconomicsSettings.target_blended_hourly_rate}/hr</strong> Rate</span
						>
					{/if}
				</div>
			{/if}
		</div>
	</div>
	<a href={`${base}/roi-planner`} class="btn btn-secondary roi-planner-cta__btn">
		Open Full ROI Planner →
	</a>
</div>

<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-2 finance-dashboard__summary-grid">
	<GreenOpsWidget />
	<div bind:this={financeDetailAnchor}>
		{#if financeDetailsVisible}
			{#await loadCloudDistributionMatrix()}
				<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
					<div class="skeleton h-8 w-40"></div>
					<div class="skeleton finance-dashboard__chart-skeleton"></div>
				</div>
			{:then module}
				{@const CloudDistributionMatrix = module.default}
				<CloudDistributionMatrix />
			{/await}
		{:else}
			<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
				<div class="skeleton h-8 w-40"></div>
				<div class="skeleton finance-dashboard__chart-skeleton"></div>
			</div>
		{/if}
	</div>
</div>

{#if financeDetailsVisible}
	<div class="grid gap-6 md:grid-cols-1 lg:grid-cols-2 finance-dashboard__detail-grid">
		{#await loadRoaChart()}
			<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
				<div class="skeleton h-8 w-32"></div>
				<div
					class="skeleton finance-dashboard__chart-skeleton finance-dashboard__chart-skeleton--tall"
				></div>
			</div>
		{:then module}
			{@const ROAChart = module.default}
			<ROAChart />
		{/await}

		{#if allocation && allocation.buckets && allocation.buckets.length > 0}
			{#await loadAllocationBreakdown()}
				<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
					<div class="skeleton h-8 w-44"></div>
					<div
						class="skeleton finance-dashboard__chart-skeleton finance-dashboard__chart-skeleton--tall"
					></div>
				</div>
			{:then module}
				{@const AllocationBreakdown = module.default}
				<AllocationBreakdown
					data={{
						buckets: allocation.buckets.map((bucket: AllocationBucket) => ({
							name: bucket.name ?? 'Unallocated',
							total_amount: bucket.value ?? 0,
							record_count: 0
						})),
						total: allocation.buckets.reduce(
							(sum: number, bucket: AllocationBucket) => sum + (bucket.value ?? 0),
							0
						)
					}}
				/>
			{/await}
		{:else if !tierAtLeast(tier, 'growth')}
			<UpgradeNotice
				currentTier={tier}
				requiredTier="growth"
				feature="Cost Allocation (chargeback/showback)"
			/>
		{:else}
			<div class="glass-panel finance-dashboard__empty-state">
				<p>Cost Allocation data will appear here once attribution rules are defined.</p>
			</div>
		{/if}
	</div>
{:else}
	<div class="grid gap-6 md:grid-cols-1 lg:grid-cols-2 finance-dashboard__detail-grid">
		<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
			<div class="skeleton h-8 w-32"></div>
			<div
				class="skeleton finance-dashboard__chart-skeleton finance-dashboard__chart-skeleton--tall"
			></div>
		</div>
		<div class="glass-panel finance-dashboard__card-skeleton" aria-hidden="true">
			<div class="skeleton h-8 w-44"></div>
			<div
				class="skeleton finance-dashboard__chart-skeleton finance-dashboard__chart-skeleton--tall"
			></div>
		</div>
	</div>
{/if}

<style>
	.finance-dashboard__summary-grid,
	.finance-dashboard__detail-grid {
		align-items: stretch;
	}

	.finance-dashboard__card-skeleton {
		display: flex;
		flex-direction: column;
		gap: var(--space-4);
		padding: var(--space-6);
		min-height: 18rem;
	}

	.finance-dashboard__chart-skeleton {
		width: 100%;
		min-height: 13rem;
		border-radius: 1.5rem;
	}

	.finance-dashboard__chart-skeleton--tall {
		min-height: 18rem;
	}

	.finance-dashboard__empty-state {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 18rem;
		color: var(--color-ink-500);
		text-align: center;
		padding: var(--space-6);
	}

	.finance-dashboard__empty-state p {
		margin: 0;
	}

	/* ROI Planner CTA band */
	.roi-planner-cta {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		padding: 16px 20px;
		border-radius: 12px;
		background: rgba(0, 207, 124, 0.04);
		border: 1px solid rgba(0, 207, 124, 0.15);
		margin-bottom: 4px;
		flex-wrap: wrap;
	}

	.roi-planner-cta__content {
		display: flex;
		align-items: flex-start;
		gap: 12px;
	}

	.roi-planner-cta__icon {
		font-size: 20px;
		line-height: 1;
		flex-shrink: 0;
		margin-top: 2px;
	}

	.roi-planner-cta__title {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-ink-100, #f0f4f8);
		margin: 0 0 3px;
	}

	.roi-planner-cta__sub {
		font-size: 12px;
		color: var(--color-ink-400, rgba(240, 244, 248, 0.55));
		margin: 0;
		line-height: 1.5;
		max-width: 480px;
	}

	.roi-planner-cta__btn {
		flex-shrink: 0;
		white-space: nowrap;
	}

	.roi-targets-summary {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 12px;
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px dashed rgba(0, 207, 124, 0.15);
	}

	.roi-targets-summary__badge {
		font-size: 9px;
		font-weight: 700;
		text-transform: uppercase;
		background: rgba(0, 207, 124, 0.15);
		color: #00cf7c;
		padding: 2px 6px;
		border-radius: 4px;
		letter-spacing: 0.05em;
	}

	.roi-targets-summary__item {
		font-size: 11px;
		color: var(--color-ink-300, rgba(240, 244, 248, 0.75));
	}

	.roi-targets-summary__item strong {
		color: var(--color-ink-100, #f0f4f8);
	}
</style>
