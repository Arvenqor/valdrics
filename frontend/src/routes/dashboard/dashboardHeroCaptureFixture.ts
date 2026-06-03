type DashboardCaptureFinding = {
	provider: 'aws' | 'azure' | 'gcp';
	finding_id: string;
	resource_id: string;
	resource_type: string;
	monthly_cost: string;
	confidence: 'high' | 'medium' | 'low';
	risk_if_deleted: 'high' | 'medium' | 'low';
	explanation: string;
	confidence_reason: string;
	recommended_action: string;
	connection_id: string;
	owner: string;
	confidence_score: number;
	explainability_notes: string;
	is_gpu?: boolean;
	instance_type?: string;
};

function formatDateOnly(value: Date): string {
	return value.toISOString().split('T')[0] ?? '';
}

function buildDefaultDateRange(): { startDate: string; endDate: string } {
	const end = new Date();
	const start = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
	return {
		startDate: formatDateOnly(start),
		endDate: formatDateOnly(end)
	};
}

const ENGINEERING_FINDINGS: DashboardCaptureFinding[] = [
	{
		provider: 'aws',
		finding_id: 'finding-ec2-idle-1',
		resource_id: 'i-0ac9e73d42f9187f2',
		resource_type: 'EC2 Instance',
		monthly_cost: '842.00',
		confidence: 'high',
		risk_if_deleted: 'medium',
		explanation:
			'Instance utilization stayed below 3% for 14 days, with no deployment tag activity or production traffic attached.',
		confidence_reason: 'Matched against CPU, network, ownership, and deployment history.',
		recommended_action: 'Resize to burstable class or stop outside production hours.',
		connection_id: 'conn-aws-prod',
		owner: 'platform@valdrics.com',
		confidence_score: 0.94,
		explainability_notes:
			'Cost, traffic, and ownership signals agree that this instance is materially underused.',
		instance_type: 'm6i.2xlarge'
	},
	{
		provider: 'aws',
		finding_id: 'finding-ebs-orphan-1',
		resource_id: 'vol-0473c1d239a6de91d',
		resource_type: 'EBS Volume',
		monthly_cost: '386.00',
		confidence: 'high',
		risk_if_deleted: 'low',
		explanation:
			'Volume has been detached for 21 days and is not referenced by any launch template, AMI, or recovery policy.',
		confidence_reason:
			'No compute attachment, no backup policy reference, no snapshot delta changes.',
		recommended_action: 'Archive snapshot, then delete detached volume.',
		connection_id: 'conn-aws-prod',
		owner: 'finops@valdrics.com',
		confidence_score: 0.97,
		explainability_notes:
			'Detached storage with no matching recovery or deployment dependency was found.',
		is_gpu: false
	},
	{
		provider: 'azure',
		finding_id: 'finding-snapshot-stale-1',
		resource_id: 'snap-prd-ledger-2025-12-01',
		resource_type: 'Snapshot',
		monthly_cost: '214.00',
		confidence: 'medium',
		risk_if_deleted: 'medium',
		explanation:
			'Snapshot retention exceeds the current policy and newer validated restore points already exist.',
		confidence_reason: 'Retention history suggests safe archive or policy-based expiration.',
		recommended_action: 'Move to cold retention or expire on next review window.',
		connection_id: 'conn-azure-prod',
		owner: 'security@valdrics.com',
		confidence_score: 0.82,
		explainability_notes:
			'Newer restore points are available and the existing snapshot is outside the stated retention window.'
	}
];

const ZOMBIE_FINDINGS = {
	idle_instances: [ENGINEERING_FINDINGS[0]],
	unattached_volumes: [ENGINEERING_FINDINGS[1]],
	old_snapshots: [ENGINEERING_FINDINGS[2]]
} as const;

export function buildDashboardHeroCaptureData() {
	const { startDate, endDate } = buildDefaultDateRange();

	return {
		user: {
			id: 'user-capture-1',
			tenant_id: 'tenant-capture-1'
		},
		session: null,
		subscription: { tier: 'pro', status: 'active' },
		profile: {
			persona: 'engineering',
			role: 'admin',
			platform_operator: false
		},
		costs: {
			total_cost: 184236.45,
			data_quality: {
				freshness: {
					status: 'final',
					latest_record_date: endDate
				}
			}
		},
		carbon: {
			total_co2_kg: 42.8
		},
		zombies: {
			...ZOMBIE_FINDINGS,
			total_monthly_waste: 1442,
			ai_analysis: {
				total_monthly_savings: '$18,420',
				summary:
					'Three owner-ready actions are carrying the majority of avoidable monthly waste across compute, storage, and backup retention.',
				resources: ENGINEERING_FINDINGS,
				general_recommendations: [
					'Route underused compute to the platform owner before the next planning cycle.',
					'Archive detached storage after backup validation completes.',
					'Collapse stale snapshot retention into the reviewed cold-storage policy.'
				]
			}
		},
		analysis: null,
		allocation: null,
		unitEconomics: null,
		unitEconomicsSettings: null,
		leadershipKpis: {
			total_cost_usd: 184236.45,
			cost_by_provider: {
				aws: 112480.12,
				azure: 43890.26,
				gcp: 27866.07
			},
			top_services: [
				{ service: 'EC2 Compute', cost_usd: 72440.2 },
				{ service: 'Azure VM', cost_usd: 33860.4 },
				{ service: 'Cloud SQL', cost_usd: 21890.32 },
				{ service: 'Object Storage', cost_usd: 14620.11 }
			],
			carbon_total_kgco2e: 42.8,
			carbon_coverage_percent: 92,
			savings_opportunity_monthly_usd: 18420,
			savings_realized_monthly_usd: 7240,
			open_recommendations: 7,
			applied_recommendations: 5,
			pending_remediations: 3,
			completed_remediations: 9,
			security_high_risk_decisions: 1,
			security_approval_required_decisions: 4,
			security_anomaly_signal_decisions: 2,
			notes: [
				'Capture data is generated from dashboardHeroCaptureFixture and mirrors current dashboard contracts.'
			]
		},
		dailyCosts: {
			total_cost_usd: 184236.45,
			total_carbon_kgco2e: 42.8,
			points: [
				{ date: startDate, provider: 'aws', cost_usd: 5480, carbon_kgco2e: 1.3 },
				{ date: startDate, provider: 'azure', cost_usd: 2380, carbon_kgco2e: 0.7 },
				{ date: '2026-05-10', provider: 'aws', cost_usd: 6120, carbon_kgco2e: 1.5 },
				{ date: '2026-05-10', provider: 'gcp', cost_usd: 1490, carbon_kgco2e: 0.4 },
				{ date: '2026-05-16', provider: 'aws', cost_usd: 6840, carbon_kgco2e: 1.7 },
				{ date: '2026-05-16', provider: 'azure', cost_usd: 2840, carbon_kgco2e: 0.8 },
				{ date: '2026-05-22', provider: 'aws', cost_usd: 7320, carbon_kgco2e: 1.9 },
				{ date: '2026-05-22', provider: 'gcp', cost_usd: 1960, carbon_kgco2e: 0.5 },
				{ date: endDate, provider: 'aws', cost_usd: 7010, carbon_kgco2e: 1.8 },
				{ date: endDate, provider: 'azure', cost_usd: 2690, carbon_kgco2e: 0.8 }
			]
		},
		approvalsQueue: [
			{
				approval_id: 'approval-prod-gpu-1',
				action: 'resize_gpu_cluster',
				environment: 'prod',
				resource_reference: 'gpu-prod-training',
				estimated_monthly_delta_usd: 4820,
				expires_at: '2026-06-03T12:00:00Z',
				reason_codes: ['high_delta', 'production']
			},
			{
				approval_id: 'approval-storage-archive-1',
				action: 'archive_storage_tier',
				environment: 'prod',
				resource_reference: 'bucket-ledger-exports',
				estimated_monthly_delta_usd: -1260,
				expires_at: '2026-06-05T12:00:00Z',
				reason_codes: ['retention_policy']
			}
		],
		freshness: {
			status: 'final',
			latest_record_date: endDate
		},
		startDate,
		endDate,
		provider: '',
		error: '',
		warning: ''
	};
}
