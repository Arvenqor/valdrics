import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Any

from app.modules.reporting.api.v1.costs_helpers import sanitize_csv_cell


def _coerce_finite_float(value: object, *, field_name: str) -> float:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric") from exc
    if not amount.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return float(amount)


def render_summary_csv(payload: Any) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "provider",
            "opportunity_monthly_usd",
            "realized_monthly_usd",
            "open_recommendations",
            "applied_recommendations",
            "pending_remediations",
            "completed_remediations",
        ]
    )
    for item in payload.breakdown:
        writer.writerow(
            [
                sanitize_csv_cell(item.provider),
                f"{_coerce_finite_float(item.opportunity_monthly_usd, field_name='breakdown_opportunity_monthly_usd'):.2f}",
                f"{_coerce_finite_float(item.realized_monthly_usd, field_name='breakdown_realized_monthly_usd'):.2f}",
                item.open_recommendations,
                item.applied_recommendations,
                item.pending_remediations,
                item.completed_remediations,
            ]
        )
    writer.writerow([])
    writer.writerow(
        [
            "TOTAL",
            f"{_coerce_finite_float(payload.opportunity_monthly_usd, field_name='opportunity_monthly_usd'):.2f}",
            f"{_coerce_finite_float(payload.realized_monthly_usd, field_name='realized_monthly_usd'):.2f}",
            payload.open_recommendations,
            payload.applied_recommendations,
            payload.pending_remediations,
            payload.completed_remediations,
        ]
    )
    return out.getvalue()


def render_drilldown_csv(payload: Any) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            sanitize_csv_cell(payload.dimension),
            "opportunity_monthly_usd",
            "realized_monthly_usd",
            "open_recommendations",
            "applied_recommendations",
            "pending_remediations",
            "completed_remediations",
        ]
    )
    for item in payload.buckets:
        writer.writerow(
            [
                sanitize_csv_cell(item.key),
                f"{_coerce_finite_float(item.opportunity_monthly_usd, field_name='bucket_opportunity_monthly_usd'):.2f}",
                f"{_coerce_finite_float(item.realized_monthly_usd, field_name='bucket_realized_monthly_usd'):.2f}",
                item.open_recommendations,
                item.applied_recommendations,
                item.pending_remediations,
                item.completed_remediations,
            ]
        )
    writer.writerow([])
    writer.writerow(
        [
            "TOTAL",
            f"{_coerce_finite_float(payload.opportunity_monthly_usd, field_name='opportunity_monthly_usd'):.2f}",
            f"{_coerce_finite_float(payload.realized_monthly_usd, field_name='realized_monthly_usd'):.2f}",
            sum(bucket.open_recommendations for bucket in payload.buckets),
            sum(bucket.applied_recommendations for bucket in payload.buckets),
            sum(bucket.pending_remediations for bucket in payload.buckets),
            sum(bucket.completed_remediations for bucket in payload.buckets),
        ]
    )
    return out.getvalue()
