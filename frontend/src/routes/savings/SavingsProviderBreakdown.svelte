<script lang="ts">
	import type { SavingsProofBreakdownItem } from './savingsTypes';
	import {
		maxMonthlyValue,
		percentOf,
		providerAccent,
		providerLabel,
		savingsAccentStyle
	} from './savingsViewModel';

	let {
		breakdown,
		formatUsd
	}: {
		breakdown: SavingsProofBreakdownItem[];
		formatUsd: (value: number) => string;
	} = $props();

	let maxValue = $derived(maxMonthlyValue(breakdown));
</script>

<section class="savings-panel savings-provider-panel" aria-labelledby="savings-breakdown-title">
	<div class="savings-panel__header">
		<div>
			<h2 id="savings-breakdown-title">Breakdown</h2>
			<p>Provider-level opportunity and realized monthly savings.</p>
		</div>
		<span class="savings-panel__meta">{breakdown.length} provider rows</span>
	</div>

	{#if breakdown.length === 0}
		<div class="savings-empty-state">
			<p>No provider savings found for this window.</p>
		</div>
	{:else}
		<div class="savings-provider-list">
			{#each breakdown as row (row.provider)}
				{@const accent = providerAccent(row.provider)}
				{@const opportunityWidth = percentOf(row.opportunity_monthly_usd, maxValue)}
				{@const realizedWidth = percentOf(row.realized_monthly_usd, maxValue)}
				<article class="savings-provider-row" style={savingsAccentStyle(accent)}>
					<div class="savings-provider-row__top">
						<div class="savings-provider-row__identity">
							<span class="savings-provider-row__dot" aria-hidden="true"></span>
							<div>
								<h3>{providerLabel(row.provider)}</h3>
								<p>
									{row.open_recommendations} open · {row.pending_remediations} pending ·
									{row.completed_remediations} completed
								</p>
							</div>
						</div>
						<div class="savings-provider-row__amounts">
							<strong>{formatUsd(row.realized_monthly_usd)}</strong>
							<span>realized / mo</span>
						</div>
					</div>
					<div class="savings-bar-stack" aria-hidden="true">
						<div class="savings-bar-line">
							<span>Opportunity</span>
							<div class="savings-bar-track">
								<div
									class="savings-bar-fill savings-bar-fill--opportunity"
									style={`width: ${opportunityWidth}%`}
								></div>
							</div>
							<strong>{formatUsd(row.opportunity_monthly_usd)}</strong>
						</div>
						<div class="savings-bar-line">
							<span>Realized</span>
							<div class="savings-bar-track">
								<div
									class="savings-bar-fill savings-bar-fill--realized"
									style={`width: ${realizedWidth}%`}
								></div>
							</div>
							<strong>{formatUsd(row.realized_monthly_usd)}</strong>
						</div>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</section>
