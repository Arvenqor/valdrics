<script lang="ts">
	import { browser } from '$app/environment';
	import { base } from '$app/paths';
	import { untrack } from 'svelte';
	import { api } from '$lib/api';
	import { bearerHeaders, extractApiErrorMessage } from '$lib/http';
	import LandingRoiCalculator from '$lib/components/landing/LandingRoiCalculator.svelte';
	import { edgeApiPath } from '$lib/edgeProxy';
	import { TimeoutError } from '$lib/fetchWithTimeout';
	import {
		resolveInitialLandingCurrency,
		setLandingCurrencyPreference,
		type LandingCurrencyCode
	} from '$lib/landing/currencyPreference';
	import {
		DEFAULT_LANDING_ROI_INPUTS,
		calculateLandingRoi,
		normalizeLandingRoiInputs
	} from '$lib/landing/roiCalculator';
	import { formatCurrency } from '$lib/format';
	import type { UnitEconomicsSettings } from '../ops/opsTypes';

	let { data } = $props();
	const SAVE_TIMEOUT_MS = 8000;

	// untrack() reads the prop value at initialization time without subscribing
	// to future changes — the canonical Svelte 5 pattern for seeding $state
	// from server-side load data. See: https://svelte.dev/docs/svelte/svelte#untrack
	const _initial = untrack(() => data.savedSettings);
	let savedSettings = $state<UnitEconomicsSettings | null>(_initial ?? null);

	let roiMonthlySpendUsd = $state(DEFAULT_LANDING_ROI_INPUTS.monthlySpendUsd);
	let roiExpectedReductionPct = $state(
		_initial?.target_spend_reduction_pct ?? DEFAULT_LANDING_ROI_INPUTS.expectedReductionPct
	);
	let roiRolloutDays = $state(
		_initial?.target_rollout_days ?? DEFAULT_LANDING_ROI_INPUTS.rolloutDays
	);
	let roiTeamMembers = $state(
		_initial?.target_team_members ?? DEFAULT_LANDING_ROI_INPUTS.teamMembers
	);
	let roiBlendedHourlyUsd = $state(
		_initial?.target_blended_hourly_rate ?? DEFAULT_LANDING_ROI_INPUTS.blendedHourlyUsd
	);
	let roiPlatformAnnualCostUsd = $state(DEFAULT_LANDING_ROI_INPUTS.platformAnnualCostUsd);
	let roiCurrencyOverride = $state<LandingCurrencyCode | null>(null);
	let savingPlannerDefaults = $state(false);
	let saveError = $state('');
	let saveSuccess = $state('');

	let localCurrencyCode = $derived.by(() => data.detectedCurrencyCode);
	let roiCurrencyCode = $derived(
		roiCurrencyOverride ?? resolveInitialLandingCurrency(localCurrencyCode)
	);
	let canSavePlannerDefaults = $derived(Boolean(data.user && data.session?.access_token));

	let roiInputs = $derived(
		normalizeLandingRoiInputs({
			monthlySpendUsd: roiMonthlySpendUsd,
			expectedReductionPct: roiExpectedReductionPct,
			rolloutDays: roiRolloutDays,
			teamMembers: roiTeamMembers,
			blendedHourlyUsd: roiBlendedHourlyUsd,
			platformAnnualCostUsd: roiPlatformAnnualCostUsd
		})
	);
	let roiResult = $derived(calculateLandingRoi(roiInputs));

	function handleCurrencyCodeChange(value: LandingCurrencyCode): void {
		roiCurrencyOverride = value;
		if (browser) {
			setLandingCurrencyPreference(value);
		}
	}

	function buildPlannerSettingsPayload() {
		return {
			target_spend_reduction_pct: Number(roiInputs.expectedReductionPct),
			target_rollout_days: Number(roiInputs.rolloutDays),
			target_team_members: Number(roiInputs.teamMembers),
			target_blended_hourly_rate: Number(roiInputs.blendedHourlyUsd)
		};
	}

	async function savePlannerDefaults(): Promise<void> {
		if (!canSavePlannerDefaults || !data.session?.access_token) {
			return;
		}

		savingPlannerDefaults = true;
		saveError = '';
		saveSuccess = '';
		try {
			const response = await api.put(
				edgeApiPath('/costs/unit-economics/settings'),
				buildPlannerSettingsPayload(),
				{
					headers: bearerHeaders(data.session.access_token),
					timeoutMs: SAVE_TIMEOUT_MS
				}
			);
			if (!response.ok) {
				const payload = await response.json().catch(() => ({}));
				throw new Error(extractApiErrorMessage(payload, 'Failed to save planner defaults.'));
			}
			savedSettings = (await response.json()) as UnitEconomicsSettings;
			saveSuccess = 'Planner defaults saved for this workspace.';
		} catch (error) {
			if (error instanceof TimeoutError) {
				saveError = 'Saving planner defaults timed out. Please try again.';
			} else {
				const err = error as Error;
				saveError = err.message || 'Failed to save planner defaults.';
			}
		} finally {
			savingPlannerDefaults = false;
		}
	}
</script>

<svelte:head>
	<title>ROI Planner | Valdrics</title>
	<meta
		name="description"
		content="Build a full 12-month ROI plan with your own cloud and software spend assumptions before rollout."
	/>
</svelte:head>

<div class="roi-planner-page">
	<!-- Page header -->
	<div class="roi-planner-header">
		<div class="roi-planner-header__inner">
			<div class="roi-planner-header__badge" role="presentation" aria-hidden="true">
				<span class="roi-planner-header__dot"></span>
				ROI WORKSPACE
			</div>
			<h1 class="roi-planner-header__title">12-Month ROI Planner</h1>
			<p class="roi-planner-header__sub">
				Model rollout effort, implementation cost, and payback using your own spend assumptions.
				{#if savedSettings}
					<span class="roi-planner-header__hint">
						Pre-filled with your saved KPI targets — adjust any value below.
					</span>
				{/if}
			</p>
		</div>
	</div>

	<div class="roi-planner-body">
		<LandingRoiCalculator
			sectionId="roi-planner"
			heading="Build your 12-month ROI plan"
			subtitle="Set realistic assumptions, pressure-test rollout timelines, and align engineering and finance on expected value."
			ctaLabel="Continue to Guided Setup"
			ctaNote="Directional planning model. Validate assumptions with your own usage and contract baselines."
			{roiInputs}
			{roiResult}
			{roiMonthlySpendUsd}
			{roiExpectedReductionPct}
			{roiRolloutDays}
			{roiTeamMembers}
			{roiBlendedHourlyUsd}
			buildRoiCtaHref={`${base}/onboarding?intent=roi_assessment`}
			{formatCurrency}
			onRoiControlInput={() => {
				saveError = '';
				saveSuccess = '';
			}}
			onRoiMonthlySpendChange={(value) => {
				roiMonthlySpendUsd = value;
			}}
			onRoiExpectedReductionChange={(value) => {
				roiExpectedReductionPct = value;
			}}
			onRoiRolloutDaysChange={(value) => {
				roiRolloutDays = value;
			}}
			onRoiTeamMembersChange={(value) => {
				roiTeamMembers = value;
			}}
			onRoiBlendedHourlyChange={(value) => {
				roiBlendedHourlyUsd = value;
			}}
			onRoiCta={() => {}}
			{localCurrencyCode}
			currencyCode={roiCurrencyCode}
			onCurrencyCodeChange={handleCurrencyCodeChange}
		/>

		<div class="material-perspective">
			<section class="roi-planner-save material-card-3d" aria-labelledby="roi-planner-save-title">
				<div>
					<h2 id="roi-planner-save-title">Planner defaults</h2>
					<p>
						Save reduction, rollout, staffing, and hourly-rate targets to pre-fill Ops Center KPI
						planning.
					</p>
				</div>

				{#if canSavePlannerDefaults}
					<button
						type="button"
						class="roi-planner-save__button material-button-3d"
						disabled={savingPlannerDefaults}
						onclick={savePlannerDefaults}
					>
						{savingPlannerDefaults ? 'Saving...' : 'Save Planner Defaults'}
					</button>
				{:else}
					<a class="roi-planner-save__link material-button-3d" href={`${base}/auth/login?next=%2Froi-planner`}>
						Sign in to save plan
					</a>
				{/if}
			</section>
		</div>

		{#if saveSuccess}
			<p class="roi-planner-status roi-planner-status--success" role="status">{saveSuccess}</p>
		{/if}
		{#if saveError}
			<p class="roi-planner-status roi-planner-status--error" role="alert">{saveError}</p>
		{/if}
	</div>
</div>

<style>
	.roi-planner-page {
		min-height: 100vh;
		background: var(--base, #030912);
	}

	.roi-planner-header {
		padding: 80px 40px 48px;
		border-bottom: 1px solid var(--bdr, rgba(255, 255, 255, 0.06));
		background: linear-gradient(180deg, rgba(0, 207, 124, 0.04) 0%, transparent 100%);
	}

	.roi-planner-header__inner {
		max-width: 760px;
		margin: 0 auto;
	}

	.roi-planner-header__badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 5px 13px;
		border-radius: 100px;
		background: rgba(0, 207, 124, 0.1);
		border: 1px solid rgba(0, 207, 124, 0.2);
		font-family: var(--font-mono, monospace);
		font-size: 11px;
		color: var(--jade, #00cf7c);
		letter-spacing: 0;
		margin-bottom: 20px;
	}

	.roi-planner-header__dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--jade, #00cf7c);
		animation: pulse-dot 1.8s ease-in-out infinite;
	}

	@keyframes pulse-dot {
		0%,
		100% {
			opacity: 1;
			transform: scale(1);
		}
		50% {
			opacity: 0.4;
			transform: scale(0.65);
		}
	}

	.roi-planner-header__title {
		font-family: var(--font-display, system-ui);
		font-weight: 800;
		font-size: clamp(28px, 4vw, 48px);
		color: var(--white, #f0f4f8);
		line-height: 1.06;
		letter-spacing: 0;
		margin: 0 0 12px;
	}

	.roi-planner-header__sub {
		font-size: 16px;
		color: var(--sub, rgba(240, 244, 248, 0.55));
		line-height: 1.7;
		margin: 0;
	}

	.roi-planner-header__hint {
		display: block;
		margin-top: 8px;
		font-size: 13px;
		color: var(--jade, #00cf7c);
		opacity: 0.85;
	}

	.roi-planner-body {
		padding: 48px 40px;
		max-width: 1100px;
		margin: 0 auto;
	}

	:global(.roi-planner-page .landing-h2),
	:global(.roi-planner-page .landing-roi-metric strong) {
		color: var(--color-ink-50);
	}

	:global(.roi-planner-page .landing-section-sub),
	:global(.roi-planner-page .landing-roi-note),
	:global(.roi-planner-page .landing-roi-metric p) {
		color: var(--color-ink-300);
	}

	:global(.roi-planner-page .landing-proof-k),
	:global(.roi-planner-page .landing-roi-label),
	:global(.roi-planner-page .landing-cta-link) {
		color: #67e8f9;
	}

	:global(.roi-planner-page .landing-currency-toggle__label),
	:global(.roi-planner-page .landing-roi-meta) {
		color: var(--color-ink-300);
	}

	:global(.roi-planner-page .landing-currency-toggle__controls),
	:global(.roi-planner-page .landing-roi-control),
	:global(.roi-planner-page .landing-roi-metric) {
		border-color: rgb(255 255 255 / 0.08);
		background: rgb(255 255 255 / 0.04);
	}

	:global(.roi-planner-page .landing-roi-control input.input) {
		border-color: rgb(255 255 255 / 0.12);
		background: rgb(3 9 18 / 0.72);
		color: var(--color-ink-50);
	}

	.roi-planner-save {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 24px;
		margin: 28px 24px 0;
		padding: 24px;
		border: 1px solid var(--bdr, rgba(255, 255, 255, 0.08));
		border-radius: 16px;
		background: rgba(255, 255, 255, 0.035);
	}

	.roi-planner-save h2 {
		margin: 0 0 6px;
		font-size: 18px;
		font-weight: 750;
		color: var(--white, #f0f4f8);
		letter-spacing: 0;
	}

	.roi-planner-save p {
		max-width: 620px;
		margin: 0;
		color: var(--sub, rgba(240, 244, 248, 0.6));
		font-size: 14px;
		line-height: 1.6;
	}

	.roi-planner-save__button,
	.roi-planner-save__link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		min-height: 44px;
		padding: 0 18px;
		border-radius: 10px;
		border: 1px solid rgba(0, 207, 124, 0.32);
		background: var(--jade, #00cf7c);
		color: #031008;
		font-size: 14px;
		font-weight: 750;
		text-decoration: none;
		white-space: nowrap;
		cursor: pointer;
	}

	.roi-planner-save__button:disabled {
		opacity: 0.6;
		cursor: wait;
	}

	.roi-planner-status {
		margin: 16px 24px 0;
		padding: 12px 14px;
		border-radius: 10px;
		font-size: 14px;
		line-height: 1.5;
	}

	.roi-planner-status--success {
		border: 1px solid rgba(0, 207, 124, 0.22);
		background: rgba(0, 207, 124, 0.1);
		color: var(--jade, #00cf7c);
	}

	.roi-planner-status--error {
		border: 1px solid rgba(255, 93, 93, 0.24);
		background: rgba(255, 93, 93, 0.1);
		color: #ffb4b4;
	}

	@media (max-width: 900px) {
		.roi-planner-header {
			padding: 60px 24px 36px;
		}

		.roi-planner-body {
			padding: 36px 24px;
		}

		.roi-planner-save {
			align-items: stretch;
			flex-direction: column;
			margin-inline: 0;
		}

		.roi-planner-status {
			margin-inline: 0;
		}
	}
</style>
