from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def build_evidence_payload(
    *,
    tenant_id: Any,
    package_payload: dict[str, Any],
) -> dict[str, Any]:
    canonical = json.dumps(package_payload, sort_keys=True, default=str)
    content_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return {
        "schema_version": "valdrics.reporting.close_evidence.v1",
        "tenant_id": str(tenant_id),
        "package_sha256": content_sha256,
        "package_payload": package_payload,
    }


def sign_evidence(
    *,
    evidence_payload: dict[str, Any],
    secret: str,
    key_id: str = "reporting-close-hmac-v1",
) -> dict[str, Any]:
    canonical = json.dumps(evidence_payload, sort_keys=True, default=str)
    signature = hmac.new(
        secret.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        **evidence_payload,
        "signature": signature,
        "signature_algorithm": "hmac-sha256",
        "signature_key_id": key_id,
    }


def resolve_evidence_secret() -> str:
    from app.shared.core.config import get_settings

    secret = getattr(get_settings(), "CLOSE_PACKAGE_HMAC_SECRET", "")
    if not secret or len(secret) < 32:
        raise ValueError(
            "CLOSE_PACKAGE_HMAC_SECRET must be set (>= 32 chars) to sign close packages."
        )
    return secret
