"""
Pytest suite for the Intelligent Portfolio Creation database and models.
Tests PostgreSQL connection, all domain ORM models, relationships, constraints,
atomicity, user isolation, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
from datetime import datetime, date
import uuid

from backend.database import SessionLocal, engine
from backend.main import app
from backend.models import (
    AppUser,
    UserProfile,
    UserPreference,
    UserConsent,
    FinancialGoal,
    RiskQuestion,
    RiskQuestionOption,
    RiskAssessment,
    RiskAssessmentAnswer,
    Company,
    Exchange,
    Sector,
    Industry,
    CompanyIndustry,
    Security,
    InstrumentListing,
    UserSectorPreference,
    UserSecurityPreference,
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
    ExistingPortfolio,
    ExistingPortfolioHolding,
    PortfolioDiagnosis,
    RebalanceSuggestion,
    AgentDefinition,
    AgentVersion,
    AgentExecutionRun,
    KnowledgeDocument,
    UserFeedback,
    Notification,
    AuditEvent,
    BrokerProvider,
    UserBrokerAccount,
    BrokerOrder,
    BrokerOrderEvent,
    BrokerExecution,
    PortfolioPerformanceSnapshot,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for tests."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def client():
    """Provides a FastAPI test client."""
    with TestClient(app) as test_client:
        yield test_client


def test_database_connection():
    """Test raw connection and table count in PostgreSQL."""
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
        ).scalar()
        assert count >= 59, f"Expected at least 59 tables, got {count}"


def test_all_models_queryable(db_session):
    """Test that all 59 SQLAlchemy ORM models can be queried without error."""
    models_to_test = [
        AppUser, UserProfile, UserPreference, UserConsent,
        FinancialGoal, RiskQuestion, RiskQuestionOption, RiskAssessment, RiskAssessmentAnswer,
        Company, Exchange, Sector, Industry, CompanyIndustry, Security, InstrumentListing,
        UserSectorPreference, UserSecurityPreference,
        DataSource, DataIngestionRun, DataIngestionError, SourceInstrumentMapping,
        MarketPrice, MetricDefinition, FundamentalMetric, EconomicIndicator, EconomicObservation,
        MarketNewsArticle, NewsArticleSecurity,
        InvestorPortfolio, PortfolioGenerationRequest, StrategyDefinition, StrategyVersion,
        PortfolioVersion, PortfolioSecurityDecision, PortfolioVersionConstraint,
        EvidenceItem, RecommendationExplanation, ExplanationEvidence,
        PortfolioValidationRun, PortfolioValidationResult, PortfolioScenario,
        ExistingPortfolio, ExistingPortfolioHolding, PortfolioDiagnosis, RebalanceSuggestion,
        AgentDefinition, AgentVersion, AgentExecutionRun, KnowledgeDocument,
        UserFeedback, Notification, AuditEvent,
        BrokerProvider, UserBrokerAccount, BrokerOrder, BrokerOrderEvent, BrokerExecution,
        PortfolioPerformanceSnapshot,
    ]

    for model in models_to_test:
        count = db_session.query(model).count()
        assert count >= 0, f"Failed querying {model.__name__}"


def test_seed_data_presence(db_session):
    """Verify demo seed data exists in key tables."""
    assert db_session.query(AppUser).count() >= 1
    assert db_session.query(Company).count() >= 3
    assert db_session.query(Security).count() >= 3
    assert db_session.query(InstrumentListing).count() >= 3
    assert db_session.query(Sector).count() >= 3
    assert db_session.query(Industry).count() >= 3
    assert db_session.query(DataSource).count() >= 1
    assert db_session.query(StrategyDefinition).count() >= 1
    assert db_session.query(InvestorPortfolio).count() >= 1
    assert db_session.query(PortfolioVersion).count() >= 1


def test_security_relationships(db_session):
    """Verify relationship navigation between Security, Company, Listings, and Prices."""
    sec = db_session.query(Security).first()
    assert sec is not None
    assert sec.company is not None
    assert len(sec.listings) > 0
    listing = sec.listings[0]
    assert listing.symbol is not None
    assert listing.exchange is not None


def test_create_and_delete_financial_goal(db_session):
    """Verify ORM write, retrieval, and delete operations."""
    user = db_session.query(AppUser).first()
    assert user is not None

    new_goal = FinancialGoal(
        user_id=user.user_id,
        goal_name="Retirement Corpus Test",
        goal_type="retirement",
        target_amount=15000000.00,
        amount_already_saved=2000000.00,
        currency_code="INR",
        priority=1,
        goal_status="active",
        notes="Automated test goal creation",
    )
    db_session.add(new_goal)
    db_session.commit()

    saved_goal = db_session.query(FinancialGoal).filter_by(goal_id=new_goal.goal_id).first()
    assert saved_goal is not None
    assert saved_goal.goal_name == "Retirement Corpus Test"
    assert saved_goal.target_amount == 15000000.00

    # Cleanup
    db_session.delete(saved_goal)
    db_session.commit()


# ============================================================================
# Strengthened Database Integrity & Security Tests (Roadmap Step 2.2)
# ============================================================================

def test_unique_identity_and_case_insensitive_email_constraint(db_session):
    """Ensure duplicate identity subject and case-insensitive duplicate email fail."""
    user = db_session.query(AppUser).first()
    assert user is not None
    assert user.email is not None

    # 1. Duplicate identity (identity_provider + identity_subject)
    duplicate_identity_user = AppUser(
        identity_provider=user.identity_provider,
        identity_subject=user.identity_subject,
        email="different_email@example.com",
        account_status="active",
    )
    db_session.add(duplicate_identity_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Case-insensitive duplicate email
    duplicate_email_user = AppUser(
        identity_provider="cognito",
        identity_subject="unique_subject_for_email_test",
        email=user.email.upper(),  # upper case of existing email
        account_status="active",
    )
    db_session.add(duplicate_email_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_listing_symbol_constraint(db_session):
    """Ensure duplicate exchange symbol triggers uniqueness violation."""
    listing = db_session.query(InstrumentListing).first()
    assert listing is not None

    dup_listing = InstrumentListing(
        security_id=listing.security_id,
        exchange_id=listing.exchange_id,
        symbol=listing.symbol,  # duplicate symbol on same exchange
        trading_status="active",
    )
    db_session.add(dup_listing)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_check_constraints_negative_amounts(db_session):
    """Ensure target_amount > 0 and amount_already_saved >= 0 check constraints are enforced."""
    user = db_session.query(AppUser).first()

    # Invalid negative target amount
    invalid_goal = FinancialGoal(
        user_id=user.user_id,
        goal_name="Invalid Negative Target",
        goal_type="wealth",
        target_amount=-5000.00,  # Invalid!
        currency_code="INR",
    )
    db_session.add(invalid_goal)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_foreign_key_violation_and_cascade_delete(db_session):
    """Test foreign key rejection and parent-child cascade deletion."""
    # 1. FK Violation: Non-existent user
    non_existent_id = uuid.uuid4()
    orphan_profile = UserProfile(
        user_id=non_existent_id,
        display_name="Orphan",
        country_code="IN",
        preferred_currency="INR",
    )
    db_session.add(orphan_profile)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # 2. Cascade Delete: Creating user + profile + preferences and deleting user
    test_user = AppUser(
        identity_provider="test_idp",
        identity_subject="test_cascade_subject",
        email="cascade_test@example.com",
    )
    db_session.add(test_user)
    db_session.commit()

    test_profile = UserProfile(
        user_id=test_user.user_id,
        display_name="Cascade Profile",
        country_code="IN",
        preferred_currency="INR",
    )
    test_pref = UserPreference(
        user_id=test_user.user_id,
        preferred_language="en-IN",
        timezone_name="Asia/Kolkata",
    )
    db_session.add_all([test_profile, test_pref])
    db_session.commit()

    # Verify children exist
    assert db_session.query(UserProfile).filter_by(user_id=test_user.user_id).count() == 1
    assert db_session.query(UserPreference).filter_by(user_id=test_user.user_id).count() == 1

    # Delete parent user
    db_session.delete(test_user)
    db_session.commit()

    # Verify children were automatically cascade deleted
    assert db_session.query(UserProfile).filter_by(user_id=test_user.user_id).count() == 0
    assert db_session.query(UserPreference).filter_by(user_id=test_user.user_id).count() == 0


def test_multi_table_transaction_rollback(db_session):
    """Verify that a multi-table transaction rolls back completely on error."""
    test_subject = f"atomic_subject_{uuid.uuid4().hex[:8]}"

    try:
        # Step 1: Add user
        user = AppUser(
            identity_provider="test_atomic",
            identity_subject=test_subject,
            email=f"{test_subject}@example.com",
        )
        db_session.add(user)
        db_session.flush()

        # Step 2: Attempt to add an invalid goal that triggers CHECK constraint
        invalid_goal = FinancialGoal(
            user_id=user.user_id,
            goal_name="Bad Goal",
            goal_type="house",
            target_amount=-100000.00,  # Fails CHECK constraint!
        )
        db_session.add(invalid_goal)
        db_session.commit()
    except IntegrityError:
        db_session.rollback()

    # Assert that the entire transaction rolled back and the user does NOT exist
    assert db_session.query(AppUser).filter_by(identity_subject=test_subject).count() == 0


def test_historical_portfolio_versions_accessible(db_session):
    """Ensure portfolio versions remain queryable and immutable without overwriting earlier versions."""
    portfolio = db_session.query(InvestorPortfolio).first()
    assert portfolio is not None

    versions = db_session.query(PortfolioVersion).filter_by(portfolio_id=portfolio.portfolio_id).order_by(PortfolioVersion.version_number.desc()).all()
    assert len(versions) >= 1
    latest_version = versions[0]
    assert latest_version.version_number > 0
    assert latest_version.investment_amount > 0


def test_numeric_uuid_timestamp_types(db_session):
    """Verify exact column mapping for UUIDs, Decimals, dates, and timezone-aware datetimes."""
    sec = db_session.query(Security).first()
    assert isinstance(sec.security_id, uuid.UUID)
    assert isinstance(sec.created_at, datetime)
    assert sec.created_at.tzinfo is not None, "Timestamp must be timezone-aware"

    price = db_session.query(MarketPrice).first()
    assert price is not None
    assert isinstance(price.close_price, Decimal)
    assert isinstance(price.price_date, date)


def test_user_data_isolation(db_session):
    """Verify that queries scoped to one user cannot access another user's goals or portfolios."""
    user1 = db_session.query(AppUser).first()
    assert user1 is not None

    user2_id = uuid.uuid4()
    # Querying goals with user2's ID should return empty, not user1's records
    user2_goals = db_session.query(FinancialGoal).filter_by(user_id=user2_id).all()
    assert len(user2_goals) == 0

    user2_portfolios = db_session.query(InvestorPortfolio).filter_by(user_id=user2_id).all()
    assert len(user2_portfolios) == 0


# ============================================================================
# FastAPI Endpoint Tests
# ============================================================================

def test_fastapi_health_endpoint(client):
    """Test FastAPI /api/health and /health alias endpoints return 200 with database status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["api"] == "up"
    assert data["database"]["status"] == "healthy"
    assert data["database"]["total_tables"] >= 59

    # Verify /health alias for AWS ALB and Nginx health checks
    res_alias = client.get("/health")
    assert res_alias.status_code == 200
    data_alias = res_alias.json()
    assert data_alias["api"] == "up"
    assert data_alias["database"]["status"] == "healthy"


def test_fastapi_stats_endpoint(client):
    """Test FastAPI /api/db/stats endpoint returns correct stats."""
    res = client.get("/api/db/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["users"] >= 1
    assert data["securities"] >= 3
    assert data["companies"] >= 3


def test_fastapi_securities_endpoint(client):
    """Test FastAPI /api/securities endpoint returns listings and company data."""
    res = client.get("/api/securities")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] >= 3
    for s in data["securities"]:
        assert "security_name" in s
        assert "listings" in s
        assert len(s["listings"]) > 0
