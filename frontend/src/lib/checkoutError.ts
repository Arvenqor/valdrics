const DEFAULT_CHECKOUT_ERROR = 'Checkout failed. Please try again or contact support.';

function stringField(value: unknown): string | null {
	return typeof value === 'string' && value.trim() ? value.trim() : null;
}

export function resolveCheckoutErrorMessage(payload: unknown): string {
	if (!payload || typeof payload !== 'object') {
		return DEFAULT_CHECKOUT_ERROR;
	}

	const record = payload as Record<string, unknown>;
	return (
		stringField(record.detail) ||
		stringField(record.message) ||
		stringField(record.error) ||
		DEFAULT_CHECKOUT_ERROR
	);
}

export async function readCheckoutErrorMessage(response: Response): Promise<string> {
	const payload = await response.json().catch(() => null);
	return resolveCheckoutErrorMessage(payload);
}
