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

_start_uvicorn() {
  echo "Starting uvicorn on ${PORT}..."
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
}

for attempt in 1 2 3; do
  if _start_uvicorn; then
    exit 0
  fi
  echo "uvicorn exited unexpectedly (attempt ${attempt}); retrying in 5s..."
  sleep 5
done

echo "uvicorn failed after retries; exiting"
exit 1
