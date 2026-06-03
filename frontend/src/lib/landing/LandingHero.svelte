<script lang="ts">
	import LandingHeroPreview from './LandingHeroPreview.svelte';
	import LandingTicker from './LandingTicker.svelte';

	export let heroCardState: 'pending' | 'approved' | 'denied' = 'pending';
	export let heroCardVisible = true;
	export let signupHref: (source: string) => string;
	export let salesHref: (source: string, intent?: string) => string;
</script>

<section class="hero" id="hero" aria-label="Valdrics governance platform hero">
	<div class="hero__bg" aria-hidden="true">
		<div class="hero__grid"></div>
		<div class="hero__orb hero__orb--1"></div>
		<div class="hero__orb hero__orb--2"></div>
		<div class="hero__orb hero__orb--3"></div>
		<div class="hero__gate"></div>
	</div>
	<div class="hero__inner">
		<div class="hero__text">
			<div class="hero__badge" role="status">
				<span class="hero__badge-dot" aria-hidden="true"></span>
				LIVE AT VALDRICS.COM
			</div>
			<h1 class="hero__headline">
				<span class="hero__headline-line">Govern</span>
				<span class="hero__headline-line hero__headline-line--accent">first.</span>
				<span class="hero__headline-line hero__headline-line--dim">Optimize</span>
				<span class="hero__headline-line hero__headline-line--dim">always.</span>
			</h1>
			<p class="hero__sub">
				Valdrics enforces approval workflows, ownership tracking, and governance policies across
				cloud infrastructure and software services — so engineering and finance teams stop paying
				for things they never needed.
			</p>
			<div class="hero__actions">
				<a href={signupHref('landing_hero_primary')} class="btn btn--jade btn--lg">
					Start Free Workspace →
				</a>
				<a href={salesHref('landing_hero_demo')} class="btn btn--ghost btn--lg">
					See a live demo ↗
				</a>
			</div>
			<div class="hero__chips" role="list" aria-label="Key statistics">
				<div class="chip" role="listitem">
					<strong>Proactive</strong> governance, not reactive reports
				</div>
				<div class="chip" role="listitem"><strong>Cloud + SaaS</strong> in one platform</div>
				<div class="chip" role="listitem">
					<strong>&lt; 20 min</strong> to first approval workflow
				</div>
			</div>
		</div>
		<LandingHeroPreview {heroCardState} {heroCardVisible} />
	</div>
</section>

<LandingTicker />

<style>
	.hero {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding: 120px 40px 80px;
		position: relative;
		overflow: hidden;
	}
	.hero__bg {
		position: absolute;
		inset: 0;
		z-index: 0;
		pointer-events: none;
	}
	.hero__grid {
		position: absolute;
		inset: 0;
		background-image:
			linear-gradient(rgba(0, 207, 124, 0.04) 1px, transparent 1px),
			linear-gradient(90deg, rgba(0, 207, 124, 0.04) 1px, transparent 1px);
		background-size: 54px 54px;
		mask-image: radial-gradient(ellipse 80% 80% at 50% 40%, black 30%, transparent 100%);
	}
	.hero__orb {
		position: absolute;
		border-radius: 50%;
		filter: blur(80px);
		animation: orb 14s ease-in-out infinite;
	}
	.hero__orb--1 {
		width: 500px;
		height: 500px;
		background: radial-gradient(circle, rgba(0, 207, 124, 0.1), transparent 70%);
		top: -80px;
		left: 30%;
		animation-duration: 16s;
	}
	.hero__orb--2 {
		width: 400px;
		height: 400px;
		background: radial-gradient(circle, rgba(0, 194, 255, 0.08), transparent 70%);
		bottom: 0;
		right: -80px;
		animation-duration: 18s;
		animation-delay: -7s;
	}
	.hero__orb--3 {
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, rgba(146, 112, 255, 0.07), transparent 70%);
		top: 40%;
		left: -60px;
		animation-duration: 20s;
		animation-delay: -4s;
	}
	.hero__gate {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 50%;
		width: 1px;
		background: linear-gradient(
			to bottom,
			transparent,
			rgba(0, 207, 124, 0.3) 20%,
			rgba(0, 207, 124, 0.3) 80%,
			transparent
		);
		transform-origin: top;
		animation: lineGrow 1.4s cubic-bezier(0.22, 1, 0.36, 1) 0.4s both;
	}
	.hero__inner {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 64px;
		align-items: center;
		max-width: 1100px;
		margin: 0 auto;
		width: 100%;
		position: relative;
		z-index: 1;
	}
	.hero__badge,
	.hero__headline,
	.hero__sub,
	.hero__actions,
	.hero__chips {
		animation: fadeUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
	}
	.hero__badge {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 5px 13px;
		border-radius: 100px;
		background: rgba(0, 207, 124, 0.1);
		border: 1px solid rgba(0, 207, 124, 0.2);
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--jade);
		letter-spacing: 0.07em;
		margin-bottom: 24px;
		animation-delay: 0.2s;
	}
	.hero__badge-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--jade);
		animation: pulseDot 1.8s ease-in-out infinite;
	}
	.hero__headline {
		font-family: var(--font-display);
		font-weight: 800;
		font-size: clamp(48px, 6vw, 82px);
		line-height: 1;
		letter-spacing: -0.03em;
		animation-delay: 0.35s;
	}
	.hero__headline-line {
		display: block;
		color: var(--white);
	}
	.hero__headline-line--accent {
		color: var(--jade);
	}
	.hero__headline-line--dim {
		color: var(--sub);
	}
	.hero__sub {
		font-size: 16px;
		color: var(--sub);
		line-height: 1.7;
		margin-top: 20px;
		max-width: 460px;
		animation-delay: 0.5s;
	}
	.hero__actions,
	.hero__chips {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-top: 32px;
		flex-wrap: wrap;
		animation-delay: 0.65s;
	}
	.hero__chips {
		gap: 9px;
		margin-top: 24px;
		animation-delay: 0.8s;
	}
	@keyframes orb {
		50% {
			transform: scale(1.06) translate(-16px, 12px);
		}
	}
	@keyframes lineGrow {
		from {
			transform: scaleY(0);
		}
		to {
			transform: scaleY(1);
		}
	}
	@keyframes fadeUp {
		from {
			opacity: 0;
			transform: translateY(18px);
		}
		to {
			opacity: 1;
			transform: none;
		}
	}
	@media (max-width: 900px) {
		.hero__inner {
			grid-template-columns: 1fr;
		}
		.hero {
			min-height: auto;
			padding: 100px 24px 64px;
		}
	}
</style>
