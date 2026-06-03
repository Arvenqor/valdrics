// @vitest-environment jsdom

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mocks = vi.hoisted(() => ({
	fetch: vi.fn(),
	showRateLimitWarning: vi.fn(),
	addToast: vi.fn()
}));

vi.mock('$app/paths', () => ({
	base: ''
}));

vi.mock('./edgeProxy', () => ({
	edgeApiPath: (path: string) => `/api/edge${path}`
}));

vi.mock('./stores/ui.svelte', () => ({
	uiState: {
		showRateLimitWarning: mocks.showRateLimitWarning,
		addToast: mocks.addToast
	}
}));

describe('resilientFetch auth retry', () => {
	beforeEach(() => {
		vi.resetModules();
		mocks.fetch.mockReset();
		mocks.showRateLimitWarning.mockReset();
		mocks.addToast.mockReset();
		vi.stubGlobal('fetch', mocks.fetch);
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it('retries once with an access token from the server session endpoint after a 401', async () => {
		mocks.fetch
			.mockResolvedValueOnce(
				new Response('{}', {
					status: 401,
					headers: { 'Content-Type': 'application/json' }
				})
			)
			.mockResolvedValueOnce(
				new Response(JSON.stringify({ accessToken: 'fresh-token', tenantId: 'tenant-123' }), {
					status: 200,
					headers: { 'Content-Type': 'application/json' }
				})
			)
			.mockResolvedValueOnce(
				new Response('ok', {
					status: 200,
					headers: { 'Content-Type': 'text/plain' }
				})
			);

		const { resilientFetch } = await import('./api');
		const response = await resilientFetch('/api/edge/jobs', {
			method: 'GET',
			headers: { Authorization: 'Bearer stale-token' }
		});

		expect(response.status).toBe(200);
		expect(mocks.fetch).toHaveBeenCalledTimes(3);
		expect(mocks.fetch.mock.calls[1]?.[0]).toBe('/auth/session');
		expect(mocks.fetch.mock.calls[1]?.[1]).toEqual(
			expect.objectContaining({
				method: 'GET',
				credentials: 'include',
				cache: 'no-store'
			})
		);
		expect(mocks.fetch.mock.calls[2]?.[0]).toBe('/api/edge/jobs');
		expect(mocks.fetch.mock.calls[2]?.[1]).toEqual(
			expect.objectContaining({
				method: 'GET',
				headers: expect.any(Headers)
			})
		);
		const retryHeaders = mocks.fetch.mock.calls[2]?.[1]?.headers as Headers;
		expect(retryHeaders.get('Authorization')).toBe('Bearer fresh-token');
	});
});
