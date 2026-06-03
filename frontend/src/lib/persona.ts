export type Persona = 'engineering' | 'finance' | 'platform' | 'leadership';

export function normalizePersona(value: unknown): Persona {
	const normalized = String(value || '')
		.toLowerCase()
		.trim();
	if (normalized === 'finance') return 'finance';
	if (normalized === 'platform') return 'platform';
	if (normalized === 'leadership') return 'leadership';
	return 'engineering';
}

export function isAdminRole(role: unknown): boolean {
	const normalized = String(role || '')
		.toLowerCase()
		.trim();
	return normalized === 'admin' || normalized === 'owner';
}

export function allowedNavHrefs(
	persona: unknown,
	role: unknown,
	options: { platformOperator?: boolean } = {}
): Set<string> {
	const p = normalizePersona(persona);
	const isAdmin = isAdminRole(role);
	const platformOperator = Boolean(options.platformOperator);

	let hrefs: string[];
	switch (p) {
		case 'finance':
			hrefs = [
				'/dashboard',
				'/leaderboards',
				'/savings',
				'/approvals',
				'/billing',
				'/connections',
				'/inventory',
				'/greenops',
				'/audit'
			];
			break;
		case 'platform':
			hrefs = ['/ops', '/approvals', '/connections', '/inventory', '/audit'];
			if (platformOperator) {
				hrefs.push('/admin/health');
			}
			break;
		case 'leadership':
			hrefs = [
				'/dashboard',
				'/leaderboards',
				'/savings',
				'/approvals',
				'/inventory',
				'/greenops',
				'/audit'
			];
			break;
		case 'engineering':
		default:
			hrefs = [
				'/dashboard',
				'/ops',
				'/approvals',
				'/connections',
				'/inventory',
				'/greenops',
				'/llm',
				'/audit'
			];
			break;
	}

	// Safety: core setup and planning paths should always be discoverable.
	hrefs.push('/settings', '/onboarding', '/roi-planner');

	// Subscription management is an admin concern, regardless of persona.
	if (isAdmin) {
		hrefs.push('/billing', '/admin/landing-campaigns');
		if (platformOperator) {
			hrefs.push('/admin/health');
		}
	}

	// Hide admin-only routes unless admin/owner.
	if (!isAdmin) {
		hrefs = hrefs.filter((href) => href !== '/admin/health' && href !== '/admin/landing-campaigns');
	}

	return new Set(hrefs);
}
