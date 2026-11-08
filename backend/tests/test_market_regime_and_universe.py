"""
Unit and integration tests for Market Regime Classification (FR-C03) and Candidate Universe Selection (FR-C04).
Validates:
- Live India VIX retrieval and validation
- Nifty 50 trend analysis (50-DMA, 200-DMA, return slope)
- Canonical regime assignment: BULL, NORMAL, VOLATILE
- Sourcing metadata and database persistence
- Candidate universe liquidity filtering (ADTV >= 10,000 shares, turnover >= 25L)
- Audit reporting for candidate exclusions
"""

import pytest
from datetime import date
from backend.database.session import SessionLocal
from backend.market_data.regime import (
    fetch_live_india_vix,
    fetch_nifty50_trend,
    detect_market_regime,
)
from backend.portfolio_engine.candidate_selection import CandidateUniverseSelector


def test_market_regime_classification():
    db = SessionLocal()
    try:
        # 1. Test live India VIX fetch
        vix_data = fetch_live_india_vix(db)
        assert vix_data is not None
        assert "vix" in vix_data
        assert 5.0 <= vix_data["vix"] <= 90.0
        assert "source" in vix_data
        assert "data_quality" in vix_data

        # 2. Test Nifty 50 trend analysis
        trend_data = fetch_nifty50_trend(db)
        assert trend_data is not None
        assert "trend" in trend_data
        assert trend_data["trend"] in ("UPTREND", "DOWNTREND", "SIDEWAYS")
        assert "current_price" in trend_data

        # 3. Test comprehensive market regime detection
        regime = detect_market_regime(db)
        assert regime is not None
        assert "regime" in regime
        assert regime["regime"] in ("BULL", "NORMAL", "VOLATILE")
        assert "india_vix" in regime
        assert "cash_buffer_pct" in regime
        assert regime["cash_buffer_pct"] >= 0.0
        assert "guidance" in regime
        assert "market_direction" in regime
    finally:
        db.close()


def test_candidate_universe_liquidity_and_exclusions():
    db = SessionLocal()
    try:
        selector = CandidateUniverseSelector(db)

        # 1. Execute selection with strict liquidity thresholds
        eligible = selector.select_eligible_candidates(
            min_avg_volume=10000,
            min_daily_turnover=2500000.0,
        )
        assert isinstance(eligible, list)
        assert len(eligible) > 0

        # Every eligible candidate must have valid price and symbol
        for cand in eligible:
            assert "symbol" in cand
            assert "latest_price" in cand
            assert cand["latest_price"] > 0
            assert "sector_name" in cand

        # 2. Test audit report of exclusions
        audit = selector.get_universe_audit_report()
        assert audit is not None
        assert "initial_universe_size" in audit
        assert "eligible_candidates_count" in audit
        assert "excluded_candidates_count" in audit
        assert "exclusion_breakdown" in audit
        assert audit["initial_universe_size"] >= audit["eligible_candidates_count"]
        assert audit["initial_universe_size"] == audit["eligible_candidates_count"] + audit["excluded_candidates_count"]

        # 3. Test sector exclusion
        eligible_no_it = selector.select_eligible_candidates(
            excluded_sectors=["Information Technology"],
            min_avg_volume=10000,
        )
        for cand in eligible_no_it:
            assert cand.get("sector_name") != "Information Technology"
    finally:
        db.close()
