<script lang="ts">
	import AllocationBreakdown from '$lib/components/AllocationBreakdown.svelte';
	import CloudDistributionMatrix from '$lib/components/CloudDistributionMatrix.svelte';
	import GreenOpsWidget from '$lib/components/GreenOpsWidget.svelte';
	import ROAChart from '$lib/components/ROAChart.svelte';
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

	let { allocation, tier, unitEconomics } = $props<{
		allocation: AllocationData | null | undefined;
		tier: string;
		unitEconomics: Record<string, unknown> | null | undefined;
	}>();
</script>

<UnitEconomicsCards {unitEconomics} />

<div class="grid gap-6 md:grid-cols-2 lg:grid-cols-2">
	<GreenOpsWidget />
	<CloudDistributionMatrix />
</div>

<div class="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
	<ROAChart />
	{#if allocation && allocation.buckets && allocation.buckets.length > 0}
		<AllocationBreakdown data={allocation} />
	{:else if !tierAtLeast(tier, 'growth')}
		<UpgradeNotice
			currentTier={tier}
			requiredTier="growth"
			feature="Cost Allocation (chargeback/showback)"
		/>
	{:else}
		<div class="glass-panel flex flex-col items-center justify-center text-ink-500">
			<p>Cost Allocation data will appear here once attribution rules are defined.</p>
		</div>
	{/if}
</div>
