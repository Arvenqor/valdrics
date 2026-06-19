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
	import AuthEvidence from './AuthEvidence.svelte';
	import './login.css';

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

		<AuthEvidence />
	</div>
</div>
