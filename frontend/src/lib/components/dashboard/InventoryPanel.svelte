<script lang="ts">
	import { Boxes, Clock, ShieldAlert } from '@lucide/svelte';
	import type { ApprovalQueueSummary, TopServiceSpend } from './overviewTypes';

	let {
		zombieCount = 0,
		monthlyWasteUsd = 0,
		topServices = [],
		approvals
	} = $props<{
		zombieCount: number;
		monthlyWasteUsd: number;
		topServices: TopServiceSpend[];
		approvals: ApprovalQueueSummary;
	}>();

	function formatMoney(value: number): string {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: value >= 1000 ? 0 : 2
		}).format(value);
	}

	function formatAction(value: string): string {
		return value.replace(/_/g, ' ');
	}
</script>

<section class="inventory-panel" aria-labelledby="inventory-panel-title">
	<div class="panel-heading">
		<div>
			<p class="panel-kicker">Evidence inventory</p>
			<h2 id="inventory-panel-title">Operational Signals</h2>
		</div>
		<Boxes size={21} />
	</div>

	<div class="inventory-stats">
		<div>
			<ShieldAlert size={18} />
			<span>{zombieCount}</span>
			<small>waste findings</small>
		</div>
		<div>
			<Clock size={18} />
			<span>{approvals.pendingCount}</span>
			<small>pending approvals</small>
		</div>
	</div>

	<div class="waste-band">
		<span>Monthly opportunity from waste signals</span>
		<strong>{formatMoney(monthlyWasteUsd)}</strong>
	</div>

	<div class="split-list">
		<div>
			<h3>Top Services</h3>
			{#if topServices.length > 0}
				<ul>
					{#each topServices.slice(0, 4) as service (service.service)}
						<li>
							<span>{service.service}</span>
							<strong>{formatMoney(service.costUsd)}</strong>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="empty">Service spend evidence unavailable.</p>
			{/if}
		</div>

		<div>
			<h3>Approval Queue</h3>
			{#if approvals.items.length > 0}
				<ul>
					{#each approvals.items as item (item.id)}
						<li>
							<span>{formatAction(item.action)} · {item.environment}</span>
							<strong>{formatMoney(item.monthlyDeltaUsd)}</strong>
						</li>
					{/each}
				</ul>
			{:else}
				<p class="empty">No reviewer-visible approval requests.</p>
			{/if}
		</div>
	</div>
</section>

<style>
	.inventory-panel {
		min-height: 22rem;
		padding: 1.25rem;
		border: 1px solid rgb(128 154 176 / 0.2);
		border-radius: var(--radius-md);
		background: linear-gradient(180deg, rgb(24 32 40 / 0.84), rgb(10 13 18 / 0.72));
		box-shadow: 0 18px 50px rgb(0 0 0 / 0.24);
	}

	.panel-heading {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
		color: var(--color-accent-300);
	}

	.panel-kicker {
		margin: 0 0 0.25rem;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		font-weight: 700;
		text-transform: uppercase;
	}

	h2,
	h3 {
		margin: 0;
		color: var(--color-ink-50);
		letter-spacing: 0;
	}

	h2 {
		font-size: var(--text-xl);
		font-weight: 750;
	}

	h3 {
		margin-bottom: 0.625rem;
		font-size: var(--text-sm);
		font-weight: 750;
	}

	.inventory-stats {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 0.75rem;
	}

	.inventory-stats div {
		display: grid;
		gap: 0.25rem;
		padding: 0.85rem;
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
		color: var(--color-ink-400);
	}

	.inventory-stats span {
		color: var(--color-ink-50);
		font-family: var(--font-mono);
		font-size: var(--text-2xl);
		font-weight: 850;
		line-height: 1;
	}

	.inventory-stats small {
		color: var(--color-ink-400);
		font-size: var(--text-xs);
	}

	.waste-band {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 1rem;
		margin: 0.9rem 0 1rem;
		padding: 0.8rem 0.9rem;
		border: 1px solid rgb(251 191 36 / 0.24);
		border-radius: var(--radius-md);
		background: rgb(251 191 36 / 0.07);
	}

	.waste-band span {
		color: var(--color-ink-300);
		font-size: var(--text-sm);
	}

	.waste-band strong {
		color: var(--color-warning-400);
		font-family: var(--font-mono);
		white-space: nowrap;
	}

	.split-list {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 1rem;
	}

	ul {
		display: grid;
		gap: 0.55rem;
		margin: 0;
		padding: 0;
		list-style: none;
	}

	li {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.75rem;
		min-width: 0;
		font-size: var(--text-sm);
	}

	li span {
		min-width: 0;
		overflow: hidden;
		color: var(--color-ink-300);
		text-overflow: ellipsis;
		text-transform: capitalize;
		white-space: nowrap;
	}

	li strong {
		color: var(--color-ink-100);
		font-family: var(--font-mono);
		font-size: var(--text-xs);
		white-space: nowrap;
	}

	.empty {
		margin: 0;
		color: var(--color-ink-400);
		font-size: var(--text-sm);
	}

	@media (max-width: 760px) {
		.inventory-stats,
		.split-list {
			grid-template-columns: 1fr;
		}

		.waste-band {
			align-items: flex-start;
			flex-direction: column;
			gap: 0.3rem;
		}
	}
</style>
