"""
Tests for AI Copilot's Portfolio Diagnosis & Stock-Specific Rebalancing Explanations.
Verifies:
1. Intent classification of diagnosis & rebalancing inquiries.
2. Retrieval of diagnosis copilot context and 7-part structured fiduciary explanation.
3. Whole-share BUY/SELL/HOLD trade explanations with deterministic figures.
4. Correct single-stock and sector concentration limits from risk policies.
5. Interactive conversational answers for trims, additions, non-rebalance risks, and crash simulations.
6. Integration with GET /diagnosis/{id}/explanation and POST /diagnosis/{id}/chat.
7. Universal /api/v1/chat endpoint delegation when asking about imported portfolios.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.main import app
from backend.database import SessionLocal
from backend.models import AppUser, ExistingPortfolio, PortfolioDiagnosis
from backend.auth.dependencies import create_access_token
from backend.portfolio_engine.conversational_assistant import (
    classify_user_intent,
    ConversationSession,
)
from backend.portfolio_engine.diagnosis_copilot_service import (
    get_diagnosis_copilot_context,
    generate_diagnosis_explanation,
    chat_with_diagnosis_copilot,
)

client = TestClient(app)


@pytest.fixture
def auth_context():
    """Provides a valid test user, token, and headers."""
    with SessionLocal() as db:
        user = db.query(AppUser).first()
        assert user is not None, "At least one AppUser must exist in DB"
        token = create_access_token(user.user_id, user.email)
        user_id = user.user_id

    headers = {"Authorization": f"Bearer {token}"}
    return {"user_id": user_id, "headers": headers}


@pytest.fixture
def diagnosed_portfolio(auth_context):
    """
    Creates and diagnoses a test portfolio with the user's exact reported 4-stock configuration:
    RELIANCE: 40, TCS: 25, HDFCBANK: 60, INFY: 30
    under 'very_conservative' policy (15% single-stock cap, 35% sector cap).
    """
    headers = auth_context["headers"]

    # 1. Register portfolio
    create_res = client.post(
        "/api/v1/diagnosis/portfolios",
        json={
            "portfolio_name": "My Brokerage Portfolio (Imported)",
            "source_type": "manual",
            "holdings": [
                {"symbol": "RELIANCE", "quantity": 40.0, "average_purchase_price": 2834.0},
                {"symbol": "TCS", "quantity": 25.0, "average_purchase_price": 3885.0},
                {"symbol": "HDFCBANK", "quantity": 60.0, "average_purchase_price": 1670.0},
                {"symbol": "INFY", "quantity": 30.0, "average_purchase_price": 1879.0},
            ],
        },
        headers=headers,
    )
    assert create_res.status_code == 201, create_res.text
    port_data = create_res.json()
    ep_id = port_data["existing_portfolio_id"]

    # 2. Run Diagnosis & Whole-Share Rebalance Preview under very_conservative policy
    diag_res = client.post(
        f"/api/v1/diagnosis/analyze/{ep_id}?risk_category=very_conservative",
        headers=headers,
    )
    assert diag_res.status_code == 200, diag_res.text
    diag_data = diag_res.json()

    return {
        "existing_portfolio_id": ep_id,
        "portfolio_name": "My Brokerage Portfolio (Imported)",
        "diag_data": diag_data,
    }


def test_intent_classification_routes_rebalance_queries():
    """Verifies that rebalancing trade inquiries are not classified as generic concept queries."""
    session = ConversationSession("user-1", "sess-1")

    # Specific rebalancing queries
    q1 = "Explain the rebalancing trades proposed for My Brokerage Portfolio (Imported): why were specific stocks trimmed or added, and how does this protect my capital?"
    intent1, _ = classify_user_intent(q1, session)
    assert intent1 == "PORTFOLIO_DIAGNOSIS_AND_REBALANCE"

    q2 = "Why are you trimming my Reliance holdings?"
    intent2, _ = classify_user_intent(q2, session)
    assert intent2 == "PORTFOLIO_DIAGNOSIS_AND_REBALANCE"

    q3 = "Why reduce TCS?"
    intent3, _ = classify_user_intent(q3, session)
    assert intent3 == "PORTFOLIO_DIAGNOSIS_AND_REBALANCE"

    q4 = "What happens if I don't rebalance?"
    intent4, _ = classify_user_intent(q4, session)
    assert intent4 == "PORTFOLIO_DIAGNOSIS_AND_REBALANCE"

    # General education query
    q5 = "What is rebalancing?"
    intent5, _ = classify_user_intent(q5, session)
    assert intent5 == "EXPLAIN_REBALANCING"


def test_diagnosis_copilot_service_explanation_structure(diagnosed_portfolio):
    """Verifies that generate_diagnosis_explanation produces the complete 7-part analysis."""
    ep_id = UUID(diagnosed_portfolio["existing_portfolio_id"])

    with SessionLocal() as db:
        expl = generate_diagnosis_explanation(ep_id, db=db)

    # Verify metadata
    assert expl["portfolio_name"] == "My Brokerage Portfolio (Imported)"
    assert expl["effective_stock_limit"] == 15.0  # very_conservative cap
    assert expl["effective_sector_limit"] == 35.0
    assert expl["total_market_value"] > 300000.0

    # Section 1: Portfolio Summary
    assert "section_1_portfolio_summary" in expl
    assert "very conservative" in expl["section_1_portfolio_summary"].lower()

    # Section 2: Identified Problems
    assert len(expl["section_2_problems_identified"]) > 0
    for prob in expl["section_2_problems_identified"]:
        assert "issue" in prob
        assert "policy_origin" in prob
        assert "impact" in prob

    # Section 3: Proposed Trades
    trades = expl["section_3_proposed_trades"]
    assert len(trades) > 0
    actions = {t["action"] for t in trades}
    assert "SELL" in actions
    assert "BUY" in actions

    # RELIANCE must be trimmed down to ~15%
    rel_trade = next(t for t in trades if t["symbol"] == "RELIANCE")
    assert rel_trade["action"] == "SELL"
    assert rel_trade["current_quantity"] == 40
    assert rel_trade["target_quantity"] < 40
    assert rel_trade["target_weight_pct"] <= 15.1
    assert "15.0%" in rel_trade["reason"]

    # Section 4: Why Recommended
    assert len(expl["section_4_why_recommended"]) >= 4

    # Section 5: Before vs After Comparison
    comp = expl["section_5_before_after_comparison"]
    assert "total_portfolio_value" in comp
    assert "largest_stock_weight" in comp
    assert "it_sector_exposure" in comp
    assert "diversification_score" in comp
    assert "cash_remaining" in comp

    # Section 6: Remaining Risks
    assert len(expl["section_6_remaining_risks"]) >= 3
    assert any("Systemic Market Risk" in r for r in expl["section_6_remaining_risks"])

    # Section 7: Final Summary
    assert "section_7_final_fiduciary_summary" in expl
    assert len(expl["suggested_followups"]) >= 3


def test_diagnosis_copilot_chat_stock_questions(diagnosed_portfolio):
    """Verifies that chat_with_diagnosis_copilot answers stock-specific trim/add questions."""
    ep_id = UUID(diagnosed_portfolio["existing_portfolio_id"])

    with SessionLocal() as db:
        # Question about trimming Reliance
        res_rel = chat_with_diagnosis_copilot(ep_id, "Why are you trimming my Reliance holdings?", db=db)
        assert "SELL" in res_rel["reply"]
        assert "RELIANCE" in res_rel["reply"]
        assert "15.0%" in res_rel["reply"]
        assert "40 shares" in res_rel["reply"] or "40" in res_rel["reply"]

        # Question about why not rebalance
        res_not_reb = chat_with_diagnosis_copilot(ep_id, "What happens if I don't rebalance?", db=db)
        assert "What Happens If You Do Not Rebalance?" in res_not_reb["reply"]
        assert "Concentration" in res_not_reb["reply"] or "Single-Stock" in res_not_reb["reply"]

        # Question about 30% crash
        res_crash = chat_with_diagnosis_copilot(ep_id, "What happens if the market falls 30%?", db=db)
        assert "Market Crash Simulation" in res_crash["reply"]
        assert "-30%" in res_crash["reply"]


def test_api_diagnosis_explanation_endpoint(auth_context, diagnosed_portfolio):
    """Tests GET /api/v1/diagnosis/{id}/explanation HTTP endpoint."""
    ep_id = diagnosed_portfolio["existing_portfolio_id"]
    headers = auth_context["headers"]

    resp = client.get(f"/api/v1/diagnosis/{ep_id}/explanation", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["portfolio_name"] == "My Brokerage Portfolio (Imported)"
    assert "section_1_portfolio_summary" in data
    assert "section_3_proposed_trades" in data
    assert "section_5_before_after_comparison" in data


def test_api_diagnosis_chat_endpoint(auth_context, diagnosed_portfolio):
    """Tests POST /api/v1/diagnosis/{id}/chat HTTP endpoint."""
    ep_id = diagnosed_portfolio["existing_portfolio_id"]
    headers = auth_context["headers"]

    resp = client.post(
        f"/api/v1/diagnosis/{ep_id}/chat",
        json={"message": "Why reduce TCS?"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert "reply" in data
    assert "TCS" in data["reply"]
    assert "suggested_followups" in data


def test_api_universal_chat_with_rebalance_query(auth_context, diagnosed_portfolio):
    """
    Tests POST /api/v1/chat with the exact user prompt from the ticket:
    'Explain the rebalancing trades proposed for My Brokerage Portfolio (Imported): why were specific stocks trimmed or added, and how does this protect my capital?'
    Verifies that it returns real deterministic trade rationales and NOT the generic textbook explanation.
    """
    ep_id = diagnosed_portfolio["existing_portfolio_id"]
    headers = auth_context["headers"]

    prompt = (
        "Explain the rebalancing trades proposed for My Brokerage Portfolio (Imported): "
        "why were specific stocks trimmed or added, and how does this protect my capital?"
    )

    resp = client.post(
        "/api/v1/chat",
        json={"query": prompt, "existing_portfolio_id": ep_id},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    reply = data["reply"]
    # Must NOT contain the old generic textbook response
    assert "Would you like to diagnose your current holdings to see if a rebalance is needed?" not in reply
    assert "Weight Drift > 5%" not in reply

    # Must contain actual portfolio details
    assert "My Brokerage Portfolio (Imported)" in reply or "Rebalancing Plan" in reply
    assert "Trims to Relieve Overconcentration" in reply or "SELL" in reply
    assert "Additions to Restore Diversification" in reply or "BUY" in reply

