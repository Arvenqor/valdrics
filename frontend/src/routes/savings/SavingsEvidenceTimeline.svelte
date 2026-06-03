<script lang="ts">
	import { AlertTriangle, CheckCircle2, Clock } from '@lucide/svelte';
	import type { RealizedSavingsEvent } from './savingsTypes';
	import {
		evidenceEventLocation,
		evidenceEventTimestamp,
		evidenceEventTitle,
		providerAccent,
		providerLabel,
		savingsAccentStyle
	} from './savingsViewModel';

	let {
		realizedEvents,
		realizedEventsError,
		formatUsd,
		formatDate
	}: {
		realizedEvents: RealizedSavingsEvent[];
		realizedEventsError: string;
		formatUsd: (value: number) => string;
		formatDate: (value: string) => string;
	} = $props();
</script>

<section class="savings-panel savings-evidence-panel" aria-labelledby="savings-evidence-title">
	<div class="savings-panel__header">
		<div>
			<h2 id="savings-evidence-title">
				Completed remediations with finance-grade realized savings evidence
			</h2>
			<p>Finding provenance carried from discovery through execution and measurement.</p>
		</div>
		<span class="savings-panel__meta">{realizedEvents.length} events</span>
	</div>

	{#if realizedEventsError}
		<div class="savings-inline-alert savings-inline-alert--warning" role="status">
			<AlertTriangle size={16} />
			<span>{realizedEventsError}</span>
		</div>
	{/if}

	{#if realizedEvents.length === 0}
		<div class="savings-empty-state savings-empty-state--tall">
			<CheckCircle2 size={24} />
			<p>No realized savings evidence events were found for this window.</p>
		</div>
	{:else}
		<div class="savings-event-list">
			{#each realizedEvents as event (event.remediation_request_id)}
				{@const accent = providerAccent(event.provider)}
				<article class="savings-event-row" style={savingsAccentStyle(accent)}>
					<div class="savings-event-row__rail" aria-hidden="true">
						<span></span>
					</div>
					<div class="savings-event-row__body">
						<div class="savings-event-row__top">
							<span class="savings-provider-chip">{providerLabel(event.provider)}</span>
							<span class="savings-raw-chip">{event.finding_category || 'unknown'}</span>
						</div>
						<h3>{evidenceEventTitle(event)}</h3>
						<dl class="savings-event-row__meta">
							<div>
								<dt>Resource</dt>
								<dd>{event.resource_id || '-'}</dd>
							</div>
							<div>
								<dt>Scope</dt>
								<dd>{evidenceEventLocation(event)}</dd>
							</div>
							<div>
								<dt>Method</dt>
								<dd>{event.method}</dd>
							</div>
							<div>
								<dt>Confidence</dt>
								<dd>
									{event.confidence_score === null
										? 'n/a'
										: `${Math.round(event.confidence_score * 100)}%`}
								</dd>
							</div>
						</dl>
						<p class="savings-event-row__window">
							{event.baseline_start_date} to {event.baseline_end_date} baseline ·
							{event.measurement_start_date} to {event.measurement_end_date} measured
						</p>
					</div>
					<div class="savings-event-row__amount">
						<strong>{formatUsd(event.realized_monthly_savings_usd)}</strong>
						<span>/mo realized</span>
						<small>
							<Clock size={12} />
							{formatDate(evidenceEventTimestamp(event))}
						</small>
					</div>
				</article>
			{/each}
		</div>
	{/if}
</section>
