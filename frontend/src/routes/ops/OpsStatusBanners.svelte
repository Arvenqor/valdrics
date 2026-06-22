<script lang="ts">
	let {
		error = '',
		success = ''
	}: {
		error?: string;
		success?: string;
	} = $props();
</script>

{#if error}
	<div class="material-perspective">
		<div class="card material-card-3d border-danger-500/30 bg-danger-500/10 p-4">
			<p class="text-danger-400 text-sm">{error}</p>
		</div>
	</div>
{/if}
{#if success}
	<div class="material-perspective">
		<div class="card material-card-3d border-success-500/30 bg-success-500/10 p-4">
			<p class="text-success-400 text-sm">{success}</p>
		</div>
	</div>
{/if}
