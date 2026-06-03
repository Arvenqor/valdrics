import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/svelte';
import Page from './+page.svelte';
import type { PageData } from './$types';

const { getMock, gotoMock, loggerErrorMock } = vi.hoisted(() => ({
	getMock: vi.fn(),
	gotoMock: vi.fn(),
	loggerErrorMock: vi.fn()
}));

vi.mock('$env/static/public', () => ({
	PUBLIC_API_URL: 'https://api.test/api/v1'
}));

vi.mock('$env/dynamic/public', () => ({
	env: {
		PUBLIC_API_URL: 'https://api.test/api/v1'
	}
}));

vi.mock('$app/paths', () => ({
	base: ''
}));

vi.mock('$app/navigation', () => ({
	goto: (...args: unknown[]) => gotoMock(...args)
}));

vi.mock('$lib/api', () => ({
	api: {
		get: (...args: unknown[]) => getMock(...args)
	}
}));

vi.mock('$lib/logging/client', () => ({
	clientLogger: {
		error: (...args: unknown[]) => loggerErrorMock(...args)
	}
}));

function jsonResponse(payload: unknown, status = 200): Response {
	return new Response(JSON.stringify(payload), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

function pageData(overrides: Partial<PageData> = {}): PageData {
	return {
		user: { id: 'user-id', tenant_id: 'tenant-id' },
		session: { access_token: 'token' },
		subscription: { tier: 'pro', status: 'active' },
		inventoryType: 'all',
		inventoryStatus: 'all',
		inventorySearch: '',
		inventoryPage: 1,
		...overrides
	} as unknown as PageData;
}

const inventoryPayload = {
	items: [
		{
			id: 'conn:aws:aws-1',
			name: 'AWS account 123456789012',
			resource_type: 'cloud',
			provider: 'aws',
			region: 'us-east-1',
			owner_name: null,
			owner_email: null,
			team_name: null,
			monthly_cost: 0,
			cost_basis: 'not_reported',
			status: 'active',
			last_seen_at: '2026-06-02T08:30:00Z',
			tags: { organization_id: 'o-valdrics' },
			source_kind: 'connection',
			source_connection_id: 'aws-1',
			source_label: 'AWS connection'
		},
		{
			id: 'feed:saas:saas-1:0',
			name: 'Stripe API',
			resource_type: 'software',
			provider: 'stripe',
			region: null,
			owner_name: 'Finance Ops',
			owner_email: 'finops@example.com',
			team_name: 'Finance',
			monthly_cost: 980.25,
			cost_basis: 'monthly_cost_usd',
			status: 'active',
			last_seen_at: '2026-06-01T00:00:00Z',
			tags: { cost_center: 'fin' },
			source_kind: 'feed',
			source_connection_id: 'saas-1',
			source_label: 'SaaS spend feed'
		},
		{
			id: 'feed:license:license-1:0',
			name: 'M365 E5',
			resource_type: 'software',
			provider: 'microsoft_365',
			region: null,
			owner_name: null,
			owner_email: null,
			team_name: 'Corporate IT',
			monthly_cost: 450,
			cost_basis: 'reported_cost_usd',
			status: 'expiring',
			last_seen_at: '2026-05-30T00:00:00Z',
			tags: {},
			source_kind: 'feed',
			source_connection_id: 'license-1',
			source_label: 'License feed'
		}
	],
	total: 3,
	page: 1,
	per_page: 40,
	type: 'all',
	status: 'all',
	search: '',
	summary: {
		total: 3,
		cloud: 1,
		software: 2,
		service: 0,
		active: 2,
		pending: 0,
		error: 0,
		idle: 0,
		shadow: 0,
		expiring: 1,
		unowned: 2,
		source_count: 3,
		reported_cost_usd: 1430.25
	}
};

describe('inventory page', () => {
	afterEach(() => {
		cleanup();
		getMock.mockReset();
		gotoMock.mockReset();
		loggerErrorMock.mockReset();
		vi.useRealTimers();
	});

	it('loads inventory through the edge proxy and renders real rows', async () => {
		getMock.mockResolvedValue(jsonResponse(inventoryPayload));

		render(Page, { data: pageData() });

		await screen.findByText('Stripe API');
		expect(screen.getByText('AWS account 123456789012')).toBeTruthy();
		expect(screen.getByText('M365 E5')).toBeTruthy();
		expect(screen.getByText('$980.25/mo')).toBeTruthy();
		expect(screen.getByText('$450 reported')).toBeTruthy();
		expect(screen.getByText('Not reported')).toBeTruthy();
		expect(screen.getByText('License feed')).toBeTruthy();
		await waitFor(() => {
			expect(getMock).toHaveBeenCalledWith(
				'/api/edge/api/v1/inventory?type=all&status=all&page=1&per_page=40',
				expect.objectContaining({
					headers: expect.objectContaining({ Authorization: 'Bearer token' }),
					timeoutMs: 8000
				})
			);
		});
	});

	it('renders empty state from an empty backend response', async () => {
		getMock.mockResolvedValue(
			jsonResponse({
				items: [],
				total: 0,
				page: 1,
				per_page: 40,
				type: 'all',
				status: 'all',
				search: '',
				summary: {
					total: 0,
					cloud: 0,
					software: 0,
					service: 0,
					active: 0,
					pending: 0,
					error: 0,
					idle: 0,
					shadow: 0,
					expiring: 0,
					unowned: 0,
					source_count: 0,
					reported_cost_usd: 0
				}
			})
		);

		render(Page, { data: pageData() });

		await screen.findByText('No inventory resources yet');
		const emptyState = screen.getByText('No inventory resources yet').closest('section');
		expect(emptyState).toBeTruthy();
		expect(
			within(emptyState as HTMLElement).getByRole('link', { name: 'Connect sources' })
		).toBeTruthy();
	});

	it('shows backend errors without fabricating inventory rows', async () => {
		getMock.mockResolvedValue(jsonResponse({ detail: 'Inventory unavailable.' }, 503));

		render(Page, { data: pageData() });

		await screen.findByText('Inventory unavailable.');
		expect(screen.queryByText('Stripe API')).toBeNull();
		expect(loggerErrorMock).toHaveBeenCalled();
	});

	it('applies type and status filters through URL and API query params', async () => {
		getMock.mockResolvedValue(jsonResponse(inventoryPayload));

		render(Page, { data: pageData() });
		await screen.findByText('Stripe API');

		await fireEvent.click(screen.getByRole('tab', { name: 'Software' }));
		await waitFor(() => {
			expect(gotoMock).toHaveBeenLastCalledWith(
				'/inventory?type=software',
				expect.objectContaining({ keepFocus: true, noScroll: true, replaceState: true })
			);
			expect(getMock).toHaveBeenLastCalledWith(
				'/api/edge/api/v1/inventory?type=software&status=all&page=1&per_page=40',
				expect.objectContaining({ timeoutMs: 8000 })
			);
		});

		await fireEvent.click(screen.getByRole('tab', { name: 'Shadow IT' }));
		await waitFor(() => {
			expect(gotoMock).toHaveBeenLastCalledWith(
				'/inventory?status=shadow',
				expect.objectContaining({ keepFocus: true, noScroll: true, replaceState: true })
			);
			expect(getMock).toHaveBeenLastCalledWith(
				'/api/edge/api/v1/inventory?type=all&status=shadow&page=1&per_page=40',
				expect.objectContaining({ timeoutMs: 8000 })
			);
		});

		await fireEvent.click(screen.getByRole('tab', { name: 'Expiring Soon' }));
		await waitFor(() => {
			expect(gotoMock).toHaveBeenLastCalledWith(
				'/inventory?status=expiring',
				expect.objectContaining({ keepFocus: true, noScroll: true, replaceState: true })
			);
			expect(getMock).toHaveBeenLastCalledWith(
				'/api/edge/api/v1/inventory?type=all&status=expiring&page=1&per_page=40',
				expect.objectContaining({ timeoutMs: 8000 })
			);
		});

		await fireEvent.change(screen.getByLabelText('Status'), { target: { value: 'active' } });
		await waitFor(() => {
			expect(gotoMock).toHaveBeenLastCalledWith(
				'/inventory?status=active',
				expect.objectContaining({ keepFocus: true, noScroll: true, replaceState: true })
			);
		});
	});

	it('debounces search and keeps the search value visible', async () => {
		vi.useFakeTimers();
		getMock.mockResolvedValue(jsonResponse(inventoryPayload));

		render(Page, { data: pageData() });
		await screen.findByText('Stripe API');

		const search = screen.getByLabelText('Search asset inventory') as HTMLInputElement;
		await fireEvent.input(search, { target: { value: 'stripe' } });
		expect(search.value).toBe('stripe');
		expect(gotoMock).toHaveBeenLastCalledWith(
			'/inventory?q=stripe',
			expect.objectContaining({ keepFocus: true, noScroll: true, replaceState: true })
		);

		await vi.advanceTimersByTimeAsync(300);
		await waitFor(() => {
			expect(getMock).toHaveBeenLastCalledWith(
				'/api/edge/api/v1/inventory?type=all&status=all&page=1&per_page=40&q=stripe',
				expect.objectContaining({ timeoutMs: 8000 })
			);
		});
	});
});
