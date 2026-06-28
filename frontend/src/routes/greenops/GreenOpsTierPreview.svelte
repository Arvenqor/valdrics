<script lang="ts">
	import { getUpgradePrompt } from '$lib/pricing/upgradePrompt';

	interface Props {
		toAppPath: (path: string) => string;
	}

	let { toAppPath }: Props = $props();
	const upgradePrompt = getUpgradePrompt('growth', 'GreenOps visibility');
</script>

<div class="relative overflow-hidden rounded-2xl">
	<div
		class="absolute inset-0 z-20 flex flex-col items-center justify-center text-center bg-ink-950/80 backdrop-blur-md rounded-2xl p-8"
	>
		<div class="text-6xl mb-4 drop-shadow-[0_0_15px_rgba(16,185,129,0.3)]">🌱</div>
		<h2 class="text-3xl font-extrabold text-white mb-2 tracking-tight">{upgradePrompt.heading}</h2>
		<p class="text-ink-300 max-w-md text-sm mb-3 leading-relaxed">{upgradePrompt.body}</p>
		<p class="text-ink-500 text-xs max-w-md mb-6 leading-normal">{upgradePrompt.footnote}</p>
		<p class="text-ink-400 text-sm max-w-md mb-6 leading-relaxed">
			Track cloud carbon footprint, compare greener regions, and monitor sustainability metrics once
			your workspace moves into the Growth operating lane.
		</p>
		<div class="flex items-center gap-2 mb-6">
			<span
				class="px-2.5 py-1 text-xs font-bold bg-yellow-950/40 text-yellow-400 border border-yellow-500/20 rounded-full"
				>{upgradePrompt.badge}</span
			>
		</div>
		<a
			href={toAppPath('/billing')}
			class="material-button-3d px-6 py-3 bg-accent-600 hover:bg-accent-500 text-white rounded-xl text-sm font-semibold transition-all shadow-lg shadow-accent-600/20 cursor-pointer"
			>{upgradePrompt.cta}</a
		>
	</div>

	<div class="opacity-20 pointer-events-none select-none">
		<div class="bento-grid">
			<div class="material-card-3d col-span-2 p-6 h-full flex flex-col justify-between">
				<div>
					<h2 class="text-ink-400 text-xs font-semibold uppercase tracking-wider mb-2">
						Total Carbon Footprint
					</h2>
					<span class="text-5xl font-extrabold text-white tracking-tight">42.7 kg</span>
				</div>
				<p class="text-ink-400 text-sm mt-3">Combined Scope 2 + Scope 3</p>
			</div>
			<div class="material-card-3d p-6 text-center flex flex-col items-center justify-center">
				<div
					class="text-3xl p-3 bg-cyan-950/30 border border-cyan-800/20 rounded-2xl mb-2 text-cyan-400"
				>
					📈
				</div>
				<h3 class="text-ink-400 text-xs font-semibold uppercase tracking-wider">
					Efficiency Score
				</h3>
				<p class="text-3xl font-extrabold text-white mt-1">89</p>
			</div>
			<div class="material-card-3d p-6 text-center flex flex-col items-center justify-center">
				<div
					class="text-3xl p-3 bg-emerald-950/30 border border-emerald-800/20 rounded-2xl mb-2 text-emerald-400"
				>
					⚡
				</div>
				<h3 class="text-ink-400 text-xs font-semibold uppercase tracking-wider">Est. Energy</h3>
				<p class="text-3xl font-extrabold text-white mt-1">156 kWh</p>
			</div>
			<div class="material-card-3d col-span-2 p-6">
				<h3 class="text-lg font-bold text-white mb-4">📊 Monthly Carbon Budget</h3>
				<div
					class="w-full bg-ink-950 rounded-full h-3 border border-ink-800 overflow-hidden shadow-inner"
				>
					<div
						class="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 rounded-full"
						style="width: 65%"
					></div>
				</div>
				<p class="text-right text-xs text-ink-500 mt-2 font-semibold">65% consumed</p>
			</div>
		</div>
	</div>
</div>
