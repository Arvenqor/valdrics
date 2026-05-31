<script lang="ts">
	import { TICKER_ITEMS } from './landingContent';
</script>

<div class="ticker" aria-hidden="true">
	<div class="ticker__track">
		{#each Array(2) as _}
			{#each TICKER_ITEMS as item}
				<div class="ticker__item">
					<span class="tdot"></span>
					{item.before}{#if item.strong}<strong>{item.strong}</strong>{/if}{item.after ?? ''}
				</div>
			{/each}
		{/each}
	</div>
</div>

<style>
	.ticker {
		overflow: hidden;
		padding: 16px 0;
		border-top: 1px solid var(--bdr);
		border-bottom: 1px solid var(--bdr);
		background: var(--base);
		position: relative;
	}
	.ticker::before,
	.ticker::after {
		content: '';
		position: absolute;
		top: 0;
		bottom: 0;
		width: 100px;
		z-index: 2;
	}
	.ticker::before {
		left: 0;
		background: linear-gradient(to right, var(--base), transparent);
	}
	.ticker::after {
		right: 0;
		background: linear-gradient(to left, var(--base), transparent);
	}
	.ticker__track {
		display: flex;
		width: max-content;
		animation: ticker 32s linear infinite;
	}
	.ticker__item {
		display: flex;
		align-items: center;
		gap: 9px;
		padding: 0 30px;
		white-space: nowrap;
		font-family: var(--font-mono);
		font-size: 13px;
		color: var(--sub);
		border-right: 1px solid var(--bdr);
	}
	.ticker__item strong {
		color: var(--white);
	}
	.tdot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: var(--jade);
		flex-shrink: 0;
	}
	@keyframes ticker {
		to {
			transform: translateX(-50%);
		}
	}
</style>
