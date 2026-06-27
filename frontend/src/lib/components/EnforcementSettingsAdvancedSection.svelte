<script lang="ts">
	import { onMount } from 'svelte';
	import { BadgeDollarSign, Clock, ShieldCheck } from '@lucide/svelte';
	import {
		createEnforcementCredit,
		loadEnforcementBudgets,
		loadEnforcementCredits,
		saveEnforcementBudget
	} from './enforcementSettingsApi';
	import {
		type EnforcementBudget,
		type EnforcementCredit
	} from './enforcementSettingsModel';
	import { formatUsd } from '$lib/format';

	let { accessToken }: { accessToken?: string | null } = $props();

	let budgets = $state<EnforcementBudget[]>([]);
	let credits = $state<EnforcementCredit[]>([]);
	let loading = $state(true);
	let savingBudget = $state(false);
	let savingCredit = $state(false);
	let error = $state('');
	let success = $state('');

	let budgetForm = $state({
		scope_key: 'default',
		monthly_limit_usd: 0,
		active: true
	});

	let creditForm = $state({
		scope_key: 'default',
		total_amount_usd: 0,
		expires_at: '',
		reason: ''
	});
	const activeBudgetCount = $derived(budgets.filter((budget) => budget.active).length);
	const activeCreditCount = $derived(credits.filter((credit) => credit.active).length);
	const monthlyLimitTotal = $derived(
		budgets.reduce((total, budget) => total + Number(budget.monthly_limit_usd || 0), 0)
	);
	const remainingCreditTotal = $derived(
		credits.reduce((total, credit) => total + Number(credit.remaining_amount_usd || 0), 0)
	);

	async function loadAdvancedState() {
		loading = true;
		error = '';
		success = '';
		try {
			if (!accessToken) {
				budgets = [];
				credits = [];
				return;
			}
			const [nextBudgets, nextCredits] = await Promise.all([
				loadEnforcementBudgets(accessToken),
				loadEnforcementCredits(accessToken)
			]);
			budgets = nextBudgets;
			credits = nextCredits;
		} catch (nextError) {
			const err = nextError as Error;
			error = err.message || 'Failed to load budget and credit controls';
		} finally {
			loading = false;
		}
	}

	async function upsertBudget() {
		savingBudget = true;
		error = '';
		success = '';
		try {
			const payload = {
				scope_key: budgetForm.scope_key.trim() || 'default',
				monthly_limit_usd: Number(budgetForm.monthly_limit_usd),
				active: budgetForm.active
			};
			await saveEnforcementBudget(accessToken, payload);
			await loadAdvancedState();
			success = 'Enforcement budget saved.';
		} catch (nextError) {
			const err = nextError as Error;
			error = err.message || 'Failed to save enforcement budget';
		} finally {
			savingBudget = false;
		}
	}

	async function createCredit() {
		savingCredit = true;
		error = '';
		success = '';
		try {
			const payload = {
				scope_key: creditForm.scope_key.trim() || 'default',
				total_amount_usd: Number(creditForm.total_amount_usd),
				expires_at: creditForm.expires_at ? new Date(creditForm.expires_at).toISOString() : null,
				reason: creditForm.reason.trim() || null
			};
			await createEnforcementCredit(accessToken, payload);
			creditForm = {
				scope_key: creditForm.scope_key,
				total_amount_usd: 0,
				expires_at: '',
				reason: ''
			};
			await loadAdvancedState();
			success = 'Enforcement credit created.';
		} catch (nextError) {
			const err = nextError as Error;
			error = err.message || 'Failed to create enforcement credit';
		} finally {
			savingCredit = false;
		}
	}

	onMount(() => {
		void loadAdvancedState();
	});
</script>

<div class="space-y-6 enforcement-advanced">
	{#if error}
		<div role="alert" class="card border-danger-500/50 bg-danger-500/10">
			<p class="text-danger-400 text-sm">{error}</p>
		</div>
	{/if}

	{#if success}
		<div role="status" class="card border-success-500/50 bg-success-500/10">
			<p class="text-success-400 text-sm">{success}</p>
		</div>
	{/if}

	<div class="enforcement-advanced__summary" aria-label="Budget and credit summary">
		<div class="enforcement-advanced__summary-card">
			<ShieldCheck size={17} aria-hidden="true" />
			<span>Active budgets</span>
			<strong>{activeBudgetCount}</strong>
		</div>
		<div class="enforcement-advanced__summary-card">
			<BadgeDollarSign size={17} aria-hidden="true" />
			<span>Monthly envelope</span>
			<strong>{formatUsd(monthlyLimitTotal)}</strong>
		</div>
		<div class="enforcement-advanced__summary-card">
			<Clock size={17} aria-hidden="true" />
			<span>Active credits</span>
			<strong>{activeCreditCount}</strong>
		</div>
		<div class="enforcement-advanced__summary-card">
			<BadgeDollarSign size={17} aria-hidden="true" />
			<span>Credit remaining</span>
			<strong>{formatUsd(remainingCreditTotal)}</strong>
		</div>
	</div>

	<div class="enforcement-advanced__section">
		<div class="enforcement-advanced__section-header">
			<div>
				<h3>Budget Allocations</h3>
				<p>Tenant-scoped monthly envelopes evaluated by the enforcement service.</p>
			</div>
		</div>
		<div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
			<div class="form-group">
				<label for="enforcement_budget_scope">Scope Key</label>
				<input
					id="enforcement_budget_scope"
					bind:value={budgetForm.scope_key}
					aria-label="Enforcement budget scope key"
				/>
			</div>
			<div class="form-group">
				<label for="enforcement_budget_limit">Monthly Limit (USD)</label>
				<input
					type="number"
					id="enforcement_budget_limit"
					min="0"
					step="0.01"
					bind:value={budgetForm.monthly_limit_usd}
					aria-label="Enforcement budget monthly limit"
				/>
			</div>
			<label class="flex items-center gap-3 cursor-pointer mt-7">
				<input
					type="checkbox"
					class="toggle"
					bind:checked={budgetForm.active}
					aria-label="Enforcement budget active"
				/>
				<span>Active</span>
			</label>
		</div>
		<button
			type="button"
			class="btn btn-secondary mb-3"
			onclick={upsertBudget}
			disabled={savingBudget}
			aria-label="Save enforcement budget"
		>
			{savingBudget ? 'Saving...' : 'Save Budget'}
		</button>

		{#if loading}
			<div class="skeleton h-4 w-48"></div>
		{:else if budgets.length === 0}
			<p class="text-xs text-ink-500">No budgets configured yet.</p>
		{:else}
			<div class="overflow-x-auto enforcement-advanced__table-wrap">
				<table class="w-full text-sm">
					<thead>
						<tr class="text-left text-ink-500">
							<th class="py-2">Scope</th>
							<th class="py-2">Monthly Limit</th>
							<th class="py-2">Active</th>
						</tr>
					</thead>
					<tbody>
						{#each budgets as row (row.id)}
							<tr class="border-t border-ink-700">
								<td class="py-2">{row.scope_key}</td>
								<td class="py-2">{formatUsd(row.monthly_limit_usd)}</td>
								<td class="py-2">
									<span class:enforcement-advanced__status-on={row.active}>
										{row.active ? 'active' : 'inactive'}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>

	<div class="enforcement-advanced__section">
		<div class="enforcement-advanced__section-header">
			<div>
				<h3>Temporary Credits</h3>
				<p>Short-lived exceptions that preserve audit context while reducing manual overrides.</p>
			</div>
		</div>
		<div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
			<div class="form-group">
				<label for="enforcement_credit_scope">Scope Key</label>
				<input
					id="enforcement_credit_scope"
					bind:value={creditForm.scope_key}
					aria-label="Enforcement credit scope key"
				/>
			</div>
			<div class="form-group">
				<label for="enforcement_credit_total">Credit Amount (USD)</label>
				<input
					type="number"
					id="enforcement_credit_total"
					min="0.01"
					step="0.01"
					bind:value={creditForm.total_amount_usd}
					aria-label="Enforcement credit total amount"
				/>
			</div>
			<div class="form-group">
				<label for="enforcement_credit_expiry">Expiry (optional)</label>
				<input
					type="datetime-local"
					id="enforcement_credit_expiry"
					bind:value={creditForm.expires_at}
					aria-label="Enforcement credit expiry"
				/>
			</div>
			<div class="form-group">
				<label for="enforcement_credit_reason">Reason (optional)</label>
				<input
					id="enforcement_credit_reason"
					bind:value={creditForm.reason}
					aria-label="Enforcement credit reason"
				/>
			</div>
		</div>
		<button
			type="button"
			class="btn btn-secondary mb-3"
			onclick={createCredit}
			disabled={savingCredit}
			aria-label="Create enforcement credit"
		>
			{savingCredit ? 'Creating...' : 'Create Credit'}
		</button>

		{#if loading}
			<div class="skeleton h-4 w-48"></div>
		{:else if credits.length === 0}
			<p class="text-xs text-ink-500">No credits available.</p>
		{:else}
			<div class="overflow-x-auto enforcement-advanced__table-wrap">
				<table class="w-full text-sm">
					<thead>
						<tr class="text-left text-ink-500">
							<th class="py-2">Scope</th>
							<th class="py-2">Remaining</th>
							<th class="py-2">Expires</th>
						</tr>
					</thead>
					<tbody>
						{#each credits as row (row.id)}
							<tr class="border-t border-ink-700">
								<td class="py-2">{row.scope_key}</td>
								<td class="py-2">{formatUsd(row.remaining_amount_usd)}</td>
								<td class="py-2">
									{row.expires_at ? new Date(row.expires_at).toLocaleString() : 'none'}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<style>
	.enforcement-advanced__summary {
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 0.7rem;
		padding-top: 1rem;
		border-top: 1px solid var(--color-ink-700);
	}

	.enforcement-advanced__summary-card,
	.enforcement-advanced__section {
		border: 1px solid rgb(128 154 176 / 0.18);
		border-radius: var(--radius-md);
		background: linear-gradient(180deg, rgb(24 32 40 / 0.72), rgb(10 13 18 / 0.58));
	}

	.enforcement-advanced__summary-card {
		display: grid;
		gap: 0.35rem;
		min-height: 5.85rem;
		padding: 0.85rem;
		color: var(--color-accent-300);
	}

	.enforcement-advanced__summary-card span {
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		font-weight: 700;
		line-height: 1.25;
	}

	.enforcement-advanced__summary-card strong {
		align-self: end;
		color: var(--color-ink-50);
		font-family: var(--font-mono);
		font-size: clamp(0.96rem, 1.6vw, 1.2rem);
		font-weight: 850;
		line-height: 1.1;
		overflow-wrap: anywhere;
	}

	.enforcement-advanced__section {
		padding: 1rem;
	}

	.enforcement-advanced__section-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: 0.9rem;
	}

	.enforcement-advanced__section h3 {
		margin: 0;
		color: var(--color-ink-50);
		font-size: var(--text-sm);
		font-weight: 800;
		letter-spacing: 0;
	}

	.enforcement-advanced__section p {
		margin: 0.25rem 0 0;
		color: var(--color-ink-400);
		font-size: var(--text-xs);
		line-height: 1.5;
	}

	.enforcement-advanced__table-wrap {
		border: 1px solid rgb(128 154 176 / 0.16);
		border-radius: var(--radius-md);
		background: rgb(10 13 18 / 0.34);
	}

	.enforcement-advanced__table-wrap table {
		min-width: 24rem;
	}

	.enforcement-advanced__table-wrap th,
	.enforcement-advanced__table-wrap td {
		padding-inline: 0.75rem;
	}

	.enforcement-advanced__status-on {
		color: var(--color-success-400);
		font-weight: 750;
	}

	@media (max-width: 900px) {
		.enforcement-advanced__summary {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}

	@media (max-width: 640px) {
		.enforcement-advanced__summary {
			grid-template-columns: 1fr;
		}
	}
</style>
