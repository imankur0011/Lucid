"""
Unit and Integration Tests for Portfolio Deletion, Permanent Account Deletion,
and Data Export (User Data Management & GDPR/SEBI Compliance).
"""

import pytest
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import get_db, SessionLocal
from backend.models import (
    AppUser,
    UserProfile,
    UserPreference,
    UserConsent,
    FinancialGoal,
    RiskAssessment,
    RiskAssessmentAnswer,
    InvestorPortfolio,
    PortfolioGenerationRequest,
    PortfolioVersion,
    PortfolioSecurityDecision,
    PortfolioVersionConstraint,
    RecommendationExplanation,
    PortfolioValidationRun,
    PortfolioValidationResult,
    PortfolioScenario,
    ExistingPortfolio,
    ExistingPortfolioHolding,
    PortfolioDiagnosis,
    RebalanceSuggestion,
    AuditEvent,
    Security,
    StrategyVersion,
)
from backend.auth.dependencies import create_access_token
from backend.api.v1.auth import hash_password


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    return TestClient(app)


def get_first_listing_and_sec(db):
    from backend.models import InstrumentListing
    listing = db.query(InstrumentListing).first()
    if listing:
        return listing.listing_id, listing.security_id
    sec = db.query(Security).first()
    sec_id = sec.security_id if sec else uuid.uuid4()
    return uuid.uuid4(), sec_id


def get_first_strategy_version_id(db):
    strat = db.query(StrategyVersion).first()
    if strat:
        return strat.strategy_version_id
    strat_id = uuid.uuid4()
    return strat_id


def create_test_user(db, email_prefix="del_test", password="SecurePassword123!"):
    user_id = uuid.uuid4()
    user = AppUser(
        user_id=user_id,
        identity_provider="local-test",
        identity_subject=f"sub-{user_id}",
        email=f"{email_prefix}_{uuid.uuid4().hex[:6]}@lucidtest.local",
        password_hash=hash_password(password),
        account_status="active",
    )
    db.add(user)

    profile = UserProfile(
        user_id=user_id,
        display_name="Test Investor",
        country_code="IN",
        preferred_currency="INR",
        investment_experience="intermediate",
        investment_knowledge_level="intermediate",
    )
    db.add(profile)

    prefs = UserPreference(
        user_id=user_id,
        email_notifications_enabled=True,
        in_app_notifications_enabled=True,
    )
    db.add(prefs)
    db.commit()
    db.refresh(user)
    return user


def create_full_test_portfolio(db, user_id):
    strat_ver_id = get_first_strategy_version_id(db)
    listing_id, sec_id = get_first_listing_and_sec(db)

    # Goal & Risk Assessment
    goal = FinancialGoal(
        goal_id=uuid.uuid4(),
        user_id=user_id,
        goal_name="Retirement Fund",
        goal_type="retirement",
        target_amount=Decimal("1000000.00"),
        priority=1,
        goal_status="active",
    )
    db.add(goal)

    ra = RiskAssessment(
        risk_assessment_id=uuid.uuid4(),
        user_id=user_id,
        questionnaire_version="1.0",
        risk_category="moderate",
        risk_tolerance_score=Decimal("65.0"),
        assessment_status="completed",
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
    )
    db.add(ra)
    db.commit()

    # Portfolio & Generation Request
    pf = InvestorPortfolio(
        portfolio_id=uuid.uuid4(),
        user_id=user_id,
        portfolio_name="Alpha Core Growth",
        portfolio_status="active",
    )
    db.add(pf)

    gen_req = PortfolioGenerationRequest(
        generation_request_id=uuid.uuid4(),
        portfolio_id=pf.portfolio_id,
        user_id=user_id,
        goal_id=goal.goal_id,
        risk_assessment_id=ra.risk_assessment_id,
        request_type="create",
        request_status="succeeded",
        requested_amount=Decimal("250000.00"),
    )
    db.add(gen_req)

    # Version
    pv = PortfolioVersion(
        portfolio_version_id=uuid.uuid4(),
        portfolio_id=pf.portfolio_id,
        generation_request_id=gen_req.generation_request_id,
        strategy_version_id=strat_ver_id,
        version_number=1,
        version_status="generated",
        investment_amount=Decimal("250000.00"),
        risk_category="moderate",
        expected_return_pct=Decimal("14.5"),
        expected_volatility_pct=Decimal("12.2"),
        diversification_score=Decimal("88.5"),
    )
    db.add(pv)

    # Security Decision
    dec = PortfolioSecurityDecision(
        decision_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        security_id=sec_id,
        listing_id=listing_id,
        decision_status="selected",
        target_weight_pct=Decimal("10.000000"),
        decision_reason="Strong moat and return on equity.",
    )
    db.add(dec)

    # Constraint
    c = PortfolioVersionConstraint(
        portfolio_constraint_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        constraint_code="max_sector_exposure",
        operator="<=",
        comparison_value=Decimal("0.25"),
        is_mandatory=True,
        applied=True,
    )
    db.add(c)

    # Explanation
    exp = RecommendationExplanation(
        explanation_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        decision_id=dec.decision_id,
        explanation_type="selection",
        title="Holding Rationale",
        explanation_text="Robust margin expansion and balance sheet strength.",
        display_order=1,
    )
    db.add(exp)

    # Validation Run & Result
    vrun = PortfolioValidationRun(
        validation_run_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        rule_set_version="1.0",
        calculation_engine_version="1.0",
        validation_status="passed",
    )
    db.add(vrun)

    vres = PortfolioValidationResult(
        validation_result_id=uuid.uuid4(),
        validation_run_id=vrun.validation_run_id,
        rule_code="SEBI_SECTOR_CAP",
        result_status="pass",
        severity="info",
        security_id=sec_id,
        actual_value=Decimal("0.20"),
        threshold_value=Decimal("0.40"),
        result_message="Compliant with 40% sector cap rule.",
    )
    db.add(vres)

    # Scenario
    scen = PortfolioScenario(
        portfolio_scenario_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        scenario_code="macro_rate_shock",
        scenario_name="50 bps Rate Tightening",
        scenario_type="stress",
        estimated_change_pct=Decimal("-3.2"),
        result_summary="Controlled drawdown within risk budget.",
    )
    db.add(scen)

    db.commit()
    db.refresh(pf)
    return pf


# =========================================================================
# 1. PORTFOLIO DELETION TESTS
# =========================================================================

def test_delete_portfolio_success(client, db_session):
    user = create_test_user(db_session, "pf_del_ok")
    pf = create_full_test_portfolio(db_session, user.user_id)
    pf_id = pf.portfolio_id
    user_id = user.user_id
    token = create_access_token(user_id, user.email)

    # Verify portfolio exists in DB
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf_id).first() is not None

    response = client.delete(
        f"/api/v1/portfolios/{pf_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["portfolio_id"] == str(pf_id)

    # Confirm cascading deletion in database
    db_session.expire_all()
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf_id).first() is None
    assert db_session.query(PortfolioVersion).filter_by(portfolio_id=pf_id).count() == 0
    assert db_session.query(PortfolioGenerationRequest).filter_by(portfolio_id=pf_id).count() == 0

    # Confirm user account is completely intact
    assert db_session.query(AppUser).filter_by(user_id=user_id).first() is not None


def test_delete_portfolio_unauthorized_other_user(client, db_session):
    user1 = create_test_user(db_session, "user1")
    user2 = create_test_user(db_session, "user2")
    pf1 = create_full_test_portfolio(db_session, user1.user_id)
    token2 = create_access_token(user2.user_id, user2.email)

    # User 2 attempts to delete User 1's portfolio -> 403 Forbidden
    response = client.delete(
        f"/api/v1/portfolios/{pf1.portfolio_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 403

    # Ensure User 1's portfolio was NOT deleted
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf1.portfolio_id).first() is not None


def test_batch_delete_portfolios(client, db_session):
    user = create_test_user(db_session, "batch_user")
    pf1 = create_full_test_portfolio(db_session, user.user_id)
    pf2 = create_full_test_portfolio(db_session, user.user_id)
    pf3 = create_full_test_portfolio(db_session, user.user_id)
    token = create_access_token(user.user_id, user.email)

    pf1_id = pf1.portfolio_id
    pf2_id = pf2.portfolio_id
    pf3_id = pf3.portfolio_id

    assert db_session.query(InvestorPortfolio).filter_by(user_id=user.user_id).count() == 3

    # Batch delete pf1 and pf2
    response = client.post(
        "/api/v1/portfolios/batch-delete",
        headers={"Authorization": f"Bearer {token}"},
        json={"portfolio_ids": [str(pf1_id), str(pf2_id)]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_count"] == 2

    db_session.expire_all()
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf1_id).first() is None
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf2_id).first() is None
    # pf3 must still remain intact
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf3_id).first() is not None
    assert db_session.query(InvestorPortfolio).filter_by(user_id=user.user_id).count() == 1


def test_batch_delete_unauthorized_does_not_affect_other_user(client, db_session):
    user1 = create_test_user(db_session, "b_user1")
    user2 = create_test_user(db_session, "b_user2")
    pf1 = create_full_test_portfolio(db_session, user1.user_id)
    token2 = create_access_token(user2.user_id, user2.email)

    # User 2 attempts batch deletion with User 1's portfolio ID
    response = client.post(
        "/api/v1/portfolios/batch-delete",
        headers={"Authorization": f"Bearer {token2}"},
        json={"portfolio_ids": [str(pf1.portfolio_id)]},
    )
    assert response.status_code == 200
    assert response.json()["deleted_count"] == 0

    # User 1's portfolio must remain untouched
    db_session.expire_all()
    assert db_session.query(InvestorPortfolio).filter_by(portfolio_id=pf1.portfolio_id).first() is not None


def test_delete_all_portfolios(client, db_session):
    user = create_test_user(db_session, "del_all_user")
    pf1 = create_full_test_portfolio(db_session, user.user_id)
    pf2 = create_full_test_portfolio(db_session, user.user_id)
    token = create_access_token(user.user_id, user.email)

    assert db_session.query(InvestorPortfolio).filter_by(user_id=user.user_id).count() == 2

    # Delete all portfolios
    response = client.delete(
        "/api/v1/portfolios",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_count"] == 2

    db_session.expire_all()
    # All portfolios gone
    assert db_session.query(InvestorPortfolio).filter_by(user_id=user.user_id).count() == 0
    # User account and financial goals MUST remain intact
    assert db_session.query(AppUser).filter_by(user_id=user.user_id).first() is not None
    assert db_session.query(FinancialGoal).filter_by(user_id=user.user_id).count() >= 1


def test_delete_portfolio_not_found(client, db_session):
    user = create_test_user(db_session, "pf_nf")
    token = create_access_token(user.user_id, user.email)
    fake_id = uuid.uuid4()

    response = client.delete(
        f"/api/v1/portfolios/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_delete_imported_portfolio(client, db_session):
    user = create_test_user(db_session, "import_del")
    token = create_access_token(user.user_id, user.email)

    listing_id, sec_id = get_first_listing_and_sec(db_session)
    ep = ExistingPortfolio(
        existing_portfolio_id=uuid.uuid4(),
        user_id=user.user_id,
        portfolio_name="Zerodha Import",
        source_type="file_import",
        source_name="zerodha_holdings.csv",
        portfolio_status="active",
        as_of_date=datetime.now(timezone.utc).date(),
    )
    db_session.add(ep)

    holding = ExistingPortfolioHolding(
        existing_portfolio_holding_id=uuid.uuid4(),
        existing_portfolio_id=ep.existing_portfolio_id,
        security_id=sec_id,
        listing_id=listing_id,
        quantity=Decimal("50"),
        average_purchase_price=Decimal("1500.00"),
        market_value=Decimal("75000.00"),
    )
    db_session.add(holding)

    diag = PortfolioDiagnosis(
        portfolio_diagnosis_id=uuid.uuid4(),
        existing_portfolio_id=ep.existing_portfolio_id,
        diagnosis_status="completed",
        summary="High concentration in financial services.",
    )
    db_session.add(diag)

    reb = RebalanceSuggestion(
        rebalance_suggestion_id=uuid.uuid4(),
        portfolio_diagnosis_id=diag.portfolio_diagnosis_id,
        security_id=sec_id,
        suggested_action="sell",
        current_quantity=Decimal("50"),
        target_quantity=Decimal("30"),
        current_value=Decimal("75000.00"),
        target_value=Decimal("45000.00"),
        change_value=Decimal("-30000.00"),
        explanation="Trim to conform to sector bounds.",
    )
    db_session.add(reb)
    db_session.commit()

    ep_id = ep.existing_portfolio_id
    diag_id = diag.portfolio_diagnosis_id
    reb_id = reb.rebalance_suggestion_id

    # Delete imported portfolio
    response = client.delete(
        f"/api/v1/diagnosis/portfolios/{ep_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify deleted
    db_session.expire_all()
    assert db_session.query(ExistingPortfolio).filter_by(existing_portfolio_id=ep_id).first() is None
    assert db_session.query(PortfolioDiagnosis).filter_by(portfolio_diagnosis_id=diag_id).first() is None
    assert db_session.query(RebalanceSuggestion).filter_by(rebalance_suggestion_id=reb_id).first() is None


# =========================================================================
# 2. DATA EXPORT TESTS (GDPR / SEBI PORTABILITY)
# =========================================================================

def test_export_user_account_data(client, db_session):
    user = create_test_user(db_session, "export_test")
    pf = create_full_test_portfolio(db_session, user.user_id)
    token = create_access_token(user.user_id, user.email)

    response = client.get(
        "/api/v1/profile/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["account"]["email"] == user.email
    assert data["profile"]["display_name"] == "Test Investor"
    assert len(data["financial_goals"]) >= 1
    assert len(data["risk_assessments"]) >= 1
    assert len(data["portfolios"]) >= 1
    assert data["portfolios"][0]["portfolio_name"] == "Alpha Core Growth"


# =========================================================================
# 3. PERMANENT ACCOUNT DELETION TESTS
# =========================================================================

def test_account_deletion_requires_exact_phrase(client, db_session):
    user = create_test_user(db_session, "phrase_test")
    token = create_access_token(user.user_id, user.email)

    # Incomplete phrase
    response = client.post(
        "/api/v1/profile/delete-account",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "SecurePassword123!", "confirmation_phrase": "delete account"},
    )
    assert response.status_code == 400
    assert "DELETE MY ACCOUNT" in response.json()["detail"]


def test_account_deletion_wrong_password_rejected(client, db_session):
    user = create_test_user(db_session, "pwd_test", password="CorrectPassword123!")
    token = create_access_token(user.user_id, user.email)

    response = client.post(
        "/api/v1/profile/delete-account",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "WrongPassword!", "confirmation_phrase": "DELETE MY ACCOUNT"},
    )
    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]


def test_full_account_deletion_flow(client, db_session):
    password = "SuperSecretPassword123!"
    user = create_test_user(db_session, "full_del", password=password)
    user_id = user.user_id
    pf = create_full_test_portfolio(db_session, user_id)
    token = create_access_token(user_id, user.email)

    # Add audit event for user
    audit = AuditEvent(
        audit_event_id=uuid.uuid4(),
        actor_user_id=user_id,
        action_code="PORTFOLIO_GENERATE",
        resource_type="portfolio",
        resource_id=pf.portfolio_id,
        outcome="success",
    )
    audit_id = audit.audit_event_id
    db_session.add(audit)
    db_session.commit()

    # Execute full account deletion
    response = client.post(
        "/api/v1/profile/delete-account",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": password, "confirmation_phrase": "DELETE MY ACCOUNT"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "permanently_deleted"

    # Verify database state
    db_session.expire_all()
    # 1. User is deleted
    assert db_session.query(AppUser).filter_by(user_id=user_id).first() is None
    # 2. Profile is deleted
    assert db_session.query(UserProfile).filter_by(user_id=user_id).first() is None
    # 3. Portfolios are deleted
    assert db_session.query(InvestorPortfolio).filter_by(user_id=user_id).count() == 0
    # 4. Goals and assessments are deleted
    assert db_session.query(FinancialGoal).filter_by(user_id=user_id).count() == 0
    assert db_session.query(RiskAssessment).filter_by(user_id=user_id).count() == 0
    # 5. Audit event has actor_user_id set to NULL (anonymized)
    updated_audit = db_session.query(AuditEvent).filter_by(audit_event_id=audit_id).first()
    assert updated_audit is not None
    assert updated_audit.actor_user_id is None

    # 6. Verify subsequent requests using the deleted token fail with 401 or 404
    post_del_resp = client.get(
        "/api/v1/profile",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert post_del_resp.status_code in (401, 404)
