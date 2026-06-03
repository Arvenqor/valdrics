import { describe, expect, it, vi } from 'vitest';

import { POST } from './+server';

type MockAuthApi = {
	signInWithPassword: ReturnType<typeof vi.fn>;
	signUp: ReturnType<typeof vi.fn>;
	signInWithOtp: ReturnType<typeof vi.fn>;
	signInWithSSO: ReturnType<typeof vi.fn>;
};

function createAuthApi(): MockAuthApi {
	return {
		signInWithPassword: vi.fn().mockResolvedValue({ error: null }),
		signUp: vi.fn().mockResolvedValue({ error: null }),
		signInWithOtp: vi.fn().mockResolvedValue({ error: null }),
		signInWithSSO: vi.fn().mockResolvedValue({ data: { url: 'https://idp.example' }, error: null })
	};
}

function createEvent(body: unknown, auth = createAuthApi()) {
	return {
		request: new Request('https://example.com/auth/flow', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		}),
		url: new URL('https://example.com/auth/flow'),
		locals: {
			supabase: {
				auth
			}
		}
	} as unknown as Parameters<typeof POST>[0];
}

describe('auth flow route', () => {
	it('signs in with password on the server and normalizes email', async () => {
		const auth = createAuthApi();
		const response = await POST(
			createEvent(
				{
					action: 'password-login',
					email: 'USER@EXAMPLE.COM',
					password: 'TopSecret123'
				},
				auth
			)
		);

		expect(response.status).toBe(200);
		expect(auth.signInWithPassword).toHaveBeenCalledWith({
			email: 'user@example.com',
			password: 'TopSecret123'
		});
	});

	it('rejects cross-origin signup redirect targets', async () => {
		const auth = createAuthApi();
		const response = await POST(
			createEvent(
				{
					action: 'password-signup',
					email: 'user@example.com',
					password: 'TopSecret123',
					emailRedirectTo: 'https://evil.example/auth/callback'
				},
				auth
			)
		);

		expect(response.status).toBe(400);
		expect(await response.json()).toEqual({
			message: 'Invalid email confirmation redirect target.'
		});
		expect(auth.signUp).not.toHaveBeenCalled();
	});

	it('returns the SSO redirect URL for provider-based flows', async () => {
		const auth = createAuthApi();
		const response = await POST(
			createEvent(
				{
					action: 'sso',
					mode: 'provider_id',
					providerId: 'sso-provider-id',
					redirectTo: 'https://example.com/auth/callback'
				},
				auth
			)
		);

		expect(response.status).toBe(200);
		expect(auth.signInWithSSO).toHaveBeenCalledWith({
			providerId: 'sso-provider-id',
			options: { redirectTo: 'https://example.com/auth/callback' }
		});
		expect(await response.json()).toEqual({
			url: 'https://idp.example'
		});
	});
});
