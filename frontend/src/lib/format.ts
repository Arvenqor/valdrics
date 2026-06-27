/**
 * Shared formatting utilities for currency, dates, and duration display.
 */

/**
 * Format a numeric value as US dollars.
 *
 * Falls back to `$0` when the input is not a finite number.
 * Omits decimal places for whole-dollar amounts.
 */
export function formatUsd(value: number | string): string {
	const amount = Number(value);
	if (!Number.isFinite(amount)) return '$0';
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		maximumFractionDigits: Number.isInteger(amount) ? 0 : 2
	}).format(amount);
}

/**
 * Format a compact USD value: omit decimals for amounts ≥ 1000.
 */
export function formatCompactUsd(value: number): string {
	if (!Number.isFinite(value)) return '$0';
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD',
		maximumFractionDigits: value >= 1000 ? 0 : 2
	}).format(value);
}

/**
 * Format a numeric value in an arbitrary currency.
 *
 * @param amount - The numeric amount to format.
 * @param currencyCode - ISO 4217 currency code (e.g. `'EUR'`, `'GBP'`).
 * @returns A locale-aware currency string, or `'—'` on non-finite input.
 */
export function formatCurrency(amount: number, currencyCode: string = 'USD'): string {
	if (!Number.isFinite(amount)) return '—';
	try {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: currencyCode,
			maximumFractionDigits: Number.isInteger(amount) ? 0 : 2
		}).format(amount);
	} catch {
		return new Intl.NumberFormat('en-US', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: Number.isInteger(amount) ? 0 : 2
		}).format(amount);
	}
}

/**
 * Format a duration in seconds to a compact human-readable string.
 *
 * Examples: `45s`, `1m 30s`, `2h 15m`, `1h 5s`.
 */
export function formatTtl(seconds: number): string {
	if (!Number.isFinite(seconds) || seconds <= 0) return '0s';
	if (seconds < 60) return `${seconds}s`;
	const hours = Math.floor(seconds / 3600);
	const minutes = Math.floor((seconds % 3600) / 60);
	const remainingSeconds = seconds % 60;
	const parts: string[] = [];
	if (hours > 0) parts.push(`${hours}h`);
	if (minutes > 0) parts.push(`${minutes}m`);
	if (remainingSeconds > 0) parts.push(`${remainingSeconds}s`);
	return parts.join(' ');
}

/**
 * Format a duration in seconds to a human-readable string.
 *
 * @param seconds - Duration in seconds, or null/NaN for unknown.
 * @returns Formatted string like `1m 30s`, `2h 15m`, or `-` for unknown.
 */
export function formatDuration(seconds: number | null): string {
	if (seconds === null || Number.isNaN(seconds)) return '-';
	if (seconds < 60) return `${Math.round(seconds)}s`;
	const minutes = Math.floor(seconds / 60);
	const remainder = Math.round(seconds % 60);
	if (minutes < 60) return `${minutes}m ${remainder}s`;
	const hours = Math.floor(minutes / 60);
	const mins = minutes % 60;
	return `${hours}h ${mins}m`;
}

/**
 * Format a date string to a localized representation.
 *
 * @param value - ISO date string, or null/undefined for unknown.
 * @param fallback - Text to show when value is missing or unparseable. Defaults to `'-'`.
 * @returns Localized date string, or the fallback.
 */
export function formatDate(value: string | null | undefined, fallback = '-'): string {
	if (!value) return fallback;
	const date = new Date(value);
	if (Number.isNaN(date.getTime())) return fallback;
	return date.toLocaleString();
}

/**
 * Format a number with controlled decimal places.
 *
 * @param value - The number to format.
 * @param fractionDigits - Maximum fraction digits. Defaults to 2.
 * @returns Localized number string, or `'0'` for non-finite input.
 */
export function formatNumber(value: number, fractionDigits = 2): string {
	return new Intl.NumberFormat('en-US', {
		maximumFractionDigits: fractionDigits
	}).format(Number.isFinite(value) ? value : 0);
}
