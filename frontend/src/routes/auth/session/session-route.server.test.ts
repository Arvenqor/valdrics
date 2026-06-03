import { describe, expect, it, vi } from 'vitest';

import { GET } from './+server';

describe('auth session route', () => {
	it('returns 401 when there is no active session', async () => {
		const response = await GET({
			locals: {
				safeGetSession: vi.fn().mockResolvedValue({ session: null, user: null })
			}
		} as unknown as Parameters<typeof GET>[0]);

		expect(response.status).toBe(401);
		expect(await response.json()).toEqual({
			accessToken: null,
			tenantId: null
		});
	});

	it('returns access token and tenant id when session exists', async () => {
		const response = await GET({
			locals: {
				safeGetSession: vi.fn().mockResolvedValue({
					session: {
						access_token: 'access-token',
						user: {
							user_metadata: {
								tenant_id: 'tenant-123'
							}
						}
					},
					user: {
						id: 'user-1'
					}
				})
			}
		} as unknown as Parameters<typeof GET>[0]);

		expect(response.status).toBe(200);
		expect(await response.json()).toEqual({
			accessToken: 'access-token',
			tenantId: 'tenant-123'
		});
	});
});
