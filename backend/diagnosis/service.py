"""
Portfolio Diagnosis and Rebalancing Service.
Analyzes existing investor holdings for concentration, diversification, and sector imbalances,
and generates structured, integer-share rebalancing previews without executing trades.
"""

from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import uuid
import math
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from backend.models import (
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Security,
        InstrumentListing,
        MarketPrice,
    )
    from backend.portfolio_engine import (
        PortfolioEngineService,
        compute_portfolio_metrics,
    )
    from backend.portfolio_engine.constraints import get_effective_constraints
except ImportError:
    from models import (
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Security,
        InstrumentListing,
        MarketPrice,
    )
    from portfolio_engine import (
        PortfolioEngineService,
        compute_portfolio_metrics,
    )
    from portfolio_engine.constraints import get_effective_constraints


class PortfolioDiagnosisService:
    """Service analyzing existing portfolios and generating deterministic rebalancing plans."""

    def __init__(self, db: Session):
        self.db = db

    def diagnose_and_rebalance(
        self,
        existing_portfolio_id: uuid.UUID,
        user_id: uuid.UUID,
        target_risk_category: str = "moderate",
    ) -> Dict[str, Any]:
        """
        Executes comprehensive diagnosis on an existing portfolio:
        1. Evaluates current holdings at latest market prices.
        2. Detects concentration risks (single-stock > 25%, sector > 40%).
        3. Computes current diversification score and risk metrics.
        4. Derives target optimal portfolio for the same total capital.
        5. Computes exact buy/sell/hold whole share suggestions, turnover, and unallocated cash.
        6. Persists diagnosis and rebalance records into PostgreSQL.
        """
        now = datetime.now()

        # 1. Fetch Existing Portfolio with user isolation
        portfolio = (
            self.db.query(ExistingPortfolio)
            .filter(
                ExistingPortfolio.existing_portfolio_id == existing_portfolio_id,
                ExistingPortfolio.user_id == user_id,
            )
            .first()
        )
        if not portfolio:
            raise ValueError("Existing portfolio not found or unauthorized access")

        if not portfolio.holdings:
            raise ValueError("Existing portfolio contains no holdings to diagnose")

        # 2. Price holdings and compute current values
        current_holdings = []
        total_market_val = Decimal("0.0")

        for h in portfolio.holdings:
            sec = h.security
            listing = h.listing or (sec.listings[0] if sec.listings else None)
            symbol = listing.symbol if listing else (sec.isin or "SECURITY")

            # Lookup latest market price
            latest_price = Decimal("100.0")
            if listing:
                price_rec = (
                    self.db.query(MarketPrice)
                    .filter(MarketPrice.listing_id == listing.listing_id)
                    .order_by(desc(MarketPrice.price_date))
                    .first()
                )
                if price_rec:
                    latest_price = Decimal(str(price_rec.close_price))

            qty = Decimal(str(h.quantity))
            holding_val = round(qty * latest_price, 2)
            total_market_val += holding_val

            sector_name = "General"
            if sec.company and sec.company.industries:
                ind = sec.company.industries[0].industry
                if ind and ind.sector:
                    sector_name = ind.sector.sector_name

            current_holdings.append({
                "security_id": sec.security_id,
                "listing_id": listing.listing_id if listing else None,
                "symbol": symbol,
                "security_name": sec.security_name,
                "sector_name": sector_name,
                "quantity": qty,
                "latest_price": latest_price,
                "current_value": holding_val,
            })

        if total_market_val <= Decimal("0.0"):
            raise ValueError("Portfolio total market value must be positive")

        # 3. Calculate current weights and identify warnings
        warnings = []
        sector_weights: Dict[str, Decimal] = {}

        for ch in current_holdings:
            weight = round((ch["current_value"] / total_market_val) * Decimal("100.0"), 2)
            ch["target_weight_pct"] = float(weight)  # for metric calculation
            sec = ch["sector_name"]
            sector_weights[sec] = sector_weights.get(sec, Decimal("0.0")) + weight

        eff_constraints = get_effective_constraints(risk_category=target_risk_category)
        stock_cap = Decimal(str(eff_constraints.max_single_stock_pct))
        sector_cap = Decimal(str(eff_constraints.max_sector_pct))

        for ch in current_holdings:
            weight = (ch["current_value"] / total_market_val) * Decimal("100.0")
            ch["weight_pct"] = float(round(weight, 2))
            sec = ch["sector_name"]
            sector_weights[sec] = sector_weights.get(sec, Decimal("0.0")) + weight

            if weight > stock_cap:
                warnings.append(
                    f"Excessive single-stock concentration: {ch['symbol']} represents {weight:.1f}% "
                    f"of total capital (Effective limit: {stock_cap}% for {target_risk_category})."
                )

        for sec_name, sec_wt in sector_weights.items():
            if sec_wt > sector_cap:
                warnings.append(
                    f"High sector concentration: '{sec_name}' represents {sec_wt:.1f}% of total portfolio (Effective limit: {sector_cap}%)."
                )

        current_metrics = compute_portfolio_metrics(current_holdings)

        # 4. Generate Target Allocation via PortfolioEngineService
        engine = PortfolioEngineService(self.db)
        target_res = engine.generate_portfolio(
            investment_amount=total_market_val,
            risk_category=target_risk_category,
            max_single_stock_pct=eff_constraints.max_single_stock_pct,
            max_sector_pct=eff_constraints.max_sector_pct,
        )

        target_holdings_by_id = {
            h["security_id"]: h for h in target_res.get("holdings", [])
        }

        # 5. Compute Buy/Sell/Hold Rebalance Suggestions
        all_security_ids = set(h["security_id"] for h in current_holdings) | set(target_holdings_by_id.keys())
        suggestions = []
        total_turnover_pct = 0.0

        for sec_id in all_security_ids:
            cur = next((h for h in current_holdings if h["security_id"] == sec_id), None)
            tgt = target_holdings_by_id.get(sec_id)

            cur_qty = int(cur["quantity"]) if cur else 0
            cur_price = cur["latest_price"] if cur else (Decimal(str(tgt["latest_price"])) if tgt else Decimal("100.0"))
            cur_val = cur["current_value"] if cur else Decimal("0.0")

            tgt_qty = int(tgt["shares_quantity"]) if tgt else 0
            tgt_val = Decimal(str(tgt["target_amount"])) if tgt else Decimal("0.0")

            qty_diff = tgt_qty - cur_qty
            change_val = round(Decimal(qty_diff) * cur_price, 2)

            cur_wt = float(cur["target_weight_pct"]) if cur else 0.0
            tgt_wt = float(tgt["target_weight_pct"]) if tgt else 0.0
            total_turnover_pct += abs(tgt_wt - cur_wt)

            if qty_diff > 0:
                action = "buy"
                explanation = (
                    f"Increase position by {qty_diff} shares (+₹{abs(change_val):,.2f}) to align with "
                    f"target allocation of {tgt_wt:.1f}%."
                )
            elif qty_diff < 0:
                action = "sell"
                explanation = (
                    f"Trim position by {abs(qty_diff)} shares (-₹{abs(change_val):,.2f}) to reduce concentration "
                    f"from {cur_wt:.1f}% to {tgt_wt:.1f}%."
                )
            else:
                action = "hold"
                explanation = f"Hold current position of {cur_qty} shares (aligned with target model)."

            symbol = cur["symbol"] if cur else (tgt["symbol"] if tgt else "EQUITY")

            suggestions.append({
                "security_id": sec_id,
                "symbol": symbol,
                "action": action,
                "current_quantity": cur_qty,
                "target_quantity": tgt_qty,
                "quantity_change": qty_diff,
                "current_value": cur_val,
                "target_value": tgt_val,
                "change_value": change_val,
                "explanation": explanation,
            })

        rebalance_turnover = round(total_turnover_pct / 2.0, 2)

        # 6. Persist Diagnosis and Suggestions to PostgreSQL
        diagnosis = PortfolioDiagnosis(
            portfolio_diagnosis_id=uuid.uuid4(),
            existing_portfolio_id=portfolio.existing_portfolio_id,
            diagnosis_status="completed",
            summary=(
                f"Evaluated {len(current_holdings)} holdings totaling ₹{total_market_val:,.2f}. "
                f"Diversification score is {current_metrics['diversification_score']:.1f}/100 with {len(warnings)} risk alerts. "
                f"Rebalance plan requires {rebalance_turnover:.1f}% portfolio turnover."
            ),
            metrics={
                "total_market_value": float(total_market_val),
                "current_metrics": current_metrics,
                "target_metrics": target_res.get("metrics", {}),
                "turnover_pct": rebalance_turnover,
                "warnings": warnings,
                "post_rebalance_unallocated_cash": float(target_res.get("unallocated_cash", Decimal("0.0"))),
            },
            market_context_as_of=now,
            started_at=now,
            completed_at=now,
        )
        self.db.add(diagnosis)
        self.db.flush()

        for s in suggestions:
            rs = RebalanceSuggestion(
                rebalance_suggestion_id=uuid.uuid4(),
                portfolio_diagnosis_id=diagnosis.portfolio_diagnosis_id,
                security_id=s["security_id"],
                suggested_action=s["action"],
                current_quantity=Decimal(str(s["current_quantity"])),
                target_quantity=Decimal(str(s["target_quantity"])),
                current_value=s["current_value"],
                target_value=s["target_value"],
                change_value=s["change_value"],
                explanation=s["explanation"],
            )
            self.db.add(rs)

        self.db.commit()

        return {
            "portfolio_diagnosis_id": diagnosis.portfolio_diagnosis_id,
            "existing_portfolio_id": portfolio.existing_portfolio_id,
            "portfolio_name": portfolio.portfolio_name,
            "total_market_value": total_market_val,
            "warnings": warnings,
            "current_metrics": current_metrics,
            "target_metrics": target_res.get("metrics", {}),
            "rebalance_turnover_pct": rebalance_turnover,
            "unallocated_cash": target_res.get("unallocated_cash", Decimal("0.0")),
            "suggestions": suggestions,
            "created_at": now,
        }
