import { describe, it, expect } from 'vitest';
import { bearerHeaders, withBearerAuth, extractApiErrorMessage } from './http';

describe('bearerHeaders', () => {
	it('returns Authorization header for a valid token', () => {
		expect(bearerHeaders('abc123')).toEqual({ Authorization: 'Bearer abc123' });
	});

	it('returns empty object for undefined', () => {
		expect(bearerHeaders(undefined)).toEqual({});
	});

	it('returns empty object for null', () => {
		expect(bearerHeaders(null)).toEqual({});
	});

	it('returns empty object for empty string', () => {
		expect(bearerHeaders('')).toEqual({});
	});
});

describe('withBearerAuth', () => {
	it('merges bearer auth with extra headers', () => {
		expect(withBearerAuth('token', { 'X-Id': '1' })).toEqual({
			Authorization: 'Bearer token',
			'X-Id': '1'
		});
	});

	it('returns only extra headers when token is missing', () => {
		expect(withBearerAuth(undefined, { 'X-Id': '1' })).toEqual({ 'X-Id': '1' });
	});

	it('returns only bearer headers when no extras', () => {
		expect(withBearerAuth('token')).toEqual({ Authorization: 'Bearer token' });
	});

	it('extra headers override bearer headers if same key', () => {
		expect(withBearerAuth('token', { Authorization: 'Basic xyz' })).toEqual({
			Authorization: 'Basic xyz'
		});
	});
});

describe('extractApiErrorMessage', () => {
	it('returns fallback for null', () => {
		expect(extractApiErrorMessage(null, 'fallback')).toBe('fallback');
	});

	it('returns fallback for non-object', () => {
		expect(extractApiErrorMessage('string', 'fallback')).toBe('fallback');
	});

	it('extracts detail string', () => {
		expect(extractApiErrorMessage({ detail: 'Not found' }, 'fallback')).toBe('Not found');
	});

	it('extracts detail with leading/trailing whitespace', () => {
		expect(extractApiErrorMessage({ detail: '  spaced  ' }, 'fallback')).toBe('spaced');
	});

	it('returns fallback for empty detail string', () => {
		expect(extractApiErrorMessage({ detail: '   ' }, 'fallback')).toBe('fallback');
	});

	it('extracts message string', () => {
		expect(extractApiErrorMessage({ message: 'Bad request' }, 'fallback')).toBe('Bad request');
	});

	it('extracts error string when no detail or message', () => {
		expect(extractApiErrorMessage({ error: 'Server error' }, 'fallback')).toBe('Server error');
	});

	it('prefers detail over message over error', () => {
		expect(extractApiErrorMessage({ detail: 'd', message: 'm', error: 'e' }, 'fallback')).toBe('d');
	});

	it('prefers message over error when detail is missing', () => {
		expect(extractApiErrorMessage({ message: 'm', error: 'e' }, 'fallback')).toBe('m');
	});

	it('joins array detail entries', () => {
		expect(
			extractApiErrorMessage({ detail: [{ msg: 'first' }, { msg: 'second' }] }, 'fallback')
		).toBe('first, second');
	});

	it('joins array detail entries using message field', () => {
		expect(
			extractApiErrorMessage({ detail: [{ message: 'first' }, { message: 'second' }] }, 'fallback')
		).toBe('first, second');
	});

	it('skips non-object entries in detail array', () => {
		expect(extractApiErrorMessage({ detail: ['string', null, { msg: 'ok' }] }, 'fallback')).toBe(
			'ok'
		);
	});

	it('returns fallback for empty detail array', () => {
		expect(extractApiErrorMessage({ detail: [] }, 'fallback')).toBe('fallback');
	});

	it('returns fallback when no recognised fields exist', () => {
		expect(extractApiErrorMessage({ other: 'value' }, 'fallback')).toBe('fallback');
	});
});
