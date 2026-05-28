const DEFAULT_PRODUCTION_APP_ORIGIN = 'https://app.valdrics.com';
const PUBLIC_MARKETING_HOSTS = new Set(['valdrics.com', 'www.valdrics.com']);

function normalizePath(path: string): string {
	return path.startsWith('/') ? path : `/${path}`;
}

export function resolvePublicAppOrigin(currentUrl: URL): string | null {
	const hostname = currentUrl.hostname.toLowerCase();
	if (PUBLIC_MARKETING_HOSTS.has(hostname)) {
		return DEFAULT_PRODUCTION_APP_ORIGIN;
	}

	return null;
}

export function buildPublicAuthHref(path: string, currentUrl: URL): string {
	const normalizedPath = normalizePath(path);
	const appOrigin = resolvePublicAppOrigin(currentUrl);
	return appOrigin ? `${appOrigin}${normalizedPath}` : normalizedPath;
}
