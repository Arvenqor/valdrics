# Month-End Close (Operator Runbook)

Valdrics “month-end close” is a deterministic reconciliation package meant for
finance and audit review:

- Close status (ready / not-ready reasons)
- Lifecycle counts (preliminary vs final)
- Discrepancy detection summary
- Restatement history snapshot
- Integrity hash for tamper-evident evidence

This is not a production cutover packet. Deployment cutover remains on
`docs/runbooks/unified_platform_release.md`.

## Prerequisites

- Tenant must be on a tier that includes `close_workflow` (typically Pro/Enterprise).
- Billing ledger ingestion should be running and finalization should have progressed (preliminary -> final).

## UI (Fastest)

1. Open `Ops Center` in the dashboard.
2. In **Reconciliation Close Workflow**:
   - Select the period (start/end).
   - Optionally filter by provider (AWS/Azure/GCP/SaaS/License).
3. Click:
   - `Preview Close Status`
   - `Download Close JSON`
   - `Download Close CSV`
   - `Download Restatements CSV`

## API (Automation-Friendly)

- Preview / export close package:
  - `GET /api/v1/costs/reconciliation/close-package?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&response_format=json|csv&enforce_finalized=false`
- Export restatement history:
  - `GET /api/v1/costs/reconciliation/restatements?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&response_format=csv`
- Export restatement run summaries (grouped by ingestion_batch_id):
  - `GET /api/v1/costs/reconciliation/restatement-runs?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&response_format=csv`

## Evidence Bundle (Recommended)

Capture supplemental finance evidence under `reports/acceptance/`:

```bash
export VALDRICS_API_URL="http://127.0.0.1:8000"
export VALDRICS_TOKEN="your-bearer-jwt"
uv run python scripts/capture_acceptance_evidence.py \
  --close-start-date 2026-01-01 \
  --close-end-date 2026-01-31 \
  --close-provider all
```

This produces (among other artifacts):

- `close_package.json` — lifecycle counts, reconciliation summary, restatement history, integrity hash
- `close_package.csv` — same data in tabular form
- `restatements.csv` — raw restatement entries

When `CLOSE_PACKAGE_HMAC_SECRET` (>= 32 chars) is configured, `close_package.json` includes a `evidence` block with HMAC-SHA256 signature and key metadata for tamper verification.

This bundle supports finance/procurement review. It does not replace the
managed deployment bundle or the cutover evidence path in
`docs/runbooks/unified_platform_release.md`.

## Notes

- `enforce_finalized=false` is useful for readiness previews; it reports that a close is not ready instead of hard-failing.
- Close package CSV is never stored inside audit logs (too large); it is captured as an operator artifact instead.
