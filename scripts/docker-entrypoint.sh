#!/bin/sh
set -eu

python - <<'PY'
from app.shared.core.config import get_settings
from app.shared.core.runtime_dependencies import validate_runtime_dependencies

settings = get_settings()
validate_runtime_dependencies(settings)
print("runtime_env_validation_passed", f"environment={settings.ENVIRONMENT}")
PY

PORT="${PORT:-8000}"

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
