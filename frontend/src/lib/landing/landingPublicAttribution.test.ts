import { describe, expect, it } from 'vitest';

import { buildLandingPublicPath } from './landingPublicAttribution';

describe('landingPublicAttribution', () => {
	it('preserves existing query params while adding landing attribution', () => {
		expect(
			buildLandingPublicPath({
				path: '/enterprise?source=preseed&intent=existing#proof',
				source: 'trust_enterprise',
				persona: 'security',
				utm: {
					source: 'linkedin',
					medium: 'paid_social',
					campaign: 'q2_launch'
				}
			})
		).toBe(
			'/enterprise?source=preseed&intent=existing&entry=landing&persona=security&utm_source=linkedin&utm_medium=paid_social&utm_campaign=q2_launch#proof'
		);
	});
});
