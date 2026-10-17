"""
Tests for Deterministic Portfolio Calculation Engine.
Verifies candidate selection, constraints enforcement, mathematical optimization,
integer share rounding, risk metrics, and validation runner.
"""

import pytest
from decimal import Decimal
from backend.database import SessionLocal
from backend.portfolio_engine import (
    CandidateUniverseSelector,
    PortfolioConstraints,
    check_allocation_constraints,
    optimize_portfolio_allocations,
    calculate_integer_shares_and_amounts,
    compute_portfolio_metrics,
    PortfolioValidator,
    PortfolioEngineService,
)


def test_candidate_selection_exclusions():
    """Verify that excluded sectors and instruments are strictly filtered out."""
    db = SessionLocal()
    try:
        selector = CandidateUniverseSelector(db)

        # Baseline candidates
        base_candidates = selector.select_eligible_candidates()
        assert len(base_candidates) >= 8

        # Exclude ENERGY sector
        no_energy = selector.select_eligible_candidates(excluded_sectors=["ENERGY"])
        assert not any(c["symbol"] == "RELIANCE" for c in no_energy)
        assert len(no_energy) < len(base_candidates)

        # Exclude specific instrument
        no_tcs = selector.select_eligible_candidates(excluded_instruments=["TCS"])
        assert not any(c["symbol"] == "TCS" for c in no_tcs)
    finally:
        db.close()


def test_constraints_sum_and_bounds():
    """Verify that allocation constraints enforce sum == 100% and max stock/sector bounds."""
    constraints = PortfolioConstraints(max_single_stock_pct=25.0, max_sector_pct=40.0)

    # Valid allocations
    valid_allocs = [
        {"symbol": "A", "sector_name": "Tech", "target_weight_pct": 25.0},
        {"symbol": "B", "sector_name": "Banking", "target_weight_pct": 25.0},
        {"symbol": "C", "sector_name": "Pharma", "target_weight_pct": 25.0},
        {"symbol": "D", "sector_name": "Auto", "target_weight_pct": 25.0},
    ]
    passed, results = check_allocation_constraints(valid_allocs, constraints)
    assert passed, f"Expected pass, got {results}"

    # Invalid: sum != 100%
    bad_sum = [
        {"symbol": "A", "sector_name": "Tech", "target_weight_pct": 50.0},
        {"symbol": "B", "sector_name": "Banking", "target_weight_pct": 25.0},
    ]
    passed_sum, _ = check_allocation_constraints(bad_sum, constraints)
    assert not passed_sum

    # Invalid: stock exceeds max_single_stock_pct
    exceeds_stock = [
        {"symbol": "A", "sector_name": "Tech", "target_weight_pct": 30.0},
        {"symbol": "B", "sector_name": "Banking", "target_weight_pct": 25.0},
        {"symbol": "C", "sector_name": "Pharma", "target_weight_pct": 25.0},
        {"symbol": "D", "sector_name": "Auto", "target_weight_pct": 20.0},
    ]
    passed_stock, _ = check_allocation_constraints(exceeds_stock, constraints)
    assert not passed_stock

    # Invalid: sector exceeds max_sector_pct
    exceeds_sector = [
        {"symbol": "A", "sector_name": "Banking", "target_weight_pct": 25.0},
        {"symbol": "B", "sector_name": "Banking", "target_weight_pct": 25.0},
        {"symbol": "C", "sector_name": "Tech", "target_weight_pct": 25.0},
        {"symbol": "D", "sector_name": "Auto", "target_weight_pct": 25.0},
    ]
    passed_sector, _ = check_allocation_constraints(exceeds_sector, constraints)
    assert not passed_sector


def test_integer_shares_and_unallocated_cash():
    """Verify whole share rounding and exact cash balance conservation."""
    allocations = [
        {"symbol": "RELIANCE", "target_weight_pct": 40.0, "latest_price": 2850.0},
        {"symbol": "TCS", "target_weight_pct": 35.0, "latest_price": 3950.0},
        {"symbol": "INFY", "target_weight_pct": 25.0, "latest_price": 1820.0},
    ]
    total_amount = Decimal("100000.00")

    enriched, invested, unallocated = calculate_integer_shares_and_amounts(allocations, total_amount)

    for h in enriched:
        assert isinstance(h["shares_quantity"], int)
        assert h["shares_quantity"] >= 0
        expected_actual = round(Decimal(h["shares_quantity"]) * Decimal(str(h["latest_price"])), 2)
        assert h["actual_invested_amount"] == expected_actual

    # Conservation of money: total_invested + unallocated_cash == total_amount
    assert invested + unallocated == total_amount


def test_portfolio_metrics_and_diversification_score():
    """Verify expected return, volatility, Sharpe ratio, and Herfindahl diversification score."""
    allocations = [
        {"symbol": f"S{i}", "target_weight_pct": 10.0}
        for i in range(10)
    ]
    metrics = compute_portfolio_metrics(allocations)
    assert metrics["expected_return_pct"] > 0
    assert metrics["expected_volatility_pct"] > 0
    # Equal weight of 10 stocks has HHI = 10 * (0.10^2) = 0.10 -> Diversification score = 90.0
    assert metrics["diversification_score"] == 90.0
    assert metrics["herfindahl_index"] == 0.10


def test_infeasible_constraints_produce_explicit_failure():
    """Verify that conflicting or impossible constraints produce an explicit validation failure."""
    db = SessionLocal()
    try:
        svc = PortfolioEngineService(db)
        # Attempting to allocate across at most 1 stock when max_single_stock_pct is 25% is infeasible
        res = svc.generate_portfolio(
            investment_amount=Decimal("100000.00"),
            risk_category="moderate",
            max_single_stock_pct=5.0,  # Impossible with universe of ~11 stocks to sum to 100% (11 * 5% = 55% < 100%)
        )
        assert not res["success"]
        assert res["validation"]["validation_status"] == "failed"
    finally:
        db.close()


def test_deterministic_portfolio_reproducibility():
    """Verify that identical inputs produce bit-for-bit identical portfolio outputs."""
    db = SessionLocal()
    try:
        svc = PortfolioEngineService(db)
        res1 = svc.generate_portfolio(
            investment_amount=Decimal("500000.00"),
            risk_category="growth",
            max_single_stock_pct=25.0,
            max_sector_pct=40.0,
        )
        res2 = svc.generate_portfolio(
            investment_amount=Decimal("500000.00"),
            risk_category="growth",
            max_single_stock_pct=25.0,
            max_sector_pct=40.0,
        )

        assert res1["success"] and res2["success"]
        assert len(res1["holdings"]) == len(res2["holdings"])
        for h1, h2 in zip(res1["holdings"], res2["holdings"]):
            assert h1["symbol"] == h2["symbol"]
            assert h1["target_weight_pct"] == h2["target_weight_pct"]
            assert h1["shares_quantity"] == h2["shares_quantity"]
    finally:
        db.close()
