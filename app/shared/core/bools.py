from __future__ import annotations

from typing import Any


def parse_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) or type(value).__name__ == "Decimal":
        if value == 1:
            return True
        if value == 0:
            return False
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return None


def coerce_bool(value: Any, *, default: bool = False) -> bool:
    parsed = parse_bool(value)
    return parsed if parsed is not None else default


__all__ = ["coerce_bool", "parse_bool"]
