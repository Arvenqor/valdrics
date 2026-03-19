<script lang="ts">
	import { assets } from '$app/paths';
	import { page } from '$app/stores';
	import LandingHero from '$lib/components/LandingHero.svelte';
	import { PUBLIC_HOME_META } from './homeDashboardContent';

	let canonicalUrl = $derived(new URL($page.url.pathname, $page.url.origin).toString());
	let ogImageUrl = $derived(new URL(`${assets}/og-image.png`, $page.url.origin).toString());
</script>

<svelte:head>
	<title>{PUBLIC_HOME_META.title}</title>
	<meta name="description" content={PUBLIC_HOME_META.description} />
	<meta name="keywords" content={PUBLIC_HOME_META.keywords} />
	<meta property="og:title" content={PUBLIC_HOME_META.title} />
	<meta property="og:description" content={PUBLIC_HOME_META.ogDescription} />
	<meta property="og:type" content="website" />
	<meta property="og:url" content={canonicalUrl} />
	<meta property="og:image" content={ogImageUrl} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={PUBLIC_HOME_META.title} />
	<meta name="twitter:description" content={PUBLIC_HOME_META.ogDescription} />
	<meta name="twitter:image" content={ogImageUrl} />
</svelte:head>

<LandingHero />
