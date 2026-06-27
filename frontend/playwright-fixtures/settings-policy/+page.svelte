<script lang="ts">
	import '../../settings/settings.app.css';
	import EnforcementSettingsCardView from '$lib/components/EnforcementSettingsCardView.svelte';
	import type { EnforcementPolicy } from '$lib/components/enforcementSettingsModel';

	let policy = $state<EnforcementPolicy>({
		terraform_mode: 'hard',
		k8s_admission_mode: 'soft',
		require_approval_for_prod: true,
		require_approval_for_nonprod: true,
		auto_approve_below_monthly_usd: 100,
		hard_deny_above_monthly_usd: 7500,
		default_ttl_seconds: 1800,
		policy_version: 7,
		updated_at: '2026-06-03T12:00:00.000Z'
	});

	async function savePolicy(): Promise<void> {
		return undefined;
	}
</script>

<svelte:head>
	<title>Settings Policy Capture</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<main class="settings-policy-capture-shell">
	<section class="settings-policy-capture" data-settings-policy-capture>
		<EnforcementSettingsCardView
			accessToken={null}
			proPlus={true}
			billingHref="/billing"
			loading={false}
			savingPolicy={false}
			error=""
			success=""
			bind:policy
			onSavePolicy={savePolicy}
		/>
	</section>
</main>

<style>
	.settings-policy-capture-shell {
		min-height: 100vh;
		padding: 1rem;
		background:
			radial-gradient(circle at 20% 0%, rgb(34 211 238 / 0.08), transparent 28rem), #030912;
		color: var(--color-ink-50);
	}

	.settings-policy-capture {
		width: min(100%, 1180px);
		margin: 0 auto;
	}

	:global(.public-site-header),
	:global(.public-site-footer) {
		display: none !important;
	}

	@media (max-width: 760px) {
		.settings-policy-capture-shell {
			padding: 0.75rem;
		}
	}
</style>
