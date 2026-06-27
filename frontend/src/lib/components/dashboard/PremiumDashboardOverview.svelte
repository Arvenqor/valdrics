<script lang="ts">
	import { base } from '$app/paths';
	import { formatCompactUsd, formatNumber } from '$lib/format';
	import InventoryPanel from './InventoryPanel.svelte';
	import PolicyHealthRings from './PolicyHealthRings.svelte';
	import SavingsPanel from './SavingsPanel.svelte';
	import SpendTopologyChart from './SpendTopologyChart.svelte';
	import type { DashboardOverviewModel, PolicyHealthMetric } from './overviewTypes';

	let { overview } = $props<{
		overview: DashboardOverviewModel;
	}>();

	function formatPercent(value: number | null): string {
		return value === null ? 'N/A' : `${value.toFixed(0)}%`;
	}

	function averageAvailableMetric(metrics: PolicyHealthMetric[]): number | null {
		const available = metrics
			.map((metric: PolicyHealthMetric) => metric.value)
			.filter((value: number | null): value is number => value !== null);
		if (available.length === 0) return null;
		return available.reduce((sum: number, value: number) => sum + value, 0) / available.length;
	}

	const policyScore = $derived(averageAvailableMetric(overview.policyHealth.metrics));
	const policyScoreTone = $derived(
		policyScore === null
			? 'var(--color-ink-300)'
			: policyScore >= 90
				? 'var(--color-success-300)'
				: policyScore >= 70
					? 'var(--color-warning-400)'
					: 'var(--color-danger-400)'
	);
	const annualizedSavings = $derived(overview.savings.realizedMonthlyUsd * 12);
	const summaryCards = $derived([
		{
			id: 'spend',
			label: `${overview.periodLabel} Spend`,
			value: formatCompactUsd(overview.totalSpendUsd),
			sub: `${overview.cloudBreakdown.length} provider signals · ${overview.dailySpend.length} daily ledger points`,
			tone: 'var(--color-ink-50)',
			href: '',
			blink: false
		},
		{
			id: 'approvals',
			label: 'Pending Approvals',
			value: String(overview.approvals.pendingCount),
			sub:
				overview.approvals.pendingCount > 0
					? `${formatCompactUsd(overview.approvals.monthlyDeltaUsd)} monthly delta awaiting review`
					: 'No reviewer-visible approval requests',
			tone:
				overview.approvals.pendingCount > 0
					? 'var(--color-warning-400)'
					: 'var(--color-success-300)',
			href: `${base}/approvals`,
			blink: overview.approvals.pendingCount > 0
		},
		{
			id: 'policy',
			label: 'Policy Health',
			value: formatPercent(policyScore),
			sub:
				policyScore === null
					? 'No current governance coverage evidence'
					: `${overview.policyHealth.highRiskDecisions} high-risk decisions in window`,
			tone: policyScoreTone,
			href: '',
			blink: false
		},
		{
			id: 'savings',
			label: 'Savings Realized',
			value: formatCompactUsd(overview.savings.realizedMonthlyUsd),
			sub: `${formatCompactUsd(annualizedSavings)}/yr run-rate from applied actions`,
			tone: 'var(--color-success-300)',
			href: `${base}/savings`,
			blink: false
		}
	]);
</script>

<section class="premium-overview" aria-labelledby="premium-overview-title">
	<div class="overview-header">
		<div>
			<p class="panel-kicker">Production control plane</p>
			<h2 id="premium-overview-title">Governance Overview</h2>
		</div>
		<p class="overview-context">
			{overview.provider ? `${overview.provider.toUpperCase()} filter` : 'All providers'} · {overview.periodLabel}
		</p>
	</div>

	<div class="summary-grid" aria-label="Key governance metrics">
		{#each summaryCards as card (card.id)}
			<div class="summary-card">
				<div class="summary-card__label">
					{#if card.blink}
						<span class="blink-dot" aria-hidden="true"></span>
					{/if}
					{card.label}
				</div>
				{#if card.href}
					<a
						class="summary-card__value summary-card__value--link"
						href={card.href}
						style={`color: ${card.tone}`}
					>
						{card.value}
					</a>
				{:else}
					<div class="summary-card__value" style={`color: ${card.tone}`}>
						{card.value}
					</div>
				{/if}
				<div class="summary-card__sub">{card.sub}</div>
			</div>
		{/each}
	</div>

	<div class="evidence-strip" aria-label="Additional operating evidence">
		<span>{formatNumber(overview.carbonTotalKgco2e)} kg CO2e evidence</span>
		<span>{overview.zombieCount} waste findings</span>
		<span>{formatCompactUsd(overview.monthlyWasteUsd)} monthly waste opportunity</span>
	</div>

	<div class="overview-grid overview-grid--top">
		<SpendTopologyChart
			dailySpend={overview.dailySpend}
			cloudBreakdown={overview.cloudBreakdown}
			totalSpendUsd={overview.totalSpendUsd}
			periodLabel={overview.periodLabel}
			spendTrendPercent={overview.spendTrendPercent}
		/>
		<PolicyHealthRings
			metrics={overview.policyHealth.metrics}
			highRiskDecisions={overview.policyHealth.highRiskDecisions}
			approvalRequiredDecisions={overview.policyHealth.approvalRequiredDecisions}
			anomalySignalDecisions={overview.policyHealth.anomalySignalDecisions}
		/>
	</div>

	<div class="overview-grid overview-grid--bottom">
		<InventoryPanel
			zombieCount={overview.zombieCount}
			monthlyWasteUsd={overview.monthlyWasteUsd}
			topServices={overview.topServices}
			approvals={overview.approvals}
		/>
		<SavingsPanel savings={overview.savings} />
	</div>

	{#if overview.notes.length > 0}
		<div class="overview-notes" aria-label="Dashboard data notes">
			{#each overview.notes.slice(0, 2) as note}
				<p>{note}</p>
			{/each}
		</div>
	{/if}
</section>

<style>
	.premium-overview {
		display: grid;
		gap: 1rem;
	}

	.overview-header {
		display: flex;
		align-items: end;
		justify-content: space-between;
		gap: 1rem;
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
		font-size: var(--text-2xl);
		font-weight: 800;
		letter-spacing: 0;
	}

	.overview-context {
		margin: 0;
		color: var(--color-ink-400);
		font-size: var(--text-sm);
		text-align: right;
	}

	.summary-grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 1px;
		overflow: hidden;
		border: 1px solid rgb(128 154 176 / 0.18);
		border-radius: var(--radius-md);
		background: rgb(128 154 176 / 0.18);
	}

	.summary-card {
		display: grid;
		gap: 0.35rem;
		min-height: 7.2rem;
		padding: 1.05rem 1.2rem;
		background:
			linear-gradient(180deg, rgb(15 19 24 / 0.94), rgb(10 13 18 / 0.86)),
			radial-gradient(circle at 24% 0%, rgb(34 211 238 / 0.08), transparent 32%);
		transition:
			background var(--duration-fast) var(--ease-out),
			transform var(--duration-fast) var(--ease-out);
	}

	.summary-card:hover {
		background:
			linear-gradient(180deg, rgb(24 32 40 / 0.96), rgb(10 13 18 / 0.9)),
			radial-gradient(circle at 24% 0%, rgb(52 211 153 / 0.1), transparent 34%);
		transform: translateY(-1px);
	}

	.summary-card__label {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.blink-dot {
		width: 0.4rem;
		height: 0.4rem;
		border-radius: var(--radius-full);
		background: var(--color-warning-400);
		box-shadow: 0 0 0 0 rgb(251 191 36 / 0.6);
		animation: blinkDot 1.6s ease-in-out infinite;
	}

	@keyframes blinkDot {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.45;
			transform: scale(0.72);
		}
	}

	.summary-card__value {
		align-self: end;
		min-width: 0;
		overflow-wrap: anywhere;
		font-family: var(--font-mono);
		font-size: clamp(1.3rem, 2vw, 1.8rem);
		font-weight: 850;
		line-height: 1;
	}

	.summary-card__value--link {
		text-decoration: none;
	}

	.summary-card__value--link:hover {
		opacity: 0.82;
	}

	.summary-card__sub {
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		line-height: 1.45;
	}

	.evidence-strip {
		display: flex;
		flex-wrap: wrap;
		gap: 0.6rem;
	}

	.evidence-strip span {
		padding: 0.38rem 0.55rem;
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-sm);
		background: rgb(10 13 18 / 0.34);
		color: var(--color-ink-300);
		font-size: var(--text-xs);
	}

	.overview-grid {
		display: grid;
		gap: 1rem;
		align-items: stretch;
	}

	.overview-grid--top {
		grid-template-columns: minmax(0, 1.35fr) minmax(20rem, 0.85fr);
	}

	.overview-grid--bottom {
		grid-template-columns: minmax(0, 1fr) minmax(20rem, 0.7fr);
	}

	.overview-notes {
		display: grid;
		gap: 0.35rem;
		padding: 0.8rem 1rem;
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
	}

	.overview-notes p {
		margin: 0;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		line-height: 1.45;
	}

	@media (max-width: 1100px) {
		.summary-grid,
		.overview-grid--top,
		.overview-grid--bottom {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 760px) {
		.overview-header {
			align-items: flex-start;
			flex-direction: column;
		}

		.overview-context {
			text-align: left;
		}

		.summary-grid,
		.overview-grid--top,
		.overview-grid--bottom {
			grid-template-columns: 1fr;
		}
	}
</style>
