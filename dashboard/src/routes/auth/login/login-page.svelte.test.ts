import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';

import LoginPage from './+page.svelte';

type PageState = { url: URL };

function createPageStore(initial: PageState) {
	let value = initial;
	const subscribers = new Set<(next: PageState) => void>();
	return {
		subscribe(run: (next: PageState) => void) {
			run(value);
			subscribers.add(run);
			return () => subscribers.delete(run);
		},
		set(next: PageState) {
			value = next;
			for (const subscriber of subscribers) {
				subscriber(next);
			}
		}
	};
}

const mocks = vi.hoisted(() => {
	const pageStore = createPageStore({ url: new URL('https://example.com/auth/login') });
	return {
		pageStore,
		goto: vi.fn(),
		invalidateAll: vi.fn(),
		fetch: vi.fn()
	};
});

vi.mock('$app/stores', () => ({
	page: mocks.pageStore
}));

vi.mock('$app/navigation', () => ({
	goto: mocks.goto,
	invalidateAll: mocks.invalidateAll
}));

vi.mock('$app/paths', () => ({
	base: ''
}));

vi.mock('$lib/edgeProxy', () => ({
	edgeApiPath: (path: string) => `/api/edge${path}`
}));

vi.mock('$lib/security/turnstile', () => ({
	getTurnstileToken: vi.fn().mockResolvedValue(null)
}));

vi.mock('$lib/landing/landingTelemetry', () => ({
	emitLandingTelemetry: vi.fn()
}));

describe('auth login page conversion flow', () => {
	beforeEach(() => {
		cleanup();
		mocks.pageStore.set({ url: new URL('https://example.com/auth/login') });
		mocks.goto.mockReset();
		mocks.invalidateAll.mockReset();
		mocks.fetch.mockReset();
		mocks.fetch.mockResolvedValue(
			new Response(JSON.stringify({ ok: true }), {
				status: 200,
				headers: { 'Content-Type': 'application/json' }
			})
		);
		vi.stubGlobal('fetch', mocks.fetch);
	});

	afterEach(() => {
		vi.unstubAllGlobals();
	});

	it('auto-enters signup mode and surfaces intent/persona context from landing params', () => {
		mocks.pageStore.set({
			url: new URL(
				'https://example.com/auth/login?intent=roi_assessment&persona=cfo&utm_source=google'
			)
		});
		render(LoginPage);

		expect(screen.getByRole('heading', { level: 1, name: /create your account/i })).toBeTruthy();
		expect(screen.getByText(/Starting with/i)).toBeTruthy();
		expect(screen.getByText(/ROI Assessment/i)).toBeTruthy();
		expect(screen.getByText(/CFO/i)).toBeTruthy();
		expect(screen.getByRole('button', { name: /send secure signup link/i })).toBeTruthy();
	});

	it('logs in with password and redirects to onboarding context when intent is present', async () => {
		mocks.pageStore.set({
			url: new URL(
				'https://example.com/auth/login?mode=login&intent=engineering_control&persona=cto'
			)
		});
		render(LoginPage);

		const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;
		const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;
		await fireEvent.input(emailInput, { target: { value: 'user@example.com' } });
		await fireEvent.input(passwordInput, { target: { value: 'TopSecret123' } });

		await fireEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

		await waitFor(() => {
			expect(mocks.fetch).toHaveBeenCalledTimes(1);
			expect(mocks.invalidateAll).toHaveBeenCalledOnce();
			expect(mocks.goto).toHaveBeenCalledWith('/onboarding?intent=engineering_control&persona=cto');
		});
		expect(mocks.fetch.mock.calls[0]?.[0]).toBe('/auth/flow');
		const requestInit = mocks.fetch.mock.calls[0]?.[1] as RequestInit;
		expect(requestInit.method).toBe('POST');
		expect(requestInit.credentials).toBe('include');
		expect(JSON.parse(String(requestInit.body))).toEqual({
			action: 'password-login',
			email: 'user@example.com',
			password: 'TopSecret123'
		});
	});

	it('sends secure magic links with callback redirect and context-preserving next path', async () => {
		mocks.pageStore.set({
			url: new URL(
				'https://example.com/auth/login?intent=roi_assessment&persona=cfo&utm_source=google&utm_medium=cpc'
			)
		});
		render(LoginPage);

		const emailInput = screen.getByLabelText(/email address/i) as HTMLInputElement;
		await fireEvent.input(emailInput, { target: { value: 'FOUNDER@EXAMPLE.COM' } });

		await fireEvent.click(screen.getByRole('button', { name: /send secure signup link/i }));

		await waitFor(() => {
			expect(mocks.fetch).toHaveBeenCalledTimes(1);
		});
		const requestInit = mocks.fetch.mock.calls[0]?.[1] as RequestInit;
		const payload = JSON.parse(String(requestInit.body)) as {
			email: string;
			shouldCreateUser?: boolean;
			emailRedirectTo?: string;
		};
		expect(payload.email).toBe('founder@example.com');
		expect(payload.shouldCreateUser).toBe(true);
		expect(payload.emailRedirectTo).toContain(
			'/auth/callback?next=%2Froi-planner%3Fintent%3Droi_assessment'
		);
		expect((await screen.findByRole('status')).textContent).toMatch(/Secure sign-in link sent/i);
	});

	it('keeps the public auth page free of inline style attributes', () => {
		const file = resolve(process.cwd(), 'src/routes/auth/login/+page.svelte');
		const contents = readFileSync(file, 'utf8');
		expect(contents).not.toMatch(/style\s*=/);
	});
});
