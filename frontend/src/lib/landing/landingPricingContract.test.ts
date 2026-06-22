import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { DEFAULT_PRICING_PLANS } from '$lib/pricing/publicPlans';
import { COMPARISON_ROWS, structuredData } from './landingContent';

type StructuredGraphNode = {
	'@type'?: string;
	offers?: Array<{
		name?: string;
		price?: string;
		priceCurrency?: string;
		description?: string;
	}>;
};

describe('landing pricing contract', () => {
	it('derives landing structured data offers from the production pricing plans', () => {
		const graph = structuredData['@graph'] as readonly StructuredGraphNode[];
		const softwareApplication = graph.find((node) => node['@type'] === 'SoftwareApplication');

		expect(softwareApplication?.offers).toEqual(
			DEFAULT_PRICING_PLANS.map((plan) => ({
				'@type': 'Offer',
				name: plan.name,
				price: String(plan.price_monthly),
				priceCurrency: 'USD',
				description: plan.description
			}))
		);
	});

	it('keeps handoff-only pricing and trial claims out of landing sources', () => {
		const sourcePaths = [
			'src/lib/components/LandingHero.svelte',
			'src/lib/components/landing/LandingHeroView.svelte',
			'src/lib/components/landing/LandingHeroBelowFold.svelte',
			'src/lib/components/landing/LandingPlansSection.svelte',
			'src/lib/components/landing/LandingHeroTrustSections.svelte',
			'src/lib/landing/LandingCtaFooter.svelte',
			'src/lib/landing/landingContent.ts'
		];

		const source = sourcePaths
			.map((path) => readFileSync(resolve(process.cwd(), path), 'utf8'))
			.join('\n');

		expect(source).not.toMatch(/\$799|Start free trial|14-day trial|no card needed/i);
		expect(source).not.toMatch(/name:\s*['"]Team['"]/);
		expect(source).not.toMatch(/tier:\s*['"]Team['"]/);
		expect(source).not.toMatch(/price:\s*['"]\$299['"]/);
		expect(COMPARISON_ROWS).toContainEqual([
			'Starting price',
			'$0 free tier / $49 paid entry',
			'$$$$ custom',
			'$$$$ custom',
			'Free'
		]);
	});
});
