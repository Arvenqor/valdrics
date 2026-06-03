<script lang="ts">
	import { FOOTER_COLUMNS, TRUST_BADGES } from './landingContent';
	import { reveal } from './landingActions';

	export let signupHref: (source: string) => string;
	export let salesHref: (source: string, intent?: string) => string;
	export let appPath: (path: string) => string;
	export let footerHref: (label: string) => string;
</script>

<div class="trust-bar">
	<div class="trust-bar__inner">
		{#each TRUST_BADGES as badge}
			<div class="trust-badge">
				<svg
					width="13"
					height="13"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /></svg
				>
				{badge}
			</div>
		{/each}
	</div>
</div>

<section class="cta">
	<div class="cta__bg" aria-hidden="true">
		<div class="cta__glow"></div>
		<div class="cta__gate"></div>
	</div>
	<div class="container cta__inner">
		<div use:reveal>
			<span class="section-label">Start today</span>
			<h2 class="cta__title">Govern first.<br />Optimize always.</h2>
			<p class="cta__sub">
				Start on the permanent free tier, then upgrade only when your governance rollout needs
				broader coverage, automation, or finance-grade proof.
			</p>
			<div class="cta__actions">
				<a href={signupHref('landing_final_cta')} class="btn btn--jade btn--lg"
					>Start Free Workspace →</a
				>
				<a href={salesHref('landing_final_demo')} class="btn btn--ghost btn--lg">Book a live demo</a
				>
			</div>
			<p class="cta__note">
				Permanent free tier · Read-only onboarding where supported · Upgrade when ready
			</p>
		</div>
	</div>
</section>

<div class="footer" role="contentinfo">
	<div class="container">
		<div class="footer__top">
			<div class="footer__brand">
				<a href={appPath('/')} class="nav__logo" aria-label="Valdrics home">
					<div class="nav__mark">
						<img src={appPath('/valdrics_icon.png')} alt="" width="24" height="24" />
					</div>
					<span>VALDRICS</span>
				</a>
				<p>
					Cloud and software spend governance for engineering and finance teams. Approval workflows,
					ownership tracking, and measurable cost optimization — at valdrics.com
				</p>
			</div>
			{#each FOOTER_COLUMNS as col}
				<div>
					<div class="footer__col-title">{col.title}</div>
					<ul class="footer__links">
						{#each col.links as link}
							<li><a href={footerHref(link)}>{link}</a></li>
						{/each}
					</ul>
				</div>
			{/each}
		</div>
		<div class="footer__bottom">
			<span class="footer__copy">© 2026 Valdrics · valdrics.com · Governed FinOps</span>
			<div class="footer__social" aria-label="Social media links">
				<a
					href="https://twitter.com/valdrics"
					class="social-link"
					aria-label="Valdrics on Twitter"
					rel="noopener">𝕏</a
				>
				<a
					href="https://linkedin.com/company/valdrics"
					class="social-link"
					aria-label="Valdrics on LinkedIn"
					rel="noopener">in</a
				>
				<a
					href="https://github.com/valdrics"
					class="social-link"
					aria-label="Valdrics on GitHub"
					rel="noopener">gh</a
				>
			</div>
		</div>
	</div>
</div>

<style>
	.trust-bar {
		padding: 28px 40px;
		background: var(--base);
		border-top: 1px solid var(--bdr);
		border-bottom: 1px solid var(--bdr);
	}
	.trust-bar__inner {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 28px;
		flex-wrap: wrap;
		max-width: 1100px;
		margin: 0 auto;
	}
	.trust-badge {
		display: flex;
		align-items: center;
		gap: 7px;
		font-size: 12px;
		color: var(--sub);
	}
	.cta {
		padding: 112px 40px;
		position: relative;
		overflow: hidden;
		background: var(--void);
	}
	.cta__bg {
		position: absolute;
		inset: 0;
		pointer-events: none;
	}
	.cta__glow {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 600px;
		height: 600px;
		border-radius: 50%;
		background: radial-gradient(circle, rgba(0, 207, 124, 0.07), transparent 70%);
	}
	.cta__gate {
		position: absolute;
		top: 0;
		bottom: 0;
		left: 50%;
		width: 1px;
		background: linear-gradient(
			to bottom,
			transparent,
			rgba(0, 207, 124, 0.2) 30%,
			rgba(0, 207, 124, 0.2) 70%,
			transparent
		);
	}
	.cta__inner {
		position: relative;
		z-index: 1;
		text-align: center;
	}
	.cta__title {
		font-family: var(--font-display);
		font-weight: 800;
		font-size: clamp(36px, 5vw, 66px);
		color: var(--white);
		line-height: 1.05;
		letter-spacing: -0.02em;
		margin-bottom: 18px;
	}
	.cta__sub {
		font-size: 16px;
		color: var(--sub);
		max-width: 420px;
		margin: 0 auto 36px;
		line-height: 1.7;
	}
	.cta__actions {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 14px;
		flex-wrap: wrap;
	}
	.cta__note {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--muted);
		margin-top: 16px;
	}
	.footer {
		padding: 48px 40px;
		background: var(--base);
		border-top: 1px solid var(--bdr);
	}
	.footer__top {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 1fr;
		gap: 40px;
		margin-bottom: 40px;
	}
	.footer__brand p {
		font-size: 13px;
		color: var(--sub);
		margin-top: 12px;
		max-width: 240px;
		line-height: 1.7;
	}
	.footer__col-title {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 11px;
		letter-spacing: 0.06em;
		color: var(--white);
		margin-bottom: 14px;
		text-transform: uppercase;
	}
	.footer__links {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 9px;
	}
	.footer__links a {
		font-size: 13px;
		color: var(--sub);
		text-decoration: none;
		transition: color 0.15s;
	}
	.footer__links a:hover {
		color: var(--text);
	}
	.footer__bottom {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding-top: 28px;
		border-top: 1px solid var(--bdr);
		flex-wrap: wrap;
		gap: 14px;
	}
	.footer__copy {
		font-family: var(--font-mono);
		font-size: 12px;
		color: var(--muted);
	}
	.footer__social {
		display: flex;
		gap: 12px;
	}
	.social-link {
		width: 30px;
		height: 30px;
		border-radius: 8px;
		border: 1px solid var(--bdr);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--sub);
		text-decoration: none;
		font-size: 12px;
		font-weight: 600;
		transition: all 0.15s;
	}
	.social-link:hover {
		border-color: var(--bdr-hi);
		color: var(--text);
		background: var(--s1);
	}
	@media (max-width: 900px) {
		.footer__top {
			grid-template-columns: 1fr 1fr;
		}
	}
	@media (max-width: 600px) {
		.footer__top {
			grid-template-columns: 1fr;
		}
	}
</style>
