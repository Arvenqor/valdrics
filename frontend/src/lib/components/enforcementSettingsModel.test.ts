import { describe, expect, it } from 'vitest';

import {
	buildEnforcementPolicyRails,
	enforcementModeMeta,
	type EnforcementPolicy
} from './enforcementSettingsModel';
import { formatTtl, formatUsd } from '$lib/format';

const policy: EnforcementPolicy = {
	terraform_mode: 'hard',
	k8s_admission_mode: 'soft',
	require_approval_for_prod: true,
	require_approval_for_nonprod: false,
	auto_approve_below_monthly_usd: 25,
	hard_deny_above_monthly_usd: 5000,
	default_ttl_seconds: 3900
};

describe('enforcement settings model', () => {
	it('derives policy engine rails from the current enforcement policy contract', () => {
		const rails = buildEnforcementPolicyRails(policy);
		const byId = Object.fromEntries(rails.map((rail) => [rail.id, rail]));

		expect(rails).toHaveLength(6);
		expect(byId.terraform?.label).toBe('Terraform provisioning gate');
		expect(byId.terraform?.value).toBe('hard');
		expect(byId.terraform?.tone).toBe('hard');
		expect(byId.terraform?.blocking).toBe(true);
		expect(byId.kubernetes?.value).toBe('soft');
		expect(byId.kubernetes?.tone).toBe('soft');
		expect(byId.kubernetes?.blocking).toBe(false);
		expect(byId['prod-approval']?.value).toBe('required');
		expect(byId['prod-approval']?.tone).toBe('enabled');
		expect(byId['prod-approval']?.blocking).toBe(true);
		expect(byId['nonprod-approval']?.value).toBe('optional');
		expect(byId['nonprod-approval']?.tone).toBe('disabled');
		expect(byId['nonprod-approval']?.blocking).toBe(false);
		expect(byId['spend-envelope']?.value).toBe('$25 auto / $5,000 deny');
		expect(byId['spend-envelope']?.blocking).toBe(true);
		expect(byId['approval-ttl']?.value).toBe('1h 5m');
		expect(byId['approval-ttl']?.blocking).toBe(false);
	});

	it('keeps hard, soft, and shadow semantics explicit', () => {
		expect(enforcementModeMeta('hard')).toMatchObject({
			meta: 'blocking gate',
			blocking: true
		});
		expect(enforcementModeMeta('soft')).toMatchObject({
			meta: 'review gate',
			blocking: false
		});
		expect(enforcementModeMeta('shadow')).toMatchObject({
			meta: 'observe only',
			blocking: false
		});
	});

	it('formats enforcement money and TTL values for dense settings UI', () => {
		expect(formatUsd('1200.5000')).toBe('$1,200.50');
		expect(formatUsd('5000.0000')).toBe('$5,000');
		expect(formatTtl(75)).toBe('1m 15s');
		expect(formatTtl(3600)).toBe('1h');
	});
});
