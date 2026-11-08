"""
Tests for Market Data Ingestion Pipeline, Data Quality Rules, and Idempotency.
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

from backend.database import SessionLocal
from backend.models import MarketPrice, InstrumentListing, DataIngestionRun, DataIngestionError
from backend.market_data.quality import validate_price_record, verify_listing_freshness
from backend.market_data.adapter import SimulatedMarketProvider
from backend.market_data.ingestion import MarketDataIngestionService
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_market_data_quality_rules():
    """Verify that quality rules reject negative prices, inverted high/low, and out-of-range bars."""
    today = date.today()

    # Valid bar
    valid_bar = {
        "symbol": "RELIANCE",
        "price_date": today,
        "open": 2800.0,
        "high": 2850.0,
        "low": 2790.0,
        "close": 2830.0,
        "volume": 50000,
    }
    is_valid, msg = validate_price_record(valid_bar)
    assert is_valid, msg

    # Invalid non-positive close
    bad_close = dict(valid_bar, close=-10.0)
    is_valid, msg = validate_price_record(bad_close)
    assert not is_valid
    assert "Invalid or non-positive close price" in msg

    # Inverted high and low
    inverted_hl = dict(valid_bar, high=2700.0, low=2800.0)
    is_valid, msg = validate_price_record(inverted_hl)
    assert not is_valid
    assert "cannot be lower than Low price" in msg

    # Close exceeds high
    close_exceeds = dict(valid_bar, close=2900.0, high=2850.0)
    is_valid, msg = validate_price_record(close_exceeds)
    assert not is_valid
    assert "outside high-low range" in msg

    # Negative volume
    neg_vol = dict(valid_bar, volume=-500)
    is_valid, msg = validate_price_record(neg_vol)
    assert not is_valid
    assert "Volume cannot be negative" in msg

    # Future date
    future_date = dict(valid_bar, price_date=today + timedelta(days=5))
    is_valid, msg = validate_price_record(future_date)
    assert not is_valid
    assert "in the future" in msg


def test_idempotent_ingestion_pipeline():
    """Verify that running ingestion multiple times for the same date range does not duplicate rows."""
    db = SessionLocal()
    try:
        service = MarketDataIngestionService(db, provider=SimulatedMarketProvider())
        start = date.today() - timedelta(days=7)
        end = date.today()

        listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == "TCS").first()
        assert listing is not None, "TCS listing must exist in seeded DB"

        # Count prices before
        initial_count = db.query(MarketPrice).filter(MarketPrice.listing_id == listing.listing_id).count()

        # Run 1
        run1 = service.ingest_symbol_history("TCS", start, end)
        assert run1.run_status in ["succeeded", "partial"]
        count_after_run1 = db.query(MarketPrice).filter(MarketPrice.listing_id == listing.listing_id).count()

        # Run 2 (exact same range)
        run2 = service.ingest_symbol_history("TCS", start, end)
        assert run2.run_status in ["succeeded", "partial"]
        count_after_run2 = db.query(MarketPrice).filter(MarketPrice.listing_id == listing.listing_id).count()

        # Idempotency assertion: re-running does not create duplicate rows
        assert count_after_run1 == count_after_run2, "Idempotent upsert should not produce duplicate price records"

    finally:
        db.close()


def test_market_data_freshness_verification():
    """Verify that the engine detects stale market prices."""
    db = SessionLocal()
    try:
        listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == "HDFCBANK").first()
        assert listing is not None

        # As of today, price is fresh (seeded within last few days)
        is_fresh, price_date, latest_p, reason = verify_listing_freshness(db, listing.listing_id, max_stale_days=7)
        assert is_fresh, f"Expected fresh data, got {reason}"

        # If simulated reference date is 30 days in the future, should report stale
        future_ref = date.today() + timedelta(days=30)
        is_fresh_future, _, _, reason_future = verify_listing_freshness(
            db, listing.listing_id, as_of_date=future_ref, max_stale_days=7
        )
        assert not is_fresh_future
        assert "stale" in reason_future.lower()
    finally:
        db.close()


def test_market_regime_and_macro_endpoints():
    """Verify market regime detection, macro indicators, and news API endpoints."""
    # 1. Test Regime Detection
    regime_res = client.get("/api/v1/market-data/regime")
    assert regime_res.status_code == 200, regime_res.text
    regime_data = regime_res.json()
    assert regime_data["regime"] in ("BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY", "CALM", "MODERATE", "VOLATILE", "EXTREME", "NORMAL")
    assert "india_vix" in regime_data
    assert "risk_multiplier" in regime_data
    assert "volatility_dimension" in regime_data

    # Test override
    override_res = client.get("/api/v1/market-data/regime?vix=28.5")
    assert override_res.status_code == 200
    assert override_res.json()["volatility_dimension"] == "EXTREME_VOLATILITY"

    # 2. Test Macro Indicators
    macro_res = client.get("/api/v1/market-data/macro-indicators")
    assert macro_res.status_code == 200, macro_res.text
    macro_data = macro_res.json()
    assert macro_data["count"] >= 4
    codes = [i["indicator_code"] for i in macro_data["indicators"]]
    assert "RBI_REPO_RATE" in codes
    assert "INDIA_CPI_INFLATION" in codes

    # 3. Test Market News
    news_res = client.get("/api/v1/market-data/news")
    assert news_res.status_code == 200, news_res.text
    news_data = news_res.json()
    assert news_data["count"] >= 1
    assert "headline" in news_data["articles"][0]
    assert "sentiment_score" in news_data["articles"][0]

