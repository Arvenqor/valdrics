<script lang="ts">
	import { ArrowLeft, ArrowRight, CheckCircle2, LoaderCircle } from '@lucide/svelte';

	let { selectedProvider, isVerifying, onBack, verifyConnection, proceedToVerify } = $props();
</script>

<div class="onboarding-actions">
	<button type="button" class="secondary-btn onboarding-actions__back" onclick={onBack}>
		<ArrowLeft size={16} aria-hidden="true" />
		Back
	</button>
	{#if selectedProvider === 'aws'}
		<button
			type="button"
			class="primary-btn onboarding-actions__primary"
			onclick={verifyConnection}
			disabled={isVerifying}
		>
			{#if isVerifying}
				<LoaderCircle size={16} aria-hidden="true" class="onboarding-spin" />
				Verifying...
			{:else}
				<CheckCircle2 size={16} aria-hidden="true" />
				Verify Connection
			{/if}
		</button>
	{:else}
		<button
			type="button"
			class="primary-btn onboarding-actions__primary"
			onclick={proceedToVerify}
			disabled={isVerifying}
		>
			{#if isVerifying}
				<LoaderCircle size={16} aria-hidden="true" class="onboarding-spin" />
				Verifying...
			{:else if selectedProvider === 'saas' || selectedProvider === 'license'}
				<CheckCircle2 size={16} aria-hidden="true" />
				Create & Verify Connector
			{:else}
				Next: Verify Connection
				<ArrowRight size={16} aria-hidden="true" />
			{/if}
		</button>
	{/if}
</div>
