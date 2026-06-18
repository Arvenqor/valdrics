from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, DateTime, Boolean, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.db.base import Base


class CustomerApiKey(Base):
    """Customer-facing scoped API key for programmatic access."""

    __tablename__ = "customer_api_keys"
    __table_args__ = (
        UniqueConstraint("key_prefix", name="uq_customer_api_key_prefix"),
        {"extend_existing": True},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="User-assigned key label")
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False, comment="First 8-12 chars of raw key for display")
    encrypted_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=False, comment="Fernet-encrypted raw key")
    key_fingerprint: Mapped[Optional[str]] = mapped_column(String(64), comment="SHA-256 fingerprint for rotation matching")
    scopes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    allowed_ips: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    rate_limit_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="standard")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[Optional[UUID]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    key_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
