"""
Database models package for the Intelligent Portfolio Creation backend.
Exports all SQLAlchemy ORM models and Pydantic schemas.
"""

from backend.database.base import Base

# User domain
from backend.models.users import (
    AppUser,
    UserProfile,
    UserPreference,
    UserConsent,
)

# Investor domain
from backend.models.investor import (
    FinancialGoal,
    RiskQuestion,
    RiskQuestionOption,
    RiskAssessment,
    RiskAssessmentAnswer,
)

# Security master domain
from backend.models.security import (
    Company,
    Exchange,
    Sector,
    Industry,
    CompanyIndustry,
    Security,
    InstrumentListing,
    UserSectorPreference,
    UserSecurityPreference,
)

# Market, fundamental & economic domain
from backend.models.market_data import (
    DataSource,
    DataIngestionRun,
    DataIngestionError,
    SourceInstrumentMapping,
    MarketPrice,
    MetricDefinition,
    FundamentalMetric,
    EconomicIndicator,
    EconomicObservation,
    MarketNewsArticle,
    NewsArticleSecurity,
)

# Portfolio generation & validation domain
from backend.models.portfolio import (
    InvestorPortfolio,
    PortfolioGenerationRequest,
    StrategyDefinition,
    StrategyVersion,
    PortfolioVersion,
    PortfolioSecurityDecision,
    PortfolioVersionConstraint,
    EvidenceItem,
    RecommendationExplanation,
    ExplanationEvidence,
    PortfolioValidationRun,
    PortfolioValidationResult,
    PortfolioScenario,
)

# Diagnosis & rebalance domain
from backend.models.diagnosis import (
    ExistingPortfolio,
    ExistingPortfolioHolding,
    PortfolioDiagnosis,
    RebalanceSuggestion,
)

# Agent, telemetry & feedback domain
from backend.models.agent import (
    AgentDefinition,
    AgentVersion,
    AgentExecutionRun,
    KnowledgeDocument,
    UserFeedback,
    Notification,
    AuditEvent,
)

# Broker & performance extension domain
from backend.models.broker import (
    BrokerProvider,
    UserBrokerAccount,
    BrokerOrder,
    BrokerOrderEvent,
    BrokerExecution,
    PortfolioPerformanceSnapshot,
)

__all__ = [
    "Base",
    # Users
    "AppUser",
    "UserProfile",
    "UserPreference",
    "UserConsent",
    # Investor & Goals
    "FinancialGoal",
    "RiskQuestion",
    "RiskQuestionOption",
    "RiskAssessment",
    "RiskAssessmentAnswer",
    # Securities Master
    "Company",
    "Exchange",
    "Sector",
    "Industry",
    "CompanyIndustry",
    "Security",
    "InstrumentListing",
    "UserSectorPreference",
    "UserSecurityPreference",
    # Market Data
    "DataSource",
    "DataIngestionRun",
    "DataIngestionError",
    "SourceInstrumentMapping",
    "MarketPrice",
    "MetricDefinition",
    "FundamentalMetric",
    "EconomicIndicator",
    "EconomicObservation",
    "MarketNewsArticle",
    "NewsArticleSecurity",
    # Portfolio Generation
    "InvestorPortfolio",
    "PortfolioGenerationRequest",
    "StrategyDefinition",
    "StrategyVersion",
    "PortfolioVersion",
    "PortfolioSecurityDecision",
    "PortfolioVersionConstraint",
    "EvidenceItem",
    "RecommendationExplanation",
    "ExplanationEvidence",
    "PortfolioValidationRun",
    "PortfolioValidationResult",
    "PortfolioScenario",
    # Diagnosis
    "ExistingPortfolio",
    "ExistingPortfolioHolding",
    "PortfolioDiagnosis",
    "RebalanceSuggestion",
    # Agents & Telemetry
    "AgentDefinition",
    "AgentVersion",
    "AgentExecutionRun",
    "KnowledgeDocument",
    "UserFeedback",
    "Notification",
    "AuditEvent",
    # Broker & Performance
    "BrokerProvider",
    "UserBrokerAccount",
    "BrokerOrder",
    "BrokerOrderEvent",
    "BrokerExecution",
    "PortfolioPerformanceSnapshot",
]
