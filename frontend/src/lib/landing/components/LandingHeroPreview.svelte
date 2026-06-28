<script lang="ts">
	export let heroCardState: 'pending' | 'approved' | 'denied' = 'pending';
	export let heroCardVisible = true;

	$: stripeClass =
		heroCardState === 'approved'
			? 'hero-card__stripe--jade'
			: heroCardState === 'denied'
				? 'hero-card__stripe--ruby'
				: 'hero-card__stripe--amber';
</script>

<div class="hero__preview" aria-label="Live approval queue preview showing governance in action">
	<div class="hero__preview-label" aria-hidden="true">
		<span class="live-dot" aria-hidden="true"></span>
		APPROVAL QUEUE · LIVE
	</div>
	{#if heroCardVisible}
		<div
			class="hero-card"
			class:hero-card--approved={heroCardState === 'approved'}
			class:hero-card--denied={heroCardState === 'denied'}
		>
			<div class="hero-card__stripe {stripeClass}"></div>
			<div class="hero-card__body">
				<div class="hero-card__top">
					<span class="tag tag--cloud">CLOUD</span>
					<span class="hero-card__name">AWS r6i.4xlarge × 8</span>
					{#if heroCardState === 'pending'}
						<span class="tag tag--critical">CRITICAL</span>
					{:else if heroCardState === 'approved'}
						<span class="tag tag--approved">✓ APPROVED</span>
					{:else}
						<span class="tag tag--denied">✕ DENIED</span>
					{/if}
				</div>
				<div class="hero-card__policies">
					<span class="policy-tag policy-tag--warn">⚠ Budget</span>
					<span class="policy-tag policy-tag--pass">✓ Region</span>
					<span class="policy-tag policy-tag--pass">✓ Instance</span>
				</div>
				<div class="hero-card__meta">James Obi · ML Platform · 4h ago</div>
			</div>
			<div class="hero-card__cost">
				<div class="hero-card__cost-val">$4,200/mo</div>
				<div class="hero-card__cost-label">COST IMPACT</div>
				{#if heroCardState === 'pending'}
					<div class="hero-card__actions">
						<button type="button" class="btn-approve" aria-label="Approve this request">✓</button>
						<button type="button" class="btn-deny" aria-label="Deny this request">✕</button>
					</div>
				{:else if heroCardState === 'approved'}
					<div class="hero-card__decision hero-card__decision--approved">Approved by Sarah</div>
				{:else}
					<div class="hero-card__decision hero-card__decision--denied">Denied · over budget</div>
				{/if}
			</div>
		</div>
	{/if}
	<div class="hero-card hero-card--ghost">
		<div class="hero-card__stripe hero-card__stripe--violet"></div>
		<div class="hero-card__body">
			<div class="hero-card__top">
				<span class="tag tag--software">SOFTWARE</span>
				<span class="hero-card__name">Figma Pro — 15 seats</span>
			</div>
			<div class="hero-card__meta">Sarah Chen · Product Design · 6h ago</div>
		</div>
		<div class="hero-card__cost"><div class="hero-card__cost-val">$675/mo</div></div>
	</div>
	<div class="hero__health">
		<div class="hero__health-ring" aria-hidden="true">
			<svg width="52" height="52" viewBox="0 0 52 52">
				<circle cx="26" cy="26" r="20" fill="none" stroke="var(--s3)" stroke-width="6" />
				<circle
					cx="26"
					cy="26"
					r="20"
					fill="none"
					stroke="var(--jade)"
					stroke-width="6"
					stroke-linecap="round"
					stroke-dasharray="113 126"
					transform="rotate(-90 26 26)"
				/>
			</svg>
			<span class="hero__health-score">94</span>
		</div>
		<div>
			<div class="hero__health-label">GOVERNANCE SCORE</div>
			<div class="hero__health-sub">↑ 4% this month</div>
		</div>
	</div>
</div>

<style>
	.hero__preview {
		display: flex;
		flex-direction: column;
		gap: 12px;
		animation: fadeUp 0.9s cubic-bezier(0.22, 1, 0.36, 1) 1s both;
	}
	.hero__preview-label {
		font-family: var(--font-mono);
		font-size: 10px;
		color: var(--sub);
		letter-spacing: 0.1em;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.hero-card {
		display: flex;
		align-items: center;
		gap: 12px;
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 12px;
		padding: 13px 14px;
		animation: heroCardIn 0.3s cubic-bezier(0.22, 1, 0.36, 1) both;
		transition: border-color 0.3s;
	}
	.hero-card--ghost {
		opacity: 0.45;
		transform: scale(0.97);
		margin-top: -4px;
	}
	.hero-card--approved {
		border-color: rgba(0, 207, 124, 0.3);
		background: rgba(0, 207, 124, 0.05);
	}
	.hero-card--denied {
		border-color: rgba(255, 58, 92, 0.25);
		background: rgba(255, 58, 92, 0.04);
	}
	.hero-card__stripe {
		width: 3px;
		height: 36px;
		border-radius: 2px;
		flex-shrink: 0;
	}
	.hero-card__stripe--amber {
		background: var(--amber);
	}
	.hero-card__stripe--jade {
		background: var(--jade);
	}
	.hero-card__stripe--ruby {
		background: var(--ruby);
	}
	.hero-card__stripe--violet {
		background: var(--violet);
	}
	.hero-card__body {
		flex: 1;
		min-width: 0;
	}
	.hero-card__top,
	.hero-card__policies,
	.hero-card__actions {
		display: flex;
		align-items: center;
		gap: 7px;
		flex-wrap: wrap;
	}
	.hero-card__name {
		font-size: 12px;
		font-weight: 600;
		color: var(--white);
	}
	.hero-card__policies {
		gap: 5px;
		margin: 5px 0 4px;
	}
	.hero-card__meta,
	.hero-card__decision {
		font-size: 10px;
		color: var(--sub);
	}
	.hero-card__cost {
		text-align: right;
		flex-shrink: 0;
	}
	.hero-card__cost-val {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 14px;
		color: var(--amber);
	}
	.hero-card__cost-label {
		font-size: 9px;
		color: var(--sub);
		font-family: var(--font-mono);
		letter-spacing: 0.07em;
		text-transform: uppercase;
		margin-top: 2px;
	}
	.hero-card__actions {
		justify-content: flex-end;
		margin-top: 6px;
	}
	.hero-card__decision {
		font-family: var(--font-mono);
		margin-top: 5px;
	}
	.hero-card__decision--approved {
		color: var(--jade);
	}
	.hero-card__decision--denied {
		color: var(--ruby);
	}
	.btn-approve,
	.btn-deny {
		width: 24px;
		height: 24px;
		border-radius: 6px;
		border: 1px solid;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 11px;
		cursor: pointer;
		background: none;
	}
	.btn-approve {
		color: var(--jade);
		border-color: rgba(0, 207, 124, 0.3);
		background: rgba(0, 207, 124, 0.1);
	}
	.btn-deny {
		color: var(--ruby);
		border-color: rgba(255, 58, 92, 0.3);
		background: rgba(255, 58, 92, 0.1);
	}
	.hero__health {
		display: flex;
		align-items: center;
		gap: 12px;
		padding: 10px 14px;
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 10px;
	}
	.hero__health-ring {
		position: relative;
		width: 52px;
		height: 52px;
		flex-shrink: 0;
	}
	.hero__health-score {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 13px;
		color: var(--jade);
	}
	.hero__health-label {
		font-family: var(--font-mono);
		font-size: 9px;
		color: var(--sub);
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}
	.hero__health-sub {
		font-size: 11px;
		color: var(--jade);
		margin-top: 2px;
	}
	@keyframes fadeUp {
		from {
			opacity: 0;
			transform: translateY(18px);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
	@keyframes heroCardIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	@media (max-width: 900px) {
		.hero__preview {
			display: none;
		}
	}
</style>
