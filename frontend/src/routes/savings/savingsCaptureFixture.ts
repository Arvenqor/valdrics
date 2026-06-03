import type {
	RealizedSavingsEvent,
	SavingsProofDrilldownResponse,
	SavingsProofResponse
} from './savingsTypes';

export const savingsCaptureReport: SavingsProofResponse = {
	start_date: '2026-05-01',
	end_date: '2026-05-31',
	as_of: '2026-06-02T08:00:00Z',
	tier: 'pro',
	opportunity_monthly_usd: 18420,
	realized_monthly_usd: 7240,
	open_recommendations: 7,
	applied_recommendations: 5,
	pending_remediations: 3,
	completed_remediations: 9,
	breakdown: [
		{
			provider: 'aws',
			opportunity_monthly_usd: 11260,
			realized_monthly_usd: 4320,
			open_recommendations: 4,
			applied_recommendations: 3,
			pending_remediations: 2,
			completed_remediations: 5
		},
		{
			provider: 'azure',
			opportunity_monthly_usd: 3820,
			realized_monthly_usd: 1710,
			open_recommendations: 1,
			applied_recommendations: 1,
			pending_remediations: 1,
			completed_remediations: 2
		},
		{
			provider: 'saas',
			opportunity_monthly_usd: 2180,
			realized_monthly_usd: 940,
			open_recommendations: 1,
			applied_recommendations: 1,
			pending_remediations: 0,
			completed_remediations: 1
		},
		{
			provider: 'license',
			opportunity_monthly_usd: 1160,
			realized_monthly_usd: 270,
			open_recommendations: 1,
			applied_recommendations: 0,
			pending_remediations: 0,
			completed_remediations: 1
		}
	],
	notes: [
		'Opportunity includes open recommendations and pending remediations in the selected window.',
		'Realized savings are derived from applied recommendations and completed remediation evidence.'
	]
};

export const savingsCaptureDrilldown: SavingsProofDrilldownResponse = {
	start_date: savingsCaptureReport.start_date,
	end_date: savingsCaptureReport.end_date,
	as_of: savingsCaptureReport.as_of,
	tier: savingsCaptureReport.tier,
	provider: null,
	dimension: 'strategy_type',
	opportunity_monthly_usd: savingsCaptureReport.opportunity_monthly_usd,
	realized_monthly_usd: savingsCaptureReport.realized_monthly_usd,
	buckets: [
		{
			key: 'rightsizing',
			opportunity_monthly_usd: 8120,
			realized_monthly_usd: 2860,
			open_recommendations: 3,
			applied_recommendations: 2,
			pending_remediations: 1,
			completed_remediations: 4
		},
		{
			key: 'idle_resource_cleanup',
			opportunity_monthly_usd: 5240,
			realized_monthly_usd: 2980,
			open_recommendations: 2,
			applied_recommendations: 2,
			pending_remediations: 1,
			completed_remediations: 3
		},
		{
			key: 'license_reclamation',
			opportunity_monthly_usd: 3060,
			realized_monthly_usd: 1400,
			open_recommendations: 2,
			applied_recommendations: 1,
			pending_remediations: 1,
			completed_remediations: 2
		}
	],
	truncated: false,
	limit: 50,
	notes: ['Grouped by strategy type.']
};

export const savingsCaptureRealizedEvents: RealizedSavingsEvent[] = [
	{
		remediation_request_id: '7fb0b34e-9474-4f0f-83dc-4f91d9bd62b1',
		finding_id: 'b5bbf6be-1374-48ad-a36d-6a8139c42003',
		finding_category: 'idle_instances',
		provider: 'aws',
		account_id: 'acct-prod-01',
		resource_id: 'i-0ac9e73d42f9187f2',
		region: 'us-east-1',
		method: 'ledger_delta_avg_daily_v1',
		executed_at: '2026-05-29T14:20:00Z',
		baseline_start_date: '2026-05-01',
		baseline_end_date: '2026-05-14',
		measurement_start_date: '2026-05-15',
		measurement_end_date: '2026-05-31',
		baseline_avg_daily_cost_usd: 96,
		measurement_avg_daily_cost_usd: 41,
		realized_monthly_savings_usd: 1650,
		confidence_score: 0.93,
		computed_at: '2026-06-02T08:00:00Z'
	},
	{
		remediation_request_id: 'd49ee673-dbc0-45f0-9f34-a626d9e71c33',
		finding_id: '2d409eb5-0ab1-41e8-bb66-3cb076318503',
		finding_category: 'unattached_volumes',
		provider: 'azure',
		account_id: 'acct-azure-core',
		resource_id: 'disk-ledger-archive-019',
		region: 'eastus',
		method: 'ledger_delta_avg_daily_v1',
		executed_at: '2026-05-27T09:40:00Z',
		baseline_start_date: '2026-05-01',
		baseline_end_date: '2026-05-12',
		measurement_start_date: '2026-05-13',
		measurement_end_date: '2026-05-31',
		baseline_avg_daily_cost_usd: 48,
		measurement_avg_daily_cost_usd: 19,
		realized_monthly_savings_usd: 870,
		confidence_score: 0.88,
		computed_at: '2026-06-02T08:00:00Z'
	},
	{
		remediation_request_id: 'a38bdf2c-f623-4d50-90e9-526e1c65cda0',
		finding_id: null,
		finding_category: 'license_reclamation',
		provider: 'saas',
		account_id: 'okta-workspace',
		resource_id: 'notion-seat-pool',
		region: null,
		method: 'licensed_seat_delta_v1',
		executed_at: '2026-05-25T16:15:00Z',
		baseline_start_date: '2026-05-01',
		baseline_end_date: '2026-05-10',
		measurement_start_date: '2026-05-11',
		measurement_end_date: '2026-05-31',
		baseline_avg_daily_cost_usd: 28,
		measurement_avg_daily_cost_usd: 9,
		realized_monthly_savings_usd: 570,
		confidence_score: 0.81,
		computed_at: '2026-06-02T08:00:00Z'
	}
];
