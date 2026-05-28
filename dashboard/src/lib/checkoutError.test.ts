import { describe, expect, it } from 'vitest';

import { resolveCheckoutErrorMessage } from './checkoutError';

describe('checkoutError', () => {
	it('prefers backend detail messages', () => {
		expect(resolveCheckoutErrorMessage({ detail: 'Live FX rate unavailable.' })).toBe(
			'Live FX rate unavailable.'
		);
	});

	it('uses resilient fetch message payloads from 5xx responses', () => {
		expect(
			resolveCheckoutErrorMessage({
				error: 'Internal Server Error',
				message: 'Failed to create checkout session'
			})
		).toBe('Failed to create checkout session');
	});

	it('falls back to a support-oriented checkout message', () => {
		expect(resolveCheckoutErrorMessage(null)).toBe(
			'Checkout failed. Please try again or contact support.'
		);
	});
});
