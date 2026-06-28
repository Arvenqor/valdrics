import {
	resolvePublicBuyerPersona,
	resolvePublicBuyingMotion,
	type PublicBuyerPersona,
	type PublicBuyingMotion
} from './publicBuyerSignals';
import { buildPublicAuthHref } from './publicAppOrigin';

export { resolvePublicBuyerPersona, resolvePublicBuyingMotion } from './publicBuyerSignals';

interface PublicPathOptions {
	entry: string;
	source?: string;
	persona?: PublicBuyerPersona;
	extraParams?: Record<string, string | undefined>;
}

interface PublicSignupHrefOptions extends PublicPathOptions {
	intent?: string;
	mode?: 'login' | 'signup';
}

interface PublicSalesHrefOptions extends PublicPathOptions {
	intent?: string;
}

const UTM_QUERY_KEYS = Object.freeze([
	'utm_source',
	'utm_medium',
	'utm_campaign',
	'utm_term',
	'utm_content'
]);

function normalizeToken(value: string | null | undefined): string {
	return (value || '').trim().toLowerCase();
}

function normalizeOptionalToken(value: string | null | undefined): string | undefined {
	const token = normalizeToken(value);
	return token || undefined;
}

function setParams(
	params: URLSearchParams,
	values: Record<string, string | undefined>,
	overwriteExisting = false
): void {
	for (const [key, value] of Object.entries(values)) {
		if (!value) {
			continue;
		}
		if (!overwriteExisting && params.has(key)) {
			continue;
		}
		params.set(key, value);
	}
}

function preserveUtmParams(params: URLSearchParams, currentUrl: URL): void {
	for (const key of UTM_QUERY_KEYS) {
		if (params.has(key)) {
			continue;
		}
		const value = normalizeOptionalToken(currentUrl.searchParams.get(key));
		if (value) {
			params.set(key, value);
		}
	}
}

export function appendPublicAttribution(
	href: string,
	currentUrl: URL,
	options: PublicPathOptions
): string {
	if (/^(https?:|mailto:)/i.test(href)) {
		return href;
	}

	const parsed = new URL(href, currentUrl.origin);
	const persona = options.persona || resolvePublicBuyerPersona(currentUrl);

	setParams(parsed.searchParams, {
		entry: options.entry,
		source: options.source || options.entry,
		persona,
		...(options.extraParams || {})
	});
	preserveUtmParams(parsed.searchParams, currentUrl);

	return `${parsed.pathname}${parsed.search}${parsed.hash}`;
}

export function buildPublicSignupHref(
	basePath: string,
	currentUrl: URL,
	options: PublicSignupHrefOptions
): string {
	const relativeHref = appendPublicAttribution(`${basePath}/auth/login`, currentUrl, {
		entry: options.entry,
		source: options.source,
		persona: options.persona,
		extraParams: {
			mode: options.mode || 'signup',
			intent: options.intent,
			...(options.extraParams || {})
		}
	});
	return buildPublicAuthHref(relativeHref, currentUrl);
}

export function buildPublicEnterpriseHref(
	basePath: string,
	currentUrl: URL,
	options: PublicPathOptions
): string {
	return appendPublicAttribution(`${basePath}/enterprise`, currentUrl, options);
}

export function buildPublicSalesHref(
	basePath: string,
	currentUrl: URL,
	options: PublicSalesHrefOptions
): string {
	return appendPublicAttribution(`${basePath}/talk-to-sales`, currentUrl, {
		entry: options.entry,
		source: options.source,
		persona: options.persona,
		extraParams: {
			intent: options.intent,
			...(options.extraParams || {})
		}
	});
}
