import { describe, expect, it } from 'vitest';
import { load } from './+page.server';

async function expectRedirectLocation(
	callback: () => unknown,
	expected: { status: number; location: string }
): Promise<void> {
	try {
		await callback();
		throw new Error('expected redirect to be thrown');
	} catch (error) {
		const redirectError = error as { status?: number; location?: string };
		expect(redirectError.status).toBe(expected.status);
		expect(redirectError.location).toBe(expected.location);
	}
}

describe('landing motion query canonicalization', () => {
	it('passes through supported motion variants', async () => {
		const result = await load({
			url: new URL('https://example.com/?motion=cinematic'),
			locals: {
				safeGetSession: async () => ({ user: null })
			}
		} as Parameters<typeof load>[0]);

		expect(result).toEqual({});
	});

	it('canonicalizes supported motion values to lowercase', async () => {
		await expectRedirectLocation(
			() =>
				load({
					url: new URL('https://example.com/?motion=CINEMATIC&utm_source=ads'),
					locals: {
						safeGetSession: async () => ({ user: null })
					}
				} as Parameters<typeof load>[0]),
			{
				status: 308,
				location: '/?motion=cinematic&utm_source=ads'
			}
		);
	});

	it('strips unsupported motion values and preserves other query params', async () => {
		await expectRedirectLocation(
			() =>
				load({
					url: new URL('https://example.com/?motion=neon&utm_source=ads&persona=finance'),
					locals: {
						safeGetSession: async () => ({ user: null })
					}
				} as Parameters<typeof load>[0]),
			{
				status: 308,
				location: '/?utm_source=ads&persona=finance'
			}
		);
	});

	it('redirects authenticated users to the dedicated dashboard route', async () => {
		await expectRedirectLocation(
			() =>
				load({
					url: new URL('https://example.com/?start_date=2024-01-01&end_date=2024-01-31'),
					locals: {
						safeGetSession: async () => ({ user: { id: 'user-1' } })
					}
				} as Parameters<typeof load>[0]),
			{
				status: 307,
				location: '/dashboard?start_date=2024-01-01&end_date=2024-01-31'
			}
		);
	});
});
