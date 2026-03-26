import type { LandingUtmParams } from './landingFunnel';

type LandingPublicPathOptions = {
	path: string;
	source: string;
	persona: string;
	utm: LandingUtmParams;
	extraParams?: Record<string, string | undefined>;
};

function appendUtmParams(params: URLSearchParams, utm: LandingUtmParams): void {
	if (utm.source) params.set('utm_source', utm.source);
	if (utm.medium) params.set('utm_medium', utm.medium);
	if (utm.campaign) params.set('utm_campaign', utm.campaign);
	if (utm.term) params.set('utm_term', utm.term);
	if (utm.content) params.set('utm_content', utm.content);
}

export function buildLandingPublicPath(options: LandingPublicPathOptions): string {
	const parsed = new URL(options.path, 'https://valdrics.local');
	const params = parsed.searchParams;

	if (!params.has('entry')) {
		params.set('entry', 'landing');
	}
	if (!params.has('source')) {
		params.set('source', options.source);
	}
	if (!params.has('persona')) {
		params.set('persona', options.persona);
	}

	for (const [key, value] of Object.entries(options.extraParams || {})) {
		if (!value || params.has(key)) {
			continue;
		}
		params.set(key, value);
	}

	appendUtmParams(params, options.utm);
	return `${parsed.pathname}${parsed.search}${parsed.hash}`;
}
