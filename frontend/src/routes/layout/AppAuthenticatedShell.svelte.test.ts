import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';
import type { Snippet } from 'svelte';
import AppAuthenticatedShell from './AppAuthenticatedShell.svelte';
import { AUTH_SESSION_SIGNAL_KEY } from '$lib/auth/authSessionSignal';
import { uiState } from '$lib/stores/ui.svelte';

const mocks = vi.hoisted(() => ({
	invalidate: vi.fn(),
	jobStore: {
		activeJobsCount: 0,
		init: vi.fn().mockResolvedValue(undefined),
		disconnect: vi.fn()
	}
}));

vi.mock('$app/environment', () => ({
	browser: true
}));

vi.mock('$app/navigation', () => ({
	invalidate: mocks.invalidate
}));

vi.mock('$lib/stores/jobs.svelte', () => ({
	jobStore: mocks.jobStore
}));

const emptySnippet = (() => '') as unknown as Snippet;

function renderShell() {
	render(AppAuthenticatedShell, {
		props: {
			user: { email: 'operator@example.com' },
			role: 'owner',
			platformOperator: false,
			subscription: { tier: 'growth' },
			primaryNavItems: [
				{
					href: '/dashboard',
					label: 'Dashboard',
					icon: 'M3 12l2-2 7-7 7 7 2 2'
				}
			],
			secondaryNavItems: [{ href: '/llm', label: 'LLM Usage', icon: 'M9 9v6h6V9H9Z' }],
			activeSecondaryNavItems: [],
			persona: 'finops',
			toAppPath: (path: string) => path,
			isActive: (href: string) => href === '/dashboard',
			children: emptySnippet
		}
	});
}

describe('AppAuthenticatedShell', () => {
	beforeEach(() => {
		Object.defineProperty(window, 'matchMedia', {
			configurable: true,
			value: vi.fn().mockReturnValue({
				matches: false,
				addEventListener: vi.fn(),
				removeEventListener: vi.fn()
			})
		});
		window.localStorage.clear();
		mocks.invalidate.mockClear();
		mocks.jobStore.init.mockClear();
		mocks.jobStore.disconnect.mockClear();
	});

	afterEach(() => {
		cleanup();
		uiState.isCommandPaletteOpen = false;
		uiState.isSidebarOpen = true;
		uiState.toasts = [];
	});

	it('lazy-loads and opens the command palette on demand', async () => {
		renderShell();

		await fireEvent.click(screen.getByRole('button', { name: /open command palette/i }));

		expect(
			await screen.findByRole('dialog', {
				name: /command palette/i
			})
		).toBeTruthy();
		expect(screen.getByPlaceholderText(/search actions, routes, or documentation/i)).toBeTruthy();
	});

	it('revalidates auth state on focus and storage signals without loading the browser auth client', async () => {
		renderShell();

		window.dispatchEvent(new Event('focus'));
		window.dispatchEvent(
			new StorageEvent('storage', {
				key: AUTH_SESSION_SIGNAL_KEY,
				newValue: String(Date.now())
			})
		);

		await waitFor(() => {
			expect(mocks.invalidate).toHaveBeenCalledWith('supabase:auth');
		});
	});
});
