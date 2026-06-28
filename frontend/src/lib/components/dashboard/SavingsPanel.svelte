<script lang="ts">
	import { BadgeDollarSign, CircleDollarSign, TrendingDown } from '@lucide/svelte';
	import type { DashboardOverviewModel } from './overviewTypes';

	let { savings } = $props<{
		savings: DashboardOverviewModel['savings'];
	}>();

	const executionPercent = $derived(savings.executionPercent ?? 0);

	function formatCompactUsd(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: value >= 1000 ? 0 : 2
		}).format(value);
	}
</script>

<section class="savings-panel" aria-labelledby="savings-panel-title">
	<div class="panel-heading">
		<div>
			<p class="panel-kicker">Savings proof</p>
			<h2 id="savings-panel-title">Execution Yield</h2>
		</div>
		<BadgeDollarSign size={21} />
	</div>

	<div
		class="yield-meter"
		aria-label={`Realized savings execution yield ${executionPercent.toFixed(0)} percent`}
	>
		<div class="yield-meter__value">
			<span>{savings.executionPercent === null ? 'N/A' : `${executionPercent.toFixed(0)}%`}</span>
			<small>realized share</small>
		</div>
		<div class="yield-meter__track" aria-hidden="true">
			<span style={`width: ${Math.max(0, Math.min(100, executionPercent))}%`}></span>
		</div>
	</div>

	<div class="money-grid">
		<div>
			<TrendingDown size={18} />
			<span>Opportunity</span>
			<strong>{formatCompactUsd(savings.opportunityMonthlyUsd)}</strong>
		</div>
		<div>
			<CircleDollarSign size={18} />
			<span>Realized</span>
			<strong>{formatCompactUsd(savings.realizedMonthlyUsd)}</strong>
		</div>
	</div>

	<div class="workflow-grid">
		<div>
			<span>{savings.openRecommendations}</span>
			<small>open recommendations</small>
		</div>
		<div>
			<span>{savings.appliedRecommendations}</span>
			<small>applied recommendations</small>
		</div>
		<div>
			<span>{savings.pendingRemediations}</span>
			<small>pending remediations</small>
		</div>
		<div>
			<span>{savings.completedRemediations}</span>
			<small>completed remediations</small>
		</div>
	</div>
</section>

<style>
	.savings-panel {
		min-height: 22rem;
		padding: 1.25rem;
		border: 1px solid rgb(128 154 176 / 0.2);
		border-radius: var(--radius-md);
		background:
			linear-gradient(180deg, rgb(24 32 40 / 0.84), rgb(10 13 18 / 0.72)),
			radial-gradient(circle at 100% 10%, rgb(52 211 153 / 0.1), transparent 28%);
		box-shadow: 0 18px 50px rgb(0 0 0 / 0.24);
	}

	.panel-heading {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
		color: var(--color-success-300);
	}

	.panel-kicker {
		margin: 0 0 0.25rem;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		font-weight: 700;
		text-transform: uppercase;
	}

	h2 {
		margin: 0;
		color: var(--color-ink-50);
		font-size: var(--text-xl);
		font-weight: 750;
		letter-spacing: 0;
	}

	.yield-meter {
		display: grid;
		gap: 0.8rem;
		margin-bottom: 1rem;
		padding: 1rem;
		border: 1px solid rgb(52 211 153 / 0.2);
		border-radius: var(--radius-md);
		background: rgb(52 211 153 / 0.07);
	}

	.yield-meter__value {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
	}

	.yield-meter__value span {
		color: var(--color-success-300);
		font-family: var(--font-mono);
		font-size: var(--text-3xl);
		font-weight: 850;
		line-height: 1;
	}

	.yield-meter__value small {
		color: var(--color-ink-400);
		font-size: var(--text-xs);
	}

	.yield-meter__track {
		height: 0.6rem;
		overflow: hidden;
		border-radius: var(--radius-full);
		background: rgb(128 154 176 / 0.16);
	}

	.yield-meter__track span {
		display: block;
		height: 100%;
		border-radius: inherit;
		background: linear-gradient(90deg, var(--color-success-400), var(--color-accent-300));
	}

	.money-grid,
	.workflow-grid {
		display: grid;
		gap: 0.75rem;
	}

	.money-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
		margin-bottom: 1rem;
	}

	.money-grid div,
	.workflow-grid div {
		padding: 0.75rem;
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
	}

	.money-grid div {
		font-size: var(--text-xs);
	}

	.money-grid strong,
	.workflow-grid span {
		color: var(--color-ink-50);
		font-family: var(--font-mono);
		font-weight: 850;
	}

	.workflow-grid {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}

	.workflow-grid span,
	.workflow-grid small {
		display: block;
	}

	.workflow-grid span {
		font-size: var(--text-lg);
		line-height: 1.1;
	}

	@media (max-width: 760px) {
		.money-grid,
		.workflow-grid {
			grid-template-columns: 1fr;
		}
	}
</style>
