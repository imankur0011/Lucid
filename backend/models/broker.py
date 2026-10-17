"""
SQLAlchemy ORM models for Broker Providers, User Broker Accounts, Orders, Executions, and Performance Snapshots.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Boolean,
    Numeric,
    Text,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    ForeignKeyConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, Dict, Any, List
from datetime import datetime, date
import uuid

from backend.database.base import Base


class BrokerProvider(Base):
    __tablename__ = "broker_providers"

    broker_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    provider_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    provider_name: Mapped[str] = mapped_column(String(160), nullable=False)
    developer_docs_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    accounts = relationship("UserBrokerAccount", back_populates="provider")


class UserBrokerAccount(Base):
    __tablename__ = "user_broker_accounts"

    user_broker_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="RESTRICT"), nullable=False
    )
    broker_provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("broker_providers.broker_provider_id", ondelete="RESTRICT"), nullable=False
    )
    external_account_reference: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    account_label: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    connection_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", server_default="pending"
    )
    granted_permissions: Mapped[List[Any]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    secret_reference: Mapped[Optional[str]] = mapped_column(String(400), nullable=True)
    connected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "broker_provider_id", "external_account_reference"),
        CheckConstraint(
            "connection_status IN ('pending', 'connected', 'expired', 'revoked', 'error')",
            name="ck_user_broker_accounts_status",
        ),
        Index("ix_user_broker_accounts_user", "user_id", "connection_status"),
    )

    user = relationship("AppUser")
    provider = relationship("BrokerProvider", back_populates="accounts")
    orders = relationship("BrokerOrder", back_populates="account")


class BrokerOrder(Base):
    __tablename__ = "broker_orders"

    broker_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_broker_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_broker_accounts.user_broker_account_id", ondelete="RESTRICT"), nullable=False
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    provider_order_reference: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    order_quantity: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    limit_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    order_status: Mapped[str] = mapped_column(String(24), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_broker_account_id", "provider_order_reference"),
        ForeignKeyConstraint(
            ["listing_id", "security_id"],
            ["instrument_listings.listing_id", "instrument_listings.security_id"],
            ondelete="RESTRICT",
            name="fk_broker_order_listing_security",
        ),
        CheckConstraint("side IN ('buy', 'sell')", name="ck_broker_orders_side"),
        CheckConstraint("order_type IN ('market', 'limit', 'stop', 'stop_limit', 'other')", name="ck_broker_orders_type"),
        CheckConstraint("order_quantity > 0", name="ck_broker_orders_quantity"),
        CheckConstraint("limit_price IS NULL OR limit_price >= 0", name="ck_broker_orders_limit_price"),
        CheckConstraint(
            "order_status IN ('created', 'submitted', 'accepted', 'partially_filled', 'filled', 'cancelled', 'rejected', 'expired', 'unknown')",
            name="ck_broker_orders_status",
        ),
        Index("ix_broker_orders_account_time", "user_broker_account_id", text("created_at DESC")),
        Index("ix_broker_orders_status", "order_status", text("last_updated_at DESC")),
    )

    account = relationship("UserBrokerAccount", back_populates="orders")
    security = relationship("Security")
    listing = relationship(
        "InstrumentListing",
        foreign_keys=[listing_id],
        primaryjoin="BrokerOrder.listing_id == InstrumentListing.listing_id",
    )
    events = relationship("BrokerOrderEvent", back_populates="order", cascade="all, delete-orphan")
    executions = relationship("BrokerExecution", back_populates="order", cascade="all, delete-orphan")


class BrokerOrderEvent(Base):
    __tablename__ = "broker_order_events"

    broker_order_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    broker_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("broker_orders.broker_order_id", ondelete="RESTRICT"), nullable=False
    )
    event_status: Mapped[str] = mapped_column(String(24), nullable=False)
    event_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_event_reference: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    event_payload: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("broker_order_id", "provider_event_reference"),
        Index("ix_broker_order_events_order_time", "broker_order_id", text("occurred_at DESC")),
    )

    order = relationship("BrokerOrder", back_populates="events")


class BrokerExecution(Base):
    __tablename__ = "broker_executions"

    broker_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    broker_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("broker_orders.broker_order_id", ondelete="RESTRICT"), nullable=False
    )
    provider_execution_reference: Mapped[Optional[str]] = mapped_column(String(240), nullable=True)
    executed_quantity: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    execution_price: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fees_amount: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")

    __table_args__ = (
        UniqueConstraint("broker_order_id", "provider_execution_reference"),
        CheckConstraint("executed_quantity > 0", name="ck_broker_exec_quantity"),
        CheckConstraint("execution_price >= 0", name="ck_broker_exec_price"),
        CheckConstraint("fees_amount IS NULL OR fees_amount >= 0", name="ck_broker_exec_fees"),
        Index("ix_broker_executions_order_time", "broker_order_id", text("executed_at DESC")),
    )

    order = relationship("BrokerOrder", back_populates="executions")


class PortfolioPerformanceSnapshot(Base):
    __tablename__ = "portfolio_performance_snapshots"

    performance_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    valuation_amount: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    return_since_previous_pct: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    cumulative_return_pct: Mapped[Optional[float]] = mapped_column(Numeric(12, 6), nullable=True)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_version_id", "snapshot_date", "source_type"),
        CheckConstraint("valuation_amount >= 0", name="ck_perf_valuation_amount"),
        CheckConstraint(
            "source_type IN ('simulated', 'user_reported', 'broker_confirmed')",
            name="ck_perf_source_type",
        ),
        Index("ix_performance_snapshot_date", "portfolio_version_id", text("snapshot_date DESC")),
    )

    portfolio_version = relationship("PortfolioVersion")
