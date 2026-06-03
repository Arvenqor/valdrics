import type { InventoryListResponse } from './inventoryTypes';

export const inventoryCaptureResponse: InventoryListResponse = {
	items: [
		{
			id: 'conn:aws:11111111-1111-4111-8111-111111111111',
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
			tags: {
				organization_id: 'o-valdrics',
				cur_status: 'active'
			},
			source_kind: 'connection',
			source_connection_id: '11111111-1111-4111-8111-111111111111',
			source_label: 'AWS connection'
		},
		{
			id: 'feed:saas:22222222-2222-4222-8222-222222222222:0',
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
			tags: {
				cost_center: 'fin'
			},
			source_kind: 'feed',
			source_connection_id: '22222222-2222-4222-8222-222222222222',
			source_label: 'SaaS spend feed'
		},
		{
			id: 'feed:license:33333333-3333-4333-8333-333333333333:0',
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
			source_connection_id: '33333333-3333-4333-8333-333333333333',
			source_label: 'License feed'
		},
		{
			id: 'feed:hybrid:44444444-4444-4444-8444-444444444444:0',
			name: 'DC Core',
			resource_type: 'service',
			provider: 'datacenter',
			region: 'dc-lagos-1',
			owner_name: 'Platform Reliability',
			owner_email: null,
			team_name: 'Platform',
			monthly_cost: 1250.5,
			cost_basis: 'reported_cost_usd',
			status: 'active',
			last_seen_at: '2026-06-01T12:00:00Z',
			tags: {},
			source_kind: 'feed',
			source_connection_id: '44444444-4444-4444-8444-444444444444',
			source_label: 'Hybrid infrastructure feed'
		},
		{
			id: 'disc:aws:55555555-5555-4555-8555-555555555555',
			name: 'Platform Sandbox',
			resource_type: 'cloud',
			provider: 'aws',
			region: 'global',
			owner_name: null,
			owner_email: null,
			team_name: null,
			monthly_cost: 0,
			cost_basis: 'not_reported',
			status: 'pending',
			last_seen_at: '2026-06-02T07:30:00Z',
			tags: {
				account_id: '210987654321',
				discovery_status: 'discovered'
			},
			source_kind: 'discovered_account',
			source_connection_id: '11111111-1111-4111-8111-111111111111',
			source_label: 'AWS Organizations discovery'
		}
	],
	total: 5,
	page: 1,
	per_page: 40,
	type: 'all',
	status: 'all',
	search: '',
	summary: {
		total: 5,
		cloud: 2,
		software: 2,
		service: 1,
		active: 3,
		pending: 1,
		error: 0,
		idle: 0,
		shadow: 0,
		expiring: 1,
		unowned: 3,
		source_count: 4,
		reported_cost_usd: 2680.75
	}
};
