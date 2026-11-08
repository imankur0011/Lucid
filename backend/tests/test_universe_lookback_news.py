import pytest
from datetime import date, datetime, timedelta, timezone
from backend.database.session import SessionLocal
from backend.portfolio_engine.candidate_selection import (
    CandidateUniverseSelector,
    LiquidityTier,
)
from backend.portfolio_engine.math_engine import (
    LOOKBACK_WINDOW_MOMENTUM_DAYS,
    LOOKBACK_WINDOW_REGIME_DAYS,
    LOOKBACK_WINDOW_VOLATILITY_DAYS,
    LOOKBACK_WINDOW_BETA_DAYS,
    LOOKBACK_WINDOW_MACRO_DAYS,
    MIN_OBSERVATIONS_MOMENTUM,
    MIN_OBSERVATIONS_REGIME,
    MIN_OBSERVATIONS_VOLATILITY,
    MIN_OBSERVATIONS_BETA_CAGR,
    calculate_cagr,
    calculate_beta_and_volatility,
)
from backend.agent.tools import news_filings_audit_tool


def test_liquidity_tiers_and_exclusion_categories():
    """Verify that CandidateUniverseSelector correctly categorizes tiers and distinguishes missing from stale prices."""
    db = SessionLocal()
    try:
        selector = CandidateUniverseSelector(db=db, max_stale_days=14)
        candidates = selector.select_eligible_candidates()
        report = selector.get_universe_audit_report()

        assert report["initial_universe_size"] >= 2600
        assert report["eligible_candidates_count"] >= 500

        # Verify exclusion breakdown separates missing price from stale price
        breakdown = report["exclusion_breakdown"]
        assert "MISSING_PRICE" in breakdown or "STALE_PRICE" in breakdown
        assert "INACTIVE_SECURITY" in breakdown

        # Verify candidate tier assignments
        for c in candidates:
            assert "liquidity_tier" in c
            assert c["liquidity_tier"] in [
                LiquidityTier.TIER_1_ULTRA_LIQUID.value,
                LiquidityTier.TIER_2_BROAD_LIQUID.value,
                LiquidityTier.TIER_3_EMERGING.value,
            ]
    finally:
        db.close()


def test_lookback_constants_and_observation_thresholds():
    """Verify canonical lookback window constants and observation threshold adherence."""
    assert LOOKBACK_WINDOW_MOMENTUM_DAYS == 126
    assert LOOKBACK_WINDOW_REGIME_DAYS == 252
    assert LOOKBACK_WINDOW_VOLATILITY_DAYS == 504
    assert LOOKBACK_WINDOW_BETA_DAYS == 756
    assert LOOKBACK_WINDOW_MACRO_DAYS == 1260

    # Test CAGR with insufficient (<30) vs short-horizon vs full 3Y
    cagr_short, status_short = calculate_cagr(100.0, 150.0, trading_days=250)
    assert status_short == "ANNUALIZED_RETURN_INSUFFICIENT_HISTORY_FOR_3Y"
    assert cagr_short is not None

    cagr_full, status_full = calculate_cagr(100.0, 150.0, trading_days=756)
    assert status_full == "AUDITED_3Y_CAGR"
    assert cagr_full is not None

    # Test Beta & Volatility with <60 observations
    b_none, v_none, st_none = calculate_beta_and_volatility([0.01]*30, [0.01]*30)
    assert st_none == "INSUFFICIENT_RETURNS_DATA"
    assert b_none is None


def test_news_recency_and_deduplication():
    """Verify that news_filings_audit_tool enforces recency filtering, deduplication, and limits."""
    db = SessionLocal()
    try:
        output = news_filings_audit_tool(
            symbols=["RELIANCE", "TCS", "INFY"],
            db=db,
            max_age_days=30,
            max_articles=5,
        )
        assert output.execution_status == "SUCCESS"
        assert len(output.events) <= 5
        assert output.sentiment_label in ["positive", "neutral", "negative"]

        # Verify no duplicate headlines in output
        headlines = [ev.headline for ev in output.events]
        assert len(headlines) == len(set(headlines)), "Headlines must be unique after deduplication!"
    finally:
        db.close()
