/**
 * Shared HTTP utilities for authenticated requests and error extraction.
 */

/**
 * Build a standard Bearer auth header object.
 *
 * Returns an empty object when `accessToken` is missing, undefined, null, or empty
 * so callers can spread the result unconditionally:
 *
 * @example
 * const headers = { ...bearerHeaders(token), 'Content-Type': 'application/json' };
 */
export function bearerHeaders(accessToken?: string | null): Record<string, string> {
	if (!accessToken) return {};
	return { Authorization: `Bearer ${accessToken}` };
}

/**
 * Merge Bearer auth headers with additional headers.
 *
 * @example
 * const headers = withBearerAuth(token, { 'X-Request-Id': 'abc' });
 */
export function withBearerAuth(
	accessToken: string | null | undefined,
	extra?: Record<string, string>
): Record<string, string> {
	return { ...bearerHeaders(accessToken), ...extra };
}

/**
 * Extract a human-readable error message from an unknown API error payload.
 *
 * Handles:
 * - `{ detail: string }`
 * - `{ detail: Array<{ msg?: string; message?: string }> }`
 * - `{ message: string }`
 * - `{ error: string }`
 */
export function extractApiErrorMessage(data: unknown, fallback: string): string {
	if (!data || typeof data !== 'object') return fallback;
	const payload = data as Record<string, unknown>;
	const detail = payload.detail;
	if (typeof detail === 'string' && detail.trim()) return detail.trim();
	if (Array.isArray(detail)) {
		const parts = detail
			.map((entry) => {
				if (!entry || typeof entry !== 'object') return '';
				const obj = entry as Record<string, unknown>;
				if (typeof obj.msg === 'string') return obj.msg.trim();
				if (typeof obj.message === 'string') return obj.message.trim();
				return '';
			})
			.filter(Boolean);
		if (parts.length) return parts.join(', ');
	}
	const message = payload.message;
	if (typeof message === 'string' && message.trim()) return message.trim();
	const error = payload.error;
	if (typeof error === 'string' && error.trim()) return error.trim();
	return fallback;
}
