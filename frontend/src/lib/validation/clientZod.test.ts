import { describe, expect, it } from 'vitest';

import { formatValidationIssues, isValidationError, z } from './clientZod';

describe('clientZod', () => {
	it('recognizes Zod Mini validation errors', () => {
		try {
			z.string().check(z.minLength(2)).parse('');
		} catch (error) {
			expect(isValidationError(error)).toBe(true);
			if (!isValidationError(error)) return;
			const firstIssue = error.issues[0];
			expect(firstIssue).toBeDefined();
			if (!firstIssue || typeof firstIssue.message !== 'string') return;
			expect(firstIssue.path).toEqual([]);
			expect(typeof firstIssue.message).toBe('string');
			expect(firstIssue.message.length).toBeGreaterThan(0);
		}
	});

	it('formats validation paths when includePath is true', () => {
		const schema = z.object({
			name: z.string().check(z.minLength(2))
		});

		const result = schema.safeParse({ name: '' });
		expect(result.success).toBe(false);
		if (result.success) return;
		expect(result.error.issues[0].path).toEqual(['name']);
		const formatted = formatValidationIssues(result.error, true);
		expect(formatted).toContain('name:');
		expect(formatted.length).toBeGreaterThan(5);
	});
});
