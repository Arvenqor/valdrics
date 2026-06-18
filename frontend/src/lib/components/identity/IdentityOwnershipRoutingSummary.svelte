<script lang="ts">
	import type { IdentitySettings } from './identitySettingsTypes';

	let {
		settings,
		tier
	}: {
		settings: IdentitySettings;
		tier?: string | null;
	} = $props();

	const normalizedTier = $derived((tier ?? '').toLowerCase());
	const isEnterprise = $derived(normalizedTier === 'enterprise');
	const allowedDomainCount = $derived(
		settings.allowed_email_domains.filter((domain) => domain.trim()).length
	);
	const mappedGroupCount = $derived(
		settings.scim_group_mappings.filter((mapping) => mapping.group.trim()).length
	);
	const mappedGroupLabel = $derived(
		`${mappedGroupCount} mapped ${mappedGroupCount === 1 ? 'group' : 'groups'}`
	);

	const domainStatus = $derived.by(() => {
		if (settings.sso_enabled && allowedDomainCount > 0) return 'Active';
		if (allowedDomainCount > 0) return 'Prepared';
		return 'Not configured';
	});

	const federationStatus = $derived.by(() => {
		if (!settings.sso_federation_enabled) return 'Not configured';
		return settings.sso_federation_mode === 'provider_id' ? 'Provider pinned' : 'Domain routed';
	});

	const scimStatus = $derived.by(() => {
		if (!isEnterprise) return 'Enterprise only';
		if (!settings.scim_enabled) return 'Not configured';
		if (mappedGroupCount === 0) return 'Ready for groups';
		return 'Active';
	});

	const rows = $derived([
		{
			label: 'SSO domain guard',
			status: domainStatus,
			detail:
				allowedDomainCount === 0
					? 'No verified domains'
					: `${allowedDomainCount} verified ${allowedDomainCount === 1 ? 'domain' : 'domains'}`,
			active: settings.sso_enabled && allowedDomainCount > 0
		},
		{
			label: 'Federated login',
			status: federationStatus,
			detail:
				settings.sso_federation_mode === 'provider_id'
					? settings.sso_federation_provider_id || 'Provider id required'
					: 'Domain discovery',
			active: settings.sso_federation_enabled
		},
		{
			label: 'SCIM group mapping',
			status: scimStatus,
			detail: isEnterprise ? mappedGroupLabel : 'Upgrade path is enterprise',
			active: isEnterprise && settings.scim_enabled && mappedGroupCount > 0
		}
	]);
</script>

<section class="ownership-routing" aria-labelledby="ownership-routing-title">
	<div class="ownership-routing__header">
		<div>
			<h3 id="ownership-routing-title">Provisioning to ownership</h3>
			<p>
				Verified domains, SSO federation, and SCIM groups route workspace access into Valdrics role
				and persona assignments.
			</p>
		</div>
		<div class="ownership-routing__metric" aria-label={mappedGroupLabel}>
			<strong>{mappedGroupCount}</strong>
			<span>mapped groups</span>
		</div>
	</div>

	<div class="ownership-routing__grid">
		{#each rows as row}
			<div class="ownership-routing__row" class:ownership-routing__row--active={row.active}>
				<div>
					<span class="ownership-routing__label">{row.label}</span>
					<span class="ownership-routing__detail">{row.detail}</span>
				</div>
				<span class="ownership-routing__status">{row.status}</span>
			</div>
		{/each}
	</div>
</section>

<style>
	.ownership-routing {
		border: 1px solid rgba(56, 189, 248, 0.2);
		border-radius: 0.75rem;
		background:
			linear-gradient(135deg, rgba(14, 165, 233, 0.08), rgba(16, 185, 129, 0.08)),
			rgba(2, 6, 23, 0.46);
		padding: 1rem;
	}

	.ownership-routing__header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
	}

	.ownership-routing h3 {
		margin: 0;
		color: rgb(248, 250, 252);
		font-size: 0.95rem;
		font-weight: 650;
		letter-spacing: 0;
	}

	.ownership-routing p {
		margin: 0.35rem 0 0;
		max-width: 42rem;
		color: rgb(148, 163, 184);
		font-size: 0.82rem;
		line-height: 1.55;
	}

	.ownership-routing__metric {
		display: grid;
		min-width: 5.75rem;
		place-items: center;
		border: 1px solid rgba(148, 163, 184, 0.2);
		border-radius: 0.625rem;
		background: rgba(15, 23, 42, 0.72);
		padding: 0.7rem 0.8rem;
		text-align: center;
	}

	.ownership-routing__metric strong {
		color: rgb(255, 255, 255);
		font-size: 1.35rem;
		line-height: 1;
	}

	.ownership-routing__metric span {
		margin-top: 0.3rem;
		color: rgb(148, 163, 184);
		font-size: 0.65rem;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	.ownership-routing__grid {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 0.75rem;
		margin-top: 1rem;
	}

	.ownership-routing__row {
		display: flex;
		min-height: 5.25rem;
		flex-direction: column;
		justify-content: space-between;
		gap: 0.75rem;
		border: 1px solid rgba(148, 163, 184, 0.16);
		border-radius: 0.625rem;
		background: rgba(15, 23, 42, 0.56);
		padding: 0.85rem;
	}

	.ownership-routing__row--active {
		border-color: rgba(52, 211, 153, 0.34);
		background: rgba(6, 78, 59, 0.22);
	}

	.ownership-routing__label,
	.ownership-routing__detail,
	.ownership-routing__status {
		display: block;
	}

	.ownership-routing__label {
		color: rgb(226, 232, 240);
		font-size: 0.77rem;
		font-weight: 650;
	}

	.ownership-routing__detail {
		margin-top: 0.25rem;
		color: rgb(148, 163, 184);
		font-size: 0.72rem;
		line-height: 1.45;
		overflow-wrap: anywhere;
	}

	.ownership-routing__status {
		align-self: flex-start;
		border: 1px solid rgba(148, 163, 184, 0.2);
		border-radius: 999px;
		background: rgba(15, 23, 42, 0.74);
		color: rgb(203, 213, 225);
		font-size: 0.68rem;
		font-weight: 650;
		line-height: 1;
		padding: 0.35rem 0.5rem;
		white-space: nowrap;
	}

	.ownership-routing__row--active .ownership-routing__status {
		border-color: rgba(52, 211, 153, 0.4);
		background: rgba(16, 185, 129, 0.14);
		color: rgb(167, 243, 208);
	}

	@media (max-width: 760px) {
		.ownership-routing__header {
			flex-direction: column;
		}

		.ownership-routing__metric {
			width: 100%;
			grid-auto-flow: column;
			justify-content: center;
			gap: 0.65rem;
		}

		.ownership-routing__metric span {
			margin-top: 0;
		}

		.ownership-routing__grid {
			grid-template-columns: 1fr;
		}
	}
</style>
