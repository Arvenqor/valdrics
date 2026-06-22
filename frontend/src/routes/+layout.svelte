<!--
  Root Layout - Premium SaaS Design (2026)

  Features:
  - Collapsible sidebar navigation
  - Clean header with user menu
  - Motion-enhanced page transitions
  - Responsive design
-->

<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve */
	import '../app.css';
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';
	import { uiState } from '$lib/stores/ui.svelte';
	import type { Toast } from '$lib/stores/ui.svelte';
	import { base } from '$app/paths';
	import { canAccessAdminHealth } from '$lib/entitlements';
	import { allowedNavHrefs, normalizePersona } from '$lib/persona';
	import { createLazyComponent } from '$lib/lazyComponent';
	import { buildPublicAuthHref } from '$lib/public/publicAppOrigin';
	import { isPublicPath } from '$lib/routeProtection';
	import PublicSiteShell from './layout/PublicSiteShell.svelte';
	import AppAuthenticatedShell from './layout/AppAuthenticatedShell.svelte';

	type ToastComponentProps = { toast: Toast };
	type PublicTone = 'default' | 'landing';
	type NavItem = { href: string; label: string; icon: string };
	type SubscriptionSummary = {
		tier?: string | null;
		status?: string | null;
	} | null;
	const loadToastComponent = createLazyComponent<ToastComponentProps>(
		() => import('$lib/components/Toast.svelte')
	);
	let { data, children } = $props();

	const currentYear = new Date().getFullYear();

	const allNavItems: NavItem[] = [
		{
			href: '/dashboard',
			label: 'Dashboard',
			icon: 'M3 12l2-2 7-7 7 7 2 2M5 10v10a1 1 0 0 0 1 1h3v-5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v5h3a1 1 0 0 0 1-1V10'
		},
		{
			href: '/ops',
			label: 'Ops Center',
			icon: 'M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.8-3.8a6 6 0 0 1-7.9 7.9l-6.9 6.9a2.1 2.1 0 0 1-3-3l6.9-6.9a6 6 0 0 1 7.9-7.9l-3.8 3.8Z'
		},
		{
			href: '/approvals',
			label: 'Approvals',
			icon: 'M9 12l2 2 4-4M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z'
		},
		{
			href: '/onboarding',
			label: 'Onboarding',
			icon: 'M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83M12 8l3 4-3 4-3-4 3-4Z'
		},
		{
			href: '/roi-planner',
			label: 'ROI Planner',
			icon: 'M3 17l6-6 4 4 8-8M14 7h7v7'
		},
		{
			href: '/audit',
			label: 'Audit Logs',
			icon: 'M9 11h6M9 15h6M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z'
		},
		{
			href: '/connections',
			label: 'Connections',
			icon: 'M17.5 19H8a5 5 0 1 1 1.8-9.7A7 7 0 0 1 23 12a4 4 0 0 1-5.5 7Z'
		},
		{
			href: '/inventory',
			label: 'Inventory',
			icon: 'M3 7l9-4 9 4-9 4-9-4ZM3 7v10l9 4 9-4V7M12 11v10'
		},
		{
			href: '/greenops',
			label: 'GreenOps',
			icon: 'M11 20A7 7 0 0 1 4 13c0-5 4-8 12-9 1 8-2 12-7 12M20 20c-3-3-6-4-11-4'
		},
		{
			href: '/llm',
			label: 'LLM Usage',
			icon: 'M9 3h6v3h3v6h3v6h-3v3h-6v-3H9v3H3v-6h3v-6H3V6h6V3ZM9 9v6h6V9H9Z'
		},
		{
			href: '/billing',
			label: 'Billing',
			icon: 'M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7ZM3 10h18M7 15h4'
		},
		{
			href: '/leaderboards',
			label: 'Leaderboards',
			icon: 'M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4ZM5 6H3v2a4 4 0 0 0 4 4M19 6h2v2a4 4 0 0 1-4 4'
		},
		{
			href: '/savings',
			label: 'Savings Proof',
			icon: 'M12 3v18M17 7.5A4 4 0 0 0 12 6c-2.2 0-4 .9-4 2.5S9.8 11 12 11s4 .9 4 2.5S14.2 16 12 16a5 5 0 0 1-5-2'
		},
		{
			href: '/settings',
			label: 'Settings',
			icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6ZM19.4 15a1.7 1.7 0 0 0 .34 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.7 1.7 0 0 0-1-1.51 1.7 1.7 0 0 0-1.82.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.6 9a1.7 1.7 0 0 0-.34-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09A1.7 1.7 0 0 0 15 4.6a1.7 1.7 0 0 0 1.82-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9a1.7 1.7 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09A1.7 1.7 0 0 0 19.4 15Z'
		},
		{
			href: '/admin/health',
			label: 'Admin Health',
			icon: 'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 1 0-7.8 7.8l1 1L12 21l7.8-7.6 1-1a5.5 5.5 0 0 0 0-7.8ZM8 12h2l1.5-3 2 6 1.5-3h2'
		}
	];

	let persona = $derived(normalizePersona(data.profile?.persona));
	let role = $derived(String(data.profile?.role ?? 'member'));
	let platformOperator = $derived(Boolean(data.profile?.platform_operator));

	let visibleNavItems = $derived(
		allNavItems.filter((item) => {
			if (item.href !== '/admin/health') return true;
			return canAccessAdminHealth(role, platformOperator);
		})
	);
	let allowlist = $derived(allowedNavHrefs(persona, role, { platformOperator }));
	let primaryNavItems = $derived(visibleNavItems.filter((item) => allowlist.has(item.href)));
	let secondaryNavItems = $derived(visibleNavItems.filter((item) => !allowlist.has(item.href)));
	let activeSecondaryNavItems = $derived(secondaryNavItems.filter((item) => isActive(item.href)));

	function toAppPath(path: string): string {
		const normalizedPath = path.startsWith('/') ? path : `/${path}`;
		const normalizedBase = base === '/' ? '' : base;
		return `${normalizedBase}${normalizedPath}`;
	}

	function getAbsoluteAppPath(path: string): string {
		const baseStr = String(base);
		const cleanBase = (baseStr === '.' || baseStr === './') ? '' : baseStr;
		const normalizedPath = path.startsWith('/') ? path : `/${path}`;
		return `${cleanBase}${normalizedPath}`;
	}

	function toAuthPath(path: string): string {
		return buildPublicAuthHref(toAppPath(path), $page.url);
	}

	function resolvePublicTone(pathname: string): PublicTone {
		const target = getAbsoluteAppPath('/');
		return pathname === target || pathname === target + '/' || pathname + '/' === target ? 'landing' : 'default';
	}

	let publicTone = $derived(resolvePublicTone($page.url.pathname));
	let usesAppShell = $derived(!isPublicPath($page.url.pathname));
	let canonicalHref = $derived(new URL($page.url.pathname, $page.url.origin).toString());
	let shouldNoIndex = $derived(
		!!data.user ||
			$page.url.pathname === getAbsoluteAppPath('/auth') ||
			$page.url.pathname.startsWith(`${getAbsoluteAppPath('/auth')}/`)
	);

	function isActive(href: string): boolean {
		const resolvedHref = getAbsoluteAppPath(href);
		if (resolvedHref === getAbsoluteAppPath('/')) {
			return $page.url.pathname === resolvedHref;
		}
		return $page.url.pathname.startsWith(resolvedHref);
	}
</script>

<svelte:head>
	<link rel="canonical" href={canonicalHref} />
	<meta name="robots" content={shouldNoIndex ? 'noindex,nofollow' : 'index,follow'} />
</svelte:head>

<div class="layout-root">
	<a href="#main" class="skip-link">Skip to content</a>
	<noscript>
		<div class="noscript-banner" data-noscript-banner>
			<div class="noscript-banner__copy">
				<strong>JavaScript is disabled.</strong>
				<span>
					Public pages remain readable, but sign-in, live telemetry, and dashboard actions require
					JavaScript.
				</span>
			</div>
			<nav class="noscript-banner__links" aria-label="No JavaScript fallback links">
				<a href={toAppPath('/pricing')}>Pricing</a>
				<a href={toAppPath('/resources')}>Resources</a>
				<a href={toAppPath('/docs')}>Docs</a>
				<a href={toAppPath('/status')}>Status</a>
				<a href={toAppPath('/privacy')}>Privacy</a>
				<a href={toAppPath('/terms')}>Terms</a>
			</nav>
		</div>
	</noscript>
	{#if usesAppShell && data.user}
		<AppAuthenticatedShell
			user={data.user}
			subscription={data.subscription}
			{primaryNavItems}
			{secondaryNavItems}
			{activeSecondaryNavItems}
			{persona}
			{role}
			{platformOperator}
			{toAppPath}
			{isActive}
		>
			{@render children()}
		</AppAuthenticatedShell>
	{:else}
		<PublicSiteShell {currentYear} {toAppPath} {toAuthPath} {publicTone}>
			{@render children()}
		</PublicSiteShell>
	{/if}
</div>

{#if uiState.toasts.length > 0}
	<div class="layout-toast-region">
		{#await loadToastComponent() then { default: ToastComponent }}
			<div class="layout-toast-stack">
				{#each uiState.toasts as toast (toast.id)}
					<ToastComponent {toast} />
				{/each}
			</div>
		{/await}
	</div>
{/if}
