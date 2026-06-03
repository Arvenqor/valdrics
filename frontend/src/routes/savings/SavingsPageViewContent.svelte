<script lang="ts">
	import { base } from '$app/paths';
	import {
		AlertTriangle,
		CalendarDays,
		CheckCircle2,
		Download,
		FileText,
		ListChecks,
		RefreshCw,
		TrendingUp,
		Wallet
	} from '@lucide/svelte';
	import AuthGate from '$lib/components/AuthGate.svelte';
	import DateRangePicker from '$lib/components/DateRangePicker.svelte';
	import { getUpgradePrompt } from '$lib/pricing/upgradePrompt';
	import SavingsDrilldownPanel from './SavingsDrilldownPanel.svelte';
	import SavingsEvidenceTimeline from './SavingsEvidenceTimeline.svelte';
	import SavingsProviderBreakdown from './SavingsProviderBreakdown.svelte';
	import type {
		RealizedSavingsEvent,
		SavingsProofDrilldownResponse,
		SavingsProofResponse
	} from './savingsTypes';
	import { compactUsd, realizedRate, totalGovernanceActions } from './savingsViewModel';

	type DrilldownDimension = 'strategy_type' | 'remediation_action' | 'finding_category';

	interface Props {
		data: {
			user?: unknown;
			subscription?: {
				tier?: string;
			};
		};
		loading: boolean;
		downloading: boolean;
		error: string;
		success: string;
		drilldownError: string;
		realizedEventsError: string;
		report: SavingsProofResponse | null;
		drilldown: SavingsProofDrilldownResponse | null;
		realizedEvents: RealizedSavingsEvent[];
		drilldownDimension: DrilldownDimension;
		provider: string;
		datePreset: string;
		dateRange: {
			startDate: string;
			endDate: string;
		};
		isProPlus: (tierValue: string | null | undefined) => boolean;
		formatUsd: (value: number) => string;
		formatDate: (value: string) => string;
		loadReport: () => Promise<void>;
		loadDrilldown: () => Promise<void>;
		downloadCsv: () => Promise<void>;
		handleDateChange: (dates: { startDate: string; endDate: string }) => void;
	}

	let {
		data,
		loading,
		downloading,
		error,
		success,
		drilldownError,
		realizedEventsError,
		report,
		drilldown,
		realizedEvents,
		drilldownDimension = $bindable(),
		provider = $bindable(),
		datePreset = $bindable(),
		dateRange,
		isProPlus,
		formatUsd,
		formatDate,
		loadReport,
		loadDrilldown,
		downloadCsv,
		handleDateChange
	}: Props = $props();

	const upgradePrompt = getUpgradePrompt('pro', 'savings proof');

	let hasProAccess = $derived(isProPlus(data.subscription?.tier));
	let periodLabel = $derived(
		dateRange.startDate && dateRange.endDate
			? `${dateRange.startDate} to ${dateRange.endDate}`
			: 'Selected reporting window'
	);
	let asOfLabel = $derived(report ? formatDate(report.as_of) : 'Waiting for report');
	let realizationPercent = $derived(Math.round(realizedRate(report)));
	let actionCount = $derived(totalGovernanceActions(report));
	let annualizedRealized = $derived((report?.realized_monthly_usd ?? 0) * 12);
	let hasPartialIssues = $derived(Boolean(drilldownError || realizedEventsError));
</script>

<div class="savings-page">
	<header class="savings-hero">
		<div class="savings-hero__copy">
			<h1>Savings Proof</h1>
			<p>
				Procurement-ready proof of savings opportunity, realized actions, and remediation evidence.
			</p>
		</div>
		<div class="savings-hero__status" aria-label="Savings report freshness">
			<CalendarDays size={18} />
			<div>
				<span>Window</span>
				<strong>{periodLabel}</strong>
			</div>
		</div>
	</header>

	<AuthGate authenticated={!!data.user} action="view savings proof" className="savings-auth-empty">
		{#if !hasProAccess}
			<section class="savings-upgrade-panel" aria-labelledby="savings-upgrade-title">
				<div>
					<h2 id="savings-upgrade-title">{upgradePrompt.heading}</h2>
					<p>{upgradePrompt.body}</p>
					<span>{upgradePrompt.footnote}</span>
				</div>
				<a href={`${base}/billing`} class="savings-primary-link">{upgradePrompt.cta}</a>
			</section>
		{:else}
			<section class="savings-toolbar" aria-label="Savings report controls">
				<div class="savings-toolbar__filters">
					<DateRangePicker bind:value={datePreset} onDateChange={handleDateChange} />
					<label class="savings-select-field" for="provider">
						<span>Provider</span>
						<select
							id="provider"
							bind:value={provider}
							class="savings-select"
							onchange={() => void loadReport()}
						>
							<option value="">All providers</option>
							<option value="aws">AWS</option>
							<option value="azure">Azure</option>
							<option value="gcp">GCP</option>
							<option value="saas">SaaS</option>
							<option value="license">License</option>
							<option value="platform">Platform</option>
							<option value="hybrid">Hybrid</option>
						</select>
					</label>
				</div>
				<div class="savings-toolbar__actions">
					<button
						type="button"
						class="savings-secondary-button"
						onclick={loadReport}
						disabled={loading}
					>
						<RefreshCw size={16} />
						<span>Refresh</span>
					</button>
					<button
						type="button"
						class="savings-primary-button"
						onclick={downloadCsv}
						disabled={downloading || loading}
					>
						<Download size={16} />
						<span>{downloading ? 'Exporting...' : 'Download CSV'}</span>
					</button>
				</div>
			</section>

			{#if error}
				<div role="alert" class="savings-alert savings-alert--danger">
					<AlertTriangle size={18} />
					<p>{error}</p>
				</div>
			{/if}

			{#if success}
				<div role="status" class="savings-alert savings-alert--success">
					<CheckCircle2 size={18} />
					<p>{success}</p>
				</div>
			{/if}

			{#if hasPartialIssues && !error}
				<div role="status" class="savings-alert savings-alert--warning">
					<AlertTriangle size={18} />
					<p>One savings proof section could not refresh. Available report data remains visible.</p>
				</div>
			{/if}

			{#if loading && !report}
				<section class="savings-loading" aria-label="Loading savings proof">
					<div class="savings-skeleton savings-skeleton--hero"></div>
					<div class="savings-skeleton-grid">
						<div class="savings-skeleton"></div>
						<div class="savings-skeleton"></div>
						<div class="savings-skeleton"></div>
					</div>
				</section>
			{:else if !report}
				<section class="savings-panel">
					<div class="savings-empty-state savings-empty-state--tall">
						<FileText size={26} />
						<p>No report available.</p>
					</div>
				</section>
			{:else}
				<section class="savings-kpi-grid" aria-label="Savings proof summary">
					<article class="savings-kpi-card savings-kpi-card--primary">
						<div class="savings-kpi-card__icon">
							<Wallet size={18} />
						</div>
						<span>Realized monthly</span>
						<strong>{compactUsd(report.realized_monthly_usd)}</strong>
						<p>{compactUsd(annualizedRealized)} annualized from completed and applied actions.</p>
					</article>
					<article class="savings-kpi-card">
						<div class="savings-kpi-card__icon">
							<TrendingUp size={18} />
						</div>
						<span>Opportunity monthly</span>
						<strong>{compactUsd(report.opportunity_monthly_usd)}</strong>
						<p>{realizationPercent}% realized against the current proof snapshot.</p>
					</article>
					<article class="savings-kpi-card">
						<div class="savings-kpi-card__icon">
							<ListChecks size={18} />
						</div>
						<span>Open recommendations</span>
						<strong>{report.open_recommendations}</strong>
						<p>{report.applied_recommendations} applied recommendations in evidence.</p>
					</article>
					<article class="savings-kpi-card">
						<div class="savings-kpi-card__icon">
							<CheckCircle2 size={18} />
						</div>
						<span>Governance actions</span>
						<strong>{actionCount}</strong>
						<p>{report.completed_remediations} completed remediations in this window.</p>
					</article>
				</section>

				<section class="savings-proof-meta" aria-label="Savings proof metadata">
					<div>
						<span>As of</span>
						<strong>{asOfLabel}</strong>
					</div>
					<div>
						<span>Contract tier</span>
						<strong>{report.tier}</strong>
					</div>
					<div>
						<span>Reporting period</span>
						<strong>{report.start_date} to {report.end_date}</strong>
					</div>
				</section>

				<div class="savings-main-grid">
					<SavingsProviderBreakdown breakdown={report.breakdown} {formatUsd} />
					<SavingsDrilldownPanel
						{drilldown}
						{drilldownError}
						bind:drilldownDimension
						{loading}
						{formatUsd}
						{loadDrilldown}
					/>
				</div>

				<SavingsEvidenceTimeline {realizedEvents} {realizedEventsError} {formatUsd} {formatDate} />

				{#if report.notes?.length}
					<section class="savings-panel savings-notes-panel" aria-labelledby="savings-notes-title">
						<div class="savings-panel__header">
							<div>
								<h2 id="savings-notes-title">Notes</h2>
								<p>Backend-generated context for this savings proof snapshot.</p>
							</div>
						</div>
						<ul>
							{#each report.notes as note (note)}
								<li>{note}</li>
							{/each}
						</ul>
					</section>
				{/if}
			{/if}
		{/if}
	</AuthGate>
</div>
