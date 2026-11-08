"""
Unified Rebalancing and Drift Trigger Service for Lucid Platform.
Supports both Native Generated Portfolios and Imported Brokerage Portfolios.
Enforces whole-share integer lot sizing, post-trade policy constraints,
statutory Indian equity transaction cost estimation, and automated alert dispatch.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

try:
    from backend.models.portfolio import InvestorPortfolio, PortfolioVersion
    from backend.models.diagnosis import ExistingPortfolio, ExistingPortfolioHolding
    from backend.portfolio_engine.monitoring_service import (
        PortfolioMonitoringService,
        DRIFT_THRESHOLD_STOCK_PCT,
        DRIFT_THRESHOLD_SECTOR_PCT,
        MAX_PERMITTED_SINGLE_STOCK_PCT,
        MAX_PERMITTED_SECTOR_PCT,
    )
    from backend.services.notification_service import NotificationService
    from backend.portfolio_engine.transaction_costs import (
        TransactionCostEngine,
        estimate_indian_equity_transaction_costs,
        ExchangeCode,
        DEFAULT_BROKER_PROFILES,
    )
except ImportError:
    from models.portfolio import InvestorPortfolio, PortfolioVersion
    from models.diagnosis import ExistingPortfolio, ExistingPortfolioHolding
    from portfolio_engine.monitoring_service import (
        PortfolioMonitoringService,
        DRIFT_THRESHOLD_STOCK_PCT,
        DRIFT_THRESHOLD_SECTOR_PCT,
        MAX_PERMITTED_SINGLE_STOCK_PCT,
        MAX_PERMITTED_SECTOR_PCT,
    )
    from services.notification_service import NotificationService
    from portfolio_engine.transaction_costs import (
        TransactionCostEngine,
        estimate_indian_equity_transaction_costs,
        ExchangeCode,
        DEFAULT_BROKER_PROFILES,
    )



class RebalancingService:
    """Orchestrates drift threshold evaluation, whole-share trade previews, and notification alerts."""

    @classmethod
    def evaluate_native_rebalancing(
        cls,
        db: Session,
        portfolio_version_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        stock_drift_threshold: float = DRIFT_THRESHOLD_STOCK_PCT,
        sector_drift_threshold: float = DRIFT_THRESHOLD_SECTOR_PCT,
        provider: Optional[Any] = None,
        exchange: str = "NSE",
        broker_profile_id: Optional[str] = "flat_20",
    ) -> Dict[str, Any]:
        """
        Evaluates drift for a native portfolio version.
        If thresholds are breached, generates whole-share trade preview (BUY/SELL/HOLD),
        calculates turnover, verifies cash conservation, computes Indian transaction costs,
        and dispatches a rebalancing notification.
        """
        mon = PortfolioMonitoringService.monitor_native_portfolio(
            db=db,
            portfolio_version_id=portfolio_version_id,
            user_id=user_id,
            provider=provider,
        )

        total_cap = float(mon["total_portfolio_value"])
        holdings = mon["holdings"]
        max_drift = float(mon["max_holding_drift_pct"])
        drift_warnings = mon["drift_warnings"]

        # Check triggers
        trigger_breached = (
            max_drift >= stock_drift_threshold
            or any("exceeds" in w for w in drift_warnings)
            or any(abs(s.get("sector_drift_pct", 0.0)) >= sector_drift_threshold for s in mon.get("sectors", []))
        )

        suggestions = []
        total_post_rebalance_invested = 0.0

        for h in holdings:
            sym = h["symbol"]
            curr_qty = int(h["quantity"])
            price = float(h["current_price"])
            tgt_wt = float(h["target_weight_pct"])
            curr_wt = float(h["current_weight_pct"])
            drift = float(h["weight_drift_pct"])

            if price <= 0:
                continue

            # Target capital value under target weight
            tgt_val = total_cap * (tgt_wt / 100.0)
            # Whole-share integer rounding
            tgt_qty = int(tgt_val // price)
            qty_change = tgt_qty - curr_qty
            trade_val = round(qty_change * price, 2)

            if qty_change > 0:
                action = "buy"
                rat = f"Adding {qty_change} share(s) of {sym} to restore target weight of {tgt_wt:.1f}% (currently {curr_wt:.1f}%)."
            elif qty_change < 0:
                action = "sell"
                rat = f"Trimming {abs(qty_change)} share(s) of {sym} to rebalance drift of {drift:+.1f}% and harvest capital gains."
            else:
                action = "hold"
                rat = f"Maintaining current position of {curr_qty} share(s); allocation is aligned with target weight {tgt_wt:.1f}%."

            post_val = round(tgt_qty * price, 2)
            total_post_rebalance_invested += post_val

            suggestions.append({
                "security_id": str(h.get("security_id") or h.get("symbol") or uuid.uuid4()),
                "symbol": sym,
                "company_name": h.get("company_name", sym),
                "sector": h.get("sector", "General"),
                "action": action.upper(),
                "current_quantity": curr_qty,
                "target_quantity": tgt_qty,
                "quantity_change": qty_change,
                "trade_quantity": qty_change,
                "latest_price": price,
                "reference_price": price,
                "current_weight_pct": curr_wt,
                "target_weight_pct": tgt_wt,
                "post_rebalance_weight_pct": round((post_val / total_cap) * 100.0, 2) if total_cap > 0 else 0.0,
                "trade_value": abs(trade_val),
                "rationale": rat,
            })

        # Cash balance post-rebalancing with strict non-negative cash conservation
        post_cash = round(total_cap - total_post_rebalance_invested, 2)
        while post_cash < 0:
            # If rounding causes slight over-allocation, trim 1 share from the largest buy trade
            buy_trades = [s for s in suggestions if s["action"] == "BUY" and s["target_quantity"] > 0]
            if not buy_trades:
                break
            # Find largest buy by trade_value
            largest_buy = max(buy_trades, key=lambda s: s["trade_value"])
            largest_buy["target_quantity"] -= 1
            largest_buy["trade_quantity"] -= 1
            largest_buy["quantity_change"] -= 1
            if largest_buy["trade_quantity"] == 0:
                largest_buy["action"] = "HOLD"
            price = largest_buy["latest_price"]
            largest_buy["trade_value"] = round(abs(largest_buy["trade_quantity"]) * price, 2)
            post_val = round(largest_buy["target_quantity"] * price, 2)
            largest_buy["post_rebalance_weight_pct"] = round((post_val / total_cap) * 100.0, 2) if total_cap > 0 else 0.0
            total_post_rebalance_invested -= price
            post_cash = round(total_cap - total_post_rebalance_invested, 2)

        # Audit post-trade sector exposures
        post_sector_weights: Dict[str, float] = {}
        for s in suggestions:
            sec = s["sector"]
            post_sector_weights[sec] = post_sector_weights.get(sec, 0.0) + s["post_rebalance_weight_pct"]
        post_sector_summary = [
            {
                "sector": sec,
                "post_rebalance_weight_pct": round(wt, 2),
                "policy_cap_pct": MAX_PERMITTED_SECTOR_PCT,
                "within_limit": wt <= MAX_PERMITTED_SECTOR_PCT,
            }
            for sec, wt in sorted(post_sector_weights.items(), key=lambda x: -x[1])
        ]

        turnover_pct = round(
            sum(abs(s["post_rebalance_weight_pct"] - s["current_weight_pct"]) for s in suggestions) / 2.0,
            2,
        )

        # Compute statutory Indian equity transaction costs with broker and exchange awareness
        tx_costs = estimate_indian_equity_transaction_costs(
            suggestions,
            exchange=exchange,
            broker_profile_id=broker_profile_id,
        )

        # Account for transaction costs in net cash conservation
        total_costs = float(tx_costs.get("total_estimated_costs", 0.0))
        estimated_post_trade_cash = round(post_cash - total_costs, 2)
        while estimated_post_trade_cash < 0:
            buy_trades = [s for s in suggestions if s["action"] == "BUY" and s["target_quantity"] > 0]
            if not buy_trades:
                break
            largest_buy = max(buy_trades, key=lambda s: s["trade_value"])
            largest_buy["target_quantity"] -= 1
            largest_buy["trade_quantity"] -= 1
            largest_buy["quantity_change"] -= 1
            if largest_buy["trade_quantity"] == 0:
                largest_buy["action"] = "HOLD"
            price = largest_buy["latest_price"]
            largest_buy["trade_value"] = round(abs(largest_buy["trade_quantity"]) * price, 2)
            post_val = round(largest_buy["target_quantity"] * price, 2)
            largest_buy["post_rebalance_weight_pct"] = round((post_val / total_cap) * 100.0, 2) if total_cap > 0 else 0.0
            total_post_rebalance_invested -= price
            post_cash = round(total_cap - total_post_rebalance_invested, 2)
            tx_costs = estimate_indian_equity_transaction_costs(
                suggestions,
                exchange=exchange,
                broker_profile_id=broker_profile_id,
            )
            total_costs = float(tx_costs.get("total_estimated_costs", 0.0))
            estimated_post_trade_cash = round(post_cash - total_costs, 2)

        rebalance_status = "rebalance_recommended" if trigger_breached else "no_trades_required"

        # Dispatch notification if trigger was breached and user_id is provided
        if user_id and trigger_breached:
            try:
                NotificationService.create_notification(
                    db=db,
                    user_id=user_id,
                    notification_type="rebalance_available",
                    title="Portfolio Rebalancing Available",
                    message=(
                        f"Rebalancing preview ready: {len([s for s in suggestions if s['action'] != 'HOLD'])} trades proposed "
                        f"with {turnover_pct:.1f}% portfolio turnover to realign holdings with target weights."
                    ),
                    metadata={
                        "portfolio_version_id": str(portfolio_version_id),
                        "turnover_pct": turnover_pct,
                        "trades_count": len([s for s in suggestions if s["action"] != "HOLD"]),
                        "total_estimated_costs": tx_costs["total_estimated_costs"],
                    },
                    cooldown_minutes=120,
                )
            except Exception:
                pass

        return {
            "portfolio_version_id": str(portfolio_version_id),
            "rebalance_status": rebalance_status,
            "trigger_breached": trigger_breached,
            "trigger_status": "REBALANCE_TRIGGERED" if trigger_breached else "NO_ACTION_REQUIRED",
            "triggers_breached": [w for w in drift_warnings if "exceeds" in w] if trigger_breached else [],
            "max_drift_pct": max_drift,
            "total_portfolio_value": total_cap,
            "total_post_rebalance_invested": round(total_post_rebalance_invested, 2),
            "unallocated_cash_post_rebalance": post_cash,
            "post_rebalance_cash": post_cash,
            "estimated_post_trade_cash": estimated_post_trade_cash,
            "net_cash_impact": float(tx_costs.get("net_cash_impact", 0.0)),
            "turnover_pct": turnover_pct,
            "turnover_amount": round((turnover_pct / 100.0) * total_cap, 2),
            "trades_required_count": len([s for s in suggestions if s["action"] != "HOLD"]),
            "trades_count": len([s for s in suggestions if s["action"] != "HOLD"]),
            "warnings": drift_warnings,
            "suggestions": suggestions,
            "trades": suggestions,
            "post_rebalance_sectors": post_sector_summary,
            "transaction_costs": tx_costs,
            "non_custodial_disclosure": (
                "Lucid operates as a non-custodial mathematical research and advisory interface under "
                "SEBI (Investment Advisers) Regulations, 2013 standards. Lucid does not place trades or "
                "exercise discretionary broker routing. You must review and execute recommended whole-share "
                "trades through your registered broker."
            ),
        }
