from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, Dict, Any
from sqlalchemy import (
    String,
    DateTime,
    Numeric,
    Boolean,
    JSON,
    ForeignKey,
    Uuid as PG_UUID,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class PricingPlan(Base):
    """
    Database-driven pricing plans.
    Allows updating prices and features without code deployment.
    """

    __tablename__ = "pricing_plans"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(50), primary_key=True
    )  # e.g. 'starter', 'growth'
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    # Store features and limits as JSONB for flexibility
    features: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )
    limits: Mapped[Dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=dict
    )

    # UI Metadata
    display_features: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), default=list
    )
    cta_text: Mapped[str] = mapped_column(String(50), default="Get Started")
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Timestamps are inherited from Base


class ExchangeRate(Base):
    """
    Stores exchange rates for currency conversion (e.g., USD to NGN).
    """

    __tablename__ = "exchange_rates"
    __table_args__ = {"extend_existing": True}

    from_currency: Mapped[str] = mapped_column(
        String(3), primary_key=True, default="USD"
    )
    to_currency: Mapped[str] = mapped_column(String(3), primary_key=True, default="NGN")

    rate: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), default="exchangerate-api")

    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class TenantSubscription(Base):
    """
    Formalized subscription record for Paystack integration.
    Includes dunning tracking and reusable auth codes.
    """

    __tablename__ = "tenant_subscriptions"
    __table_args__ = (
        UniqueConstraint(
            "last_charge_reference",
            name="uq_tenant_subscriptions_last_charge_reference",
        ),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Paystack IDs
    paystack_customer_code: Mapped[Optional[str]] = mapped_column(String(255))
    paystack_subscription_code: Mapped[Optional[str]] = mapped_column(String(255))
    paystack_email_token: Mapped[Optional[str]] = mapped_column(String(255))
    paystack_auth_code: Mapped[Optional[str]] = mapped_column(String(255))

    tier: Mapped[str] = mapped_column(String(20), default="free")
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Billing & Dunning
    next_payment_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    billing_currency: Mapped[str] = mapped_column(String(3), default="NGN")
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly")
    last_charge_amount_subunits: Mapped[Optional[int]] = mapped_column(Numeric(20, 0))
    last_charge_fx_rate: Mapped[Optional[float]] = mapped_column(Numeric(12, 6))
    last_charge_fx_provider: Mapped[Optional[str]] = mapped_column(String(50))
    last_charge_reference: Mapped[Optional[str]] = mapped_column(String(255))
    last_charge_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dunning_attempts: Mapped[int] = mapped_column(Numeric(2, 0), default=0)
    last_dunning_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    dunning_next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LLMProviderPricing(Base):
    """
    Dynamic pricing for LLM providers and models.
    Transition from hardcoded 2026 rates to DB-driven costs.
    """

    __tablename__ = "llm_provider_pricing"
    __table_args__ = {"extend_existing": True}

    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(50), index=True)  # groq, openai, etc.
    model: Mapped[str] = mapped_column(String(100), index=True)

    input_cost_per_million: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )
    output_cost_per_million: Mapped[float] = mapped_column(
        Numeric(10, 4), nullable=False
    )

    free_tier_tokens: Mapped[int] = mapped_column(Numeric(20, 0), default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CloudResourcePricing(Base):
    """
    Persisted cloud pricing catalog used by optimization and reporting logic.
    """

    __tablename__ = "cloud_resource_pricing"
    __table_args__ = (
        UniqueConstraint(
            "provider",
            "resource_type",
            "resource_size",
            "region",
            name="uq_cloud_resource_pricing_catalog_key",
        ),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    resource_size: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    region: Mapped[str] = mapped_column(String(64), index=True, nullable=False, default="global")
    hourly_rate_usd: Mapped[float] = mapped_column(Numeric(12, 6), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="default_catalog")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pricing_metadata: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
    )
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# --- PACKAGING MODELS ---
class ManagedSpendSnapshot(Base):
    __tablename__ = "managed_spend_snapshots"
    __table_args__ = {"extend_existing": True}
    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    account_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    gross_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    provider_discounts: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    net_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    source_reference: Mapped[Optional[str]] = mapped_column(String(255))
    inclusion_flags: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class OptimizationCreditLedger(Base):
    __tablename__ = "optimization_credit_ledger"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_optimization_credit_idempotency"), {"extend_existing": True})
    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    starting_balance: Mapped[int] = mapped_column(Numeric(12, 0), nullable=False)
    action_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(), nullable=True)
    credits_consumed: Mapped[int] = mapped_column(Numeric(10, 0), nullable=False)
    action_weight: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=1)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[Optional[str]] = mapped_column(String(20), default="completed", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

class AddOnCatalog(Base):
    __tablename__ = "addon_catalog"
    __table_args__ = {"extend_existing": True}
    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))
    addon_type: Mapped[str] = mapped_column(String(50), nullable=False)
    price_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    price_annual_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    credit_amount: Mapped[Optional[int]] = mapped_column(Numeric(12, 0))
    connector_limit: Mapped[Optional[int]] = mapped_column(Numeric(10, 0))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class EnterpriseContractOverride(Base):
    __tablename__ = "enterprise_contract_overrides"
    __table_args__ = {"extend_existing": True}
    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    custom_managed_spend_commitment: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    custom_credit_commitment: Mapped[Optional[int]] = mapped_column(Numeric(12, 0))
    custom_retention_days: Mapped[Optional[int]] = mapped_column(Numeric(12, 0))
    custom_cap_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    deployment_model: Mapped[Optional[str]] = mapped_column(String(50))
    data_residency: Mapped[Optional[str]] = mapped_column(String(10))
    support_sla: Mapped[Optional[str]] = mapped_column(String(100))
    custom_addons: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    contract_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    signed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class SavingsShareCalculation(Base):
    __tablename__ = "savings_share_calculations"
    __table_args__ = {"extend_existing": True}
    id: Mapped[UUID] = mapped_column(PG_UUID(), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(PG_UUID(), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    baseline_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    baseline_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recommendation_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID())
    opted_in_scope: Mapped[str] = mapped_column(String(100), nullable=False)
    normalized_baseline_spend: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    normalized_actual_spend: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    excluded_adjustments: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    validated_savings: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    share_percentage: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    cap_amount: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    calculated_share: Mapped[Optional[float]] = mapped_column(Numeric(14, 2))
    dispute_status: Mapped[Optional[str]] = mapped_column(String(20), default="pending", index=True)
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
