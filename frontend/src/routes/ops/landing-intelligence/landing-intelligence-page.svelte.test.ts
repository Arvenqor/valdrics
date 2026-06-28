import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import Page from './+page.svelte';
import {
	incrementLandingCtaValue,
	incrementLandingWeeklyStage
} from '$lib/landing/telemetry/funnel';

vi.mock('$app/environment', () => ({
	browser: true
}));

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_URL: 'https://api.test/api/v1'
	}
}));

vi.mock('$app/paths', () => ({
	base: ''
}));

describe('landing intelligence page', () => {
	beforeEach(() => {
		window.localStorage.clear();
	});

	it('renders weekly conversion metrics and trend checks', async () => {
		incrementLandingWeeklyStage('view', window.localStorage, new Date('2026-02-16T10:00:00.000Z'));
		incrementLandingWeeklyStage(
			'engaged',
			window.localStorage,
			new Date('2026-02-16T10:05:00.000Z')
		);
		incrementLandingWeeklyStage('view', window.localStorage, new Date('2026-02-23T10:00:00.000Z'));
		incrementLandingWeeklyStage(
			'engaged',
			window.localStorage,
			new Date('2026-02-23T10:05:00.000Z')
		);
		incrementLandingWeeklyStage('cta', window.localStorage, new Date('2026-02-23T10:10:00.000Z'));
		incrementLandingWeeklyStage(
			'signup_intent',
			window.localStorage,
			new Date('2026-02-23T10:15:00.000Z')
		);
		incrementLandingCtaValue('start_free', window.localStorage);
		incrementLandingCtaValue('enterprise_review', window.localStorage);
		incrementLandingCtaValue('start_free', window.localStorage);

		render(Page, {
			props: {
				data: {
					user: { email: 'ops@valdrics.com', role: 'admin' },
					session: { access_token: 'mock-token' }
				}
			}
		});

		expect(
			screen.getByRole('heading', { level: 1, name: /growth & conversion analytics/i })
		).toBeTruthy();
		expect(screen.getByText(/all-time views/i)).toBeTruthy();
		expect(screen.getByText(/weekly funnel detail/i)).toBeTruthy();
		expect(screen.getByText('2026-02-16')).toBeTruthy();
		expect(screen.getByText('2026-02-23')).toBeTruthy();
		expect(screen.getAllByText(/cta rate/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getAllByText(/signup intent rate/i).length).toBeGreaterThanOrEqual(1);
		expect(screen.getByRole('heading', { level: 2, name: /cta intent breakdown/i })).toBeTruthy();
		expect(screen.getByText(/start free/i)).toBeTruthy();
		expect(screen.getByText(/enterprise review/i)).toBeTruthy();
	});
});
