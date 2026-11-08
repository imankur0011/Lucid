"""
Tests for Stock-Specific 'Ask AI Why?' Equity Research and Explanation Experience.
Verifies the 10-section structured analysis, two-level financial parameter definitions,
whole-share mathematical proof, and contextual follow-up chat.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.models.portfolio import PortfolioVersion, PortfolioSecurityDecision

client = TestClient(app)


def test_stock_why_ten_section_breakdown():
    """Verifies that the /stocks/{symbol}/why endpoint returns all 10 structured analytical sections."""
    db = SessionLocal()
    pv = db.query(PortfolioVersion).first()
    assert pv is not None, "At least one PortfolioVersion must exist in the database for testing"

    dec = (
        db.query(PortfolioSecurityDecision)
        .filter(PortfolioSecurityDecision.portfolio_version_id == pv.portfolio_version_id)
        .first()
    )
    sym = dec.listing.symbol if dec and dec.listing else "TCS"
    db.close()

    url = f"/api/v1/portfolios/{pv.portfolio_id}/versions/{pv.portfolio_version_id}/stocks/{sym}/why"
    response = client.get(url)
    assert response.status_code == 200, f"Failed with {response.text}"
    data = response.json()

    # Core metadata
    assert data["symbol"] == sym.upper()
    assert "company_name" in data
    assert "sector" in data
    assert "shares_quantity" in data
    assert "target_weight_pct" in data

    # 10 Detailed Analytical Sections
    assert "section_1_why_selected" in data
    assert "portfolio_role" in data["section_1_why_selected"]
    assert "core_thesis" in data["section_1_why_selected"]
    assert "alternatives_evaluated" in data["section_1_why_selected"]

    assert "section_2_fundamental_analysis" in data
    params = data["section_2_fundamental_analysis"]["parameters"]
    assert len(params) >= 3, "Must include core audited parameters"
    for p in params:
        assert "parameter_name" in p
        assert "value" in p
        assert "level_1_summary" in p
        assert "what_it_means" in p["level_1_summary"]
        assert "how_to_interpret" in p["level_1_summary"]
        assert "level_2_deep_dive" in p
        assert "benchmark_comparison" in p["level_2_deep_dive"]
        assert "calculation_methodology" in p["level_2_deep_dive"]
        assert "limitations" in p["level_2_deep_dive"]

    assert "section_3_valuation_analysis" in data
    assert "trailing_pe" in data["section_3_valuation_analysis"]
    assert "valuation_verdict" in data["section_3_valuation_analysis"]

    assert "section_4_market_and_sector" in data
    assert "sector_headwinds_tailwinds" in data["section_4_market_and_sector"]

    assert "section_5_macro_and_news" in data
    assert "rbi_monetary_policy_impact" in data["section_5_macro_and_news"]
    assert len(data["section_5_macro_and_news"]["verified_exchange_filings"]) >= 1

    assert "section_6_risk_analysis" in data
    assert "systematic_risk" in data["section_6_risk_analysis"]
    assert "stress_test_simulations" in data["section_6_risk_analysis"]

    assert "section_7_why_this_allocation" in data
    sec7 = data["section_7_why_this_allocation"]
    assert "math_proof" in sec7
    assert "why_not_higher" in sec7
    assert "why_not_lower" in sec7
    assert sec7["actual_allocated_amount"] == round(data["shares_quantity"] * data["current_price"], 2)

    assert "section_8_agent_contributions" in data
    assert len(data["section_8_agent_contributions"]["contributions"]) >= 5

    assert "section_9_what_could_make_this_wrong" in data
    assert len(data["section_9_what_could_make_this_wrong"]["thesis_invalidation_catalysts"]) >= 2

    assert "section_10_final_conclusion" in data
    assert "executive_summary" in data["section_10_final_conclusion"]
    assert "suitability_statement" in data["section_10_final_conclusion"]

    assert len(data["suggested_followups"]) >= 3


def test_stock_why_contextual_follow_up_chat():
    """Verifies that follow-up questions within the stock why experience maintain stock and portfolio context."""
    db = SessionLocal()
    pv = db.query(PortfolioVersion).first()
    assert pv is not None

    dec = (
        db.query(PortfolioSecurityDecision)
        .filter(PortfolioSecurityDecision.portfolio_version_id == pv.portfolio_version_id)
        .first()
    )
    sym = dec.listing.symbol if dec and dec.listing else "TCS"
    db.close()

    url = f"/api/v1/portfolios/{pv.portfolio_id}/versions/{pv.portfolio_version_id}/stocks/{sym}/chat"
    payload = {
        "message": f"Why not allocate more capital to {sym}?",
        "history": [],
    }
    response = client.post(url, json=payload)
    assert response.status_code == 200, f"Chat failed with {response.text}"
    chat_data = response.json()

    assert "reply" in chat_data
    assert sym.upper() in chat_data["reply"].upper()
    assert "Why not higher" in chat_data["reply"] or "SEBI" in chat_data["reply"] or "shares" in chat_data["reply"]
    assert len(chat_data["suggested_followups"]) >= 2

