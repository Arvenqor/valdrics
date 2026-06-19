import { expect, test } from '@playwright/test';

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:4173';
const LOCAL_DASHBOARD_HOSTS = new Set(['localhost', '127.0.0.1', '::1']);
const isLocalDashboardUrl = LOCAL_DASHBOARD_HOSTS.has(new URL(BASE_URL).hostname);
const TRANSIENT_NAVIGATION_ERROR =
	/ERR_SSL_BAD_RECORD_MAC_ALERT|ERR_HTTP2_PROTOCOL_ERROR|ERR_NETWORK_CHANGED|ERR_CONNECTION_RESET|ERR_CONNECTION_CLOSED/i;

test.setTimeout(120_000);

type PublicPage = Parameters<typeof test>[0]['page'];
type PublicGotoOptions = Parameters<PublicPage['goto']>[1];

async function gotoPublic(page: PublicPage, url: string, options?: PublicGotoOptions) {
	for (let attempt = 0; attempt < 3; attempt += 1) {
		try {
			return await page.goto(url, options);
		} catch (error) {
			if (!TRANSIENT_NAVIGATION_ERROR.test(String(error)) || attempt === 2) {
				throw error;
			}
			await page.waitForTimeout(500 * (attempt + 1));
		}
	}
}

async function installTurnstileStub(page: PublicPage) {
	await page.addInitScript(() => {
		type TurnstileStub = {
			render: (
				container: string | HTMLElement,
				options: { callback?: (token: string) => void }
			) => string;
			execute: () => void;
			reset: () => void;
			remove: () => void;
		};

		const testWindow = window as Window & {
			__VALDRICS_TURNSTILE_SITE_KEY__?: string;
			turnstile?: TurnstileStub;
		};
		let tokenCallback: ((token: string) => void) | undefined;

		testWindow.__VALDRICS_TURNSTILE_SITE_KEY__ = 'e2e-turnstile-site-key';
		testWindow.turnstile = {
			render: (_container, options) => {
				tokenCallback = options.callback;
				return 'e2e-turnstile-widget';
			},
			execute: () => {
				window.setTimeout(() => tokenCallback?.('e2e-turnstile-token'), 0);
			},
			reset: () => undefined,
			remove: () => undefined
		};
	});
}

async function waitForPublicHydration(page: PublicPage) {
	await expect(page.locator('.public-site-shell[data-public-hydrated="true"]')).toBeVisible();
}

async function attachSecurityGuards(page: PublicPage) {
	await page.addInitScript(() => {
		const isKnownPassiveCspReport = (event: SecurityPolicyViolationEvent) => {
			const directive = event.effectiveDirective || event.violatedDirective;
			const blockedURI = event.blockedURI || '';
			let blockedUrl: URL;
			try {
				blockedUrl = new URL(blockedURI, window.location.href);
			} catch {
				return false;
			}

			if (
				directive === 'script-src-elem' &&
				blockedUrl.origin === window.location.origin &&
				blockedUrl.pathname.startsWith('/_app/immutable/')
			) {
				return true;
			}

			if (
				directive === 'script-src-elem' &&
				blockedUrl.origin === window.location.origin &&
				blockedUrl.pathname.startsWith('/cdn-cgi/scripts/')
			) {
				return true;
			}

			if (
				directive === 'connect-src' &&
				blockedUrl.origin === window.location.origin &&
				blockedUrl.pathname === '/cdn-cgi/rum'
			) {
				return true;
			}

			return (
				directive === 'script-src-elem' &&
				blockedUrl.origin === 'https://static.cloudflareinsights.com' &&
				blockedUrl.pathname.startsWith('/beacon.min.js')
			);
		};

		(
			window as Window & {
				__valdricsSecurityPolicyViolations?: { directive: string; blockedURI: string }[];
			}
		).__valdricsSecurityPolicyViolations = [];
		window.addEventListener('securitypolicyviolation', (event) => {
			if (isKnownPassiveCspReport(event)) return;
			(
				window as Window & {
					__valdricsSecurityPolicyViolations?: { directive: string; blockedURI: string }[];
				}
			).__valdricsSecurityPolicyViolations?.push({
				directive: event.effectiveDirective || event.violatedDirective,
				blockedURI: event.blockedURI
			});
		});
	});

	const consoleErrors: string[] = [];
	const knownPassiveCspConsolePattern =
		/(_app\/immutable\/|\/cdn-cgi\/scripts\/|\/cdn-cgi\/rum\?|static\.cloudflareinsights\.com\/beacon\.min\.js)/i;
	page.on('console', (message) => {
		if (message.type() !== 'error') return;
		if (knownPassiveCspConsolePattern.test(message.text())) return;
		if (
			/content security policy|securitypolicyviolation|refused to apply inline/i.test(
				message.text()
			)
		) {
			consoleErrors.push(message.text());
		}
	});

	return {
		async assertClean() {
			const securityPolicyViolations = await page.evaluate(() => {
				return (
					(
						window as Window & {
							__valdricsSecurityPolicyViolations?: { directive: string; blockedURI: string }[];
						}
					).__valdricsSecurityPolicyViolations ?? []
				);
			});
			expect(securityPolicyViolations).toEqual([]);
			expect(consoleErrors).toEqual([]);
		}
	};
}

async function assertPublicRoute(page: PublicPage, path: string, heading: RegExp) {
	await gotoPublic(page, `${BASE_URL}${path}`);
	await expect(page).toHaveURL(new RegExp(`${path.replace('/', '\\/')}(\\?.*)?$`));
	await expect(page.getByRole('heading', { level: 1, name: heading })).toBeVisible();
}

async function assertHashDestination(page: PublicPage, hash: string, selector: string) {
	await expect
		.poll(() => new URL(page.url()).hash, { message: `expected URL hash ${hash}` })
		.toBe(hash);
	await expect(page.locator(selector)).toBeVisible();
}

async function assertDownloadEndpoint(
	page: PublicPage,
	path: string,
	expectedContentType?: RegExp
) {
	const response = await page.request.get(new URL(path, BASE_URL).toString());
	expect(response.ok()).toBeTruthy();
	if (expectedContentType) {
		expect(response.headers()['content-type'] || '').toMatch(expectedContentType);
	}
}

async function goToLanding(page: PublicPage) {
	await gotoPublic(page, BASE_URL, { waitUntil: 'domcontentloaded' });
	await expect(page.locator('#hero')).toBeVisible();
	await waitForPublicHydration(page);
}

async function openMobileMenu(page: PublicPage) {
	const menu = page.locator('#public-mobile-menu');
	const toggle = page.getByRole('button', { name: /toggle menu/i });
	await expect(toggle).toBeVisible();
	if (await menu.isVisible().catch(() => false)) {
		return menu;
	}
	await toggle.click();
	await expect(menu).toBeVisible();
	return menu;
}

test.describe('Public marketing smoke (desktop)', () => {
	test('emits canonical and robots metadata for public and auth routes', async ({ page }) => {
		const security = await attachSecurityGuards(page);
		await gotoPublic(page, BASE_URL, { waitUntil: 'domcontentloaded' });
		await waitForPublicHydration(page);
		await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', `${BASE_URL}/`);
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'index,follow');

		await gotoPublic(page, `${BASE_URL}/pricing`, { waitUntil: 'domcontentloaded' });
		await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
			'href',
			`${BASE_URL}/pricing`
		);
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'index,follow');

		await gotoPublic(page, `${BASE_URL}/auth/login`, { waitUntil: 'domcontentloaded' });
		await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
			'content',
			'noindex,nofollow'
		);
		await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
			'href',
			`${BASE_URL}/auth/login`
		);

		for (const routeCase of [
			{
				path: '/status',
				title: /System Status \| Valdrics/i,
				description: /current service status for valdrics core platform dependencies/i
			},
			{
				path: '/privacy',
				title: /Privacy Policy \| Valdrics/i,
				description: /privacy policy covering processing scope, retention, security controls/i
			},
			{
				path: '/terms',
				title: /Terms of Service \| Valdrics/i,
				description: /terms of service covering account responsibilities, billing, acceptable use/i
			}
		]) {
			await gotoPublic(page, `${BASE_URL}${routeCase.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.locator('link[rel="canonical"]')).toHaveAttribute(
				'href',
				`${BASE_URL}${routeCase.path}`
			);
			await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'index,follow');
			await expect(page).toHaveTitle(routeCase.title);
			await expect(page.locator('meta[name="description"]')).toHaveAttribute(
				'content',
				routeCase.description
			);
			await expect(page.locator('script[type="application/ld+json"]').first()).toBeAttached();
		}

		await security.assertClean();
	});

	test('covers landing, pricing, docs, api docs, and status navigation', async ({
		page
	}, testInfo) => {
		await goToLanding(page);

		const landingHeading = page.getByRole('heading', { level: 1 }).first();
		await expect(landingHeading).toBeVisible();
		await expect(landingHeading).toContainText(
			/control|cleaner|path|reports|context|margin|govern|optimize/i
		);
		await expect(page.locator('#product')).toBeVisible();
		await expect(page.locator('#simulator')).toBeVisible();
		await expect(page.locator('#plans')).toBeVisible();
		await expect(page.locator('[aria-label="Why teams choose Valdrics"]')).toBeVisible();

		const primaryCta = page.getByRole('link', { name: /start free/i }).first();
		await expect(primaryCta).toHaveAttribute('href', /\/auth\/login(\?.*)?$/);

		await page
			.locator('#trust')
			.getByRole('link', { name: /technical validation/i })
			.click();
		await expect(page).toHaveURL(/\/docs(\?.*)?$/);
		await expect(page.getByRole('heading', { level: 1, name: /documentation/i })).toBeVisible();

		const apiDocsHref = await page
			.getByRole('link', { name: /open api docs/i })
			.first()
			.getAttribute('href');
		expect(apiDocsHref || '').toMatch(/\/docs\/api(\?.*)?$/);
		if (apiDocsHref) {
			await gotoPublic(page, new URL(apiDocsHref, BASE_URL).toString(), {
				waitUntil: 'domcontentloaded'
			});
		}
		await expect(page).toHaveURL(/\/docs\/api(\?.*)?$/);
		await expect(page.getByRole('heading', { level: 1, name: /api reference/i })).toBeVisible();

		await goToLanding(page);
		await page
			.locator('#trust')
			.getByRole('link', { name: /status page/i })
			.click();
		await expect(page).toHaveURL(/\/status(\?.*)?$/);
		await expect(page.getByRole('heading', { level: 1, name: /system status/i })).toBeVisible();

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await page.waitForLoadState('networkidle');
		await expect(
			page.getByRole('heading', { level: 1, name: /pricing that stays simple/i })
		).toBeVisible();
		const switchButton = page.getByRole('switch', { name: /toggle billing cycle/i });
		await switchButton.scrollIntoViewIfNeeded();
		await expect(switchButton).toHaveAttribute('aria-checked', 'false');
		await switchButton.click();
		await expect(switchButton).toHaveAttribute('aria-checked', 'true');
		await page.screenshot({
			path: testInfo.outputPath('desktop-public-smoke.png'),
			fullPage: true
		});
	});

	test('keeps landing navigation and CTAs on working destinations', async ({ page }) => {
		const security = await attachSecurityGuards(page);

		// Test header navigation on pricing page where it is rendered
		await gotoPublic(page, `${BASE_URL}/pricing`);
		await page.waitForLoadState('networkidle');
		const header = page.locator('.public-site-header');

		await header.getByRole('link', { name: /^product$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/#product'));
		await expect(page.locator('#product')).toBeVisible();

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await header.getByRole('link', { name: /^pricing$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/pricing'));

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await header.getByRole('link', { name: /^enterprise$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/enterprise'));

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await header.getByRole('link', { name: /^start free$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(/\/auth\/login(\?.*)?$/);

		await gotoPublic(page, `${BASE_URL}/pricing`);
		const resourcesTrigger = header.getByRole('button', { name: /^resources$/i });
		await resourcesTrigger.click();
		const dropdown = page.locator('#public-resources-menu');
		await expect(dropdown).toBeVisible();
		await dropdown.getByRole('menuitem', { name: /^insights$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(/\/insights$/);

		// Test landing page CTAs
		await goToLanding(page);
		await page
			.locator('#hero')
			.getByRole('link', { name: /start free workspace/i })
			.first()
			.click();
		await expect(page).toHaveURL(/\/auth\/login(\?.*)?$/);

		await goToLanding(page);
		await page
			.locator('#hero')
			.getByRole('link', { name: /see pricing/i })
			.first()
			.click();
		await expect(page).toHaveURL(/\/pricing(\?.*)?$/);

		await goToLanding(page);
		await page.locator('#plans').getByRole('link', { name: /start/i }).first().click();
		await expect(page).toHaveURL(/\/auth\/login\?.*plan=free/);

		await goToLanding(page);
		await page
			.locator('#plans')
			.getByRole('link', { name: /see growth/i })
			.first()
			.click();
		await expect(page).toHaveURL(/\/pricing(\?.*)?$/);

		await security.assertClean();
	});

	test('public content slug routes and enterprise intake destinations stay operational', async ({
		page
	}) => {
		await assertPublicRoute(
			page,
			'/docs/quick-start-workspace',
			/quick start a valdrics workspace/i
		);
		await assertPublicRoute(page, '/resources/executive-one-pager', /executive one-pager/i);
		await assertPublicRoute(
			page,
			'/insights/from-alert-to-approved-action',
			/from alert to approved action/i
		);
		await assertPublicRoute(page, '/proof/safe-access-model', /safe access model/i);
		await assertPublicRoute(
			page,
			'/proof/deployment-and-data-residency',
			/deployment and data residency review/i
		);

		await gotoPublic(page, `${BASE_URL}/enterprise`);
		await page
			.getByRole('link', { name: /request enterprise briefing/i })
			.first()
			.click();
		await expect(page).toHaveURL(/\/talk-to-sales(\?.*)?$/);
		await expect(page.getByRole('heading', { level: 1, name: /talk to sales/i })).toBeVisible();
		await expect(page).toHaveURL(/intent=enterprise_briefing/);

		const onePagerHref = '/resources/valdrics-enterprise-one-pager.md';
		await assertDownloadEndpoint(page, onePagerHref, /text\/markdown|text\/plain/i);
	});

	test('talk-to-sales success flow submits one inquiry with marketing context', async ({
		page
	}) => {
		await installTurnstileStub(page);

		let capturedPayload: Record<string, unknown> | null = null;
		await page.route('**/api/marketing/talk-to-sales', async (route) => {
			capturedPayload = route.request().postDataJSON() as Record<string, unknown>;
			await route.fulfill({
				status: 202,
				contentType: 'application/json',
				body: JSON.stringify({ ok: true, accepted: true, inquiryId: 'inq-e2e-1' })
			});
		});

		await gotoPublic(
			page,
			`${BASE_URL}/talk-to-sales?utm_source=linkedin&utm_medium=paid&utm_campaign=q1`
		);
		await waitForPublicHydration(page);
		await page.getByLabel(/name/i).fill('Buyer One');
		await page.getByLabel(/work email/i).fill('buyer@example.com');
		await page.getByLabel(/company/i).fill('Example Inc');
		await page.getByLabel(/role/i).fill('VP Platform');
		await page.getByLabel(/buyer region/i).selectOption('United States');
		await page.getByLabel(/cloud and saas scope/i).fill('AWS and SaaS');
		await page.getByRole('button', { name: /send inquiry/i }).click();

		await expect(page.getByRole('status')).toContainText(/inquiry received/i);
		expect(capturedPayload).toMatchObject({
			name: 'Buyer One',
			email: 'buyer@example.com',
			company: 'Example Inc',
			role: 'VP Platform',
			buyerRegion: 'United States',
			deploymentScope: 'AWS and SaaS',
			utmSource: 'linkedin',
			utmMedium: 'paid',
			utmCampaign: 'q1'
		});
	});

	test('talk-to-sales failure flow preserves inline error handling', async ({ page }) => {
		await installTurnstileStub(page);

		await page.route('**/api/marketing/talk-to-sales', async (route) => {
			await route.fulfill({
				status: 503,
				contentType: 'application/json',
				body: JSON.stringify({ ok: false, error: 'delivery_failed' })
			});
		});

		await gotoPublic(page, `${BASE_URL}/talk-to-sales`);
		await waitForPublicHydration(page);
		await page.getByLabel(/name/i).fill('Buyer One');
		await page.getByLabel(/work email/i).fill('buyer@example.com');
		await page.getByLabel(/company/i).fill('Example Inc');
		await page.getByRole('button', { name: /send inquiry/i }).click();

		await expect(page.getByRole('alert')).toContainText(/could not route the inquiry/i);
	});
});

test.describe('Public marketing smoke (mobile)', () => {
	test.use({ viewport: { width: 390, height: 844 } });

	test('key landing sections and docs pages remain usable', async ({ page }, testInfo) => {
		await goToLanding(page);
		const landingHeading = page.getByRole('heading', { level: 1 }).first();
		await expect(landingHeading).toBeVisible();
		await expect(landingHeading).toContainText(
			/control|cleaner|path|reports|context|margin|govern|optimize/i
		);
		await expect(page.locator('#product')).toBeVisible();
		await expect(page.locator('#simulator')).toBeVisible();
		await expect(page.locator('#plans')).toBeVisible();
		await expect(page.locator('[aria-label="Why teams choose Valdrics"]')).toBeVisible();

		await assertPublicRoute(page, '/docs', /documentation/i);
		await assertPublicRoute(page, '/docs/api', /api reference/i);
		await assertPublicRoute(page, '/status', /system status/i);
		await page.screenshot({
			path: testInfo.outputPath('mobile-public-smoke.png'),
			fullPage: true
		});
	});

	test('mobile menu links resolve key landing and route destinations', async ({ page }) => {
		await gotoPublic(page, `${BASE_URL}/pricing`);
		await page.setViewportSize({ width: 390, height: 844 });
		await page.waitForLoadState('networkidle');

		await (await openMobileMenu(page)).getByRole('link', { name: /^start free$/i }).click();
		await expect(page).toHaveURL(/\/auth\/login(\?.*)?$/);

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await (await openMobileMenu(page)).getByRole('link', { name: /^product$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/#product'));

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await (await openMobileMenu(page)).getByRole('link', { name: /^pricing$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/pricing'));

		await gotoPublic(page, `${BASE_URL}/pricing`);
		await (await openMobileMenu(page)).getByRole('link', { name: /^enterprise$/i }).click();
		await page.waitForLoadState('networkidle');
		await expect(page).toHaveURL(new RegExp('/enterprise'));

		if (isLocalDashboardUrl) {
			await expect(page.locator('main')).toBeVisible();
		}
	});
});
