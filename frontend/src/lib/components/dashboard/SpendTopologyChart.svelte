<script lang="ts">
	import { Activity } from '@lucide/svelte';
	import type { DailySpendPoint, ProviderSpendBreakdown } from './overviewTypes';

	let {
		dailySpend = [],
		cloudBreakdown = [],
		totalSpendUsd = 0,
		periodLabel = 'Period',
		spendTrendPercent = null
	} = $props<{
		dailySpend: DailySpendPoint[];
		cloudBreakdown: ProviderSpendBreakdown[];
		totalSpendUsd: number;
		periodLabel: string;
		spendTrendPercent: number | null;
	}>();

	const width = 720;
	const height = 250;
	const padding = { top: 24, right: 28, bottom: 34, left: 48 };
	const colors = ['#22d3ee', '#34d399', '#fbbf24', '#a78bfa', '#fb7185', '#94a3b8'];

	const chart = $derived(buildChart(dailySpend));
	const hasChart = $derived(chart.points.length >= 2);
	const trendLabel = $derived(
		spendTrendPercent === null
			? 'Trend unavailable'
			: `${spendTrendPercent >= 0 ? '+' : ''}${spendTrendPercent.toFixed(1)}% first-to-last day`
	);

	function formatMoney(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: value >= 1000 ? 0 : 2
		}).format(value);
	}

	function formatDate(value: string): string {
		const date = new Date(`${value}T00:00:00Z`);
		if (Number.isNaN(date.getTime())) return value;
		return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(date);
	}

	function buildChart(points: DailySpendPoint[]) {
		const sorted = [...points].sort((left, right) => left.date.localeCompare(right.date));
		const maxCost = Math.max(...sorted.map((point) => point.costUsd), 0);
		const xSpan = width - padding.left - padding.right;
		const ySpan = height - padding.top - padding.bottom;
		const scaled = sorted.map((point, index) => {
			const x = padding.left + (sorted.length <= 1 ? 0 : (index / (sorted.length - 1)) * xSpan);
			const y = padding.top + (maxCost <= 0 ? ySpan : ySpan - (point.costUsd / maxCost) * ySpan);
			return { ...point, x, y };
		});
		const linePath = scaled
			.map(
				(point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
			)
			.join(' ');
		const areaPath =
			scaled.length > 0
				? `${linePath} L ${scaled[scaled.length - 1].x.toFixed(2)} ${height - padding.bottom} L ${scaled[0].x.toFixed(2)} ${height - padding.bottom} Z`
				: '';
		return {
			points: scaled,
			linePath,
			areaPath,
			maxCost
		};
	}
</script>

<section class="topology-panel" aria-labelledby="spend-topology-title">
	<div class="panel-heading">
		<div>
			<p class="panel-kicker">{periodLabel} ledger topology</p>
			<h2 id="spend-topology-title">Spend Topology</h2>
		</div>
		<div class="spend-total">
			<span>{formatMoney(totalSpendUsd)}</span>
			<small>{trendLabel}</small>
		</div>
	</div>

	{#if hasChart}
		<svg
			class="chart"
			viewBox={`0 0 ${width} ${height}`}
			role="img"
			aria-label={`Daily spend trend for ${periodLabel}; total spend ${formatMoney(totalSpendUsd)}.`}
		>
			<defs>
				<linearGradient id="spend-area-gradient" x1="0" y1="0" x2="0" y2="1">
					<stop offset="0%" stop-color="#22d3ee" stop-opacity="0.34" />
					<stop offset="100%" stop-color="#34d399" stop-opacity="0.04" />
				</linearGradient>
			</defs>
			<g class="grid-lines" aria-hidden="true">
				{#each [0, 1, 2, 3] as tick}
					<line
						x1={padding.left}
						x2={width - padding.right}
						y1={padding.top + tick * ((height - padding.top - padding.bottom) / 3)}
						y2={padding.top + tick * ((height - padding.top - padding.bottom) / 3)}
					/>
				{/each}
			</g>
			<path class="area" d={chart.areaPath} />
			<path class="line" d={chart.linePath} />
			{#each chart.points as point (point.date)}
				<circle class="point" cx={point.x} cy={point.y} r="4">
					<title>{formatDate(point.date)}: {formatMoney(point.costUsd)}</title>
				</circle>
			{/each}
			<text class="axis-label axis-label--left" x={padding.left} y="18">
				{formatMoney(chart.maxCost)}
			</text>
			<text class="axis-label" x={padding.left} y={height - 8}>
				{formatDate(chart.points[0].date)}
			</text>
			<text class="axis-label axis-label--right" x={width - padding.right} y={height - 8}>
				{formatDate(chart.points[chart.points.length - 1].date)}
			</text>
		</svg>
	{:else}
		<div class="empty-chart" role="status">
			<Activity size={20} />
			<p>Daily spend series unavailable for this view.</p>
		</div>
	{/if}

	<div class="provider-strip" aria-label="Provider spend breakdown">
		{#if cloudBreakdown.length > 0}
			{#each cloudBreakdown.slice(0, 6) as provider, index (provider.provider)}
				<div class="provider-row">
					<div class="provider-row__label">
						<span class="swatch" style={`--swatch: ${colors[index % colors.length]}`}></span>
						<span>{provider.label}</span>
					</div>
					<div class="provider-row__meter" aria-hidden="true">
						<span
							style={`width: ${Math.max(2, provider.share)}%; --meter: ${colors[index % colors.length]}`}
						></span>
					</div>
					<strong>{formatMoney(provider.costUsd)}</strong>
				</div>
			{/each}
		{:else}
			<p class="muted">Provider breakdown unavailable.</p>
		{/if}
	</div>
</section>

<style>
	.topology-panel {
		min-height: 30rem;
		padding: 1.25rem;
		border: 1px solid rgb(128 154 176 / 0.2);
		border-radius: var(--radius-md);
		background:
			linear-gradient(180deg, rgb(24 32 40 / 0.88), rgb(10 13 18 / 0.72)),
			radial-gradient(circle at 20% 0%, rgb(34 211 238 / 0.12), transparent 30%);
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

	.spend-total {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 0.125rem;
		text-align: right;
	}

	.spend-total span {
		color: var(--color-accent-300);
		font-size: var(--text-xl);
		font-weight: 800;
	}

	.spend-total small,
	.muted {
		color: var(--color-ink-400);
		font-size: var(--text-xs);
	}

	.chart {
		width: 100%;
		min-height: 16rem;
		overflow: visible;
	}

	.grid-lines line {
		stroke: rgb(128 154 176 / 0.16);
		stroke-width: 1;
	}

	.area {
		fill: url('#spend-area-gradient');
	}

	.line {
		fill: none;
		stroke: var(--color-accent-300);
		stroke-width: 3;
		stroke-linecap: round;
		stroke-linejoin: round;
	}

	.point {
		fill: var(--color-ink-950);
		stroke: var(--color-success-300);
		stroke-width: 2;
	}

	.axis-label {
		fill: var(--color-ink-400);
		font-size: 12px;
		font-family: var(--font-mono);
	}

	.axis-label--left {
		text-anchor: start;
	}

	.axis-label--right {
		text-anchor: end;
	}

	.empty-chart {
		display: grid;
		min-height: 16rem;
		place-items: center;
		align-content: center;
		gap: 0.625rem;
		color: var(--color-ink-400);
		border: 1px dashed rgb(128 154 176 / 0.24);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
	}

	.empty-chart p {
		margin: 0;
		font-size: var(--text-sm);
	}

	.provider-strip {
		display: grid;
		gap: 0.625rem;
		margin-top: 1rem;
	}

	.provider-row {
		display: grid;
		grid-template-columns: minmax(5.5rem, 0.8fr) minmax(5rem, 1fr) minmax(5rem, auto);
		align-items: center;
		gap: 0.75rem;
		font-size: var(--text-sm);
	}

	.provider-row__label {
		display: flex;
		min-width: 0;
		align-items: center;
		gap: 0.5rem;
		color: var(--color-ink-200);
	}

	.provider-row__label span:last-child {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.swatch {
		width: 0.625rem;
		height: 0.625rem;
		border-radius: var(--radius-full);
		background: var(--swatch);
		box-shadow: 0 0 16px color-mix(in srgb, var(--swatch), transparent 50%);
	}

	.provider-row__meter {
		height: 0.375rem;
		overflow: hidden;
		border-radius: var(--radius-full);
		background: rgb(128 154 176 / 0.14);
	}

	.provider-row__meter span {
		display: block;
		height: 100%;
		border-radius: inherit;
		background: var(--meter);
	}

	.provider-row strong {
		color: var(--color-ink-100);
		font-family: var(--font-mono);
		font-size: var(--text-xs);
		text-align: right;
	}

	@media (max-width: 700px) {
		.panel-heading {
			flex-direction: column;
		}

		.spend-total {
			align-items: flex-start;
			text-align: left;
		}

		.provider-row {
			grid-template-columns: 1fr;
			gap: 0.4rem;
		}

		.provider-row strong {
			text-align: left;
		}
	}
</style>
