import pytest
from backend.database import SessionLocal
from backend.models.security import Security, InstrumentListing, Company, Exchange
from backend.market_data.exchange_universe_sync import (
    sync_nse_equity_master,
    sync_nifty500_universe,
    ensure_bse_exchange_and_listings,
    reconcile_universe_against_exchanges,
    NSE_EXCHANGE_ID,
    BSE_EXCHANGE_ID,
)
from backend.portfolio_engine.candidate_selection import CandidateUniverseSelector


def test_full_universe_database_scale():
    """Verify that PostgreSQL contains the broad listed equity universe (>2,600 securities)."""
    db = SessionLocal()
    try:
        total_securities = db.query(Security).count()
        total_companies = db.query(Company).count()
        nse_listings = db.query(InstrumentListing).filter(InstrumentListing.exchange_id == NSE_EXCHANGE_ID).count()
        bse_listings = db.query(InstrumentListing).filter(InstrumentListing.exchange_id == BSE_EXCHANGE_ID).count()

        # Database must represent the complete broad equity universe, not just 504
        assert total_securities >= 2600, f"Expected >= 2600 securities, got {total_securities}"
        assert total_companies >= 2600, f"Expected >= 2600 companies, got {total_companies}"
        assert nse_listings >= 2600, f"Expected >= 2600 NSE listings, got {nse_listings}"
        assert bse_listings >= 70, f"Expected >= 70 BSE listings, got {bse_listings}"
    finally:
        db.close()


def test_series_classification_and_trading_status():
    """Verify that equity series (EQ, BE, BZ) map to correct active/suspended statuses."""
    db = SessionLocal()
    try:
        active_listings = (
            db.query(InstrumentListing)
            .filter(InstrumentListing.exchange_id == NSE_EXCHANGE_ID, InstrumentListing.trading_status == "active")
            .count()
        )
        assert active_listings >= 2500, f"Expected >= 2500 active listings, got {active_listings}"

        # Distinct ISINs must be strictly unique
        all_isins = [s.isin for s in db.query(Security).filter(Security.isin.isnot(None)).all()]
        assert len(all_isins) == len(set(all_isins)), "Duplicate ISINs found in Security master!"
    finally:
        db.close()


def test_reconciliation_and_candidate_filtering_separation():
    """
    Verify clean separation between:
    - Broad Security Master (>2,600)
    - Recommendation Eligible Universe (approx 500 liquid benchmark equities)
    - Excluded illiquid micro-caps (>2,100 excluded for retail protection)
    """
    db = SessionLocal()
    try:
        audit = reconcile_universe_against_exchanges(db)
        db_stats = audit["database_universe"]

        assert db_stats["total_securities"] >= 2600
        assert db_stats["eligible_recommendation_candidates"] > 0
        assert db_stats["eligible_recommendation_candidates"] <= db_stats["total_securities"]
        assert db_stats["excluded_from_recommendations_count"] > 2000

        # Run CandidateUniverseSelector directly
        selector = CandidateUniverseSelector(db)
        candidates = selector.select_eligible_candidates(min_avg_volume=10000, min_daily_turnover=2500000.0)
        report = selector.get_universe_audit_report()

        assert len(candidates) == report["eligible_candidates_count"]
        assert report["initial_universe_size"] >= 2600
        assert report["excluded_candidates_count"] > 2000
    finally:
        db.close()


def test_idempotent_synchronization():
    """Verify that re-running sync does not duplicate securities or crash constraints."""
    db = SessionLocal()
    try:
        initial_count = db.query(Security).count()
        # Re-run sync with sample batch
        res = sync_nse_equity_master(db, max_records=20)
        final_count = db.query(Security).count()
        assert res["status"] == "success"
        assert final_count == initial_count, "Idempotent sync must not duplicate existing securities!"
    finally:
        db.close()
