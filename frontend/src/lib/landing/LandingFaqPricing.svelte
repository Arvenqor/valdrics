<script lang="ts">
	import { DEFAULT_PRICING_PLANS, type PricingPlan } from '$lib/pricing/publicPlans';
	import { FAQS } from './landingContent';
	import { reveal } from './landingActions';

	export let openFaq: number | null = null;
	export let toggleFaq: (i: number) => void;
	export let pricingPlanHref: (plan: PricingPlan) => string;

	const landingPricingPlans = DEFAULT_PRICING_PLANS;

	function formatMonthlyPrice(plan: PricingPlan): string {
		return plan.price_monthly === 0 ? '$0' : `$${plan.price_monthly}`;
	}
</script>

<section class="faq" id="faq" aria-label="Frequently asked questions">
	<div class="container">
		<div use:reveal>
			<span class="section-label">FAQ</span>
			<h2 class="section-title">Governance questions,<br />answered honestly.</h2>
		</div>
		<div class="faq__grid" use:reveal={{ delay: 80 }}>
			{#each FAQS as faq, i}
				<div
					class="faq__item"
					class:faq__item--open={openFaq === i}
					itemscope
					itemtype="https://schema.org/Question"
				>
					<button
						type="button"
						class="faq__q"
						on:click={() => toggleFaq(i)}
						aria-expanded={openFaq === i}
					>
						<span class="faq__q-text" itemprop="name">{faq.q}</span>
						<svg
							class="faq__chevron"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							aria-hidden="true"
						>
							<polyline points="6 9 12 15 18 9" />
						</svg>
					</button>
					{#if openFaq === i}
						<div
							class="faq__a"
							itemprop="acceptedAnswer"
							itemscope
							itemtype="https://schema.org/Answer"
						>
							<p itemprop="text">{faq.a}</p>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	</div>
</section>

<section class="pricing" id="pricing">
	<div class="container">
		<div class="section-center" use:reveal>
			<span class="section-label">Pricing</span>
			<h2 class="section-title section-title--center">
				Start free, then expand<br />when governance depth grows.
			</h2>
			<p class="section-sub section-sub--center">
				Use the permanent free tier first. Paid plans follow the current published Free, Starter,
				Growth, and Pro pricing contract.
			</p>
		</div>
		<div class="pricing__grid">
			{#each landingPricingPlans as plan, i}
				<article class="pcard" class:pcard--popular={plan.popular} use:reveal={{ delay: i * 80 }}>
					{#if plan.popular}
						<div class="pcard__badge">RECOMMENDED</div>
					{/if}
					<div class="pcard__tier" class:pcard__tier--jade={plan.popular}>{plan.name}</div>
					<div class="pcard__price">
						<span class="pcard__num">{formatMonthlyPrice(plan)}</span>
						<span class="pcard__per">{plan.period}</span>
					</div>
					<p class="pcard__desc">{plan.story?.summary ?? plan.description}</p>
					<a
						href={pricingPlanHref(plan)}
						class="btn btn--full"
						class:btn--jade={plan.popular}
						class:btn--ghost={!plan.popular}
					>
						{plan.cta}
					</a>
					<div class="pcard__divider"></div>
					<ul class="pcard__features">
						{#each plan.features as f}
							<li class="pcard__feature">
								<span class="pcard__check" aria-hidden="true"> ✓ </span>
								{f}
							</li>
						{/each}
					</ul>
				</article>
			{/each}
		</div>
		<p class="pricing__note">
			Annual billing and localized checkout details live on the full pricing page. Enterprise review
			is reserved for private deployment, SCIM, procurement, or custom control requirements.
		</p>
	</div>
</section>

<style>
	.faq {
		background: var(--base);
	}
	.faq__grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 10px;
		margin-top: 48px;
	}
	.faq__item {
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 12px;
		overflow: hidden;
		transition: border-color 0.2s;
	}
	.faq__item:hover,
	.faq__item--open {
		border-color: var(--bdr-hi);
	}
	.faq__item--open {
		border-color: rgba(0, 207, 124, 0.3);
	}
	.faq__q {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 14px;
		padding: 17px 19px;
		background: none;
		border: none;
		cursor: pointer;
		text-align: left;
	}
	.faq__q-text {
		font-size: 14px;
		font-weight: 600;
		color: var(--white);
		line-height: 1.5;
	}
	.faq__chevron {
		width: 18px;
		height: 18px;
		flex-shrink: 0;
		color: var(--sub);
		transition:
			transform 0.25s,
			color 0.2s;
	}
	.faq__item--open .faq__chevron {
		transform: rotate(180deg);
		color: var(--jade);
	}
	.faq__a {
		padding: 14px 19px 16px;
		border-top: 1px solid var(--bdr);
		animation: faqAnswerIn 0.22s cubic-bezier(0.22, 1, 0.36, 1) both;
	}
	.faq__a p {
		font-size: 13px;
		color: var(--sub);
		line-height: 1.75;
	}
	.pricing {
		background: var(--void);
	}
	.pricing__grid {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 18px;
		margin-top: 56px;
	}
	.pcard {
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 18px;
		padding: 32px;
		position: relative;
		transition:
			border-color 0.2s,
			transform 0.2s;
	}
	.pcard:hover {
		border-color: var(--bdr-hi);
		transform: translateY(-2px);
	}
	.pcard--popular {
		border-color: rgba(0, 207, 124, 0.35);
		background: var(--s2);
		box-shadow: 0 0 60px rgba(0, 207, 124, 0.07);
	}
	.pcard__badge {
		position: absolute;
		top: -13px;
		left: 50%;
		transform: translateX(-50%);
		padding: 5px 16px;
		border-radius: 100px;
		background: var(--jade);
		color: #030912;
		font-family: var(--font-display);
		font-size: 11px;
		font-weight: 700;
		letter-spacing: 0.06em;
		white-space: nowrap;
	}
	.pcard__tier {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.1em;
		color: var(--sub);
		margin-bottom: 13px;
		text-transform: uppercase;
	}
	.pcard__tier--jade {
		color: var(--jade);
	}
	.pcard__price {
		display: flex;
		align-items: baseline;
		gap: 4px;
		margin-bottom: 7px;
	}
	.pcard__num {
		font-family: var(--font-display);
		font-weight: 800;
		font-size: 38px;
		color: var(--white);
		line-height: 1;
	}
	.pcard__per,
	.pcard__desc,
	.pcard__feature {
		color: var(--sub);
	}
	.pcard__desc {
		font-size: 13px;
		margin-bottom: 22px;
		line-height: 1.6;
	}
	.pcard__divider {
		height: 1px;
		background: var(--bdr);
		margin: 20px 0;
	}
	.pcard__features {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 10px;
		margin-bottom: 24px;
	}
	.pcard__feature {
		display: flex;
		align-items: center;
		gap: 9px;
		font-size: 13px;
	}
	.pcard__check {
		font-size: 14px;
		color: var(--jade);
		flex-shrink: 0;
	}
	.pricing__note {
		max-width: 760px;
		margin: 28px auto 0;
		color: var(--sub);
		font-size: 13px;
		line-height: 1.7;
		text-align: center;
	}
	@keyframes faqAnswerIn {
		from {
			opacity: 0;
			transform: translateY(-6px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
	@media (max-width: 900px) {
		.faq__grid,
		.pricing__grid {
			grid-template-columns: 1fr;
		}
	}
	@media (min-width: 901px) and (max-width: 1180px) {
		.pricing__grid {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
