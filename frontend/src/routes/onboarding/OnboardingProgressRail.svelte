<script lang="ts">
	import { Check, CircleDashed, LoaderCircle, ShieldCheck } from '@lucide/svelte';
	import type { OnboardingProvider } from './onboardingTypesUtils';

	interface Props {
		currentStep: number;
		selectedProvider: OnboardingProvider;
		isLoading: boolean;
		isVerifying: boolean;
		success: boolean;
		error: string;
		getProviderLabel: (provider: OnboardingProvider) => string;
	}

	let {
		currentStep,
		selectedProvider,
		isLoading,
		isVerifying,
		success,
		error,
		getProviderLabel
	}: Props = $props();

	const steps = [
		{ label: 'Choose provider', short: '01' },
		{ label: 'Configure access', short: '02' },
		{ label: 'Verify signal', short: '03' },
		{ label: 'Go live', short: '04' }
	];
	const progress = $derived(Math.min(100, Math.max(25, ((currentStep + 1) / steps.length) * 100)));
	const providerLabel = $derived(getProviderLabel(selectedProvider));
	const statusLabel = $derived(
		error
			? 'Action needed'
			: success
				? 'Connection verified'
				: isVerifying
					? 'Verifying connection'
					: isLoading
						? 'Preparing setup'
						: 'Progress saved'
	);
	const statusClass = $derived(
		error ? 'error' : success ? 'success' : isLoading || isVerifying ? 'busy' : 'ready'
	);
</script>

<section class="onboarding-hero" aria-labelledby="onboarding-title">
	<div class="onboarding-hero__copy">
		<div class="onboarding-hero__status" data-status={statusClass} aria-live="polite">
			{#if statusClass === 'success'}
				<Check size={14} aria-hidden="true" />
			{:else if statusClass === 'busy'}
				<LoaderCircle size={14} aria-hidden="true" class="onboarding-spin" />
			{:else if statusClass === 'error'}
				<CircleDashed size={14} aria-hidden="true" />
			{:else}
				<ShieldCheck size={14} aria-hidden="true" />
			{/if}
			<span>{statusLabel}</span>
		</div>
		<h1 id="onboarding-title">Connect Cloud & Cloud+ Providers</h1>
		<p>
			Read-only setup for {providerLabel}. Valdrics validates the account path before it unlocks
			spend, ownership, and governance signals.
		</p>
	</div>

	<div
		class="onboarding-progress"
		role="progressbar"
		aria-label="Setup progress"
		aria-valuemin="0"
		aria-valuemax="100"
		aria-valuenow={Math.round(progress)}
	>
		<div class="onboarding-progress__meta">
			<span>Setup progress</span>
			<strong>{Math.round(progress)}%</strong>
		</div>
		<div class="onboarding-progress__track" aria-hidden="true">
			<div class="onboarding-progress__fill" style={`width: ${progress}%`}></div>
		</div>
	</div>
</section>

<nav class="onboarding-steps" aria-label="Setup steps">
	{#each steps as step, index}
		<div
			class="onboarding-step"
			class:onboarding-step--active={index === currentStep}
			class:onboarding-step--complete={index < currentStep}
			aria-current={index === currentStep ? 'step' : undefined}
		>
			<span class="onboarding-step__num" aria-hidden="true">
				{#if index < currentStep}
					<Check size={13} />
				{:else}
					{step.short}
				{/if}
			</span>
			<span>{step.label}</span>
		</div>
	{/each}
</nav>
