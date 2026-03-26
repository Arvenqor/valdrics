import { json, type RequestHandler } from '@sveltejs/kit';

type PasswordLoginRequest = {
	action: 'password-login';
	email: string;
	password: string;
};

type PasswordSignupRequest = {
	action: 'password-signup';
	email: string;
	password: string;
	emailRedirectTo: string;
};

type MagicLinkRequest = {
	action: 'magic-link';
	email: string;
	shouldCreateUser: boolean;
	emailRedirectTo: string;
};

type SsoRequest = {
	action: 'sso';
	mode: 'domain' | 'provider_id';
	domain?: string;
	providerId?: string;
	redirectTo: string;
};

type AuthFlowRequest = PasswordLoginRequest | PasswordSignupRequest | MagicLinkRequest | SsoRequest;

const NO_STORE_HEADERS = {
	'cache-control': 'no-store',
	'content-type': 'application/json'
};

function fail(message: string, status = 400): Response {
	return json({ message }, { status, headers: NO_STORE_HEADERS });
}

function normalizeEmail(value: unknown): string {
	return typeof value === 'string' ? value.trim().toLowerCase() : '';
}

function normalizePassword(value: unknown): string {
	return typeof value === 'string' ? value : '';
}

function normalizeRedirectTo(value: unknown, origin: string): string | null {
	if (typeof value !== 'string' || !value.trim()) return null;
	try {
		const parsed = new URL(value);
		if (parsed.origin !== origin) return null;
		return parsed.toString();
	} catch {
		return null;
	}
}

export const POST: RequestHandler = async ({ request, locals, url }) => {
	if (!locals.supabase) {
		return fail('Authentication is not configured for this environment.', 503);
	}

	const body = (await request.json().catch(() => null)) as AuthFlowRequest | null;
	if (!body || typeof body !== 'object' || typeof body.action !== 'string') {
		return fail('Invalid authentication request.');
	}

	if (body.action === 'password-login') {
		const email = normalizeEmail(body.email);
		const password = normalizePassword(body.password);
		if (!email || !password) return fail('Enter your email and password to continue.');
		const { error } = await locals.supabase.auth.signInWithPassword({ email, password });
		if (error) return fail(error.message, 401);
		return json({ ok: true }, { headers: NO_STORE_HEADERS });
	}

	if (body.action === 'password-signup') {
		const email = normalizeEmail(body.email);
		const password = normalizePassword(body.password);
		const emailRedirectTo = normalizeRedirectTo(body.emailRedirectTo, url.origin);
		if (!email || !password) return fail('Enter your email and password to continue.');
		if (!emailRedirectTo) return fail('Invalid email confirmation redirect target.');
		const { error } = await locals.supabase.auth.signUp({
			email,
			password,
			options: { emailRedirectTo }
		});
		if (error) return fail(error.message, 400);
		return json({ ok: true }, { headers: NO_STORE_HEADERS });
	}

	if (body.action === 'magic-link') {
		const email = normalizeEmail(body.email);
		const emailRedirectTo = normalizeRedirectTo(body.emailRedirectTo, url.origin);
		if (!email) return fail('Enter your work email to continue.');
		if (!emailRedirectTo) return fail('Invalid email redirect target.');
		const { error } = await locals.supabase.auth.signInWithOtp({
			email,
			options: {
				emailRedirectTo,
				shouldCreateUser: body.shouldCreateUser
			}
		});
		if (error) return fail(error.message, 400);
		return json({ ok: true }, { headers: NO_STORE_HEADERS });
	}

	if (body.action === 'sso') {
		const redirectTo = normalizeRedirectTo(body.redirectTo, url.origin);
		if (!redirectTo) return fail('Invalid SSO redirect target.');
		const requestParams =
			body.mode === 'provider_id'
				? body.providerId
					? { providerId: body.providerId, options: { redirectTo } }
					: null
				: body.domain
					? { domain: body.domain, options: { redirectTo } }
					: null;
		if (!requestParams) return fail('SSO configuration is incomplete.');
		const { data, error } = await locals.supabase.auth.signInWithSSO(requestParams);
		if (error) return fail(error.message, 400);
		return json({ url: data?.url ?? null }, { headers: NO_STORE_HEADERS });
	}

	return fail('Unsupported authentication action.');
};
