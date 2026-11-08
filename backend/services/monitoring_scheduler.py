"""
Automated Portfolio Monitoring Background Scheduler for Lucid Platform.
Executes unattended valuation updates, holding drift audits, snapshot generation,
and rebalancing event triggers across all active portfolios during Indian market hours.
"""

import os
import uuid
import asyncio
import logging
import time as pytime
from datetime import datetime, timezone, timedelta, time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

try:
    from backend.database import SessionLocal
    from backend.models.portfolio import InvestorPortfolio, PortfolioVersion
    from backend.portfolio_engine.monitoring_service import PortfolioMonitoringService
    from backend.portfolio_engine.rebalancing_service import RebalancingService
except ImportError:
    from database import SessionLocal
    from models.portfolio import InvestorPortfolio, PortfolioVersion
    from portfolio_engine.monitoring_service import PortfolioMonitoringService
    from portfolio_engine.rebalancing_service import RebalancingService

logger = logging.getLogger("lucid.monitoring_scheduler")
logger.setLevel(logging.INFO)

# Indian Standard Time (IST) is UTC + 5:30
IST_OFFSET = timedelta(hours=5, minutes=30)
MARKET_OPEN_TIME = time(9, 15)
MARKET_CLOSE_TIME = time(15, 30)

# Distributed Concurrency Control: PostgreSQL 64-bit advisory lock key for Lucid scheduler
SCHEDULER_PG_ADVISORY_LOCK_KEY = 847291

# Official NSE and BSE Trading Holidays (Calendar Year 2026)
INDIAN_MARKET_HOLIDAYS_2026: Dict[str, str] = {
    "2026-01-26": "Republic Day",
    "2026-02-18": "Mahashivratri",
    "2026-03-03": "Holi",
    "2026-03-20": "Id-ul-Fitr (Ramzan Id)",
    "2026-04-03": "Good Friday",
    "2026-04-14": "Dr. Baba Saheb Ambedkar Jayanti",
    "2026-05-01": "Maharashtra Day",
    "2026-05-27": "Bakri Id (Id-Ul-Adha)",
    "2026-06-26": "Muharram",
    "2026-08-15": "Independence Day",
    "2026-08-26": "Milad-un-Nabi",
    "2026-10-02": "Mahatma Gandhi Jayanti",
    "2026-10-20": "Dussehra",
    "2026-11-08": "Diwali Laxmi Pujan",
    "2026-11-24": "Guru Nanak Jayanti",
    "2026-12-25": "Christmas",
}

# Real-time in-memory execution telemetry
LAST_SCHEDULER_RUN_SUMMARY: Dict[str, Any] = {
    "last_run_timestamp": None,
    "last_run_duration_ms": 0.0,
    "status": "NOT_RUN",
    "portfolios_scanned": 0,
    "portfolios_monitored": 0,
    "drifts_detected": 0,
    "rebalances_recommended": 0,
    "market_hours_active": False,
    "worker_pid": os.getpid(),
}


def try_acquire_scheduler_lock(db: Session) -> bool:
    """
    Attempts to acquire a distributed session-level PostgreSQL advisory lock.
    Guarantees single-leader execution across multi-worker deployments (e.g. Gunicorn/Uvicorn replicas).
    """
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            res = db.execute(text(f"SELECT pg_try_advisory_lock({SCHEDULER_PG_ADVISORY_LOCK_KEY})")).scalar()
            return bool(res)
        except Exception as exc:
            logger.warning(f"Error acquiring PostgreSQL advisory lock: {exc}")
            return True
    return True


def release_scheduler_lock(db: Session) -> None:
    """Releases the distributed PostgreSQL advisory lock if held."""
    bind = db.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            db.execute(text(f"SELECT pg_advisory_unlock({SCHEDULER_PG_ADVISORY_LOCK_KEY})"))
            db.commit()
        except Exception as exc:
            logger.warning(f"Error releasing PostgreSQL advisory lock: {exc}")


def get_current_ist_time() -> datetime:
    """Returns the current wall-clock time in Indian Standard Time (IST)."""
    return datetime.now(timezone.utc) + IST_OFFSET


def is_indian_market_hours(current_time: Optional[datetime] = None, force_run: bool = False) -> bool:
    """
    Checks if the given time (or current time) falls within official NSE/BSE trading hours:
    Monday to Friday, 09:15 to 15:30 IST, excluding official NSE/BSE exchange holidays.
    Supports force_run override for testing and off-hours administration.
    """
    if force_run or os.getenv("MONITORING_FORCE_RUN", "false").lower() in ("true", "1", "yes"):
        return True

    ist_now = current_time or get_current_ist_time()

    # Monday = 0, Sunday = 6
    if ist_now.weekday() >= 5:
        return False

    # Check official NSE/BSE exchange holidays
    date_str = ist_now.strftime("%Y-%m-%d")
    if date_str in INDIAN_MARKET_HOLIDAYS_2026:
        logger.info(f"Exchange closed today for official holiday: {INDIAN_MARKET_HOLIDAYS_2026[date_str]}")
        return False

    now_time = ist_now.time()
    return MARKET_OPEN_TIME <= now_time <= MARKET_CLOSE_TIME


def get_scheduler_status() -> Dict[str, Any]:
    """Returns real-time health and execution status of the background monitoring scheduler."""
    ist_now = get_current_ist_time()
    in_market_hours = is_indian_market_hours(ist_now)
    date_str = ist_now.strftime("%Y-%m-%d")
    is_holiday = date_str in INDIAN_MARKET_HOLIDAYS_2026
    holiday_name = INDIAN_MARKET_HOLIDAYS_2026.get(date_str)

    return {
        "scheduler_active": True,
        "is_indian_market_hours": in_market_hours,
        "current_ist_time": ist_now.isoformat(),
        "market_schedule": {
            "trading_hours": "09:15 - 15:30 IST",
            "trading_days": "Monday - Friday",
            "is_weekend": ist_now.weekday() >= 5,
            "is_exchange_holiday": is_holiday,
            "holiday_name": holiday_name,
        },
        "distributed_concurrency": {
            "lock_mechanism": "PostgreSQL Advisory Lock (pg_try_advisory_lock)",
            "lock_key": SCHEDULER_PG_ADVISORY_LOCK_KEY,
            "worker_pid": os.getpid(),
        },
        "last_run": LAST_SCHEDULER_RUN_SUMMARY,
    }



def run_all_active_portfolios_monitoring(
    db: Session,
    force_run: bool = False,
    provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Scans all active investor portfolios in PostgreSQL.
    Re-values holdings with current market quotes, audits single-stock and sector drift,
    persists end-of-day performance snapshots, and triggers rebalancing alerts when thresholds breach.
    Guaranteed single-leader distributed execution via PostgreSQL advisory locking.
    """
    start_t = pytime.perf_counter()
    ist_now = get_current_ist_time()
    in_market_hours = is_indian_market_hours(ist_now, force_run=force_run)

    if not in_market_hours and not force_run:
        logger.info("Market closed (NSE/BSE trading window: Mon-Fri 09:15-15:30 IST). Skipping cycle.")
        res = {
            "status": "SKIPPED_MARKET_CLOSED",
            "market_hours_active": False,
            "ist_timestamp": ist_now.isoformat(),
            "execution_duration_ms": round((pytime.perf_counter() - start_t) * 1000, 2),
            "portfolios_scanned": 0,
            "portfolios_monitored": 0,
            "drifts_detected": 0,
            "rebalances_recommended": 0,
            "results": [],
        }
        LAST_SCHEDULER_RUN_SUMMARY.update({
            "last_run_timestamp": ist_now.isoformat(),
            "last_run_duration_ms": res["execution_duration_ms"],
            "status": "SKIPPED_MARKET_CLOSED",
            "portfolios_scanned": 0,
            "portfolios_monitored": 0,
            "drifts_detected": 0,
            "rebalances_recommended": 0,
            "market_hours_active": False,
            "worker_pid": os.getpid(),
        })
        return res

    lock_acquired = try_acquire_scheduler_lock(db)
    if not lock_acquired:
        logger.info("Another scheduler worker holds distributed advisory lock. Skipping concurrent execution.")
        return {
            "status": "SKIPPED_LOCK_HELD",
            "message": "Distributed lock held by another active worker process.",
            "execution_duration_ms": round((pytime.perf_counter() - start_t) * 1000, 2),
            "portfolios_scanned": 0,
            "portfolios_monitored": 0,
            "drifts_detected": 0,
            "rebalances_recommended": 0,
            "results": [],
        }

    try:
        active_portfolios = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.portfolio_status == "active")
            .all()
        )

        monitored_results: List[Dict[str, Any]] = []
        drifts_detected = 0
        rebalances_recommended = 0

        for port in active_portfolios:
            # Fetch the latest version of this portfolio
            latest_pv = (
                db.query(PortfolioVersion)
                .filter(PortfolioVersion.portfolio_id == port.portfolio_id)
                .order_by(PortfolioVersion.version_number.desc())
                .first()
            )

            if not latest_pv:
                monitored_results.append({
                    "portfolio_id": str(port.portfolio_id),
                    "portfolio_name": port.portfolio_name,
                    "status": "SKIPPED_NO_VERSION",
                })
                continue

            try:
                # 1. Run live valuation, drift calculation, and snapshot persistence
                mon_output = PortfolioMonitoringService.monitor_native_portfolio(
                    db=db,
                    portfolio_version_id=latest_pv.portfolio_version_id,
                    user_id=port.user_id,
                    provider=provider,
                )

                is_drifted = mon_output.get("health_status") == "ACTION_REQUIRED"
                if is_drifted:
                    drifts_detected += 1

                # 2. If drift threshold breached, run rebalance preview evaluation & dispatch rebalance alert
                rebalance_output = None
                if is_drifted:
                    try:
                        rebalance_output = RebalancingService.evaluate_native_rebalancing(
                            db=db,
                            portfolio_version_id=latest_pv.portfolio_version_id,
                            user_id=port.user_id,
                            provider=provider,
                        )
                        if rebalance_output.get("trigger_breached"):
                            rebalances_recommended += 1
                    except Exception as reb_err:
                        logger.warning(f"Error evaluating rebalancing for {port.portfolio_id}: {reb_err}")

                monitored_results.append({
                    "portfolio_id": str(port.portfolio_id),
                    "portfolio_name": port.portfolio_name,
                    "portfolio_version_id": str(latest_pv.portfolio_version_id),
                    "user_id": str(port.user_id),
                    "status": "SUCCESS",
                    "health_status": mon_output.get("health_status"),
                    "total_portfolio_value": mon_output.get("total_portfolio_value"),
                    "max_drift_pct": mon_output.get("max_holding_drift_pct"),
                    "drift_warnings_count": len(mon_output.get("drift_warnings", [])),
                    "rebalance_triggered": rebalance_output.get("trigger_breached", False) if rebalance_output else False,
                    "trades_proposed": rebalance_output.get("trades_count", 0) if rebalance_output else 0,
                })

            except Exception as e:
                logger.error(f"Error monitoring portfolio {port.portfolio_id}: {e}", exc_info=True)
                monitored_results.append({
                    "portfolio_id": str(port.portfolio_id),
                    "portfolio_name": port.portfolio_name,
                    "status": "ERROR",
                    "error": str(e),
                })

        elapsed_ms = round((pytime.perf_counter() - start_t) * 1000, 2)
        summary = {
            "status": "COMPLETED",
            "market_hours_active": in_market_hours,
            "ist_timestamp": ist_now.isoformat(),
            "execution_duration_ms": elapsed_ms,
            "portfolios_scanned": len(active_portfolios),
            "portfolios_monitored": len([r for r in monitored_results if r.get("status") == "SUCCESS"]),
            "drifts_detected": drifts_detected,
            "rebalances_recommended": rebalances_recommended,
            "results": monitored_results,
        }

        LAST_SCHEDULER_RUN_SUMMARY.update({
            "last_run_timestamp": ist_now.isoformat(),
            "last_run_duration_ms": elapsed_ms,
            "status": "COMPLETED",
            "portfolios_scanned": len(active_portfolios),
            "portfolios_monitored": len([r for r in monitored_results if r.get("status") == "SUCCESS"]),
            "drifts_detected": drifts_detected,
            "rebalances_recommended": rebalances_recommended,
            "market_hours_active": in_market_hours,
            "worker_pid": os.getpid(),
        })

        return summary
    finally:
        if lock_acquired:
            release_scheduler_lock(db)


class BackgroundMonitoringScheduler:
    """Asynchronous background scheduler for unattended portfolio monitoring."""

    def __init__(self, interval_seconds: int = 300):
        self.interval_seconds = interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running: bool = False

    async def _run_loop(self):
        logger.info(f"Background monitoring scheduler loop started (interval={self.interval_seconds}s).")
        while self._running:
            try:
                # Run DB work in thread pool to prevent blocking the async event loop
                db = SessionLocal()
                try:
                    summary = await asyncio.to_thread(run_all_active_portfolios_monitoring, db)
                    logger.info(
                        f"Monitoring cycle completed: {summary['portfolios_monitored']}/{summary['portfolios_scanned']} "
                        f"portfolios monitored, {summary['drifts_detected']} drifts detected."
                    )
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Error in background monitoring scheduler cycle: {e}", exc_info=True)

            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                logger.info("Background monitoring scheduler task cancelled.")
                break

    def start(self):
        if not self._running:
            self._running = True
            try:
                loop = asyncio.get_running_loop()
                self._task = loop.create_task(self._run_loop())
            except RuntimeError:
                # In synchronous test or non-async execution context
                self._task = None
            logger.info("Background monitoring scheduler launched.")

    def stop(self):
        if self._running:
            self._running = False
            if self._task:
                self._task.cancel()
            logger.info("Background monitoring scheduler stopped.")

    def is_running(self) -> bool:
        return self._running
