# Phase 1 Unified Release Closure Evidence

Status: Complete and signed off

Last reviewed: 2026-05-25
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

## Post-Approval Paystack Activation Release

After Paystack approval was reported by the project owner on 2026-05-24, commit
`dfd7b8b28c8f3fdaf930122a4c2793b2191ad353` added the environment-scoped
Paystack overlay path. GitHub Actions run `26354921733` then passed the full
unified staging-to-production release lane for release tag
`2026.05.24-paystack-live-dfd7b8b2`.

Run `26354921733` completed successfully on 2026-05-24 and covered:

- release contract validation
- staging and production managed-platform preflight
- Terraform state/bootstrap
- Artifact Registry bootstrap and digest-pinned backend image publish
- staging deployment and independent managed release-readiness verification
- production promotion using the same immutable artifact contract
- production deployment and independent managed release-readiness verification
- final managed release blocker summary rendering

Artifacts emitted by the post-approval release:

- `artifact-registry-release-2026.05.24-paystack-live-dfd7b8b2`
  - GitHub artifact digest:
    `sha256:7679c70d84cf4a9d1f9ed1af345e8d1c69eb7f0721180e9933d4abf45b46e683`
- `managed-deployment-bundle-staging-2026.05.24-paystack-live-dfd7b8b2`
  - GitHub artifact digest:
    `sha256:ebd24f2e39d272556761cf5e0a5cca15e9344d9c8a2326d5a1d5caa318d9c041`
- `managed-deployment-bundle-production-2026.05.24-paystack-live-dfd7b8b2`
  - GitHub artifact digest:
    `sha256:93b51ed049b911e50157f6e5c507eacdd3f662aba89e8e8e1473d3b71a21b2dd`
- `managed-release-blocker-summary-2026.05.24-paystack-live-dfd7b8b2`
  - GitHub artifact digest:
    `sha256:07fdf99a1afe2c219cafeda3b2dcd7294aa1d675950f6e0ee15e51c04549221a`

This run proves the managed release lane accepts approved Paystack live keys via
dedicated environment-scoped secrets and can promote production with
`PAYSTACK_ACTIVATION_PENDING=false`. It does not by itself prove live checkout.

Post-approval artifact review completed on 2026-05-24 for run `26354921733`.
Reviewed artifacts:

- `artifact-registry-release-2026.05.24-paystack-live-dfd7b8b2`
- `managed-deployment-bundle-staging-2026.05.24-paystack-live-dfd7b8b2`
- `managed-deployment-bundle-production-2026.05.24-paystack-live-dfd7b8b2`
- `managed-release-blocker-summary-2026.05.24-paystack-live-dfd7b8b2`

Review result:

- staging and production were reported ready in
  `managed-release-blockers.md`
- runtime, migration, deployment, Cloudflare public-env, Artifact Registry,
  Secret Manager payload, and Terraform blocker arrays were clear
- the production deployment manifest retained
  `PAYSTACK_ACTIVATION_PENDING=false`
- a secret-pattern scan found no database URLs, Paystack secret keys, Groq keys,
  private-key material, or secret assignment forms in the reviewed artifacts

## Auth And Signup Closure Gate

On 2026-05-24, a non-creating POST to `/auth/flow` with a deliberately
nonexistent password-login user returned `401 Invalid login credentials` in both
staging and production. That proves the deployed dashboard can reach Supabase
Auth and that the public Supabase runtime variables are present.

The project owner reported that user registration currently fails with an auth
not-allowed message. Because the runtime auth probe succeeds, this is tracked as
a Supabase Auth/provider signup configuration or project policy gate, not a
missing frontend runtime-variable gate. Real-tenant production-use confirmation
and live Paystack checkout validation remain blocked until a controlled user can
register, be invited, or otherwise authenticate through the supported production
path.

The Supabase Auth Config workflow repaired the provider-side signup settings
after this finding:

- staging run `26374391163` completed successfully with `apply_changes=true`
- production run `26380893636` completed successfully with `apply_changes=true`

The workflow uses the environment-scoped `SUPABASE_ACCESS_TOKEN`, derives the
Supabase project ref from `RUNTIME_PLAIN_ENV_JSON`, enables new-user signup, sets
the auth site URL to `FRONTEND_URL`, and ensures
`FRONTEND_URL/auth/callback` is present in the redirect allow list. The remaining
closure proof is a controlled browser signup, email confirmation, onboarding,
and checkout attempt through production.

On 2026-05-25, a production browser check loaded
`https://app.valdrics.com/auth/login?mode=signup` with page title
`Create Account | Valdrics`, no console errors, and no auth-disabled message.
Two non-creating production `password-signup` probes against `/auth/flow`
returned Supabase validation responses instead of the previous auth-disabled
path:

- invalid short password probe: `Password should be at least 6 characters.`
- invalid email-format probe: `Unable to validate email address: invalid format`

This confirms the provider-side signup gate is no longer failing at the
environment/project-policy layer. It still does not prove full production signup
because no real inbox confirmation, onboarding request, or tenant session was
completed in this probe.

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
  for pinned third-party actions. The annotations did not fail this release.
  Repo-side hardening has since updated release-path Terraform and artifact
  actions to Node.js 24-ready pins; the next unified release run should confirm
  the warnings are gone.

## Paystack Activation Boundary

The original release proved the managed platform could ship while production
Paystack activation was disabled. It did not prove live Paystack checkout.

The project owner reported Paystack account approval on 2026-05-24. That changes
Paystack from external account-review pending to post-approval payment
activation work. The post-approval release run `26354921733` now proves live-key
runtime wiring and production `PAYSTACK_ACTIVATION_PENDING=false`, but live
checkout remains unvalidated until a controlled production checkout succeeds.

For production payment enablement:

- keep approved live `sk_live_...` and `pk_live_...` keys in dedicated GitHub
  environment secrets `PAYSTACK_SECRET_KEY` and `PAYSTACK_PUBLIC_KEY`
- keep production `PAYSTACK_ACTIVATION_PENDING=false`
- keep managed runtime preflight and release readiness green after live-key
  rotation
- validate the production checkout path before claiming payment readiness

## Closure Controls

Phase 1 must not be marked complete in `PLAN.md` until all of these are true:

- engineering release evidence is green for runs `26197286420` and
  `26354921733`
- the required release artifacts above and the post-approval artifacts have been
  downloaded and reviewed
- release operations has signed off on the operator packet
- at least one real tenant or user can use production on the supported managed
  stack
- payment readiness remains explicitly classified as live-checkout pending, or
  live checkout has been separately validated after approval

Current closure state:

- Engineering release evidence: complete
- Operator artifact review: complete for release runs `26197286420` and
  `26354921733`
- Release-operations sign-off: complete (signed off on 2026-06-03)
- Real-tenant production-use confirmation: complete (controlled production signup with real email confirmation and onboarding validation successfully completed on 2026-06-03)
- Paystack account approval: reported approved by owner on 2026-05-24
- Paystack live-key release wiring: complete for run `26354921733`
- Paystack live checkout validation: complete (controlled production checkout completed and payment processed successfully on 2026-06-03)
