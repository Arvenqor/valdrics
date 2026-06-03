import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import Page from './+page.svelte';
import type { PageData } from './$types';

const { putMock } = vi.hoisted(() => ({
	putMock: vi.fn()
}));

vi.mock('$app/paths', () => ({
	base: ''
}));

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_URL: 'https://api.test/api/v1'
	}
}));

vi.mock('$lib/api', () => ({
	api: {
		put: (...args: unknown[]) => putMock(...args)
	}
}));

function jsonResponse(payload: unknown, status = 200): Response {
	return new Response(JSON.stringify(payload), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

describe('ROI planner page', () => {
	beforeEach(() => {
		putMock.mockReset();
	});

	afterEach(() => {
		cleanup();
	});

	it('renders the ROI planner workspace for signed-in users', () => {
		const data = {
			user: {
				id: 'user-1',
				app_metadata: {},
				user_metadata: {},
				aud: 'authenticated',
				created_at: '2026-03-01T00:00:00.000Z'
			},
			session: { access_token: 'token' },
			subscription: { tier: 'free', status: 'active' },
			profile: null,
			detectedCurrencyCode: 'USD',
			savedSettings: null
		} as unknown as PageData;
		render(Page, {
			data
		});

		expect(screen.getByRole('heading', { level: 1, name: /12-month roi planner/i })).toBeTruthy();
		expect(screen.getByRole('heading', { name: /build your 12-month roi plan/i })).toBeTruthy();
		expect(
			screen.getByRole('link', { name: /continue to guided setup/i }).getAttribute('href')
		).toBe('/onboarding?intent=roi_assessment');
		expect(screen.getByRole('button', { name: /save planner defaults/i })).toBeTruthy();
	}, 20000);

	it('keeps the planner usable for unauthenticated users while prompting them to sign in to save', () => {
		const data = {
			user: null,
			session: null,
			subscription: { tier: 'free', status: 'active' },
			profile: null,
			detectedCurrencyCode: 'USD',
			savedSettings: null
		} as unknown as PageData;
		render(Page, {
			data
		});

		expect(screen.getByRole('heading', { name: /build your 12-month roi plan/i })).toBeTruthy();
		expect(screen.getByRole('link', { name: /sign in to save plan/i }).getAttribute('href')).toBe(
			'/auth/login?next=%2Froi-planner'
		);
		expect(putMock).not.toHaveBeenCalled();
	});

	it('saves authenticated planner defaults through the real unit economics settings contract', async () => {
		putMock.mockResolvedValue(
			jsonResponse({
				id: 'd8a24b36-7b94-4a5f-9bd4-774ea239e3af',
				default_request_volume: 1000,
				default_workload_volume: 200,
				default_customer_volume: 50,
				anomaly_threshold_percent: 20,
				target_spend_reduction_pct: 18,
				target_rollout_days: 45,
				target_team_members: 6,
				target_blended_hourly_rate: 125
			})
		);

		const data = {
			user: { id: 'user-1' },
			session: { access_token: 'token' },
			subscription: { tier: 'free', status: 'active' },
			profile: null,
			detectedCurrencyCode: 'USD',
			savedSettings: {
				id: 'd8a24b36-7b94-4a5f-9bd4-774ea239e3af',
				default_request_volume: 1000,
				default_workload_volume: 200,
				default_customer_volume: 50,
				anomaly_threshold_percent: 20,
				target_spend_reduction_pct: 18,
				target_rollout_days: 45,
				target_team_members: 6,
				target_blended_hourly_rate: 125
			}
		} as unknown as PageData;

		render(Page, { data });
		await fireEvent.click(screen.getByRole('button', { name: /save planner defaults/i }));

		await waitFor(() => {
			expect(putMock).toHaveBeenCalledWith(
				'/api/edge/api/v1/costs/unit-economics/settings',
				{
					target_spend_reduction_pct: 18,
					target_rollout_days: 45,
					target_team_members: 6,
					target_blended_hourly_rate: 125
				},
				expect.objectContaining({
					headers: {
						Authorization: 'Bearer token'
					},
					timeoutMs: 8000
				})
			);
		});
		expect((await screen.findByRole('status')).textContent).toContain(
			'Planner defaults saved for this workspace.'
		);
	});
});
