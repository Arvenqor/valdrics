<script lang="ts">
	import { AlertTriangle, CheckCircle2, ShieldCheck } from '@lucide/svelte';
	import type { PolicyHealthMetric } from './overviewTypes';

	let {
		metrics = [],
		highRiskDecisions = 0,
		approvalRequiredDecisions = 0,
		anomalySignalDecisions = 0
	} = $props<{
		metrics: PolicyHealthMetric[];
		highRiskDecisions: number;
		approvalRequiredDecisions: number;
		anomalySignalDecisions: number;
	}>();

	const size = 188;
	const center = size / 2;
	const baseRadius = 72;
	const stroke = 10;
	const colors = ['#34d399', '#22d3ee', '#fbbf24'];
	const normalizedMetrics = $derived(metrics.slice(0, 3));
	const riskLabel = $derived(
		highRiskDecisions > 0
			? `${highRiskDecisions} high-risk decisions`
			: 'No high-risk decisions in window'
	);
	const healthAriaLabel = $derived(
		`Policy health: ${
			normalizedMetrics
				.map((metric: PolicyHealthMetric) => `${metric.label} ${metricLabel(metric)}`)
				.join(', ') || 'no health evidence available'
		}.`
	);
	const healthScore = $derived(computeHealthScore(normalizedMetrics));

	function circumference(radius: number): number {
		return 2 * Math.PI * radius;
	}

	function dash(metric: PolicyHealthMetric, radius: number): string {
		if (metric.value === null) return `0 ${circumference(radius)}`;
		const clamped = Math.max(0, Math.min(100, metric.value));
		const length = (clamped / 100) * circumference(radius);
		return `${length} ${circumference(radius) - length}`;
	}

	function metricLabel(metric: PolicyHealthMetric): string {
		return metric.value === null ? 'Unavailable' : `${metric.value.toFixed(0)}%`;
	}

	function computeHealthScore(values: PolicyHealthMetric[]): number | null {
		const available = values
			.map((metric) => metric.value)
			.filter((value): value is number => value !== null);
		if (available.length === 0) return null;
		return available.reduce((sum, value) => sum + value, 0) / available.length;
	}
</script>

<section class="health-panel" aria-labelledby="policy-health-title">
	<div class="panel-heading">
		<div>
			<p class="panel-kicker">Governance posture</p>
			<h2 id="policy-health-title">Policy Health</h2>
		</div>
		<div class:warn={highRiskDecisions > 0} class="risk-badge">
			{#if highRiskDecisions > 0}
				<AlertTriangle size={15} />
			{:else}
				<CheckCircle2 size={15} />
			{/if}
			<span>{riskLabel}</span>
		</div>
	</div>

	<div class="health-body">
		<svg class="rings" viewBox={`0 0 ${size} ${size}`} role="img" aria-label={healthAriaLabel}>
			<circle class="ring-core" cx={center} cy={center} r="39" />
			{#each normalizedMetrics as metric, index (metric.key)}
				{@const radius = baseRadius - index * 18}
				<circle
					class="ring-track"
					cx={center}
					cy={center}
					r={radius}
					stroke-width={stroke}
					pathLength={circumference(radius)}
				/>
				<circle
					class="ring-progress"
					cx={center}
					cy={center}
					r={radius}
					stroke={colors[index % colors.length]}
					stroke-width={stroke}
					stroke-dasharray={dash(metric, radius)}
					pathLength={circumference(radius)}
				/>
			{/each}
			{#if healthScore === null}
				<foreignObject x="61" y="61" width="66" height="66">
					<div class="core-mark">
						<ShieldCheck size={28} />
					</div>
				</foreignObject>
			{:else}
				<text class="score-value" x={center} y={center - 1}>{healthScore.toFixed(0)}</text>
				<text class="score-label" x={center} y={center + 19}>score</text>
			{/if}
		</svg>

		<div class="metric-list">
			{#each normalizedMetrics as metric, index (metric.key)}
				<div class="metric-row">
					<span class="metric-dot" style={`--metric-color: ${colors[index % colors.length]}`}
					></span>
					<div>
						<strong>{metric.label}</strong>
						<small>{metric.detail}</small>
					</div>
					<span class="metric-value">{metricLabel(metric)}</span>
				</div>
			{/each}
		</div>
	</div>

	<div class="decision-grid">
		<div>
			<span>{approvalRequiredDecisions}</span>
			<small>approval-gated</small>
		</div>
		<div>
			<span>{anomalySignalDecisions}</span>
			<small>anomaly signals</small>
		</div>
	</div>
</section>

<style>
	.health-panel {
		min-height: 30rem;
		padding: 1.25rem;
		border: 1px solid rgb(128 154 176 / 0.2);
		border-radius: var(--radius-md);
		background:
			linear-gradient(180deg, rgb(24 32 40 / 0.88), rgb(10 13 18 / 0.72)),
			radial-gradient(circle at 86% 0%, rgb(52 211 153 / 0.12), transparent 34%);
		box-shadow: 0 18px 50px rgb(0 0 0 / 0.28);
	}

	.panel-heading {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
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

	.risk-badge {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.35rem 0.55rem;
		border: 1px solid rgb(52 211 153 / 0.28);
		border-radius: var(--radius-md);
		color: var(--color-success-300);
		background: rgb(52 211 153 / 0.08);
		font-size: var(--text-xs);
		font-weight: 700;
		white-space: nowrap;
	}

	.risk-badge.warn {
		border-color: rgb(251 191 36 / 0.34);
		color: var(--color-warning-400);
		background: rgb(251 191 36 / 0.08);
	}

	.health-body {
		display: grid;
		grid-template-columns: minmax(10rem, 13rem) 1fr;
		align-items: center;
		gap: 1rem;
	}

	.rings {
		width: min(100%, 13rem);
		justify-self: center;
		overflow: visible;
	}

	.ring-track,
	.ring-progress {
		fill: none;
		transform: rotate(-90deg);
		transform-origin: center;
		stroke-linecap: round;
	}

	.ring-track {
		stroke: rgb(128 154 176 / 0.16);
	}

	.ring-progress {
		filter: drop-shadow(0 0 10px rgb(34 211 238 / 0.18));
		transition: stroke-dasharray var(--duration-slow) var(--ease-out);
	}

	.ring-core {
		fill: rgb(10 13 18 / 0.84);
		stroke: rgb(128 154 176 / 0.2);
	}

	.core-mark {
		display: grid;
		width: 100%;
		height: 100%;
		place-items: center;
		color: var(--color-accent-300);
	}

	.score-value,
	.score-label {
		text-anchor: middle;
	}

	.score-value {
		fill: var(--color-success-300);
		font-family: var(--font-mono);
		font-size: 1.6rem;
		font-weight: 850;
	}

	.score-label {
		fill: var(--color-ink-400);
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.metric-list {
		display: grid;
		gap: 0.8rem;
	}

	.metric-row {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) auto;
		align-items: start;
		gap: 0.625rem;
	}

	.metric-dot {
		width: 0.625rem;
		height: 0.625rem;
		margin-top: 0.4rem;
		border-radius: var(--radius-full);
		background: var(--metric-color);
	}

	.metric-row strong {
		display: block;
		color: var(--color-ink-100);
		font-size: var(--text-sm);
		line-height: 1.2;
	}

	.metric-row small {
		display: block;
		margin-top: 0.2rem;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		line-height: 1.35;
	}

	.metric-value {
		color: var(--color-ink-100);
		font-family: var(--font-mono);
		font-size: var(--text-sm);
		font-weight: 800;
	}

	.decision-grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.decision-grid div {
		padding: 0.8rem;
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
	}

	.decision-grid span {
		display: block;
		color: var(--color-ink-50);
		font-family: var(--font-mono);
		font-size: var(--text-lg);
		font-weight: 800;
	}

	.decision-grid small {
		display: block;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
	}

	@media (max-width: 760px) {
		.panel-heading,
		.health-body {
			grid-template-columns: 1fr;
			flex-direction: column;
		}

		.risk-badge {
			white-space: normal;
		}
	}
</style>
