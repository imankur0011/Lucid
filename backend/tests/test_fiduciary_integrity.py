"""
Comprehensive Fiduciary Integrity, Mathematical Robustness, and Agent Workflow Evaluation Suite.
Verifies all 10 areas of mathematical methodologies, centralized policies, feasibility checks,
Critic verdict states, bounded rework, evidence provenance, and optimizer fallbacks.

Authoritative Date: 2026-11-04
"""

import math
from decimal import Decimal
import pytest
import numpy as np

from backend.portfolio_engine.policy import (
    POLICY_RULES,
    RISK_PROFILE_POLICIES,
    RuleCategory,
    get_risk_profile_policy,
)
from backend.portfolio_engine.math_engine import (
    calculate_earnings_yield,
    calculate_cagr,
    calculate_beta_and_volatility,
    winsorize_and_zscore,
    calculate_quality_factor,
    compute_expected_annual_return,
)
from backend.portfolio_engine.feasibility import (
    check_portfolio_feasibility,
    FeasibilityCheckResult,
)
from backend.portfolio_engine.optimizer import (
    optimize_portfolio_allocations,
    _sector_constrained_fallback,
)
from backend.portfolio_engine.allocation_rounding import calculate_integer_shares_and_amounts
from backend.portfolio_engine.validators import PortfolioValidator
from backend.portfolio_engine.constraints import PortfolioConstraints
from backend.agent.schemas import (
    CriticVerdictStatus,
    CriticEvaluationOutput,
    DataQualityStatus,
    ReportingBasis,
    MetricEvidenceRecord,
)
from backend.agent.tools import critic_fiduciary_audit_tool


# ==============================================================================
# 1. MATHEMATICAL METHODOLOGY TESTS
# ==============================================================================

def test_earnings_yield_calculation_edge_cases():
    """Verifies that Earnings Yield handles positive, negative, zero, and missing PE correctly."""
    # Positive PE: 1 / 25 = 0.04
    ey, status = calculate_earnings_yield(pe_ratio=25.0)
    assert ey == 0.04
    assert status == "COMPUTED_FROM_POSITIVE_PE"

    # Negative PE (Losses): 1 / (-10) = -0.10
    ey, status = calculate_earnings_yield(pe_ratio=-10.0)
    assert ey == -0.10
    assert status == "COMPUTED_FROM_NEGATIVE_PE_LOSSES"

    # Extreme Negative PE: clamped at -0.25 to prevent extreme distortion
    ey, status = calculate_earnings_yield(pe_ratio=-2.0)
    assert ey == -0.25
    assert status == "COMPUTED_FROM_NEGATIVE_PE_LOSSES"

    # Zero PE: division by zero prevented
    ey, status = calculate_earnings_yield(pe_ratio=0.0)
    assert ey is None
    assert status == "ZERO_PE_RATIO"

    # Missing PE
    ey, status = calculate_earnings_yield(pe_ratio=None)
    assert ey is None
    assert status == "MISSING_PE_RATIO"

    # Direct EPS and Price
    ey, status = calculate_earnings_yield(eps=50.0, price=1000.0)
    assert ey == 0.05
    assert status == "COMPUTED_FROM_EPS_AND_PRICE"


def test_cagr_compounding_and_history_thresholds():
    """Verifies 3-year CAGR compounding formula and history length requirements."""
    # 3-year CAGR: 756 trading days (3 years), price doubles from 100 to 200 => ~25.99%
    cagr, status = calculate_cagr(start_price=100.0, end_price=200.0, trading_days=756)
    assert cagr is not None
    assert round(cagr, 4) == pytest.approx(0.2599, abs=1e-3)
    assert status == "AUDITED_3Y_CAGR"

    # Short history (< 700 trading days): returns annualized rate with explicit warning
    cagr, status = calculate_cagr(start_price=100.0, end_price=120.0, trading_days=252)
    assert cagr is not None
    assert round(cagr, 4) == pytest.approx(0.2000, abs=1e-3)
    assert status == "ANNUALIZED_RETURN_INSUFFICIENT_HISTORY_FOR_3Y"

    # Invalid non-positive prices
    cagr, status = calculate_cagr(start_price=-10.0, end_price=100.0, trading_days=252)
    assert cagr is None
    assert status == "INVALID_PRICE_NON_POSITIVE"


def test_beta_and_volatility_distinct_measures():
    """Verifies that Systematic Beta and Total Volatility are calculated as distinct metrics."""
    np.random.seed(42)
    bench_returns = list(np.random.normal(0.0005, 0.01, 756))
    # Asset with beta ~ 1.5 + idiosyncratic noise
    asset_returns = [1.5 * r + float(np.random.normal(0, 0.005)) for r in bench_returns]

    beta, vol, status = calculate_beta_and_volatility(asset_returns, bench_returns)
    assert beta is not None
    assert vol is not None
    assert status == "AUDITED_3Y_RISK_METRICS"
    assert beta == pytest.approx(1.5, abs=0.15)
    # Total volatility is annualized std (daily std * sqrt(252))
    assert vol > 0.15

    # Insufficient length returns None and warning
    short_beta, short_vol, short_status = calculate_beta_and_volatility([0.01] * 10, [0.01] * 10)
    assert short_beta is None
    assert short_status == "INSUFFICIENT_RETURNS_DATA"


def test_sector_normalization_small_samples_and_zero_variance():
    """Verifies robust Z-score behavior under small samples (N < 3) and zero variance."""
    # Sample < 3: statistically uninformative, returns neutral 0.0
    scores, status = winsorize_and_zscore([15.0, 20.0])
    assert scores == [0.0, 0.0]
    assert status == "SMALL_SAMPLE_SIZE_NEUTRAL_DEFAULT"

    # Zero variance: identical values
    scores, status = winsorize_and_zscore([15.0, 15.0, 15.0, 15.0])
    assert scores == [0.0, 0.0, 0.0, 0.0]
    assert status == "ZERO_VARIANCE_NEUTRAL_DEFAULT"

    # Standard distribution with outlier
    scores, status = winsorize_and_zscore([10.0, 12.0, 14.0, 16.0, 100.0])
    assert len(scores) == 5
    assert status == "WINSORIZED_ZSCORE_COMPUTED"
    # Winsorization prevents the 100.0 outlier from creating an extreme score
    assert max(scores) <= 3.0


def test_quality_score_financial_vs_non_financial():
    """Verifies that non-financial firms are penalized for high leverage while financials exclude D/E."""
    # Non-financial with D/E 0.20: high quality
    q_good, s_good = calculate_quality_factor(roe=0.25, debt_to_equity=0.20, is_financial=False)
    assert q_good > 0.40
    assert s_good == "QUALITY_COMBINED_ROE_AND_LEVERAGE"

    # Non-financial with high leverage D/E 3.50: heavily penalized
    q_leveraged, s_lev = calculate_quality_factor(roe=0.25, debt_to_equity=3.50, is_financial=False)
    assert q_leveraged < q_good

    # Financial firm (Bank) with structural D/E 5.0: D/E is excluded, judged on ROE
    q_bank, s_bank = calculate_quality_factor(roe=0.18, debt_to_equity=5.0, is_financial=True)
    assert q_bank > 0.0
    assert s_bank == "ROE_ONLY_FINANCIAL_PROFILE"


def test_expected_returns_units_and_goal_orientations():
    """Verifies that expected returns are annualized percentages and not confused with factor Z-scores."""
    # Baseline target 12.5% for moderate
    ret_balanced = compute_expected_annual_return(
        base_target_return_pct=12.5,
        quality_z=1.0,
        value_z=0.5,
        momentum_z=0.0,
        beta=1.1,
        goal="wealth_creation",
    )
    assert 12.0 <= ret_balanced <= 16.0  # Proper percentage range

    # Growth goal tilts to momentum
    ret_growth = compute_expected_annual_return(
        base_target_return_pct=15.0,
        quality_z=0.5,
        value_z=0.0,
        momentum_z=2.0,
        beta=1.3,
        goal="aggressive_growth",
    )
    assert ret_growth > ret_balanced


# ==============================================================================
# 2. CENTRALIZED POLICY SYSTEM TESTS
# ==============================================================================

def test_centralized_policy_definitions_and_rationales():
    """Verifies all hard constraints and risk profile policies have documented legal bases."""
    # Check hard ceilings
    assert POLICY_RULES["POL-ALLOC-01"].threshold == 25.0
    assert POLICY_RULES["POL-ALLOC-01"].category == RuleCategory.HARD_CONSTRAINT
    assert "SEBI" in POLICY_RULES["POL-ALLOC-01"].regulatory_basis

    assert POLICY_RULES["POL-SECT-01"].threshold == 40.0
    assert POLICY_RULES["POL-SECT-01"].category == RuleCategory.HARD_CONSTRAINT
    assert "Lucid Internal Fiduciary Risk Policy" in POLICY_RULES["POL-SECT-01"].regulatory_basis

    # Check risk profile mappings
    very_cons = get_risk_profile_policy("very_conservative")
    assert very_cons.max_single_stock_pct == 15.0
    assert very_cons.max_sector_pct == 35.0
    assert very_cons.min_holdings_count == 7

    agg = get_risk_profile_policy("aggressive")
    assert agg.max_single_stock_pct == 25.0
    assert agg.risk_aversion == 1.0


# ==============================================================================
# 3. PRE-EXECUTION FEASIBILITY CHECKER TESTS
# ==============================================================================

def test_feasibility_check_valid_portfolio():
    """Feasibility check passes when sufficient eligible securities and sectors exist."""
    candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "latest_price": 3800.0},
        {"symbol": "INFY", "sector_name": "Information Technology", "latest_price": 1600.0},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "latest_price": 1650.0},
        {"symbol": "ICICIBANK", "sector_name": "Banking & Financial Services", "latest_price": 1100.0},
        {"symbol": "RELIANCE", "sector_name": "Energy & Oil", "latest_price": 2800.0},
        {"symbol": "SUNPHARMA", "sector_name": "Healthcare & Pharmaceuticals", "latest_price": 1500.0},
    ]

    res: FeasibilityCheckResult = check_portfolio_feasibility(
        capital=100000.0,
        risk_category="moderate",
        eligible_candidates=candidates,
    )
    assert res.is_feasible is True
    assert len(res.conditions_violated) == 0
    assert res.unique_sectors_count == 4


def test_feasibility_check_insufficient_capital():
    """Feasibility check fails when capital is below ₹1,000 threshold."""
    candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "latest_price": 3800.0},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "latest_price": 1650.0},
        {"symbol": "RELIANCE", "sector_name": "Energy & Oil", "latest_price": 2800.0},
        {"symbol": "SUNPHARMA", "sector_name": "Healthcare & Pharmaceuticals", "latest_price": 1500.0},
    ]

    res = check_portfolio_feasibility(
        capital=500.0,
        risk_category="moderate",
        eligible_candidates=candidates,
    )
    assert res.is_feasible is False
    assert any("below minimum threshold" in v for v in res.conditions_violated)


def test_feasibility_check_insufficient_holdings_for_cap():
    """Feasibility check fails when candidate pool is smaller than 100 / max_stock_pct."""
    # Very conservative has 15% max stock cap => requires at least ceil(100/15) = 7 stocks
    few_candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "latest_price": 3800.0},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "latest_price": 1650.0},
        {"symbol": "RELIANCE", "sector_name": "Energy & Oil", "latest_price": 2800.0},
    ]

    res = check_portfolio_feasibility(
        capital=100000.0,
        risk_category="very_conservative",
        eligible_candidates=few_candidates,
    )
    assert res.is_feasible is False
    assert any("Insufficient candidates" in v for v in res.conditions_violated)


def test_feasibility_check_insufficient_sectors():
    """Feasibility check fails when all candidates belong to a single sector (violating 40% sector cap)."""
    single_sector_candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "latest_price": 3800.0},
        {"symbol": "INFY", "sector_name": "Information Technology", "latest_price": 1600.0},
        {"symbol": "HCLTECH", "sector_name": "Information Technology", "latest_price": 1400.0},
        {"symbol": "WIPRO", "sector_name": "Information Technology", "latest_price": 500.0},
    ]

    res = check_portfolio_feasibility(
        capital=100000.0,
        risk_category="moderate",
        eligible_candidates=single_sector_candidates,
    )
    assert res.is_feasible is False
    assert any("Insufficient sector diversity" in v for v in res.conditions_violated)


# ==============================================================================
# 4. RISK CRITIC EXPLICIT VERDICT STATES & BOUNDED REWORK TESTS
# ==============================================================================

def test_critic_verdict_approved_for_clean_candidates():
    """Critic approves a compliant, high-quality, diversified candidate set."""
    candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "roe": 0.42, "debt_to_equity": 0.0},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "roe": 0.17, "debt_to_equity": 0.0},
        {"symbol": "RELIANCE", "sector_name": "Energy & Oil", "roe": 0.12, "debt_to_equity": 0.45},
        {"symbol": "SUNPHARMA", "sector_name": "Healthcare & Pharmaceuticals", "roe": 0.16, "debt_to_equity": 0.05},
    ]

    verdict: CriticEvaluationOutput = critic_fiduciary_audit_tool(
        candidates=candidates,
        capital=100000.0,
        risk_category="moderate",
        iteration=1,
    )
    assert verdict.verdict_status == CriticVerdictStatus.APPROVED
    assert verdict.approved is True
    assert len(verdict.removable_tickers) == 0


def test_critic_verdict_rework_required_on_high_leverage():
    """Critic flags non-financial company with D/E > 2.50 and issues explicit rework directives."""
    candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "roe": 0.42, "debt_to_equity": 0.0},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "roe": 0.17, "debt_to_equity": 0.0},
        {"symbol": "HIGHDEBT_CO", "sector_name": "Manufacturing & Industrials", "roe": 0.14, "debt_to_equity": 3.80},
        {"symbol": "SUNPHARMA", "sector_name": "Healthcare & Pharmaceuticals", "roe": 0.16, "debt_to_equity": 0.05},
    ]

    verdict: CriticEvaluationOutput = critic_fiduciary_audit_tool(
        candidates=candidates,
        capital=100000.0,
        risk_category="moderate",
        iteration=1,
    )
    assert verdict.verdict_status == CriticVerdictStatus.REWORK_REQUIRED
    assert verdict.approved is False
    assert "HIGHDEBT_CO" in verdict.removable_tickers
    assert any("POL-LEVERAGE-01" in r for r in verdict.rework_instructions or [f["message"] for f in verdict.findings])


def test_critic_verdict_blocked_after_rework_exhausted():
    """After 2 rework cycles, unresolved critical defects result in BLOCKED_VIOLATION, not approval."""
    candidates = [
        {"symbol": "DEFECTIVE_1", "sector_name": "Information Technology", "roe": -0.05, "debt_to_equity": 0.0},
        {"symbol": "DEFECTIVE_2", "sector_name": "Automotive", "roe": 0.08, "debt_to_equity": 4.50},
    ]

    verdict: CriticEvaluationOutput = critic_fiduciary_audit_tool(
        candidates=candidates,
        capital=100000.0,
        risk_category="moderate",
        iteration=2,  # Max iteration reached
    )
    assert verdict.verdict_status == CriticVerdictStatus.BLOCKED_VIOLATION
    assert verdict.approved is False
    assert len(verdict.blocking_reasons) > 0


# ==============================================================================
# 5. DETERMINISTIC OPTIMIZER & FALLBACK HARDENING TESTS
# ==============================================================================

def test_optimizer_fallback_strictly_honors_sector_caps():
    """Fallback logic must respect the 40% sector cap and return infeasible if impossible."""
    # 4 candidates but 3 belong to IT => IT would be 75% under simple equal weight
    candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "alpha_score": 0.6},
        {"symbol": "INFY", "sector_name": "Information Technology", "alpha_score": 0.5},
        {"symbol": "WIPRO", "sector_name": "Information Technology", "alpha_score": 0.4},
        {"symbol": "HDFCBANK", "sector_name": "Banking & Financial Services", "alpha_score": 0.7},
    ]

    # Max sector frac = 0.40 (40%). With only 2 sectors and 3 IT stocks, IT must be capped at 40%
    ok, weights = _sector_constrained_fallback(candidates, max_stock_frac=0.25, max_sector_frac=0.40)
    if ok:
        it_weight = weights[0] + weights[1] + weights[2]
        bank_weight = weights[3]
        assert it_weight <= 0.40001
        assert bank_weight <= 0.40001
        assert sum(weights) == pytest.approx(1.0, abs=1e-4)


def test_optimizer_returns_explicit_failure_when_infeasible():
    """When candidates cannot satisfy sector limits (e.g. 100% single sector with 40% cap), optimizer fails explicitly."""
    single_sector_candidates = [
        {"symbol": "TCS", "sector_name": "Information Technology", "alpha_score": 0.6},
        {"symbol": "INFY", "sector_name": "Information Technology", "alpha_score": 0.5},
        {"symbol": "WIPRO", "sector_name": "Information Technology", "alpha_score": 0.4},
        {"symbol": "HCLTECH", "sector_name": "Information Technology", "alpha_score": 0.4},
    ]

    constraints = PortfolioConstraints(max_single_stock_pct=25.0, max_sector_pct=40.0)
    ok, allocs, msg = optimize_portfolio_allocations(
        candidates=single_sector_candidates,
        risk_category="moderate",
        constraints=constraints,
    )
    # Must fail explicitly rather than returning an invalid portfolio violating the 40% cap
    assert ok is False
    assert len(allocs) == 0
    assert "infeasible" in msg.lower() or "failed" in msg.lower()


def test_integer_lot_rounding_across_budgets():
    """Discrete lot rounding mathematically guarantees non-negative cash residual across ₹15k, ₹50k, ₹100k, ₹1M."""
    allocations = [
        {"symbol": "TCS", "latest_price": 3800.0, "target_weight_pct": 25.0},
        {"symbol": "HDFCBANK", "latest_price": 1650.0, "target_weight_pct": 25.0},
        {"symbol": "RELIANCE", "latest_price": 2800.0, "target_weight_pct": 25.0},
        {"symbol": "SUNPHARMA", "latest_price": 1500.0, "target_weight_pct": 25.0},
    ]

    budgets = [Decimal("15000"), Decimal("50000"), Decimal("100000"), Decimal("1000000")]

    for b in budgets:
        rounded_allocs, total_inv, unalloc_cash = calculate_integer_shares_and_amounts(allocations, b)
        # 1. Zero deficit invariant: Total invested + unallocated cash == budget
        assert (total_inv + unalloc_cash) == b
        # 2. Non-negative cash residual: C >= 0
        assert unalloc_cash >= Decimal("0.0")
        # 3. Whole shares: each quantity must be integer >= 0
        for item in rounded_allocs:
            assert item["shares_quantity"] >= 0
            assert isinstance(item["shares_quantity"], int)


# ==============================================================================
# 6. EVIDENCE PROVENANCE MODEL TESTS
# ==============================================================================

def test_evidence_provenance_record_types():
    """Verifies that MetricEvidenceRecord strictly classifies data quality and reporting basis."""
    rec = MetricEvidenceRecord(
        instrument_symbol="TCS.NS",
        exchange_code="NSE",
        metric_name="Return on Equity (ROE)",
        metric_value=42.1,
        unit="percent",
        data_quality_status=DataQualityStatus.CALCULATED_RATIO,
        reporting_basis=ReportingBasis.CONSOLIDATED,
        document_reference="Audited Q2 FY26 Financial Results / BSE Scrip 532540",
        reporting_period="TTM",
        retrieval_timestamp="2026-11-04T10:00:00Z",
        calculation_formula="Net Income / Average Shareholders Equity",
    )
    assert rec.data_quality_status == DataQualityStatus.CALCULATED_RATIO
    assert rec.reporting_basis == ReportingBasis.CONSOLIDATED
    assert rec.instrument_symbol == "TCS.NS"


def test_optimizer_provenance_distinguishes_optimal_vs_fallback():
    """
    Verifies that the optimizer clearly distinguishes a proven SLSQP optimal solution
    from a sector-constrained fallback solution, setting explicit provenance tags.
    """
    from backend.portfolio_engine.optimizer import optimize_portfolio_allocations, _sector_constrained_fallback

    candidates = [
        {"security_id": "sec-1", "symbol": "RELIANCE", "sector_name": "Energy", "latest_price": 2800.0, "factor_score": 0.85},
        {"security_id": "sec-2", "symbol": "TCS", "sector_name": "IT", "latest_price": 3800.0, "factor_score": 0.80},
        {"security_id": "sec-3", "symbol": "HDFCBANK", "sector_name": "Financials", "latest_price": 1600.0, "factor_score": 0.75},
        {"security_id": "sec-4", "symbol": "INFY", "sector_name": "IT", "latest_price": 1700.0, "factor_score": 0.70},
        {"security_id": "sec-5", "symbol": "ITC", "sector_name": "Consumer", "latest_price": 450.0, "factor_score": 0.65},
    ]

    # Standard run: SLSQP converges
    ok, allocs, msg = optimize_portfolio_allocations(candidates, risk_category="moderate")
    assert ok is True
    assert "SLSQP_OPTIMAL_CONVERGED" in msg
    for a in allocs:
        assert a.get("optimization_provenance") == "SLSQP_OPTIMAL_CONVERGED"

    # Direct fallback test: verifies feasible weights strictly honor sector limits
    fallback_ok, weights = _sector_constrained_fallback(candidates, max_stock_frac=0.25, max_sector_frac=0.40)
    assert fallback_ok is True
    assert abs(np.sum(weights) - 1.0) < 1e-5
    assert np.all(weights <= 0.25001)
    # Check IT sector sum (indices 1 and 3)
    assert (weights[1] + weights[3]) <= 0.40001


def test_missing_data_explicit_provenance_marking():
    """
    Verifies that unavailable macro and news data are explicitly marked as
    FALLBACK_ASSUMPTION with is_live_data=False, not silently masked as audited data.
    """
    from backend.agent.tools import macro_data_tool, news_filings_audit_tool

    # 1. Macro tool without DB: returns fallback baseline with explicit warning
    macro_out = macro_data_tool(db=None)
    assert macro_out.is_live_data is False
    assert macro_out.data_sufficiency_status == "FALLBACK_ASSUMPTION"
    assert "baseline policy assumption utilized" in macro_out.macro_summary
    for ev in macro_out.evidence_records:
        assert ev.data_quality_status == DataQualityStatus.FALLBACK_ASSUMPTION
        assert ev.limitations is not None

    # 2. News tool without DB: returns fallback baseline with explicit warning
    news_out = news_filings_audit_tool(symbols=["RELIANCE", "TCS"], db=None)
    assert news_out.is_live_data is False
    assert news_out.data_sufficiency_status == "FALLBACK_ASSUMPTION"
    assert "baseline market disclosures referenced" in news_out.news_summary

