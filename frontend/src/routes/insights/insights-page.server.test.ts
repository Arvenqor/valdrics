import { describe, expect, it } from 'vitest';
import { load } from './+page.server';

describe('insights redirect route', () => {
	it('redirects insights visitors to resources without losing query params', () => {
		try {
			load({
				url: new URL('https://example.com/insights?topic=finops')
			} as Parameters<typeof load>[0]);
			throw new Error('expected redirect to be thrown');
		} catch (error) {
			expect(error).toMatchObject({
				status: 308,
				location: '/resources?topic=finops'
			});
		}
	});
});
