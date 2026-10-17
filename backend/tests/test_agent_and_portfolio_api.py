"""
End-to-End Tests for LangGraph Portfolio Generation, Persistence, Versioning, and Scenario Stress Testing APIs.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.main import app
from backend.database import SessionLocal
from backend.models import (
    InvestorPortfolio,
    PortfolioVersion,
    PortfolioGenerationRequest,
    PortfolioSecurityDecision,
    PortfolioValidationRun,
    RecommendationExplanation,
)

client = TestClient(app)
DEMO_USER_ID = "10000000-0000-4000-8000-000000000001"


def test_end_to_end_portfolio_generation_workflow():
    """
    Tests the complete end-to-end portfolio creation journey:
    API request -> LangGraph agent workflow -> deterministic calculation & validation -> PostgreSQL persistence.
    """
    payload = {
        "portfolio_name": "Autonomous Growth Portfolio",
        "investment_amount": 250000.0,
        "currency_code": "INR",
        "investment_horizon_months": 72,
        "preferences": {
            "excluded_sectors": [],
            "excluded_instruments": [],
            "max_single_stock_weight_pct": 25.0,
            "max_sector_weight_pct": 40.0,
            "target_stock_count": 5,
        },
        "user_prompt": "Maximize growth while maintaining prudent sector diversification across India's top leaders.",
    }

    # 1. Trigger Generation
    res = client.post("/api/v1/portfolio-generation-requests", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    portfolio_id = data["portfolio_id"]
    version_id = data["portfolio_version_id"]

    assert data["version_status"] == "generated"
    assert data["validation_status"] in ["passed", "passed_with_warnings"]
    assert float(data["investment_amount"]) == 250000.0
    assert len(data["holdings"]) >= 3, "Expected at least 3 holdings"
    assert len(data["explanations"]) >= 1, "Expected user-facing explanations"
    assert len(data["validation_results"]) >= 1, "Expected mathematical validation results"

    # Verify holdings integrity
    total_weight = sum(h["target_weight_pct"] for h in data["holdings"])
    assert abs(total_weight - 100.0) <= 0.05, f"Weights must sum to 100%, got {total_weight}"

    for h in data["holdings"]:
        assert h["shares_quantity"] >= 0
        assert float(h["target_amount"]) > 0
        assert h["decision_reason"]

    # 2. Verify Database Persistence Integrity
    db = SessionLocal()
    try:
        p_uuid = UUID(portfolio_id)
        v_uuid = UUID(version_id)

        # Check Portfolio
        port = db.query(InvestorPortfolio).filter(InvestorPortfolio.portfolio_id == p_uuid).first()
        assert port is not None
        assert str(port.user_id) == DEMO_USER_ID

        # Check Version
        ver = db.query(PortfolioVersion).filter(PortfolioVersion.portfolio_version_id == v_uuid).first()
        assert ver is not None
        assert ver.version_status == "generated"

        # Check Security Decisions
        decisions = (
            db.query(PortfolioSecurityDecision)
            .filter(PortfolioSecurityDecision.portfolio_version_id == v_uuid)
            .all()
        )
        assert len(decisions) == len(data["holdings"])

        # Check Validation Run
        val_run = (
            db.query(PortfolioValidationRun)
            .filter(PortfolioValidationRun.portfolio_version_id == v_uuid)
            .first()
        )
        assert val_run is not None
        assert val_run.validation_status in ["passed", "passed_with_warnings"]

        # Check Explanations
        exps = (
            db.query(RecommendationExplanation)
            .filter(RecommendationExplanation.portfolio_version_id == v_uuid)
            .all()
        )
        assert len(exps) == len(data["explanations"])

    finally:
        db.close()

    # 3. Test Retrieval Endpoints
    # List Portfolios
    list_res = client.get("/api/v1/portfolios")
    assert list_res.status_code == 200
    user_ports = list_res.json()
    assert any(p["portfolio_id"] == portfolio_id for p in user_ports)

    # Get Version Detail
    ver_res = client.get(f"/api/v1/portfolios/{portfolio_id}/versions/{version_id}")
    assert ver_res.status_code == 200
    assert ver_res.json()["portfolio_version_id"] == version_id

    # 4. Run Scenario Stress Testing
    # Market Shock Scenario
    shock_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/scenarios",
        json={
            "scenario_type": "market_shock",
            "scenario_name": "Severe Market Correction (-20%)",
            "drop_pct": 20.0,
        },
    )
    assert shock_res.status_code == 200, shock_res.text
    shock_data = shock_res.json()
    assert shock_data["scenario_type"] == "market_shock"
    assert float(shock_data["loss_pct"]) == 20.0
    assert float(shock_data["stressed_value"]) == 200000.0  # 250k - 20% = 200k
    assert float(shock_data["loss_amount"]) == 50000.0

    # Sector Shock Scenario
    sector_shock_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/scenarios",
        json={
            "scenario_type": "sector_shock",
            "scenario_name": "IT Sector Headwind (-15%)",
            "drop_pct": 15.0,
            "affected_sector": "Information Technology",
        },
    )
    assert sector_shock_res.status_code == 200, sector_shock_res.text
    sector_data = sector_shock_res.json()
    assert sector_data["scenario_type"] == "sector_shock"
    # Overall impact is contained because IT is only a fraction of total portfolio
    assert float(sector_data["loss_pct"]) < 15.0
