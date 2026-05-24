# Phase 1 Unified Release Closure Evidence

Status: Engineering release green; Phase 1 closure pending
release-operations sign-off and real-tenant production-use confirmation.

Last reviewed: 2026-05-24
Canonical plan: `PLAN.md`

## Release Identity

- Workflow: `.github/workflows/release-unified-platform.yml`
- GitHub Actions run ID: `26197286420`
- Workflow run URL: `https://github.com/Arvenqor/valdrics/actions/runs/26197286420`
- Branch: `main`
- Commit: `43c3cb5bd6bdb694f9cad48868ef90efd5a9fb67`
- Release tag: `2026.05.21-paystack-pending-43c3cb5b`

## Engineering Release Result

Run `26197286420` passed the full unified staging-to-production release lane for
commit `43c3cb5bd6bdb694f9cad48868ef90efd5a9fb67` and release tag
`2026.05.21-paystack-pending-43c3cb5b`.

The green release covered:

- release contract validation
- staging and production managed-platform preflight
- Terraform state/bootstrap
- Artifact Registry bootstrap and digest-pinned backend image publish
- staging deployment and independent managed release-readiness verification
- production promotion using the same immutable artifact contract
- production deployment and independent managed release-readiness verification
- final managed release blocker summary rendering

An earlier dispatch, run `26197236570`, used the short SHA `43c3cb5b` as
`git_ref` and failed during checkout before any staging or production mutation.
The authoritative release evidence is run `26197286420`, dispatched with the
full commit SHA.

## Required Release Artifacts

Download and review these artifacts from the workflow run before marking Phase 1
closed:

- `artifact-registry-release-2026.05.21-paystack-pending-43c3cb5b`
- `managed-deployment-bundle-staging-2026.05.21-paystack-pending-43c3cb5b`
- `managed-deployment-bundle-production-2026.05.21-paystack-pending-43c3cb5b`
- `managed-release-blocker-summary-2026.05.21-paystack-pending-43c3cb5b`

The per-environment managed deployment bundles are the non-secret evidence
packets. They must contain the runtime report, migration report, deployment
report, unified platform manifest, Cloudflare Pages env report,
Artifact Registry release report, and operator handoff for the target
environment.

## Artifact Review

Artifact review completed on 2026-05-21 for GitHub Actions run
`26197286420`.

Reviewed artifacts:

- `artifact-registry-release-2026.05.21-paystack-pending-43c3cb5b`
  - GitHub artifact digest:
    `sha256:3f8f467dcd830cf5b96fa92611b70c6f2fc96f117bc0a25cd8bbd76c0cab16d8`
  - Reviewed files: `artifact-registry-release.env`,
    `artifact-registry-release.json`
  - Result: release tag, commit SHA, and Artifact Registry promotion refs were
    present.
- `managed-deployment-bundle-staging-2026.05.21-paystack-pending-43c3cb5b`
  - GitHub artifact digest:
    `sha256:dd02d90db2de0c57f882dfef7f67aa398e982fe1382fb290ce3db36241cc77db`
  - Reviewed files: runtime report, migration report, deployment report,
    unified platform manifest, Cloudflare Pages env report, Artifact Registry
    release report, Technology Value admission receipt, and operator handoff.
  - Result: runtime, migration, Terraform, unified-platform, release
    promotion, Cloudflare public env, Artifact Registry, and Secret Manager
    blocker arrays were clear.
- `managed-deployment-bundle-production-2026.05.21-paystack-pending-43c3cb5b`
  - GitHub artifact digest:
    `sha256:1cc01fb41c00f413c020a24488407b28eef6f056f4b20b4b2de6746953a0bbca`
  - Reviewed files: runtime report, migration report, deployment report,
    unified platform manifest, Cloudflare Pages env report, Artifact Registry
    release report, Technology Value admission receipt, and operator handoff.
  - Result: runtime, migration, Terraform, unified-platform, release
    promotion, Cloudflare public env, Artifact Registry, and Secret Manager
    blocker arrays were clear. The production manifest retained
    `PAYSTACK_ACTIVATION_PENDING=true`.
- `managed-release-blocker-summary-2026.05.21-paystack-pending-43c3cb5b`
  - GitHub artifact digest:
    `sha256:daeebeffd3f7b7c00d4683b79960aa49af9f2c41b0a74b128347dc6ce11ab138`
  - Reviewed file: `managed-release-blockers.md`
  - Result: staging and production were reported ready, with no shared,
    staging-only, or production-only blockers.

Review notes:

- The downloaded non-secret bundles contained secret names, public runtime
  values, and Secret Manager payload headings only. A pattern scan found no
  database URLs, Paystack secret keys, Groq keys, private-key material, or
  secret assignment forms in the reviewed artifacts.
- The artifact review is scoped to release commit
  `43c3cb5bd6bdb694f9cad48868ef90efd5a9fb67`. Later documentation-only commits
  must not be treated as runtime release proof without a new release run.
- The release workflow emitted GitHub Node.js 20 action-deprecation annotations
  for pinned third-party actions. The annotations did not fail this release, but
  workflow hardening should update those actions before GitHub forces Node.js 24
  for JavaScript actions on 2026-06-02.

## Paystack Activation Boundary

This release proves the managed platform can ship while production Paystack
activation is disabled. It does not prove live Paystack checkout.

The project owner reported Paystack account approval on 2026-05-24. That changes
Paystack from external account-review pending to post-approval payment
activation pending. The reviewed production release still retained
`PAYSTACK_ACTIVATION_PENDING=true`, so live checkout remains unvalidated.

For production payment enablement:

- install approved live `sk_live_...` and `pk_live_...` keys without committing
  secret values to the repository; the preferred path is dedicated GitHub
  environment secrets `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY`, set
  together
- change production to `PAYSTACK_ACTIVATION_PENDING=false`
- rerun the managed runtime preflight and release readiness checks after live
  keys are installed
- validate the production checkout path before claiming payment readiness

## Closure Controls

Phase 1 must not be marked complete in `PLAN.md` until all of these are true:

- engineering release evidence is green for run `26197286420`
- the required release artifacts above have been downloaded and reviewed
- release operations has signed off on the operator packet
- at least one real tenant or user can use production on the supported managed
  stack
- Paystack post-approval activation remains explicitly classified as pending, or
  live checkout has been separately validated after approval

Current closure state:

- Engineering release evidence: complete
- Operator artifact review: complete for release run `26197286420`
- Release-operations sign-off: pending manual sign-off
- Real-tenant production-use confirmation: pending manual sign-off
- Paystack account approval: reported approved by owner on 2026-05-24
- Paystack live checkout validation: pending post-approval activation release
