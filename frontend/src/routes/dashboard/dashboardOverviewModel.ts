import { countZombieFindings, type ZombieCollections } from '$lib/zombieCollections';
import type {
	ApprovalQueueSummary,
	DailySpendPoint,
	DashboardOverviewModel,
	PolicyHealthMetric,
	ProviderSpendBreakdown
} from '$lib/components/dashboard/overviewTypes';

type CostSummary = {
	total_cost?: unknown;
	total_cost_usd?: unknown;
};

type CarbonSummary = {
	total_co2_kg?: unknown;
	total_carbon_kgco2e?: unknown;
};

type LeadershipTopService = {
	service?: unknown;
	cost_usd?: unknown;
};

type LeadershipKpis = {
	total_cost_usd?: unknown;
	cost_by_provider?: Record<string, unknown> | null;
	top_services?: LeadershipTopService[] | null;
	carbon_total_kgco2e?: unknown;
	carbon_coverage_percent?: unknown;
	savings_opportunity_monthly_usd?: unknown;
	savings_realized_monthly_usd?: unknown;
	open_recommendations?: unknown;
	applied_recommendations?: unknown;
	pending_remediations?: unknown;
	completed_remediations?: unknown;
	security_high_risk_decisions?: unknown;
	security_approval_required_decisions?: unknown;
	security_anomaly_signal_decisions?: unknown;
	notes?: unknown;
};

type CostDailyPoint = {
	date?: unknown;
	provider?: unknown;
	cost_usd?: unknown;
	carbon_kgco2e?: unknown;
};

type CostDailySeries = {
	total_cost_usd?: unknown;
	total_carbon_kgco2e?: unknown;
	points?: CostDailyPoint[] | null;
};

type ApprovalQueueItem = {
	approval_id?: unknown;
	action?: unknown;
	environment?: unknown;
	resource_reference?: unknown;
	estimated_monthly_delta_usd?: unknown;
	expires_at?: unknown;
	reason_codes?: unknown;
};

type BuildDashboardOverviewInput = {
	costs?: CostSummary | null;
	carbon?: CarbonSummary | null;
	zombies?: ZombieCollections | null;
	leadershipKpis?: LeadershipKpis | null;
	dailyCosts?: CostDailySeries | null;
	approvalsQueue?: ApprovalQueueItem[] | null;
	periodLabel: string;
	provider?: string | null;
};

function toFiniteNumber(value: unknown, fallback = 0): number {
	if (typeof value === 'number') return Number.isFinite(value) ? value : fallback;
	if (typeof value === 'string' && value.trim()) {
		const parsed = Number(value);
		return Number.isFinite(parsed) ? parsed : fallback;
	}
	return fallback;
}

function firstFiniteNumber(...values: unknown[]): number {
	for (const value of values) {
		const number = toFiniteNumber(value, Number.NaN);
		if (Number.isFinite(number)) return number;
	}
	return 0;
}

function toNullablePercent(value: unknown): number | null {
	if (value === null || value === undefined || value === '') return null;
	const number = toFiniteNumber(value, Number.NaN);
	if (!Number.isFinite(number)) return null;
	return Math.max(0, Math.min(100, number));
}

function toLabel(value: unknown, fallback: string): string {
	const text = String(value ?? '').trim();
	return text || fallback;
}

function providerLabel(provider: string): string {
	const normalized = provider.trim().toLowerCase();
	if (normalized === 'aws') return 'AWS';
	if (normalized === 'azure') return 'Azure';
	if (normalized === 'gcp') return 'GCP';
	if (normalized === 'saas') return 'SaaS';
	if (normalized === 'license') return 'License';
	if (normalized === 'platform') return 'Platform';
	if (normalized === 'hybrid') return 'Hybrid';
	if (normalized === 'ai') return 'AI';
	return normalized ? normalized.replace(/_/g, ' ') : 'Unknown';
}

function percent(numerator: number, denominator: number): number | null {
	if (denominator <= 0) return null;
	return Math.max(0, Math.min(100, (numerator / denominator) * 100));
}

function buildDailySpend(dailyCosts?: CostDailySeries | null): DailySpendPoint[] {
	const byDate = new Map<string, DailySpendPoint>();
	for (const point of dailyCosts?.points ?? []) {
		const date = toLabel(point.date, '');
		if (!date) continue;
		const existing = byDate.get(date) ?? { date, costUsd: 0, carbonKgco2e: 0 };
		existing.costUsd += toFiniteNumber(point.cost_usd);
		existing.carbonKgco2e += toFiniteNumber(point.carbon_kgco2e);
		byDate.set(date, existing);
	}
	return [...byDate.values()].sort((left, right) => left.date.localeCompare(right.date));
}

function buildCloudBreakdown(params: {
	leadershipKpis?: LeadershipKpis | null;
	dailyCosts?: CostDailySeries | null;
}): ProviderSpendBreakdown[] {
	const providerTotals = new Map<string, number>();
	const rawBreakdown = params.leadershipKpis?.cost_by_provider;
	if (rawBreakdown && typeof rawBreakdown === 'object') {
		for (const [provider, rawCost] of Object.entries(rawBreakdown)) {
			const costUsd = toFiniteNumber(rawCost);
			if (costUsd > 0) providerTotals.set(provider.toLowerCase(), costUsd);
		}
	}

	if (providerTotals.size === 0) {
		for (const point of params.dailyCosts?.points ?? []) {
			const provider = toLabel(point.provider, 'unknown').toLowerCase();
			const current = providerTotals.get(provider) ?? 0;
			providerTotals.set(provider, current + toFiniteNumber(point.cost_usd));
		}
	}

	const total = [...providerTotals.values()].reduce((sum, value) => sum + value, 0);
	return [...providerTotals.entries()]
		.map(([provider, costUsd]) => ({
			provider,
			label: providerLabel(provider),
			costUsd,
			share: total > 0 ? (costUsd / total) * 100 : 0
		}))
		.sort((left, right) => right.costUsd - left.costUsd);
}

function buildSpendTrend(dailySpend: DailySpendPoint[]): number | null {
	const nonZero = dailySpend.filter((point) => point.costUsd > 0);
	if (nonZero.length < 2) return null;
	const first = nonZero[0].costUsd;
	const last = nonZero[nonZero.length - 1].costUsd;
	return first > 0 ? ((last - first) / first) * 100 : null;
}

function buildApprovals(queue?: ApprovalQueueItem[] | null): ApprovalQueueSummary {
	const items = (queue ?? []).map((item, index) => {
		const reasonCodes = Array.isArray(item.reason_codes)
			? item.reason_codes.map((reason) => String(reason)).filter(Boolean)
			: [];
		return {
			id: toLabel(item.approval_id, `approval-${index + 1}`),
			action: toLabel(item.action, 'Review change'),
			environment: toLabel(item.environment, 'unknown'),
			resource: toLabel(item.resource_reference, 'Unspecified resource'),
			monthlyDeltaUsd: toFiniteNumber(item.estimated_monthly_delta_usd),
			expiresAt: toLabel(item.expires_at, ''),
			reasonCodes
		};
	});
	items.sort((left, right) => {
		if (!left.expiresAt) return 1;
		if (!right.expiresAt) return -1;
		return left.expiresAt.localeCompare(right.expiresAt);
	});
	return {
		pendingCount: items.length,
		monthlyDeltaUsd: items.reduce((sum, item) => sum + item.monthlyDeltaUsd, 0),
		items: items.slice(0, 3)
	};
}

export function buildDashboardOverview(input: BuildDashboardOverviewInput): DashboardOverviewModel {
	const leadership = input.leadershipKpis;
	const dailySpend = buildDailySpend(input.dailyCosts);
	const cloudBreakdown = buildCloudBreakdown({
		leadershipKpis: leadership,
		dailyCosts: input.dailyCosts
	});
	const approvals = buildApprovals(input.approvalsQueue);
	const openRecommendations = Math.max(
		0,
		Math.round(toFiniteNumber(leadership?.open_recommendations))
	);
	const appliedRecommendations = Math.max(
		0,
		Math.round(toFiniteNumber(leadership?.applied_recommendations))
	);
	const pendingRemediations = Math.max(
		0,
		Math.round(toFiniteNumber(leadership?.pending_remediations))
	);
	const completedRemediations = Math.max(
		0,
		Math.round(toFiniteNumber(leadership?.completed_remediations))
	);
	const opportunityMonthlyUsd = toFiniteNumber(leadership?.savings_opportunity_monthly_usd);
	const realizedMonthlyUsd = toFiniteNumber(leadership?.savings_realized_monthly_usd);
	const carbonCoveragePercent = toNullablePercent(leadership?.carbon_coverage_percent);
	const recommendationDenominator = openRecommendations + appliedRecommendations;
	const remediationDenominator = pendingRemediations + completedRemediations;
	const totalSavingsEvidence = opportunityMonthlyUsd + realizedMonthlyUsd;

	const policyMetrics: PolicyHealthMetric[] = [
		{
			key: 'carbon_coverage',
			label: 'Carbon Coverage',
			value: carbonCoveragePercent,
			detail:
				carbonCoveragePercent === null
					? 'No carbon coverage evidence in this window'
					: `${carbonCoveragePercent.toFixed(1)}% of cost records carry carbon evidence`
		},
		{
			key: 'recommendation_application',
			label: 'Recommendation Application',
			value: percent(appliedRecommendations, recommendationDenominator),
			detail:
				recommendationDenominator > 0
					? `${appliedRecommendations} applied / ${openRecommendations} open`
					: 'No recommendation workflow evidence in this window'
		},
		{
			key: 'remediation_completion',
			label: 'Remediation Completion',
			value: percent(completedRemediations, remediationDenominator),
			detail:
				remediationDenominator > 0
					? `${completedRemediations} completed / ${pendingRemediations} pending`
					: 'No remediation workflow evidence in this window'
		}
	];

	const notes = Array.isArray(leadership?.notes)
		? leadership.notes.map((note) => String(note)).filter(Boolean)
		: [];

	return {
		periodLabel: input.periodLabel,
		provider: toLabel(input.provider, ''),
		totalSpendUsd: firstFiniteNumber(
			leadership?.total_cost_usd,
			input.costs?.total_cost,
			input.costs?.total_cost_usd
		),
		carbonTotalKgco2e: firstFiniteNumber(
			leadership?.carbon_total_kgco2e,
			input.carbon?.total_co2_kg,
			input.carbon?.total_carbon_kgco2e
		),
		carbonCoveragePercent,
		dailySpend,
		spendTrendPercent: buildSpendTrend(dailySpend),
		cloudBreakdown,
		topServices: (leadership?.top_services ?? [])
			.map((service) => ({
				service: toLabel(service.service, 'Unknown service'),
				costUsd: toFiniteNumber(service.cost_usd)
			}))
			.filter((service) => service.costUsd > 0)
			.slice(0, 5),
		zombieCount: countZombieFindings(input.zombies),
		monthlyWasteUsd: toFiniteNumber(input.zombies?.total_monthly_waste),
		approvals,
		policyHealth: {
			highRiskDecisions: Math.max(
				0,
				Math.round(toFiniteNumber(leadership?.security_high_risk_decisions))
			),
			approvalRequiredDecisions: Math.max(
				0,
				Math.round(toFiniteNumber(leadership?.security_approval_required_decisions))
			),
			anomalySignalDecisions: Math.max(
				0,
				Math.round(toFiniteNumber(leadership?.security_anomaly_signal_decisions))
			),
			metrics: policyMetrics
		},
		savings: {
			opportunityMonthlyUsd,
			realizedMonthlyUsd,
			executionPercent: percent(realizedMonthlyUsd, totalSavingsEvidence),
			openRecommendations,
			appliedRecommendations,
			pendingRemediations,
			completedRemediations
		},
		notes
	};
}
