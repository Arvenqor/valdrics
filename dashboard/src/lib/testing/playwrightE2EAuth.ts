import { createHmac } from 'node:crypto';

export interface PlaywrightE2EFixture {
	tenantId: string;
	tenantName: string;
	userId: string;
	userName: string;
	email: string;
	role: string;
	persona: string;
	tier: string;
}

export const DEFAULT_PLAYWRIGHT_E2E_FIXTURE: PlaywrightE2EFixture = {
	tenantId: '11111111-1111-4111-8111-111111111111',
	tenantName: 'Playwright Test Tenant',
	userId: '22222222-2222-4222-8222-222222222222',
	userName: 'E2E Test User',
	email: 'e2e@valdrics.test',
	role: 'admin',
	persona: 'engineering',
	tier: 'growth'
};

function resolveValue(value: string | undefined, fallback: string): string {
	const normalized = String(value || '').trim();
	return normalized.length > 0 ? normalized : fallback;
}

export function resolvePlaywrightE2EFixture(
	values: Partial<Record<keyof PlaywrightE2EFixture, string | undefined>> = {}
): PlaywrightE2EFixture {
	return {
		tenantId: resolveValue(
			values.tenantId ?? process.env.PLAYWRIGHT_E2E_TENANT_ID,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.tenantId
		),
		tenantName: resolveValue(
			values.tenantName ?? process.env.PLAYWRIGHT_E2E_TENANT_NAME,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.tenantName
		),
		userId: resolveValue(
			values.userId ?? process.env.PLAYWRIGHT_E2E_USER_ID,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.userId
		),
		userName: resolveValue(
			values.userName ?? process.env.PLAYWRIGHT_E2E_USER_NAME,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.userName
		),
		email: resolveValue(
			values.email ?? process.env.PLAYWRIGHT_E2E_USER_EMAIL,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.email
		),
		role: resolveValue(
			values.role ?? process.env.PLAYWRIGHT_E2E_USER_ROLE,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.role
		),
		persona: resolveValue(
			values.persona ?? process.env.PLAYWRIGHT_E2E_USER_PERSONA,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.persona
		),
		tier: resolveValue(
			values.tier ?? process.env.PLAYWRIGHT_E2E_TIER,
			DEFAULT_PLAYWRIGHT_E2E_FIXTURE.tier
		)
	};
}

function encodeSegment(value: Record<string, unknown>): string {
	return Buffer.from(JSON.stringify(value)).toString('base64url');
}

export function createPlaywrightE2EAccessToken(params: {
	secret: string;
	fixture?: PlaywrightE2EFixture;
	issuer?: string;
	nowMs?: number;
	lifetimeSeconds?: number;
}): string {
	const secret = String(params.secret || '').trim();
	if (!secret) {
		throw new Error('SUPABASE_JWT_SECRET is required for Playwright E2E access tokens.');
	}

	const fixture = params.fixture ?? resolvePlaywrightE2EFixture();
	const issuer = resolveValue(params.issuer, 'supabase');
	const issuedAt = Math.floor((params.nowMs ?? Date.now()) / 1000);
	const lifetimeSeconds = Math.max(60, Math.floor(params.lifetimeSeconds ?? 3600));
	const header = { alg: 'HS256', typ: 'JWT' };
	const payload = {
		aud: 'authenticated',
		iss: issuer,
		sub: fixture.userId,
		email: fixture.email,
		role: 'authenticated',
		iat: issuedAt,
		exp: issuedAt + lifetimeSeconds
	};

	const encodedHeader = encodeSegment(header);
	const encodedPayload = encodeSegment(payload);
	const signingInput = `${encodedHeader}.${encodedPayload}`;
	const signature = createHmac('sha256', secret).update(signingInput).digest('base64url');

	return `${signingInput}.${signature}`;
}
