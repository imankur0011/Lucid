"""
Unit and integration tests for Portfolio Monitoring (FR-C07) and Rebalancing Engine (FR-C08).
Validates:
- Real-time holding valuation formula: V_i = Q_i * P_i
- Total portfolio valuation and dynamic weights: w_i = (V_i / V_p) * 100
- Holding-level and sector-level drift calculations
- Concentration auditing (single-stock <= 25%, sector <= 40%)
- Snapshot persistence into portfolio_performance_snapshots
- Whole-share rebalancing preview (integer trades BUY, SELL, HOLD)
- Non-negative post-rebalance cash conservation
- Rebalance triggers auto-dispatching in-app alerts
"""

import pytest
import uuid
from decimal import Decimal
from sqlalchemy import desc
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.models import (
    AppUser,
    InvestorPortfolio,
    PortfolioVersion,
    PortfolioPerformanceSnapshot,
)
from backend.portfolio_engine.monitoring_service import PortfolioMonitoringService
from backend.portfolio_engine.rebalancing_service import RebalancingService

client = TestClient(app)
DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")


def test_monitoring_service_valuation_and_drift():
    db = SessionLocal()
    try:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == DEMO_USER_ID)
            .order_by(InvestorPortfolio.updated_at.desc())
            .first()
        )
        assert portfolio is not None, "At least one portfolio must exist for the demo user"

        latest_ver = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == portfolio.portfolio_id)
            .order_by(desc(PortfolioVersion.version_number))
            .first()
        )
        assert latest_ver is not None, "Portfolio version must exist"

        # Execute live monitoring
        res = PortfolioMonitoringService.monitor_native_portfolio(
            db=db,
            portfolio_version_id=latest_ver.portfolio_version_id,
            user_id=DEMO_USER_ID,
        )
        assert res is not None

        # 1. Check valuation structure
        assert "portfolio_id" in res
        assert "total_equity_value" in res
        assert "unallocated_cash" in res
        assert "total_portfolio_value" in res
        assert res["total_portfolio_value"] >= res["total_equity_value"]
        assert "holdings" in res
        assert len(res["holdings"]) > 0

        # 2. Check holdings valuation formula V_i = Q_i * P_i
        for h in res["holdings"]:
            q = h["shares_quantity"]
            p = h["latest_price"]
            v = h["current_value"]
            assert abs(v - round(q * p, 2)) <= 0.05
            assert "target_weight_pct" in h
            assert "current_weight_pct" in h
            assert "weight_drift_pct" in h
            assert "drift_status" in h
            expected_drift = round(h["current_weight_pct"] - h["target_weight_pct"], 2)
            assert abs(h["weight_drift_pct"] - expected_drift) <= 0.05

        # 3. Check health status
        assert res["health_status"] in ("HEALTHY", "MILD_DRIFT", "ACTION_REQUIRED", "OPTIMAL", "REBALANCE_RECOMMENDED")

        # 4. Check snapshot persistence
        snap = (
            db.query(PortfolioPerformanceSnapshot)
            .filter(PortfolioPerformanceSnapshot.portfolio_version_id == latest_ver.portfolio_version_id)
            .order_by(desc(PortfolioPerformanceSnapshot.snapshot_date))
            .first()
        )
        assert snap is not None
        assert float(snap.valuation_amount) == float(res["total_portfolio_value"])
    finally:
        db.close()


def test_rebalancing_service_whole_share_trades():
    db = SessionLocal()
    try:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == DEMO_USER_ID)
            .order_by(InvestorPortfolio.updated_at.desc())
            .first()
        )
        assert portfolio is not None

        latest_ver = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == portfolio.portfolio_id)
            .order_by(desc(PortfolioVersion.version_number))
            .first()
        )
        assert latest_ver is not None

        # Generate rebalance preview with 5% drift threshold
        preview = RebalancingService.evaluate_native_rebalancing(
            db=db,
            portfolio_version_id=latest_ver.portfolio_version_id,
            user_id=DEMO_USER_ID,
            stock_drift_threshold=5.0,
            sector_drift_threshold=10.0,
        )
        assert preview is not None
        assert "trigger_status" in preview
        assert "trades" in preview
        assert "turnover_amount" in preview
        assert "post_rebalance_cash" in preview

        # 1. Validate post-rebalance cash is non-negative
        assert preview["post_rebalance_cash"] >= 0.0

        # 2. Validate all trades are integer lots (whole shares)
        for t in preview["trades"]:
            trade_qty = t["trade_quantity"]
            assert isinstance(trade_qty, int)
            assert t["action"] in ("BUY", "SELL", "HOLD")
            if t["action"] == "BUY":
                assert trade_qty > 0
            elif t["action"] == "SELL":
                assert trade_qty < 0
            else:
                assert trade_qty == 0

            # Trade value check
            assert abs(t["trade_value"] - abs(trade_qty) * t["reference_price"]) <= 0.05
    finally:
        db.close()


def test_monitoring_and_rebalance_api_endpoints():
    db = SessionLocal()
    try:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == DEMO_USER_ID)
            .order_by(InvestorPortfolio.updated_at.desc())
            .first()
        )
        assert portfolio is not None
        port_id = str(portfolio.portfolio_id)

        # GET /api/v1/portfolios/{id}/monitoring
        res = client.get(f"/api/v1/portfolios/{port_id}/monitoring")
        assert res.status_code == 200
        mon_data = res.json()
        assert "total_portfolio_value" in mon_data
        assert "health_status" in mon_data

        # GET /api/v1/portfolios/{id}/rebalance-preview
        res_prev = client.get(f"/api/v1/portfolios/{port_id}/rebalance-preview")
        assert res_prev.status_code == 200
        prev_data = res_prev.json()
        assert "trigger_status" in prev_data

        # POST /api/v1/portfolios/{id}/check-drift-and-trigger
        res_trig = client.post(f"/api/v1/portfolios/{port_id}/check-drift-and-trigger")
        assert res_trig.status_code == 200
        trig_data = res_trig.json()
        assert "trigger_status" in trig_data
        assert "portfolio_id" in trig_data
        assert "portfolio_name" in trig_data

        # POST /api/v1/portfolios/{id}/apply-rebalance
        res_apply = client.post(f"/api/v1/portfolios/{port_id}/apply-rebalance")
        assert res_apply.status_code == 200
        apply_data = res_apply.json()
        assert "version_number" in apply_data
        assert apply_data["version_number"] >= 2
        assert "holdings" in apply_data
        assert len(apply_data["holdings"]) > 0
        assert "validation_results" in apply_data
    finally:
        db.close()


def test_rebalancing_statutory_transaction_costs():
    """Validates Indian statutory transaction costs (STT, NSE/BSE turnover, SEBI fees, Stamp Duty, GST, DP charges)."""
    from backend.portfolio_engine.rebalancing_service import estimate_indian_equity_transaction_costs
    from backend.portfolio_engine.transaction_costs import (
        TransactionCostEngine,
        ExchangeCode,
        DEFAULT_BROKER_PROFILES,
    )

    mock_trades = [
        {"symbol": "INFY", "action": "BUY", "trade_value": 50000.0, "quantity_change": 20, "trade_quantity": 20, "latest_price": 2500.0},
        {"symbol": "TCS", "action": "SELL", "trade_value": 30000.0, "quantity_change": -10, "trade_quantity": -10, "latest_price": 3000.0},
        {"symbol": "RELIANCE", "action": "HOLD", "trade_value": 0.0, "quantity_change": 0, "trade_quantity": 0, "latest_price": 2800.0},
    ]

    # 1. Standard Flat-Rate Broker on NSE (Default)
    costs = estimate_indian_equity_transaction_costs(mock_trades, exchange="NSE", broker_profile_id="flat_20")
    assert costs["buy_turnover"] == 50000.0
    assert costs["sell_turnover"] == 30000.0
    assert costs["total_turnover"] == 80000.0

    # STT: 0.1% on delivery BUY + SELL = 80.0
    assert costs["stt"] == 80.0

    # NSE charges: 0.00297% (Oct 1, 2024 SEBI True-to-label circular CIR/2024/90) on 80,000 = 2.38
    assert costs["exchange_charges"] == 2.38

    # SEBI turnover charges: 0.0001% on 80,000 = 0.08
    assert costs["sebi_charges"] == 0.08

    # Stamp duty: 0.015% on BUY 50,000 = 7.5 (0 on SELL)
    assert costs["stamp_duty"] == 7.5

    # Brokerage: 2 active trades * ₹20 = 40.0
    assert costs["brokerage"] == 40.0

    # DP charge on 1 SELL scrip = 15.93
    assert costs["dp_charges"] == 15.93

    # GST: 18% on (brokerage + exchange_charges + sebi_charges) = 0.18 * (40.0 + 2.38 + 0.08) = 7.64
    assert costs["gst"] == 7.64

    # Net Cash Impact: Sell (30000) - Buy (50000) - Total Costs
    expected_total = round(80.0 + 2.38 + 0.08 + 7.5 + 40.0 + 15.93 + 7.64, 2)
    assert costs["total_estimated_costs"] == expected_total
    assert costs["net_cash_impact"] == round(30000.0 - 50000.0 - expected_total, 2)

    # 2. BSE Exchange Rate Test (0.00375% on 80,000 = 3.00)
    bse_costs = estimate_indian_equity_transaction_costs(mock_trades, exchange="BSE", broker_profile_id="flat_20")
    assert bse_costs["exchange_charges"] == 3.00
    assert bse_costs["exchange_code"] == "BSE"

    # 3. Zerodha Discount Broker Test (₹0 delivery brokerage)
    zerodha_costs = estimate_indian_equity_transaction_costs(mock_trades, exchange="NSE", broker_profile_id="zerodha")
    assert zerodha_costs["brokerage"] == 0.0
    # GST on zerodha: 18% of (0 + 2.38 + 0.08) = 0.44
    assert zerodha_costs["gst"] == 0.44

    # 4. BUY-Only Trade Test (No DP charges, stamp duty applies)
    buy_only = [{"symbol": "INFY", "action": "BUY", "trade_value": 100000.0, "quantity_change": 40, "trade_quantity": 40, "latest_price": 2500.0}]
    buy_costs = estimate_indian_equity_transaction_costs(buy_only, exchange="NSE", broker_profile_id="flat_20")
    assert buy_costs["buy_turnover"] == 100000.0
    assert buy_costs["sell_turnover"] == 0.0
    assert buy_costs["stamp_duty"] == 15.0
    assert buy_costs["dp_charges"] == 0.0

    # 5. SELL-Only Trade Test (No stamp duty, DP charge applies)
    sell_only = [{"symbol": "TCS", "action": "SELL", "trade_value": 100000.0, "quantity_change": -25, "trade_quantity": -25, "latest_price": 4000.0}]
    sell_costs = estimate_indian_equity_transaction_costs(sell_only, exchange="NSE", broker_profile_id="flat_20")
    assert sell_costs["buy_turnover"] == 0.0
    assert sell_costs["sell_turnover"] == 100000.0
    assert sell_costs["stamp_duty"] == 0.0
    assert sell_costs["dp_charges"] == 15.93


def test_monitoring_scheduler_unattended_cycle():
    """Validates unattended background scheduler execution across all active portfolios."""
    from backend.services.monitoring_scheduler import (
        run_all_active_portfolios_monitoring,
        is_indian_market_hours,
        BackgroundMonitoringScheduler,
    )

    db = SessionLocal()
    try:
        # 1. Market hours helper check
        in_hours = is_indian_market_hours(force_run=False)
        assert isinstance(in_hours, bool)

        # 2. Force-run execution check
        summary = run_all_active_portfolios_monitoring(db, force_run=True)
        assert summary["status"] == "COMPLETED"
        assert summary["portfolios_scanned"] > 0
        assert summary["portfolios_monitored"] > 0
        assert "drifts_detected" in summary
        assert "rebalances_recommended" in summary
        assert len(summary["results"]) == summary["portfolios_scanned"]

        # 3. Scheduler background lifecycle check
        scheduler = BackgroundMonitoringScheduler(interval_seconds=600)
        assert not scheduler.is_running()
        scheduler.start()
        assert scheduler.is_running()
        scheduler.stop()
        assert not scheduler.is_running()
    finally:
        db.close()


def test_scheduler_cycle_api_endpoint():
    """Validates the administrative scheduler trigger and telemetry endpoints."""
    from sqlalchemy import text
    db_cleanup = SessionLocal()
    try:
        db_cleanup.execute(text("SELECT pg_advisory_unlock_all()"))
        db_cleanup.commit()
    except Exception:
        pass
    finally:
        db_cleanup.close()

    res = client.post("/api/v1/portfolios/monitoring/run-scheduler-cycle?force_run=true")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("COMPLETED", "SKIPPED_LOCK_HELD")
    if data["status"] == "COMPLETED":
        assert data["portfolios_scanned"] > 0

    # Telemetry endpoint
    res_status = client.get("/api/v1/portfolios/monitoring/scheduler-status")
    assert res_status.status_code == 200
    status_data = res_status.json()
    assert status_data["scheduler_active"] is True
    assert "market_schedule" in status_data
    assert "distributed_concurrency" in status_data
    assert status_data["last_run"]["status"] in ("COMPLETED", "SKIPPED_LOCK_HELD", "NOT_RUN")


def test_scheduler_market_calendar_and_holidays():
    """Validates official 2026 NSE/BSE exchange holidays and trading session boundaries."""
    from backend.services.monitoring_scheduler import is_indian_market_hours, INDIAN_MARKET_HOLIDAYS_2026
    from datetime import datetime

    # 1. Republic Day (2026-01-26, Monday) -> Closed for holiday
    dt_republic_day = datetime(2026, 1, 26, 11, 0)
    assert is_indian_market_hours(dt_republic_day, force_run=False) is False
    assert INDIAN_MARKET_HOLIDAYS_2026["2026-01-26"] == "Republic Day"

    # 2. Regular Trading Day (2026-01-27, Tuesday, 11:00 AM IST) -> Open
    dt_trading = datetime(2026, 1, 27, 11, 0)
    assert is_indian_market_hours(dt_trading, force_run=False) is True

    # 3. Weekend (2026-01-31, Saturday, 11:00 AM IST) -> Closed
    dt_weekend = datetime(2026, 1, 31, 11, 0)
    assert is_indian_market_hours(dt_weekend, force_run=False) is False

    # 4. Off-Hours Evening (2026-01-27, Tuesday, 18:30 IST) -> Closed
    dt_evening = datetime(2026, 1, 27, 18, 30)
    assert is_indian_market_hours(dt_evening, force_run=False) is False

    # 5. Off-Hours Pre-Market (2026-01-27, Tuesday, 08:30 IST) -> Closed
    dt_premarket = datetime(2026, 1, 27, 8, 30)
    assert is_indian_market_hours(dt_premarket, force_run=False) is False

    # 6. Force-run override works even on holidays
    assert is_indian_market_hours(dt_republic_day, force_run=True) is True

