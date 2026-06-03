<script lang="ts">
	type Tone = 'primary' | 'secondary';
	type Props = {
		href: string;
		label: string;
		icon: string;
		tone?: Tone;
	};

	let { href, label, icon, tone = 'secondary' }: Props = $props();
</script>

<a
	{href}
	class="authenticated-shell__action"
	class:authenticated-shell__action--primary={tone === 'primary'}
	class:authenticated-shell__action--secondary={tone === 'secondary'}
	data-sveltekit-preload-data="hover"
	data-sveltekit-preload-code="hover"
>
	<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
		<path d={icon} />
	</svg>
	<span>{label}</span>
</a>
