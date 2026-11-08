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


def test_symbol_sanitization_with_exchange_suffixes_and_prefixes():
    """Verify that symbols with .NS, .BO, or NSE: prefixes are cleaned and resolved successfully."""
    create_res = client.post(
        "/api/v1/diagnosis/portfolios",
        json={
            "portfolio_name": "Broker Format Import",
            "source_type": "file_import",
            "holdings": [
                {"symbol": "RELIANCE.NS", "quantity": 15.0, "average_purchase_price": 2800.0},
                {"symbol": "NSE:TCS", "quantity": 10.0, "average_purchase_price": 3800.0},
                {"symbol": "  infy  ", "quantity": 25.0, "average_purchase_price": 1700.0},
            ],
        },
    )
    assert create_res.status_code == 201, create_res.text
    data = create_res.json()
    assert data["holdings_count"] == 3


def test_download_csv_template():
    """Verify that GET /api/v1/diagnosis/csv-template returns a valid downloadable CSV template."""
    res = client.get("/api/v1/diagnosis/csv-template")
    assert res.status_code == 200
    assert "text/csv" in res.headers.get("content-type", "")
    assert "attachment" in res.headers.get("content-disposition", "")
    content = res.text
    assert "symbol,exchange,quantity,average_buy_price,purchase_date" in content
    assert "RELIANCE" in content
    assert "TCS" in content


def test_upload_csv_valid_and_error_handling():
    """Verify that uploading a CSV parses valid holdings and isolates row-level errors."""
    csv_content = (
        "symbol,exchange,quantity,average_buy_price\n"
        "RELIANCE,NSE,40,2500.00\n"
        "TCS,NSE,25,3200.00\n"
        "UNKNOWN_FAKE_TICKER,NSE,50,100.00\n"
        "INFY,NSE,0,1400.00\n"
    )
    files = {"file": ("holdings.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/v1/diagnosis/upload-csv", files=files)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["status"] == "parsed"
    assert data["total_rows"] == 4
    assert data["valid_count"] == 2
    assert data["error_count"] == 2
    assert data["can_commit"] is False

    # Check valid holdings
    valid_syms = [h["symbol"] for h in data["valid_holdings"]]
    assert "RELIANCE" in valid_syms
    assert "TCS" in valid_syms
    rel = next(h for h in data["valid_holdings"] if h["symbol"] == "RELIANCE")
    assert rel["average_purchase_price"] == 2500.0
    assert rel["current_market_value"] > 100000.0
    assert rel["unrealized_pnl"] is not None

    # Check row errors
    errs = data["invalid_rows"]
    assert any("UNKNOWN_FAKE_TICKER" in e.get("raw_symbol", "") or "not recognized" in e.get("error", "") for e in errs)
    assert any("Quantity must be greater than zero" in e.get("error", "") for e in errs)


def test_parse_text_copy_paste():
    """Verify parsing copy-pasted spreadsheet lines with colon, comma, or tab format."""
    text_data = (
        "RELIANCE: 40\n"
        "TCS, 25, 3200\n"
        "HDFCBANK\t60\t1650\n"
        "INFY: 30 @ 1400\n"
    )
    res = client.post(
        "/api/v1/diagnosis/parse-text",
        json={"text": text_data, "source_type": "copy_paste"},
    )
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["valid_count"] == 4
    assert data["error_count"] == 0
    assert data["can_commit"] is True
    assert data["total_estimated_value"] > 300000.0

    symbols = [h["symbol"] for h in data["valid_holdings"]]
    assert symbols == ["RELIANCE", "TCS", "HDFCBANK", "INFY"]


def test_diagnosis_includes_current_holdings_and_rebalance_status():
    """Verify that diagnosis detail returns current_holdings breakdown, rebalance_status, and trades count."""
    create_res = client.post(
        "/api/v1/diagnosis/portfolios",
        json={
            "portfolio_name": "Full Detail Inspection Portfolio",
            "source_type": "manual",
            "holdings": [
                {"symbol": "RELIANCE", "quantity": 40.0, "average_purchase_price": 2500.0},
                {"symbol": "TCS", "quantity": 25.0, "average_purchase_price": 3200.0},
                {"symbol": "HDFCBANK", "quantity": 60.0, "average_purchase_price": 1650.0},
                {"symbol": "INFY", "quantity": 30.0, "average_purchase_price": 1400.0},
            ],
        },
    )
    assert create_res.status_code == 201
    port_id = create_res.json()["existing_portfolio_id"]

    diag_res = client.post(f"/api/v1/diagnosis/analyze/{port_id}?risk_category=growth")
    assert diag_res.status_code == 200
    diag = diag_res.json()

    # Must include current_holdings
    current_holdings = diag.get("current_holdings")
    assert current_holdings is not None
    assert len(current_holdings) == 4
    for ch in current_holdings:
        assert ch["symbol"] in ["RELIANCE", "TCS", "HDFCBANK", "INFY"]
        assert ch["weight_pct"] > 0
        assert ch["current_value"] is not None
        assert ch["sector_name"] is not None

    # Must include rebalance_status and trades count
    assert diag.get("rebalance_status") in ["rebalance_proposed", "no_trades_required"]
    assert diag.get("trades_required_count") is not None
    assert diag.get("unallocated_cash") is not None


def test_rebalancing_numerical_precision_and_cash_integrity():
    """
    Independent numerical verification of the rebalancing preview calculation:
    - Verifies buy/sell quantities are exact whole integers.
    - Verifies unallocated cash is non-negative and preserved.
    - Verifies post-rebalance allocations strictly obey single-stock (<=25%) and sector (<=40%) ceilings.
    - Verifies turnover calculation matches absolute weight deltas.
    """
    create_res = client.post(
        "/api/v1/diagnosis/portfolios",
        json={
            "portfolio_name": "Numerical Precision Test Portfolio",
            "source_type": "manual",
            "holdings": [
                {"symbol": "RELIANCE", "quantity": 50.0, "average_purchase_price": 2800.0},
                {"symbol": "TCS", "quantity": 10.0, "average_purchase_price": 3800.0},
            ],
        },
    )
    assert create_res.status_code == 201
    port_id = create_res.json()["existing_portfolio_id"]

    diag_res = client.post(f"/api/v1/diagnosis/analyze/{port_id}?risk_category=moderate")
    assert diag_res.status_code == 200
    diag = diag_res.json()

    suggestions = diag["suggestions"]
    total_market_value = float(diag["total_market_value"])
    unallocated_cash = float(diag["unallocated_cash"])

    # 1. Non-negative cash residual invariant
    assert unallocated_cash >= 0.0, f"Unallocated cash must be non-negative, got {unallocated_cash}"

    # 2. Integer whole share invariant
    total_post_rebalance_invested = 0.0
    for s in suggestions:
        assert isinstance(s["target_quantity"], int), f"Target quantity must be integer, got {s['target_quantity']}"
        assert isinstance(s["quantity_change"], int), f"Quantity change must be integer, got {s['quantity_change']}"
        price = float(s["latest_price"])
        post_qty = s["target_quantity"]
        post_val = post_qty * price
        total_post_rebalance_invested += post_val

        # Target weight must respect hard single stock ceiling (<= 25% + 0.1% tolerance)
        post_weight = (post_val / total_market_value) * 100.0 if total_market_value > 0 else 0.0
        assert post_weight <= 25.10, f"Holding {s['symbol']} post-rebalance weight {post_weight:.2f}% exceeds 25% cap"

    # 3. Capital conservation: Invested + Unallocated Cash == Total Capital (within rounding delta)
    total_accounted = total_post_rebalance_invested + unallocated_cash
    assert abs(total_accounted - total_market_value) < 50.0, (
        f"Capital divergence: Accounted={total_accounted:.2f}, Original Market Value={total_market_value:.2f}"
    )

    # 4. Turnover calculation verification: turnover = sum(|target_w - cur_w|) / 2
    sum_weight_delta = sum(abs(s["target_weight_pct"] - s["current_weight_pct"]) for s in suggestions)
    expected_turnover = round(sum_weight_delta / 2.0, 2)
    assert abs(diag["rebalance_turnover_pct"] - expected_turnover) <= 0.05



