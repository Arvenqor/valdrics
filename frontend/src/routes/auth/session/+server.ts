import { json, type RequestHandler } from '@sveltejs/kit';

const NO_STORE_HEADERS = {
	'cache-control': 'no-store',
	'content-type': 'application/json'
};

export const GET: RequestHandler = async ({ locals }) => {
	const { session } = await locals.safeGetSession();
	if (!session?.access_token) {
		return json({ accessToken: null, tenantId: null }, { status: 401, headers: NO_STORE_HEADERS });
	}

	const tenantId =
		typeof session.user?.user_metadata?.tenant_id === 'string'
			? session.user.user_metadata.tenant_id
			: null;

	return json({ accessToken: session.access_token, tenantId }, { headers: NO_STORE_HEADERS });
};
