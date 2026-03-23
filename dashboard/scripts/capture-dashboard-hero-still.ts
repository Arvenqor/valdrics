import { mkdir } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

import { BASE_URL, enableAuthenticatedSession } from '../e2e/support/e2eAuth';

const __dirname = dirname(fileURLToPath(import.meta.url));

const outputPath = resolve(
	process.env.HERO_STILL_OUTPUT_PATH || resolve(__dirname, '../static/landing-dashboard-still.jpg')
);
const routePath = process.env.HERO_STILL_ROUTE || '/dashboard';
const viewportWidth = Number(process.env.HERO_STILL_VIEWPORT_WIDTH || '1440');
const viewportHeight = Number(process.env.HERO_STILL_VIEWPORT_HEIGHT || '960');

const browser = await chromium.launch({
	headless: true
});

try {
	const context = await browser.newContext({
		viewport: { width: viewportWidth, height: viewportHeight },
		deviceScaleFactor: 1
	});

	await enableAuthenticatedSession(context);

	const page = await context.newPage();
	await page.emulateMedia({ reducedMotion: 'reduce' });
	await page.goto(new URL(routePath, BASE_URL).toString(), {
		waitUntil: 'domcontentloaded'
	});
	await page.waitForLoadState('networkidle');
	await page.getByRole('heading', { level: 1, name: /dashboard/i }).waitFor({
		state: 'visible',
		timeout: 30_000
	});
	await page.waitForTimeout(400);

	await mkdir(dirname(outputPath), { recursive: true });
	await page.screenshot({
		path: outputPath,
		type: 'jpeg',
		quality: 84,
		fullPage: false,
		animations: 'disabled',
		caret: 'hide'
	});
} finally {
	await browser.close();
}
