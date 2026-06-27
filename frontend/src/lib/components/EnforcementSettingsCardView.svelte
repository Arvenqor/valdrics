<script lang="ts">
	import { onMount } from 'svelte';
	import { AlertTriangle, BadgeDollarSign, Clock, ShieldCheck } from '@lucide/svelte';
	import { createLazyComponent } from '$lib/lazyComponent';
	import { getUpgradePrompt } from '$lib/pricing/upgradePrompt';
	import {
		buildEnforcementPolicyRails,
		type EnforcementPolicy
	} from './enforcementSettingsModel';
	import { formatTtl, formatUsd } from '$lib/format';
	import './EnforcementSettingsCardView.css';

	let {
		accessToken,
		proPlus,
		billingHref,
		loading,
		savingPolicy,
		error,
		success,
		policy = $bindable(),
		onSavePolicy
	}: {
		accessToken?: string | null;
		proPlus: boolean;
		billingHref: string;
		loading: boolean;
		savingPolicy: boolean;
		error: string;
		success: string;
		policy: EnforcementPolicy;
		onSavePolicy: () => void | Promise<void>;
	} = $props();

	type EnforcementSettingsAdvancedSectionProps = {
		accessToken?: string | null;
	};

	const loadEnforcementSettingsAdvancedSection =
		createLazyComponent<EnforcementSettingsAdvancedSectionProps>(
			() => import('./EnforcementSettingsAdvancedSection.svelte')
		);

	const upgradePrompt = getUpgradePrompt('pro', 'enforcement controls');
	const policyRails = $derived(buildEnforcementPolicyRails(policy));
	const blockingRailCount = $derived(policyRails.filter((rail) => rail.blocking).length);
	const activeApprovalScopes = $derived(
		[policy.require_approval_for_prod, policy.require_approval_for_nonprod].filter(Boolean).length
	);

	let advancedSectionAnchor = $state<HTMLDivElement | null>(null);
	let advancedSectionReady = $state(import.meta.env.MODE === 'test');

	onMount(() => {
		if (advancedSectionReady || typeof IntersectionObserver === 'undefined') {
			advancedSectionReady = true;
			return;
		}

		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting)) {
					advancedSectionReady = true;
					observer.disconnect();
				}
			},
			{ rootMargin: '280px 0px' }
		);

		if (advancedSectionAnchor) {
			observer.observe(advancedSectionAnchor);
		}

		return () => observer.disconnect();
	});
</script>

<div
	class="card stagger-enter relative enforcement-policy-engine"
	class:opacity-60={!proPlus}
	class:pointer-events-none={!proPlus}
>
	<div class="enforcement-policy-engine__header">
		<div>
			<p class="enforcement-policy-engine__kicker">Policy Engine</p>
			<h2 class="text-lg font-semibold flex items-center gap-2">
				<ShieldCheck size={19} aria-hidden="true" /> Enforcement Control Plane
			</h2>
			<p>
				Configure approval gates, monthly spend envelopes, and temporary credits from the real
				enforcement API.
			</p>
		</div>
		{#if !proPlus}
			<span class="badge badge-warning text-xs">Pro Plan Required</span>
		{/if}
	</div>

	{#if !proPlus}
		<div
			class="absolute inset-0 z-10 flex items-center justify-center rounded-xl bg-ink-950/55 px-6 text-center"
		>
			<div class="max-w-md space-y-3 pointer-events-auto">
				<h3 class="text-lg font-semibold text-white">{upgradePrompt.heading}</h3>
				<p class="text-sm text-ink-300">{upgradePrompt.body}</p>
				<p class="text-xs text-ink-500">{upgradePrompt.footnote}</p>
				<a href={billingHref} class="btn btn-primary shadow-lg">{upgradePrompt.cta}</a>
			</div>
		</div>
	{/if}

	{#if error}
		<div role="alert" class="card border-danger-500/50 bg-danger-500/10 mb-4">
			<p class="text-danger-400 text-sm">{error}</p>
		</div>
	{/if}

	{#if success}
		<div role="status" class="card border-success-500/50 bg-success-500/10 mb-4">
			<p class="text-success-400 text-sm">{success}</p>
		</div>
	{/if}

	{#if loading}
		<div class="skeleton h-4 w-64"></div>
	{:else}
		<div class="space-y-6">
			<div class="enforcement-policy-engine__summary" aria-label="Enforcement policy summary">
				<div class="enforcement-policy-engine__summary-card">
					<AlertTriangle size={17} aria-hidden="true" />
					<span>Blocking rails</span>
					<strong>{blockingRailCount}</strong>
				</div>
				<div class="enforcement-policy-engine__summary-card">
					<ShieldCheck size={17} aria-hidden="true" />
					<span>Approval scopes</span>
					<strong>{activeApprovalScopes}/2</strong>
				</div>
				<div class="enforcement-policy-engine__summary-card">
					<BadgeDollarSign size={17} aria-hidden="true" />
					<span>Hard deny above</span>
					<strong>{formatUsd(policy.hard_deny_above_monthly_usd)}</strong>
				</div>
				<div class="enforcement-policy-engine__summary-card">
					<Clock size={17} aria-hidden="true" />
					<span>Decision TTL</span>
					<strong>{formatTtl(policy.default_ttl_seconds)}</strong>
				</div>
			</div>

			<div class="enforcement-policy-engine__callout">
				<ShieldCheck size={16} aria-hidden="true" />
				<p>
					Hard rails block failing requests, soft rails route them through review, and shadow rails
					record evidence without changing the approval decision.
				</p>
			</div>

			<div class="enforcement-policy-engine__rail-list" aria-label="Configured enforcement rails">
				{#each policyRails as rail (rail.id)}
					<article
						class="enforcement-policy-engine__rail enforcement-policy-engine__rail--{rail.tone}"
					>
						<div>
							<div class="enforcement-policy-engine__rail-top">
								<span>{rail.label}</span>
								{#if rail.blocking}
									<strong>Blocking</strong>
								{/if}
							</div>
							<p>{rail.description}</p>
						</div>
						<div class="enforcement-policy-engine__rail-state">
							<span>{rail.meta}</span>
							<strong>{rail.value}</strong>
						</div>
					</article>
				{/each}
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<div class="form-group">
					<label for="enforcement_terraform_mode">Terraform Gate Mode</label>
					<select
						id="enforcement_terraform_mode"
						class="select"
						bind:value={policy.terraform_mode}
						aria-label="Terraform gate mode"
					>
						<option value="shadow">shadow</option>
						<option value="soft">soft</option>
						<option value="hard">hard</option>
					</select>
				</div>
				<div class="form-group">
					<label for="enforcement_k8s_mode">K8s Admission Mode</label>
					<select
						id="enforcement_k8s_mode"
						class="select"
						bind:value={policy.k8s_admission_mode}
						aria-label="Kubernetes admission mode"
					>
						<option value="shadow">shadow</option>
						<option value="soft">soft</option>
						<option value="hard">hard</option>
					</select>
				</div>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<div class="form-group">
					<label for="enforcement_auto_approve_threshold">Auto-Approve Below (USD/month)</label>
					<input
						type="number"
						id="enforcement_auto_approve_threshold"
						min="0"
						step="0.01"
						bind:value={policy.auto_approve_below_monthly_usd}
						aria-label="Auto approve threshold per month"
					/>
				</div>
				<div class="form-group">
					<label for="enforcement_hard_deny_threshold">Hard-Deny Above (USD/month)</label>
					<input
						type="number"
						id="enforcement_hard_deny_threshold"
						min="0.01"
						step="0.01"
						bind:value={policy.hard_deny_above_monthly_usd}
						aria-label="Hard deny threshold per month"
					/>
				</div>
				<div class="form-group">
					<label for="enforcement_ttl_seconds">Approval TTL (seconds)</label>
					<input
						type="number"
						id="enforcement_ttl_seconds"
						min="60"
						max="86400"
						step="1"
						bind:value={policy.default_ttl_seconds}
						aria-label="Approval TTL in seconds"
					/>
				</div>
			</div>

			<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
				<label class="flex items-center gap-3 cursor-pointer">
					<input
						type="checkbox"
						class="toggle"
						bind:checked={policy.require_approval_for_prod}
						aria-label="Require approval for prod"
					/>
					<span>Require approval for prod</span>
				</label>
				<label class="flex items-center gap-3 cursor-pointer">
					<input
						type="checkbox"
						class="toggle"
						bind:checked={policy.require_approval_for_nonprod}
						aria-label="Require approval for nonprod"
					/>
					<span>Require approval for non-prod</span>
				</label>
			</div>

			<div class="flex flex-wrap gap-3 items-center">
				<button
					type="button"
					class="btn btn-primary"
					onclick={onSavePolicy}
					disabled={savingPolicy}
					aria-label="Save enforcement policy"
				>
					{#if savingPolicy}
						Saving...
					{:else}
						<ShieldCheck size={16} aria-hidden="true" /> Save Enforcement Policy
					{/if}
				</button>
				{#if policy.policy_version}
					<span class="text-xs text-ink-500">
						Policy v{policy.policy_version}{policy.updated_at
							? ` • updated ${new Date(policy.updated_at).toLocaleString()}`
							: ''}
					</span>
				{/if}
			</div>

			<div bind:this={advancedSectionAnchor}>
				{#if advancedSectionReady}
					{#await loadEnforcementSettingsAdvancedSection()}
						<div class="pt-4 border-t border-ink-700 space-y-4">
							<div class="skeleton h-4 w-40"></div>
							<div class="skeleton h-4 w-full"></div>
							<div class="skeleton h-4 w-2/3"></div>
						</div>
					{:then module}
						{@const EnforcementSettingsAdvancedSection = module.default}
						<EnforcementSettingsAdvancedSection {accessToken} />
					{:catch}
						<div class="pt-4 border-t border-ink-700">
							<p class="text-xs text-ink-500">
								Budget and credit controls are temporarily unavailable.
							</p>
						</div>
					{/await}
				{:else}
					<div class="pt-4 border-t border-ink-700 space-y-4">
						<div class="skeleton h-4 w-40"></div>
						<div class="skeleton h-4 w-full"></div>
						<div class="skeleton h-4 w-2/3"></div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
