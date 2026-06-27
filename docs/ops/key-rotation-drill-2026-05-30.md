# Enforcement Key Rotation Drill Evidence (2026-05-30)

Generated from live enforcement test execution for release gate verification.

## Metadata

- drill_id: KRD-2026-05-30-ENF-RT
- executed_at_utc: 2026-05-30T23:50:19Z
- environment: ci
- owner: ci-security-oncall
- approver: ci-platform-oncall
- next_drill_due_on: 2026-08-28

## Evidence Sources

- source_pre_rotation_tokens_accepted: tests/unit/enforcement/enforcement_service_cases_part03.py::test_consume_approval_token_accepts_primary_secret
- source_result_pre_rotation_tokens_accepted: pass
- source_post_rotation_new_tokens_accepted: tests/unit/enforcement/enforcement_service_cases_part03.py::test_consume_approval_token_accepts_new_primary_secret_after_rotation
- source_result_post_rotation_new_tokens_accepted: pass
- source_post_rotation_old_tokens_rejected: tests/unit/enforcement/enforcement_service_cases_part04.py::test_consume_approval_token_rejects_rotated_secret_without_fallback
- source_result_post_rotation_old_tokens_rejected: pass
- source_fallback_verification_passed: tests/unit/enforcement/enforcement_service_cases_part03.py::test_consume_approval_token_accepts_rotated_fallback_secret
- source_result_fallback_verification_passed: pass
- source_rollback_validation_passed: tests/unit/enforcement/enforcement_service_cases_part04.py::test_consume_approval_token_accepts_rollback_fallback_secret
- source_result_rollback_validation_passed: pass
- source_replay_protection_intact: tests/unit/enforcement/enforcement_service_cases_part03.py::test_consume_approval_token_rejects_replay
- source_result_replay_protection_intact: pass
- source_alert_pipeline_verified: tests/unit/enforcement/test_reservation_settlement_worker.py::test_reservation_settlement_worker_sends_sla_release_alert
- source_result_alert_pipeline_verified: pass
- source_endpoint_replay_tamper_guard: tests/unit/enforcement/test_key_rotation_drill_selectors.py::test_consume_approval_token_endpoint_rejects_replay_and_tamper
- source_result_endpoint_replay_tamper_guard: pass

## Validation Outcomes

- pre_rotation_tokens_accepted: true
- post_rotation_new_tokens_accepted: true
- post_rotation_old_tokens_rejected: true
- fallback_verification_passed: true
- rollback_validation_passed: true
- replay_protection_intact: true
- alert_pipeline_verified: true
- endpoint_replay_tamper_guard: true
- post_drill_status: PASS

## Executed Selector Summary

- total_selectors_run: 8
