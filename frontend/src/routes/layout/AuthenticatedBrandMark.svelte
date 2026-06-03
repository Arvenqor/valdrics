<script lang="ts">
	import { base } from '$app/paths';

	type Props = {
		href: string;
	};

	let { href }: Props = $props();
</script>

<a {href} class="authenticated-shell__brand-link" aria-label="Valdrics home">
	<span class="authenticated-shell__brand-mark" aria-hidden="true">
		<img src={`${base}/valdrics_icon.png`} alt="" width="28" height="28" decoding="async" />
	</span>
</a>
