<script lang="ts">
	import type { AuditLog } from './auditTypes';

	interface Props {
		loading: boolean;
		logs: AuditLog[];
		onViewDetail: (id: string) => void;
		formatDate: (value: string) => string;
	}

	let { loading, logs, onViewDetail, formatDate }: Props = $props();
</script>

<div class="material-perspective">
	<div class="card material-card-3d p-6">
		<h2 class="text-lg font-bold mb-4">Events</h2>
		{#if loading}
			<div class="skeleton h-5 w-72 mb-2"></div>
			<div class="skeleton h-5 w-full mb-2"></div>
			<div class="skeleton h-5 w-full"></div>
		{:else}
			<div class="overflow-x-auto">
				<table class="table w-full">
					<thead>
						<tr>
							<th>Timestamp</th>
							<th>Event</th>
							<th>Actor</th>
							<th>Resource</th>
							<th>Status</th>
							<th>Correlation</th>
							<th>Detail</th>
						</tr>
					</thead>
					<tbody>
						{#if logs.length === 0}
							<tr>
								<td colspan="7" class="text-ink-400 text-center py-4">No audit logs found.</td>
							</tr>
						{:else}
							{#each logs as log (log.id)}
								<tr>
									<td class="text-xs text-ink-500">{formatDate(log.event_timestamp)}</td>
									<td class="font-mono text-xs">{log.event_type}</td>
									<td>{log.actor_email || '-'}</td>
									<td>{log.resource_type || '-'} {log.resource_id || ''}</td>
									<td>
										<span class="badge {log.success ? 'badge-success' : 'badge-warning'}">
											{log.success ? 'SUCCESS' : 'FAILED'}
										</span>
									</td>
									<td class="text-xs font-mono">{log.correlation_id || '-'}</td>
									<td>
										<button
											type="button"
											class="btn btn-secondary material-button-3d text-xs px-3 py-1.5"
											onclick={() => onViewDetail(log.id)}
										>
											View
										</button>
									</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>
