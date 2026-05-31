<script lang="ts">
	import { onMount } from 'svelte';
	import { base } from '$app/paths';
	import { page } from '$app/stores';
	import LandingCtaFooter from '$lib/landing/LandingCtaFooter.svelte';
	import LandingFaqPricing from '$lib/landing/LandingFaqPricing.svelte';
	import LandingFeatures from '$lib/landing/LandingFeatures.svelte';
	import LandingHead from '$lib/landing/LandingHead.svelte';
	import LandingHero from '$lib/landing/LandingHero.svelte';
	import LandingHowCounterIntegrations from '$lib/landing/LandingHowCounterIntegrations.svelte';
	import LandingNav from '$lib/landing/LandingNav.svelte';
	import LandingProblem from '$lib/landing/LandingProblem.svelte';
	import LandingProofComparison from '$lib/landing/LandingProofComparison.svelte';
	import type { PricingPlan } from '$lib/landing/landingContent';
	import { buildPublicAuthHref } from '$lib/public/publicAppOrigin';
	import { buildPublicSalesHref, buildPublicSignupHref } from '$lib/public/publicBuyingMotion';

	let scrolled = false;
	let mobileMenuOpen = false;
	let openFaq: number | null = null;
	let decisionsToday = 1847;
	let shadowFlagged = 312;
	let violationsCaught = 2941;
	let heroCardState: 'pending' | 'approved' | 'denied' = 'pending';
	let heroCardVisible = true;

	function appPath(path: string): string {
		const normalizedBase = base === '/' ? '' : base;
		const normalizedPath = path.startsWith('/') ? path : `/${path}`;
		return `${normalizedBase}${normalizedPath}`;
	}

	function loginHref(): string {
		return buildPublicAuthHref(`${appPath('/auth/login')}?mode=login`, $page.url);
	}

	function signupHref(source: string, extraParams: Record<string, string> = {}): string {
		return buildPublicSignupHref(base, $page.url, {
			entry: 'landing_gate',
			source,
			intent: 'signup',
			extraParams
		});
	}

	function salesHref(source: string, intent = 'demo'): string {
		return buildPublicSalesHref(base, $page.url, {
			entry: 'landing_gate',
			source,
			intent
		});
	}

	function pricingPlanHref(plan: PricingPlan): string {
		if (plan.tier === 'Enterprise') {
			return salesHref('landing_pricing_enterprise', 'enterprise_briefing');
		}
		const planId = plan.tier === 'Team' ? 'growth' : 'starter';
		return signupHref(`landing_pricing_${planId}`, { plan: planId });
	}

	function footerHref(label: string): string {
		switch (label) {
			case 'Features':
				return '#features';
			case 'Pricing':
				return '#pricing';
			case 'Integrations':
				return '#integrations';
			case 'Insights':
				return appPath('/insights');
			case 'Documentation':
			case 'Governance Guides':
			case 'Glossary':
				return appPath('/docs');
			case 'Case Studies':
				return appPath('/proof');
			case 'About':
			case 'Careers':
			case 'Press':
				return appPath('/about');
			case 'Contact':
			case 'Roadmap':
				return salesHref(`landing_footer_${label.toLowerCase()}`, label.toLowerCase());
			case 'Security':
				return appPath('/docs/technical-validation');
			case 'Privacy Policy':
			case 'DPA':
			case 'Cookie Policy':
				return appPath('/privacy');
			case 'Terms of Service':
				return appPath('/terms');
			case 'SLA':
				return appPath('/status');
			case 'Changelog':
			default:
				return appPath('/resources');
		}
	}

	function toggleFaq(i: number) {
		openFaq = openFaq === i ? null : i;
	}

	function fmt(n: number): string {
		return n.toLocaleString();
	}

	onMount(() => {
		const handleScroll = () => {
			scrolled = window.scrollY > 48;
		};
		handleScroll();
		window.addEventListener('scroll', handleScroll, { passive: true });

		const counterInterval = setInterval(() => {
			decisionsToday += Math.floor(Math.random() * 3);
			shadowFlagged += Math.random() > 0.8 ? 1 : 0;
			violationsCaught += Math.floor(Math.random() * 2);
		}, 3200);

		let cardCycleTimeout: ReturnType<typeof setTimeout> | undefined;
		const cardCycle = setInterval(() => {
			heroCardVisible = false;
			cardCycleTimeout = setTimeout(() => {
				heroCardState =
					heroCardState === 'pending' ? (Math.random() > 0.4 ? 'approved' : 'denied') : 'pending';
				heroCardVisible = true;
			}, 400);
		}, 3500);

		return () => {
			window.removeEventListener('scroll', handleScroll);
			clearInterval(counterInterval);
			clearInterval(cardCycle);
			if (cardCycleTimeout) clearTimeout(cardCycleTimeout);
		};
	});
</script>

<LandingHead />

<div class="landing-page">
	<LandingNav {appPath} {loginHref} {signupHref} {scrolled} bind:mobileMenuOpen />
	<LandingHero {heroCardState} {heroCardVisible} {signupHref} {salesHref} />
	<LandingProblem />
	<LandingFeatures />
	<LandingHowCounterIntegrations {decisionsToday} {shadowFlagged} {violationsCaught} {fmt} />
	<LandingProofComparison />
	<LandingFaqPricing {openFaq} {toggleFaq} {pricingPlanHref} />
	<LandingCtaFooter {signupHref} {salesHref} {appPath} {footerHref} />
</div>

<style>
	:global(.landing-page) {
		min-height: 100vh;
		overflow-x: hidden;
		background: var(--base);
		color: var(--text);
	}
	:global(.v-hidden) {
		opacity: 0;
		transform: translateY(18px);
		transition:
			opacity 0.7s cubic-bezier(0.22, 1, 0.36, 1),
			transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);
	}
	:global(.v-visible) {
		opacity: 1;
		transform: none;
	}
	:global(.landing-page .container) {
		max-width: 1100px;
		margin: 0 auto;
		padding: 0 40px;
	}
	:global(.landing-page section) {
		padding: 96px 40px;
	}
	:global(.landing-page .section-label) {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.13em;
		color: var(--jade);
		text-transform: uppercase;
		display: block;
		margin-bottom: 12px;
	}
	:global(.landing-page .section-title) {
		font-family: var(--font-display);
		font-weight: 800;
		font-size: clamp(28px, 4vw, 48px);
		color: var(--white);
		line-height: 1.07;
		letter-spacing: -0.02em;
	}
	:global(.landing-page .section-sub) {
		font-size: 16px;
		color: var(--sub);
		max-width: 520px;
		margin-top: 14px;
		line-height: 1.7;
	}
	:global(.landing-page .section-center) {
		text-align: center;
	}
	:global(.landing-page .section-title--center) {
		margin: 0 auto;
	}
	:global(.landing-page .section-sub--center) {
		margin: 14px auto 0;
		text-align: center;
	}
	:global(.landing-page .btn) {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 10px 22px;
		border-radius: 10px;
		font-size: 14px;
		font-family: var(--font-body);
		font-weight: 600;
		cursor: pointer;
		border: 1px solid transparent;
		text-decoration: none;
		transition: all 0.18s ease;
	}
	:global(.landing-page .btn--sm) {
		padding: 8px 16px;
		font-size: 13px;
		border-radius: 9px;
	}
	:global(.landing-page .btn--lg) {
		padding: 14px 28px;
		font-size: 15px;
		border-radius: 12px;
	}
	:global(.landing-page .btn--full) {
		width: 100%;
		justify-content: center;
	}
	:global(.landing-page .btn--jade) {
		background: var(--jade);
		color: #030912;
		box-shadow: 0 0 20px rgba(0, 207, 124, 0.25);
		border-color: var(--jade);
	}
	:global(.landing-page .btn--jade:hover) {
		background: #11e888;
		box-shadow: 0 0 32px rgba(0, 207, 124, 0.4);
		transform: translateY(-1px);
	}
	:global(.landing-page .btn--ghost) {
		background: transparent;
		color: var(--sub);
		border-color: var(--bdr);
	}
	:global(.landing-page .btn--ghost:hover) {
		color: var(--text);
		border-color: var(--bdr-hi);
		background: var(--s1);
	}
	:global(.landing-page .nav__logo) {
		display: flex;
		align-items: center;
		gap: 9px;
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 15px;
		color: var(--white);
		letter-spacing: 0.08em;
		text-decoration: none;
	}
	:global(.landing-page .nav__mark) {
		width: 30px;
		height: 30px;
		border-radius: 8px;
		background: rgba(0, 207, 124, 0.1);
		border: 1px solid rgba(0, 207, 124, 0.25);
		display: flex;
		align-items: center;
		justify-content: center;
	}
	:global(.landing-page .live-dot) {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--jade);
		animation: pulseDot 1.5s ease-in-out infinite;
		display: inline-block;
	}
	:global(.landing-page .live-dot--jade) {
		background: var(--jade);
	}
	:global(.landing-page .tag) {
		display: inline-flex;
		align-items: center;
		padding: 2px 6px;
		border-radius: 4px;
		font-family: var(--font-mono);
		font-size: 9px;
		font-weight: 700;
		letter-spacing: 0.06em;
	}
	:global(.landing-page .tag--cloud) {
		background: rgba(0, 194, 255, 0.1);
		color: var(--ion);
	}
	:global(.landing-page .tag--software) {
		background: rgba(146, 112, 255, 0.1);
		color: var(--violet);
	}
	:global(.landing-page .tag--critical),
	:global(.landing-page .tag--denied) {
		background: rgba(255, 58, 92, 0.1);
		color: var(--ruby);
	}
	:global(.landing-page .tag--approved) {
		background: rgba(0, 207, 124, 0.1);
		color: var(--jade);
	}
	:global(.landing-page .chip) {
		display: flex;
		align-items: center;
		gap: 5px;
		padding: 5px 11px;
		border-radius: 100px;
		background: var(--s1);
		border: 1px solid var(--bdr);
		font-size: 12px;
		color: var(--sub);
	}
	:global(.landing-page .chip strong) {
		color: var(--white);
		font-family: var(--font-display);
		font-size: 13px;
	}
	:global(.landing-page .policy-tag) {
		display: inline-flex;
		align-items: center;
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 9px;
		font-family: var(--font-mono);
		font-weight: 600;
	}
	:global(.landing-page .policy-tag--warn) {
		background: rgba(245, 166, 35, 0.1);
		color: var(--amber);
	}
	:global(.landing-page .policy-tag--pass) {
		background: rgba(0, 207, 124, 0.1);
		color: var(--jade);
	}
	@keyframes pulseDot {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.3;
			transform: scale(0.6);
		}
	}
	@media (max-width: 900px) {
		:global(.landing-page section) {
			padding: 72px 24px;
		}
		:global(.landing-page .container) {
			padding: 0 24px;
		}
	}
</style>
