export type PublicBuyerPersona = 'cto' | 'finops' | 'security' | 'cfo';
export type PublicBuyingMotion = 'self_serve_first' | 'enterprise_first';

const ENTERPRISE_SIGNAL_PATTERNS = Object.freeze([
	'enterprise',
	'procurement',
	'security',
	'compliance',
	'risk',
	'privacy',
	'scim',
	'private',
	'diligence',
	'executive',
	'leadership',
	'legal',
	'board',
	'abm',
	'rfp',
	'rfi'
]);

const SELF_SERVE_SIGNAL_PATTERNS = Object.freeze([
	'docs',
	'documentation',
	'resource',
	'insight',
	'guide',
	'playbook',
	'roi',
	'simulator',
	'pricing',
	'trial',
	'developer',
	'self serve',
	'self_serve'
]);

function normalizeToken(value: string | null | undefined): string {
	return (value || '').trim().toLowerCase();
}

function normalizeOptionalToken(value: string | null | undefined): string | undefined {
	const token = normalizeToken(value);
	return token || undefined;
}

function mapPersonaToken(value: string | null | undefined): PublicBuyerPersona | undefined {
	const token = normalizeToken(value);
	if (!token) {
		return undefined;
	}

	switch (token) {
		case 'cto':
		case 'engineering':
		case 'engineer':
		case 'platform':
		case 'operator':
		case 'ops':
		case 'devops':
		case 'infra':
			return 'cto';
		case 'finops':
		case 'finance':
		case 'financeops':
		case 'fpanda':
			return 'finops';
		case 'security':
		case 'compliance':
		case 'risk':
		case 'privacy':
		case 'identity':
			return 'security';
		case 'cfo':
		case 'executive':
		case 'leadership':
		case 'procurement':
		case 'board':
		case 'legal':
			return 'cfo';
		default:
			return undefined;
	}
}

function collectSignalValues(url: URL): string[] {
	return [
		url.searchParams.get('buyer'),
		url.searchParams.get('persona'),
		url.searchParams.get('entry'),
		url.searchParams.get('source'),
		url.searchParams.get('intent'),
		url.searchParams.get('utm_source'),
		url.searchParams.get('utm_medium'),
		url.searchParams.get('utm_campaign'),
		url.searchParams.get('utm_term'),
		url.searchParams.get('utm_content')
	]
		.map((value) => normalizeOptionalToken(value))
		.filter((value): value is string => Boolean(value));
}

function inferPersonaFromSignals(signalValues: string[]): PublicBuyerPersona | undefined {
	for (const signal of signalValues) {
		const directMatch = mapPersonaToken(signal);
		if (directMatch) {
			return directMatch;
		}
	}

	const joinedSignals = signalValues.join(' ');
	if (/(security|compliance|risk|privacy|identity|scim)/.test(joinedSignals)) {
		return 'security';
	}
	if (/(procurement|executive|leadership|board|legal|cfo)/.test(joinedSignals)) {
		return 'cfo';
	}
	if (/(finops|financeops|cloud cost|cost review|allocation|chargeback)/.test(joinedSignals)) {
		return 'finops';
	}
	if (/(engineering|platform|developer|docs|api|operator|workload)/.test(joinedSignals)) {
		return 'cto';
	}
	return undefined;
}

function hasAnySignal(signalValues: string[], patterns: readonly string[]): boolean {
	const joinedSignals = signalValues.join(' ');
	return patterns.some((pattern) => joinedSignals.includes(pattern));
}

export function resolvePublicBuyerPersona(url: URL): PublicBuyerPersona | undefined {
	return (
		mapPersonaToken(url.searchParams.get('buyer')) ||
		mapPersonaToken(url.searchParams.get('persona')) ||
		inferPersonaFromSignals(collectSignalValues(url))
	);
}

export function resolvePublicBuyingMotion(
	url: URL,
	defaultMotion: PublicBuyingMotion = 'self_serve_first'
): PublicBuyingMotion {
	const signalValues = collectSignalValues(url);
	const persona = resolvePublicBuyerPersona(url);

	if (persona === 'security' || persona === 'cfo') {
		return 'enterprise_first';
	}
	if (persona === 'cto' || persona === 'finops') {
		return 'self_serve_first';
	}
	if (hasAnySignal(signalValues, ENTERPRISE_SIGNAL_PATTERNS)) {
		return 'enterprise_first';
	}
	if (hasAnySignal(signalValues, SELF_SERVE_SIGNAL_PATTERNS)) {
		return 'self_serve_first';
	}
	return defaultMotion;
}
