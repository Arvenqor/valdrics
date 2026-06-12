from decimal import Decimal, InvalidOperation
from typing import Any


def coerce_finite_decimal(value: Any, *, field_name: str = "value") -> Decimal:
    """
    Coerces a value to a finite Decimal, raising ValueError if conversion fails
    or the resulting Decimal is not finite.
    """
    if value is None or value == "":
        return Decimal("0")
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError(f"{field_name} must be finite")
        return value
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not amount.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return amount


def coerce_finite_float(value: Any, *, field_name: str = "value") -> float:
    """
    Coerces a value to a finite float, raising ValueError if conversion fails
    or the resulting float is not finite.
    """
    return float(coerce_finite_decimal(value, field_name=field_name))


def coerce_finite_int(value: Any, *, field_name: str = "value") -> int:
    """
    Coerces a value to a finite integer, raising ValueError if conversion fails
    or the resulting integer is not finite.
    """
    return int(coerce_finite_decimal(value, field_name=field_name))


def coerce_positive_int(
    value: Any,
    *,
    default: int,
    minimum: int,
    field_name: str = "value",
) -> int:
    """
    Coerces a value to a positive integer, with a default and minimum.
    """
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}")
    return parsed