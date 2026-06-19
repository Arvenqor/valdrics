import { expect, test } from '@playwright/test';

async function attachSecurityGuards(page: Parameters<typeof test>[0]['page']) {
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

			// Chromium can report SvelteKit modulepreload headers and Cloudflare edge
			// injections as CSP violations even when the app scripts hydrate correctly.
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

test.describe('Landing layout audit regressions', () => {
	test.use({ reducedMotion: 'reduce' });

	test('keeps the public landing concise, structured, and CSP-clean', async ({ page }) => {
		const security = await attachSecurityGuards(page);
		await page.setViewportSize({ width: 1365, height: 820 });
		await page.goto('/');
		await page.waitForLoadState('networkidle');

		for (const sectionId of ['#hero', '#product', '#simulator', '#plans', '#trust']) {
			await expect(page.locator(sectionId)).toBeVisible();
		}

		await expect(page.locator('#hero')).toContainText(/control|cleaner|path|reports|context|margin|govern|optimize/i);
		await expect(page.locator('#hero .badge-accent')).toBeVisible();
		await expect(page.locator('#product .landing-public-pillar-card')).toHaveCount(3);
		await expect(page.locator('#plans .landing-public-plan-card')).toHaveCount(3);
		await expect(page.locator('#trust .landing-public-trust-card')).toHaveCount(3);
		await expect(page.locator('.landing-public-proof-strip .landing-public-proof-item')).toHaveCount(3);

		const overflow = await page.evaluate(() => ({
			scrollWidth: document.documentElement.scrollWidth,
			viewportWidth: window.innerWidth
		}));
		expect(overflow.scrollWidth).toBeLessThanOrEqual(overflow.viewportWidth + 1);

		await security.assertClean();
	});

	test.describe('mobile viewport 390', () => {
		test.use({ viewport: { width: 390, height: 844 } });

		test('keeps mobile landing and footer chips inside the viewport', async ({ page }) => {
			const security = await attachSecurityGuards(page);
			
			// Verify landing page viewport on /
			await page.goto('/');
			await page.waitForLoadState('networkidle');
			const landingOverflow = await page.evaluate(() => ({
				scrollWidth: document.documentElement.scrollWidth,
				viewportWidth: window.innerWidth
			}));
			expect(landingOverflow.scrollWidth).toBeLessThanOrEqual(landingOverflow.viewportWidth + 1);

			// Verify footer viewport on /pricing since footer is hidden on landing page in Svelte 5
			await page.goto('/pricing');
			await page.waitForLoadState('networkidle');

			await page.evaluate(() => {
				window.scrollTo({ top: Math.round(document.documentElement.scrollHeight * 0.38) });
			});
			await page.waitForTimeout(120);

			const footer = page.getByRole('contentinfo');
			await expect(footer).toBeVisible();
			const lastFooterLink = footer.locator('.public-footer-link').last();
			await lastFooterLink.scrollIntoViewIfNeeded();
			const linkBounds = await lastFooterLink.boundingBox();
			expect(linkBounds).not.toBeNull();
			if (linkBounds) {
				expect(linkBounds.x).toBeGreaterThanOrEqual(0);
				expect(linkBounds.x + linkBounds.width).toBeLessThanOrEqual(390);
			}

			await security.assertClean();
		});
	});

	test.describe('mobile viewport 500', () => {
		test.use({ viewport: { width: 500, height: 900 } });

		test('keeps header actions on-screen at mobile breakpoint', async ({ page }) => {
			// Navigate to /pricing since header and mobile menu are hidden on landing page in Svelte 5
			await page.goto('/pricing');
			await page.waitForLoadState('networkidle');

			const headerOverflow = await page.evaluate(() => ({
				scrollWidth: document.documentElement.scrollWidth,
				viewportWidth: window.innerWidth
			}));
			expect(headerOverflow.scrollWidth).toBeLessThanOrEqual(headerOverflow.viewportWidth + 1);

			const menuToggle = page.getByRole('button', { name: /toggle menu/i });
			await expect(menuToggle).toBeVisible();
			await menuToggle.click();

			const mobileStartFree = page.locator('#public-mobile-menu a', { hasText: 'Start Free' });
			await expect(mobileStartFree).toBeVisible();
			const ctaBounds = await mobileStartFree.boundingBox();
			expect(ctaBounds).not.toBeNull();
			if (ctaBounds) {
				expect(ctaBounds.x).toBeGreaterThanOrEqual(0);
				expect(ctaBounds.x + ctaBounds.width).toBeLessThanOrEqual(500);
			}
		});
	});
});
