<script lang="ts">
	import LandingHead from '$lib/landing/LandingHead.svelte';
	import LandingHero from '$lib/components/LandingHero.svelte';

	let { data } = $props();
</script>

<LandingHead />
<LandingHero {...data.landingHero} />
