<script lang="ts">
	import { base } from '$app/paths';
	import { HOW_STEPS, INTEGRATIONS } from './landingContent';
	import { reveal } from './landingActions';

	export let decisionsToday = 0;
	export let shadowFlagged = 0;
	export let violationsCaught = 0;
	export let fmt: (n: number) => string;
</script>

<section class="how" id="how-it-works">
	<div class="container">
		<div class="section-center" use:reveal>
			<span class="section-label">How it works</span>
			<h2 class="section-title section-title--center">
				From first connection to governed spend<br />in under an hour.
			</h2>
			<p class="section-sub section-sub--center">
				No professional services. No IT ticket. No onboarding marathon.
			</p>
		</div>
		<div class="how__steps" use:reveal={{ delay: 100 }}>
			{#each HOW_STEPS as step, i}
				<div class="how__step">
					<div class="how__step-num" class:how__step-num--done={i < 2}>{step.n}</div>
					<div class="how__step-connector" class:how__step-connector--done={i < 2}></div>
					<h3 class="how__step-title">{step.title}</h3>
					<p class="how__step-desc">{step.desc}</p>
				</div>
			{/each}
		</div>
	</div>
</section>

<section class="live-counter">
	<div class="container">
		<div class="live-counter__inner" use:reveal>
			<div class="live-counter__label">
				<span class="live-dot live-dot--jade" aria-hidden="true"></span>
				Across all Valdrics workspaces in the last 24 hours
			</div>
			<div class="live-counter__stats">
				<div class="live-counter__stat">
					<div class="live-counter__val live-counter__val--jade">{fmt(decisionsToday)}</div>
					<div class="live-counter__sub">approval decisions made</div>
				</div>
				<div class="live-counter__divider" aria-hidden="true"></div>
				<div class="live-counter__stat">
					<div class="live-counter__val live-counter__val--ruby">{fmt(shadowFlagged)}</div>
					<div class="live-counter__sub">shadow IT tools flagged</div>
				</div>
				<div class="live-counter__divider" aria-hidden="true"></div>
				<div class="live-counter__stat">
					<div class="live-counter__val live-counter__val--ion">{fmt(violationsCaught)}</div>
					<div class="live-counter__sub">policy violations caught</div>
				</div>
			</div>
		</div>
	</div>
</section>

<section class="integrations" id="integrations">
	<div class="container">
		<div class="section-center" use:reveal>
			<span class="section-label">Integrations</span>
			<h2 class="section-title section-title--center">
				Governance that lives where your team works.
			</h2>
			<p class="section-sub section-sub--center">
				Connect cloud providers and workflow tools in minutes — no agents, no code.
			</p>
		</div>
		<div class="integrations__grid" use:reveal={{ delay: 100 }}>
			{#each INTEGRATIONS as t}
				<div class="integ-card">
					{#if t.logo}
						<img
							class="integ-card__logo"
							src={`${base}/service-logos/${t.logo}`}
							alt={`${t.name} logo`}
							loading="lazy"
							decoding="async"
						/>
					{:else}
						<span class="integ-card__icon" class:integ-card__icon--muted={t.tone === 'muted'}
							>{t.icon}</span
						>
					{/if}
					<span
						class="integ-card__name"
						class:integ-card__name--ion={t.tone === 'ion'}
						class:integ-card__name--violet={t.tone === 'violet'}
						class:integ-card__name--muted={t.tone === 'muted'}>{t.name}</span
					>
				</div>
			{/each}
		</div>
	</div>
</section>

<style>
	.how {
		background: var(--base);
	}
	.how__steps {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0;
		margin-top: 60px;
		position: relative;
	}
	.how__steps::after {
		content: '';
		position: absolute;
		top: 30px;
		left: 10%;
		right: 10%;
		height: 1px;
		background: linear-gradient(
			to right,
			var(--bdr),
			var(--jade) 25%,
			var(--ion) 50%,
			var(--violet) 75%,
			var(--bdr)
		);
	}
	.how__step {
		padding: 0 16px;
		text-align: center;
		position: relative;
		z-index: 1;
	}
	.how__step-num {
		width: 60px;
		height: 60px;
		border-radius: 50%;
		border: 1px solid var(--bdr);
		background: var(--s1);
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 16px;
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--sub);
		transition:
			border-color 0.25s,
			color 0.25s;
	}
	.how__step-num--done,
	.how__step:hover .how__step-num {
		border-color: var(--jade);
		color: var(--jade);
	}
	.how__step-connector {
		display: none;
	}
	.how__step-title {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 13px;
		color: var(--white);
		margin-bottom: 6px;
	}
	.how__step-desc {
		font-size: 12px;
		color: var(--sub);
		line-height: 1.6;
	}
	.live-counter {
		background: var(--s1);
		border-top: 1px solid var(--bdr);
		border-bottom: 1px solid var(--bdr);
		padding: 48px 40px;
	}
	.live-counter__inner {
		max-width: 1100px;
		margin: 0 auto;
	}
	.live-counter__label {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		font-family: var(--font-mono);
		font-size: 11px;
		color: var(--sub);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 32px;
	}
	.live-counter__stats {
		display: grid;
		grid-template-columns: 1fr auto 1fr auto 1fr;
		align-items: center;
	}
	.live-counter__stat {
		text-align: center;
	}
	.live-counter__val {
		font-family: var(--font-display);
		font-weight: 800;
		font-size: clamp(36px, 5vw, 60px);
		line-height: 1;
		letter-spacing: -0.03em;
	}
	.live-counter__val--jade {
		color: var(--jade);
	}
	.live-counter__val--ruby {
		color: var(--ruby);
	}
	.live-counter__val--ion {
		color: var(--ion);
	}
	.live-counter__sub {
		font-size: 13px;
		color: var(--sub);
		margin-top: 6px;
	}
	.live-counter__divider {
		width: 1px;
		height: 60px;
		background: var(--bdr);
	}
	.integrations {
		background: var(--void);
	}
	.integrations__grid {
		display: grid;
		grid-template-columns: repeat(8, 1fr);
		gap: 10px;
		margin-top: 44px;
	}
	.integ-card {
		padding: 14px 8px;
		border-radius: 11px;
		border: 1px solid var(--bdr);
		background: var(--s1);
		text-align: center;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 5px;
		transition:
			border-color 0.2s,
			transform 0.2s;
	}
	.integ-card:hover {
		border-color: var(--bdr-hi);
		transform: translateY(-2px);
	}
	.integ-card__icon {
		font-size: 20px;
	}
	.integ-card__icon--muted,
	.integ-card__name--muted {
		color: var(--sub);
	}
	.integ-card__logo {
		width: 20px;
		height: 20px;
		object-fit: contain;
	}
	.integ-card__name {
		font-size: 10px;
		color: var(--sub);
		font-family: var(--font-mono);
		letter-spacing: 0.04em;
	}
	.integ-card__name--ion {
		color: var(--ion);
	}
	.integ-card__name--violet {
		color: var(--violet);
	}
	@media (max-width: 900px) {
		.how__steps {
			grid-template-columns: 1fr 1fr;
			gap: 24px;
		}
		.how__steps::after,
		.live-counter__divider {
			display: none;
		}
		.live-counter__stats {
			grid-template-columns: 1fr;
			gap: 24px;
		}
		.integrations__grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}
	@media (max-width: 600px) {
		.integrations__grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>
