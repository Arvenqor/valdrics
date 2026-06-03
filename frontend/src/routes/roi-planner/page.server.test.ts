import { describe, expect, it, vi } from 'vitest';
import { load } from './+page.server';

function buildRequest(headers: Record<string, string> = {}): Request {
	return new Request('https://example.com/roi-planner', {
		method: 'GET',
		headers
	});
}

function asLoadResult(
	value: Awaited<ReturnType<typeof load>>
): Exclude<Awaited<ReturnType<typeof load>>, void> {
	if (!value) {
		throw new Error('expected load result data');
	}
	return value;
}

describe('roi planner currency detection', () => {
	it('defaults to USD when there is no trusted country header', async () => {
		const result = asLoadResult(
			await load({
				request: buildRequest(),
				parent: async () => ({ session: null })
			} as Parameters<typeof load>[0])
		);

		expect(result.detectedCurrencyCode).toBe('USD');
	});

	it('uses supported public geo currencies from trusted headers', async () => {
		const result = asLoadResult(
			await load({
				request: buildRequest({ 'x-vercel-ip-country': 'GB' }),
				parent: async () => ({ session: null })
			} as Parameters<typeof load>[0])
		);

		expect(result.detectedCurrencyCode).toBe('GBP');
	});

	it('uses NGN for NG visitors on the public planner surface', async () => {
		const result = asLoadResult(
			await load({
				request: buildRequest({ 'cf-ipcountry': 'NG' }),
				parent: async () => ({ session: null })
			} as Parameters<typeof load>[0])
		);

		expect(result.detectedCurrencyCode).toBe('NGN');
	});

	it('loads saved tenant KPI targets from the canonical unit economics settings endpoint', async () => {
		const savedSettings = {
			id: 'd8a24b36-7b94-4a5f-9bd4-774ea239e3af',
			default_request_volume: 1000,
			default_workload_volume: 200,
			default_customer_volume: 50,
			anomaly_threshold_percent: 20,
			target_spend_reduction_pct: 18,
			target_rollout_days: 45,
			target_team_members: 6,
			target_blended_hourly_rate: 125
		};
		const fetchMock = vi.fn().mockResolvedValue(
			new Response(JSON.stringify(savedSettings), {
				status: 200,
				headers: { 'Content-Type': 'application/json' }
			})
		);

		const result = asLoadResult(
			await load({
				request: buildRequest(),
				fetch: fetchMock,
				parent: async () => ({ session: { access_token: 'token' } })
			} as unknown as Parameters<typeof load>[0])
		);

		expect(fetchMock).toHaveBeenCalledWith(
			'/api/edge/api/v1/costs/unit-economics/settings',
			expect.objectContaining({
				headers: {
					Authorization: 'Bearer token'
				}
			})
		);
		expect(result.savedSettings).toEqual(savedSettings);
	});

	it('falls back to planner defaults when saved settings cannot be loaded', async () => {
		const fetchMock = vi.fn().mockRejectedValue(new Error('network unavailable'));

		const result = asLoadResult(
			await load({
				request: buildRequest(),
				fetch: fetchMock,
				parent: async () => ({ session: { access_token: 'token' } })
			} as unknown as Parameters<typeof load>[0])
		);

		expect(result.savedSettings).toBeNull();
	});
});
