import { describe, expect, it, vi } from 'vitest';

import { actions } from './+page.server';

describe('auth logout route', () => {
	it('signs out through Supabase and redirects to the production login route', async () => {
		const signOut = vi.fn().mockResolvedValue({ error: null });

		await expect(
			actions.default({
				locals: {
					supabase: {
						auth: { signOut }
					}
				}
			} as unknown as Parameters<typeof actions.default>[0])
		).rejects.toMatchObject({
			status: 303,
			location: '/auth/login'
		});

		expect(signOut).toHaveBeenCalledOnce();
	});
});
