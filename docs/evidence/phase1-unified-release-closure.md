# Phase 1 Unified Release Closure Evidence

Status: Engineering release green; Phase 1 closure pending manual artifact
review, release-operations sign-off, and real-tenant production-use
confirmation.

Last reviewed: 2026-05-20
Canonical plan: `PLAN.md`

## Release Identity

- Workflow: `.github/workflows/release-unified-platform.yml`
- GitHub Actions run ID: `26131799197`
- Workflow run URL: `https://github.com/Arvenqor/valdrics/actions/runs/26131799197`
- Branch: `main`
- Commit: `8ef0b893c2ac7d7d87798d8efee94f70044a7fa0`
- Release tag: `2026.05.19-paystack-pending-8ef0b893`

## Engineering Release Result

Run `26131799197` passed the full unified staging-to-production release lane for
commit `8ef0b893c2ac7d7d87798d8efee94f70044a7fa0` and release tag
`2026.05.19-paystack-pending-8ef0b893`.

The green release covered:

- release contract validation
- staging and production managed-platform preflight
- Terraform state/bootstrap
- Artifact Registry bootstrap and digest-pinned backend image publish
- staging deployment and managed release-readiness verification
- production promotion using the same immutable artifact contract
- production deployment and managed release-readiness verification
- final managed release blocker summary rendering
- public marketing smoke, public accessibility, public performance, and visual
  smoke gates

## Required Release Artifacts

Download and review these artifacts from the workflow run before marking Phase 1
closed:

- `artifact-registry-release-2026.05.19-paystack-pending-8ef0b893`
- `managed-deployment-bundle-staging-2026.05.19-paystack-pending-8ef0b893`
- `managed-deployment-bundle-production-2026.05.19-paystack-pending-8ef0b893`
- `managed-release-blocker-summary-2026.05.19-paystack-pending-8ef0b893`

The per-environment managed deployment bundles are the non-secret evidence
packets. They must contain the runtime report, migration report, deployment
report, unified platform manifest, Cloudflare Pages env report,
Artifact Registry release report, and operator handoff for the target
environment.

## Paystack Activation Boundary

This release proves the managed platform can ship while Paystack account
activation is pending. It does not prove live Paystack checkout.

For production payment enablement:

- keep `PAYSTACK_ACTIVATION_PENDING=true` while Paystack approval is pending
- keep checkout review-safe while activation is pending
- change to `PAYSTACK_ACTIVATION_PENDING=false` only after approved live
  `sk_live_...` and `pk_live_...` keys are available
- rerun the managed runtime preflight and release readiness checks after live
  keys are installed

## Closure Controls

Phase 1 must not be marked complete in `PLAN.md` until all of these are true:

- engineering release evidence is green for run `26131799197`
- the required release artifacts above have been downloaded and reviewed
- release operations has signed off on the operator packet
- at least one real tenant or user can use production on the supported managed
  stack
- Paystack remains explicitly classified as external pending work, or live
  checkout has been separately validated after approval

Current closure state:

- Engineering release evidence: complete
- Operator artifact review: pending manual sign-off
- Release-operations sign-off: pending manual sign-off
- Real-tenant production-use confirmation: pending manual sign-off
- Paystack live checkout validation: pending external approval
