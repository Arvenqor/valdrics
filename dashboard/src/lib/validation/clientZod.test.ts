import { describe, expect, it } from 'vitest';

import { formatValidationIssues, isValidationError, z } from './clientZod';

describe('clientZod', () => {
	it('configures English locale for Zod Mini errors', () => {
		try {
			z.string().check(z.minLength(2)).parse('');
		} catch (error) {
			expect(isValidationError(error)).toBe(true);
			expect(formatValidationIssues(error)).toMatch(/Too small/);
		}
	});

	it('formats validation paths when requested', () => {
		const schema = z.object({
			name: z.string().check(z.minLength(2))
		});

		const result = schema.safeParse({ name: '' });
		expect(result.success).toBe(false);
		if (result.success) return;
		expect(formatValidationIssues(result.error, true)).toContain('name: Too small');
	});
});
