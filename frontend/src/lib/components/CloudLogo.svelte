<script lang="ts">
	import { base } from '$app/paths';

	export let provider: string = 'aws'; // aws, azure, gcp, valdrics
	export let size: number = 16;
	export let className: string = '';
	export let emphasizeMark: boolean = false;

	$: lowProvider = provider?.toLowerCase() || 'aws';
	$: prioritizeImage = lowProvider === 'valdrics' && (emphasizeMark || size >= 80);

	const logos: Record<string, string> = {
		aws: `${base}/aws-logo.svg`,
		azure: `${base}/azure-logo.png`,
		gcp: `${base}/gcp.svg`,
		valdrics: `${base}/valdrics_icon.png`
	};
</script>

<div class="inline-flex items-center justify-center {className}">
	{#if logos[lowProvider]}
		{#if lowProvider === 'valdrics'}
			<span class="valdrics-logo-3d-container size-{size}">
				<span class="valdrics-logo-3d-mark size-{size}">
					<img
						src={logos[lowProvider]}
						alt="Valdrics logo"
						class="object-contain cloud-logo-image valdrics-logo-3d-image"
						class:cloud-logo-image-emphasized={emphasizeMark}
						width={size}
						height={size}
						decoding="async"
						loading={prioritizeImage ? 'eager' : undefined}
						fetchpriority={prioritizeImage ? 'high' : undefined}
					/>
				</span>
			</span>
		{:else}
			<img
				src={logos[lowProvider]}
				alt={provider}
				class="object-contain cloud-logo-image"
				width={size}
				height={size}
				decoding="async"
			/>
		{/if}
	{:else}
		<!-- Fallback Cloud Icon -->
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			width={size}
			height={size}
		>
			<path
				d="M17.5 19c2.5 0 4.5-2 4.5-4.5 0-2.3-1.7-4.2-3.9-4.5-.6-3.1-3.3-5.5-6.6-5.5-2.8 0-5.3 1.7-6.2 4.2C3.1 9.4 1 11.5 1 14.3c0 2.6 2.1 4.7 4.7 4.7h11.8z"
			/>
		</svg>
	{/if}
</div>

<style>
	.cloud-logo-image {
		display: block;
	}

	.cloud-logo-image-emphasized {
		transform: scale(1.36);
		transform-origin: center;
	}

	/* CSP Compliant Sizing Rules */
	.valdrics-logo-3d-container.size-16 {
		width: 16px;
		height: 16px;
	}
	.valdrics-logo-3d-container.size-24 {
		width: 24px;
		height: 24px;
	}
	.valdrics-logo-3d-container.size-32 {
		width: 32px;
		height: 32px;
	}
	.valdrics-logo-3d-container.size-40 {
		width: 40px;
		height: 40px;
	}
	.valdrics-logo-3d-container.size-48 {
		width: 48px;
		height: 48px;
	}
	.valdrics-logo-3d-container.size-64 {
		width: 64px;
		height: 64px;
	}
	.valdrics-logo-3d-container.size-80 {
		width: 80px;
		height: 80px;
	}
	.valdrics-logo-3d-container.size-96 {
		width: 96px;
		height: 96px;
	}

	.valdrics-logo-3d-mark.size-16 {
		border-radius: 4px;
		padding: 1px;
	}
	.valdrics-logo-3d-mark.size-24 {
		border-radius: 4px;
		padding: 1px;
	}
	.valdrics-logo-3d-mark.size-32 {
		border-radius: 8px;
		padding: 3px;
	}
	.valdrics-logo-3d-mark.size-40 {
		border-radius: 8px;
		padding: 3px;
	}
	.valdrics-logo-3d-mark.size-48 {
		border-radius: 8px;
		padding: 3px;
	}
	.valdrics-logo-3d-mark.size-64 {
		border-radius: 8px;
		padding: 3px;
	}
	.valdrics-logo-3d-mark.size-80 {
		border-radius: 12px;
		padding: 4px;
	}
	.valdrics-logo-3d-mark.size-96 {
		border-radius: 12px;
		padding: 4px;
	}
</style>
