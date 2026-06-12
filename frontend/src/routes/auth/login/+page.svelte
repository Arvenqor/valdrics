<script lang="ts">
	/* eslint-disable svelte/no-navigation-without-resolve */
	import { getTurnstileToken } from '$lib/security/turnstile';
	import { goto, invalidateAll } from '$app/navigation';
	import { page } from '$app/stores';
	import { base } from '$app/paths';
	import { edgeApiPath } from '$lib/edgeProxy';
	import {
		buildAuthCallbackPath,
		buildPostAuthRedirectPath,
		describePublicIntent,
		describePublicPersona,
		parsePublicAuthContext,
		type PublicAuthContext
	} from '$lib/auth/publicAuthIntent';
	import { emitLandingTelemetry } from '$lib/landing/landingTelemetry';
	import { broadcastAuthSessionChanged } from '$lib/auth/authSessionSignal';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let ssoLoading = $state(false);
	let magicLinkLoading = $state(false);
	let error = $state('');
	let success = $state('');
	let authContext = $derived<PublicAuthContext>(parsePublicAuthContext($page.url));
	let mode: 'login' | 'signup' = $state(parsePublicAuthContext($page.url).mode);
	let intentLabel = $derived<string | null>(describePublicIntent(authContext.intent));
	let personaLabel = $derived<string | null>(describePublicPersona(authContext.persona));

	type AuthFlowRequest =
		| { action: 'password-login'; email: string; password: string }
		| { action: 'password-signup'; email: string; password: string; emailRedirectTo: string }
		| {
				action: 'magic-link';
				email: string;
				shouldCreateUser: boolean;
				emailRedirectTo: string;
		  }
		| {
				action: 'sso';
				mode: 'domain' | 'provider_id';
				domain?: string;
				providerId?: string;
				redirectTo: string;
		  };

	type AuthFlowResponse = {
		ok?: boolean;
		url?: string | null;
		message?: string;
	};

	async function postAuthFlow(payload: AuthFlowRequest): Promise<AuthFlowResponse> {
		const response = await fetch(`${base}/auth/flow`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Accept: 'application/json'
			},
			credentials: 'include',
			body: JSON.stringify(payload)
		});

		const body = (await response.json().catch(() => null)) as AuthFlowResponse | null;
		if (!response.ok) {
			throw new Error(
				body?.message ||
					'Authentication is not configured for this environment. Contact support if this should be enabled.'
			);
		}

		return body ?? { ok: true };
	}

	$effect(() => {
		mode = authContext.mode;
		const oauthError = $page.url.searchParams.get('error');
		if (oauthError) {
			error = oauthError;
		}
	});

	type SsoDiscoveryResponse = {
		available: boolean;
		mode: 'domain' | 'provider_id' | null;
		domain: string | null;
		provider_id: string | null;
		reason: string | null;
	};

	function normalizeDomain(value: string): string {
		const normalized = value.trim().toLowerCase();
		if (!normalized.includes('@')) return '';
		return (
			normalized
				.split('@')[1]
				?.trim()
				.toLowerCase()
				.replace(/^\.+|\.+$/g, '') ?? ''
		);
	}

	function callbackRedirectTo(): string {
		if (typeof window === 'undefined') {
			return `${base}/auth/callback`;
		}
		const callbackPath = buildAuthCallbackPath(authContext);
		return `${window.location.origin}${base}${callbackPath}`;
	}

	function emitAuthEvent(action: string, value?: string): void {
		emitLandingTelemetry(action, 'auth', value, {
			persona: authContext.persona,
			funnelStage: 'signup_intent',
			pagePath: $page.url.pathname,
			experiment: undefined,
			utm: authContext.utm
		});
	}

	async function handleSubmit() {
		loading = true;
		error = '';
		success = '';

		try {
			if (mode === 'login') {
				emitAuthEvent('auth_password_submit', 'login');
				await postAuthFlow({
					action: 'password-login',
					email,
					password
				});

				broadcastAuthSessionChanged();

				// Invalidate all load functions to refresh user data, then navigate
				await invalidateAll();
				const nextPath = buildPostAuthRedirectPath(authContext);
				await goto(`${base}${nextPath}`);
			} else {
				emitAuthEvent('auth_password_submit', 'signup');
				await postAuthFlow({
					action: 'password-signup',
					email,
					password,
					emailRedirectTo: callbackRedirectTo()
				});
				success =
					'Check your email for the confirmation link. Your setup flow will continue after verification.';
			}
		} catch (e) {
			const err = e as Error;
			error = err.message;
		} finally {
			loading = false;
		}
	}

	async function handleMagicLinkSubmit() {
		magicLinkLoading = true;
		error = '';
		success = '';
		try {
			const normalizedEmail = email.trim().toLowerCase();
			if (!normalizedEmail) {
				throw new Error('Enter your work email to continue.');
			}
			emitAuthEvent('auth_magic_link_submit', mode);
			await postAuthFlow({
				action: 'magic-link',
				email: normalizedEmail,
				emailRedirectTo: callbackRedirectTo(),
				shouldCreateUser: mode === 'signup'
			});
			success = 'Secure sign-in link sent. Check your inbox to continue.';
		} catch (e) {
			const err = e as Error;
			error = err.message;
		} finally {
			magicLinkLoading = false;
		}
	}

	async function handleSsoSubmit() {
		ssoLoading = true;
		error = '';
		success = '';
		try {
			if (!email.trim()) {
				throw new Error('Enter your work email to continue with SSO.');
			}

			const turnstileToken = await getTurnstileToken('sso_discovery');
			const res = await fetch(edgeApiPath('/public/sso/discovery'), {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					...(turnstileToken ? { 'X-Turnstile-Token': turnstileToken } : {})
				},
				body: JSON.stringify({ email: email.trim().toLowerCase() })
			});
			if (!res.ok) {
				throw new Error('Unable to discover SSO configuration. Try again.');
			}
			const discovery = (await res.json()) as SsoDiscoveryResponse;
			if (!discovery.available || !discovery.mode) {
				throw new Error(
					discovery.reason === 'sso_not_configured_for_domain'
						? 'No SSO configuration was found for your domain.'
						: 'SSO is not ready for this domain. Contact your admin.'
				);
			}

			const redirectTo = callbackRedirectTo();
			emitAuthEvent('auth_sso_submit', discovery.mode);
			if (discovery.mode === 'provider_id') {
				if (!discovery.provider_id) {
					throw new Error('SSO provider configuration is incomplete.');
				}
				const data = await postAuthFlow({
					action: 'sso',
					mode: 'provider_id',
					providerId: discovery.provider_id,
					redirectTo
				});
				if (!data.url) {
					throw new Error('SSO redirect URL was not returned.');
				}
				window.location.assign(data.url);
				return;
			}

			const domain = discovery.domain || normalizeDomain(email);
			if (!domain) {
				throw new Error('Unable to determine your SSO domain.');
			}
			const data = await postAuthFlow({
				action: 'sso',
				mode: 'domain',
				domain,
				redirectTo
			});
			if (!data.url) {
				throw new Error('SSO redirect URL was not returned.');
			}
			window.location.assign(data.url);
		} catch (e) {
			const err = e as Error;
			error = err.message;
		} finally {
			ssoLoading = false;
		}
	}
</script>

<svelte:head>
	<title>{mode === 'login' ? 'Sign In' : 'Create Account'} | Valdrics</title>
</svelte:head>

<div class="auth-page">
	<div class="auth-frame">
		<section class="auth-panel" aria-labelledby="auth-heading">
			<div class="auth-brand-row">
				<a href={`${base}/`} class="auth-brand" aria-label="Valdrics home">
					<span class="auth-brand__mark" aria-hidden="true">
						<img src={`${base}/valdrics_icon.png`} alt="" width="32" height="32" />
					</span>
					<span class="auth-brand__word">VALDRICS</span>
				</a>
				<span class="auth-route-label">
					{mode === 'login' ? 'Secure access' : 'Workspace setup'}
				</span>
			</div>

			<div class="auth-heading">
				<h1 id="auth-heading">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>
				<p>
					{mode === 'login'
						? 'Sign in to continue with controlled execution.'
						: 'Create a verified workspace and continue into onboarding.'}
				</p>
				{#if intentLabel || personaLabel}
					<p class="auth-context">
						Starting with
						{#if intentLabel}
							<strong>{intentLabel}</strong>
						{/if}
						{#if intentLabel && personaLabel}
							for
						{/if}
						{#if personaLabel}
							<strong>{personaLabel}</strong>
						{/if}
					</p>
				{/if}
			</div>

			{#if error}
				<div role="alert" class="auth-message auth-message--error">
					<span aria-hidden="true">!</span>
					<p>{error}</p>
				</div>
			{/if}

			{#if success}
				<div role="status" class="auth-message auth-message--success">
					<span aria-hidden="true">✓</span>
					<p>{success}</p>
				</div>
			{/if}

			<form
				class="auth-form"
				onsubmit={(event) => {
					event.preventDefault();
					void handleSubmit();
				}}
			>
				<div class="auth-field">
					<label for="email">Email address</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						required
						placeholder="you@company.com"
						autocomplete="email"
					/>
				</div>

				<div class="auth-field">
					<label for="password">Password</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						required
						minlength="6"
						placeholder="Minimum 6 characters"
						autocomplete={mode === 'login' ? 'current-password' : 'new-password'}
					/>
				</div>

				<button type="submit" class="auth-button auth-button--primary" disabled={loading}>
					{#if loading}
						<span class="auth-spinner" aria-hidden="true"></span>
						<span>Checking credentials...</span>
					{:else}
						{mode === 'login' ? 'Sign in' : 'Create account'}
					{/if}
				</button>
			</form>

			<div class="auth-divider" aria-hidden="true">
				<span></span>
				<small>or</small>
				<span></span>
			</div>

			<div class="auth-secondary-actions">
				<button
					type="button"
					class="auth-button auth-button--secondary"
					disabled={magicLinkLoading}
					onclick={() => void handleMagicLinkSubmit()}
					aria-label={mode === 'login' ? 'Send secure sign-in link' : 'Send secure signup link'}
				>
					{#if magicLinkLoading}
						<span class="auth-spinner auth-spinner--muted" aria-hidden="true"></span>
						<span>Sending secure link...</span>
					{:else}
						{mode === 'login' ? 'Send secure sign-in link' : 'Send secure signup link'}
					{/if}
				</button>

				<button
					type="button"
					class="auth-button auth-button--secondary"
					disabled={ssoLoading}
					onclick={() => void handleSsoSubmit()}
					aria-label="Continue with SSO"
				>
					{#if ssoLoading}
						<span class="auth-spinner auth-spinner--muted" aria-hidden="true"></span>
						<span>Redirecting to IdP...</span>
					{:else}
						Continue with SSO
					{/if}
				</button>
			</div>

			<p class="auth-switch">
				{#if mode === 'login'}
					Don't have an account?
					<button type="button" onclick={() => (mode = 'signup')}>Sign up</button>
				{:else}
					Already have an account?
					<button type="button" onclick={() => (mode = 'login')}>Sign in</button>
				{/if}
			</p>

			<p class="auth-legal">
				By continuing, you agree to our
				<a href={`${base}/terms`}>Terms</a>
				and
				<a href={`${base}/privacy`}>Privacy Policy</a>.
			</p>
		</section>

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
	</div>
</div>

<style>
	.auth-page {
		position: relative;
		isolation: isolate;
		width: 100vw;
		margin-inline: calc(50% - 50vw);
		overflow: hidden;
		background:
			linear-gradient(135deg, rgb(3 9 18) 0%, rgb(7 16 25) 48%, rgb(8 21 18) 100%),
			linear-gradient(90deg, rgb(34 211 238 / 0.08), rgb(52 211 153 / 0.1));
		color: var(--color-ink-100);
	}

	.auth-page::before {
		content: '';
		position: absolute;
		inset: 0;
		z-index: -2;
		background-image:
			linear-gradient(rgb(148 163 184 / 0.055) 1px, transparent 1px),
			linear-gradient(90deg, rgb(148 163 184 / 0.045) 1px, transparent 1px);
		background-size: 48px 48px;
		mask-image: linear-gradient(180deg, rgb(0 0 0 / 0.9), transparent 92%);
	}

	.auth-page::after {
		content: '';
		position: absolute;
		inset: 0;
		z-index: -1;
		background:
			linear-gradient(110deg, transparent 0 20%, rgb(34 211 238 / 0.1) 20% 20.2%, transparent 20.2% 100%),
			linear-gradient(150deg, transparent 0 70%, rgb(251 191 36 / 0.1) 70% 70.18%, transparent 70.18% 100%);
		opacity: 0.9;
	}

	.auth-frame {
		display: grid;
		grid-template-columns: minmax(0, 440px) minmax(18rem, 0.86fr);
		gap: clamp(1rem, 4vw, 3rem);
		align-items: stretch;
		width: min(1120px, calc(100% - 2rem));
		min-height: min(720px, calc(100vh - 9rem));
		margin: 0 auto;
		padding: clamp(1.5rem, 4vw, 4rem) 0;
	}

	.auth-panel,
	.auth-evidence {
		border: 1px solid rgb(128 154 176 / 0.18);
		border-radius: var(--radius-md);
		background:
			linear-gradient(180deg, rgb(15 19 24 / 0.94), rgb(10 13 18 / 0.96)),
			radial-gradient(460px 220px at 18% 0%, rgb(34 211 238 / 0.1), transparent 72%);
		box-shadow:
			inset 0 1px 0 rgb(255 255 255 / 0.06),
			0 30px 80px rgb(0 0 0 / 0.34);
	}

	.auth-panel {
		display: flex;
		flex-direction: column;
		padding: clamp(1.35rem, 3vw, 2rem);
	}

	.auth-brand-row,
	.auth-brand,
	.auth-route-label,
	.auth-message,
	.auth-button,
	.auth-divider,
	.auth-evidence li {
		display: flex;
		align-items: center;
	}

	.auth-brand-row {
		justify-content: space-between;
		gap: 1rem;
		margin-bottom: clamp(1.75rem, 3vw, 2.35rem);
	}

	.auth-brand {
		min-width: 0;
		gap: 0.65rem;
		color: var(--color-ink-50);
		text-decoration: none;
	}

	.auth-brand__mark {
		display: grid;
		place-items: center;
		width: 42px;
		height: 42px;
		border: 1px solid rgb(34 211 238 / 0.3);
		border-radius: var(--radius-md);
		background:
			radial-gradient(circle at 30% 18%, rgb(255 255 255 / 0.14), transparent 34%),
			linear-gradient(145deg, rgb(34 211 238 / 0.2), rgb(52 211 153 / 0.1) 58%, rgb(3 9 18 / 0.74));
		box-shadow: 0 14px 30px rgb(8 126 164 / 0.22);
	}

	.auth-brand__mark img {
		width: 30px;
		height: 30px;
		object-fit: contain;
		filter: drop-shadow(0 6px 10px rgb(34 211 238 / 0.22));
	}

	.auth-brand__word,
	.auth-route-label,
	.auth-context,
	.auth-evidence__header p,
	.auth-evidence li > span {
		font-family: var(--font-mono);
	}

	.auth-brand__word {
		font-size: 0.82rem;
		font-weight: 800;
		letter-spacing: 0.14em;
	}

	.auth-route-label {
		flex-shrink: 0;
		min-height: 2rem;
		padding: 0.3rem 0.55rem;
		border: 1px solid rgb(52 211 153 / 0.2);
		border-radius: var(--radius-sm);
		background: rgb(52 211 153 / 0.08);
		color: var(--color-success-300);
		font-size: 0.7rem;
		font-weight: 800;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}

	.auth-heading {
		margin-bottom: 1.35rem;
	}

	.auth-heading h1 {
		margin: 0;
		color: var(--color-ink-50);
		font-size: clamp(1.65rem, 3.4vw, 2.2rem);
		font-weight: 800;
		line-height: 1.05;
		letter-spacing: 0;
	}

	.auth-heading p {
		margin: 0.65rem 0 0;
		color: var(--color-ink-300);
		font-size: 0.95rem;
		line-height: 1.65;
	}

	.auth-context {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		align-items: center;
		color: var(--color-ink-200);
		font-size: 0.78rem;
	}

	.auth-context strong {
		color: var(--color-accent-300);
		font-weight: 800;
	}

	.auth-message {
		gap: 0.65rem;
		margin-bottom: 1rem;
		padding: 0.78rem 0.85rem;
		border-radius: var(--radius-md);
		font-size: 0.88rem;
		line-height: 1.45;
	}

	.auth-message span {
		display: grid;
		place-items: center;
		flex: 0 0 auto;
		width: 1.35rem;
		height: 1.35rem;
		border-radius: var(--radius-full);
		font-weight: 900;
	}

	.auth-message p {
		margin: 0;
	}

	.auth-message--error {
		border: 1px solid rgb(244 63 94 / 0.28);
		background: rgb(244 63 94 / 0.1);
		color: var(--color-danger-400);
	}

	.auth-message--error span {
		background: rgb(244 63 94 / 0.16);
	}

	.auth-message--success {
		border: 1px solid rgb(16 185 129 / 0.26);
		background: rgb(16 185 129 / 0.1);
		color: var(--color-success-300);
	}

	.auth-message--success span {
		background: rgb(16 185 129 / 0.16);
	}

	.auth-form,
	.auth-secondary-actions {
		display: grid;
		gap: 0.9rem;
	}

	.auth-field {
		display: grid;
		gap: 0.42rem;
	}

	.auth-field label {
		color: var(--color-ink-200);
		font-size: 0.83rem;
		font-weight: 750;
	}

	.auth-field input {
		width: 100%;
		min-height: 46px;
		padding: 0.68rem 0.82rem;
		border: 1px solid rgb(128 154 176 / 0.22);
		border-radius: var(--radius-md);
		background: rgb(3 9 18 / 0.56);
		color: var(--color-ink-50);
		font: inherit;
		font-size: 0.95rem;
		outline: none;
		transition:
			border-color var(--duration-fast) var(--ease-out),
			box-shadow var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out);
	}

	.auth-field input::placeholder {
		color: var(--color-ink-500);
	}

	.auth-field input:focus-visible {
		border-color: rgb(34 211 238 / 0.62);
		background: rgb(3 9 18 / 0.72);
		box-shadow: 0 0 0 3px rgb(34 211 238 / 0.13);
	}

	.auth-button {
		justify-content: center;
		gap: 0.55rem;
		width: 100%;
		min-height: 46px;
		border: 0;
		border-radius: var(--radius-md);
		font: inherit;
		font-size: 0.92rem;
		font-weight: 850;
		cursor: pointer;
		transition:
			transform var(--duration-fast) var(--ease-out),
			border-color var(--duration-fast) var(--ease-out),
			background var(--duration-fast) var(--ease-out),
			color var(--duration-fast) var(--ease-out),
			box-shadow var(--duration-fast) var(--ease-out);
	}

	.auth-button:hover:not(:disabled) {
		transform: translateY(-1px);
	}

	.auth-button:focus-visible,
	.auth-switch button:focus-visible,
	.auth-brand:focus-visible,
	.auth-legal a:focus-visible {
		outline: 2px solid var(--color-success-400);
		outline-offset: 3px;
	}

	.auth-button:disabled {
		cursor: wait;
		opacity: 0.68;
	}

	.auth-button--primary {
		margin-top: 0.15rem;
		background: linear-gradient(135deg, var(--color-success-400), var(--color-accent-300));
		color: var(--color-ink-950);
		box-shadow: 0 18px 34px rgb(16 185 129 / 0.22);
	}

	.auth-button--primary:hover:not(:disabled) {
		box-shadow: 0 24px 46px rgb(34 211 238 / 0.25);
	}

	.auth-button--secondary {
		border: 1px solid rgb(128 154 176 / 0.22);
		background: rgb(128 154 176 / 0.08);
		color: var(--color-ink-100);
	}

	.auth-button--secondary:hover:not(:disabled) {
		border-color: rgb(34 211 238 / 0.34);
		background: rgb(34 211 238 / 0.09);
		color: var(--color-ink-50);
	}

	.auth-spinner {
		display: inline-block;
		width: 0.9rem;
		height: 0.9rem;
		border: 2px solid rgb(3 9 18 / 0.28);
		border-top-color: rgb(3 9 18);
		border-radius: var(--radius-full);
		animation: authSpin 0.7s linear infinite;
	}

	.auth-spinner--muted {
		border-color: rgb(226 232 239 / 0.22);
		border-top-color: var(--color-ink-50);
	}

	.auth-divider {
		gap: 0.75rem;
		margin: 1rem 0;
		color: var(--color-ink-500);
	}

	.auth-divider span {
		height: 1px;
		flex: 1;
		background: rgb(128 154 176 / 0.18);
	}

	.auth-divider small {
		font-size: 0.72rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.12em;
	}

	.auth-switch,
	.auth-legal {
		margin: 1rem 0 0;
		color: var(--color-ink-300);
		font-size: 0.86rem;
		line-height: 1.6;
		text-align: center;
	}

	.auth-switch button,
	.auth-legal a {
		border: 0;
		background: transparent;
		color: var(--color-accent-300);
		font: inherit;
		font-weight: 800;
		text-decoration: none;
		cursor: pointer;
	}

	.auth-switch button:hover,
	.auth-legal a:hover {
		color: var(--color-success-300);
		text-decoration: underline;
		text-underline-offset: 0.2em;
	}

	.auth-legal {
		margin-top: 0.75rem;
		font-size: 0.76rem;
		color: var(--color-ink-400);
	}

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
		gap: 0.85rem;
		align-items: flex-start;
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

	@keyframes authSpin {
		to {
			transform: rotate(360deg);
		}
	}

	@media (max-width: 840px) {
		.auth-frame {
			grid-template-columns: minmax(0, 1fr);
			min-height: auto;
		}

		.auth-evidence {
			min-height: auto;
		}

		.auth-evidence ul {
			margin-top: 1.5rem;
		}
	}

	@media (max-width: 520px) {
		.auth-frame {
			width: min(100% - 1rem, 440px);
			padding: 1rem 0 1.25rem;
		}

		.auth-panel,
		.auth-evidence {
			padding: 1rem;
		}

		.auth-brand-row {
			align-items: flex-start;
			flex-direction: column;
			margin-bottom: 1.5rem;
		}

		.auth-heading h1 {
			font-size: 1.55rem;
		}
	}
</style>
