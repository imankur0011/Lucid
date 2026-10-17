"""
SQLAlchemy ORM models for Portfolios, Generation Requests, Strategies, Decisions, Validation, Scenarios, and Explanations.
"""

from sqlalchemy import (
    Column,
    String,
    CHAR,
    Boolean,
    Integer,
    Numeric,
    Text,
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
from datetime import datetime
import uuid

from backend.database.base import Base


class InvestorPortfolio(Base):
    __tablename__ = "investor_portfolios"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("app_users.user_id", ondelete="CASCADE"), nullable=False
    )
    portfolio_name: Mapped[str] = mapped_column(String(160), nullable=False)
    portfolio_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft", server_default="draft"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_id", "user_id", name="uq_portfolio_id_user"),
        CheckConstraint("portfolio_status IN ('draft', 'active', 'archived')", name="ck_investor_portfolios_status"),
        Index("ix_portfolios_user_updated", "user_id", text("updated_at DESC")),
    )

    user = relationship("AppUser", back_populates="portfolios")
    generation_requests = relationship(
        "PortfolioGenerationRequest",
        back_populates="portfolio",
        primaryjoin="InvestorPortfolio.portfolio_id == PortfolioGenerationRequest.portfolio_id",
        foreign_keys="[PortfolioGenerationRequest.portfolio_id]",
    )
    versions = relationship(
        "PortfolioVersion",
        back_populates="portfolio",
        primaryjoin="InvestorPortfolio.portfolio_id == PortfolioVersion.portfolio_id",
        foreign_keys="[PortfolioVersion.portfolio_id]",
    )


class PortfolioGenerationRequest(Base):
    __tablename__ = "portfolio_generation_requests"

    generation_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    risk_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    request_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="create", server_default="create"
    )
    request_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="queued", server_default="queued"
    )
    user_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_amount: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    investment_horizon_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    normalized_inputs: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    investor_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    market_context_as_of: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("generation_request_id", "portfolio_id", name="uq_generation_request_portfolio"),
        ForeignKeyConstraint(
            ["portfolio_id", "user_id"],
            ["investor_portfolios.portfolio_id", "investor_portfolios.user_id"],
            ondelete="RESTRICT",
            name="fk_generation_portfolio_owner",
        ),
        ForeignKeyConstraint(
            ["goal_id", "user_id"],
            ["financial_goals.goal_id", "financial_goals.user_id"],
            ondelete="RESTRICT",
            name="fk_generation_goal_owner",
        ),
        ForeignKeyConstraint(
            ["risk_assessment_id", "user_id"],
            ["risk_assessments.risk_assessment_id", "risk_assessments.user_id"],
            ondelete="RESTRICT",
            name="fk_generation_risk_owner",
        ),
        CheckConstraint("request_type IN ('create', 'revise', 'scenario')", name="ck_generation_requests_type"),
        CheckConstraint(
            "request_status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_generation_requests_status",
        ),
        CheckConstraint("requested_amount > 0", name="ck_generation_requests_amount"),
        CheckConstraint(
            "investment_horizon_months IS NULL OR investment_horizon_months > 0",
            name="ck_generation_requests_horizon",
        ),
        CheckConstraint(
            "completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at",
            name="ck_generation_requests_dates",
        ),
        Index("ix_generation_user_time", "user_id", text("created_at DESC")),
        Index("ix_generation_status_time", "request_status", text("created_at DESC")),
        Index("ix_generation_portfolio_time", "portfolio_id", text("created_at DESC")),
    )

    portfolio = relationship(
        "InvestorPortfolio",
        foreign_keys=[portfolio_id],
        primaryjoin="PortfolioGenerationRequest.portfolio_id == InvestorPortfolio.portfolio_id",
        back_populates="generation_requests",
    )
    versions = relationship(
        "PortfolioVersion",
        back_populates="generation_request",
        primaryjoin="PortfolioGenerationRequest.generation_request_id == PortfolioVersion.generation_request_id",
        foreign_keys="[PortfolioVersion.generation_request_id]",
    )


class StrategyDefinition(Base):
    __tablename__ = "strategy_definitions"

    strategy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    strategy_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    strategy_name: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    versions = relationship("StrategyVersion", back_populates="strategy")


class StrategyVersion(Base):
    __tablename__ = "strategy_versions"

    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    strategy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategy_definitions.strategy_id", ondelete="RESTRICT"), nullable=False
    )
    version_label: Mapped[str] = mapped_column(String(80), nullable=False)
    optimizer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    implementation_revision: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    configuration: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    constraint_set_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("strategy_id", "version_label", name="uq_strategy_version"),
    )

    strategy = relationship("StrategyDefinition", back_populates="versions")
    portfolio_versions = relationship("PortfolioVersion", back_populates="strategy_version")


class PortfolioVersion(Base):
    __tablename__ = "portfolio_versions"

    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    generation_request_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    strategy_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategy_versions.strategy_version_id", ondelete="RESTRICT"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    version_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="generated", server_default="generated"
    )
    investment_amount: Mapped[float] = mapped_column(Numeric(20, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR", server_default="INR")
    investment_horizon_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    risk_category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    expected_return_pct: Mapped[Optional[float]] = mapped_column(Numeric(9, 4), nullable=True)
    expected_volatility_pct: Mapped[Optional[float]] = mapped_column(Numeric(9, 4), nullable=True)
    diversification_score: Mapped[Optional[float]] = mapped_column(Numeric(8, 4), nullable=True)
    market_context_as_of: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    generation_context: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_id", "version_number", name="uq_portfolio_version_number"),
        UniqueConstraint("portfolio_version_id", "portfolio_id", name="uq_version_id_portfolio"),
        ForeignKeyConstraint(
            ["generation_request_id", "portfolio_id"],
            ["portfolio_generation_requests.generation_request_id", "portfolio_generation_requests.portfolio_id"],
            ondelete="RESTRICT",
            name="fk_version_request_portfolio",
        ),
        CheckConstraint("version_number > 0", name="ck_portfolio_versions_number"),
        CheckConstraint(
            "version_status IN ('generated', 'reviewed', 'accepted', 'rejected', 'superseded', 'archived')",
            name="ck_portfolio_versions_status",
        ),
        CheckConstraint("investment_amount > 0", name="ck_portfolio_versions_amount"),
        CheckConstraint(
            "investment_horizon_months IS NULL OR investment_horizon_months > 0",
            name="ck_portfolio_versions_horizon",
        ),
        CheckConstraint(
            "risk_category IS NULL OR risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive')",
            name="ck_portfolio_versions_risk",
        ),
        CheckConstraint(
            "diversification_score IS NULL OR (diversification_score BETWEEN 0 AND 100)",
            name="ck_portfolio_versions_diversification",
        ),
        Index("ix_portfolio_versions_recent", "portfolio_id", text("version_number DESC")),
        Index("ix_portfolio_versions_generated", text("generated_at DESC")),
    )

    portfolio = relationship(
        "InvestorPortfolio",
        foreign_keys=[portfolio_id],
        primaryjoin="PortfolioVersion.portfolio_id == InvestorPortfolio.portfolio_id",
        back_populates="versions",
    )
    generation_request = relationship(
        "PortfolioGenerationRequest",
        foreign_keys=[generation_request_id],
        primaryjoin="PortfolioVersion.generation_request_id == PortfolioGenerationRequest.generation_request_id",
        back_populates="versions",
    )
    strategy_version = relationship("StrategyVersion", back_populates="portfolio_versions")
    decisions = relationship("PortfolioSecurityDecision", back_populates="portfolio_version", cascade="all, delete-orphan")
    constraints = relationship("PortfolioVersionConstraint", back_populates="portfolio_version", cascade="all, delete-orphan")
    explanations = relationship("RecommendationExplanation", back_populates="portfolio_version", cascade="all, delete-orphan")
    validation_runs = relationship("PortfolioValidationRun", back_populates="portfolio_version", cascade="all, delete-orphan")
    scenarios = relationship("PortfolioScenario", back_populates="portfolio_version", cascade="all, delete-orphan")


class PortfolioSecurityDecision(Base):
    __tablename__ = "portfolio_security_decisions"

    decision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=False
    )
    listing_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    decision_status: Mapped[str] = mapped_column(String(20), nullable=False)
    target_weight_pct: Mapped[Optional[float]] = mapped_column(Numeric(9, 6), nullable=True)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_version_id", "security_id", name="uq_version_security"),
        UniqueConstraint("decision_id", "portfolio_version_id", name="uq_decision_version"),
        ForeignKeyConstraint(
            ["listing_id", "security_id"],
            ["instrument_listings.listing_id", "instrument_listings.security_id"],
            ondelete="RESTRICT",
            name="fk_decision_listing_security",
        ),
        CheckConstraint("decision_status IN ('selected', 'excluded', 'watchlist')", name="ck_security_decisions_status"),
        CheckConstraint(
            "(decision_status = 'selected' AND target_weight_pct IS NOT NULL AND target_weight_pct > 0 AND target_weight_pct <= 100) OR "
            "(decision_status IN ('excluded', 'watchlist') AND target_weight_pct IS NULL)",
            name="ck_security_decisions_weights",
        ),
        Index("ix_decisions_security", "security_id", "portfolio_version_id"),
        Index("ix_decisions_version_status", "portfolio_version_id", "decision_status"),
    )

    portfolio_version = relationship("PortfolioVersion", back_populates="decisions")
    security = relationship("Security")
    listing = relationship(
        "InstrumentListing",
        foreign_keys=[listing_id],
        primaryjoin="PortfolioSecurityDecision.listing_id == InstrumentListing.listing_id",
    )


class PortfolioVersionConstraint(Base):
    __tablename__ = "portfolio_version_constraints"

    portfolio_constraint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    constraint_code: Mapped[str] = mapped_column(String(100), nullable=False)
    operator: Mapped[str] = mapped_column(String(12), nullable=False)
    comparison_value: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    upper_value: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    unit_code: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_version_id", "constraint_code", name="uq_version_constraint"),
        CheckConstraint("operator IN ('<=', '>=', '=', 'between')", name="ck_constraints_operator"),
        CheckConstraint(
            "operator <> 'between' OR (comparison_value IS NOT NULL AND upper_value IS NOT NULL AND comparison_value <= upper_value)",
            name="ck_constraints_between",
        ),
        CheckConstraint("operator = 'between' OR comparison_value IS NOT NULL", name="ck_constraints_comp_val"),
        CheckConstraint("operator = 'between' OR upper_value IS NULL", name="ck_constraints_upper_val"),
        Index("ix_version_constraints_code", "constraint_code", "portfolio_version_id"),
    )

    portfolio_version = relationship("PortfolioVersion", back_populates="constraints")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_sources.data_source_id", ondelete="RESTRICT"), nullable=True
    )
    security_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=True
    )
    market_price_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_prices.market_price_id", ondelete="RESTRICT"), nullable=True
    )
    fundamental_metric_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("fundamental_metrics.fundamental_metric_id", ondelete="RESTRICT"), nullable=True
    )
    economic_observation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("economic_observations.economic_observation_id", ondelete="RESTRICT"), nullable=True
    )
    news_article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("market_news_articles.news_article_id", ondelete="RESTRICT"), nullable=True
    )
    evidence_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    evidence_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_record_reference: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cited_value_snapshot: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        Index("ix_evidence_security_time", "security_id", text("observed_at DESC")),
        Index("ix_evidence_source_time", "data_source_id", text("observed_at DESC")),
    )

    data_source = relationship("DataSource")
    security = relationship("Security")
    explanations = relationship("ExplanationEvidence", back_populates="evidence_item")


class RecommendationExplanation(Base):
    __tablename__ = "recommendation_explanations"

    explanation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    decision_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    explanation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["decision_id", "portfolio_version_id"],
            ["portfolio_security_decisions.decision_id", "portfolio_security_decisions.portfolio_version_id"],
            ondelete="RESTRICT",
            name="fk_explanation_decision_version",
        ),
        CheckConstraint(
            "explanation_type IN ('portfolio', 'selection', 'exclusion', 'risk', 'diversification', 'constraint', 'scenario', 'review')",
            name="ck_explanations_type",
        ),
        Index("ix_explanations_version_order", "portfolio_version_id", "display_order"),
    )

    portfolio_version = relationship("PortfolioVersion", back_populates="explanations")
    decision = relationship(
        "PortfolioSecurityDecision",
        foreign_keys=[decision_id],
        primaryjoin="RecommendationExplanation.decision_id == PortfolioSecurityDecision.decision_id",
    )
    evidence_links = relationship("ExplanationEvidence", back_populates="explanation", cascade="all, delete-orphan")


class ExplanationEvidence(Base):
    __tablename__ = "explanation_evidence"

    explanation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendation_explanations.explanation_id", ondelete="RESTRICT"), primary_key=True
    )
    evidence_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evidence_items.evidence_item_id", ondelete="RESTRICT"), primary_key=True
    )
    relationship_label: Mapped[str] = mapped_column(
        String(40), nullable=False, default="supports", server_default="supports"
    )

    __table_args__ = (
        CheckConstraint(
            "relationship_label IN ('supports', 'contradicts', 'contextualizes')",
            name="ck_explanation_evidence_label",
        ),
        Index("ix_explanation_evidence_evidence", "evidence_item_id"),
    )

    explanation = relationship("RecommendationExplanation", back_populates="evidence_links")
    evidence_item = relationship("EvidenceItem", back_populates="explanations")


class PortfolioValidationRun(Base):
    __tablename__ = "portfolio_validation_runs"

    validation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    rule_set_version: Mapped[str] = mapped_column(String(100), nullable=False)
    calculation_engine_version: Mapped[str] = mapped_column(String(100), nullable=False)
    validation_status: Mapped[str] = mapped_column(String(24), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (
        CheckConstraint(
            "validation_status IN ('running', 'passed', 'failed', 'passed_with_warnings')",
            name="ck_validation_runs_status",
        ),
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at", name="ck_validation_runs_dates"),
        Index("ix_validation_runs_version_time", "portfolio_version_id", text("started_at DESC")),
    )

    portfolio_version = relationship("PortfolioVersion", back_populates="validation_runs")
    results = relationship("PortfolioValidationResult", back_populates="validation_run", cascade="all, delete-orphan")


class PortfolioValidationResult(Base):
    __tablename__ = "portfolio_validation_results"

    validation_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    validation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_validation_runs.validation_run_id", ondelete="RESTRICT"), nullable=False
    )
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False)
    result_status: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(20), nullable=False, default="info", server_default="info"
    )
    security_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.security_id", ondelete="RESTRICT"), nullable=True
    )
    actual_value: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(Numeric(24, 8), nullable=True)
    result_message: Mapped[str] = mapped_column(Text, nullable=False)
    details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "result_status IN ('pass', 'fail', 'warning', 'not_applicable')",
            name="ck_validation_results_status",
        ),
        CheckConstraint(
            "severity IN ('info', 'low', 'medium', 'high', 'critical')",
            name="ck_validation_results_severity",
        ),
        Index("ix_validation_results_run_status", "validation_run_id", "result_status"),
        Index("ix_validation_results_rule_status", "rule_code", "result_status"),
    )

    validation_run = relationship("PortfolioValidationRun", back_populates="results")
    security = relationship("Security")


class PortfolioScenario(Base):
    __tablename__ = "portfolio_scenarios"

    portfolio_scenario_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()")
    )
    portfolio_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("portfolio_versions.portfolio_version_id", ondelete="RESTRICT"), nullable=False
    )
    scenario_code: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(180), nullable=False)
    scenario_type: Mapped[str] = mapped_column(String(30), nullable=False)
    assumptions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb")
    )
    estimated_portfolio_value: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    estimated_change_amount: Mapped[Optional[float]] = mapped_column(Numeric(20, 2), nullable=True)
    estimated_change_pct: Mapped[Optional[float]] = mapped_column(Numeric(9, 4), nullable=True)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    calculation_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("portfolio_version_id", "scenario_code", name="uq_scenario_code_per_version"),
        CheckConstraint(
            "scenario_type IN ('stress', 'what_if', 'market_regime', 'sensitivity')",
            name="ck_scenarios_type",
        ),
        CheckConstraint(
            "estimated_portfolio_value IS NULL OR estimated_portfolio_value >= 0",
            name="ck_scenarios_value",
        ),
        Index("ix_scenarios_version_time", "portfolio_version_id", text("created_at DESC")),
    )

    portfolio_version = relationship("PortfolioVersion", back_populates="scenarios")
