<script lang="ts">
	import CloudLogo from '$lib/components/CloudLogo.svelte';
	import { type ZombieCollectionKey, type ZombieCollections } from '$lib/zombieCollections';

	type RemediationFinding = {
		finding_id?: string;
		resource_id: string;
		resource_type?: string;
		provider?: string;
		connection_id?: string;
		monthly_cost?: string | number;
		recommended_action?: string;
		owner?: string;
		explainability_notes?: string;
		confidence_score?: number;
		db_class?: string;
		lb_type?: string;
		is_gpu?: boolean;
		instance_type?: string;
		recommended_instance_type?: string;
	};

	type RemediationZombieCollections = ZombieCollections<RemediationFinding>;

	type ZombieCategoryConfig = {
		key: ZombieCollectionKey;
		defaultExplainability: string;
		compactResource?: boolean;
		typeLabel: string | ((finding: RemediationFinding) => string);
	};

	const CATEGORY_CONFIG: ZombieCategoryConfig[] = [
		{
			key: 'unattached_volumes',
			typeLabel: 'EBS Volume',
			defaultExplainability: 'Resource detached and accruing idle costs.'
		},
		{
			key: 'old_snapshots',
			typeLabel: 'Snapshot',
			defaultExplainability: 'Snapshot age exceeds standard retention policy.'
		},
		{
			key: 'unused_elastic_ips',
			typeLabel: 'Elastic IP',
			defaultExplainability: 'Unassociated EIP address found.'
		},
		{
			key: 'idle_instances',
			typeLabel: (finding) =>
				`Idle EC2${finding.instance_type ? ` (${finding.instance_type})` : ''}`,
			defaultExplainability: 'Low CPU and network utilization detected over 7 days.'
		},
		{
			key: 'orphan_load_balancers',
			typeLabel: (finding) => `Orphan ${(finding.lb_type || 'load balancer').toUpperCase()}`,
			defaultExplainability: 'Load balancer has no healthy targets associated.'
		},
		{
			key: 'idle_rds_databases',
			typeLabel: (finding) => `Idle RDS${finding.db_class ? ` (${finding.db_class})` : ''}`,
			defaultExplainability: 'No connections detected in the last billing cycle.'
		},
		{
			key: 'underused_nat_gateways',
			typeLabel: 'Idle NAT Gateway',
			defaultExplainability: 'Minimal data processing detected compared to runtime cost.'
		},
		{
			key: 'idle_s3_buckets',
			typeLabel: 'Idle S3 Bucket',
			defaultExplainability: 'No GET/PUT requests recorded in the last 30 days.'
		},
		{
			key: 'stale_ecr_images',
			typeLabel: 'ECR Image',
			defaultExplainability: 'Untagged or superseded by multiple newer versions.',
			compactResource: true
		},
		{
			key: 'idle_sagemaker_endpoints',
			typeLabel: 'SageMaker Endpoint',
			defaultExplainability: 'Endpoint has not processed any inference requests recently.'
		},
		{
			key: 'cold_redshift_clusters',
			typeLabel: 'Redshift Cluster',
			defaultExplainability: 'Cluster has been in idle state for over 14 days.'
		}
	];

	let { zombies, zombieCount, onRemediate } = $props<{
		zombies: RemediationZombieCollections | null | undefined;
		zombieCount: number;
		onRemediate: (finding: RemediationFinding) => void;
	}>();

	function providerTone(provider: string | undefined): string {
		if (provider === 'aws') return 'zombie-table__provider-label--aws';
		if (provider === 'azure') return 'zombie-table__provider-label--azure';
		return 'zombie-table__provider-label--gcp';
	}

	function providerLabel(provider: string | undefined): string {
		return provider || 'AWS';
	}

	function confidenceRatio(score: number | undefined): number | null {
		if (typeof score !== 'number' || !Number.isFinite(score)) return null;
		return Math.max(0, Math.min(1, score));
	}

	function confidencePercent(score: number | undefined): number {
		const ratio = confidenceRatio(score);
		return Math.round((ratio ?? 0) * 100);
	}

	function confidenceLabel(score: number | undefined): string {
		const ratio = confidenceRatio(score);
		if (ratio === null) return 'N/A';
		return `${Math.round(ratio * 100)}% Match`;
	}

	function typeLabel(config: ZombieCategoryConfig, finding: RemediationFinding): string {
		return typeof config.typeLabel === 'function' ? config.typeLabel(finding) : config.typeLabel;
	}

	function monthlyCostLabel(value: RemediationFinding['monthly_cost']): string {
		if (value === null || value === undefined || value === '') return '0';
		return String(value);
	}

	let zombieRows = $derived.by(() =>
		CATEGORY_CONFIG.flatMap((config) => {
			const findings = (zombies?.[config.key] ?? []) as RemediationFinding[];
			return findings.map((finding) => ({
				key: `${config.key}:${finding.resource_id}`,
				config,
				finding
			}));
		})
	);
</script>

<div class="card stagger-enter zombie-table">
	<div class="zombie-table__header">
		<h2 class="zombie-table__title">Zombie Resources</h2>
		<span class="badge badge-warning">{zombieCount} found</span>
	</div>

	<div class="zombie-table__scroller">
		<table class="table zombie-table__table">
			<thead>
				<tr>
					<th>Cloud</th>
					<th>Resource</th>
					<th>Type</th>
					<th>Monthly Cost</th>
					<th>Owner</th>
					<th>AI Reasoning & Confidence</th>
					<th>Action</th>
				</tr>
			</thead>
			<tbody>
				{#each zombieRows as row (row.key)}
					<tr>
						<td class="zombie-table__cloud-cell">
							<CloudLogo provider={row.finding.provider} size={12} />
							<span class={`zombie-table__provider-label ${providerTone(row.finding.provider)}`}>
								{providerLabel(row.finding.provider)}
							</span>
						</td>
						<td
							class="zombie-table__resource-id"
							class:zombie-table__resource-id--compact={row.config.compactResource}
							title={row.finding.resource_id}
						>
							{row.finding.resource_id}
						</td>
						<td>
							<div class="zombie-table__type-group">
								<span class="badge badge-default">{typeLabel(row.config, row.finding)}</span>
								{#if row.config.key === 'idle_instances' && row.finding.is_gpu}
									<span class="zombie-table__gpu-badge">GPU</span>
								{/if}
							</div>
						</td>
						<td class="zombie-table__cost">${monthlyCostLabel(row.finding.monthly_cost)}</td>
						<td class="zombie-table__owner">{row.finding.owner || 'unknown'}</td>
						<td>
							<div class="zombie-table__confidence">
								<p class="zombie-table__explanation">
									{row.finding.explainability_notes || row.config.defaultExplainability}
								</p>
								<div class="zombie-table__confidence-meta">
									<progress
										class="zombie-table__confidence-meter"
										value={confidencePercent(row.finding.confidence_score)}
										max="100"
									></progress>
									<span class="zombie-table__confidence-label">
										{confidenceLabel(row.finding.confidence_score)}
									</span>
								</div>
							</div>
						</td>
						<td>
							<button
								type="button"
								class="btn btn-ghost zombie-table__action"
								onclick={() => onRemediate(row.finding)}
								disabled={!row.finding.finding_id}
								title={!row.finding.finding_id
									? 'Persisted finding binding missing. Rerun the scan to remediate safely.'
									: 'Review remediation'}
							>
								{row.finding.finding_id ? 'Review' : 'Unavailable'}
							</button>
						</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<style>
	.zombie-table {
		animation-delay: 250ms;
	}

	.zombie-table__header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-3);
		margin-bottom: var(--space-5);
	}

	.zombie-table__title {
		margin: 0;
		font-size: var(--text-lg);
		font-weight: 600;
	}

	.zombie-table__scroller {
		overflow-x: auto;
	}

	.zombie-table__table {
		min-width: 100%;
	}

	.zombie-table__cloud-cell {
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.zombie-table__provider-label {
		font-size: var(--text-xs);
		font-weight: 700;
		text-transform: uppercase;
	}

	.zombie-table__provider-label--aws {
		color: #fb923c;
	}

	.zombie-table__provider-label--azure {
		color: #60a5fa;
	}

	.zombie-table__provider-label--gcp {
		color: #facc15;
	}

	.zombie-table__resource-id {
		max-width: 14rem;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-family: var(--font-mono);
		font-size: var(--text-xs);
	}

	.zombie-table__resource-id--compact {
		max-width: 9.375rem;
	}

	.zombie-table__type-group {
		display: flex;
		align-items: center;
		gap: 0.375rem;
	}

	.zombie-table__gpu-badge {
		display: inline-flex;
		align-items: center;
		padding: 0 0.375rem;
		border-radius: var(--radius-full);
		background: rgb(239 68 68 / 0.18);
		color: var(--color-danger-400);
		font-size: var(--text-xs);
		font-weight: 700;
		text-transform: uppercase;
	}

	.zombie-table__cost {
		color: var(--color-danger-400);
	}

	.zombie-table__owner {
		font-size: var(--text-xs);
		color: var(--color-ink-400);
	}

	.zombie-table__confidence {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		max-width: 20rem;
	}

	.zombie-table__explanation {
		margin: 0;
		font-size: var(--text-xs);
		line-height: 1.35;
		color: var(--color-ink-300);
	}

	.zombie-table__confidence-meta {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.zombie-table__confidence-meter {
		inline-size: 4rem;
		block-size: 0.25rem;
		appearance: none;
		border: none;
		border-radius: var(--radius-full);
		background: var(--color-ink-700);
		overflow: hidden;
	}

	.zombie-table__confidence-meter::-webkit-progress-bar {
		background: var(--color-ink-700);
	}

	.zombie-table__confidence-meter::-webkit-progress-value {
		background: var(--color-accent-500);
	}

	.zombie-table__confidence-meter::-moz-progress-bar {
		background: var(--color-accent-500);
	}

	.zombie-table__confidence-label {
		font-size: var(--text-xs);
		font-weight: 700;
		color: var(--color-accent-400);
	}

	.zombie-table__action {
		font-size: var(--text-xs);
	}

	@media (max-width: 900px) {
		.zombie-table__header {
			flex-direction: column;
			align-items: flex-start;
		}

		.zombie-table__table {
			min-width: 52rem;
		}
	}
</style>
