"""
Portfolio Monitoring Service for Lucid Platform.
Performs dynamic holding valuation, current weight calculation, drift detection,
portfolio health auditing, performance snapshot persistence, and automated alert dispatch.
"""

import uuid
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

try:
    from backend.models.portfolio import (
        InvestorPortfolio,
        PortfolioVersion,
        PortfolioSecurityDecision,
    )
    from backend.models.broker import PortfolioPerformanceSnapshot
    from backend.models.market_data import MarketPrice
    from backend.models.security import InstrumentListing, Security
    from backend.models.diagnosis import ExistingPortfolio, ExistingPortfolioHolding
    from backend.market_data.adapter import MarketDataProvider, SimulatedMarketProvider, YFinanceProvider
    from backend.services.notification_service import NotificationService
except ImportError:
    from models.portfolio import (
        InvestorPortfolio,
        PortfolioVersion,
        PortfolioSecurityDecision,
    )
    from models.broker import PortfolioPerformanceSnapshot
    from models.market_data import MarketPrice
    from models.security import InstrumentListing, Security
    from models.diagnosis import ExistingPortfolio, ExistingPortfolioHolding
    from market_data.adapter import MarketDataProvider, SimulatedMarketProvider, YFinanceProvider
    from services.notification_service import NotificationService


# Centralized Lucid Internal Risk & Drift Policy Thresholds
try:
    from backend.portfolio_engine.policy import (
        DEFAULT_MAX_SINGLE_STOCK_PCT as MAX_PERMITTED_SINGLE_STOCK_PCT,
        DEFAULT_MAX_SECTOR_PCT as MAX_PERMITTED_SECTOR_PCT,
        DEFAULT_DRIFT_THRESHOLD_STOCK_PCT as DRIFT_THRESHOLD_STOCK_PCT,
        DEFAULT_DRIFT_THRESHOLD_SECTOR_PCT as DRIFT_THRESHOLD_SECTOR_PCT,
        get_portfolio_policy_limits,
    )
except ImportError:
    from portfolio_engine.policy import (
        DEFAULT_MAX_SINGLE_STOCK_PCT as MAX_PERMITTED_SINGLE_STOCK_PCT,
        DEFAULT_MAX_SECTOR_PCT as MAX_PERMITTED_SECTOR_PCT,
        DEFAULT_DRIFT_THRESHOLD_STOCK_PCT as DRIFT_THRESHOLD_STOCK_PCT,
        DEFAULT_DRIFT_THRESHOLD_SECTOR_PCT as DRIFT_THRESHOLD_SECTOR_PCT,
        get_portfolio_policy_limits,
    )


class PortfolioMonitoringService:
    """Computes real-time dynamic portfolio revaluations, drifts, and health metrics."""

    @staticmethod
    def get_latest_prices_batch(
        db: Session, symbols: List[str], provider: Optional[Any] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Retrieves latest available market quotes for a batch of symbols.
        Checks recent market prices in DB first; if missing, fetches via provider.
        """
        results: Dict[str, Dict[str, Any]] = {}
        today = date.today()

        for sym in symbols:
            s_clean = sym.strip().upper()
            # If symbol is a numeric BSE scrip code, resolve to primary NSE ticker symbol
            if s_clean.isdigit():
                bse_listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == s_clean).first()
                if bse_listing:
                    all_listings = db.query(InstrumentListing).filter(InstrumentListing.security_id == bse_listing.security_id).all()
                    nse_listing = next((l for l in all_listings if not l.symbol.isdigit()), None)
                    if nse_listing:
                        s_clean = nse_listing.symbol

            # 1. Query latest market price from DB
            latest_db_price = (
                db.query(MarketPrice)
                .join(InstrumentListing, MarketPrice.listing_id == InstrumentListing.listing_id)
                .filter(InstrumentListing.symbol == s_clean)
                .order_by(desc(MarketPrice.price_date))
                .first()
            )

            if latest_db_price and latest_db_price.close_price and float(latest_db_price.close_price) > 0:
                results[s_clean] = {
                    "price": float(latest_db_price.close_price),
                    "price_date": latest_db_price.price_date.isoformat(),
                    "source": "database_market_price",
                }
            else:
                # 2. Fetch on-demand via real market provider (YFinance)
                if provider is None:
                    provider = YFinanceProvider()
                try:
                    q = provider.fetch_latest_quote(s_clean)
                    p = float(q.get("close") or q.get("open") or 100.0)
                    results[s_clean] = {
                        "price": p,
                        "price_date": today.isoformat(),
                        "source": type(provider).__name__,
                    }
                except Exception:
                    results[s_clean] = {
                        "price": 100.0,
                        "price_date": today.isoformat(),
                        "source": "fallback_default",
                    }

        return results

    @classmethod
    def monitor_native_portfolio(
        cls,
        db: Session,
        portfolio_version_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        provider: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Calculates dynamic valuation, current weights, and drift for a native Lucid PortfolioVersion.
        Persists a performance snapshot and creates alerts if thresholds are breached.
        """
        pv = db.query(PortfolioVersion).filter(PortfolioVersion.portfolio_version_id == portfolio_version_id).first()
        if not pv:
            raise ValueError(f"PortfolioVersion {portfolio_version_id} not found")

        # Resolve user_id from parent portfolio if not provided
        if not user_id:
            parent_port = db.query(InvestorPortfolio).filter(InvestorPortfolio.portfolio_id == pv.portfolio_id).first()
            user_id = parent_port.user_id if parent_port else None

        # Extract holdings/positions from optimizer_output or allocations in generation_context
        ctx = pv.generation_context or {}
        opt = ctx.get("optimizer_output") or {}
        raw_positions = opt.get("positions") or []
        unallocated_cash = float(opt.get("unallocated_cash") or ctx.get("unallocated_cash") or 0.0)
        original_investment = float(pv.investment_amount)

        def _resolve_security_info(ticker: str, fallback_sec_id=None, fallback_name=None):
            sec = None
            if fallback_sec_id:
                try:
                    fid = uuid.UUID(str(fallback_sec_id))
                    sec = db.query(Security).filter(Security.security_id == fid).first()
                except Exception:
                    pass
            if not sec and ticker:
                listing = (
                    db.query(InstrumentListing)
                    .filter(func.upper(InstrumentListing.symbol) == ticker.upper())
                    .first()
                )
                if listing:
                    sec = db.query(Security).filter(Security.security_id == listing.security_id).first()

            sec_id_str = str(sec.security_id) if sec else (str(fallback_sec_id) if fallback_sec_id else str(uuid.uuid4()))
            company_name = sec.security_name if sec else (fallback_name or ticker)

            sec_sector = "General"
            if sec and sec.company and sec.company.industries:
                ind = sec.company.industries[0].industry
                if ind and ind.sector:
                    sec_sector = ind.sector.sector_name
            return sec_id_str, company_name, sec_sector

        if not raw_positions and "allocations" in ctx:
            raw_positions = [
                {
                    "security_id": str(a.get("security_id")) if a.get("security_id") else None,
                    "ticker": a.get("symbol"),
                    "company_name": a.get("security_name"),
                    "sector": a.get("sector_name"),
                    "target_quantity": a.get("shares_quantity"),
                    "reference_price": a.get("latest_price"),
                    "target_weight_pct": a.get("target_weight_pct"),
                }
                for a in ctx.get("allocations", [])
            ]

        if not raw_positions:
            decisions = (
                db.query(PortfolioSecurityDecision)
                .filter(PortfolioSecurityDecision.portfolio_version_id == portfolio_version_id)
                .all()
            )
            raw_positions = []
            for d in decisions:
                sec = db.query(Security).filter(Security.security_id == d.security_id).first()
                if not sec:
                    continue
                listings = db.query(InstrumentListing).filter(InstrumentListing.security_id == d.security_id).all()
                nse_listing = next((l for l in listings if not l.symbol.isdigit()), listings[0] if listings else None)
                sym = nse_listing.symbol if nse_listing else "UNKNOWN"
                target_wt = float(d.target_weight_pct or 0.0)
                quotes = cls.get_latest_prices_batch(db, [sym], provider)
                price = quotes.get(sym, {}).get("price", 100.0)
                qty = int((original_investment * (target_wt / 100.0)) // price) if price > 0 else 0

                sec_sector = "General"
                if sec.company and sec.company.industries:
                    ind = sec.company.industries[0].industry
                    if ind and ind.sector:
                        sec_sector = ind.sector.sector_name
                if sec_sector == "General" and d.decision_reason and "in " in d.decision_reason:
                    sec_sector = d.decision_reason.split("in ")[-1].strip() or "General"

                raw_positions.append({
                    "security_id": str(sec.security_id),
                    "ticker": sym,
                    "company_name": sec.security_name,
                    "sector": sec_sector,
                    "target_quantity": qty,
                    "reference_price": price,
                    "target_weight_pct": target_wt,
                })

        symbols = [p.get("ticker") for p in raw_positions if p.get("ticker")]
        quotes = cls.get_latest_prices_batch(db, symbols, provider)

        holdings_evaluated = []
        total_equity_market_value = 0.0

        # Step 1: Compute holding market values V_i = Q_i * P_i
        for pos in raw_positions:
            ticker = (pos.get("ticker") or "").upper()
            qty = int(pos.get("target_quantity") or 0)
            ref_price = float(pos.get("reference_price") or 0.0)
            quote = quotes.get(ticker, {})
            curr_price = float(quote.get("price") or ref_price)

            pos_sec_id = pos.get("security_id")
            pos_sector = pos.get("sector")
            if not pos_sec_id or not pos_sector or pos_sector == "General":
                resolved_id, resolved_name, resolved_sec = _resolve_security_info(
                    ticker, fallback_sec_id=pos_sec_id, fallback_name=pos.get("company_name")
                )
                if not pos_sec_id:
                    pos_sec_id = resolved_id
                if not pos_sector or pos_sector == "General":
                    pos_sector = resolved_sec
            else:
                resolved_name = pos.get("company_name", ticker)

            curr_val = round(qty * curr_price, 2)
            orig_val = round(qty * ref_price, 2) if ref_price > 0 else curr_val
            pnl_amt = round(curr_val - orig_val, 2)
            pnl_pct = round((pnl_amt / orig_val) * 100.0, 2) if orig_val > 0 else 0.0

            total_equity_market_value += curr_val

            holdings_evaluated.append({
                "security_id": pos_sec_id,
                "symbol": ticker,
                "company_name": resolved_name,
                "sector": pos_sector,
                "sector_name": pos_sector,
                "quantity": qty,
                "shares_quantity": qty,
                "reference_price": ref_price,
                "current_price": curr_price,
                "latest_price": curr_price,
                "target_weight_pct": float(pos.get("target_weight_pct") or 0.0),
                "original_value": orig_val,
                "current_value": curr_val,
                "unrealized_pnl": pnl_amt,
                "unrealized_pnl_pct": pnl_pct,
                "price_source": quote.get("source", "market_price"),
            })

        total_portfolio_value = round(total_equity_market_value + unallocated_cash, 2)

        # Step 2: Compute current weights w_i = (V_i / V_total) * 100, drift, and sector aggregates
        sector_weights: Dict[str, Dict[str, float]] = {}
        drift_warnings: List[str] = []
        max_holding_drift = 0.0

        for h in holdings_evaluated:
            curr_wt = round((h["current_value"] / total_portfolio_value) * 100.0, 2) if total_portfolio_value > 0 else 0.0
            tgt_wt = h["target_weight_pct"]
            drift = round(curr_wt - tgt_wt, 2)
            abs_drift = round(abs(drift), 2)

            h["current_weight_pct"] = curr_wt
            h["weight_drift_pct"] = drift
            h["abs_weight_drift_pct"] = abs_drift
            h["drift_status"] = "ALIGNED" if abs_drift <= 2.0 else ("MILD_DRIFT" if abs_drift <= 5.0 else "SEVERE_DRIFT")

            if abs_drift > max_holding_drift:
                max_holding_drift = abs_drift

            if abs_drift >= DRIFT_THRESHOLD_STOCK_PCT:
                drift_warnings.append(
                    f"Holding {h['symbol']} has drifted by {drift:+.2f}% ({tgt_wt:.1f}% -> {curr_wt:.1f}%)"
                )

            # Concentration cap audit
            if curr_wt > MAX_PERMITTED_SINGLE_STOCK_PCT:
                drift_warnings.append(
                    f"Holding {h['symbol']} weight {curr_wt:.1f}% exceeds single-stock concentration cap ({MAX_PERMITTED_SINGLE_STOCK_PCT}%)"
                )

            # Sector aggregation
            sec = h["sector"]
            if sec not in sector_weights:
                sector_weights[sec] = {"target_weight_pct": 0.0, "current_weight_pct": 0.0}
            sector_weights[sec]["target_weight_pct"] += tgt_wt
            sector_weights[sec]["current_weight_pct"] += curr_wt

        # Sector drift & caps
        sector_summary = []
        for sec, wts in sector_weights.items():
            tgt_s = round(wts["target_weight_pct"], 2)
            cur_s = round(wts["current_weight_pct"], 2)
            s_drift = round(cur_s - tgt_s, 2)
            sector_summary.append({
                "sector": sec,
                "target_weight_pct": tgt_s,
                "current_weight_pct": cur_s,
                "sector_drift_pct": s_drift,
            })
            if abs(s_drift) >= DRIFT_THRESHOLD_SECTOR_PCT:
                drift_warnings.append(
                    f"Sector '{sec}' has drifted by {s_drift:+.2f}% ({tgt_s:.1f}% -> {cur_s:.1f}%)"
                )
            if cur_s > MAX_PERMITTED_SECTOR_PCT:
                drift_warnings.append(
                    f"Sector '{sec}' exposure {cur_s:.1f}% exceeds sector concentration ceiling ({MAX_PERMITTED_SECTOR_PCT}%)"
                )

        # Health status determination
        if len(drift_warnings) == 0:
            health_status = "HEALTHY"
            health_label = "Optimal Alignment"
        elif max_holding_drift >= DRIFT_THRESHOLD_STOCK_PCT or any("exceeds" in w for w in drift_warnings):
            health_status = "ACTION_REQUIRED"
            health_label = "Rebalancing Recommended"
        else:
            health_status = "MILD_DRIFT"
            health_label = "Minor Price Dispersion"

        total_pnl = round(total_portfolio_value - original_investment, 2)
        total_pnl_pct = round((total_pnl / original_investment) * 100.0, 2) if original_investment > 0 else 0.0

        # Step 3: Persist Performance Snapshot
        today_date = date.today()
        try:
            existing_snap = (
                db.query(PortfolioPerformanceSnapshot)
                .filter(
                    PortfolioPerformanceSnapshot.portfolio_version_id == portfolio_version_id,
                    PortfolioPerformanceSnapshot.snapshot_date == today_date,
                    PortfolioPerformanceSnapshot.source_type == "simulated",
                )
                .first()
            )
            if existing_snap:
                existing_snap.valuation_amount = total_portfolio_value
                existing_snap.cumulative_return_pct = total_pnl_pct
            else:
                snap = PortfolioPerformanceSnapshot(
                    performance_snapshot_id=uuid.uuid4(),
                    portfolio_version_id=portfolio_version_id,
                    snapshot_date=today_date,
                    valuation_amount=total_portfolio_value,
                    currency_code=pv.currency_code or "INR",
                    cumulative_return_pct=total_pnl_pct,
                    source_type="simulated",
                )
                db.add(snap)
            db.commit()
        except Exception:
            db.rollback()

        # Step 4: Dispatch in-app alert if material drift detected and user_id is known
        if user_id and health_status == "ACTION_REQUIRED":
            try:
                NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="portfolio_drift",
                    title="Portfolio Drift Alert",
                    message=(
                        f"Your portfolio has drifted by {max_holding_drift:.1f}%. "
                        f"{len(drift_warnings)} allocation warnings detected. A rebalancing review is recommended."
                    ),
                    metadata={
                        "portfolio_version_id": str(portfolio_version_id),
                        "max_drift_pct": max_holding_drift,
                        "health_status": health_status,
                    },
                    cooldown_minutes=120,
                )
            except Exception:
                pass

        return {
            "portfolio_id": str(pv.portfolio_id),
            "portfolio_version_id": str(portfolio_version_id),
            "as_of_date": datetime.now(timezone.utc).isoformat(),
            "original_investment_amount": original_investment,
            "total_portfolio_value": total_portfolio_value,
            "total_equity_value": round(total_equity_market_value, 2),
            "unallocated_cash": unallocated_cash,
            "unrealized_pnl": total_pnl,
            "unrealized_pnl_pct": total_pnl_pct,
            "health_status": health_status,
            "health_label": health_label,
            "max_holding_drift_pct": max_holding_drift,
            "drift_warnings": drift_warnings,
            "holdings": holdings_evaluated,
            "sectors": sector_summary,
        }
