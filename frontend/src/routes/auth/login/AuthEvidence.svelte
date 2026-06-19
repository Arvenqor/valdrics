<aside class="auth-evidence" aria-label="Valdrics auth contract">
	<div class="auth-evidence__header">
		<p>Valdrics access protocol</p>
		<strong>Contract-backed identity, not a demo gate.</strong>
	</div>
	<ul>
		<li>
			<span>01</span>
			<div>
				<strong>Same-origin callback</strong>
				<p>Confirmation and SSO redirects stay on verified Valdrics origins.</p>
			</div>
		</li>
		<li>
			<span>02</span>
			<div>
				<strong>Intent preserved</strong>
				<p>ROI and onboarding context survives email verification and password sign-in.</p>
			</div>
		</li>
		<li>
			<span>03</span>
			<div>
				<strong>Edge-routed SSO</strong>
				<p>Domain discovery remains behind the production edge proxy contract.</p>
			</div>
		</li>
	</ul>
</aside>

<style>
	.auth-evidence {
		position: relative;
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		min-height: 100%;
		padding: clamp(1.4rem, 3vw, 2rem);
		background:
			linear-gradient(145deg, rgb(10 13 18 / 0.88), rgb(13 21 26 / 0.94)),
			radial-gradient(620px 260px at 80% 10%, rgb(251 191 36 / 0.1), transparent 68%);
		border: 1px solid rgb(128 154 176 / 0.18);
		border-radius: var(--radius-md);
		box-shadow:
			inset 0 1px 0 rgb(255 255 255 / 0.06),
			0 30px 80px rgb(0 0 0 / 0.34);
	}

	.auth-evidence::before {
		content: '';
		position: absolute;
		inset: 1rem;
		border: 1px solid rgb(34 211 238 / 0.12);
		border-radius: var(--radius-md);
		pointer-events: none;
	}

	.auth-evidence__header {
		position: relative;
		display: grid;
		gap: 0.7rem;
		max-width: 30rem;
	}

	.auth-evidence__header p {
		margin: 0;
		color: var(--color-success-300);
		font-size: 0.75rem;
		font-weight: 900;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		font-family: var(--font-mono);
	}

	.auth-evidence__header strong {
		color: var(--color-ink-50);
		font-size: clamp(1.45rem, 3vw, 2.55rem);
		font-weight: 850;
		line-height: 1.08;
		letter-spacing: 0;
	}

	.auth-evidence ul {
		position: relative;
		display: grid;
		gap: 0.9rem;
		margin: clamp(2rem, 8vw, 7rem) 0 0;
		padding: 0;
		list-style: none;
	}

	.auth-evidence li {
		display: flex;
		align-items: flex-start;
		gap: 0.85rem;
		padding: 0.9rem;
		border: 1px solid rgb(128 154 176 / 0.15);
		border-radius: var(--radius-md);
		background: rgb(3 9 18 / 0.38);
	}

	.auth-evidence li > span {
		display: grid;
		place-items: center;
		flex: 0 0 auto;
		width: 2rem;
		height: 2rem;
		border: 1px solid rgb(34 211 238 / 0.24);
		border-radius: var(--radius-sm);
		background: rgb(34 211 238 / 0.08);
		color: var(--color-accent-300);
		font-size: 0.75rem;
		font-weight: 900;
		font-family: var(--font-mono);
	}

	.auth-evidence li strong {
		display: block;
		color: var(--color-ink-100);
		font-size: 0.92rem;
	}

	.auth-evidence li p {
		margin: 0.22rem 0 0;
		color: var(--color-ink-400);
		font-size: 0.83rem;
		line-height: 1.5;
	}

	@media (max-width: 840px) {
		.auth-evidence {
			min-height: auto;
		}

		.auth-evidence ul {
			margin-top: 1.5rem;
		}
	}

	@media (max-width: 520px) {
		.auth-evidence {
			padding: 1rem;
		}
	}
</style>
