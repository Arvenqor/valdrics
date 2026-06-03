import { describe, expect, it } from 'vitest';

import { buildDashboardOverview } from './dashboardOverviewModel';

describe('dashboard overview model', () => {
	it('normalizes leadership, daily spend, approvals, and zombie data without invented values', () => {
		const overview = buildDashboardOverview({
			periodLabel: '30-Day',
			provider: '',
			costs: { total_cost: 999 },
			carbon: { total_co2_kg: 12 },
			zombies: {
				total_monthly_waste: 45,
				idle_instances: [{ resource_id: 'i-1' }],
				old_snapshots: [{ resource_id: 'snap-1' }]
			},
			leadershipKpis: {
				total_cost_usd: 120,
				cost_by_provider: { aws: 90, azure: 30 },
				top_services: [
					{ service: 'EC2', cost_usd: 80 },
					{ service: 'Azure VM', cost_usd: '20.50' }
				],
				carbon_total_kgco2e: 4,
				carbon_coverage_percent: 75,
				savings_opportunity_monthly_usd: 300,
				savings_realized_monthly_usd: 100,
				open_recommendations: 3,
				applied_recommendations: 1,
				pending_remediations: 2,
				completed_remediations: 6,
				security_high_risk_decisions: 2,
				security_approval_required_decisions: 4,
				security_anomaly_signal_decisions: 1,
				notes: ['Savings proof uses ledger-backed evidence.']
			},
			dailyCosts: {
				points: [
					{ date: '2026-01-02', provider: 'aws', cost_usd: 30, carbon_kgco2e: 1 },
					{ date: '2026-01-01', provider: 'aws', cost_usd: 10, carbon_kgco2e: 0.2 },
					{ date: '2026-01-01', provider: 'azure', cost_usd: 20, carbon_kgco2e: 0.8 }
				]
			},
			approvalsQueue: [
				{
					approval_id: 'approval-2',
					action: 'resize_instance',
					environment: 'prod',
					resource_reference: 'i-prod',
					estimated_monthly_delta_usd: '50',
					expires_at: '2026-01-20T00:00:00Z',
					reason_codes: ['high_delta']
				},
				{
					approval_id: 'approval-1',
					action: 'delete_snapshot',
					environment: 'dev',
					resource_reference: 'snap-dev',
					estimated_monthly_delta_usd: 10,
					expires_at: '2026-01-10T00:00:00Z',
					reason_codes: ['stale']
				}
			]
		});

		expect(overview.totalSpendUsd).toBe(120);
		expect(overview.carbonTotalKgco2e).toBe(4);
		expect(overview.dailySpend).toEqual([
			{ date: '2026-01-01', costUsd: 30, carbonKgco2e: 1 },
			{ date: '2026-01-02', costUsd: 30, carbonKgco2e: 1 }
		]);
		expect(overview.cloudBreakdown.map((provider) => provider.label)).toEqual(['AWS', 'Azure']);
		expect(overview.cloudBreakdown[0].share).toBe(75);
		expect(overview.approvals.pendingCount).toBe(2);
		expect(overview.approvals.monthlyDeltaUsd).toBe(60);
		expect(overview.approvals.items[0].id).toBe('approval-1');
		expect(overview.zombieCount).toBe(2);
		expect(overview.monthlyWasteUsd).toBe(45);
		expect(overview.policyHealth.metrics.map((metric) => metric.value)).toEqual([75, 25, 75]);
		expect(overview.savings.executionPercent).toBe(25);
		expect(overview.notes).toEqual(['Savings proof uses ledger-backed evidence.']);
	});

	it('keeps unavailable governance percentages null when source evidence is absent', () => {
		const overview = buildDashboardOverview({
			periodLabel: 'Period',
			provider: 'ai',
			costs: { total_cost: 12 },
			carbon: null,
			zombies: null,
			leadershipKpis: null,
			dailyCosts: null,
			approvalsQueue: null
		});

		expect(overview.provider).toBe('ai');
		expect(overview.totalSpendUsd).toBe(12);
		expect(overview.dailySpend).toEqual([]);
		expect(overview.cloudBreakdown).toEqual([]);
		expect(overview.policyHealth.metrics.map((metric) => metric.value)).toEqual([null, null, null]);
		expect(overview.savings.executionPercent).toBeNull();
		expect(overview.approvals.pendingCount).toBe(0);
	});

	it('treats zero-valued leadership totals as real values instead of falling back', () => {
		const overview = buildDashboardOverview({
			periodLabel: 'Period',
			costs: { total_cost: 999 },
			carbon: { total_co2_kg: 99 },
			leadershipKpis: {
				total_cost_usd: 0,
				carbon_total_kgco2e: 0,
				cost_by_provider: {},
				top_services: []
			},
			dailyCosts: null,
			zombies: null,
			approvalsQueue: null
		});

		expect(overview.totalSpendUsd).toBe(0);
		expect(overview.carbonTotalKgco2e).toBe(0);
	});
});
