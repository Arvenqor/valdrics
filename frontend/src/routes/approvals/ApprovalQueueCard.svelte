<script lang="ts">
	import './ApprovalQueueCard.css';
	import { AlertTriangle, Check, ChevronDown, Clock, FileText, Route, X } from '@lucide/svelte';
	import type { ApprovalQueueItem } from './approvalQueueModel';
	import { formatAction, formatDate, formatMoney, hasCostImpact } from './approvalQueueModel';

	type Props = {
		approval: ApprovalQueueItem;
		decidingApprovalId: string | null;
		onApprove: (approval: ApprovalQueueItem) => void;
		onDeny: (approval: ApprovalQueueItem) => void;
	};

	let { approval, decidingApprovalId, onApprove, onDeny }: Props = $props();
	let expanded = $state(false);

	let detailsId = $derived(`approval-details-${approval.approval_id}`);
	let costImpact = $derived(hasCostImpact(approval));
	let routeLabel = $derived(approval.routing_rule_id ?? 'Default policy route');
	let sourceLabel = $derived(approval.source.toUpperCase());
	let statusLabel = $derived(approval.status.toUpperCase());
</script>

<article class="approval-card" class:approval-card--expanded={expanded}>
	<button
		type="button"
		class="approval-card__row"
		aria-expanded={expanded}
		aria-controls={detailsId}
		onclick={() => (expanded = !expanded)}
	>
		<span
			class="approval-card__stripe"
			class:approval-card__stripe--cost={costImpact}
			aria-hidden="true"
		></span>

		<span class="approval-card__content">
			<span class="approval-card__header">
				<span class="approval-badge approval-badge--source">{sourceLabel}</span>
				<span class="approval-card__name">{approval.project_id}</span>
				<span class="approval-badge">{statusLabel}</span>
			</span>

			<span class="approval-card__action">{formatAction(approval.action)}</span>
			<span class="approval-card__resource">{approval.resource_reference}</span>

			{#if approval.reason_codes.length}
				<span class="approval-card__policies" aria-label="Reason codes">
					{#each approval.reason_codes as reason}
						<span class="policy-badge">
							<AlertTriangle size={12} />
							{formatAction(reason)}
						</span>
					{/each}
				</span>
			{/if}

			<span class="approval-card__meta">
				<span>{approval.environment}</span>
				<span aria-hidden="true">·</span>
				<span>Created {formatDate(approval.created_at)}</span>
				<span aria-hidden="true">·</span>
				<span>Route {routeLabel}</span>
			</span>
		</span>

		<span class="approval-card__right">
			<span class="approval-card__cost">
				<strong>{formatMoney(approval.estimated_monthly_delta_usd)}</strong>
				<small>Cost impact</small>
			</span>
			<ChevronDown
				size={18}
				class={`approval-card__chevron ${expanded ? 'approval-card__chevron--open' : ''}`}
			/>
		</span>
	</button>

	{#if expanded}
		<div id={detailsId} class="approval-card__details">
			<div class="detail-grid">
				<div>
					<Clock size={15} />
					<span>Expires</span>
					<strong>{formatDate(approval.expires_at)}</strong>
				</div>
				<div>
					<Route size={15} />
					<span>Routing rule</span>
					<strong>{routeLabel}</strong>
				</div>
				<div>
					<FileText size={15} />
					<span>Decision</span>
					<strong>{approval.decision_id}</strong>
				</div>
			</div>
		</div>
	{/if}

	<div class="approval-card__actions">
		<button
			type="button"
			class="decision-button decision-button--approve"
			disabled={!!decidingApprovalId}
			aria-busy={decidingApprovalId === `approve:${approval.approval_id}`}
			onclick={() => onApprove(approval)}
		>
			<Check size={16} />
			Approve
		</button>
		<button
			type="button"
			class="decision-button decision-button--deny"
			disabled={!!decidingApprovalId}
			aria-busy={decidingApprovalId === `deny:${approval.approval_id}`}
			onclick={() => onDeny(approval)}
		>
			<X size={16} />
			Deny
		</button>
	</div>
</article>
