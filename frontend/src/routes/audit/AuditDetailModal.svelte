<script lang="ts">
	import type { AuditDetail } from './auditTypes';

	interface Props {
		selectedLogId: string | null;
		selectedDetail: AuditDetail | null;
		loadingDetail: boolean;
		closeDetail: () => void;
		formatDate: (value: string) => string;
	}

	let { selectedLogId, selectedDetail, loadingDetail, closeDetail, formatDate }: Props = $props();
</script>

{#if selectedLogId}
	<div class="fixed inset-0 z-[150] flex items-center justify-center p-4">
		<button
			type="button"
			class="absolute inset-0 bg-ink-950/55 backdrop-blur-[14px] border-0"
			aria-label="Close details"
			onclick={closeDetail}
		></button>
		<div class="material-perspective w-full max-w-3xl relative z-[160]">
			<div
				class="relative w-full max-h-[85vh] overflow-auto card material-card-3d p-6"
				role="dialog"
				aria-modal="true"
				aria-label="Audit log detail"
			>
				<div class="flex items-center justify-between mb-4">
					<h3 class="text-lg font-bold">Audit Log Detail</h3>
					<button type="button" class="btn btn-secondary material-button-3d text-xs px-4 py-2" onclick={closeDetail}>Close</button>
				</div>
				{#if loadingDetail}
					<div class="skeleton h-5 w-64 mb-2"></div>
					<div class="skeleton h-5 w-full mb-2"></div>
					<div class="skeleton h-5 w-full"></div>
				{:else if selectedDetail}
					<div class="space-y-4 text-sm text-ink-300">
						<div><strong>ID:</strong> <span class="font-mono text-xs text-ink-50">{selectedDetail.id}</span></div>
						<div><strong>Event:</strong> <span class="font-mono text-ink-50">{selectedDetail.event_type}</span></div>
						<div><strong>Timestamp:</strong> {formatDate(selectedDetail.event_timestamp)}</div>
						<div><strong>Actor:</strong> {selectedDetail.actor_email || '-'}</div>
						<div><strong>IP:</strong> {selectedDetail.actor_ip || '-'}</div>
						<div>
							<strong>Request:</strong>
							<span class="font-mono text-ink-100">{selectedDetail.request_method || '-'} {selectedDetail.request_path || '-'}</span>
						</div>
						<div>
							<strong>Resource:</strong>
							{selectedDetail.resource_type || '-'} <span class="font-mono text-ink-100">{selectedDetail.resource_id || ''}</span>
						</div>
						<div>
							<strong>Status:</strong>
							<span class="badge {selectedDetail.success ? 'badge-success' : 'badge-warning'}">
								{selectedDetail.success ? 'SUCCESS' : 'FAILED'}
							</span>
						</div>
						{#if selectedDetail.error_message}
							<div><strong>Error:</strong> <span class="text-danger-400">{selectedDetail.error_message}</span></div>
						{/if}
						<div>
							<strong>Details JSON:</strong>
							<pre class="mt-2 p-3 rounded-lg bg-ink-950/80 border border-ink-700/30 text-xs overflow-auto font-mono text-ink-100">{JSON.stringify(
									selectedDetail.details || {},
									null,
									2
								)}</pre>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
