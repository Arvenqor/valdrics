<svg class="topology-chart" viewBox="0 0 280 80" preserveAspectRatio="none">
	<defs
		><linearGradient id="landing-topology-gradient" x1="0" y1="0" x2="0" y2="1"
			><stop offset="0%" stop-color="#00C2FF" stop-opacity=".22" /><stop
				offset="100%"
				stop-color="#00C2FF"
				stop-opacity=".02"
			/></linearGradient
		></defs
	>
	<line x1="0" y1="27" x2="280" y2="27" stroke="rgba(100,170,230,.07)" />
	<line x1="0" y1="54" x2="280" y2="54" stroke="rgba(100,170,230,.07)" />
	<path
		d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34 L280,80 L0,80 Z"
		fill="url(#landing-topology-gradient)"
	/>
	<path
		d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34"
		fill="none"
		stroke="var(--ion)"
		stroke-width="1.8"
	/>
	<circle cx="156" cy="18" r="4" fill="var(--ruby)" stroke="var(--s2)" stroke-width="2" />
	<line x1="156" y1="0" x2="156" y2="80" stroke="var(--ruby)" stroke-dasharray="3,3" opacity=".4" />
	<text x="162" y="12" font-size="8" fill="var(--ruby)" font-family="JetBrains Mono,monospace"
		>spike detected</text
	>
	<path
		d="M0,66 C18,62 35,68 52,64 C69,60 87,55 104,50 C121,45 139,38 156,35 C173,32 191,42 208,46 C225,50 243,45 280,48"
		fill="none"
		stroke="var(--violet)"
		stroke-width="1.2"
		opacity=".6"
	/>
</svg>
<div class="topology-legend">
	<span><i class="topology-legend__swatch--ion"></i> Cloud Infra</span>
	<span><i class="topology-legend__swatch--violet"></i> Software/SaaS</span>
</div>

<style>
	.topology-chart {
		display: block;
		width: 100%;
	}
	.topology-legend {
		display: flex;
		gap: 14px;
		margin-top: 8px;
	}
	.topology-legend span {
		display: flex;
		align-items: center;
		gap: 5px;
		font-size: 10px;
		color: var(--sub);
	}
	.topology-legend i {
		width: 12px;
		height: 3px;
		border-radius: 2px;
		display: inline-block;
	}
	.topology-legend__swatch--ion {
		background: var(--ion);
	}
	.topology-legend__swatch--violet {
		background: var(--violet);
	}
</style>
