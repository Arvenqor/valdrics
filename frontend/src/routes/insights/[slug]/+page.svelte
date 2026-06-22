<script lang="ts">
	import PublicContentArticlePage from '$lib/components/public/PublicContentArticlePage.svelte';
	import type { PageData } from './$types';

	let { data }: { data: any } = $props();
</script>

<svelte:head>
	<title>{data.entry.title} | Valdrics Insights</title>
</svelte:head>

<PublicContentArticlePage
	entry={data.entry}
	relatedEntries={data.relatedEntries}
	hubHref="/insights"
	hubLabel="Back to Insights"
/>
