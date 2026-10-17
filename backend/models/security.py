"""
SQLAlchemy ORM models for Companies, Exchanges, Sectors, Industries, Securities, Listings, and User Preferences.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from datetime import datetime, date
import uuid

from backend.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    legal_name: Mapped[str] = mapped_column(String(240), nullable=False)
    common_name: Mapped[Optional[str]] = mapped_column(String(180), nullable=True)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False, default="IN", server_default="IN")
    website_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (Index("ix_companies_legal_name", func.lower(legal_name)),)

    # Relationships
    industries = relationship("CompanyIndustry", back_populates="company", cascade="all, delete-orphan")
    securities = relationship("Security", back_populates="company")


class Exchange(Base):
    __tablename__ = "exchanges"

    exchange_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    exchange_code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    exchange_name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False, default="IN", server_default="IN")
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    listings = relationship("InstrumentListing", back_populates="exchange")


class Sector(Base):
    __tablename__ = "sectors"

    sector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    sector_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    sector_name: Mapped[str] = mapped_column(String(120), nullable=False)
    taxonomy_source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    industries = relationship("Industry", back_populates="sector")
    user_preferences = relationship("UserSectorPreference", back_populates="sector")


class Industry(Base):
    __tablename__ = "industries"

    industry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    sector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.sector_id", ondelete="RESTRICT"), nullable=False
    )
    industry_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    industry_name: Mapped[str] = mapped_column(String(160), nullable=False)
    taxonomy_source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (Index("ix_industries_sector", "sector_id", "industry_name"),)

    sector = relationship("Sector", back_populates="industries")
    company_mappings = relationship("CompanyIndustry", back_populates="industry")


class CompanyIndustry(Base):
    __tablename__ = "company_industries"

    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.company_id", ondelete="CASCADE"), primary_key=True
    )
    industry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("industries.industry_id", ondelete="RESTRICT"), primary_key=True
    )
    effective_from: Mapped[date] = mapped_column(
        Date, primary_key=True, default=date.today, server_default=text("CURRENT_DATE")
    )
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    classification_source: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    __table_args__ = (
        CheckConstraint("effective_to IS NULL OR effective_to >= effective_from", name="ck_company_industries_dates"),
        Index("ix_company_industries_industry", "industry_id", "company_id"),
    )

    company = relationship("Company", back_populates="industries")
    industry = relationship("Industry", back_populates="company_mappings")


class Security(Base):
    __tablename__ = "securities"

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.company_id", ondelete="RESTRICT"), nullable=True
    )
    security_name: Mapped[str] = mapped_column(String(240), nullable=False)
    isin: Mapped[Optional[str]] = mapped_column(CHAR(12), nullable=True)
    security_type: Mapped[str] = mapped_column(String(30), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    security_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "security_type IN ('stock', 'etf', 'index', 'mutual_fund', 'bond', 'other')",
            name="ck_securities_type",
        ),
        CheckConstraint(
            "security_status IN ('active', 'inactive', 'matured', 'delisted')",
            name="ck_securities_status",
        ),
        Index("ix_securities_company", "company_id"),
        Index("ix_securities_type_status", "security_type", "security_status"),
        Index("uq_securities_isin", isin, unique=True, postgresql_where=text("isin IS NOT NULL")),
    )

    company = relationship("Company", back_populates="securities")
    listings = relationship("InstrumentListing", back_populates="security", cascade="all, delete-orphan")
    fundamental_metrics = relationship("FundamentalMetric", back_populates="security")
    news_associations = relationship("NewsArticleSecurity", back_populates="security")
    user_preferences = relationship("UserSecurityPreference", back_populates="security")


class InstrumentListing(Base):
    __tablename__ = "instrument_listings"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    exchange_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("exchanges.exchange_id", ondelete="RESTRICT"), nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(80), nullable=False)
    trading_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    listed_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delisted_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("exchange_id", "symbol", name="uq_listing_exchange_symbol"),
        UniqueConstraint("listing_id", "security_id", name="uq_listing_id_security"),
        CheckConstraint(
            "trading_status IN ('active', 'suspended', 'delisted', 'inactive')",
            name="ck_instrument_listings_status",
        ),
        CheckConstraint(
            "delisted_on IS NULL OR listed_on IS NULL OR delisted_on >= listed_on",
            name="ck_instrument_listings_dates",
        ),
        Index("ix_listings_security", "security_id"),
        Index("ix_listings_status", "trading_status", "exchange_id"),
    )

    security = relationship("Security", back_populates="listings")
    exchange = relationship("Exchange", back_populates="listings")
    prices = relationship("MarketPrice", back_populates="listing")
    source_mappings = relationship("SourceInstrumentMapping", back_populates="listing")


class UserSectorPreference(Base):
    __tablename__ = "user_sector_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    sector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sectors.sector_id", ondelete="RESTRICT"), primary_key=True
    )
    preference_type: Mapped[str] = mapped_column(String(12), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("preference_type IN ('include', 'exclude')", name="ck_user_sector_preference_type"),
    )

    user = relationship("AppUser")
    sector = relationship("Sector", back_populates="user_preferences")


class UserSecurityPreference(Base):
    __tablename__ = "user_security_preferences"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), primary_key=True
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), primary_key=True
    )
    preference_type: Mapped[str] = mapped_column(String(12), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("preference_type IN ('include', 'exclude')", name="ck_user_security_preference_type"),
    )

    user = relationship("AppUser")
    security = relationship("Security", back_populates="user_preferences")
