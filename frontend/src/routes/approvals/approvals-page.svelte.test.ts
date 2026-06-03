import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/svelte';

import Page from './+page.svelte';

const { getMock, postMock } = vi.hoisted(() => ({
	getMock: vi.fn(),
	postMock: vi.fn()
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
		get: (...args: unknown[]) => getMock(...args),
		post: (...args: unknown[]) => postMock(...args)
	}
}));

const EDGE_BASE = '/api/edge/api/v1';
const endpoint = (path: string): string => `${EDGE_BASE}${path}`;

function jsonResponse(payload: unknown, status = 200): Response {
	return new Response(JSON.stringify(payload), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

function pageData(tier = 'pro') {
	return {
		user: { id: 'user-1', email: 'reviewer@example.com' },
		session: { access_token: 'token' },
		subscription: { tier, status: 'active' },
		profile: { role: 'member', persona: 'platform' }
	};
}

const approval = {
	approval_id: '11111111-1111-1111-1111-111111111111',
	decision_id: '22222222-2222-2222-2222-222222222222',
	status: 'pending',
	source: 'terraform',
	environment: 'prod',
	project_id: 'core-platform',
	action: 'terraform.apply',
	resource_reference: 'module.app.aws_instance.web',
	estimated_monthly_delta_usd: '42.5000',
	reason_codes: ['approval_required', 'high_delta'],
	routing_rule_id: null,
	expires_at: '2026-02-01T12:00:00Z',
	created_at: '2026-02-01T10:00:00Z'
};

const routedApproval = {
	...approval,
	approval_id: '33333333-3333-3333-3333-333333333333',
	decision_id: '44444444-4444-4444-4444-444444444444',
	project_id: 'data-platform',
	action: 'budget.override',
	resource_reference: 'aws:budget/data-platform/monthly',
	estimated_monthly_delta_usd: '0',
	reason_codes: [],
	routing_rule_id: 'finops-approval',
	expires_at: '2026-02-01T13:00:00Z'
};

describe('approvals page', () => {
	beforeEach(() => {
		getMock.mockReset();
		postMock.mockReset();
	});

	afterEach(() => {
		cleanup();
	});

	it('renders upgrade state without loading queue for lower tiers', async () => {
		render(Page, { data: pageData('growth') as never });

		expect(await screen.findByText(/policy approvals require pro or enterprise/i)).toBeTruthy();
		expect(screen.getByRole('link', { name: /review plan/i })).toBeTruthy();
		expect(getMock).not.toHaveBeenCalled();
	});

	it('loads reviewer-visible approvals and refreshes the queue', async () => {
		getMock.mockResolvedValue(jsonResponse([approval]));

		render(Page, { data: pageData() as never });

		expect(await screen.findByRole('heading', { name: /approval queue/i })).toBeTruthy();
		expect(await screen.findByText('module.app.aws_instance.web')).toBeTruthy();
		expect(screen.getAllByText('$42.50').length).toBeGreaterThanOrEqual(1);
		expect(screen.getByRole('button', { name: /^cost impact\s+1$/i })).toBeTruthy();

		await waitFor(() => {
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/enforcement/approvals/queue?limit=50'),
				expect.objectContaining({
					headers: { Authorization: 'Bearer token' },
					timeoutMs: 8000
				})
			);
		});

		await fireEvent.click(screen.getByRole('button', { name: /refresh approval queue/i }));
		await waitFor(() => {
			expect(getMock).toHaveBeenCalledTimes(2);
		});
	});

	it('filters approvals using only fields provided by the production queue contract', async () => {
		getMock.mockResolvedValue(jsonResponse([approval, routedApproval]));

		render(Page, { data: pageData() as never });

		expect(await screen.findByText('module.app.aws_instance.web')).toBeTruthy();
		expect(await screen.findByText('aws:budget/data-platform/monthly')).toBeTruthy();

		await fireEvent.click(screen.getByRole('button', { name: /routed/i }));

		expect(screen.queryByText('module.app.aws_instance.web')).toBeNull();
		expect(screen.getByText('aws:budget/data-platform/monthly')).toBeTruthy();
		expect(screen.queryByRole('button', { name: /ask a question/i })).toBeNull();
		expect(screen.queryByRole('link', { name: /full details/i })).toBeNull();
	});

	it('approves and removes a queue item with a real API decision call', async () => {
		getMock.mockResolvedValue(jsonResponse([approval]));
		postMock.mockResolvedValue(jsonResponse({ status: 'approved' }));

		render(Page, { data: pageData('enterprise') as never });

		await screen.findByText('module.app.aws_instance.web');
		await fireEvent.click(screen.getByRole('button', { name: /^approve$/i }));

		await waitFor(() => {
			expect(postMock).toHaveBeenCalledWith(
				endpoint('/enforcement/approvals/11111111-1111-1111-1111-111111111111/approve'),
				{ notes: 'frontend_approve' },
				expect.objectContaining({
					headers: { Authorization: 'Bearer token' },
					timeoutMs: 8000
				})
			);
		});
		expect(
			await screen.findByText(/approval approved for module.app.aws_instance.web/i)
		).toBeTruthy();
		await waitFor(() => {
			expect(screen.queryByText('module.app.aws_instance.web')).toBeNull();
		});
	});

	it('surfaces decision errors without removing the request', async () => {
		getMock.mockResolvedValue(jsonResponse([approval]));
		postMock.mockResolvedValue(
			jsonResponse({ detail: 'Requester cannot review own approval' }, 403)
		);

		render(Page, { data: pageData() as never });

		await screen.findByText('module.app.aws_instance.web');
		await fireEvent.click(screen.getByRole('button', { name: /^deny$/i }));

		expect((await screen.findByRole('alert')).textContent).toContain(
			'Requester cannot review own approval'
		);
		expect(screen.getByText('module.app.aws_instance.web')).toBeTruthy();
	});
});
