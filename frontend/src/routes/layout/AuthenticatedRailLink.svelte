<script lang="ts">
	type Props = {
		href: string;
		label: string;
		icon: string;
		active?: boolean;
	};

	let { href, label, icon, active = false }: Props = $props();
</script>

<a
	{href}
	class="authenticated-shell__rail-item"
	class:authenticated-shell__rail-item--active={active}
	aria-current={active ? 'page' : undefined}
	aria-label={label}
	title={label}
	data-sveltekit-preload-data="hover"
	data-sveltekit-preload-code="hover"
>
	<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
		<path d={icon} />
	</svg>
	<span class="authenticated-shell__rail-tooltip">{label}</span>
</a>
