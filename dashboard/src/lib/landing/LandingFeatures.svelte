<script lang="ts">
	import { reveal } from './landingActions';
</script>

<section class="features" id="features">
	<div class="container">
		<div use:reveal>
			<span class="section-label">Platform capabilities</span>
			<h2 class="section-title">Governance is the new<br />cloud cost optimization.</h2>
			<p class="section-sub">
				Every dollar Valdrics saves traces back to a specific governance action. An approval denied.
				An owner reclaiming a resource. A policy blocking a duplicate.
			</p>
		</div>
		<div class="features__grid">
			<div class="fcard fcard--large fcard--jade" use:reveal={{ delay: 80 }}>
				<div class="fcard__icon fcard__icon--jade">✓</div>
				<h3 class="fcard__title">Approval Workflows</h3>
				<p class="fcard__desc">
					Every cloud resource and software request passes through a policy-checked approval gate
					before spend is committed. Budget, security, vendor, and region policies run automatically.
				</p>
				<div class="fcard__illustration">
					<div class="mini-card">
						<div class="mini-card__stripe"></div>
						<div class="mini-card__content">
							<span class="mini-tag">CLOUD</span>
							<span class="mini-card__name">Datadog Pro upgrade</span>
						</div>
						<div class="mini-card__right">
							<div class="mini-card__cost">$2,800/mo</div>
							<div class="mini-card__btns">
								<span class="mini-btn mini-btn--approve">✓</span>
								<span class="mini-btn mini-btn--deny">✕</span>
							</div>
						</div>
					</div>
					<div class="policy-chips">
						<span class="policy-chip policy-chip--pass">✓ Budget</span>
						<span class="policy-chip policy-chip--fail">✕ DPA required</span>
						<span class="policy-chip policy-chip--warn">⚠ New vendor</span>
					</div>
				</div>
				<div class="fcard__stat">
					<span class="fcard__stat-val fcard__stat-val--jade">20 min</span>
					<span class="fcard__stat-label">from signup to first live approval workflow</span>
				</div>
			</div>
			<div class="fcard__col">
				<div class="fcard fcard--ion" use:reveal={{ delay: 160 }}>
					<div class="fcard__icon fcard__icon--ion">◌</div>
					<h3 class="fcard__title">Ownership Tracking</h3>
					<p class="fcard__desc">
						Every cloud resource and SaaS licence gets a named owner. Owners receive quarterly
						review requests and renewal alerts. Resources with no owner are flagged on day one.
					</p>
					<div class="fcard__stat">
						<span class="fcard__stat-val fcard__stat-val--ion">87%</span>
						<span class="fcard__stat-label">avg. ownership coverage on day 30</span>
					</div>
				</div>
				<div class="fcard fcard--violet" use:reveal={{ delay: 220 }}>
					<div class="fcard__icon fcard__icon--violet">◇</div>
					<h3 class="fcard__title">Policy Engine</h3>
					<p class="fcard__desc">
						40+ pre-built governance policies. Budget limits, vendor lists, DPA requirements, data
						residency, commitment thresholds, and custom rules for enterprise workflows.
					</p>
					<div class="fcard__stat">
						<span class="fcard__stat-val fcard__stat-val--violet">40+</span>
						<span class="fcard__stat-label">pre-built governance policy templates</span>
					</div>
				</div>
			</div>
		</div>
		<div class="features__grid features__grid--flipped features__grid--second">
			<div class="fcard__col">
				<div class="fcard fcard--ruby" use:reveal={{ delay: 80 }}>
					<div class="fcard__icon fcard__icon--ruby">!</div>
					<h3 class="fcard__title">Shadow IT Detection</h3>
					<p class="fcard__desc">
						Cross-references cloud billing, corporate card, and expense feeds against your approved
						tool inventory. Unapproved tools are flagged and consolidated.
					</p>
					<div class="fcard__stat">
						<span class="fcard__stat-val fcard__stat-val--ruby">12 tools</span>
						<span class="fcard__stat-label">avg. shadow IT found per team in month 1</span>
					</div>
				</div>
				<div class="fcard fcard--amber" use:reveal={{ delay: 160 }}>
					<div class="fcard__icon fcard__icon--amber">$</div>
					<h3 class="fcard__title">Savings Attribution</h3>
					<p class="fcard__desc">
						Every saving is tagged to the governance action that produced it. Finance gets a clear
						ROI statement — not just a cost chart with no story attached.
					</p>
					<div class="fcard__stat">
						<span class="fcard__stat-val fcard__stat-val--amber">$34K</span>
						<span class="fcard__stat-label">avg. monthly savings in first quarter</span>
					</div>
				</div>
			</div>
			<div class="fcard fcard--large fcard--ion" use:reveal={{ delay: 120 }}>
				<div class="fcard__icon fcard__icon--ion">⌁</div>
				<h3 class="fcard__title">Unified Spend Topology</h3>
				<p class="fcard__desc">
					AWS, GCP, Azure, and 100+ SaaS tools unified in one living spend map. Cloud infrastructure
					and software costs in the same inventory, approval queue, and governance layer.
				</p>
				<div class="fcard__illustration">
					<svg class="topology-chart" viewBox="0 0 280 80" preserveAspectRatio="none">
						<defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#00C2FF" stop-opacity=".22" /><stop offset="100%" stop-color="#00C2FF" stop-opacity=".02" /></linearGradient></defs>
						<line x1="0" y1="27" x2="280" y2="27" stroke="rgba(100,170,230,.07)" />
						<line x1="0" y1="54" x2="280" y2="54" stroke="rgba(100,170,230,.07)" />
						<path d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34 L280,80 L0,80 Z" fill="url(#tg)" />
						<path d="M0,58 C18,52 35,62 52,56 C69,50 87,42 104,36 C121,30 139,22 156,18 C173,14 191,28 208,32 C225,36 243,30 280,34" fill="none" stroke="var(--ion)" stroke-width="1.8" />
						<circle cx="156" cy="18" r="4" fill="var(--ruby)" stroke="var(--s2)" stroke-width="2" />
						<line x1="156" y1="0" x2="156" y2="80" stroke="var(--ruby)" stroke-dasharray="3,3" opacity=".4" />
						<text x="162" y="12" font-size="8" fill="var(--ruby)" font-family="JetBrains Mono,monospace">spike detected</text>
						<path d="M0,66 C18,62 35,68 52,64 C69,60 87,55 104,50 C121,45 139,38 156,35 C173,32 191,42 208,46 C225,50 243,45 280,48" fill="none" stroke="var(--violet)" stroke-width="1.2" opacity=".6" />
					</svg>
					<div class="topology-legend">
						<span><i class="topology-legend__swatch--ion"></i> Cloud Infra</span>
						<span><i class="topology-legend__swatch--violet"></i> Software/SaaS</span>
					</div>
				</div>
				<div class="fcard__stat">
					<span class="fcard__stat-val fcard__stat-val--ion">3 clouds</span>
					<span class="fcard__stat-label">+ 100s of SaaS tools in one unified view</span>
				</div>
			</div>
		</div>
	</div>
</section>

<style>
	.features {
		background: var(--void);
	}
	.features__grid {
		display: grid;
		grid-template-columns: 1.4fr 1fr;
		gap: 14px;
		margin-top: 52px;
	}
	.features__grid--flipped {
		grid-template-columns: 1fr 1.4fr;
	}
	.features__grid--second {
		margin-top: 14px;
	}
	.fcard__col {
		display: flex;
		flex-direction: column;
		gap: 14px;
	}
	.fcard {
		background: var(--s1);
		border: 1px solid var(--bdr);
		border-radius: 16px;
		padding: 28px;
		transition:
			border-color 0.2s,
			transform 0.2s;
		position: relative;
		overflow: hidden;
	}
	.fcard::before {
		content: '';
		position: absolute;
		inset: 0 0 auto;
		height: 1px;
		opacity: 0;
		transition: opacity 0.3s;
	}
	.fcard:hover {
		border-color: var(--bdr-hi);
		transform: translateY(-2px);
	}
	.fcard:hover::before {
		opacity: 1;
	}
	.fcard--large {
		padding: 32px;
	}
	.fcard--jade::before {
		background: linear-gradient(to right, transparent, var(--jade), transparent);
	}
	.fcard--ion::before {
		background: linear-gradient(to right, transparent, var(--ion), transparent);
	}
	.fcard--violet::before {
		background: linear-gradient(to right, transparent, var(--violet), transparent);
	}
	.fcard--ruby::before {
		background: linear-gradient(to right, transparent, var(--ruby), transparent);
	}
	.fcard--amber::before {
		background: linear-gradient(to right, transparent, var(--amber), transparent);
	}
	.fcard__icon {
		width: 42px;
		height: 42px;
		border-radius: 11px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 16px;
		font-family: var(--font-display);
		font-weight: 800;
	}
	.fcard__icon--jade,
	.fcard__stat-val--jade {
		color: var(--jade);
	}
	.fcard__icon--ion,
	.fcard__stat-val--ion {
		color: var(--ion);
	}
	.fcard__icon--violet,
	.fcard__stat-val--violet {
		color: var(--violet);
	}
	.fcard__icon--ruby,
	.fcard__stat-val--ruby {
		color: var(--ruby);
	}
	.fcard__icon--amber,
	.fcard__stat-val--amber {
		color: var(--amber);
	}
	.fcard__icon {
		background: color-mix(in srgb, currentColor 10%, transparent);
		border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
	}
	.fcard__title {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 18px;
		color: var(--white);
		margin-bottom: 9px;
	}
	.fcard__desc {
		font-size: 13px;
		color: var(--sub);
		line-height: 1.7;
	}
	.fcard__stat {
		margin-top: 20px;
		padding-top: 16px;
		border-top: 1px solid var(--bdr);
		display: flex;
		align-items: baseline;
		gap: 8px;
	}
	.fcard__stat-val {
		font-family: var(--font-display);
		font-weight: 700;
		font-size: 22px;
	}
	.fcard__stat-label {
		font-size: 12px;
		color: var(--sub);
	}
	.fcard__illustration {
		margin: 16px 0;
		border-radius: 9px;
		background: var(--s2);
		padding: 12px;
	}
	.mini-card {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 9px 10px;
		background: var(--s3);
		border-radius: 8px;
		border: 1px solid var(--bdr);
		margin-bottom: 8px;
	}
	.mini-card__stripe {
		width: 3px;
		height: 28px;
		border-radius: 2px;
		background: var(--ruby);
		animation: pulseDot 1.8s ease-in-out infinite;
	}
	.mini-card__content {
		flex: 1;
		min-width: 0;
	}
	.mini-card__name,
	.mini-tag,
	.policy-chip {
		font-size: 11px;
	}
	.mini-card__name {
		color: var(--white);
		font-weight: 600;
	}
	.mini-card__right {
		text-align: right;
	}
	.mini-card__cost {
		font-family: var(--font-display);
		font-size: 13px;
		font-weight: 700;
		color: var(--amber);
	}
	.mini-card__btns,
	.policy-chips,
	.topology-legend {
		display: flex;
		gap: 5px;
	}
	.mini-btn,
	.policy-chip,
	.mini-tag {
		display: inline-flex;
		align-items: center;
		border-radius: 4px;
		font-family: var(--font-mono);
		font-weight: 600;
	}
	.mini-tag {
		padding: 2px 5px;
		font-size: 8px;
		background: rgba(0, 194, 255, 0.12);
		color: var(--ion);
	}
	.mini-btn {
		width: 20px;
		height: 20px;
		justify-content: center;
	}
	.mini-btn--approve,
	.policy-chip--pass {
		background: rgba(0, 207, 124, 0.1);
		color: var(--jade);
	}
	.mini-btn--deny,
	.policy-chip--fail {
		background: rgba(255, 58, 92, 0.1);
		color: var(--ruby);
	}
	.policy-chip--warn {
		background: rgba(245, 166, 35, 0.1);
		color: var(--amber);
	}
	.policy-chip {
		padding: 3px 8px;
		font-size: 10px;
	}
	.topology-chart {
		display: block;
		width: 100%;
	}
	.topology-legend {
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
	@media (max-width: 900px) {
		.features__grid,
		.features__grid--flipped {
			grid-template-columns: 1fr;
		}
		.fcard__col {
			display: contents;
		}
	}
</style>
