import { z } from '$lib/validation/clientZod';

export const ENFORCEMENT_REQUEST_TIMEOUT_MS = 8000;

export type EnforcementPolicy = {
	terraform_mode: 'shadow' | 'soft' | 'hard';
	k8s_admission_mode: 'shadow' | 'soft' | 'hard';
	require_approval_for_prod: boolean;
	require_approval_for_nonprod: boolean;
	auto_approve_below_monthly_usd: number;
	hard_deny_above_monthly_usd: number;
	default_ttl_seconds: number;
	policy_version?: number;
	updated_at?: string;
};

export type EnforcementBudget = {
	id: string;
	scope_key: string;
	monthly_limit_usd: number | string;
	active: boolean;
};

export type EnforcementCredit = {
	id: string;
	scope_key: string;
	total_amount_usd: number | string;
	remaining_amount_usd: number | string;
	expires_at: string | null;
	reason: string | null;
	active: boolean;
};

export type EnforcementPolicyRailTone =
	| 'shadow'
	| 'soft'
	| 'hard'
	| 'enabled'
	| 'disabled'
	| 'info';

export type EnforcementPolicyRail = {
	id: string;
	label: string;
	value: string;
	description: string;
	tone: EnforcementPolicyRailTone;
	meta: string;
	blocking: boolean;
};

export const PolicySchema = z.object({
	terraform_mode: z.enum(['shadow', 'soft', 'hard']),
	k8s_admission_mode: z.enum(['shadow', 'soft', 'hard']),
	require_approval_for_prod: z.boolean(),
	require_approval_for_nonprod: z.boolean(),
	auto_approve_below_monthly_usd: z.number().check(z.minimum(0)),
	hard_deny_above_monthly_usd: z.number().check(z.gt(0)),
	default_ttl_seconds: z.number().check(z.int(), z.minimum(60), z.maximum(86400))
});

export function isProPlus(currentTier: string | null | undefined): boolean {
	return ['pro', 'enterprise'].includes((currentTier ?? '').toLowerCase());
}

export function extractErrorMessage(data: unknown, fallback: string): string {
	if (!data || typeof data !== 'object') return fallback;
	const payload = data as Record<string, unknown>;
	if (typeof payload.detail === 'string' && payload.detail.trim()) return payload.detail;
	if (typeof payload.message === 'string' && payload.message.trim()) return payload.message;
	return fallback;
}

export function buildEnforcementHeaders(accessToken?: string | null): Record<string, string> {
	return { Authorization: `Bearer ${accessToken}` };
}

export function enforcementModeLabel(mode: EnforcementPolicy['terraform_mode']): string {
	return mode;
}

export function enforcementModeMeta(mode: EnforcementPolicy['terraform_mode']): {
	description: string;
	meta: string;
	blocking: boolean;
} {
	if (mode === 'hard') {
		return {
			description: 'Failing evaluations stop the request before execution.',
			meta: 'blocking gate',
			blocking: true
		};
	}
	if (mode === 'soft') {
		return {
			description: 'Failing evaluations require review but can still move through approval.',
			meta: 'review gate',
			blocking: false
		};
	}
	return {
		description: 'Evaluations are recorded without changing the approval decision.',
		meta: 'observe only',
		blocking: false
	};
}

export function formatUsd(value: number | string): string {
	const amount = Number(value);
	if (!Number.isFinite(amount)) return '$0';
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		maximumFractionDigits: Number.isInteger(amount) ? 0 : 2
	}).format(amount);
}

export function formatTtl(seconds: number): string {
	if (!Number.isFinite(seconds) || seconds <= 0) return '0s';
	if (seconds < 60) return `${seconds}s`;

	const hours = Math.floor(seconds / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);
	const remainingSeconds = seconds % 60;
	const parts: string[] = [];

	if (hours > 0) parts.push(`${hours}h`);
	if (minutes > 0) parts.push(`${minutes}m`);
	if (remainingSeconds > 0) parts.push(`${remainingSeconds}s`);

	return parts.join(' ');
}

export function buildEnforcementPolicyRails(policy: EnforcementPolicy): EnforcementPolicyRail[] {
	const terraform = enforcementModeMeta(policy.terraform_mode);
	const kubernetes = enforcementModeMeta(policy.k8s_admission_mode);

	return [
		{
			id: 'terraform',
			label: 'Terraform provisioning gate',
			value: enforcementModeLabel(policy.terraform_mode),
			description: terraform.description,
			tone: policy.terraform_mode,
			meta: terraform.meta,
			blocking: terraform.blocking
		},
		{
			id: 'kubernetes',
			label: 'Kubernetes admission gate',
			value: enforcementModeLabel(policy.k8s_admission_mode),
			description: kubernetes.description,
			tone: policy.k8s_admission_mode,
			meta: kubernetes.meta,
			blocking: kubernetes.blocking
		},
		{
			id: 'prod-approval',
			label: 'Production approval rule',
			value: policy.require_approval_for_prod ? 'required' : 'optional',
			description: policy.require_approval_for_prod
				? 'Production spend changes must pass an approval decision.'
				: 'Production approval is not mandatory under the current policy.',
			tone: policy.require_approval_for_prod ? 'enabled' : 'disabled',
			meta: policy.require_approval_for_prod ? 'human approval' : 'not enforced',
			blocking: policy.require_approval_for_prod
		},
		{
			id: 'nonprod-approval',
			label: 'Non-production approval rule',
			value: policy.require_approval_for_nonprod ? 'required' : 'optional',
			description: policy.require_approval_for_nonprod
				? 'Non-production spend changes must pass an approval decision.'
				: 'Non-production changes can proceed without mandatory approval.',
			tone: policy.require_approval_for_nonprod ? 'enabled' : 'disabled',
			meta: policy.require_approval_for_nonprod ? 'human approval' : 'not enforced',
			blocking: policy.require_approval_for_nonprod
		},
		{
			id: 'spend-envelope',
			label: 'Spend envelope thresholds',
			value: `${formatUsd(policy.auto_approve_below_monthly_usd)} auto / ${formatUsd(
				policy.hard_deny_above_monthly_usd
			)} deny`,
			description:
				'Requests below the auto-approval line can clear faster; requests above the hard-deny line are blocked.',
			tone: 'hard',
			meta: 'monthly USD',
			blocking: true
		},
		{
			id: 'approval-ttl',
			label: 'Approval freshness window',
			value: formatTtl(policy.default_ttl_seconds),
			description: 'Open approvals expire after this TTL so stale spend changes are re-reviewed.',
			tone: 'info',
			meta: 'decision TTL',
			blocking: false
		}
	];
}
