<script lang="ts">
	let { loading = false }: { loading?: boolean } = $props();
</script>

<div class="flex items-center justify-between border-b border-ink-800 pb-5">
	<div>
		<h1 class="text-3xl font-bold tracking-tight text-ink-100">
			Ops Center <span
				class="text-xs font-semibold px-2 py-0.5 ml-2 rounded bg-accent-500/10 text-accent-400 border border-accent-500/20 uppercase tracking-widest"
				>Control Room</span
			>
		</h1>
		<p class="text-ink-400 text-sm mt-1">
			Manage automated remediation pipelines, background process scheduling, and cloud economics
			alignment.
		</p>
	</div>
</div>

{#if loading}
	<div class="material-perspective">
		<div class="card material-card-3d p-6 space-y-4">
			<div class="skeleton h-6 w-64"></div>
			<div class="skeleton h-4 w-full"></div>
			<div class="skeleton h-4 w-4/5"></div>
		</div>
	</div>
{/if}
