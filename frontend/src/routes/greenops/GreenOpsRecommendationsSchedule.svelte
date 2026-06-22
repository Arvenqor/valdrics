<script lang="ts">
	import type { CarbonData, IntensityData, ScheduleResult } from './greenopsTypes';
	import { Compass, Calendar, Sparkles } from '@lucide/svelte';

	interface Props {
		carbonData: CarbonData | null;
		intensityData: IntensityData | null;
		workloadDuration: number;
		scheduleResult: ScheduleResult | null;
		onGetOptimalSchedule: () => void | Promise<void>;
	}

	let {
		carbonData,
		intensityData,
		workloadDuration = $bindable(),
		scheduleResult,
		onGetOptimalSchedule
	}: Props = $props();
</script>

{#if carbonData}
	<div class="material-card-3d p-6 mt-8 relative overflow-hidden group">
		<h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
			<Compass class="w-5 h-5 text-emerald-400" />
			Recommended Regions
			<span class="text-xs font-semibold text-emerald-300 bg-emerald-950/40 px-2.5 py-0.5 rounded border border-emerald-500/20"
				>Lower Carbon Intensity</span
			>
		</h3>
		{#if (carbonData.green_region_recommendations?.length ?? 0) > 0}
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				{#each (carbonData.green_region_recommendations ?? []).slice(0, 3) as rec (rec.region)}
					<div
						class="green-gradient-card p-4 rounded-xl transition-all duration-200"
					>
						<div class="flex justify-between items-start">
							<span class="font-bold text-white transition-colors"
								>{rec.region}</span
							>
							<span class="text-xs bg-emerald-950/50 text-emerald-300 font-bold px-2 py-0.5 rounded border border-emerald-500/20"
								>{rec.carbon_intensity} g/kWh</span
							>
						</div>
						<div class="mt-3 text-sm text-ink-400 font-medium">
							Reduce emissions by <span class="text-emerald-400 font-extrabold">-{rec.savings_percent}%</span>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div
				class="p-5 rounded-xl bg-gradient-to-br from-emerald-950/10 to-emerald-950/5 border border-emerald-500/20 text-emerald-300 font-semibold text-sm flex items-center gap-2"
			>
				<span>🌿</span> You’re already running in one of the greenest regions!
			</div>
		{/if}
	</div>
{/if}

<div class="material-card-3d p-6 mt-8 relative overflow-hidden">
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
		<div>
			<h3 class="text-xl font-extrabold text-white flex items-center gap-2 tracking-tight">
				<Calendar class="w-5 h-5 text-accent-400" />
				Carbon-Aware Scheduling
			</h3>
			<p class="text-ink-400 text-sm mt-1">Schedule non-urgent batch jobs during lower carbon intensity windows.</p>
		</div>
		<div>
			{#if intensityData?.source === 'simulation'}
				<span
					class="px-2.5 py-1 text-xs font-bold bg-yellow-950/40 text-yellow-400 border border-yellow-500/30 rounded-full"
				>
					Simulated Curves
				</span>
			{:else}
				<span
					class="px-2.5 py-1 text-xs font-bold bg-emerald-950/40 text-emerald-400 border border-emerald-500/30 rounded-full glow-emerald"
				>
					Live Grid Telemetry
				</span>
			{/if}
		</div>
	</div>

	<div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
		<div class="lg:col-span-2 relative flex flex-col justify-between">
			<h4 class="text-white text-xs font-bold mb-6 uppercase tracking-wider text-ink-400">
				24h Grid Intensity Forecast (gCO₂e/kWh)
			</h4>
			
			<div class="relative h-40 w-full flex items-end gap-1.5 pt-6 border-b border-ink-800">
				<!-- Grid lines -->
				<div class="chart-grid-line" style="bottom: 75%;"></div>
				<div class="chart-grid-line" style="bottom: 50%;"></div>
				<div class="chart-grid-line" style="bottom: 25%;"></div>

				{#if intensityData?.forecast}
					{#each intensityData.forecast as hour (hour.hour_utc)}
						<div class="group relative flex-1 flex flex-col items-center justify-end h-full">
							<div
								class="w-full rounded-t-lg transition-all duration-300 hover:opacity-100 opacity-80"
								class:bg-gradient-to-t={true}
								class:from-emerald-700={hour.level === 'very_low' || hour.level === 'low'}
								class:to-emerald-400={hour.level === 'very_low' || hour.level === 'low'}
								class:from-yellow-600={hour.level === 'medium'}
								class:to-yellow-400={hour.level === 'medium'}
								class:from-red-700={hour.level === 'high' || hour.level === 'very_high'}
								class:to-red-400={hour.level === 'high' || hour.level === 'very_high'}
								style="height: {Math.max((hour.intensity_gco2_kwh / 800) * 100, 8)}%"
							></div>
							<!-- Tooltip -->
							<div
								class="absolute bottom-full mb-2.5 hidden group-hover:flex flex-col bg-ink-950 border border-ink-700 p-2.5 rounded-xl text-xs z-30 shadow-2xl pointer-events-none whitespace-nowrap"
							>
								<span class="text-ink-400 font-medium">{hour.hour_utc}:00 UTC</span>
								<span class="font-extrabold text-white mt-0.5">{hour.intensity_gco2_kwh} g/kWh</span>
							</div>
						</div>
					{/each}
				{/if}
			</div>
			
			<div class="flex justify-between mt-2.5 text-xs font-semibold text-ink-500 px-1">
				<span>NOW</span>
				<span>+12 HOURS</span>
				<span>+24 HOURS</span>
			</div>
		</div>

		<!-- Scheduler Control Panel -->
		<div class="bg-ink-950/40 p-6 rounded-2xl border border-ink-800/80 flex flex-col justify-between">
			<div>
				<h4 class="text-white text-xs font-bold mb-4 uppercase tracking-wider text-ink-400">
					Workload Scheduler
				</h4>
				<div class="space-y-5">
					<div>
						<div class="flex justify-between items-baseline mb-2">
							<label for="duration" class="text-xs font-medium text-ink-400"
								>Job Duration</label
							>
							<span class="text-xs font-mono font-bold text-white bg-ink-950 border border-ink-800 px-1.5 py-0.5 rounded">{workloadDuration} hours</span>
						</div>
						<input
							type="range"
							id="duration"
							min="1"
							max="24"
							bind:value={workloadDuration}
							class="cursor-pointer"
						/>
					</div>

					<button
						type="button"
						onclick={onGetOptimalSchedule}
						class="material-button-3d w-full py-3 bg-accent-600 hover:bg-accent-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-accent-600/10 cursor-pointer flex items-center justify-center gap-2"
					>
						<Sparkles class="w-4 h-4 text-accent-300" />
						Find Optimal Window
					</button>
				</div>
			</div>

			{#if scheduleResult}
				<div
					class="mt-6 p-4 bg-emerald-950/30 border border-emerald-500/20 rounded-xl glow-emerald animate-in fade-in slide-in-from-bottom-2 duration-300"
				>
					<div class="text-[10px] uppercase font-extrabold text-emerald-400 tracking-wider mb-1">Optimal Recommendation</div>
					<div class="text-sm text-white font-semibold leading-relaxed">{scheduleResult.recommendation}</div>
				</div>
			{/if}
		</div>
	</div>
</div>
