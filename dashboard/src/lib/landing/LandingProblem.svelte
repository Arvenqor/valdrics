<script lang="ts">
	import { reveal } from './landingActions';
</script>

<section class="problem" id="problem">
	<div class="container">
		<div use:reveal>
			<span class="section-label">The problem</span>
			<h2 class="section-title">
				Most tools tell you what went wrong<br />after the invoice arrives.
			</h2>
			<p class="section-sub">
				Monitoring tells you the bill was too high. Governance stops it from getting that high in
				the first place. There is a meaningful difference.
			</p>
		</div>
		<div class="problem__gate" use:reveal={{ delay: 100 }}>
			<div class="problem__side problem__side--chaos">
				<div class="side-label side-label--bad">
					<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<circle cx="12" cy="12" r="10" />
						<line x1="15" y1="9" x2="9" y2="15" />
						<line x1="9" y1="9" x2="15" y2="15" />
					</svg>
					Without Valdrics
				</div>
				<ul class="problem__list">
					<li>Engineers spin up tools on the company card — nobody notices for months</li>
					<li>Cloud resources running for 18 months with no owner and no justification</li>
					<li>Three teams paying separately for the same software tool</li>
					<li>Finance asks Engineering for cost justification — nobody can trace the decision</li>
					<li>A new data vendor is onboarded without a security review or signed DPA</li>
				</ul>
			</div>
			<div class="problem__gate-line" aria-hidden="true">
				<div class="gate-glow"></div>
				<div class="gate-label">THE GATE</div>
			</div>
			<div class="problem__side problem__side--clarity">
				<div class="side-label side-label--good">
					<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
						<polyline points="20 6 9 17 4 12" />
					</svg>
					With Valdrics
				</div>
				<ul class="problem__list">
					<li>Every tool request routes through a policy-checked approval gate first</li>
					<li>Every resource has a named owner responsible for reviewing it quarterly</li>
					<li>Duplicate tools are flagged automatically and consolidated</li>
					<li>Every cost traces to a named approval, a team, and a business justification</li>
					<li>Security, DPA, and vendor policies are enforced automatically — zero gaps</li>
				</ul>
			</div>
		</div>
	</div>
</section>

<style>
	.problem {
		background: var(--base);
	}
	.problem__gate {
		display: grid;
		grid-template-columns: 1fr 40px 1fr;
		border-radius: 18px;
		overflow: hidden;
		border: 1px solid var(--bdr);
		margin-top: 52px;
	}
	.problem__side {
		padding: 40px 36px;
	}
	.problem__side--chaos {
		background: rgba(255, 58, 92, 0.04);
	}
	.problem__side--clarity {
		background: rgba(0, 207, 124, 0.05);
	}
	.problem__gate-line {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		background: var(--void);
	}
	.gate-glow {
		width: 1px;
		flex: 1;
		background: linear-gradient(to bottom, transparent, var(--jade) 30% 70%, transparent);
		box-shadow: 0 0 12px rgba(0, 207, 124, 0.4);
	}
	.gate-label {
		writing-mode: vertical-lr;
		font-family: var(--font-mono);
		font-size: 8px;
		color: var(--jade);
		letter-spacing: 0.15em;
		text-transform: uppercase;
		padding: 8px 0;
	}
	.side-label {
		font-family: var(--font-mono);
		font-size: 11px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		display: flex;
		align-items: center;
		gap: 7px;
		margin-bottom: 20px;
	}
	.side-label--bad {
		color: var(--ruby);
	}
	.side-label--good {
		color: var(--jade);
	}
	.problem__list {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 12px;
		font-size: 14px;
		color: var(--sub);
		line-height: 1.65;
	}
	.problem__list li::before {
		content: '→ ';
		color: var(--muted);
	}
	@media (max-width: 900px) {
		.problem__gate {
			grid-template-columns: 1fr;
		}
		.problem__gate-line {
			display: none;
		}
	}
</style>
