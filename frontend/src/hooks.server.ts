/**
 * Server Hooks - Runs on every request
 *
 * Purpose:
 * 1. Extract valdrics_token and validate session against FastAPI profile endpoint
 * 2. Fall back to Supabase client auth if needed
 * 3. Preserve Playwright E2E auth bypasses for testing
 */

import { createServerClient } from '@supabase/ssr';
import { env as publicEnv } from '$env/dynamic/public';
import { env } from '$env/dynamic/private';
import type { Handle } from '@sveltejs/kit';
import type { Session, User } from '@supabase/supabase-js';
import { randomBytes, timingSafeEqual } from 'node:crypto';
import { serverLogger } from '$lib/logging/server';
import { isPublicPath } from '$lib/routeProtection';
import { buildPublicAuthHref } from '$lib/public/publicAppOrigin';
import { canUseE2EAuthBypass, shouldUseSecureCookies } from '$lib/serverSecurity';
import {
	createPlaywrightE2EAccessToken,
	decodePlaywrightE2EBrowserSessionCookie,
	resolvePlaywrightSupabaseStorageKey,
	resolvePlaywrightE2EFixture,
	verifyPlaywrightE2EAccessToken
} from '$lib/testing/playwrightE2EAuth';
import { resolveBackendOrigin } from '$lib/server/backend-origin';

const E2E_AUTH_HEADER = 'x-valdrics-e2e-auth';

function buildE2EBypassAuth(params: {
	jwtSecret: string;
	jwtIssuer: string;
	fixture: ReturnType<typeof resolvePlaywrightE2EFixture>;
}): { session: Session; user: User } {
	const now = Math.floor(Date.now() / 1000);
	const accessToken = createPlaywrightE2EAccessToken({
		secret: params.jwtSecret,
		issuer: params.jwtIssuer,
		fixture: params.fixture
	});
	const user = {
		id: params.fixture.userId,
		aud: 'authenticated',
		role: 'authenticated',
		email: params.fixture.email,
		email_confirmed_at: new Date(0).toISOString(),
		phone: '',
		app_metadata: { provider: 'email', providers: ['email'], tier: params.fixture.tier },
		user_metadata: {
			name: params.fixture.userName,
			source: 'playwright',
			persona: params.fixture.persona
		},
		identities: [],
		created_at: new Date(0).toISOString(),
		updated_at: new Date().toISOString(),
		is_anonymous: false
	} as unknown as User;

	const session = {
		access_token: accessToken,
		refresh_token: randomBytes(32).toString('hex'),
		expires_in: 3600,
		expires_at: now + 3600,
		token_type: 'bearer',
		user
	} as unknown as Session;

	return { session, user };
}

function hasMatchingE2ESecret(provided: string | null, expected: string): boolean {
	const providedValue = String(provided || '').trim();
	const expectedValue = String(expected || '').trim();
	if (!providedValue || !expectedValue) {
		return false;
	}

	const providedBytes = Buffer.from(providedValue, 'utf8');
	const expectedBytes = Buffer.from(expectedValue, 'utf8');
	if (providedBytes.length !== expectedBytes.length) {
		return false;
	}

	return timingSafeEqual(providedBytes, expectedBytes);
}

function resolveE2EFixtureFromEnv() {
	return resolvePlaywrightE2EFixture({
		tenantId: env.PLAYWRIGHT_E2E_TENANT_ID,
		tenantName: env.PLAYWRIGHT_E2E_TENANT_NAME,
		userId: env.PLAYWRIGHT_E2E_USER_ID,
		userName: env.PLAYWRIGHT_E2E_USER_NAME,
		email: env.PLAYWRIGHT_E2E_USER_EMAIL,
		role: env.PLAYWRIGHT_E2E_USER_ROLE,
		persona: env.PLAYWRIGHT_E2E_USER_PERSONA,
		tier: env.PLAYWRIGHT_E2E_TIER
	});
}

function tryResolveE2ECookieSession(params: {
	event: Parameters<Handle>[0]['event'];
	publicSupabaseUrl: string;
	jwtSecret: string;
	jwtIssuer: string;
	fixture: ReturnType<typeof resolvePlaywrightE2EFixture>;
}): { session: Session; user: User } | null {
	const storageKey =
		String(env.PLAYWRIGHT_SUPABASE_STORAGE_KEY || '').trim() ||
		resolvePlaywrightSupabaseStorageKey(params.publicSupabaseUrl);
	if (!storageKey) {
		return null;
	}

	const browserSession = decodePlaywrightE2EBrowserSessionCookie(
		params.event.cookies.get(storageKey)
	);
	if (!browserSession) {
		return null;
	}

	if (
		browserSession.user.id !== params.fixture.userId ||
		browserSession.user.email !== params.fixture.email ||
		!verifyPlaywrightE2EAccessToken({
			token: browserSession.access_token,
			secret: params.jwtSecret,
			issuer: params.jwtIssuer,
			fixture: params.fixture
		})
	) {
		serverLogger.warn('e2e_auth_cookie_validation_failed', {
			url: params.event.url.toString(),
			storageKey
		});
		return null;
	}

	return buildE2EBypassAuth({
		jwtSecret: params.jwtSecret,
		jwtIssuer: params.jwtIssuer,
		fixture: params.fixture
	});
}

export const handle: Handle = async ({ event, resolve }) => {
	const isPublic = isPublicPath(event.url.pathname);
	const isHttps = shouldUseSecureCookies(event.url, env.NODE_ENV || '');
	const publicSupabaseUrl = String(publicEnv.PUBLIC_SUPABASE_URL || '').trim();
	const publicSupabaseAnonKey = String(publicEnv.PUBLIC_SUPABASE_ANON_KEY || '').trim();
	const hasSupabasePublicConfig = !!(publicSupabaseUrl && publicSupabaseAnonKey);
	const authAppHref = buildPublicAuthHref(`${event.url.pathname}${event.url.search}`, event.url);
	const isAuthRoute = event.url.pathname === '/auth' || event.url.pathname.startsWith('/auth/');

	if (isAuthRoute && authAppHref.startsWith('https://')) {
		return new Response(null, {
			status: 307,
			headers: { Location: authAppHref }
		});
	}

	if (hasSupabasePublicConfig) {
		event.locals.supabase = createServerClient(publicSupabaseUrl, publicSupabaseAnonKey, {
			cookies: {
				get: (key) => event.cookies.get(key),
				set: (key, value, options) => {
					event.cookies.set(key, value, {
						path: '/',
						httpOnly: true,
						secure: isHttps,
						sameSite: 'strict',
						...options
					});
				},
				remove: (key, options) => {
					event.cookies.delete(key, {
						path: '/',
						httpOnly: true,
						secure: isHttps,
						sameSite: 'strict',
						...options
					});
				}
			}
		});
	}

	event.locals.safeGetSession = async () => {
		// 1. Try native valdrics_token cookie first (JWT session)
		const token = event.cookies.get('valdrics_token');
		if (token) {
			try {
				const backendOrigin = resolveBackendOrigin();
				const profileResponse = await fetch(`${backendOrigin}/api/v1/settings/profile`, {
					headers: {
						Authorization: `Bearer ${token}`
					}
				});
				if (profileResponse.ok) {
					const profile = await profileResponse.json();
					const parts = token.split('.');
					let userId = crypto.randomUUID();
					if (parts.length === 3) {
						try {
							const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString('utf8'));
							userId = payload.sub || userId;
						} catch {}
					}
					const user = {
						id: userId,
						email: profile.email,
						role: profile.role,
						tier: profile.tier,
						persona: profile.persona,
						user_metadata: {
							persona: profile.persona
						},
						app_metadata: {
							tier: profile.tier
						}
					} as any;
					const session = {
						access_token: token,
						user
					} as any;
					return { session, user };
				}
			} catch (error) {
				serverLogger.error('valdrics_token_validation_failed', {
					error: error instanceof Error ? error.message : String(error)
				});
			}
		}

		// 2. Playwright E2E Auth Bypass (intercept for automated test suites)
		const testingMode = env.TESTING === 'true';
		const allowProdPreviewBypass = env.E2E_ALLOW_PROD_PREVIEW === 'true';
		const canUseBypass = canUseE2EAuthBypass({
			testingMode,
			allowProdPreviewBypass,
			isDevBuild: import.meta.env.DEV,
			hostname: event.url.hostname
		});
		if (canUseBypass) {
			const fixture = resolveE2EFixtureFromEnv();
			const jwtSecret = String(env.SUPABASE_JWT_SECRET || '').trim();
			const jwtIssuer = String(env.SUPABASE_JWT_ISSUER || 'supabase').trim() || 'supabase';
			const provided = event.request.headers.get(E2E_AUTH_HEADER);
			const expected = String(env.E2E_AUTH_SECRET || '').trim();
			if (hasMatchingE2ESecret(provided, expected)) {
				try {
					return buildE2EBypassAuth({
						jwtSecret,
						jwtIssuer,
						fixture
					});
				} catch (error) {
					serverLogger.error('e2e_auth_bypass_session_build_failed', {
						url: event.url.toString(),
						error: error instanceof Error ? error.message : String(error)
					});
					return { session: null, user: null };
				}
			}

			const cookieSession = tryResolveE2ECookieSession({
				event,
				publicSupabaseUrl,
				jwtSecret,
				jwtIssuer,
				fixture
			});
			if (cookieSession) {
				return cookieSession;
			}
		}

		// 3. Fallback to Supabase SSR Auth Session if configured
		if (!hasSupabasePublicConfig) {
			return { session: null, user: null };
		}

		try {
			const {
				data: { session }
			} = await event.locals.supabase.auth.getSession();
			if (!session) return { session: null, user: null };

			const {
				data: { user },
				error
			} = await event.locals.supabase.auth.getUser();

			if (error || !user) {
				serverLogger.warn('supabase_session_validation_failed', {
					url: event.url.toString(),
					hasError: !!error,
					error: error?.message ?? null
				});
				return { session: null, user: null };
			}

			// Validate user identity against FastAPI backend settings profile check
			const backendOrigin = resolveBackendOrigin();
			const profileResponse = await fetch(`${backendOrigin}/api/v1/settings/profile`, {
				headers: {
					Authorization: `Bearer ${session.access_token}`
				}
			});

			if (!profileResponse.ok) {
				serverLogger.warn('fastapi_session_validation_failed', {
					url: event.url.toString(),
					status: profileResponse.status
				});
				return { session: null, user: null };
			}

			const profile = await profileResponse.json();
			const augmentedUser = {
				...user,
				role: profile.role,
				tier: profile.tier,
				persona: profile.persona,
				user_metadata: {
					...user.user_metadata,
					persona: profile.persona
				},
				app_metadata: {
					...user.app_metadata,
					tier: profile.tier
				}
			};

			return { session: { ...session, user: augmentedUser }, user: augmentedUser };
		} catch (error) {
			serverLogger.error('supabase_session_resolution_failed', {
				url: event.url.toString(),
				error: error instanceof Error ? error.message : String(error)
			});
			return { session: null, user: null };
		}
	};

	// Auth Guard: Protect all application routes by default.
	// Only allow public access to explicit public paths.
	if (!isPublic) {
		// Fail-closed: if auth is not configured, refuse protected requests with
		// 503 rather than redirecting — a misconfigured deployment must surface
		// a clear error instead of silently presenting a login page.
		if (!hasSupabasePublicConfig) {
			return new Response('Service temporarily unavailable. Authentication is not configured.', {
				status: 503,
				headers: { 'Cache-Control': 'no-store' }
			});
		}

		const { session } = await event.locals.safeGetSession();
		if (!session) {
			const next = `${event.url.pathname}${event.url.search}`;
			const loginPath = `/auth/login?mode=login&next=${encodeURIComponent(next)}`;
			return new Response(null, {
				status: 303,
				headers: { Location: buildPublicAuthHref(loginPath, event.url) }
			});
		}
	}

	const response = await resolve(event, {
		filterSerializedResponseHeaders(name) {
			return name === 'content-range' || name === 'x-supabase-api-version';
		}
	});

	// Security: prevent intermediary caching of authenticated HTML responses.
	const contentType = response.headers.get('content-type') || '';
	if (contentType.startsWith('text/html') && !isPublic) {
		response.headers.set('Cache-Control', 'no-store');
	}

	response.headers.set('X-Content-Type-Options', 'nosniff');
	response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
	response.headers.set('X-Frame-Options', 'DENY');
	response.headers.set(
		'Permissions-Policy',
		'camera=(), microphone=(), geolocation=(), payment=(), usb=()'
	);
	if (isHttps) {
		response.headers.set(
			'Strict-Transport-Security',
			'max-age=63072000; includeSubDomains; preload'
		);
	}

	return response;
};

/**
 * Global Error Handler - Catches unhandled errors during request processing
 */
export const handleError: import('@sveltejs/kit').HandleServerError = ({ error, event }) => {
	const errorId = crypto.randomUUID();

	serverLogger.error('Unhandled server error:', {
		errorId,
		error: error instanceof Error ? error.message : error,
		stack: error instanceof Error ? error.stack : undefined,
		url: event.url.toString()
	});

	return {
		message: 'An internal error occurred. Our engineering team has been notified.',
		errorId,
		code: 'INTERNAL_SERVER_ERROR'
	};
};
