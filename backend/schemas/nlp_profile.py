"""
Evidence-Based Structured Investor Information Schemas.
Defines typed Pydantic models for natural-language investor information extraction,
traceability, conflict detection, and questionnaire prefilling.

Version: 2026.11-v1.0
Authoritative Date: 2026-11-04
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
import uuid


class ExtractionStatus(str, Enum):
    EXPLICIT = "EXPLICIT"
    NORMALIZED_FROM_TEXT = "NORMALIZED_FROM_TEXT"
    INFERRED = "INFERRED"
    NOT_PROVIDED = "NOT_PROVIDED"


class ValidationStatus(str, Enum):
    VALID = "VALID"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    INVALID = "INVALID"
    CONFLICT = "CONFLICT"


class ContributionType(str, Enum):
    LUMP_SUM = "LUMP_SUM"
    MONTHLY_SIP = "MONTHLY_SIP"
    BOTH = "BOTH"
    NOT_SPECIFIED = "NOT_SPECIFIED"


class HorizonCategory(str, Enum):
    SHORT_TERM = "SHORT_TERM"       # < 12 months
    MEDIUM_TERM = "MEDIUM_TERM"     # 12 to 36 months
    LONG_TERM = "LONG_TERM"         # 36 to 60+ months
    NOT_SPECIFIED = "NOT_SPECIFIED"


class RiskCategoryEnum(str, Enum):
    VERY_CONSERVATIVE = "very_conservative"
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    GROWTH = "growth"
    AGGRESSIVE = "aggressive"
    UNASSESSED = "unassessed"


class ExtractedFieldMeta(BaseModel):
    """Evidence and provenance metadata for each extracted investor parameter."""
    field_name: str
    value: Any = None
    data_type: str = "string"
    extraction_status: ExtractionStatus = ExtractionStatus.NOT_PROVIDED
    validation_status: ValidationStatus = ValidationStatus.VALID
    source_span: Optional[str] = None
    user_confirmed: bool = False
    clarification_prompt: Optional[str] = None


class ExtractedGoalItem(BaseModel):
    """Structured financial goal extracted from conversation or text."""
    goal_id: Optional[str] = None
    goal_name: str
    goal_type: str = "wealth_creation"  # wealth_creation | retirement | child_education | home_purchase | income | vehicle_purchase
    target_amount: Optional[float] = None
    horizon_months: Optional[int] = None
    horizon_years: Optional[float] = None
    time_horizon_category: HorizonCategory = HorizonCategory.NOT_SPECIFIED
    priority: int = 1
    source_span: Optional[str] = None
    extraction_status: ExtractionStatus = ExtractionStatus.NORMALIZED_FROM_TEXT

    @property
    def target_horizon_months(self) -> Optional[int]:
        return self.horizon_months


class ExtractedExistingHolding(BaseModel):
    """Existing stock or portfolio holding mentioned by the investor."""
    symbol: str
    company_name: Optional[str] = None
    exchange: str = "NSE"
    quantity: Optional[int] = None
    average_purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    source_span: Optional[str] = None


class ExtractedCapitalDetails(BaseModel):
    """Investment capital, contribution type, and liquidity constraints."""
    initial_lump_sum: Optional[float] = None
    monthly_contribution: Optional[float] = None
    contribution_type: ContributionType = ContributionType.NOT_SPECIFIED
    currency_code: str = "INR"
    liquidity_needed_months: Optional[int] = None
    liquidity_notes: Optional[str] = None
    source_span: Optional[str] = None


class ExtractedRiskDetails(BaseModel):
    """Risk tolerance (psychological) vs risk capacity (financial ability to absorb loss)."""
    stated_tolerance: Optional[str] = None      # e.g. "moderate", "cannot afford to lose money"
    loss_capacity_emergency_months: Optional[float] = None  # e.g. 6.0 months living expenses
    emergency_fund_status: str = "unspecified"   # "full" | "partial" | "none" | "unspecified"
    assessed_risk_category: RiskCategoryEnum = RiskCategoryEnum.UNASSESSED
    target_volatility_pct: Optional[float] = None
    is_conflict_detected: bool = False
    conflict_description: Optional[str] = None
    fiduciary_safeguards_applied: List[str] = Field(default_factory=list)


class ExtractedSecurityPreference(BaseModel):
    """Specific stock/security preferred or requested by the investor."""
    company_name: str
    resolved_symbol: str
    exchange: str = "NSE"
    bse_code: Optional[str] = None
    isin: Optional[str] = None
    confidence: float = 1.0
    source_span: Optional[str] = None


class ExtractedSectorConstraint(BaseModel):
    """Quantitative sector exposure constraint extracted from natural language."""
    sector: str
    operator: str = "LTE"  # LTE, GTE, EQ, LT, GT
    value: float = 20.0
    unit: str = "PERCENT"
    source_span: Optional[str] = None


class ExtractedInvestmentPreferences(BaseModel):
    """Preferences vs strict negative exclusions."""
    preferred_sectors: List[str] = Field(default_factory=list)
    excluded_sectors: List[str] = Field(default_factory=list)
    excluded_instruments: List[str] = Field(default_factory=list)
    preferred_securities: List[ExtractedSecurityPreference] = Field(default_factory=list)
    sector_constraints: List[ExtractedSectorConstraint] = Field(default_factory=list)
    investment_style: Optional[str] = None       # e.g. "dividend_income", "high_growth", "value", "bluechip"
    company_characteristics: List[str] = Field(default_factory=list)  # e.g. ["high_roe", "low_debt", "reasonable_pe"]
    soft_preferences_notes: Optional[str] = None


class ExtractedInvestorExperience(BaseModel):
    """Investment knowledge and market experience level."""
    experience_level: str = "beginner"       # "beginner" | "intermediate" | "experienced"
    knowledge_level: str = "basic"           # "basic" | "intermediate" | "advanced"
    source_span: Optional[str] = None


class MappedQuestionnaireAnswerItem(BaseModel):
    """Direct mapping to existing SEBI RiskQuestion & RiskQuestionOption in PostgreSQL."""
    question_id: str
    question_code: str
    question_text: str
    selected_option_id: str
    selected_option_code: str
    selected_option_label: str
    score: float
    mapped_from_field: str
    extraction_status: ExtractionStatus = ExtractionStatus.NORMALIZED_FROM_TEXT


class ContradictionItem(BaseModel):
    """Identified conflict in investor requirements."""
    conflict_code: str
    title: str
    description: str
    conflicting_elements: List[str]
    suggested_tradeoff_resolution: str

    @property
    def code(self) -> str:
        return self.conflict_code


class StructuredInvestorProfile(BaseModel):
    """
    Authoritative, validated investor profile generated from natural language or questionnaire.
    This exact schema feeds into the LangGraph Strategist, Critic, and Optimizer.
    """
    portfolio_name: str = "AI Disciplined Equity Portfolio"
    capital: ExtractedCapitalDetails = Field(default_factory=ExtractedCapitalDetails)
    horizon_months: Optional[int] = None
    horizon_years: Optional[float] = None
    horizon_category: HorizonCategory = HorizonCategory.NOT_SPECIFIED
    goals: List[ExtractedGoalItem] = Field(default_factory=list)
    risk: ExtractedRiskDetails = Field(default_factory=ExtractedRiskDetails)
    preferences: ExtractedInvestmentPreferences = Field(default_factory=ExtractedInvestmentPreferences)
    experience: ExtractedInvestorExperience = Field(default_factory=ExtractedInvestorExperience)
    existing_holdings: List[ExtractedExistingHolding] = Field(default_factory=list)
    cleaned_user_prompt: str = ""

    # Fiduciary Validation & Evidence
    is_ready_for_recommendation: bool = False
    missing_mandatory_fields: List[str] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
    clarification_questions: List[str] = Field(default_factory=list)
    fiduciary_audit_notes: List[str] = Field(default_factory=list)
    field_evidence: Dict[str, ExtractedFieldMeta] = Field(default_factory=dict)
    mapped_questionnaire_answers: List[MappedQuestionnaireAnswerItem] = Field(default_factory=list)
    extraction_method: str = "gemini-3.8-flash"
    confidence_score: float = 0.95

    @property
    def missing_fields(self) -> List[ExtractedFieldMeta]:
        return [
            meta for meta in self.field_evidence.values()
            if meta.extraction_status == ExtractionStatus.NOT_PROVIDED
            or meta.validation_status == ValidationStatus.REQUIRES_CONFIRMATION
        ]

    def __getitem__(self, item: str) -> Any:
        if item == "extracted_profile":
            amt = self.capital.initial_lump_sum or (self.capital.monthly_contribution * 12 if self.capital.monthly_contribution else 250000.0)
            return {
                "portfolio_name": self.portfolio_name,
                "investment_amount": amt,
                "horizon_months": self.horizon_months or 60,
                "risk_category": self.risk.assessed_risk_category.value,
                "experience_level": self.experience.experience_level,
                "knowledge_level": self.experience.knowledge_level,
                "emergency_fund_status": self.risk.emergency_fund_status,
                "goal_type": self.goals[0].goal_type if self.goals else "wealth_creation",
                "goal_name": self.goals[0].goal_name if self.goals else "Long-Term Wealth Creation",
                "target_corpus": amt * 2.5,
                "preferred_sectors": self.preferences.preferred_sectors,
                "excluded_sectors": self.preferences.excluded_sectors,
                "user_prompt": self.cleaned_user_prompt,
            }
        elif item == "fiduciary_notes":
            return self.fiduciary_audit_notes
        elif item == "resolved_questionnaire_answers":
            return [
                {
                    "question_id": a.question_id,
                    "question_code": a.question_code,
                    "question_text": a.question_text,
                    "selected_option_id": a.selected_option_id,
                    "selected_option_code": a.selected_option_code,
                    "selected_option_label": a.selected_option_label,
                    "score": a.score,
                }
                for a in self.mapped_questionnaire_answers
            ]
        elif hasattr(self, item):
            return getattr(self, item)
        raise KeyError(item)

    def get(self, item: str, default: Any = None) -> Any:
        try:
            return self[item]
        except KeyError:
            return default


class NaturalLanguageProfileRequest(BaseModel):
    """Request payload for natural language profile extraction."""
    text: str = Field(..., min_length=3, description="Natural language input from investor")
    existing_profile: Optional[Dict[str, Any]] = None
    is_conversational_turn: bool = False


class NaturalLanguageProfileResponse(BaseModel):
    """Response payload returned to frontend and conversational copilot."""
    profile: StructuredInvestorProfile
    summary_text: str
    prefilled_questionnaire: Dict[str, Any] = Field(default_factory=dict)

    # Backwards compatibility fields for frontend clients
    extracted_profile: Optional[Dict[str, Any]] = None
    mapped_option_codes: Dict[str, str] = Field(default_factory=dict)
    fiduciary_notes: List[str] = Field(default_factory=list)
    confidence_score: float = 0.95
    extraction_method: str = "gemini-3.8-flash"
    resolved_questionnaire_answers: Optional[List[Dict[str, Any]]] = None
