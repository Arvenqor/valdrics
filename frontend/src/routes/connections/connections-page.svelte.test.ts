import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/svelte';
import { getUpgradePrompt } from '$lib/pricing/upgradePrompt';
import Page from './+page.svelte';
import type { PageData } from './$types';
import { TimeoutError } from '$lib/fetchWithTimeout';

const { getMock, postMock, deleteMock } = vi.hoisted(() => ({
	getMock: vi.fn(),
	postMock: vi.fn(),
	deleteMock: vi.fn()
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

vi.mock('$lib/api', () => ({
	api: {
		get: (...args: unknown[]) => getMock(...args),
		post: (...args: unknown[]) => postMock(...args),
		delete: (...args: unknown[]) => deleteMock(...args)
	}
}));

function jsonResponse(payload: unknown, status = 200): Response {
	return new Response(JSON.stringify(payload), {
		status,
		headers: { 'Content-Type': 'application/json' }
	});
}

const EDGE_BASE = '/api/edge/api/v1';
const endpoint = (path: string): string => `${EDGE_BASE}${path}`;

function pageData(tier: string = 'pro'): PageData {
	return {
		user: { id: 'user-id', tenant_id: 'tenant-id' },
		session: { access_token: 'token' },
		subscription: { tier, status: 'active' }
	} as unknown as PageData;
}

function setupGetDefaults() {
	getMock.mockImplementation(async (url: string) => {
		const path = String(url);
		if (path === endpoint('/settings/connections/aws')) {
			return jsonResponse([
				{
					id: 'aws-conn-1',
					provider: 'aws',
					aws_account_id: '123456789012',
					status: 'active',
					is_management_account: false
				}
			]);
		}
		if (
			[
				endpoint('/settings/connections/azure'),
				endpoint('/settings/connections/gcp'),
				endpoint('/settings/connections/saas'),
				endpoint('/settings/connections/license'),
				endpoint('/settings/connections/platform'),
				endpoint('/settings/connections/hybrid')
			].includes(path)
		) {
			return jsonResponse([]);
		}
		if (path === endpoint('/settings/connections/aws/discovered')) {
			return jsonResponse([]);
		}
		return jsonResponse({}, 404);
	});
}

function setupGetEmpty() {
	getMock.mockImplementation(async (url: string) => {
		const path = String(url);
		if (
			[
				endpoint('/settings/connections/aws'),
				endpoint('/settings/connections/azure'),
				endpoint('/settings/connections/gcp'),
				endpoint('/settings/connections/saas'),
				endpoint('/settings/connections/license'),
				endpoint('/settings/connections/platform'),
				endpoint('/settings/connections/hybrid'),
				endpoint('/settings/connections/aws/discovered')
			].includes(path)
		) {
			return jsonResponse([]);
		}
		return jsonResponse({}, 404);
	});
}

function setupGetConnectedInventory() {
	getMock.mockImplementation(async (url: string) => {
		const path = String(url);
		if (path === endpoint('/settings/connections/aws')) {
			return jsonResponse([
				{
					id: 'aws-mgmt-1',
					provider: 'aws',
					aws_account_id: '123456789012',
					status: 'active',
					is_management_account: true,
					organization_id: 'o-valdrics1'
				}
			]);
		}
		if (path === endpoint('/settings/connections/azure')) {
			return jsonResponse([
				{
					id: 'azure-conn-1',
					provider: 'azure',
					name: 'Azure Production',
					subscription_id: 'sub-prod-001',
					azure_tenant_id: 'tenant-prod',
					is_active: true
				}
			]);
		}
		if (path === endpoint('/settings/connections/gcp')) {
			return jsonResponse([
				{
					id: 'gcp-conn-1',
					provider: 'gcp',
					name: 'GCP FinOps',
					project_id: 'valdrics-prod',
					auth_method: 'workload_identity',
					is_active: false
				}
			]);
		}
		if (path === endpoint('/settings/connections/saas')) {
			return jsonResponse([
				{
					id: 'saas-conn-1',
					provider: 'saas',
					name: 'Stripe Billing',
					vendor: 'stripe',
					auth_method: 'api_key',
					is_active: true
				}
			]);
		}
		if (path === endpoint('/settings/connections/license')) {
			return jsonResponse([
				{
					id: 'license-conn-1',
					provider: 'license',
					name: 'Microsoft 365',
					vendor: 'microsoft_365',
					auth_method: 'oauth',
					is_active: false
				}
			]);
		}
		if (path === endpoint('/settings/connections/platform')) {
			return jsonResponse([
				{
					id: 'platform-conn-1',
					provider: 'platform',
					name: 'Shared Platform Ledger',
					vendor: 'ledger_http',
					auth_method: 'api_key',
					is_active: true
				}
			]);
		}
		if (path === endpoint('/settings/connections/hybrid')) {
			return jsonResponse([
				{
					id: 'hybrid-conn-1',
					provider: 'hybrid',
					name: 'Datacenter Ledger',
					vendor: 'vmware',
					auth_method: 'api_key',
					is_active: true
				}
			]);
		}
		if (path === endpoint('/settings/connections/aws/discovered')) {
			return jsonResponse([
				{
					id: 'disc-1',
					account_id: '210987654321',
					name: 'Platform Sandbox',
					email: 'platform@example.com',
					status: 'discovered'
				},
				{
					id: 'disc-2',
					account_id: '210987654322',
					name: 'Finance Production',
					email: 'finance@example.com',
					status: 'linked'
				}
			]);
		}
		return jsonResponse({}, 404);
	});
}

function setupPostDefaults() {
	postMock.mockImplementation(async (url: string) => {
		const path = String(url);
		if (path === endpoint('/settings/connections/saas')) {
			return jsonResponse({ id: 'saas-conn-1' });
		}
		if (path === endpoint('/settings/connections/saas/saas-conn-1/verify')) {
			return jsonResponse({ status: 'success' });
		}
		return jsonResponse({ status: 'ok' });
	});
}

describe('connections page API wiring', () => {
	beforeEach(() => {
		getMock.mockReset();
		postMock.mockReset();
		deleteMock.mockReset();
		setupGetDefaults();
		setupPostDefaults();
		vi.spyOn(window, 'confirm').mockReturnValue(true);
	});

	afterEach(() => {
		cleanup();
		vi.restoreAllMocks();
	});

	it('loads cloud connection sections via edge proxy paths', async () => {
		render(Page, { data: pageData('enterprise') });
		await screen.findByText('Cloud Accounts');

		await waitFor(() => {
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/aws'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/azure'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/gcp'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/saas'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/license'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/platform'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
			expect(getMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/hybrid'),
				expect.objectContaining({ headers: expect.any(Object), timeoutMs: 8000 })
			);
		});
	});

	it('shows an empty inventory source registry when no connectors exist', async () => {
		setupGetEmpty();
		render(Page, { data: pageData('enterprise') });

		await screen.findByText('Inventory source registry');
		await screen.findByText('No inventory sources connected');
		expect(document.body.textContent || '').toContain('Connect an inventory source');
	});

	it('reconciles connected cloud, software, license, platform, hybrid, and org sources', async () => {
		setupGetConnectedInventory();
		render(Page, { data: pageData('enterprise') });

		await screen.findByText('Inventory source registry');
		await screen.findByText('AWS account 123456789012');
		await screen.findByText('Azure Production');
		await screen.findByText('GCP FinOps');
		await screen.findByText('Stripe Billing');
		await screen.findByText('Microsoft 365');
		await screen.findByText('Shared Platform Ledger');
		await screen.findByText('Datacenter Ledger');
		expect((await screen.findAllByText('Platform Sandbox')).length).toBeGreaterThanOrEqual(1);
		expect(document.body.textContent || '').toContain('1 / 2');
		expect(document.body.textContent || '').toContain('Pending verification');
	});

	it('shows failed connection section loads in the source registry page notice', async () => {
		getMock.mockImplementation(async (url: string) => {
			const path = String(url);
			if (path === endpoint('/settings/connections/gcp')) {
				return jsonResponse({ detail: 'GCP unavailable' }, 500);
			}
			if (
				[
					endpoint('/settings/connections/aws'),
					endpoint('/settings/connections/azure'),
					endpoint('/settings/connections/saas'),
					endpoint('/settings/connections/license'),
					endpoint('/settings/connections/platform'),
					endpoint('/settings/connections/hybrid'),
					endpoint('/settings/connections/aws/discovered')
				].includes(path)
			) {
				return jsonResponse([]);
			}
			return jsonResponse({}, 404);
		});

		render(Page, { data: pageData('enterprise') });
		expect(await screen.findByText('Inventory source registry')).toBeTruthy();
		expect(await screen.findByText('1 connection section could not be loaded.')).toBeTruthy();
	});

	it('creates and verifies SaaS connector through edge proxy write endpoints', async () => {
		render(Page, { data: pageData('pro') });
		await screen.findByText('Create SaaS connector');
		const saasSummary = screen.getByText('Create SaaS connector');
		const saasPanel = saasSummary.closest('details');
		expect(saasPanel).toBeTruthy();

		await fireEvent.click(saasSummary);
		await fireEvent.input(
			within(saasPanel as HTMLElement).getByPlaceholderText(
				'Connection name (e.g. Stripe Billing)'
			),
			{
				target: { value: 'Stripe Prod' }
			}
		);
		await fireEvent.input(
			within(saasPanel as HTMLElement).getByPlaceholderText('Vendor (stripe, salesforce, etc.)'),
			{
				target: { value: 'stripe' }
			}
		);
		await fireEvent.input(
			within(saasPanel as HTMLElement).getByPlaceholderText('API key / OAuth token'),
			{
				target: { value: 'saas-api-key' }
			}
		);

		await fireEvent.click(
			within(saasPanel as HTMLElement).getByRole('button', {
				name: /Create & Verify SaaS Connector/i
			})
		);

		await waitFor(() => {
			expect(postMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/saas'),
				expect.objectContaining({ name: 'Stripe Prod', vendor: 'stripe' }),
				expect.objectContaining({ headers: expect.any(Object) })
			);
			expect(postMock).toHaveBeenCalledWith(
				endpoint('/settings/connections/saas/saas-conn-1/verify'),
				{},
				expect.objectContaining({ headers: expect.any(Object) })
			);
		});
		await screen.findByText('SAAS connection created and verified.');
	});

	it('shows timeout and write error states from connection APIs', async () => {
		setupGetDefaults();
		getMock.mockImplementationOnce(async () => {
			throw new TimeoutError(8000);
		});
		postMock.mockImplementation(async (url: string) => {
			if (String(url) === endpoint('/settings/connections/saas')) {
				return jsonResponse({ detail: 'SaaS connector validation failed' }, 400);
			}
			return jsonResponse({ status: 'ok' });
		});

		render(Page, { data: pageData('enterprise') });
		await screen.findByText('Cloud Accounts');
		await screen.findByText(/connection sections timed out/i);
		const saasSummary = await screen.findByText('Create SaaS connector');
		const saasPanel = saasSummary.closest('details');
		expect(saasPanel).toBeTruthy();

		await fireEvent.click(saasSummary);
		await fireEvent.input(
			within(saasPanel as HTMLElement).getByPlaceholderText(
				'Connection name (e.g. Stripe Billing)'
			),
			{
				target: { value: 'Stripe QA' }
			}
		);
		await fireEvent.input(
			within(saasPanel as HTMLElement).getByPlaceholderText('API key / OAuth token'),
			{
				target: { value: 'bad-key' }
			}
		);
		await fireEvent.click(
			within(saasPanel as HTMLElement).getByRole('button', {
				name: /Create & Verify SaaS Connector/i
			})
		);
		await screen.findByText('SaaS connector validation failed');
	});

	it('shows starter plan prompts for cross-cloud expansion on lower tiers', async () => {
		const starterUpgradePrompt = getUpgradePrompt('starter', 'Azure and GCP coverage');
		render(Page, { data: pageData('free') });
		await screen.findByText('Cloud Accounts');
		await screen.findAllByRole('link', { name: /View Starter plan/i });

		expect(document.body.textContent || '').toContain(starterUpgradePrompt.body);
		expect(screen.getAllByRole('link', { name: /View Starter plan/i }).length).toBeGreaterThan(0);
	});

	it('shows direct Azure and GCP connect actions on starter tier', async () => {
		render(Page, { data: pageData('starter') });
		await screen.findByText('Cloud Accounts');
		await waitFor(() => {
			expect(screen.getByRole('link', { name: 'Connect Azure' })).toBeTruthy();
			expect(screen.getByRole('link', { name: 'Connect GCP' })).toBeTruthy();
		});
	});

	it('shows pro plan prompts for cloud-plus connectors before pro', async () => {
		const proUpgradePrompt = getUpgradePrompt('pro', 'Cloud+ connectors');
		render(Page, { data: pageData('growth') });
		await screen.findByText('Cloud Accounts');
		await screen.findAllByRole('link', { name: /View Pro plan/i });

		expect(document.body.textContent || '').toContain(proUpgradePrompt.body);
		expect(document.body.textContent || '').toContain(
			'Cloud+ source feeds require Pro tier or higher'
		);
		expect(screen.getAllByRole('link', { name: /View Pro plan/i }).length).toBeGreaterThan(0);
	});
});
