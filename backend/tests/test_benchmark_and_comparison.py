"""
Tests for Quantitative Backtesting Benchmarks, Explanation Citations, and Version Comparison APIs.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import UUID

from backend.main import app
from backend.database import SessionLocal
from backend.portfolio_engine.backtest import PortfolioBacktestEngine

client = TestClient(app)


def test_quantitative_backtest_benchmark_engine():
    """Verify that the quantitative backtest engine computes valid metrics across all 3 strategies."""
    db = SessionLocal()
    try:
        engine = PortfolioBacktestEngine(db)
        results = engine.run_benchmark_comparison(
            risk_category="moderate",
            investment_amount=100000.0,
            max_single_stock_pct=25.0,
            max_sector_pct=40.0,
        )

        assert "strategies" in results
        strats = results["strategies"]

        # 1. Optimized
        assert "optimized" in strats
        opt = strats["optimized"]
        assert opt["annualized_return_pct"] > 0
        assert opt["annualized_volatility_pct"] > 0
        assert opt["diversification_score"] > 70.0
        assert opt["max_drawdown_pct"] >= 0

        # 2. Equal Weight
        assert "equal_weight" in strats
        eq = strats["equal_weight"]
        assert eq["annualized_return_pct"] > 0
        assert eq["diversification_score"] > 80.0

        # 3. Market Proxy
        assert "market_index" in strats
        mkt = strats["market_index"]
        assert mkt["annualized_return_pct"] > 0
        # Market cap weighting is more concentrated, so diversification score should be lower than equal weight
        assert mkt["diversification_score"] <= eq["diversification_score"]

        assert len(results["key_findings"]) >= 3
    finally:
        db.close()


def test_benchmark_api_endpoint():
    """Verify GET /api/v1/portfolios/benchmark-evaluation endpoint."""
    res = client.get("/api/v1/portfolios/benchmark-evaluation?risk_category=growth&amount=250000")
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["risk_category"] == "growth"
    assert "strategies" in data
    assert "optimized" in data["strategies"]


def test_portfolio_version_comparison_and_explanations_endpoints():
    """Verify comparing two generated versions side-by-side and retrieving dedicated explanations."""
    # 1. Generate Version 1 (Moderate)
    v1_res = client.post(
        "/api/v1/portfolio-generation-requests",
        json={
            "portfolio_name": "Comparative Test Portfolio",
            "investment_amount": 150000.0,
            "currency_code": "INR",
            "investment_horizon_months": 36,
            "preferences": {"max_single_stock_weight_pct": 25.0, "max_sector_weight_pct": 40.0},
        },
    )
    assert v1_res.status_code == 201, v1_res.text
    v1_data = v1_res.json()
    portfolio_id = v1_data["portfolio_id"]
    v1_id = v1_data["portfolio_version_id"]

    # 2. Generate Version 2 (Growth)
    v2_res = client.post(
        "/api/v1/portfolio-generation-requests",
        json={
            "portfolio_name": "Comparative Test Portfolio",
            "investment_amount": 150000.0,
            "currency_code": "INR",
            "investment_horizon_months": 72,
            "preferences": {"max_single_stock_weight_pct": 30.0, "max_sector_weight_pct": 45.0},
        },
    )
    assert v2_res.status_code == 201, v2_res.text
    v2_data = v2_res.json()
    v2_id = v2_data["portfolio_version_id"]

    # 3. Dedicated Explanations Endpoint
    exp_res = client.get(f"/api/v1/portfolios/{portfolio_id}/versions/{v1_id}/explanations")
    assert exp_res.status_code == 200, exp_res.text
    exp_data = exp_res.json()
    assert exp_data["version_id"] == v1_id
    assert exp_data["count"] >= 1
    assert any(e["explanation_type"] == "portfolio" for e in exp_data["explanations"])

    # 4. Compare Versions Endpoint
    comp_res = client.post(
        f"/api/v1/portfolios/{portfolio_id}/compare",
        json={"version_a_id": v1_id, "version_b_id": v2_id},
    )
    assert comp_res.status_code == 200, comp_res.text
    comp_data = comp_res.json()
    assert comp_data["portfolio_id"] == portfolio_id
    assert "deltas" in comp_data
    assert "delta_return_pct" in comp_data["deltas"]
    assert "holdings_comparison" in comp_data
    assert len(comp_data["holdings_comparison"]) >= 3

    # 5. List Portfolio Versions Endpoint
    ver_list_res = client.get(f"/api/v1/portfolios/{portfolio_id}/versions")
    assert ver_list_res.status_code == 200, ver_list_res.text
    versions_list = ver_list_res.json()
    assert len(versions_list) >= 2
    assert any(v["portfolio_version_id"] == v1_id for v in versions_list)

    # 6. Universal Compare Endpoint (Cross-Portfolio or Same Portfolio)
    univ_res = client.post(
        "/api/v1/portfolios/compare",
        json={"version_a_id": v1_id, "version_b_id": v2_id},
    )
    assert univ_res.status_code == 200, univ_res.text
    univ_data = univ_res.json()
    assert "deltas" in univ_data
    assert "holdings_comparison" in univ_data


def test_export_portfolio_orders_json_and_csv():
    """Verify exporting executable trade order baskets in JSON, standard CSV, and Zerodha formats."""
    # 1. Create a portfolio version
    gen_res = client.post(
        "/api/v1/portfolio-generation-requests",
        json={
            "portfolio_name": "Order Basket Export Portfolio",
            "investment_amount": 200000.0,
            "currency_code": "INR",
            "investment_horizon_months": 48,
            "preferences": {"max_single_stock_weight_pct": 25.0, "max_sector_weight_pct": 40.0},
        },
    )
    assert gen_res.status_code == 201, gen_res.text
    data = gen_res.json()
    pid = data["portfolio_id"]
    vid = data["portfolio_version_id"]

    # 2. JSON export
    res_json = client.get(f"/api/v1/portfolios/{pid}/versions/{vid}/export-orders?export_format=json")
    assert res_json.status_code == 200, res_json.text
    json_data = res_json.json()
    assert json_data["total_orders"] >= 3
    assert json_data["investment_amount"] == 200000.0
    first_order = json_data["orders"][0]
    assert first_order["action"] == "BUY"
    assert first_order["shares_quantity"] > 0
    assert first_order["exchange"] == "NSE"

    # 3. Standard CSV export
    res_csv = client.get(f"/api/v1/portfolios/{pid}/versions/{vid}/export-orders?export_format=csv")
    assert res_csv.status_code == 200, res_csv.text
    assert "text/csv" in res_csv.headers["content-type"]
    assert "Symbol,Security Name,Sector" in res_csv.text
    assert "Cash Reserve (INR)" in res_csv.text

    # 4. Zerodha Kite basket CSV export
    res_zk = client.get(f"/api/v1/portfolios/{pid}/versions/{vid}/export-orders?export_format=zerodha_csv")
    assert res_zk.status_code == 200, res_zk.text
    assert "text/csv" in res_zk.headers["content-type"]
    assert "Instrument,Exchange,Action,Order Type,Quantity,Price,Product" in res_zk.text
    assert "BUY,LIMIT" in res_zk.text

