# All Changes Categorization (2026-03-23)

Snapshot:
- Captured at: `2026-03-23T00:00:00Z`
- Base commit: `4cb0686024d41a3686585599abccfb67b1626fe9`
- Pending paths: `43`
- Branch at snapshot: `chore/all-changes-categorization-2026-03-22`

## Track CG: Landing Hero Composition, Visual System, and Capture Automation
Scope:
- Consolidate landing hero composition, shared landing styles, calculator surfaces, and visual-capture automation in one frontend implementation lane.
- Keep the landing component test coverage with the exact components and styles it exercises.
- Treat this as the core landing-build track separate from route-level page delivery.

Paths:
- `dashboard/scripts/capture-dashboard-hero-still.ts`
- `dashboard/src/lib/components/LandingHero.svelte`
- `dashboard/src/lib/components/LandingHero.svelte.test.ts`
- `dashboard/src/lib/components/landing/LandingCurrencyToggle.svelte`
- `dashboard/src/lib/components/landing/LandingHeroCopy.svelte`
- `dashboard/src/lib/components/landing/LandingHeroView.public.css`
- `dashboard/src/lib/components/landing/LandingHeroView.svelte`
- `dashboard/src/lib/components/landing/LandingMarketingShared.css`
- `dashboard/src/lib/components/landing/LandingPlansSection.svelte`
- `dashboard/src/lib/components/landing/LandingRoiCalculator.svelte`
- `dashboard/src/lib/components/landing/LandingRoiSimulator.svelte`
- `dashboard/src/lib/components/landing/LandingTrustSection.svelte`
- `dashboard/src/lib/landing/heroContent.extended.ts`

Notes:
- This track is the primary landing composition and visual-system slice of the batch.

## Track CH: Public Content, Pricing Data, and Navigation Contracts
Scope:
- Group shared public content models, pricing-plan data, talk-to-sales content, and public navigation contracts together.
- Keep non-route content and navigation sources in one review lane so route changes can stay focused on delivery surfaces.
- Treat this as the shared marketing-data and copy-contract track for the batch.

Paths:
- `dashboard/src/lib/content/publicCompany.ts`
- `dashboard/src/lib/content/publicContent.docs.ts`
- `dashboard/src/lib/content/publicContent.insights.ts`
- `dashboard/src/lib/content/publicContent.proof.ts`
- `dashboard/src/lib/content/publicContent.resources.ts`
- `dashboard/src/lib/landing/publicNav.ts`
- `dashboard/src/lib/pricing/publicPlans.ts`
- `dashboard/src/routes/pricing/pricingPageContent.ts`
- `dashboard/src/routes/talk-to-sales/talk-to-sales-page-content.ts`

Notes:
- This track captures shared content and navigation sources used across the public site.

## Track CI: Public Routes, Shell, and Page-Level Regression Coverage
Scope:
- Batch the public shell and page-route changes together with their page-level regression tests.
- Keep public route delivery behavior separate from shared content and landing component composition.
- Treat this as the route-level public web track for the follow-up batch.

Paths:
- `dashboard/src/routes/about/+page.svelte`
- `dashboard/src/routes/about/about-page.svelte.test.ts`
- `dashboard/src/routes/billing/+page.svelte`
- `dashboard/src/routes/billing/billing-page.svelte.test.ts`
- `dashboard/src/routes/docs/technical-validation/+page.svelte`
- `dashboard/src/routes/docs/technical-validation/technical-validation-page.svelte.test.ts`
- `dashboard/src/routes/insights/+page.svelte`
- `dashboard/src/routes/insights/insights-page.svelte.test.ts`
- `dashboard/src/routes/layout-public-menu.svelte.test.ts`
- `dashboard/src/routes/layout/PublicSiteShell.svelte`
- `dashboard/src/routes/pricing/+page.svelte`
- `dashboard/src/routes/pricing/pricing-page.svelte.test.ts`
- `dashboard/src/routes/privacy/+page.svelte`
- `dashboard/src/routes/privacy/privacy-page.svelte.test.ts`
- `dashboard/src/routes/proof/+page.svelte`
- `dashboard/src/routes/proof/proof-page.svelte.test.ts`
- `dashboard/src/routes/resources/+page.svelte`
- `dashboard/src/routes/resources/resources-page.svelte.test.ts`
- `dashboard/src/routes/roi-planner/+page.svelte`
- `dashboard/src/routes/terms/+page.svelte`
- `dashboard/src/routes/terms/terms-page.svelte.test.ts`

Notes:
- This track is the page-delivery and shell-integration slice of the public site.

## Batching Decision
Decision:
- Merge as one consolidated PR.

Reasoning:
- The batch is one active dashboard and public-site follow-up slice centered on the same landing and public-route surfaces.
- Splitting it further would create overlapping PRs across shared landing components, route content, and public shell contracts.
- The issue split keeps review accountability without fragmenting the delivery batch.
