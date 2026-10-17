"""
Pydantic schemas for all data structures used across the application.
These enforce structured output from LLM agents and validate data at every boundary.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum


# ============================================================
# Enums
# ============================================================

class MarketRegime(str, Enum):
    """Market regime classification based on India VIX."""
    CRISIS = "crisis"          # VIX > 25
    HIGH_VOL = "high_vol"      # VIX 20-25
    NORMAL = "normal"          # VIX 15-20
    LOW_VOL = "low_vol"        # VIX < 15


class Signal(str, Enum):
    """Trading signal."""
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"


class CritiqueSeverity(str, Enum):
    """Severity level for Critic's issues."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ============================================================
# Market Data Models
# ============================================================

class StockData(BaseModel):
    """Individual stock data point."""
    ticker: str
    name: str
    price: float
    change_pct: float
    pe_ratio: Optional[float] = None
    roe: Optional[float] = None
    market_cap: Optional[float] = None  # in crores
    sector: Optional[str] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    retrieved_at: datetime = Field(default_factory=datetime.now)


class MarketDataSnapshot(BaseModel):
    """Complete market data snapshot for all tracked stocks."""
    stocks: List[StockData]
    nifty50_level: float
    nifty50_change_pct: float
    retrieved_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# Macroeconomic Models
# ============================================================

class MacroIndicators(BaseModel):
    """Indian and global macroeconomic indicators."""
    india_vix: float
    repo_rate: float
    cpi_inflation: float
    gdp_growth: Optional[float] = None
    usd_inr: float
    fii_net_flow: Optional[float] = None  # in crores
    dii_net_flow: Optional[float] = None  # in crores
    regime: MarketRegime
    retrieved_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# News & Sentiment Models
# ============================================================

class HistoricalNewsMatch(BaseModel):
    """A historically similar news headline with known market impact."""
    headline: str
    date: datetime
    similarity_score: float
    actual_return_pct: float  # What actually happened to the stock after this news


class NewsSentiment(BaseModel):
    """Sentiment analysis for a single news item."""
    headline: str
    source: str
    published_at: datetime
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    ticker: Optional[str] = None
    historical_matches: List[HistoricalNewsMatch] = []


class SentimentSnapshot(BaseModel):
    """Aggregated sentiment data for the current period."""
    items: List[NewsSentiment]
    overall_sentiment: float = Field(ge=-1.0, le=1.0)
    retrieved_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# MFKG (Knowledge Graph) Models
# ============================================================

class HistoricalEpisode(BaseModel):
    """A historical fund manager episode retrieved from the MFKG."""
    fund_name: str
    manager_name: Optional[str] = None
    date: datetime
    regime: MarketRegime
    india_vix_at_time: float
    action_taken: str  # e.g., "Increased IT sector to 22%, reduced Banking to 15%"
    sector_weights: Dict[str, float]
    return_achieved_pct: float
    similarity_score: float  # Cosine similarity to current state


class MFKGQueryResult(BaseModel):
    """Result of querying the MFKG for similar historical episodes."""
    episodes: List[HistoricalEpisode]
    current_state_vector: List[float]
    query_regime: MarketRegime
    retrieved_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# Agent Output Models (Structured LLM Outputs)
# ============================================================

class PortfolioProposal(BaseModel):
    """A single portfolio allocation proposal from the Strategist."""
    proposal_id: str  # e.g., "A", "B", "C"
    title: str  # e.g., "Defensive Pharma Tilt"
    reasoning: str  # Chain-of-thought reasoning
    sector_allocation: Dict[str, float]  # e.g., {"IT": 0.22, "Banking": 0.18}
    stock_picks: List[Dict[str, float]]  # e.g., [{"INFY": 0.08}, {"HDFCBANK": 0.07}]
    risk_assessment: str
    confidence: int = Field(ge=1, le=10)
    historical_episodes_cited: List[str]  # Episode IDs from MFKG


class StrategistOutput(BaseModel):
    """Complete output from the Strategist agent."""
    proposals: List[PortfolioProposal] = Field(min_length=2, max_length=3)
    market_assessment: str
    regime_interpretation: str


class CritiqueIssue(BaseModel):
    """A single issue found by the Critic."""
    severity: CritiqueSeverity
    probe_name: str  # e.g., "Hallucination Detection", "SEBI Compliance"
    description: str
    suggested_fix: str


class CriticOutput(BaseModel):
    """Complete output from the Critic agent."""
    issues: List[CritiqueIssue]
    approved: bool
    msaea_scores: Dict[str, bool]  # e.g., {"hallucination": True, "temporal": True}
    overall_safety_score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class ModeratorOutput(BaseModel):
    """Final decision from the Moderator agent."""
    selected_proposal_id: str
    final_reasoning: str
    confidence: int = Field(ge=1, le=10)
    decision_log: str  # Auditable log entry


# ============================================================
# Final Portfolio Models
# ============================================================

class PortfolioAllocation(BaseModel):
    """Final computed portfolio allocation."""
    stocks: Dict[str, float]  # ticker → weight (0.0 to 1.0)
    sector_weights: Dict[str, float]
    total_weight: float = Field(ge=0.99, le=1.01)  # Must sum to ~1.0
    investment_amount: float
    stock_amounts: Dict[str, float]  # ticker → rupee amount


class PortfolioMetrics(BaseModel):
    """Computed portfolio risk/return metrics."""
    expected_annual_return: float
    sharpe_ratio: float
    max_drawdown: float
    beta: float
    tracking_error: Optional[float] = None


class PortfolioResult(BaseModel):
    """Complete portfolio result sent to the frontend."""
    allocation: PortfolioAllocation
    metrics: PortfolioMetrics
    reasoning_summary: str
    historical_episodes_used: List[HistoricalEpisode]
    confidence: int = Field(ge=1, le=10)
    regime: MarketRegime
    sources: List[str]
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
# User Models
# ============================================================

class UserProfile(BaseModel):
    """User investment profile."""
    user_id: str
    risk_tolerance: str = "moderate"  # conservative, moderate, aggressive
    investment_horizon: str = "medium"  # short, medium, long
    investment_amount: float = 500000.0
    preferred_sectors: List[str] = []
    excluded_sectors: List[str] = []


class PortfolioRequest(BaseModel):
    """User request for portfolio creation."""
    query: str  # Natural language query
    user_profile: Optional[UserProfile] = None
    amount: Optional[float] = None
    risk_tolerance: Optional[str] = None
