export type DailySpendPoint = {
	date: string;
	costUsd: number;
	carbonKgco2e: number;
};

export type ProviderSpendBreakdown = {
	provider: string;
	label: string;
	costUsd: number;
	share: number;
};

export type TopServiceSpend = {
	service: string;
	costUsd: number;
};

export type ApprovalQueueSummary = {
	pendingCount: number;
	monthlyDeltaUsd: number;
	items: Array<{
		id: string;
		action: string;
		environment: string;
		resource: string;
		monthlyDeltaUsd: number;
		expiresAt: string;
		reasonCodes: string[];
	}>;
};

export type PolicyHealthMetric = {
	key: string;
	label: string;
	value: number | null;
	detail: string;
};

export type DashboardOverviewModel = {
	periodLabel: string;
	provider: string;
	totalSpendUsd: number;
	carbonTotalKgco2e: number;
	carbonCoveragePercent: number | null;
	dailySpend: DailySpendPoint[];
	spendTrendPercent: number | null;
	cloudBreakdown: ProviderSpendBreakdown[];
	topServices: TopServiceSpend[];
	zombieCount: number;
	monthlyWasteUsd: number;
	approvals: ApprovalQueueSummary;
	policyHealth: {
		highRiskDecisions: number;
		approvalRequiredDecisions: number;
		anomalySignalDecisions: number;
		metrics: PolicyHealthMetric[];
	};
	savings: {
		opportunityMonthlyUsd: number;
		realizedMonthlyUsd: number;
		executionPercent: number | null;
		openRecommendations: number;
		appliedRecommendations: number;
		pendingRemediations: number;
		completedRemediations: number;
	};
	notes: string[];
};
