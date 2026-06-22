<script lang="ts">
	import AuthGate from '$lib/components/AuthGate.svelte';
	import UpgradeNotice from '$lib/components/UpgradeNotice.svelte';
	import type { AuditDetail, AuditLog } from './auditTypes';
	import { FOCUS_EXPORT_PROVIDER_OPTIONS } from './auditExportContracts';
	import AuditDetailModal from './AuditDetailModal.svelte';
	import AuditEventsTable from './AuditEventsTable.svelte';

	interface Props {
		data: {
			user?: unknown;
			subscription?: { tier?: string | null } | null;
		};
		canAccessAudit: boolean;
		loading: boolean;
		loadingDetail: boolean;
		exporting: boolean;
		exportingPack: boolean;
		exportingFocus: boolean;
		error: string;
		success: string;
		logs: AuditLog[];
		eventTypes: string[];
		selectedEventType: string;
		limit: number;
		offset: number;
		selectedLogId: string | null;
		selectedDetail: AuditDetail | null;
		focusStartDate: string;
		focusEndDate: string;
		focusProvider: string;
		focusIncludePreliminary: boolean;
		packIncludeFocus: boolean;
		packIncludeSavingsProof: boolean;
		packIncludeClosePackage: boolean;
		packCloseEnforceFinalized: boolean;
		packCloseMaxRestatements: number;
		formatDate: (value: string) => string;
		applyFilters: () => Promise<void>;
		previousPage: () => Promise<void>;
		nextPage: () => Promise<void>;
		exportCsv: () => Promise<void>;
		exportCompliancePack: () => Promise<void>;
		exportFocusCsv: () => Promise<void>;
		viewDetail: (id: string) => Promise<void>;
		closeDetail: () => void;
	}

	let {
		data,
		canAccessAudit,
		loading,
		loadingDetail,
		exporting,
		exportingPack,
		exportingFocus,
		error,
		success,
		logs,
		eventTypes,
		selectedEventType = $bindable(),
		limit = $bindable(),
		offset,
		selectedLogId,
		selectedDetail,
		focusStartDate = $bindable(),
		focusEndDate = $bindable(),
		focusProvider = $bindable(),
		focusIncludePreliminary = $bindable(),
		packIncludeFocus = $bindable(),
		packIncludeSavingsProof = $bindable(),
		packIncludeClosePackage = $bindable(),
		packCloseEnforceFinalized = $bindable(),
		packCloseMaxRestatements = $bindable(),
		formatDate,
		applyFilters,
		previousPage,
		nextPage,
		exportCsv,
		exportCompliancePack,
		exportFocusCsv,
		viewDetail,
		closeDetail
	}: Props = $props();
</script>

<div class="space-y-8">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold mb-1">Audit Logs</h1>
			<p class="text-ink-400 text-sm">
				Security and governance event trail for compliance workflows.
			</p>
		</div>
	</div>

	<AuthGate
		authenticated={!!data.user}
		action="access audit logs"
		className="card text-center py-10"
	>
		{#if !canAccessAudit}
			<div class="space-y-4">
				<UpgradeNotice
					currentTier={data.subscription?.tier}
					requiredTier="pro"
					feature="audit logs and compliance exports"
				/>
				<div class="material-perspective">
					<div class="card material-card-3d border-ink-700/60 bg-ink-900/40 text-left p-6">
						<p class="text-sm text-ink-300">
							Audit logs require an admin role on a Pro or Enterprise workspace. Upgrade the plan,
							then return here for event trails, FOCUS exports, and compliance packs.
						</p>
					</div>
				</div>
			</div>
		{:else}
			{#if error}
				<div class="material-perspective">
					<div class="card material-card-3d border-danger-500/50 bg-danger-500/10 p-4 mb-4">
						<p class="text-danger-400">{error}</p>
					</div>
				</div>
			{/if}
			{#if success}
				<div class="material-perspective">
					<div class="card material-card-3d border-success-500/50 bg-success-500/10 p-4 mb-4">
						<p class="text-success-400">{success}</p>
					</div>
				</div>
			{/if}

			<div class="material-perspective">
				<div class="card material-card-3d p-6 mb-6">
					<div class="flex flex-wrap gap-4 items-end">
						<div class="flex flex-col gap-1">
							<label class="text-xs text-ink-400 font-bold uppercase tracking-wider" for="event-type"
								>Event Type</label
							>
							<select id="event-type" bind:value={selectedEventType} class="select-input mt-1">
								<option value="">All events</option>
								{#each eventTypes as type (type)}
									<option value={type}>{type}</option>
								{/each}
							</select>
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs text-ink-400 font-bold uppercase tracking-wider" for="limit">Page Size</label
							>
							<select id="limit" bind:value={limit} class="select-input mt-1">
								<option value={20}>20</option>
								<option value={50}>50</option>
								<option value={100}>100</option>
							</select>
						</div>
						<div class="flex flex-wrap gap-2">
							<button type="button" class="btn btn-secondary material-button-3d text-xs px-4 py-2" onclick={applyFilters}
								>Apply</button
							>
							<button type="button" class="btn btn-secondary material-button-3d text-xs px-4 py-2" onclick={previousPage}
								>Prev</button
							>
							<button type="button" class="btn btn-secondary material-button-3d text-xs px-4 py-2" onclick={nextPage}>Next</button>
							<button
								type="button"
								class="btn btn-primary material-button-3d text-xs px-4 py-2"
								disabled={exporting}
								onclick={exportCsv}
							>
								{exporting ? 'Exporting...' : 'Export CSV'}
							</button>
							<button
								type="button"
								class="btn btn-primary material-button-3d text-xs px-4 py-2"
								disabled={exportingPack}
								onclick={exportCompliancePack}
							>
								{exportingPack ? 'Exporting...' : 'Compliance Pack'}
							</button>
						</div>
					</div>
				</div>
			</div>

			<div class="material-perspective">
				<div class="card material-card-3d p-6 mb-6">
					<h2 class="text-lg font-bold mb-1">Compliance Exports</h2>
					<p class="text-ink-400 text-sm mb-4">
						Download FOCUS v1.3 core CSV (Pro+) or bundle exports into the Compliance Pack ZIP
						(Owner).
					</p>
					<div class="flex flex-wrap gap-4 items-end">
						<div class="flex flex-col gap-1">
							<label class="text-xs text-ink-400 font-bold uppercase tracking-wider" for="focus-start"
								>Start</label
							>
							<input id="focus-start" type="date" class="select-input mt-1" bind:value={focusStartDate} />
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs text-ink-400 font-bold uppercase tracking-wider" for="focus-end">End</label>
							<input id="focus-end" type="date" class="select-input mt-1" bind:value={focusEndDate} />
						</div>
						<div class="flex flex-col gap-1">
							<label class="text-xs text-ink-400 font-bold uppercase tracking-wider" for="focus-provider"
								>Provider</label
							>
							<select id="focus-provider" bind:value={focusProvider} class="select-input mt-1">
								{#each FOCUS_EXPORT_PROVIDER_OPTIONS as option (option.value)}
									<option value={option.value}>{option.label}</option>
								{/each}
							</select>
						</div>
						<label class="flex items-center gap-2 text-xs text-ink-300 cursor-pointer pb-2">
							<input
								type="checkbox"
								class="accent-accent-500"
								bind:checked={focusIncludePreliminary}
							/>
							<span>Include preliminary</span>
						</label>
						<button
							type="button"
							class="btn btn-primary material-button-3d text-xs px-4 py-2"
							disabled={exportingFocus}
							onclick={exportFocusCsv}
						>
							{exportingFocus ? 'Exporting...' : 'FOCUS CSV'}
						</button>
					</div>

					<div class="mt-6 border-t border-ink-700/40 pt-4">
						<h3 class="text-sm font-semibold mb-2">Compliance Pack Add-ons</h3>
						<p class="text-ink-400 text-xs mb-4">
							Optional exports included inside the ZIP. FOCUS uses the selected provider; Savings
							Proof and Close Package ignore the AI filter until AI close evidence is available.
						</p>
						<div class="flex flex-wrap gap-4 items-center">
							<label class="flex items-center gap-2 text-xs text-ink-300 cursor-pointer">
								<input type="checkbox" class="accent-accent-500" bind:checked={packIncludeFocus} />
								<span>Include FOCUS CSV</span>
							</label>
							<label class="flex items-center gap-2 text-xs text-ink-300 cursor-pointer">
								<input
									type="checkbox"
									class="accent-accent-500"
									bind:checked={packIncludeSavingsProof}
								/>
								<span>Include Savings Proof</span>
							</label>
							<label class="flex items-center gap-2 text-xs text-ink-300 cursor-pointer">
								<input
									type="checkbox"
									class="accent-accent-500"
									bind:checked={packIncludeClosePackage}
								/>
								<span>Include Close Package</span>
							</label>
							{#if packIncludeClosePackage}
								<label class="flex items-center gap-2 text-xs text-ink-300 cursor-pointer">
									<input
										type="checkbox"
										class="accent-accent-500"
										bind:checked={packCloseEnforceFinalized}
									/>
									<span>Enforce finalized</span>
								</label>
								<label class="flex items-center gap-2 text-xs text-ink-300">
									<span>Max restatements</span>
									<input
										type="number"
										min="0"
										max="200000"
										step="100"
										class="select-input w-28 ml-2"
										bind:value={packCloseMaxRestatements}
									/>
								</label>
							{/if}
						</div>
					</div>
				</div>
			</div>

			<AuditEventsTable {loading} {logs} onViewDetail={viewDetail} {formatDate} />
		{/if}
	</AuthGate>
</div>

<AuditDetailModal {selectedLogId} {selectedDetail} {loadingDetail} {closeDetail} {formatDate} />

<style>
	.select-input {
		min-width: 180px;
	}
</style>
