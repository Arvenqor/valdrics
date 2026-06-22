<script lang="ts">
	import type { BudgetData, CarbonData, GravitonData } from './greenopsTypes';
	import { Cpu, Leaf, Zap, BarChart2 } from '@lucide/svelte';

	interface Props {
		carbonData: CarbonData | null;
		gravitonData: GravitonData | null;
		budgetData: BudgetData | null;
		formatCO2: (kg: number) => string;
	}

	let { carbonData, gravitonData, budgetData, formatCO2 }: Props = $props();
</script>

<div class="bento-grid">
	<!-- Total Carbon Footprint Card -->
	<div class="material-card-3d col-span-2 relative overflow-hidden group p-6 flex flex-col justify-between h-full glow-cyan">
		<div
			class="absolute -top-10 -right-10 p-4 opacity-5 text-9xl leading-none select-none pointer-events-none transition-transform duration-500 group-hover:scale-110"
		>
			🌍
		</div>
		<div class="relative z-10 flex flex-col justify-between h-full">
			<div>
				<div class="flex items-center gap-2 mb-2">
					<Leaf class="w-4 h-4 text-emerald-400" />
					<h2 class="text-ink-400 text-xs font-semibold uppercase tracking-wider">
						Total Carbon Footprint
					</h2>
				</div>
				<div class="flex flex-wrap items-baseline gap-3">
					<span class="text-5xl font-extrabold text-white tracking-tight">
						{carbonData ? formatCO2(carbonData.total_co2_kg) : '—'}
					</span>
					{#if carbonData?.forecast_30d}
						<span
							class="text-xs font-semibold text-emerald-300 bg-emerald-950/40 px-2.5 py-1 rounded-full border border-emerald-500/20"
						>
							30d Projected: {formatCO2(carbonData.forecast_30d.projected_co2_kg)}
						</span>
					{/if}
				</div>
				<p class="text-ink-400 text-sm mt-3 leading-relaxed">Combined Scope 2 (Operational) & Scope 3 (Embodied) emissions.</p>
			</div>

			{#if carbonData}
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-6">
					<div class="bg-ink-950/40 border border-ink-800/40 rounded-xl p-3">
						<div class="flex justify-between text-xs mb-1.5">
							<span class="text-ink-400 font-medium">Scope 2 (Operational)</span>
							<span class="text-white font-mono font-bold">
								{carbonData.total_co2_kg > 0
									? Math.round((carbonData.scope2_co2_kg / carbonData.total_co2_kg) * 100)
									: 0}%
							</span>
						</div>
						<div class="h-2 w-full bg-ink-950 rounded-full overflow-hidden border border-ink-800/80">
							<div
								class="h-full bg-gradient-to-r from-cyan-600 to-cyan-400 rounded-full shadow-[0_0_8px_rgba(6,182,212,0.4)] transition-all duration-500"
								style="width: {carbonData.total_co2_kg > 0
									? (carbonData.scope2_co2_kg / carbonData.total_co2_kg) * 100
									: 0}%"
							></div>
						</div>
						<div class="text-white text-xs font-semibold mt-1.5">{formatCO2(carbonData.scope2_co2_kg)}</div>
					</div>
					<div class="bg-ink-950/40 border border-ink-800/40 rounded-xl p-3">
						<div class="flex justify-between text-xs mb-1.5">
							<span class="text-ink-400 font-medium">Scope 3 (Embodied)</span>
							<span class="text-white font-mono font-bold">
								{carbonData.total_co2_kg > 0
									? Math.round((carbonData.scope3_co2_kg / carbonData.total_co2_kg) * 100)
									: 0}%
							</span>
						</div>
						<div class="h-2 w-full bg-ink-950 rounded-full overflow-hidden border border-ink-800/80">
							<div
								class="h-full bg-gradient-to-r from-purple-600 to-purple-400 rounded-full shadow-[0_0_8px_rgba(168,85,247,0.4)] transition-all duration-500"
								style="width: {carbonData.total_co2_kg > 0
									? (carbonData.scope3_co2_kg / carbonData.total_co2_kg) * 100
									: 0}%"
							></div>
						</div>
						<div class="text-white text-xs font-semibold mt-1.5">{formatCO2(carbonData.scope3_co2_kg)}</div>
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Efficiency Score Card -->
	<div class="material-card-3d p-6 text-center flex flex-col items-center justify-center relative overflow-hidden group">
		<div class="absolute inset-0 bg-gradient-to-b from-cyan-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
		<div class="text-3xl p-3 bg-cyan-950/30 border border-cyan-800/20 rounded-2xl mb-3 text-cyan-400 shadow-[0_0_15px_rgba(34,211,239,0.1)]">
			<BarChart2 class="w-6 h-6" />
		</div>
		<h3 class="text-ink-400 text-xs font-semibold uppercase tracking-wider">Efficiency Score</h3>
		<p class="text-4xl font-extrabold text-white mt-2 tracking-tight">
			{carbonData ? carbonData.carbon_efficiency_score : '—'}
		</p>
		<p class="text-ink-400 text-xs mt-1.5 font-medium">gCO₂e per $1 spent</p>
	</div>

	<!-- Est. Energy Card -->
	<div class="material-card-3d p-6 text-center flex flex-col items-center justify-center relative overflow-hidden group">
		<div class="absolute inset-0 bg-gradient-to-b from-emerald-500/5 to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
		<div class="text-3xl p-3 bg-emerald-950/30 border border-emerald-800/20 rounded-2xl mb-3 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]">
			<Zap class="w-6 h-6" />
		</div>
		<h3 class="text-ink-400 text-xs font-semibold uppercase tracking-wider">Est. Energy</h3>
		<p class="text-4xl font-extrabold text-white mt-2 tracking-tight">
			{carbonData ? Math.round(carbonData.estimated_energy_kwh).toLocaleString() : '—'}
		</p>
		<p class="text-ink-400 text-xs mt-1.5 font-medium">kWh (incl. PUE)</p>
	</div>

	<!-- Monthly Carbon Budget Card -->
	<div class="material-card-3d col-span-2 p-6 flex flex-col justify-between">
		<div>
			<div class="flex items-center justify-between mb-4">
				<h3 class="text-lg font-bold text-white flex items-center gap-2">
					📊 Monthly Carbon Budget
				</h3>
				{#if budgetData}
					<span
						class="px-2.5 py-1 text-xs font-bold rounded-full border transition-colors duration-300 {budgetData.alert_status === 'ok'
							? 'bg-emerald-950/40 text-emerald-400 border-emerald-500/30'
							: budgetData.alert_status === 'warning'
								? 'bg-yellow-950/40 text-yellow-400 border-yellow-500/30'
								: 'bg-red-950/40 text-red-400 border-red-500/30'}"
					>
						{budgetData.alert_status === 'ok'
							? 'ON TRACK'
							: budgetData.alert_status === 'warning'
								? 'WARNING'
								: 'EXCEEDED'}
					</span>
				{/if}
			</div>

			{#if budgetData}
				<div class="relative pt-2">
					<div class="flex justify-between text-xs font-medium text-ink-400 mb-1.5">
						<span>{formatCO2(budgetData.current_usage_kg)} used</span>
						<span>Limit: {formatCO2(budgetData.budget_kg)}</span>
					</div>
					<div class="w-full bg-ink-950 rounded-full h-3 border border-ink-800 overflow-hidden shadow-inner">
						<div
							class="h-full rounded-full transition-all duration-1000 ease-out relative"
							class:bg-gradient-to-r={true}
							class:from-emerald-600={budgetData.alert_status === 'ok'}
							class:to-emerald-400={budgetData.alert_status === 'ok'}
							class:from-yellow-600={budgetData.alert_status === 'warning'}
							class:to-yellow-400={budgetData.alert_status === 'warning'}
							class:from-red-600={budgetData.alert_status === 'exceeded'}
							class:to-red-400={budgetData.alert_status === 'exceeded'}
							style="width: {Math.min(budgetData.usage_percent, 100)}%"
						>
							<div class="absolute inset-0 bg-white/20 animate-pulse"></div>
						</div>
					</div>
					<div class="flex justify-end mt-1.5">
						<span class="text-xs font-semibold text-ink-400">{budgetData.usage_percent}% consumed</span>
					</div>
				</div>
			{:else}
				<div class="animate-pulse h-14 bg-ink-900/40 border border-ink-800/40 rounded-xl"></div>
			{/if}
		</div>
	</div>

	<!-- Graviton Candidates Card -->
	<div class="material-card-3d row-span-2 col-span-2 p-6 flex flex-col justify-between h-full">
		<div class="mb-4">
			<h3 class="text-lg font-bold text-white flex items-center gap-2">
				<Cpu class="w-5 h-5 text-accent-400" />
				Graviton Candidates
				{#if gravitonData && gravitonData.candidates?.length}
					<span class="bg-accent-500/20 text-accent-300 text-xs px-2.5 py-0.5 rounded-full border border-accent-500/30 font-bold"
						>{gravitonData.candidates.length}</span
					>
				{/if}
			</h3>
		</div>

		<div class="space-y-3 overflow-y-auto max-h-[280px] pr-2 custom-scrollbar flex-grow">
			{#if gravitonData && (gravitonData.candidates?.length ?? 0) > 0}
				{#each (gravitonData.candidates ?? []).slice(0, 5) as candidate (candidate.instance_id)}
					<div
						class="bg-ink-950/40 border border-ink-800/50 rounded-xl p-3.5 hover:border-accent-500/40 hover:bg-ink-900/40 transition-all duration-200 hover:-translate-y-0.5"
					>
						<div class="flex justify-between items-start mb-1.5">
							<span class="font-mono text-sm text-white font-semibold">{candidate.instance_id}</span>
							<span class="text-emerald-400 text-xs font-extrabold bg-emerald-950/30 px-2 py-0.5 rounded border border-emerald-500/20"
								>-{candidate.energy_savings_percent}% CO₂</span
							>
						</div>
						<div class="flex items-center gap-2.5 text-xs font-semibold text-ink-400">
							<span class="font-mono bg-ink-950 px-1.5 py-0.5 rounded border border-ink-800/40">{candidate.current_type}</span>
							<span class="text-accent-500 font-bold">→</span>
							<span class="font-mono bg-accent-950/40 text-accent-300 px-1.5 py-0.5 rounded border border-accent-500/20">{candidate.recommended_type}</span>
						</div>
					</div>
				{/each}
			{:else if gravitonData}
				<div class="text-center py-14 text-ink-400">
					<p class="text-xl mb-1">🎉</p>
					<p class="text-sm font-semibold">All workloads optimized!</p>
				</div>
			{:else}
				<div class="space-y-3">
					<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
					{#each Array(3) as _, i (i)}
						<div class="h-16 bg-ink-900/30 border border-ink-800/30 rounded-xl animate-pulse"></div>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	<!-- Environmental Equivalencies Card -->
	<div class="material-card-3d col-span-2 p-6">
		<h3 class="text-xs font-bold text-ink-400 mb-4 uppercase tracking-wider">
			Environmental Equivalencies
		</h3>

		{#if carbonData?.equivalencies}
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
				<div class="text-center p-3.5 bg-ink-950/50 rounded-xl border border-ink-800/60 hover:border-accent-500/30 hover:bg-ink-900/50 transition-all duration-200 hover:-translate-y-0.5">
					<div class="text-3xl mb-1.5 filter drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">🚗</div>
					<div class="text-base font-extrabold text-white">
						{carbonData.equivalencies.miles_driven.toLocaleString()}
					</div>
					<div class="text-xs text-ink-400 font-medium mt-0.5">miles driven</div>
				</div>
				<div class="text-center p-3.5 bg-ink-950/50 rounded-xl border border-ink-800/60 hover:border-accent-500/30 hover:bg-ink-900/50 transition-all duration-200 hover:-translate-y-0.5">
					<div class="text-3xl mb-1.5 filter drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">🌳</div>
					<div class="text-base font-extrabold text-white">
						{carbonData.equivalencies.trees_needed_for_year}
					</div>
					<div class="text-xs text-ink-400 font-medium mt-0.5">trees / year</div>
				</div>
				<div class="text-center p-3.5 bg-ink-950/50 rounded-xl border border-ink-800/60 hover:border-accent-500/30 hover:bg-ink-900/50 transition-all duration-200 hover:-translate-y-0.5">
					<div class="text-3xl mb-1.5 filter drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">📱</div>
					<div class="text-base font-extrabold text-white">
						{carbonData.equivalencies.smartphone_charges.toLocaleString()}
					</div>
					<div class="text-xs text-ink-400 font-medium mt-0.5">phone charges</div>
				</div>
				<div class="text-center p-3.5 bg-ink-950/50 rounded-xl border border-ink-800/60 hover:border-accent-500/30 hover:bg-ink-900/50 transition-all duration-200 hover:-translate-y-0.5">
					<div class="text-3xl mb-1.5 filter drop-shadow-[0_2px_4px_rgba(0,0,0,0.3)]">🏠</div>
					<div class="text-base font-extrabold text-white">
						{carbonData.equivalencies.percent_of_home_month}%
					</div>
					<div class="text-xs text-ink-400 font-medium mt-0.5">home / month</div>
				</div>
			</div>
		{:else}
			<div class="animate-pulse h-[88px] bg-ink-900/30 border border-ink-800/30 rounded-xl"></div>
		{/if}
	</div>
</div>
