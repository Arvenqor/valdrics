<script lang="ts">
	import { AlertTriangle, RefreshCw } from '@lucide/svelte';
	import type { SavingsProofDrilldownResponse } from './savingsTypes';
	import { dimensionLabel, maxMonthlyValue, percentOf } from './savingsViewModel';

	type DrilldownDimension = 'strategy_type' | 'remediation_action' | 'finding_category';

	let {
		drilldown,
		drilldownError,
		drilldownDimension = $bindable(),
		loading,
		formatUsd,
		loadDrilldown
	}: {
		drilldown: SavingsProofDrilldownResponse | null;
		drilldownError: string;
		drilldownDimension: DrilldownDimension;
		loading: boolean;
		formatUsd: (value: number) => string;
		loadDrilldown: () => Promise<void>;
	} = $props();

	let bucketMax = $derived(maxMonthlyValue(drilldown?.buckets ?? []));
</script>

<section class="savings-panel savings-drilldown-panel" aria-labelledby="savings-drilldown-title">
	<div class="savings-panel__header savings-panel__header--split">
		<div>
			<h2 id="savings-drilldown-title">Drilldown</h2>
			<p>{dimensionLabel(drilldown?.dimension ?? drilldownDimension)} view of savings proof.</p>
		</div>
		<div class="savings-panel__actions">
			<label class="savings-sr-only" for="savings-drilldown-dimension"> Drilldown dimension </label>
			<select
				id="savings-drilldown-dimension"
				class="savings-select"
				bind:value={drilldownDimension}
				onchange={() => void loadDrilldown()}
				aria-label="Drilldown dimension"
			>
				<option value="strategy_type">Strategy type</option>
				<option value="remediation_action">Remediation action</option>
				<option value="finding_category">Finding category</option>
			</select>
			<button
				type="button"
				class="savings-icon-button"
				onclick={loadDrilldown}
				disabled={loading}
				aria-label="Refresh drilldown"
				title="Refresh drilldown"
			>
				<RefreshCw size={16} />
			</button>
		</div>
	</div>

	{#if drilldownError}
		<div class="savings-inline-alert savings-inline-alert--warning" role="status">
			<AlertTriangle size={16} />
			<span>{drilldownError}</span>
		</div>
	{/if}

	{#if !drilldown}
		<div class="savings-empty-state">
			<p>No drilldown available.</p>
		</div>
	{:else}
		<div class="savings-drilldown-summary">
			<div>
				<span>Opportunity</span>
				<strong>{formatUsd(drilldown.opportunity_monthly_usd)}</strong>
			</div>
			<div>
				<span>Realized</span>
				<strong>{formatUsd(drilldown.realized_monthly_usd)}</strong>
			</div>
			<div>
				<span>Buckets</span>
				<strong>{drilldown.buckets.length}</strong>
			</div>
			<div>
				<span>Truncated</span>
				<strong>{drilldown.truncated ? 'Yes' : 'No'}</strong>
			</div>
		</div>

		{#if drilldown.buckets.length === 0}
			<div class="savings-empty-state">
				<p>No recommendation buckets matched this filter.</p>
			</div>
		{:else}
			<div class="savings-drilldown-list">
				{#each drilldown.buckets as row (row.key)}
					{@const opportunityWidth = percentOf(row.opportunity_monthly_usd, bucketMax)}
					{@const realizedWidth = percentOf(row.realized_monthly_usd, bucketMax)}
					<article class="savings-drilldown-row">
						<div class="savings-drilldown-row__copy">
							<h3>{row.key}</h3>
							<p>
								{row.open_recommendations} open · {row.applied_recommendations} applied ·
								{row.completed_remediations} completed
							</p>
						</div>
						<div class="savings-drilldown-row__bars">
							<div
								class="savings-mini-bar"
								aria-label={`${row.key} opportunity ${formatUsd(row.opportunity_monthly_usd)}`}
							>
								<span style={`width: ${opportunityWidth}%`}></span>
							</div>
							<div
								class="savings-mini-bar savings-mini-bar--realized"
								aria-label={`${row.key} realized ${formatUsd(row.realized_monthly_usd)}`}
							>
								<span style={`width: ${realizedWidth}%`}></span>
							</div>
						</div>
						<div class="savings-drilldown-row__amount">
							<strong>{formatUsd(row.realized_monthly_usd)}</strong>
							<span>realized / mo</span>
						</div>
					</article>
				{/each}
			</div>
		{/if}
	{/if}
</section>
