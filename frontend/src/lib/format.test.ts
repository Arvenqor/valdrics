import { describe, it, expect } from 'vitest';
import { formatUsd, formatCurrency, formatTtl } from './format';

describe('formatUsd', () => {
	it('formats integer as dollars without decimals', () => {
		expect(formatUsd(1000)).toBe('$1,000');
	});

	it('formats decimal with two places', () => {
		expect(formatUsd(1200.5)).toBe('$1,200.50');
	});

	it('formats string input', () => {
		expect(formatUsd('5000')).toBe('$5,000');
	});

	it('returns $0 for non-finite input', () => {
		expect(formatUsd(NaN)).toBe('$0');
		expect(formatUsd(Infinity)).toBe('$0');
	});

	it('handles zero', () => {
		expect(formatUsd(0)).toBe('$0');
	});

	it('handles negative values', () => {
		expect(formatUsd(-500)).toBe('-$500');
	});
});

describe('formatCurrency', () => {
	it('defaults to USD', () => {
		expect(formatCurrency(1000)).toBe('$1,000');
	});

	it('formats EUR', () => {
		expect(formatCurrency(1000, 'EUR')).toBe('€1,000');
	});

	it('formats GBP', () => {
		expect(formatCurrency(1000, 'GBP')).toBe('£1,000');
	});

	it('returns em dash for non-finite input', () => {
		expect(formatCurrency(NaN)).toBe('—');
		expect(formatCurrency(Infinity)).toBe('—');
	});

	it('handles unknown currency gracefully', () => {
		expect(() => formatCurrency(1000, 'INVALID')).not.toThrow();
	});
});

describe('formatTtl', () => {
	it('returns 0s for zero', () => {
		expect(formatTtl(0)).toBe('0s');
	});

	it('returns 0s for negative', () => {
		expect(formatTtl(-5)).toBe('0s');
	});

	it('formats sub-minute seconds', () => {
		expect(formatTtl(45)).toBe('45s');
	});

	it('formats minutes and seconds', () => {
		expect(formatTtl(75)).toBe('1m 15s');
	});

	it('formats hours', () => {
		expect(formatTtl(3661)).toBe('1h 1m 1s');
	});

	it('omits zero units', () => {
		expect(formatTtl(3600)).toBe('1h');
		expect(formatTtl(60)).toBe('1m');
		expect(formatTtl(1)).toBe('1s');
	});

	it('returns 0s for NaN', () => {
		expect(formatTtl(NaN)).toBe('0s');
	});
});
