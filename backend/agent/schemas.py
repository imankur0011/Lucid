"""
Strict Pydantic Schemas for Multi-Agent Investment Research, Fiduciary Audits, and Explainability.
Defines explicit typed contracts for all LangGraph nodes:
- Suitability Agent (Investor Profile, Risk Capacity/Willingness, Constraints)
- Macro Analyst (Economic Indicators, Sector Macro Direction, Policy Regime)
- Market Analyst (Market Breadth, Valuation Dispersion, Technical Posture)
- Fundamental / Equity Research Analyst (Industry-Aware Metric Observations, Balance Sheet Quality)
- News and Filings Analyst (Exchange Announcements, Sentiment, Governance Integrity)
- Lead Strategist (Portfolio Candidates, Role Allocations, Factor Weights)
- Risk Critic (Independent Audit, Objections, Bounded Rework, Post-Optimizer Final Validation)
- Deterministic Optimizer (SLSQP Math, Whole Shares, Integer Cash Reserve, Constraint Validations)
- Moderator (Consolidated Fiduciary Deliberation, Two-Level Explanations)
- Agent Communication (Structured AgentMessage protocol)

Version: 2026.11-v2.0
Authoritative Date: 2026-11-05
"""

from __future__ import annotations
from enum import Enum
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Literal, Union
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 0. STRICT BASE MODEL
# ==============================================================================

class StrictModel(BaseModel):
    """Base model enforcing strict schema adherence with zero arbitrary extra fields."""
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        arbitrary_types_allowed=False,
        str_strip_whitespace=True,
    )


# ==============================================================================
# 1. COMMON SCHEMAS SHARED BY ALL AGENTS
# ==============================================================================

class AgentOutputBase(StrictModel):
    """Standardized metadata envelope shared by every specialist agent output."""
    execution_status: Literal["SUCCESS", "PARTIAL", "FAILED", "NOT_RUN"] = "SUCCESS"
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    model_name: Optional[str] = None
    tool_calls: int = Field(default=0, ge=0)
    data_as_of: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)


class EvidenceItem(StrictModel):
    """Rigorous traceable evidence record connecting financial findings to verified sources."""
    evidence_id: str
    evidence_type: Literal[
        "MARKET_DATA",
        "FUNDAMENTAL_DATA",
        "FINANCIAL_STATEMENT",
        "MACRO_DATA",
        "NEWS",
        "EXCHANGE_DATA",
        "BROKER_DATA",
        "USER_INPUT",
        "CALCULATED_RESULT",
        "INTERNAL_POLICY",
        "REGULATORY_SOURCE",
        "OTHER",
    ]
    source_name: str
    source_url: Optional[str] = None
    metric_name: Optional[str] = None
    value: Optional[Union[float, str, bool]] = None
    unit: Optional[str] = None
    published_at: Optional[datetime] = None
    event_date: Optional[date] = None
    observation_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    methodology: Optional[str] = None
    quality_status: Literal[
        "VERIFIED",
        "ESTIMATED",
        "STALE",
        "INCOMPLETE",
        "UNVERIFIED",
    ] = "VERIFIED"
    notes: Optional[str] = None


class MetricObservation(StrictModel):
    """Contextual observation of a financial parameter with benchmark and portfolio implications."""
    metric_name: str
    value: Optional[float] = None
    unit: str
    observation_period: Optional[str] = None
    calculation_method: Optional[str] = None
    benchmark_value: Optional[float] = None
    reference_range: Optional[str] = None
    interpretation: str
    portfolio_implication: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class AgentFinding(StrictModel):
    """Structured conclusion or alert surfaced by an agent during deliberation."""
    finding_id: str
    category: Literal[
        "OPPORTUNITY",
        "RISK",
        "WARNING",
        "CONSTRAINT",
        "SUITABILITY",
        "QUALITY",
    ]
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"] = "INFO"
    title: str
    description: str
    affected_tickers: List[str] = Field(default_factory=list)
    affected_sectors: List[str] = Field(default_factory=list)
    action_required: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class PolicyConstraint(StrictModel):
    """Explicit deterministic constraint derived from SEBI regulations, exchange rules, or house policies."""
    constraint_id: str
    name: str
    origin: Literal[
        "REGULATORY",
        "EXCHANGE",
        "BROKER",
        "LUCID_HOUSE_POLICY",
        "INVESTOR_REQUIREMENT",
        "OPTIMIZATION",
    ]
    scope: Literal[
        "PORTFOLIO",
        "STOCK",
        "SECTOR",
        "INSTRUMENT",
        "TRANSACTION",
    ]
    target: Optional[str] = None
    threshold_value: Optional[float] = None
    unit: Optional[str] = None
    is_hard_constraint: bool = True
    rationale: str


class AgentMessage(StrictModel):
    """Structured message protocol for auditable inter-agent communication."""
    message_id: str
    sender: str
    recipient: str
    message_type: Literal[
        "FINDING",
        "QUESTION",
        "OBJECTION",
        "REWORK_REQUEST",
        "VALIDATION_RESULT",
        "DECISION",
        "DATA_REQUEST",
    ]
    subject: str
    message: str
    related_tickers: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)
    requires_response: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


# ==============================================================================
# 2. INDIVIDUAL AGENT OUTPUT SCHEMAS
# ==============================================================================

# --- A. SUITABILITY AGENT ---

class SuitabilityOutput(AgentOutputBase):
    """Evaluates whether the proposed strategy matches investor capacity, willingness, and horizon."""
    investor_risk_profile: Literal[
        "CONSERVATIVE",
        "MODERATE",
        "GROWTH",
        "AGGRESSIVE",
        "UNDETERMINED",
    ]
    risk_capacity: Literal["LOW", "MEDIUM", "HIGH", "UNDETERMINED"]
    risk_willingness: Literal["LOW", "MEDIUM", "HIGH", "UNDETERMINED"]
    investment_horizon_months: Optional[int] = Field(default=None, ge=0)
    liquidity_requirement: Literal["LOW", "MEDIUM", "HIGH", "UNDETERMINED"] = "LOW"
    overall_suitability: Literal[
        "SUITABLE",
        "SUITABLE_WITH_CONDITIONS",
        "UNSUITABLE",
        "INSUFFICIENT_INFORMATION",
    ]
    suitability_rationale: str
    constraints: List[PolicyConstraint] = Field(default_factory=list)
    required_clarifications: List[str] = Field(default_factory=list)
    suitability_warnings: List[str] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# --- B. MACRO ANALYST ---

class MacroIndicatorAssessment(StrictModel):
    indicator: str
    current_value: Optional[float] = None
    unit: str
    previous_value: Optional[float] = None
    observation_date: Optional[date] = None
    trend: Literal["RISING", "FALLING", "STABLE", "VOLATILE", "UNKNOWN"]
    interpretation: str
    portfolio_implication: str
    affected_sectors: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class SectorMacroImpact(StrictModel):
    sector: str
    expected_direction: Literal["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNCERTAIN"]
    impact_horizon: Literal["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM"]
    rationale: str
    evidence_ids: List[str] = Field(default_factory=list)


class MacroAnalystOutput(AgentOutputBase):
    """Assesses Indian macro regime, RBI repo rate, CPI inflation, GDP, and sector tailwinds."""
    regime: str = Field(description="Market regime classification (e.g. MODERATE, BULLISH_EXPANSION, HIGH_VOLATILITY, DEFENSIVE)")
    vix: float = Field(description="India VIX annualized volatility benchmark")
    rbi_repo_rate: float = Field(description="RBI policy repo rate in percentage")
    cpi_inflation: float = Field(description="India CPI headline inflation rate in percentage")
    gdp_growth: float = Field(description="India real GDP growth rate in percentage")
    gsec_10y_yield: float = Field(description="India 10-Year Government Securities benchmark yield in percentage")
    cash_buffer_pct: float = Field(description="Recommended unallocated liquidity buffer percentage")
    macro_stance: str = Field(description="Recommended macroeconomic posture (e.g. quality_equity_accumulation)")
    rate_cycle_outlook: str = Field(description="Monetary policy stance (e.g. pause_extended, easing, tightening)")
    macro_summary: str = Field(description="Fiduciary narrative summarizing macroeconomic conditions")
    is_live_data: bool = Field(default=True, description="True if sourced from live DB observations, False if fallback baseline")
    data_sufficiency_status: str = Field(default="LIVE_AUDITED", description="LIVE_AUDITED, FALLBACK_ASSUMPTION, or DATA_INSUFFICIENT")
    indicators: List[MacroIndicatorAssessment] = Field(default_factory=list)
    sector_impacts: List[SectorMacroImpact] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    evidence_records: List[MetricEvidenceRecord] = Field(default_factory=list)


# --- C. MARKET ANALYST ---

class MarketIndicatorAssessment(StrictModel):
    indicator: str
    value: Optional[float] = None
    unit: str
    benchmark: Optional[str] = None
    observation_period: Optional[str] = None
    interpretation: str
    investment_implication: str
    evidence_ids: List[str] = Field(default_factory=list)


class SectorMarketAssessment(StrictModel):
    sector: str
    relative_performance: Optional[float] = None
    relative_performance_unit: Optional[str] = None
    trend: Literal["BULLISH", "BEARISH", "SIDEWAYS", "MIXED", "UNKNOWN"]
    volatility_level: Literal["LOW", "MODERATE", "HIGH", "UNKNOWN"]
    rationale: str
    evidence_ids: List[str] = Field(default_factory=list)


class MarketAnalystOutput(AgentOutputBase):
    """Assesses market breadth, volatility dispersion, and sector performance relative to NIFTY 50."""
    candidates_evaluated: int
    sectors_represented: int
    sector_distribution: Dict[str, int]
    technical_posture: str
    market_breadth_score: float
    avg_30d_volatility_pct: float
    high_beta_ratio: float
    market_summary: str
    benchmark_name: str = "NIFTY 50"
    market_indicators: List[MarketIndicatorAssessment] = Field(default_factory=list)
    sector_assessments: List[SectorMarketAssessment] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# --- D. FUNDAMENTAL / EQUITY RESEARCH ANALYST ---

class CompanyFundamentalAssessment(StrictModel):
    """Industry-aware fundamental audit for an individual company."""
    ticker: str
    company_name: str
    sector: str
    investment_view: Literal["ATTRACTIVE", "NEUTRAL", "UNATTRACTIVE", "INSUFFICIENT_DATA"]
    financial_metrics: List[MetricObservation] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    valuation_assessment: str
    peer_comparison: Optional[str] = None
    investment_thesis: str
    key_risks: List[str] = Field(default_factory=list)
    suitable_for_portfolio: bool
    suitability_rationale: str
    evidence_ids: List[str] = Field(default_factory=list)


class FundamentalAnalystOutput(AgentOutputBase):
    """Detailed company-level and industry-aware fundamental research."""
    companies_analyzed: List[CompanyFundamentalAssessment] = Field(default_factory=list)
    industry_contexts: Dict[str, str] = Field(default_factory=dict)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# --- E. NEWS AND SENTIMENT ANALYST ---

class NewsEventAssessment(StrictModel):
    event_id: str
    headline: str
    publisher: str
    source_url: Optional[str] = None
    published_at: Optional[datetime] = None
    event_date: Optional[date] = None
    affected_tickers: List[str] = Field(default_factory=list)
    affected_sectors: List[str] = Field(default_factory=list)
    event_category: Literal[
        "EARNINGS",
        "CORPORATE_ACTION",
        "MANAGEMENT_CHANGE",
        "REGULATORY",
        "MACROECONOMIC",
        "LITIGATION",
        "BUSINESS_DEVELOPMENT",
        "MARKET_EVENT",
        "OTHER",
    ]
    sentiment: Literal["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNCERTAIN"]
    relevance: Literal["LOW", "MEDIUM", "HIGH"]
    summary: str
    evidence_ids: List[str] = Field(default_factory=list)


class NewsAnalystOutput(AgentOutputBase):
    """Corporate announcements, regulatory filings, auditor notes, and sentiment."""
    sentiment_score: float
    sentiment_label: Literal["positive", "neutral", "negative"]
    headlines_analyzed: List[str] = Field(default_factory=list)
    corporate_disclosures_reviewed: int
    governance_flags: List[Dict[str, Any]] = Field(default_factory=list)
    news_summary: str
    is_live_data: bool = Field(default=True, description="True if sourced from live DB news feed, False if baseline reference")
    data_sufficiency_status: str = Field(default="LIVE_AUDITED", description="LIVE_AUDITED, FALLBACK_ASSUMPTION, or DATA_INSUFFICIENT")
    source_documents: List[Dict[str, str]] = Field(default_factory=list)
    events: List[NewsEventAssessment] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# --- F. STRATEGIST AGENT ---

class PortfolioCandidate(StrictModel):
    """Candidate security selected by Strategist with assigned portfolio role."""
    ticker: str
    company_name: str
    sector: str
    proposed_weight: Optional[float] = Field(default=None, ge=0, le=1)
    portfolio_role: Literal[
        "CORE",
        "GROWTH",
        "DEFENSIVE",
        "DIVERSIFICATION",
        "OPPORTUNISTIC",
        "OTHER",
    ]
    selection_rationale: str
    allocation_rationale: str
    supporting_factors: List[str] = Field(default_factory=list)
    major_risks: List[str] = Field(default_factory=list)
    evidence_ids: List[str] = Field(default_factory=list)


class StrategistOutput(AgentOutputBase):
    """Converts specialist research into an overarching portfolio strategy theme and candidate roles."""
    investment_strategy: str
    strategy_objective: str
    target_sectors: List[str] = Field(default_factory=list)
    recommended_stance: str
    proposed_candidates: List[PortfolioCandidate] = Field(default_factory=list)
    factor_weights: Dict[str, float] = Field(default_factory=dict)
    llm_reasoning_summary: Optional[str] = None
    investor_guidance_addressed: Optional[str] = None
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# --- G. CRITIC AGENT ---

class CriticObjection(StrictModel):
    objection_id: str
    category: Literal[
        "UNSUPPORTED_RECOMMENDATION",
        "UNREALISTIC_EXPECTATION",
        "CONCENTRATION_RISK",
        "SUITABILITY_MISMATCH",
        "VALUATION_RISK",
        "DATA_QUALITY",
        "DIVERSIFICATION",
        "METHODOLOGY",
        "REGULATORY",
        "TRADING_CONSTRAINT",
        "OTHER",
    ]
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    affected_tickers: List[str] = Field(default_factory=list)
    objection: str
    evidence_against_proposal: List[str] = Field(default_factory=list)
    required_correction: Optional[str] = None


class ReworkRequest(StrictModel):
    target_agent: Literal[
        "STRATEGIST",
        "MACRO_ANALYST",
        "MARKET_ANALYST",
        "FUNDAMENTAL_ANALYST",
        "NEWS_ANALYST",
    ]
    instructions: str
    tickers_to_remove: List[str] = Field(default_factory=list)
    required_substitutes_count: int = 0


class CriticOutput(AgentOutputBase):
    """Independent audit with explicit verdict states and issue-specific rework directives."""
    critic_iteration: int
    decision: Literal[
        "APPROVED",
        "REWORK_REQUIRED",
        "BLOCKED_VIOLATION",
        "DATA_INSUFFICIENT",
    ]
    can_proceed: bool
    critic_summary: str
    objections: List[CriticObjection] = Field(default_factory=list)
    rework_requests: List[ReworkRequest] = Field(default_factory=list)
    audited_constraints: Dict[str, bool] = Field(default_factory=dict)
    blocking_reasons: List[str] = Field(default_factory=list)
    removable_tickers: List[str] = Field(default_factory=list)
    rework_instructions: List[str] = Field(default_factory=list)
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)

    @property
    def verdict_status(self) -> str:
        return self.decision

    @property
    def approved(self) -> bool:
        return self.can_proceed


# --- H. OPTIMIZER / PORTFOLIO OPTIMIZATION COMPONENT ---

class ConstraintValidation(StrictModel):
    constraint_id: str
    constraint_name: str
    origin: Literal[
        "REGULATORY",
        "EXCHANGE",
        "BROKER",
        "LUCID_HOUSE_POLICY",
        "INVESTOR_REQUIREMENT",
        "OPTIMIZATION",
    ]
    observed_value: Optional[float] = None
    threshold_value: Optional[float] = None
    unit: str
    passed: bool
    severity: Literal["INFO", "WARNING", "BLOCKING"]
    explanation: str
    evidence_ids: List[str] = Field(default_factory=list)


class OptimizedPosition(StrictModel):
    """Mathematically determined position with whole shares, amount, and reference price."""
    ticker: str
    company_name: str
    sector: str
    current_quantity: int = Field(default=0, ge=0)
    target_quantity: int = Field(default=0, ge=0)
    reference_price: float = Field(gt=0)
    reference_price_date: Optional[date] = None
    target_weight_pct: float = Field(ge=0, le=100)
    allocated_amount: float = Field(ge=0)
    role: Optional[str] = None
    selection_rationale: Optional[str] = None


class OptimizerOutput(AgentOutputBase):
    """Deterministic SLSQP optimization and integer share results."""
    objective_function: str
    optimization_status: Literal["OPTIMAL", "FEASIBLE", "INFEASIBLE", "FAILED"]
    total_capital: float
    total_invested: float
    unallocated_cash: float
    cash_reserve_pct: float
    positions: List[OptimizedPosition] = Field(default_factory=list)
    constraint_validations: List[ConstraintValidation] = Field(default_factory=list)
    expected_return_pct: float
    expected_volatility_pct: float
    sharpe_ratio: float
    diversification_score: float
    all_constraints_passed: bool
    findings: List[AgentFinding] = Field(default_factory=list)


# --- I. MODERATOR / FINAL DECISION AGENT ---

class ParameterExplanation(StrictModel):
    """
    Two-level explanation model for every financial parameter:
    Level 1: Concise plain-English summary visible by default.
    Level 2: Deep dive expandable on click with formula, benchmark corridors, and limitations.
    """
    parameter_name: str
    value: Union[float, str]
    unit: str
    # Level 1: Visible by default
    what_it_means: str                 # What is it?
    why_it_matters: str                # Why does it matter?
    how_to_interpret: str              # How should it be interpreted?
    why_it_matters_for_portfolio: str  # Why does it matter for this recommendation?
    # Level 2: Expandable deep dive
    detailed_definition: Optional[str] = None
    purpose: Optional[str] = None
    benchmark_comparison: Optional[str] = None
    calculation_methodology: Optional[str] = None
    why_favorable_or_unfavorable: Optional[str] = None
    investment_implications: Optional[str] = None
    portfolio_implications: Optional[str] = None
    limitations: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)


class PositionExplanation(StrictModel):
    """Comprehensive stock-specific explanation covering selection, allocation math, and risks."""
    ticker: str
    company_name: str
    sector: str
    decision: Literal["INCLUDE", "EXCLUDE", "RETAIN", "REDUCE", "INCREASE"]
    allocation_pct: float
    allocated_amount: float
    shares_quantity: int
    reference_price: float
    why_selected: str
    why_this_allocation: str
    why_not_higher: str
    why_not_lower: str
    important_parameters: List[ParameterExplanation] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    risks_and_limitations: List[str] = Field(default_factory=list)
    what_could_make_this_wrong: str


class ModeratorOutput(AgentOutputBase):
    """Consolidates validated agent findings into transparent user-facing recommendations."""
    final_decision_status: Literal["READY_FOR_USER_REVIEW", "BLOCKED_VIOLATION", "DATA_INSUFFICIENT"]
    executive_summary: str
    portfolio_strategy_explanation: str
    diversification_explanation: str
    cash_reserve_explanation: str
    position_explanations: List[PositionExplanation] = Field(default_factory=list)
    portfolio_parameters: List[ParameterExplanation] = Field(default_factory=list)
    critic_audit_summary: str
    sebi_guardrails_summary: str
    findings: List[AgentFinding] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)


# ==============================================================================
# 3. BACKWARDS COMPATIBILITY ALIASES & MODELS
# ==============================================================================

class CriticVerdictStatus(str, Enum):
    APPROVED = "APPROVED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    BLOCKED_VIOLATION = "BLOCKED_VIOLATION"
    DATA_INSUFFICIENT = "DATA_INSUFFICIENT"


class DataQualityStatus(str, Enum):
    AUDITED_REPORTED = "AUDITED_REPORTED"
    CALCULATED_RATIO = "CALCULATED_RATIO"
    STATISTICAL_ESTIMATE = "STATISTICAL_ESTIMATE"
    DERIVED_ESTIMATE = "DERIVED_ESTIMATE"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    FALLBACK_ASSUMPTION = "FALLBACK_ASSUMPTION"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"


class ReportingBasis(str, Enum):
    CONSOLIDATED = "CONSOLIDATED"
    STANDALONE = "STANDALONE"


class MetricEvidenceRecord(BaseModel):
    """Legacy compatibility audit record."""
    instrument_symbol: str
    exchange_code: str = "NSE"
    metric_name: str
    metric_value: Any
    unit: str
    data_quality_status: DataQualityStatus
    reporting_basis: ReportingBasis = ReportingBasis.CONSOLIDATED
    document_reference: str
    reporting_period: str
    publication_date: Optional[str] = None
    retrieval_timestamp: str
    calculation_formula: Optional[str] = None
    underlying_inputs: Optional[Dict[str, Any]] = None
    verification_hash: Optional[str] = None
    limitations: Optional[str] = None


class MacroAnalysisOutput(BaseModel):
    """Legacy compatibility schema for Macro Analyst."""
    regime: str
    vix: float
    rbi_repo_rate: float
    cpi_inflation: float
    gdp_growth: float
    gsec_10y_yield: float
    cash_buffer_pct: float
    macro_stance: str
    rate_cycle_outlook: str
    macro_summary: str
    is_live_data: bool = True
    data_sufficiency_status: str = "LIVE_AUDITED"
    evidence_records: List[MetricEvidenceRecord] = Field(default_factory=list)


class MarketAnalysisOutput(BaseModel):
    """Legacy compatibility schema for Market Analyst."""
    candidates_evaluated: int
    sectors_represented: int
    sector_distribution: Dict[str, int]
    technical_posture: str
    market_breadth_score: float
    avg_30d_volatility_pct: float
    high_beta_ratio: float
    market_summary: str
    benchmark_name: str = "NIFTY 50"
    data_sufficiency_status: str = "VALID"
    evidence_records: List[MetricEvidenceRecord] = Field(default_factory=list)


class NewsAnalysisOutput(BaseModel):
    """Legacy compatibility schema for News Analyst."""
    sentiment_score: float
    sentiment_label: str
    headlines_analyzed: List[str] = Field(default_factory=list)
    corporate_disclosures_reviewed: int
    governance_flags: List[Dict[str, Any]] = Field(default_factory=list)
    news_summary: str
    source_documents: List[Dict[str, str]] = Field(default_factory=list)
    is_live_data: bool = True
    data_sufficiency_status: str = "LIVE_AUDITED"


class StrategistProposalOutput(BaseModel):
    """Legacy compatibility schema for Lead Strategist."""
    strategy_theme: str
    target_sectors: List[str]
    recommended_stance: str
    candidate_rankings: List[Dict[str, Any]]
    factor_weights: Dict[str, float]
    llm_reasoning_summary: Optional[str] = None
    investor_guidance_addressed: Optional[str] = None


class CriticEvaluationOutput(BaseModel):
    """Legacy compatibility schema for Risk Critic."""
    critic_iteration: int
    verdict_status: CriticVerdictStatus
    approved: bool
    findings: List[Dict[str, Any]]
    audited_constraints: Dict[str, bool]
    critic_summary: str
    removable_tickers: List[str] = Field(default_factory=list)
    rework_instructions: List[str] = Field(default_factory=list)
    blocking_reasons: List[str] = Field(default_factory=list)
