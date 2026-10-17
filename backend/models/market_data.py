"""
SQLAlchemy ORM models for Data Sources, Ingestion, Prices, Fundamentals, Economic Indicators, and News.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Boolean,
    BigInteger,
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


class DataSource(Base):
    __tablename__ = "data_sources"

    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    source_code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    secret_parameter_name: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    terms_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    license_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('market_data', 'fundamentals', 'news', 'economic', 'broker', 'manual', 'internal')",
            name="ck_data_sources_type",
        ),
    )

    ingestion_runs = relationship("DataIngestionRun", back_populates="data_source")
    prices = relationship("MarketPrice", back_populates="data_source")
    fundamentals = relationship("FundamentalMetric", back_populates="data_source")
    observations = relationship("EconomicObservation", back_populates="data_source")
    articles = relationship("MarketNewsArticle", back_populates="data_source")
    instrument_mappings = relationship("SourceInstrumentMapping", back_populates="data_source")


class DataIngestionRun(Base):
    __tablename__ = "data_ingestion_runs"

    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    data_type: Mapped[str] = mapped_column(String(60), nullable=False)
    run_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running", server_default="running"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    records_seen: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    records_inserted: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    records_updated: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        UniqueConstraint("ingestion_run_id", "data_source_id", name="uq_ingestion_run_source"),
        CheckConstraint(
            "run_status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled')",
            name="ck_ingestion_runs_status",
        ),
        CheckConstraint("records_seen >= 0", name="ck_ingestion_runs_records_seen"),
        CheckConstraint("records_inserted >= 0", name="ck_ingestion_runs_records_inserted"),
        CheckConstraint("records_updated >= 0", name="ck_ingestion_runs_records_updated"),
        CheckConstraint("finished_at IS NULL OR finished_at >= started_at", name="ck_ingestion_runs_dates"),
        Index("ix_ingestion_source_time", "data_source_id", text("started_at DESC")),
        Index("ix_ingestion_status_time", "run_status", text("started_at DESC")),
    )

    data_source = relationship("DataSource", back_populates="ingestion_runs")
    errors = relationship("DataIngestionError", back_populates="ingestion_run", cascade="all, delete-orphan")


class DataIngestionError(Base):
    __tablename__ = "data_ingestion_errors"

    ingestion_error_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_ingestion_runs.ingestion_run_id", ondelete="CASCADE"), nullable=False
    )
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    record_reference: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    is_retryable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    error_details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_ingestion_errors_run_time", "ingestion_run_id", text("occurred_at DESC")),
    )

    ingestion_run = relationship("DataIngestionRun", back_populates="errors")


class SourceInstrumentMapping(Base):
    __tablename__ = "source_instrument_mappings"

    source_instrument_mapping_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instrument_listings.listing_id", ondelete="RESTRICT"), nullable=False
    )
    external_instrument_code: Mapped[str] = mapped_column(String(200), nullable=False)
    external_symbol: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("data_source_id", "external_instrument_code", name="uq_source_external_instrument"),
        UniqueConstraint("data_source_id", "listing_id", name="uq_source_listing_mapping"),
        Index("ix_source_instrument_listing", "listing_id", "data_source_id"),
    )

    data_source = relationship("DataSource", back_populates="instrument_mappings")
    listing = relationship("InstrumentListing", back_populates="source_mappings")


class MarketPrice(Base):
    __tablename__ = "market_prices"

    market_price_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instrument_listings.listing_id", ondelete="RESTRICT"), nullable=False
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    open_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    high_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    low_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    close_price: Mapped[float] = mapped_column(Numeric(20, 6), nullable=False)
    adjusted_close_price: Mapped[Optional[float]] = mapped_column(Numeric(20, 6), nullable=True)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    provider_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("listing_id", "price_date", "data_source_id", name="uq_market_price_listing_date_source"),
        ForeignKeyConstraint(
            ["ingestion_run_id", "data_source_id"],
            ["data_ingestion_runs.ingestion_run_id", "data_ingestion_runs.data_source_id"],
            ondelete="RESTRICT",
            name="fk_market_price_ingestion_source",
        ),
        CheckConstraint("close_price >= 0", name="ck_market_prices_close_price"),
        CheckConstraint("adjusted_close_price IS NULL OR adjusted_close_price >= 0", name="ck_market_prices_adj_close"),
        CheckConstraint("volume IS NULL OR volume >= 0", name="ck_market_prices_volume"),
        Index("ix_market_prices_listing_date", "listing_id", text("price_date DESC")),
        Index("ix_market_prices_source_retrieved", "data_source_id", text("retrieved_at DESC")),
    )

    listing = relationship("InstrumentListing", back_populates="prices")
    data_source = relationship("DataSource", back_populates="prices")


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    metric_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    metric_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    metric_name: Mapped[str] = mapped_column(String(180), nullable=False)
    unit_code: Mapped[str] = mapped_column(String(40), nullable=False)
    value_kind: Mapped[str] = mapped_column(String(20), nullable=False, default="numeric", server_default="numeric")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    __table_args__ = (
        CheckConstraint("value_kind IN ('numeric')", name="ck_metric_definitions_value_kind"),
    )

    metrics = relationship("FundamentalMetric", back_populates="definition")


class FundamentalMetric(Base):
    __tablename__ = "fundamental_metrics"

    fundamental_metric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    metric_definition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("metric_definitions.metric_definition_id", ondelete="RESTRICT"), nullable=False
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)
    period_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    currency_code: Mapped[Optional[str]] = mapped_column(CHAR(3), nullable=True)
    reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint(
            "security_id", "metric_definition_id", "period_type", "period_end_date", "data_source_id",
            name="uq_fundamental_fact",
        ),
        ForeignKeyConstraint(
            ["ingestion_run_id", "data_source_id"],
            ["data_ingestion_runs.ingestion_run_id", "data_ingestion_runs.data_source_id"],
            ondelete="RESTRICT",
            name="fk_fundamental_ingestion_source",
        ),
        CheckConstraint(
            "period_type IN ('quarterly', 'annual', 'ttm', 'point_in_time')",
            name="ck_fundamental_metrics_period",
        ),
        Index("ix_fundamentals_security_metric_date", "security_id", "metric_definition_id", text("period_end_date DESC")),
    )

    security = relationship("Security", back_populates="fundamental_metrics")
    definition = relationship("MetricDefinition", back_populates="metrics")
    data_source = relationship("DataSource", back_populates="fundamentals")


class EconomicIndicator(Base):
    __tablename__ = "economic_indicators"

    economic_indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    indicator_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    indicator_name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False, default="IN", server_default="IN")
    unit_code: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'irregular')",
            name="ck_economic_indicators_frequency",
        ),
    )

    observations = relationship("EconomicObservation", back_populates="indicator")


class EconomicObservation(Base):
    __tablename__ = "economic_observations"

    economic_observation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    economic_indicator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("economic_indicators.economic_indicator_id", ondelete="RESTRICT"), nullable=False
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    observation_date: Mapped[date] = mapped_column(Date, nullable=False)
    observation_value: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    release_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("economic_indicator_id", "observation_date", "data_source_id", name="uq_economic_fact"),
        ForeignKeyConstraint(
            ["ingestion_run_id", "data_source_id"],
            ["data_ingestion_runs.ingestion_run_id", "data_ingestion_runs.data_source_id"],
            ondelete="RESTRICT",
            name="fk_economic_ingestion_source",
        ),
        Index("ix_economic_indicator_date", "economic_indicator_id", text("observation_date DESC")),
    )

    indicator = relationship("EconomicIndicator", back_populates="observations")
    data_source = relationship("DataSource", back_populates="observations")


class MarketNewsArticle(Base):
    __tablename__ = "market_news_articles"

    news_article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=False
    )
    ingestion_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    provider_article_id: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    article_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    headline: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(8, 5), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    licensing_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint("data_source_id", "provider_article_id", name="uq_news_provider_article"),
        ForeignKeyConstraint(
            ["ingestion_run_id", "data_source_id"],
            ["data_ingestion_runs.ingestion_run_id", "data_ingestion_runs.data_source_id"],
            ondelete="RESTRICT",
            name="fk_news_ingestion_source",
        ),
        CheckConstraint("sentiment_score BETWEEN -1 AND 1", name="ck_news_sentiment_score"),
        CheckConstraint(
            "sentiment_label IN ('negative', 'neutral', 'positive', 'mixed')",
            name="ck_news_sentiment_label",
        ),
        Index("uq_news_source_url", "data_source_id", "article_url", unique=True, postgresql_where=text("article_url IS NOT NULL")),
        Index("ix_news_published_at", text("published_at DESC")),
        Index("ix_news_source_retrieved", "data_source_id", text("retrieved_at DESC")),
    )

    data_source = relationship("DataSource", back_populates="articles")
    security_links = relationship("NewsArticleSecurity", back_populates="article", cascade="all, delete-orphan")


class NewsArticleSecurity(Base):
    __tablename__ = "news_article_securities"

    news_article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_news_articles.news_article_id", ondelete="CASCADE"), primary_key=True
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), primary_key=True
    )
    relevance_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 5), nullable=True)
    link_method: Mapped[str] = mapped_column(
        String(30), nullable=False, default="provider", server_default="provider"
    )

    __table_args__ = (
        CheckConstraint("relevance_score IS NULL OR relevance_score BETWEEN 0 AND 1", name="ck_news_relevance_score"),
        CheckConstraint(
            "link_method IN ('provider', 'symbol_match', 'entity_match', 'manual', 'model')",
            name="ck_news_link_method",
        ),
        Index("ix_news_security", "security_id", "news_article_id"),
    )

    article = relationship("MarketNewsArticle", back_populates="security_links")
    security = relationship("Security", back_populates="news_associations")
