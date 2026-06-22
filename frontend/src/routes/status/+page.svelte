<script lang="ts">
	import PublicPageMeta from '$lib/components/public/PublicPageMeta.svelte';

	import type { PageData } from './$types';
	import type { StatusTone } from './statusPage';

	let { data }: { data: PageData } = $props();

	const toneClassByValue: Record<StatusTone, string> = {
		success: 'status-pill status-pill--success',
		warning: 'status-pill status-pill--warning',
		danger: 'status-pill status-pill--danger',
		neutral: 'status-pill status-pill--neutral'
	};

	const summaryClassByValue: Record<StatusTone, string> = {
		success: 'status-summary status-summary--success',
		warning: 'status-summary status-summary--warning',
		danger: 'status-summary status-summary--danger',
		neutral: 'status-summary status-summary--neutral'
	};

	const statusCounts = $derived(
		data.components.reduce(
			(counts, component) => {
				counts.total += 1;
				if (component.tone === 'success') counts.operational += 1;
				if (component.tone === 'warning' || component.tone === 'danger') counts.attention += 1;
				if (component.tone === 'neutral') counts.unknown += 1;
				return counts;
			},
			{ total: 0, operational: 0, attention: 0, unknown: 0 }
		)
	);

	const sourceLabel = $derived(
		data.source === 'live' ? 'Automated health summary' : 'Fallback summary'
	);
	const checkedAtLabel = $derived(formatCheckedAt(data.checkedAt));

	function formatCheckedAt(timestamp: string): string {
		const date = new Date(timestamp);
		if (Number.isNaN(date.getTime())) return 'Unknown';
		return new Intl.DateTimeFormat('en-US', {
			dateStyle: 'medium',
			timeStyle: 'short'
		}).format(date);
	}
</script>

<PublicPageMeta
	title="System Status"
	description="Current service status for Valdrics core platform dependencies and automated health checks."
	pageType="WebPage"
	pageSection="Status"
	keywords={['system status', 'service health', 'incident readiness', 'platform health']}
/>

<div class="status-page">
	<section class="status-hero" aria-labelledby="status-title">
		<div class="status-hero__copy">
			<h1 id="status-title">System status</h1>
			<p>
				Public health summary for Valdrics platform dependencies. This page reports the latest
				server-verified health snapshot only; incident response and maintenance communications
				remain separate operational workflows.
			</p>
			<div class={summaryClassByValue[data.summaryTone]}>
				<span>{data.summaryLabel}</span>
				<strong>{data.summaryDetail}</strong>
			</div>
		</div>

		<div class="material-perspective">
			<dl class="status-facts material-card-3d" aria-label="Status provenance">
				<div>
					<dt>Last checked</dt>
					<dd>{checkedAtLabel}</dd>
				</div>
				<div>
					<dt>Source</dt>
					<dd>{sourceLabel}</dd>
				</div>
				<div>
					<dt>Components tracked</dt>
					<dd>{statusCounts.total}</dd>
				</div>
			</dl>
		</div>
	</section>

	<section class="status-rollup" aria-label="Status rollup">
		<div class="material-perspective">
			<article class="material-card-3d">
				<strong>{statusCounts.operational}</strong>
				<span>operational</span>
			</article>
		</div>
		<div class="material-perspective">
			<article class="material-card-3d">
				<strong>{statusCounts.attention}</strong>
				<span>need attention</span>
			</article>
		</div>
		<div class="material-perspective">
			<article class="material-card-3d">
				<strong>{statusCounts.unknown}</strong>
				<span>unknown</span>
			</article>
		</div>
	</section>

	{#if data.source !== 'live'}
		<section class="status-notice" aria-labelledby="status-notice-title">
			<h2 id="status-notice-title">Automated checks are unavailable</h2>
			<p>{data.summaryDetail}</p>
		</section>
	{/if}

	<section class="status-services" aria-labelledby="status-services-title">
		<div class="status-services__head">
			<h2 id="status-services-title">Dependency summary</h2>
			<p>
				Each component is derived from the backend health payload or the explicit fallback snapshot.
			</p>
		</div>

		<div class="status-grid">
			{#each data.components as component (component.name)}
				<div class="material-perspective">
					<article class="status-card material-card-3d">
						<div class="status-card__head">
							<h3>{component.name}</h3>
							<span class={toneClassByValue[component.tone]}>{component.statusLabel}</span>
						</div>
						<p>{component.detail}</p>
					</article>
				</div>
			{/each}
		</div>
	</section>
</div>

<style>
	.status-page {
		width: min(1120px, calc(100% - 2rem));
		margin: 0 auto;
		padding: clamp(3rem, 8vw, 6rem) 0 clamp(4rem, 9vw, 7rem);
	}

	.status-hero {
		display: grid;
		grid-template-columns: minmax(0, 1fr) minmax(17rem, 0.42fr);
		gap: clamp(1.25rem, 4vw, 3rem);
		align-items: end;
	}

	.status-hero__copy {
		max-width: 48rem;
	}

	.status-hero h1,
	.status-services h2,
	.status-notice h2,
	.status-card h3 {
		margin: 0;
		letter-spacing: 0;
	}

	.status-hero h1 {
		color: var(--color-ink-50, #f0f4f8);
		font-size: clamp(2.75rem, 7vw, 5.75rem);
		font-weight: 760;
		line-height: 0.95;
	}

	.status-hero__copy > p {
		max-width: 42rem;
		margin: 1.3rem 0 0;
		color: var(--color-ink-300, rgba(240, 244, 248, 0.7));
		font-size: clamp(1rem, 1.6vw, 1.18rem);
		line-height: 1.7;
	}

	.status-summary {
		display: grid;
		gap: 0.45rem;
		margin-top: 1.5rem;
		border-left: 0.25rem solid rgb(148, 163, 184);
		padding: 0.2rem 0 0.2rem 1rem;
	}

	.status-summary span {
		color: var(--color-ink-50, #f0f4f8);
		font-size: 0.9rem;
		font-weight: 760;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.status-summary strong {
		color: var(--color-ink-300, rgba(240, 244, 248, 0.7));
		font-size: 0.95rem;
		font-weight: 500;
		line-height: 1.55;
	}

	.status-summary--success {
		border-color: rgb(52, 211, 153);
	}

	.status-summary--warning {
		border-color: rgb(251, 191, 36);
	}

	.status-summary--danger {
		border-color: rgb(248, 113, 113);
	}

	.status-summary--neutral {
		border-color: rgb(148, 163, 184);
	}

	.status-facts {
		display: grid;
		gap: 0.8rem;
		margin: 0;
		border: 1px solid rgb(51 65 85 / 0.72);
		border-radius: 0.75rem;
		background: rgb(15 23 42 / 0.72);
		padding: 1rem;
	}

	.status-facts div {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 1rem;
		border-bottom: 1px solid rgb(51 65 85 / 0.58);
		padding-bottom: 0.8rem;
	}

	.status-facts div:last-child {
		border-bottom: 0;
		padding-bottom: 0;
	}

	.status-facts dt {
		color: rgb(148, 163, 184);
		font-size: 0.72rem;
		font-weight: 720;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.status-facts dd {
		margin: 0;
		color: rgb(241, 245, 249);
		font-size: 0.88rem;
		font-weight: 650;
		text-align: right;
	}

	.status-rollup {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.85rem;
		margin-top: clamp(1.5rem, 4vw, 3rem);
	}

	.status-rollup article {
		min-height: 7rem;
		border: 1px solid rgb(51 65 85 / 0.68);
		border-radius: 0.75rem;
		background: rgb(2 6 23 / 0.5);
		padding: 1rem;
	}

	.status-rollup strong {
		display: block;
		color: rgb(248, 250, 252);
		font-size: clamp(2rem, 5vw, 3.2rem);
		line-height: 1;
	}

	.status-rollup span {
		display: block;
		margin-top: 0.7rem;
		color: rgb(148, 163, 184);
		font-size: 0.74rem;
		font-weight: 720;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.status-notice {
		margin-top: clamp(1.5rem, 4vw, 3rem);
		border: 1px solid rgb(251 191 36 / 0.32);
		border-radius: 0.75rem;
		background: rgb(120 53 15 / 0.16);
		padding: clamp(1rem, 3vw, 1.35rem);
	}

	.status-notice h2 {
		color: rgb(120, 53, 15);
		font-size: 1rem;
		font-weight: 760;
	}

	.status-notice p {
		margin: 0.45rem 0 0;
		color: rgb(146, 64, 14);
		font-size: 0.9rem;
		line-height: 1.6;
	}

	.status-services {
		margin-top: clamp(2.25rem, 5vw, 4rem);
	}

	.status-services__head {
		display: flex;
		align-items: end;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 1rem;
	}

	.status-services h2 {
		color: var(--color-ink-50, #f0f4f8);
		font-size: clamp(1.4rem, 3vw, 2rem);
		font-weight: 740;
	}

	.status-services__head p {
		max-width: 34rem;
		margin: 0;
		color: var(--color-ink-300, rgba(240, 244, 248, 0.7));
		font-size: 0.9rem;
		line-height: 1.55;
	}

	.status-grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.85rem;
	}

	.status-card {
		min-height: 12rem;
		border: 1px solid rgb(51 65 85 / 0.68);
		border-radius: 0.75rem;
		background: rgb(15 23 42 / 0.62);
		padding: 1rem;
	}

	.status-card__head {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 0.8rem;
	}

	.status-card h3 {
		color: rgb(248, 250, 252);
		font-size: 0.98rem;
		font-weight: 720;
	}

	.status-card p {
		margin: 1rem 0 0;
		color: rgb(203, 213, 225);
		font-size: 0.88rem;
		line-height: 1.65;
	}

	.status-pill {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 1.9rem;
		padding: 0.3rem 0.7rem;
		border-radius: 999px;
		font-size: 0.77rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		white-space: nowrap;
	}

	.status-pill--success {
		border: 1px solid rgb(52 211 153 / 0.26);
		background: rgb(16 185 129 / 0.12);
		color: rgb(167 243 208);
	}

	.status-pill--warning {
		border: 1px solid rgb(251 191 36 / 0.28);
		background: rgb(217 119 6 / 0.14);
		color: rgb(253 230 138);
	}

	.status-pill--danger {
		border: 1px solid rgb(248 113 113 / 0.28);
		background: rgb(220 38 38 / 0.14);
		color: rgb(254 202 202);
	}

	.status-pill--neutral {
		border: 1px solid rgb(148 163 184 / 0.22);
		background: rgb(148 163 184 / 0.12);
		color: rgb(203 213 225);
	}

	@media (max-width: 920px) {
		.status-hero {
			grid-template-columns: 1fr;
			align-items: start;
		}

		.status-services__head {
			display: block;
		}

		.status-services__head p {
			margin-top: 0.5rem;
		}

		.status-grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.status-page {
			width: min(100% - 1.25rem, 1120px);
			padding-top: 2.5rem;
		}

		.status-rollup,
		.status-grid {
			grid-template-columns: 1fr;
		}

		.status-card__head {
			flex-direction: column;
			align-items: flex-start;
		}

		.status-facts div {
			display: grid;
			gap: 0.25rem;
		}

		.status-facts dd {
			text-align: left;
		}
	}
</style>
