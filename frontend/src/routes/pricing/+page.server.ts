import { edgeApiPath } from '$lib/edgeProxy';
import { fetchWithTimeout } from '$lib/fetchWithTimeout';
import { resolvePublicLandingCurrencyFromHeaders } from '$lib/landing/roi/geo';
import { DEFAULT_PRICING_PLANS, isPricingPlanArray } from './plans';
import type { PageServerLoad } from './$types';

const PRICING_REQUEST_TIMEOUT_MS = 5000;

export const load: PageServerLoad = async ({ fetch, request }) => {
	const detectedCurrencyCode = resolvePublicLandingCurrencyFromHeaders(request.headers);

	try {
		const response = await fetchWithTimeout(
			fetch,
			edgeApiPath('/billing/plans'),
			{},
			PRICING_REQUEST_TIMEOUT_MS
		);

		if (!response.ok) {
			return { plans: DEFAULT_PRICING_PLANS, detectedCurrencyCode };
		}

		const payload = await response.json();
		if (isPricingPlanArray(payload) && payload.length > 0) {
			return { plans: payload, detectedCurrencyCode };
		}
	} catch {
		return { plans: DEFAULT_PRICING_PLANS, detectedCurrencyCode };
	}

	return { plans: DEFAULT_PRICING_PLANS, detectedCurrencyCode };
};
