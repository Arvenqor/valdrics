<script lang="ts">
	import { COMPARISON_ROWS, GOVERNANCE_SCENARIOS } from '../content/page';
	import { reveal } from '../telemetry/actions';
</script>

<section class="testimonials" id="customers">
	<div class="container">
		<div use:reveal>
			<span class="section-label">Governance scenarios</span>
			<h2 class="section-title">Stop asking<br />"who approved this?"</h2>
		</div>
		<div class="testimonials__grid">
			{#each GOVERNANCE_SCENARIOS as t, i}
				<article class="tcard" use:reveal={{ delay: i * 80 }}>
					<div class="tcard__saving">{t.saving}</div>
					<blockquote class="tcard__quote">{t.quote}</blockquote>
					<footer class="tcard__author">
						<div class="tcard__avatar {t.avatarClass}">{t.initials}</div>
						<div>
							<div class="tcard__name">{t.name}</div>
							<div class="tcard__role">{t.role}</div>
							<div class="tcard__co">{t.co}</div>
						</div>
					</footer>
				</article>
			{/each}
		</div>
	</div>
</section>

<section class="comparison">
	<div class="container">
		<div use:reveal>
			<span class="section-label">Why Valdrics</span>
			<h2 class="section-title">
				The only platform that governs<br />cloud <em>and</em> software together.
			</h2>
		</div>
		<!-- svelte-ignore a11y_no_noninteractive_tabindex: axe requires keyboard focus for horizontal table scrolling. -->
		<div
			class="comparison__wrap"
			role="region"
			tabindex="0"
			aria-label="Scrollable feature comparison table"
			use:reveal={{ delay: 100 }}
		>
			<table class="comp-table" aria-label="Feature comparison">
				<thead>
					<tr>
						<th scope="col">Capability</th>
						<th scope="col" class="th--v">VALDRICS</th>
						<th scope="col">Torii / Zylo</th>
						<th scope="col">Cloudability</th>
						<th scope="col">AWS Cost Explorer</th>
					</tr>
				</thead>
				<tbody>
					{#each COMPARISON_ROWS as row}
						<tr>
							<td class="td--feature">{row[0]}</td>
							{#each row.slice(1) as cell, ci}
								<td class:td--v={ci === 0}>
									{#if cell === '✕'}
										<span class="c-cross" aria-label="Not available">✕</span>
									{:else if cell.startsWith('✓')}
										<span class="c-check" aria-label="Available">{cell}</span>
									{:else if cell.startsWith('Partial')}
										<span class="c-partial">{cell}</span>
									{:else}
										{cell}
									{/if}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</div>
</section>

<style>
	.testimonials {
		background: var(--base);
	}
	.testimonials__grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px;
		margin-top: 52px;
	}
	.tcard {
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 16px;
		padding: 28px;
		display: flex;
		flex-direction: column;
		gap: 18px;
		transition: border-color 0.2s;
		position: relative;
		overflow: hidden;
	}
	.tcard::before {
		content: '\201C';
		position: absolute;
		top: 12px;
		right: 18px;
		font-family: var(--font-display);
		font-size: 72px;
		line-height: 1;
		color: rgba(0, 207, 124, 0.06);
		pointer-events: none;
	}
	.tcard:hover {
		border-color: var(--bdr-hi);
	}
	.tcard__saving {
		display: inline-flex;
		align-items: center;
		padding: 4px 10px;
		border-radius: 6px;
		background: rgba(0, 207, 124, 0.1);
		border: 1px solid rgba(0, 207, 124, 0.2);
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--jade);
		font-weight: 600;
		align-self: flex-start;
	}
	.tcard__quote {
		font-size: 14px;
		line-height: 1.75;
		color: var(--text);
		flex: 1;
		font-style: italic;
	}
	.tcard__author {
		display: flex;
		align-items: center;
		gap: 12px;
		padding-top: 16px;
		border-top: 1px solid var(--bdr);
	}
	.tcard__avatar {
		width: 38px;
		height: 38px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 13px;
		color: #fff;
		flex-shrink: 0;
	}
	.tcard__avatar--saas {
		background: linear-gradient(135deg, #00cf7c, #00c2ff);
	}
	.tcard__avatar--cloud {
		background: linear-gradient(135deg, #9270ff, #f5a623);
	}
	.tcard__avatar--reporting {
		background: linear-gradient(135deg, #f5a623, #ff3a5c);
	}
	.tcard__name {
		font-size: 13px;
		font-weight: 600;
		color: var(--white);
	}
	.tcard__role {
		font-size: 12px;
		color: var(--sub);
	}
	.tcard__co {
		font-size: 11px;
		color: var(--jade);
		font-family: var(--font-mono);
		margin-top: 2px;
	}
	.comparison {
		background: var(--void);
	}
	.comparison__wrap {
		overflow-x: auto;
		margin-top: 48px;
	}
	.comp-table {
		width: 100%;
		border-collapse: separate;
		border-spacing: 0;
		border: 1px solid var(--bdr);
		border-radius: 14px;
		overflow: hidden;
		font-size: 13px;
	}
	.comp-table th {
		padding: 13px 16px;
		background: var(--s2);
		font-family: var(--font-display);
		font-weight: 600;
		font-size: 13px;
		color: var(--sub);
		border-bottom: 1px solid var(--bdr);
		text-align: left;
	}
	.th--v {
		color: var(--jade);
		background: rgba(0, 207, 124, 0.05);
	}
	.comp-table td {
		padding: 12px 16px;
		border-bottom: 1px solid var(--bdr);
		color: var(--sub);
		vertical-align: middle;
	}
	.comp-table tr:last-child td {
		border-bottom: none;
	}
	.comp-table tr:hover td {
		background: rgba(255, 255, 255, 0.012);
	}
	.td--feature {
		color: var(--text);
		font-weight: 500;
	}
	.td--v {
		background: rgba(0, 207, 124, 0.04);
		color: var(--white);
		font-weight: 500;
	}
	.c-check {
		color: var(--jade);
	}
	.c-cross {
		color: var(--muted);
	}
	.c-partial {
		color: var(--amber);
		font-size: 12px;
		font-family: var(--font-mono);
	}
	@media (max-width: 900px) {
		.testimonials__grid {
			grid-template-columns: 1fr;
		}
	}
	@media (max-width: 600px) {
		.comp-table {
			font-size: 12px;
		}
	}
</style>
