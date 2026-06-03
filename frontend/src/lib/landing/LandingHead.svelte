<script lang="ts">
	import { structuredData } from './landingContent';

	const structuredDataJson = JSON.stringify(structuredData)
		.replaceAll('<', '\\u003c')
		.replaceAll('</script', '<\\/script');
	const structuredDataMarkup =
		'<script type="application/ld+json">' + structuredDataJson + '</scr' + 'ipt>';
</script>

<svelte:head>
	<title
		>Valdrics — Cloud & Software Spend Governance | Approval Workflows & Ownership Tracking</title
	>
	<meta
		name="description"
		content="Valdrics helps engineering and finance teams stop wasting money on cloud and software by enforcing approval workflows, ownership tracking, and governance policies before spend is committed. AWS, GCP, Azure + 100s of SaaS tools."
	/>
	<meta
		name="keywords"
		content="cloud governance platform, SaaS spend management, software license management, approval workflow software, cloud cost governance, shadow IT detection, IT spend management"
	/>
	<meta property="og:type" content="website" />
	<meta property="og:url" content="https://www.valdrics.com/" />
	<meta
		property="og:title"
		content="Valdrics — Govern cloud and software spend before the bill arrives"
	/>
	<meta
		property="og:description"
		content="Approval workflows, ownership tracking, and governance policies for cloud and SaaS spend. Stop waste before it reaches the invoice."
	/>
	<meta property="og:image" content="https://www.valdrics.com/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:site_name" content="Valdrics" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:site" content="@valdrics" />
	<meta name="twitter:title" content="Valdrics — Cloud & Software Spend Governance" />
	<meta
		name="twitter:description"
		content="Approval workflows, ownership tracking, and policy enforcement for cloud and SaaS spend. Engineering and finance, finally aligned."
	/>
	<meta name="twitter:image" content="https://www.valdrics.com/twitter-card.png" />
	<!-- Structured data in Svelte head requires raw script injection; JSON is pre-escaped above. -->
	<!-- eslint-disable-next-line svelte/no-at-html-tags -->
	{@html structuredDataMarkup}
</svelte:head>
