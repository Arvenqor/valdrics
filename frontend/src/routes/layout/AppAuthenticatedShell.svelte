<script lang="ts">
	import '../../authenticated.app.css';
	import { browser } from '$app/environment';
	import { invalidate } from '$app/navigation';
	import { base } from '$app/paths';
	import type { Snippet } from 'svelte';
	import {
		AUTH_SESSION_SIGNAL_KEY,
		broadcastAuthSessionChanged
	} from '$lib/auth/authSessionSignal';
	import { uiState } from '$lib/stores/ui.svelte';
	import { createLazyComponent } from '$lib/lazyComponent';
	import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';
	import AuthenticatedBrandMark from './AuthenticatedBrandMark.svelte';
	import AuthenticatedRailLink from './AuthenticatedRailLink.svelte';
	import AuthenticatedTopbarAction from './AuthenticatedTopbarAction.svelte';

	type NavItem = { href: string; label: string; icon: string };
	type CommandPaletteProps = {
		isOpen?: boolean;
		actions?: NavItem[];
		role?: string;
		platformOperator?: boolean;
	};

	interface Props {
		user: { email?: string | null };
		role: string;
		platformOperator: boolean;
		subscription?: { tier?: string | null } | null;
		primaryNavItems: NavItem[];
		secondaryNavItems: NavItem[];
		activeSecondaryNavItems: NavItem[];
		persona: string;
		toAppPath: (path: string) => string;
		isActive: (href: string) => boolean;
		children: Snippet;
	}

	let {
		user,
		role,
		platformOperator,
		subscription,
		primaryNavItems,
		secondaryNavItems,
		activeSecondaryNavItems,
		persona,
		toAppPath,
		isActive,
		children
	}: Props = $props();

	const NAV_SHOW_ALL_KEY = 'valdrics.nav.show_all.v1';
	const AUTH_REVALIDATION_THROTTLE_MS = 3000;
	type LiveJobStore = {
		activeJobsCount: number;
		init: () => Promise<void> | void;
		disconnect: () => void;
	};
	let showAllNav = $state(false);
	let navPreferenceLoaded = $state(false);
	let prefersReducedMotion = $state(false);
	let liveJobStore = $state<LiveJobStore | null>(null);
	let activeJobsCount = $derived(liveJobStore?.activeJobsCount ?? 0);
	let lastAuthRevalidationAt = $state(0);
	const loadCommandPalette = createLazyComponent<CommandPaletteProps>(
		() => import('$lib/components/CommandPalette.svelte')
	);
	let currentNavItem = $derived(
		[...primaryNavItems, ...secondaryNavItems].find((item) => isActive(item.href))
	);
	let pageTitle = $derived(currentNavItem?.label ?? 'Valdrics');
	let workspaceLabel = $derived(resolveWorkspaceLabel(user.email));
	let planLabel = $derived(`${titleCase(subscription?.tier || 'Free')} plan`);
	let accountInitial = $derived((user.email?.trim().charAt(0) || 'V').toUpperCase());

	function titleCase(value: string): string {
		return value
			.split(/[\s_-]+/)
			.filter(Boolean)
			.map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1).toLowerCase()}`)
			.join(' ');
	}

	function resolveWorkspaceLabel(email?: string | null): string {
		const domain = email?.split('@')[1]?.trim();
		if (!domain) return 'Valdrics workspace';
		const organization = domain.split('.')[0]?.replace(/[-_]+/g, ' ');
		return organization ? `${titleCase(organization)} workspace` : 'Valdrics workspace';
	}

	function revalidateAuthState(): void {
		const now = Date.now();
		if (now - lastAuthRevalidationAt < AUTH_REVALIDATION_THROTTLE_MS) {
			return;
		}
		lastAuthRevalidationAt = now;
		void invalidate('supabase:auth');
	}

	$effect(() => {
		if (!browser) return;
		const handleKeydown = (event: KeyboardEvent) => {
			if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
				event.preventDefault();
				uiState.isCommandPaletteOpen = !uiState.isCommandPaletteOpen;
			}
		};
		window.addEventListener('keydown', handleKeydown);
		return () => window.removeEventListener('keydown', handleKeydown);
	});

	$effect(() => {
		if (!browser || navPreferenceLoaded) return;
		const raw = window.localStorage.getItem(NAV_SHOW_ALL_KEY);
		if (raw === null) {
			showAllNav = false;
		} else {
			showAllNav = raw === '1' || raw.toLowerCase() === 'true';
		}
		navPreferenceLoaded = true;
	});

	$effect(() => {
		if (!browser || !navPreferenceLoaded) return;
		window.localStorage.setItem(NAV_SHOW_ALL_KEY, showAllNav ? '1' : '0');
	});

	$effect(() => {
		if (!browser) return;
		if (typeof window.matchMedia !== 'function') {
			prefersReducedMotion = false;
			return;
		}
		const media = window.matchMedia('(prefers-reduced-motion: reduce)');
		const update = () => {
			prefersReducedMotion = media.matches;
		};
		update();
		if (typeof media.addEventListener === 'function') {
			media.addEventListener('change', update);
			return () => media.removeEventListener('change', update);
		}
		media.addListener(update);
		return () => media.removeListener(update);
	});

	$effect(() => {
		if (!browser || typeof window.matchMedia !== 'function') return;
		const media = window.matchMedia('(max-width: 820px)');
		const closeMobileRail = () => {
			if (media.matches) {
				uiState.isSidebarOpen = false;
			}
		};
		closeMobileRail();
		if (typeof media.addEventListener === 'function') {
			media.addEventListener('change', closeMobileRail);
			return () => media.removeEventListener('change', closeMobileRail);
		}
		media.addListener(closeMobileRail);
		return () => media.removeListener(closeMobileRail);
	});

	$effect(() => {
		if (!browser) return;

		const handleFocus = () => {
			revalidateAuthState();
		};
		const handlePageShow = () => {
			revalidateAuthState();
		};
		const handleVisibilityChange = () => {
			if (document.visibilityState === 'visible') {
				revalidateAuthState();
			}
		};
		const handleStorage = (event: StorageEvent) => {
			if (event.key === AUTH_SESSION_SIGNAL_KEY && event.newValue) {
				revalidateAuthState();
			}
		};

		window.addEventListener('focus', handleFocus);
		window.addEventListener('pageshow', handlePageShow);
		window.addEventListener('storage', handleStorage);
		document.addEventListener('visibilitychange', handleVisibilityChange);

		return () => {
			window.removeEventListener('focus', handleFocus);
			window.removeEventListener('pageshow', handlePageShow);
			window.removeEventListener('storage', handleStorage);
			document.removeEventListener('visibilitychange', handleVisibilityChange);
		};
	});

	$effect(() => {
		if (!browser) return;
		let cancelled = false;
		let disconnect: (() => void) | undefined;

		void import('$lib/stores/jobs.svelte').then(({ jobStore }) => {
			if (cancelled) {
				jobStore.disconnect();
				return;
			}
			liveJobStore = jobStore;
			disconnect = () => jobStore.disconnect();
			void jobStore.init();
		});

		return () => {
			cancelled = true;
			liveJobStore = null;
			disconnect?.();
		};
	});
</script>

<svelte:head>
	<link rel="stylesheet" href={`${base}/authenticated-shell.css`} />
</svelte:head>

<aside
	id="sidebar"
	class="authenticated-shell__sidebar"
	class:authenticated-shell__sidebar--collapsed={!uiState.isSidebarOpen}
	aria-label="Valdrics application navigation"
>
	<div class="authenticated-shell__brand">
		<AuthenticatedBrandMark href={toAppPath('/dashboard')} />
	</div>

	<nav class="authenticated-shell__nav" aria-label="Primary app navigation">
		{#each primaryNavItems as item (item.href)}
			<AuthenticatedRailLink
				href={toAppPath(item.href)}
				label={item.label}
				icon={item.icon}
				active={isActive(item.href)}
			/>
		{/each}

		{#if secondaryNavItems.length > 0}
			<div class="authenticated-shell__nav-divider" aria-hidden="true"></div>
			<button
				type="button"
				class="authenticated-shell__rail-item authenticated-shell__rail-item--button"
				onclick={() => (showAllNav = !showAllNav)}
				aria-expanded={showAllNav}
				aria-controls="sidebar-more-nav"
				aria-label={showAllNav
					? `Hide extra navigation and return to ${persona} view`
					: `Show ${secondaryNavItems.length} extra navigation items`}
				title={showAllNav ? `Hide extras` : `Show all (${secondaryNavItems.length})`}
			>
				<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<path d={showAllNav ? 'M5 12h14' : 'M12 5v14M5 12h14'} />
				</svg>
				<span class="authenticated-shell__rail-tooltip">
					{showAllNav ? 'Hide extras' : `Show all (${secondaryNavItems.length})`}
				</span>
			</button>

			{#if !showAllNav && activeSecondaryNavItems.length > 0}
				<div class="authenticated-shell__active-secondary">
					{#each activeSecondaryNavItems as item (item.href)}
						<AuthenticatedRailLink
							href={toAppPath(item.href)}
							label={item.label}
							icon={item.icon}
							active
						/>
					{/each}
				</div>
			{/if}
			{#if showAllNav}
				<div id="sidebar-more-nav" class="authenticated-shell__more-nav">
					{#each secondaryNavItems as item (item.href)}
						<AuthenticatedRailLink
							href={toAppPath(item.href)}
							label={item.label}
							icon={item.icon}
							active={isActive(item.href)}
						/>
					{/each}
				</div>
			{/if}
		{/if}
	</nav>

	<div class="authenticated-shell__account">
		<div
			class="authenticated-shell__avatar"
			title={`${workspaceLabel} - ${user.email ?? 'account'}`}
			aria-label={`${workspaceLabel} account`}
		>
			{accountInitial}
		</div>
		<form method="POST" action={toAppPath('/auth/logout')} onsubmit={broadcastAuthSessionChanged}>
			<button
				type="submit"
				class="authenticated-shell__rail-item authenticated-shell__rail-item--button authenticated-shell__signout"
				aria-label="Sign out"
				title="Sign out"
			>
				<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
					<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3" />
				</svg>
				<span class="authenticated-shell__rail-tooltip">Sign out</span>
			</button>
		</form>
	</div>
</aside>

<main
	id="main"
	tabindex="-1"
	class="authenticated-shell__main"
	class:authenticated-shell__main--sidebar-collapsed={!uiState.isSidebarOpen}
>
	<header class="authenticated-shell__topbar">
		<div class="authenticated-shell__topbar-inner">
			<div class="authenticated-shell__topbar-left">
				<button
					type="button"
					class="authenticated-shell__icon-button authenticated-shell__sidebar-toggle"
					onclick={() => uiState.toggleSidebar()}
					aria-label="Toggle sidebar"
					aria-controls="sidebar"
					aria-expanded={uiState.isSidebarOpen}
				>
					<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
						<path d="M4 7h16M4 12h16M4 17h16" />
					</svg>
				</button>
				<div class="authenticated-shell__page-identity">
					<p class="authenticated-shell__page-title">{pageTitle}</p>
					<p class="authenticated-shell__page-subtitle">{workspaceLabel} · {planLabel}</p>
				</div>
			</div>

			<div class="authenticated-shell__topbar-actions">
				<AuthenticatedTopbarAction
					href={toAppPath('/approvals')}
					label="Approvals"
					icon="M9 12l2 2 4-4M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z"
					tone="primary"
				/>
				<AuthenticatedTopbarAction
					href={toAppPath('/audit')}
					label="Audit"
					icon="M9 11h6M9 15h6M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2Z"
				/>
				<button
					type="button"
					class="authenticated-shell__command-button"
					onclick={() => (uiState.isCommandPaletteOpen = true)}
					aria-label="Open command palette"
				>
					<kbd class="authenticated-shell__kbd">⌘</kbd>
					<kbd class="authenticated-shell__kbd">K</kbd>
				</button>
				{#if activeJobsCount > 0}
					<div class="authenticated-shell__jobs-pill">
						<span class="authenticated-shell__jobs-indicator">
							<span class="authenticated-shell__jobs-ping"></span>
							<span class="authenticated-shell__jobs-dot"></span>
						</span>
						<span class="authenticated-shell__jobs-label">
							{activeJobsCount} Active {activeJobsCount === 1 ? 'Job' : 'Jobs'}
						</span>
					</div>
				{/if}
			</div>
		</div>
	</header>

	<div class="authenticated-shell__content" class:authenticated-shell-enter={!prefersReducedMotion}>
		<ErrorBoundary>
			{@render children()}
		</ErrorBoundary>
	</div>
</main>

{#if uiState.isCommandPaletteOpen}
	{#await loadCommandPalette() then { default: CommandPalette }}
		<CommandPalette
			actions={[...primaryNavItems, ...secondaryNavItems]}
			{role}
			{platformOperator}
			bind:isOpen={
				() => uiState.isCommandPaletteOpen, (value) => (uiState.isCommandPaletteOpen = value)
			}
		/>
	{/await}
{/if}
