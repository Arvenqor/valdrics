<script lang="ts">
	import OnboardingPage from '../../onboarding/+page.svelte';
	import type { PageData as OnboardingPageData } from '../../onboarding/$types';

	const data = {
		user: {
			id: 'user-onboarding-capture',
			email: 'emi@company.com',
			tenant_id: 'tenant-onboarding-capture'
		},
		session: { access_token: 'capture-token' },
		subscription: { tier: 'pro', status: 'active' },
		profile: {
			persona: 'engineering',
			role: 'admin',
			platform_operator: false
		}
	} as unknown as OnboardingPageData;
</script>

<svelte:head>
	<title>Onboarding Capture</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="onboarding-capture-shell">
	<div class="onboarding-capture" data-onboarding-capture>
		<OnboardingPage {data} />
	</div>
</div>

<style>
	.onboarding-capture-shell {
		min-height: 100vh;
		padding: 1rem;
		background: #030912;
	}

	.onboarding-capture {
		width: min(100%, 1440px);
		margin: 0 auto;
	}

	@media (max-width: 760px) {
		.onboarding-capture-shell {
			padding: 0;
		}
	}

	:global(.public-site-header),
	:global(.public-site-footer) {
		display: none !important;
	}
</style>
