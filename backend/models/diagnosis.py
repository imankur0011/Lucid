"""
SQLAlchemy ORM models for Existing Portfolios, Holdings, Diagnoses, and Rebalancing Suggestions.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
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


class ExistingPortfolio(Base):
    __tablename__ = "existing_portfolios"

    existing_portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    portfolio_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual", server_default="manual"
    )
    source_name: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, default=date.today, server_default=text("CURRENT_DATE")
    )
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    portfolio_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("existing_portfolio_id", "user_id", name="uq_existing_portfolio_id_user"),
        CheckConstraint(
            "source_type IN ('manual', 'file_import', 'broker_import')",
            name="ck_existing_portfolios_source",
        ),
        CheckConstraint(
            "portfolio_status IN ('active', 'archived')",
            name="ck_existing_portfolios_status",
        ),
        Index("ix_existing_portfolios_user_date", "user_id", text("as_of_date DESC")),
    )

    user = relationship("AppUser", back_populates="existing_portfolios")
    holdings = relationship("ExistingPortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    diagnoses = relationship("PortfolioDiagnosis", back_populates="existing_portfolio")


class ExistingPortfolioHolding(Base):
    __tablename__ = "existing_portfolio_holdings"

    existing_portfolio_holding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    existing_portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("existing_portfolios.existing_portfolio_id", ondelete="CASCADE"), nullable=False
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    average_purchase_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    market_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    source_detail: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (
        UniqueConstraint("existing_portfolio_id", "security_id", name="uq_existing_holding_security"),
        ForeignKeyConstraint(
            ["listing_id", "security_id"],
            ["instrument_listings.listing_id", "instrument_listings.security_id"],
            ondelete="RESTRICT",
            name="fk_existing_holding_listing_security",
        ),
        CheckConstraint("quantity > 0", name="ck_existing_holdings_quantity"),
        CheckConstraint(
            "average_purchase_price IS NULL OR average_purchase_price >= 0",
            name="ck_existing_holdings_avg_price",
        ),
        CheckConstraint(
            "market_value IS NULL OR market_value >= 0",
            name="ck_existing_holdings_market_value",
        ),
        Index("ix_existing_holdings_security", "security_id"),
    )

    portfolio = relationship("ExistingPortfolio", back_populates="holdings")
    security = relationship("Security")
    listing = relationship(
        "InstrumentListing",
        foreign_keys=[listing_id],
        primaryjoin="ExistingPortfolioHolding.listing_id == InstrumentListing.listing_id",
    )


class PortfolioDiagnosis(Base):
    __tablename__ = "portfolio_diagnoses"

    portfolio_diagnosis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    existing_portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("existing_portfolios.existing_portfolio_id", ondelete="RESTRICT"), nullable=False
    )
    diagnosis_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed", server_default="completed"
    )
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    market_context_as_of: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "diagnosis_status IN ('queued', 'running', 'completed', 'failed')",
            name="ck_diagnoses_status",
        ),
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at", name="ck_diagnoses_dates"),
        Index("ix_diagnoses_existing_portfolio_time", "existing_portfolio_id", text("started_at DESC")),
    )

    existing_portfolio = relationship("ExistingPortfolio", back_populates="diagnoses")
    rebalance_suggestions = relationship("RebalanceSuggestion", back_populates="diagnosis", cascade="all, delete-orphan")


class RebalanceSuggestion(Base):
    __tablename__ = "rebalance_suggestions"

    rebalance_suggestion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_diagnosis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_diagnoses.portfolio_diagnosis_id", ondelete="RESTRICT"), nullable=False
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    suggested_action: Mapped[str] = mapped_column(String(10), nullable=False)
    current_quantity: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    target_quantity: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    target_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    change_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_diagnosis_id", "security_id", name="uq_rebalance_security_per_diagnosis"),
        CheckConstraint("suggested_action IN ('buy', 'sell', 'hold')", name="ck_rebalance_action"),
        CheckConstraint("current_quantity IS NULL OR current_quantity >= 0", name="ck_rebalance_cur_qty"),
        CheckConstraint("target_quantity IS NULL OR target_quantity >= 0", name="ck_rebalance_tgt_qty"),
        CheckConstraint("current_value IS NULL OR current_value >= 0", name="ck_rebalance_cur_val"),
        CheckConstraint("target_value IS NULL OR target_value >= 0", name="ck_rebalance_tgt_val"),
    )

    diagnosis = relationship("PortfolioDiagnosis", back_populates="rebalance_suggestions")
    security = relationship("Security")
