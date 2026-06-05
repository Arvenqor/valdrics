from decimal import Decimal, InvalidOperation
from typing import Any

SPEND_LEDGER_DECIMAL_PARSE_EXCEPTIONS: tuple[type[Exception], ...] = (
    InvalidOperation,
    TypeError,
    ValueError,
)


def _decimal_string(value: Any, *, places: int = 8) -> str:
    if value is None:
        return format(Decimal("0").quantize(Decimal(1).scaleb(-places)), "f")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value))
    except SPEND_LEDGER_DECIMAL_PARSE_EXCEPTIONS as exc:
        raise ValueError("Spend ledger amount must be numeric") from exc
    if not amount.is_finite():
        raise ValueError("Spend ledger amount must be finite")
    return format(amount.quantize(Decimal(1).scaleb(-places)), "f")


def _optional_decimal_string(value: Any, *, places: int = 8) -> str | None:
    if value is None:
        return None
    return _decimal_string(value, places=places)
