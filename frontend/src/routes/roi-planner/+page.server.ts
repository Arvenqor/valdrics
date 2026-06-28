import { edgeApiPath } from '$lib/edgeProxy';
import { fetchWithTimeout } from '$lib/fetchWithTimeout';
import { resolvePublicLandingCurrencyFromHeaders } from '$lib/landing/roi/geo';
import { bearerHeaders } from '$lib/http';
import type { UnitEconomicsSettings } from '../ops/opsTypes';
import type { PageServerLoad } from './$types';

const UNIT_SETTINGS_TIMEOUT_MS = 4000;

export const load: PageServerLoad = async ({ request, fetch, parent }) => {
	const { session } = await parent();
	const detectedCurrencyCode = resolvePublicLandingCurrencyFromHeaders(request.headers);

	// Pre-populate ROI planner from saved tenant KPI targets if authenticated
	let savedSettings: UnitEconomicsSettings | null = null;
	if (session?.access_token) {
		try {
			const res = await fetchWithTimeout(
				fetch,
				edgeApiPath('/costs/unit-economics/settings'),
				{
					headers: bearerHeaders(session.access_token)
				},
				UNIT_SETTINGS_TIMEOUT_MS
			);
			if (res.ok) {
				savedSettings = await res.json();
			}
		} catch {
			// Gracefully fall back to defaults; the page renders fine without saved settings
		}
	}

	return {
		detectedCurrencyCode,
		savedSettings
	};
};
