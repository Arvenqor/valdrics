import { describe, expect, it } from 'vitest';

import { buildPublicAuthHref, resolvePublicAppOrigin } from './publicAppOrigin';

describe('publicAppOrigin', () => {
	it('moves production marketing-domain auth traffic to the app host', () => {
		const currentUrl = new URL('https://valdrics.com/pricing');

		expect(resolvePublicAppOrigin(currentUrl)).toBe('https://app.valdrics.com');
		expect(buildPublicAuthHref('/auth/login?mode=signup', currentUrl)).toBe(
			'https://app.valdrics.com/auth/login?mode=signup'
		);
	});

	it('keeps same-origin auth links for app, staging, and local hosts without explicit override', () => {
		expect(buildPublicAuthHref('/auth/login', new URL('https://app.valdrics.com/'))).toBe(
			'/auth/login'
		);
		expect(buildPublicAuthHref('/auth/login', new URL('https://staging.valdrics.com/'))).toBe(
			'/auth/login'
		);
		expect(buildPublicAuthHref('/auth/login', new URL('http://localhost:5174/'))).toBe(
			'/auth/login'
		);
	});
});
