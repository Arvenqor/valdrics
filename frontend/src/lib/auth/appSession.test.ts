import { describe, expect, it } from 'vitest';
import { resolveAppSession } from './appSession';

describe('resolveAppSession', () => {
	it('normalizes a FastAPI-backed runtime session into the app session contract', () => {
		const result = resolveAppSession({
			session: {
				access_token: 'token',
				user: {
					id: 'user-1',
					email: 'owner@example.com',
					tenant_id: 'tenant-1',
					role: 'owner',
					tier: 'enterprise',
					persona: 'finance'
				}
			}
		});

		expect(result).toEqual({
			accessToken: 'token',
			user: {
				id: 'user-1',
				email: 'owner@example.com',
				tenantId: 'tenant-1',
				role: 'owner',
				tier: 'enterprise',
				persona: 'finance',
				platformOperator: false
			}
		});
	});

	it('lets fresh profile data override stale token metadata', () => {
		const result = resolveAppSession({
			session: {
				access_token: 'token',
				user: {
					id: 'user-1',
					email: 'owner@example.com',
					user_metadata: { tenant_id: 'tenant-1', persona: 'engineering' },
					app_metadata: { tier: 'free' }
				}
			},
			profile: {
				role: 'admin',
				tier: 'growth',
				persona: 'leadership',
				platform_operator: true
			}
		});

		expect(result?.user).toMatchObject({
			tenantId: 'tenant-1',
			role: 'admin',
			tier: 'growth',
			persona: 'leadership',
			platformOperator: true
		});
	});

	it('returns null when the session is not authenticated', () => {
		expect(resolveAppSession({ session: null, user: null })).toBeNull();
		expect(resolveAppSession({ session: { access_token: 'token' }, user: null })).toBeNull();
	});
});
