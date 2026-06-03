<script lang="ts">
	import { base } from '$app/paths';
	import { DEFAULT_PRICING_PLANS, type PricingPlan } from '$lib/pricing/publicPlans';

	function requirePlan(planId: string): PricingPlan {
		const plan = DEFAULT_PRICING_PLANS.find((item) => item.id === planId);
		if (!plan) {
			throw new Error(`Missing landing pricing preview plan: ${planId}`);
		}
		return plan;
	}

	const landingPlanPreview = ['free', 'growth', 'pro'].map((planId) => {
		const plan = requirePlan(planId);
		return {
			id: plan.id,
			name: plan.name,
			price: plan.price_monthly === 0 ? '$0' : `$${plan.price_monthly}`,
			summary: plan.story?.bestFor ?? plan.description,
			cta: plan.id === 'free' ? plan.cta : `See ${plan.name} on Pricing`,
			href: plan.id === 'free' ? null : `${base}/pricing`
		};
	});

	let {
		freeTierCtaHref,
		trustEnterpriseHref,
		onTrackCta
	}: {
		freeTierCtaHref: string;
		trustEnterpriseHref: string;
		onTrackCta: (action: string, section: string, value: string) => void;
	} = $props();
</script>

<section id="plans" class="landing-public-section" data-landing-section="plans">
	<div class="container mx-auto px-6 py-12">
		<div class="landing-public-section-head">
			<p class="landing-public-eyebrow">Pricing</p>
			<h2>Pricing that matches rollout stage</h2>
			<p>
				Start small, prove the workflow, and only move up when the team needs more governance depth.
			</p>
		</div>
		<div class="landing-public-plan-grid">
			{#each landingPlanPreview as plan (plan.name)}
				<article class="landing-public-surface landing-public-plan-card">
					<p class="landing-public-proof-label">{plan.name}</p>
					<div class="landing-public-plan-price">{plan.price}</div>
					<p>{plan.summary}</p>
					{#if plan.href}
						<a
							href={plan.href}
							class="btn btn-secondary"
							onclick={() => onTrackCta('cta_click', 'plans', plan.id)}
						>
							{plan.cta}
						</a>
					{:else}
						<a
							href={freeTierCtaHref}
							class="btn btn-primary"
							onclick={() => onTrackCta('cta_click', 'plans', 'free')}
						>
							{plan.cta}
						</a>
					{/if}
				</article>
			{/each}
		</div>
		<div class="landing-public-band landing-public-band--compact">
			<div>
				<p class="landing-public-eyebrow">Full pricing</p>
				<h3>Compare the full plan details before you commit</h3>
				<p>
					Use the pricing page for the full plan breakdown. Use enterprise review only when
					security, procurement, or deployment requirements need a separate path.
				</p>
			</div>
			<div class="landing-public-band-actions">
				<a
					href={`${base}/pricing`}
					class="btn btn-secondary"
					onclick={() => onTrackCta('cta_click', 'plans', 'view_pricing')}
				>
					See Detailed Pricing
				</a>
				<a
					href={trustEnterpriseHref}
					class="btn btn-secondary"
					onclick={() => onTrackCta('cta_click', 'plans', 'enterprise_review')}
				>
					Enterprise Review
				</a>
			</div>
		</div>
	</div>
</section>
