<script lang="ts">
	import '../../savings/savings.app.css';
	import SavingsPageViewContent from '../../savings/SavingsPageViewContent.svelte';
	import {
		savingsCaptureDrilldown,
		savingsCaptureRealizedEvents,
		savingsCaptureReport
	} from '../../savings/savingsCaptureFixture';

	const data = {
		user: {
			id: 'user-savings-capture',
			email: 'finance@valdrics.com',
			tenant_id: 'tenant-savings-capture'
		},
		session: { access_token: 'capture-token' },
		subscription: { tier: 'pro', status: 'active' },
		profile: {
			persona: 'finance',
			role: 'admin',
			platform_operator: false
		}
	};

	let drilldownDimension = $state<'strategy_type' | 'remediation_action' | 'finding_category'>(
		'strategy_type'
	);
	let provider = $state('');
	let datePreset = $state('30d');
	let dateRange = $state({
		startDate: savingsCaptureReport.start_date,
		endDate: savingsCaptureReport.end_date
	});

	function isProPlus(): boolean {
		return true;
	}

	function formatUsd(value: number): string {
		if (!Number.isFinite(value)) return '$0.00';
		return new Intl.NumberFormat(undefined, { style: 'currency', currency: 'USD' }).format(value);
	}

	function formatDate(value: string): string {
		const parsed = new Date(value);
		if (Number.isNaN(parsed.getTime())) return value;
		return parsed.toLocaleString();
	}

	function handleDateChange(dates: { startDate: string; endDate: string }) {
		dateRange = dates;
	}

	async function noop(): Promise<void> {
		return undefined;
	}
</script>

<svelte:head>
	<title>Savings Capture</title>
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="savings-capture-shell">
	<div class="savings-capture" data-savings-capture>
		<SavingsPageViewContent
			{data}
			loading={false}
			downloading={false}
			error=""
			success=""
			drilldownError=""
			realizedEventsError=""
			report={savingsCaptureReport}
			drilldown={savingsCaptureDrilldown}
			realizedEvents={savingsCaptureRealizedEvents}
			bind:drilldownDimension
			bind:provider
			bind:datePreset
			{dateRange}
			{isProPlus}
			{formatUsd}
			{formatDate}
			loadReport={noop}
			loadDrilldown={noop}
			downloadCsv={noop}
			{handleDateChange}
		/>
	</div>
</div>

<style>
	.savings-capture-shell {
		min-height: 100vh;
		padding: 1rem;
		background: #030912;
	}

	.savings-capture {
		width: min(100%, 1440px);
		margin: 0 auto;
	}

	:global(.public-site-header),
	:global(.public-site-footer) {
		display: none !important;
	}

	@media (max-width: 760px) {
		.savings-capture-shell {
			padding: 0;
		}
	}
</style>
