import { api } from '$lib/api';
import { edgeApiPath } from '$lib/edgeProxy';
import { TimeoutError } from '$lib/fetchWithTimeout';

export interface CloudConnection {
	id: string;
	provider: 'aws' | 'azure' | 'gcp' | 'saas' | 'license' | 'platform' | 'hybrid';
	aws_account_id?: string;
	azure_tenant_id?: string;
	subscription_id?: string;
	project_id?: string;
	billing_project_id?: string;
	billing_dataset?: string;
	billing_table?: string;
	name?: string;
	vendor?: string;
	is_management_account?: boolean;
	organization_id?: string;
	auth_method?: string;
	is_active?: boolean;
	status?: string;
	last_verified_at?: string | null;
	last_synced_at?: string | null;
	error_message?: string | null;
	created_at?: string | null;
}

export interface DiscoveredAccount {
	id: string;
	account_id: string;
	name: string;
	email: string;
	status: 'discovered' | 'linked';
}

interface JsonResponse {
	detail?: string;
	message?: string;
}

export interface LoadConnectionsSnapshot {
	aws: CloudConnection[];
	azure: CloudConnection[];
	gcp: CloudConnection[];
	saas: CloudConnection[];
	license: CloudConnection[];
	platform: CloudConnection[];
	hybrid: CloudConnection[];
	timedOutCount: number;
	failedCount: number;
}

interface ParsedConnectionsResponse {
	records: CloudConnection[];
	failed: boolean;
}

function buildHeaders(accessToken: string | undefined): Record<string, string> {
	return {
		'Content-Type': 'application/json',
		Authorization: `Bearer ${accessToken}`
	};
}

async function getWithTimeout(
	path: string,
	accessToken: string | undefined,
	timeoutMs: number
): Promise<Response> {
	return api.get(edgeApiPath(path), {
		headers: buildHeaders(accessToken),
		timeoutMs
	});
}

async function parseConnectionsResponse(
	response: Response | null
): Promise<ParsedConnectionsResponse> {
	if (!response?.ok) {
		return { records: [], failed: response !== null };
	}
	try {
		return { records: (await response.json()) as CloudConnection[], failed: false };
	} catch {
		return { records: [], failed: true };
	}
}

export async function loadConnectionsSnapshot(
	accessToken: string | undefined,
	timeoutMs: number
): Promise<LoadConnectionsSnapshot> {
	const results = await Promise.allSettled([
		getWithTimeout('/settings/connections/aws', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/azure', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/gcp', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/saas', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/license', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/platform', accessToken, timeoutMs),
		getWithTimeout('/settings/connections/hybrid', accessToken, timeoutMs)
	]);

	const responseOrNull = (index: number): Response | null =>
		results[index]?.status === 'fulfilled'
			? (results[index] as PromiseFulfilledResult<Response>).value
			: null;

	const parsed = await Promise.all([
		parseConnectionsResponse(responseOrNull(0)),
		parseConnectionsResponse(responseOrNull(1)),
		parseConnectionsResponse(responseOrNull(2)),
		parseConnectionsResponse(responseOrNull(3)),
		parseConnectionsResponse(responseOrNull(4)),
		parseConnectionsResponse(responseOrNull(5)),
		parseConnectionsResponse(responseOrNull(6))
	]);

	const [aws, azure, gcp, saas, license, platform, hybrid] = parsed.map((result) => result.records);

	const timedOutCount = results.filter(
		(result) => result.status === 'rejected' && result.reason instanceof TimeoutError
	).length;
	const failedCount =
		results.filter(
			(result) => result.status === 'rejected' && !(result.reason instanceof TimeoutError)
		).length + parsed.filter((result) => result.failed).length;

	return { aws, azure, gcp, saas, license, platform, hybrid, timedOutCount, failedCount };
}

export async function loadAwsDiscoveredAccounts(
	accessToken: string | undefined,
	timeoutMs: number
): Promise<DiscoveredAccount[]> {
	const response = await getWithTimeout(
		'/settings/connections/aws/discovered',
		accessToken,
		timeoutMs
	);
	if (!response.ok) {
		return [];
	}
	return (await response.json()) as DiscoveredAccount[];
}

export async function syncAwsOrg(
	accessToken: string | undefined,
	connectionId: string
): Promise<string> {
	const response = await api.post(
		edgeApiPath(`/settings/connections/aws/${connectionId}/sync-org`),
		{},
		{ headers: buildHeaders(accessToken) }
	);
	const payload = (await response.json().catch(() => ({}))) as JsonResponse;
	if (!response.ok) {
		throw new Error(payload.detail || 'Sync failed');
	}
	return payload.message || 'Organization sync started.';
}

export async function deleteConnectionApi(
	accessToken: string | undefined,
	provider: string,
	id: string
): Promise<{ status: number; detail?: string }> {
	const response = await api.delete(edgeApiPath(`/settings/connections/${provider}/${id}`), {
		headers: buildHeaders(accessToken)
	});
	const payload = (await response.json().catch(() => ({}))) as JsonResponse;
	return {
		status: response.status,
		detail: payload.detail
	};
}

export async function linkAwsDiscoveredAccount(
	accessToken: string | undefined,
	discoveredId: string
): Promise<string> {
	const response = await api.post(
		edgeApiPath(`/settings/connections/aws/discovered/${discoveredId}/link`),
		{},
		{ headers: buildHeaders(accessToken) }
	);
	const payload = (await response.json().catch(() => ({}))) as JsonResponse;
	if (!response.ok) {
		throw new Error(payload.detail || 'Linking failed');
	}
	return payload.message || 'Account linked successfully.';
}
