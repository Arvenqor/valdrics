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
	import CloudLogo from '$lib/components/CloudLogo.svelte';
	import ErrorBoundary from '$lib/components/ErrorBoundary.svelte';

	type NavItem = { href: string; label: string; icon: string };
	type CommandPaletteProps = {
		isOpen?: boolean;
		actions?: NavItem[];
		role?: string;
		platformOperator?: boolean;
	};

	interface Props {
		user: {
			email?: string | null;
		};
		role: string;
		platformOperator: boolean;
		subscription?: {
			tier?: string | null;
		} | null;
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

<aside id="sidebar" class="sidebar" class:sidebar-collapsed={!uiState.isSidebarOpen}>
	<div class="authenticated-shell__brand">
		<CloudLogo provider="valdrics" size={32} />
		<span class="authenticated-shell__brand-label">Valdrics</span>
	</div>

	<nav class="authenticated-shell__nav">
		{#each primaryNavItems as item (item.href)}
			<a
				href={toAppPath(item.href)}
				class="nav-item"
				class:active={isActive(item.href)}
				aria-current={isActive(item.href) ? 'page' : undefined}
				data-sveltekit-preload-data="hover"
				data-sveltekit-preload-code="hover"
			>
				<span class="text-lg">{item.icon}</span>
				<span>{item.label}</span>
			</a>
		{/each}

		{#if secondaryNavItems.length > 0}
			<div class="authenticated-shell__extras-toggle">
				<button
					type="button"
					class="btn btn-ghost authenticated-shell__extras-button"
					onclick={() => (showAllNav = !showAllNav)}
					aria-expanded={showAllNav}
					aria-controls="sidebar-more-nav"
					title="Your sidebar is filtered by persona. Toggle to show or hide additional pages."
				>
					<span class="capitalize">
						{showAllNav
							? `Hide extras (back to ${persona} view)`
							: `Show all (${secondaryNavItems.length})`}
					</span>
				</button>
			</div>
			{#if !showAllNav && activeSecondaryNavItems.length > 0}
				<div class="authenticated-shell__active-secondary">
					<p class="authenticated-shell__active-secondary-copy">
						You are viewing a page outside your persona navigation.
					</p>
					{#each activeSecondaryNavItems as item (item.href)}
						<a
							href={toAppPath(item.href)}
							class="nav-item"
							class:active={isActive(item.href)}
							aria-current={isActive(item.href) ? 'page' : undefined}
							data-sveltekit-preload-data="hover"
							data-sveltekit-preload-code="hover"
						>
							<span class="text-lg">{item.icon}</span>
							<span>{item.label}</span>
						</a>
					{/each}
				</div>
			{/if}
			{#if showAllNav}
				<div id="sidebar-more-nav" class="pb-3">
					{#each secondaryNavItems as item (item.href)}
						<a
							href={toAppPath(item.href)}
							class="nav-item"
							class:active={isActive(item.href)}
							aria-current={isActive(item.href) ? 'page' : undefined}
							data-sveltekit-preload-data="hover"
							data-sveltekit-preload-code="hover"
						>
							<span class="text-lg">{item.icon}</span>
							<span>{item.label}</span>
						</a>
					{/each}
				</div>
			{/if}
		{/if}
	</nav>

	<div class="authenticated-shell__account">
		<div class="authenticated-shell__account-row">
			<div class="authenticated-shell__avatar">
				{user.email?.charAt(0).toUpperCase()}
			</div>
			<div class="authenticated-shell__account-meta">
				<p class="authenticated-shell__email">{user.email}</p>
				<p class="authenticated-shell__tier">{subscription?.tier || 'Free'} Plan</p>
			</div>
		</div>
		<form method="POST" action={toAppPath('/auth/logout')} onsubmit={broadcastAuthSessionChanged}>
			<button type="submit" class="btn btn-ghost authenticated-shell__signout">
				<span>↩️</span>
				<span>Sign Out</span>
			</button>
		</form>
	</div>
</aside>

<main
	id="main"
	tabindex="-1"
	class="main-content authenticated-shell__main"
	class:authenticated-shell__main--sidebar-collapsed={!uiState.isSidebarOpen}
>
	<header class="authenticated-shell__topbar">
		<div class="authenticated-shell__topbar-inner">
			<button
				type="button"
				class="btn btn-ghost authenticated-shell__sidebar-toggle"
				onclick={() => uiState.toggleSidebar()}
				aria-label="Toggle sidebar"
				aria-controls="sidebar"
				aria-expanded={uiState.isSidebarOpen}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<line x1="3" y1="12" x2="21" y2="12"></line>
					<line x1="3" y1="6" x2="21" y2="6"></line>
					<line x1="3" y1="18" x2="21" y2="18"></line>
				</svg>
			</button>

			<div class="authenticated-shell__topbar-actions">
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
				<span class="badge badge-accent">Beta</span>
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
