import { api } from '$lib/api';
import { edgeApiPath } from '$lib/edgeProxy';
import type { InventoryListResponse, InventoryQuery } from './inventoryTypes';

interface ApiErrorPayload {
	detail?: string;
	message?: string;
	error?: string | { message?: string };
}

function buildHeaders(accessToken: string | undefined): Record<string, string> {
	return {
		Authorization: `Bearer ${accessToken}`
	};
}

function buildInventoryParams(query: InventoryQuery): URLSearchParams {
	const params = new URLSearchParams();
	params.set('type', query.type);
	params.set('status', query.status);
	params.set('page', String(query.page));
	params.set('per_page', String(query.perPage));
	if (query.search.trim()) {
		params.set('q', query.search.trim());
	}
	return params;
}

function extractErrorMessage(payload: ApiErrorPayload, fallback: string): string {
	if (payload.detail) return payload.detail;
	if (payload.message) return payload.message;
	if (typeof payload.error === 'string') return payload.error;
	if (typeof payload.error?.message === 'string') return payload.error.message;
	return fallback;
}

export async function loadInventorySnapshot(
	accessToken: string | undefined,
	query: InventoryQuery,
	timeoutMs: number
): Promise<InventoryListResponse> {
	const params = buildInventoryParams(query);
	const response = await api.get(edgeApiPath(`/inventory?${params.toString()}`), {
		headers: buildHeaders(accessToken),
		timeoutMs
	});
	if (!response.ok) {
		const payload = (await response.json().catch(() => ({}))) as ApiErrorPayload;
		throw new Error(extractErrorMessage(payload, 'Failed to load asset inventory.'));
	}
	return (await response.json()) as InventoryListResponse;
}
