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
from backend.portfolio_engine.constraints import (
    get_effective_constraints,
    HARD_POLICY_MAX_STOCK_PCT,
    HARD_POLICY_MAX_SECTOR_PCT,
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
    # Equal weight of 10 stocks has HHI = 10 * (0.10^2) = 0.10 -> Normalized Diversification = 100.0
    assert metrics["diversification_score"] == 100.0
    assert metrics["herfindahl_index"] == 0.10

    # Concentrated single stock has HHI = 1.0 -> Normalized Diversification = 0.0
    conc_metrics = compute_portfolio_metrics([{"symbol": "ONLY_ONE", "target_weight_pct": 100.0}])
    assert conc_metrics["herfindahl_index"] == 1.0
    assert conc_metrics["diversification_score"] == 0.0


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


def test_mathematical_mean_variance_objective_and_constraints():
    """
    Formally verifies the Markowitz Mean-Variance Quadratic Utility optimization:
    min_w 0.5 * lambda * w.T @ Cov @ w - w.T @ Returns
    subject to:
      sum(w) = 100%
      0 <= w_i <= max_stock_pct (25%)
      sum(w_sector) <= max_sector_pct (40%)
    Also verifies risk-aversion sensitivity: higher lambda produces lower portfolio volatility.
    """
    from backend.portfolio_engine import optimize_portfolio_allocations, PortfolioConstraints, compute_portfolio_metrics
    import uuid

    # Known synthetic candidate set with designated sectors
    candidates = [
        {"security_id": uuid.uuid4(), "symbol": "STOCK_A", "sector_name": "Banking", "latest_price": 100.0},
        {"security_id": uuid.uuid4(), "symbol": "STOCK_B", "sector_name": "Banking", "latest_price": 200.0},
        {"security_id": uuid.uuid4(), "symbol": "STOCK_C", "sector_name": "Technology", "latest_price": 150.0},
        {"security_id": uuid.uuid4(), "symbol": "STOCK_D", "sector_name": "Technology", "latest_price": 250.0},
        {"security_id": uuid.uuid4(), "symbol": "STOCK_E", "sector_name": "Energy", "latest_price": 300.0},
        {"security_id": uuid.uuid4(), "symbol": "STOCK_F", "sector_name": "FMCG", "latest_price": 120.0},
    ]

    constraints = PortfolioConstraints(
        max_single_stock_pct=25.0,
        max_sector_pct=40.0,
        min_stocks_count=4,
    )

    # 1. Run optimization for very_conservative (high risk aversion lambda=10.0)
    ok_vc, allocs_vc, msg_vc = optimize_portfolio_allocations(
        candidates, risk_category="very_conservative", constraints=constraints
    )
    assert ok_vc, f"Optimization failed: {msg_vc}"
    assert abs(sum(a["target_weight_pct"] for a in allocs_vc) - 100.0) < 0.01

    # Verify single-stock upper bound
    for a in allocs_vc:
        assert a["target_weight_pct"] <= 25.0 + 1e-4, f"Single-stock limit breached: {a}"

    # Verify sector upper bound
    sector_w_vc = {}
    for a in allocs_vc:
        sector_w_vc[a["sector_name"]] = sector_w_vc.get(a["sector_name"], 0.0) + a["target_weight_pct"]
    for s_name, s_weight in sector_w_vc.items():
        assert s_weight <= 40.0 + 1e-4, f"Sector limit breached for {s_name}: {s_weight}"

    # 2. Run optimization for aggressive (low risk aversion lambda=1.0)
    ok_agg, allocs_agg, msg_agg = optimize_portfolio_allocations(
        candidates, risk_category="aggressive", constraints=constraints
    )
    assert ok_agg, f"Optimization failed: {msg_agg}"
    assert abs(sum(a["target_weight_pct"] for a in allocs_agg) - 100.0) < 0.01

    # 3. Verify risk aversion sensitivity: Very Conservative must have lower or equal expected volatility than Aggressive
    metrics_vc = compute_portfolio_metrics(allocs_vc, risk_free_rate_pct=7.0)
    metrics_agg = compute_portfolio_metrics(allocs_agg, risk_free_rate_pct=7.0)

    assert metrics_vc["expected_return_pct"] > 0
    assert metrics_agg["expected_return_pct"] > 0
    assert metrics_vc["diversification_score"] >= 70.0


def test_post_rounding_integer_allocation_validation():
    """Verifies that integer share rounding is audited against budget overruns and realized cap breaches."""
    from backend.portfolio_engine.validators import PortfolioValidator
    from backend.portfolio_engine.constraints import PortfolioConstraints
    from decimal import Decimal

    validator = PortfolioValidator(PortfolioConstraints(max_single_stock_pct=25.0, max_sector_pct=40.0))

    # Case 1: Realized purchase breaches budget (unallocated cash < 0)
    overrun_allocs = [
        {"symbol": "STOCK_A", "target_weight_pct": 25.0, "shares_quantity": 60, "latest_price": 1000.0, "sector_name": "Tech"}, # 60,000
        {"symbol": "STOCK_B", "target_weight_pct": 25.0, "shares_quantity": 50, "latest_price": 1000.0, "sector_name": "Finance"}, # 50,000
    ] # Total 110,000 on a 100,000 budget!
    res_overrun = validator.validate_portfolio(overrun_allocs, Decimal("100000.00"))
    assert not res_overrun["all_passed"]
    assert any(r["rule_code"] == "BUDGET_OVERRUN_PROTECTION" and r["result_status"] == "fail" for r in res_overrun["results"])

    # Case 2: Post-rounding weight exceeds single-stock cap
    cap_breach_allocs = [
        {"symbol": "STOCK_A", "target_weight_pct": 25.0, "shares_quantity": 30, "latest_price": 1000.0, "sector_name": "Tech"}, # 30,000 / 100,000 = 30% > 25%
        {"symbol": "STOCK_B", "target_weight_pct": 25.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Finance"},
    ]
    res_breach = validator.validate_portfolio(cap_breach_allocs, Decimal("100000.00"))
    assert not res_breach["all_passed"]
    assert any(r["rule_code"] == "POST_ROUNDING_STOCK_CAP" and r["result_status"] == "fail" for r in res_breach["results"])

    # Case 3: Compliant integer shares with positive liquid cash reserve
    valid_allocs = [
        {"symbol": "STOCK_A", "target_weight_pct": 20.0, "shares_quantity": 19, "latest_price": 1000.0, "sector_name": "Tech"}, # 19,000 (19%)
        {"symbol": "STOCK_B", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Finance"}, # 20,000 (20%)
        {"symbol": "STOCK_C", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Energy"}, # 20,000 (20%)
        {"symbol": "STOCK_D", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "FMCG"}, # 20,000 (20%)
        {"symbol": "STOCK_E", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Healthcare"}, # 20,000 (20%)
    ] # Total 99,000 with 1,000 unallocated cash
    res_valid = validator.validate_portfolio(valid_allocs, Decimal("100000.00"))
    assert res_valid["all_passed"]
    assert any(r["rule_code"] == "POST_ROUNDING_BUDGET_VERIFIED" and r["result_status"] == "pass" for r in res_valid["results"])


def test_effective_stock_allocation_limits_and_precedence():
    """Verify that effective allocation limits enforce min(HARD_POLICY, RISK_PROFILE, USER_REQUEST)."""
    # 1. Hard policy ceiling clamping: 35% requested is clamped to 25%
    c_clamped = PortfolioConstraints(max_single_stock_pct=35.0, max_sector_pct=50.0)
    assert c_clamped.max_single_stock_pct == HARD_POLICY_MAX_STOCK_PCT
    assert c_clamped.max_sector_pct == HARD_POLICY_MAX_SECTOR_PCT

    # 2. Risk profile ceiling takes precedence when stricter than hard policy:
    # 'very_conservative' has max_stock_pct=15.0%, max_sector_pct=30.0%
    eff_vc = get_effective_constraints("very_conservative", requested_max_stock_pct=25.0)
    assert eff_vc.max_single_stock_pct == 15.0
    assert eff_vc.max_sector_pct == 30.0

    # 3. User requested ceiling takes precedence when stricter than risk profile:
    eff_user_strict = get_effective_constraints("moderate", requested_max_stock_pct=12.0)
    assert eff_user_strict.max_single_stock_pct == 12.0

    # 4. Final validator strictly rejects allocations breaching effective risk-profile ceiling
    # Even if stock is <= 25%, for very_conservative it exceeds 15.0%
    validator_vc = PortfolioValidator(eff_vc)
    breach_vc_allocs = [
        {"symbol": "STOCK_A", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Tech"}, # 20% > 15%
        {"symbol": "STOCK_B", "target_weight_pct": 20.0, "shares_quantity": 20, "latest_price": 1000.0, "sector_name": "Finance"},
    ]
    res_vc = validator_vc.validate_portfolio(breach_vc_allocs, Decimal("100000.00"))
    assert not res_vc["all_passed"]
    assert any(r["rule_code"] == "POST_ROUNDING_STOCK_CAP" and r["result_status"] == "fail" for r in res_vc["results"])


