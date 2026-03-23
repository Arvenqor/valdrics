import { describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import { readable } from 'svelte/store';
import Page from './+page.svelte';
import { DEFAULT_PRICING_PLANS } from './plans';

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_URL: 'https://api.test/api/v1'
	}
}));

vi.mock('$env/static/public', () => ({
	PUBLIC_API_URL: 'https://api.test/api/v1'
}));

vi.mock('$app/paths', () => ({
	assets: '',
	base: ''
}));

vi.mock('$app/navigation', () => ({
	goto: vi.fn()
}));

vi.mock('$app/stores', () => {
	return {
		page: readable({
			url: new URL('https://example.com/pricing')
		})
	};
});

describe('pricing page public messaging', () => {
	it('shows the free tier entry path plus self-serve paid plans and enterprise review', () => {
		render(Page, {
			props: {
				data: {
					user: null,
					session: null,
					subscription: { tier: 'free', status: 'active' },
					profile: null,
					plans: DEFAULT_PRICING_PLANS
				}
			}
		});

		expect(
			screen.getByRole('heading', { level: 1, name: /pricing that stays simple/i })
		).toBeTruthy();
		expect(screen.getByText(/^Start on the permanent free tier, prove one workflow/i)).toBeTruthy();
		expect(
			screen.getByRole('heading', { name: /^free tier for your first savings workflow$/i })
		).toBeTruthy();
		expect(
			screen.getByRole('link', { name: /start on free tier/i }).getAttribute('href')
		).toContain('plan=free');
		expect(screen.getByRole('heading', { name: /^starter$/i })).toBeTruthy();
		expect(screen.getByRole('heading', { name: /^growth$/i })).toBeTruthy();
		expect(screen.getByRole('heading', { name: /^pro$/i })).toBeTruthy();
		expect(screen.getByText(/first governed workflow/i)).toBeTruthy();
		expect(screen.getAllByText(/^Best for$/i).length).toBeGreaterThanOrEqual(4);
		expect(
			screen.getByText(
				/one team needs daily review cadence, initial azure\/gcp visibility, and stronger owner routing/i
			)
		).toBeTruthy();
		expect(screen.getByText(/\$49\/mo starting price\./i)).toBeTruthy();
		expect(screen.getByText(/\$149\/mo starting price\./i)).toBeTruthy();
		expect(screen.getByText(/\$299\/mo starting price\./i)).toBeTruthy();
		const growthPlanCard = screen.getByRole('heading', { name: /^growth$/i }).closest('article');
		expect(growthPlanCard?.className).toContain('pricing-plan-card--popular');

		expect(
			screen.getByRole('heading', {
				name: /use enterprise review only when the buying process requires it/i
			})
		).toBeTruthy();
		expect(screen.getByText(/start with workspace access or published pricing/i)).toBeTruthy();
		expect(screen.getByText(/prices shown in usd\./i)).toBeTruthy();
		expect(
			screen.getByText(/the permanent free tier does not require a checkout session/i)
		).toBeTruthy();

		const enterpriseReviewLinks = screen.getAllByRole('link', {
			name: /^enterprise review$/i
		});
		expect(enterpriseReviewLinks.length).toBeGreaterThanOrEqual(2);
		expect(enterpriseReviewLinks[0]?.getAttribute('href') || '').toContain('/enterprise?');
		expect(enterpriseReviewLinks[1]?.getAttribute('href') || '').toContain('/enterprise?');
		expect(
			screen.getByRole('link', { name: /request validation briefing/i }).getAttribute('href') || ''
		).toContain('/talk-to-sales?');
	});
});
