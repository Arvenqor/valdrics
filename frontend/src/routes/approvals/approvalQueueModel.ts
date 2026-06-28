export type ApprovalQueueItem = {
	approval_id: string;
	decision_id: string;
	status: string;
	source: string;
	environment: string;
	project_id: string;
	action: string;
	resource_reference: string;
	estimated_monthly_delta_usd: string | number;
	reason_codes: string[];
	routing_rule_id: string | null;
	expires_at: string;
	created_at: string;
};

export type ApprovalFilterId = 'all' | 'cost' | 'routed' | 'policy';

export type ApprovalFilter = {
	id: ApprovalFilterId;
	label: string;
};

export const APPROVAL_FILTERS: ApprovalFilter[] = [
	{ id: 'all', label: 'All' },
	{ id: 'cost', label: 'Cost impact' },
	{ id: 'routed', label: 'Routed' },
	{ id: 'policy', label: 'Policy signals' }
];

function toNumber(value: unknown): number {
	const number = Number(value ?? 0);
	return Number.isFinite(number) ? number : 0;
}

export function hasCostImpact(approval: ApprovalQueueItem): boolean {
	return toNumber(approval.estimated_monthly_delta_usd) !== 0;
}

function hasRoutingRule(approval: ApprovalQueueItem): boolean {
	return Boolean(approval.routing_rule_id);
}

function hasPolicySignals(approval: ApprovalQueueItem): boolean {
	return approval.reason_codes.length > 0;
}

export function filterApprovals(
	approvals: ApprovalQueueItem[],
	filter: ApprovalFilterId
): ApprovalQueueItem[] {
	if (filter === 'cost') return approvals.filter(hasCostImpact);
	if (filter === 'routed') return approvals.filter(hasRoutingRule);
	if (filter === 'policy') return approvals.filter(hasPolicySignals);
	return approvals;
}

export function countApprovalsByFilter(
	approvals: ApprovalQueueItem[]
): Record<ApprovalFilterId, number> {
	return {
		all: approvals.length,
		cost: approvals.filter(hasCostImpact).length,
		routed: approvals.filter(hasRoutingRule).length,
		policy: approvals.filter(hasPolicySignals).length
	};
}

export function getPendingMonthlyDelta(approvals: ApprovalQueueItem[]): number {
	return approvals.reduce(
		(sum, approval) => sum + toNumber(approval.estimated_monthly_delta_usd),
		0
	);
}

export function getEarliestExpiry(approvals: ApprovalQueueItem[]): string | null {
	return (
		approvals
			.map((approval) => approval.expires_at)
			.filter(Boolean)
			.sort((left, right) => left.localeCompare(right))[0] ?? null
	);
}

export function sortApprovalsByExpiry(approvals: ApprovalQueueItem[]): ApprovalQueueItem[] {
	return approvals.toSorted((left, right) => left.expires_at.localeCompare(right.expires_at));
}

export function formatMoney(value: number | string): string {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		maximumFractionDigits: 2
	}).format(toNumber(value));
}

export function formatDate(value: string | null): string {
	if (!value) return 'No expiry';
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return value;
	return new Intl.DateTimeFormat('en-US', {
		month: 'short',
		day: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	}).format(date);
}

export function formatAction(value: string): string {
	return String(value || 'review change').replace(/[._-]/g, ' ');
}

export function emptyTitleForFilter(filter: ApprovalFilterId): string {
	if (filter === 'cost') return 'No cost-impact approvals';
	if (filter === 'routed') return 'No routed approvals';
	if (filter === 'policy') return 'No policy-signal approvals';
	return 'No pending approval requests';
}

export function emptyBodyForFilter(filter: ApprovalFilterId): string {
	if (filter === 'all')
		return 'Reviewer-visible policy decisions will appear here as they are routed.';
	return 'Switch to All to review every pending request in the queue.';
}
