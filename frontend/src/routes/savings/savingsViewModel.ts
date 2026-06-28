import type {
	RealizedSavingsEvent,
	SavingsProofBreakdownItem,
	SavingsProofDrilldownBucket,
	SavingsProofResponse
} from './savingsTypes';

type SavingsAccent = {
	color: string;
	soft: string;
	border: string;
};

const PROVIDER_LABELS: Record<string, string> = {
	aws: 'AWS',
	azure: 'Azure',
	gcp: 'GCP',
	saas: 'SaaS',
	license: 'License',
	platform: 'Platform',
	hybrid: 'Hybrid'
};

const PROVIDER_ACCENTS: Record<string, SavingsAccent> = {
	aws: {
		color: '#fbbf24',
		soft: 'rgb(251 191 36 / 0.12)',
		border: 'rgb(251 191 36 / 0.32)'
	},
	azure: {
		color: '#38bdf8',
		soft: 'rgb(56 189 248 / 0.12)',
		border: 'rgb(56 189 248 / 0.32)'
	},
	gcp: {
		color: '#a78bfa',
		soft: 'rgb(167 139 250 / 0.12)',
		border: 'rgb(167 139 250 / 0.32)'
	},
	saas: {
		color: '#34d399',
		soft: 'rgb(52 211 153 / 0.12)',
		border: 'rgb(52 211 153 / 0.32)'
	},
	license: {
		color: '#fb7185',
		soft: 'rgb(251 113 133 / 0.12)',
		border: 'rgb(251 113 133 / 0.32)'
	},
	platform: {
		color: '#22d3ee',
		soft: 'rgb(34 211 238 / 0.12)',
		border: 'rgb(34 211 238 / 0.32)'
	},
	hybrid: {
		color: '#f97316',
		soft: 'rgb(249 115 22 / 0.12)',
		border: 'rgb(249 115 22 / 0.32)'
	}
};

const FALLBACK_ACCENT: SavingsAccent = {
	color: '#94a3b8',
	soft: 'rgb(148 163 184 / 0.1)',
	border: 'rgb(148 163 184 / 0.26)'
};

const DIMENSION_LABELS: Record<string, string> = {
	provider: 'Provider',
	strategy_type: 'Strategy type',
	remediation_action: 'Remediation action',
	finding_category: 'Finding category'
};

export function providerLabel(provider: string | null | undefined): string {
	const normalized = String(provider ?? '')
		.trim()
		.toLowerCase();
	return PROVIDER_LABELS[normalized] ?? (provider ? String(provider).toUpperCase() : 'Unknown');
}

export function providerAccent(provider: string | null | undefined): SavingsAccent {
	const normalized = String(provider ?? '')
		.trim()
		.toLowerCase();
	return PROVIDER_ACCENTS[normalized] ?? FALLBACK_ACCENT;
}

export function savingsAccentStyle(accent: SavingsAccent): string {
	return `--savings-row-accent: ${accent.color}; --savings-row-accent-soft: ${accent.soft}; --savings-row-border: ${accent.border};`;
}

export function dimensionLabel(dimension: string | null | undefined): string {
	const normalized = String(dimension ?? '')
		.trim()
		.toLowerCase();
	return DIMENSION_LABELS[normalized] ?? humanizeIdentifier(dimension ?? 'Unknown');
}

function humanizeIdentifier(value: string | null | undefined): string {
	const normalized = String(value ?? '').trim();
	if (!normalized) return 'Unknown';
	return normalized
		.replace(/[_-]+/g, ' ')
		.replace(/\s+/g, ' ')
		.trim()
		.replace(/\b\w/g, (char) => char.toUpperCase());
}

export function compactUsd(value: number): string {
	if (!Number.isFinite(value)) return '$0';
	const absolute = Math.abs(value);
	const sign = value < 0 ? '-' : '';
	if (absolute >= 1_000_000) return `${sign}$${(absolute / 1_000_000).toFixed(1)}M`;
	if (absolute >= 1_000) return `${sign}$${(absolute / 1_000).toFixed(1)}K`;
	return `${sign}$${absolute.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

export function percentOf(value: number, total: number): number {
	if (!Number.isFinite(value) || !Number.isFinite(total) || total <= 0) return 0;
	return Math.max(0, Math.min(100, (value / total) * 100));
}

export function realizedRate(report: SavingsProofResponse | null): number {
	if (!report) return 0;
	return percentOf(report.realized_monthly_usd, report.opportunity_monthly_usd);
}

export function totalGovernanceActions(report: SavingsProofResponse | null): number {
	if (!report) return 0;
	return (
		report.open_recommendations +
		report.applied_recommendations +
		report.pending_remediations +
		report.completed_remediations
	);
}

export function maxMonthlyValue(
	rows: Array<SavingsProofBreakdownItem | SavingsProofDrilldownBucket>
): number {
	return Math.max(
		1,
		...rows.map((row) => Math.max(row.opportunity_monthly_usd, row.realized_monthly_usd))
	);
}

export function evidenceEventTitle(event: RealizedSavingsEvent): string {
	return event.finding_category
		? humanizeIdentifier(event.finding_category)
		: `${providerLabel(event.provider)} remediation`;
}

export function evidenceEventTimestamp(event: RealizedSavingsEvent): string {
	return event.executed_at || event.computed_at;
}

export function evidenceEventLocation(event: RealizedSavingsEvent): string {
	return [event.account_id, event.region].filter(Boolean).join(' / ') || 'Tenant scoped';
}
