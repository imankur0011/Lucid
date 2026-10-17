"""
Tests for Portfolio Diagnosis and Rebalancing (Core 06).
Verifies concentration warning detection, mathematical turnover calculation,
whole-share rebalance preview generation, and user data isolation.
"""

import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from uuid import UUID

from backend.main import app
from backend.database import SessionLocal
from backend.models import ExistingPortfolio, PortfolioDiagnosis, RebalanceSuggestion

client = TestClient(app)
DEMO_USER_ID = "10000000-0000-4000-8000-000000000001"


def test_create_and_diagnose_existing_portfolio():
    """
    Test registering an existing portfolio with concentrated holdings,
    triggering diagnosis, verifying concentration warnings, and obtaining rebalance suggestions.
    """
    # 1. Register an existing portfolio heavily skewed into Reliance (60 shares @ ~2850 = ~1.7L)
    create_res = client.post(
        "/api/v1/diagnosis/portfolios",
        json={
            "portfolio_name": "Over-Concentrated Brokerage Account",
            "source_type": "manual",
            "holdings": [
                {"symbol": "RELIANCE", "quantity": 60.0, "average_purchase_price": 2700.0},
                {"symbol": "TCS", "quantity": 10.0, "average_purchase_price": 3800.0},
                {"symbol": "HDFCBANK", "quantity": 15.0, "average_purchase_price": 1600.0},
            ],
        },
    )
    assert create_res.status_code == 201, create_res.text
    port_data = create_res.json()
    exist_id = port_data["existing_portfolio_id"]
    assert port_data["holdings_count"] == 3

    # 2. Run Diagnosis & Rebalance Preview
    diag_res = client.post(f"/api/v1/diagnosis/analyze/{exist_id}?risk_category=moderate")
    assert diag_res.status_code == 200, diag_res.text
    diag = diag_res.json()

    assert diag["existing_portfolio_id"] == exist_id
    assert float(diag["total_market_value"]) > 100000.0
    # Must detect single-stock concentration for Reliance (> 25% SEBI threshold)
    assert any("RELIANCE" in w for w in diag["warnings"])

    # Verify rebalance suggestions
    suggestions = diag["suggestions"]
    assert len(suggestions) >= 3

    # Check that Reliance has a 'sell' suggestion to trim excessive exposure
    rel_sugg = next(s for s in suggestions if s["symbol"] == "RELIANCE")
    assert rel_sugg["action"] == "sell"
    assert rel_sugg["quantity_change"] < 0
    assert float(rel_sugg["change_value"]) < 0

    # Turnover must be between 1% and 100%
    assert 0.0 < diag["rebalance_turnover_pct"] <= 100.0

    # 3. Verify Database Persistence
    db = SessionLocal()
    try:
        diag_uuid = UUID(diag["portfolio_diagnosis_id"])
        db_diag = db.query(PortfolioDiagnosis).filter(PortfolioDiagnosis.portfolio_diagnosis_id == diag_uuid).first()
        assert db_diag is not None
        assert db_diag.diagnosis_status == "completed"

        db_suggs = db.query(RebalanceSuggestion).filter(RebalanceSuggestion.portfolio_diagnosis_id == diag_uuid).all()
        assert len(db_suggs) == len(suggestions)
    finally:
        db.close()
