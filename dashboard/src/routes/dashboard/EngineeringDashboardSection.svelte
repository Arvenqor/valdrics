<script lang="ts">
	import FindingsTable from '$lib/components/FindingsTable.svelte';
	import SavingsHero from '$lib/components/SavingsHero.svelte';
	import ZombieTable from '$lib/components/ZombieTable.svelte';
	import type { ZombieCollections } from '$lib/zombieCollections';

	type DashboardFinding = {
		provider?: 'aws' | 'azure' | 'gcp';
		finding_id?: string;
		resource_id: string;
		resource_type?: string;
		connection_id?: string;
		monthly_cost?: string | number;
		confidence?: 'high' | 'medium' | 'low';
		confidence_reason?: string;
		risk_if_deleted?: 'high' | 'medium' | 'low';
		explanation?: string;
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

	type DashboardZombieCollections = ZombieCollections<DashboardFinding>;

	type SavingsHeroData = {
		total_monthly_savings?: string;
		summary?: string;
		resources?: DashboardFinding[];
		general_recommendations?: string[];
	};

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

	let { zombies, analysisText, zombieCount, onRemediate } = $props<{
		zombies: DashboardZombieCollections | null | undefined;
		analysisText: string;
		zombieCount: number;
		onRemediate: (finding: RemediationFinding) => void;
	}>();
</script>

{#if zombies?.ai_analysis}
	{@const aiData = zombies.ai_analysis as SavingsHeroData}

	<SavingsHero {aiData} />

	{#if aiData.resources && aiData.resources.length > 0}
		<FindingsTable
			resources={aiData.resources as Array<{
				provider: 'aws' | 'azure' | 'gcp';
				finding_id?: string;
				resource_id: string;
				resource_type?: string;
				monthly_cost?: string | number;
				confidence?: 'high' | 'medium' | 'low';
				risk_if_deleted?: 'high' | 'medium' | 'low';
				explanation: string;
				confidence_reason?: string;
				recommended_action?: string;
				connection_id?: string;
				owner?: string;
				is_gpu?: boolean;
			}>}
			{onRemediate}
		/>
	{/if}

	{#if aiData.general_recommendations && aiData.general_recommendations.length > 0}
		<div class="card stagger-enter" style="animation-delay: 400ms;">
			<h3 class="text-lg font-semibold mb-3">💡 Recommendations</h3>
			<ul class="space-y-2">
				{#each aiData.general_recommendations as recommendation (recommendation)}
					<li class="flex items-start gap-2 text-sm text-ink-300">
						<span class="text-accent-400">•</span>
						{recommendation}
					</li>
				{/each}
			</ul>
		</div>
	{/if}
{:else if analysisText}
	<div class="card stagger-enter" style="animation-delay: 200ms;">
		<div class="flex items-center justify-between mb-3">
			<h2 class="text-lg font-semibold">AI Insights</h2>
			<span class="badge badge-default">LLM</span>
		</div>
		<div class="text-sm text-ink-300 whitespace-pre-wrap leading-relaxed">
			{analysisText}
		</div>
	</div>
{/if}

{#if zombieCount > 0}
	<ZombieTable
		zombies={zombies as ZombieCollections<RemediationFinding> | null | undefined}
		{zombieCount}
		{onRemediate}
	/>
{/if}
