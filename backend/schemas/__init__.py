"""
Pydantic schemas for the Intelligent Portfolio Creation Application.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


# ============================================================
# Investor Profile & Preferences Schemas
# ============================================================

class UserProfileBase(BaseModel):
    display_name: Optional[str] = Field(None, max_length=120)
    country_code: str = Field("IN", min_length=2, max_length=2)
    preferred_currency: str = Field("INR", min_length=3, max_length=3)
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = "beginner"
    investment_knowledge_level: Optional[Literal["basic", "intermediate", "advanced"]] = "basic"


class UserProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=120)
    country_code: Optional[str] = Field(None, min_length=2, max_length=2)
    preferred_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    investment_experience: Optional[Literal["beginner", "intermediate", "experienced"]] = None
    investment_knowledge_level: Optional[Literal["basic", "intermediate", "advanced"]] = None


class UserProfileRead(UserProfileBase):
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppUserRead(BaseModel):
    user_id: UUID
    identity_provider: str
    identity_subject: str
    email: Optional[str] = None
    account_status: str
    profile: Optional[UserProfileRead] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Financial Goal Schemas
# ============================================================

class FinancialGoalBase(BaseModel):
    goal_name: str = Field(..., min_length=1, max_length=120)
    goal_type: str = Field(..., max_length=40)
    target_amount: Decimal = Field(..., gt=0)
    amount_already_saved: Decimal = Field(Decimal("0.0"), ge=0)
    currency_code: str = Field("INR", min_length=3, max_length=3)
    target_date: Optional[date] = None
    priority: int = Field(3, ge=1, le=5)
    notes: Optional[str] = None


class FinancialGoalCreate(FinancialGoalBase):
    pass


class FinancialGoalUpdate(BaseModel):
    goal_name: Optional[str] = Field(None, min_length=1, max_length=120)
    goal_type: Optional[str] = Field(None, max_length=40)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    amount_already_saved: Optional[Decimal] = Field(None, ge=0)
    currency_code: Optional[str] = Field(None, min_length=3, max_length=3)
    target_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    goal_status: Optional[Literal["active", "paused", "completed", "cancelled"]] = None
    notes: Optional[str] = None


class FinancialGoalRead(FinancialGoalBase):
    goal_id: UUID
    user_id: UUID
    goal_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Risk Assessment Questionnaire Schemas
# ============================================================

class RiskQuestionOptionRead(BaseModel):
    option_id: UUID
    option_code: str
    option_label: str
    score: Optional[float] = None
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class RiskQuestionRead(BaseModel):
    question_id: UUID
    question_code: str
    question_version: int
    question_text: str
    answer_type: str
    is_required: bool
    display_order: int
    options: List[RiskQuestionOptionRead] = []

    model_config = ConfigDict(from_attributes=True)


class RiskAnswerSubmit(BaseModel):
    question_id: UUID
    selected_option_id: Optional[UUID] = None
    answer_text: Optional[str] = None
    answer_numeric: Optional[float] = None
    answer_boolean: Optional[bool] = None


class RiskAssessmentSubmit(BaseModel):
    questionnaire_version: str = "demo-questionnaire-v1"
    answers: List[RiskAnswerSubmit] = Field(..., min_length=1)


class RiskAssessmentRead(BaseModel):
    risk_assessment_id: UUID
    user_id: UUID
    questionnaire_version: str
    assessment_status: str
    risk_tolerance_score: Optional[float] = None
    risk_capacity_score: Optional[float] = None
    risk_category: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Market Data Schemas
# ============================================================

class MarketPriceRecord(BaseModel):
    listing_id: UUID
    symbol: str
    price_date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Decimal
    adjusted_close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    currency_code: str = "INR"

    @field_validator("close_price")
    @classmethod
    def validate_positive_close(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Close price must be strictly positive")
        return v


class IngestionRunRead(BaseModel):
    ingestion_run_id: UUID
    source_code: str
    data_type: str
    run_status: str
    records_seen: int
    records_inserted: int
    records_updated: int
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Portfolio Engine & Generation Schemas
# ============================================================

class PortfolioPreferences(BaseModel):
    excluded_sectors: List[str] = Field(default_factory=list)
    excluded_instruments: List[str] = Field(default_factory=list)
    max_single_stock_weight_pct: float = Field(25.0, ge=5.0, le=50.0)
    max_sector_weight_pct: float = Field(40.0, ge=10.0, le=100.0)
    target_stock_count: int = Field(5, ge=2, le=20)


class PortfolioGenerationRequestCreate(BaseModel):
    portfolio_name: Optional[str] = "Intelligent AI Portfolio"
    investment_amount: Decimal = Field(..., gt=1000)
    currency_code: str = Field("INR", min_length=3, max_length=3)
    investment_horizon_months: int = Field(60, gt=0, le=360)
    goal_id: Optional[UUID] = None
    risk_assessment_id: Optional[UUID] = None
    preferences: PortfolioPreferences = Field(default_factory=PortfolioPreferences)
    user_prompt: Optional[str] = None


class PortfolioGenerationRequestRead(BaseModel):
    generation_request_id: UUID
    portfolio_id: UUID
    user_id: UUID
    request_type: str
    request_status: str
    requested_amount: Decimal
    currency_code: str
    investment_horizon_months: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioHoldingItem(BaseModel):
    security_id: UUID
    symbol: str
    security_name: str
    sector_name: str
    target_weight_pct: float
    target_amount: Decimal
    shares_quantity: int
    latest_price: Decimal
    decision_reason: str


class PortfolioValidationItem(BaseModel):
    rule_code: str
    result_status: str
    severity: str
    result_message: str
    actual_value: Optional[float] = None
    threshold_value: Optional[float] = None


class RecommendationExplanationItem(BaseModel):
    explanation_id: UUID
    explanation_type: str
    title: str
    explanation_text: str
    display_order: int
    decision_id: Optional[UUID] = None


class PortfolioVersionDetail(BaseModel):
    portfolio_version_id: UUID
    portfolio_id: UUID
    version_number: int
    version_status: str
    investment_amount: Decimal
    currency_code: str
    investment_horizon_months: Optional[int] = None
    risk_category: Optional[str] = None
    expected_return_pct: Optional[float] = None
    expected_volatility_pct: Optional[float] = None
    diversification_score: Optional[float] = None
    generated_at: datetime
    holdings: List[PortfolioHoldingItem] = []
    validation_status: str = "passed"
    validation_results: List[PortfolioValidationItem] = []
    explanations: List[RecommendationExplanationItem] = []

    model_config = ConfigDict(from_attributes=True)


class PortfolioSummary(BaseModel):
    portfolio_id: UUID
    portfolio_name: str
    portfolio_status: str
    latest_version: Optional[PortfolioVersionDetail] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================
# Scenario Analysis Schemas
# ============================================================

class ScenarioRunRequest(BaseModel):
    scenario_type: Literal["market_shock", "sector_shock", "interest_rate_hike"]
    scenario_name: str
    drop_pct: float = Field(..., ge=1.0, le=75.0)
    affected_sector: Optional[str] = None


class ScenarioRunResult(BaseModel):
    scenario_code: str
    scenario_name: str
    scenario_type: str
    baseline_value: Decimal
    stressed_value: Decimal
    loss_amount: Decimal
    loss_pct: float
    impact_summary: str
