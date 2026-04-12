from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _extract_assignment_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key = line.split("=", 1)[0].strip()
        if key:
            keys.add(key)
    return keys


def test_env_example_contains_required_runtime_contract_keys() -> None:
    keys = _extract_assignment_keys(REPO_ROOT / ".env.example")

    required = {
        "ENVIRONMENT",
        "DATABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_JWT_SECRET",
        "ENCRYPTION_KEY",
        "KDF_SALT",
        "CSRF_SECRET_KEY",
        "ADMIN_API_KEY",
        "LLM_PROVIDER",
        "REDIS_URL",
        "APP_RUNTIME_DATA_DIR",
        "CIRCUIT_BREAKER_DISTRIBUTED_STATE",
    }

    missing = required - keys
    assert not missing, f".env.example missing keys: {sorted(missing)}"


def test_env_example_does_not_publish_local_compose_redis_url_as_shared_default() -> (
    None
):
    text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")
    assert "REDIS_URL=redis://redis:6379" not in text
    assert "Local compose default: redis://redis:6379" not in text
