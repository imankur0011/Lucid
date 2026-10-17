"""
Portfolio Engine Orchestration Service.
Connects candidate selection, optimization, integer-share rounding, risk metrics, and validation.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
import uuid
from datetime import date, datetime
from sqlalchemy.orm import Session

try:
    from backend.portfolio_engine.candidate_selection import CandidateUniverseSelector
    from backend.portfolio_engine.constraints import PortfolioConstraints, get_effective_constraints
    from backend.portfolio_engine.optimizer import optimize_portfolio_allocations
    from backend.portfolio_engine.allocation_rounding import calculate_integer_shares_and_amounts
    from backend.portfolio_engine.risk_metrics import compute_portfolio_metrics
    from backend.portfolio_engine.validators import PortfolioValidator
except ImportError:
    from portfolio_engine.candidate_selection import CandidateUniverseSelector
    from portfolio_engine.constraints import PortfolioConstraints, get_effective_constraints
    from portfolio_engine.optimizer import optimize_portfolio_allocations
    from portfolio_engine.allocation_rounding import calculate_integer_shares_and_amounts
    from portfolio_engine.risk_metrics import compute_portfolio_metrics
    from portfolio_engine.validators import PortfolioValidator


class PortfolioEngineService:
    """End-to-end deterministic portfolio calculation and validation service."""

    def __init__(self, db: Session):
        self.db = db

    def generate_portfolio(
        self,
        investment_amount: Decimal,
        risk_category: str = "moderate",
        investment_horizon_months: int = 60,
        excluded_sectors: Optional[List[str]] = None,
        excluded_instruments: Optional[List[str]] = None,
        max_single_stock_pct: float = 25.0,
        max_sector_pct: float = 40.0,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Executes the full deterministic portfolio calculation pipeline.
        Returns a structured result with holdings, metrics, validation, and explanations.
        """
        # 1. Select eligible candidates
        selector = CandidateUniverseSelector(self.db)
        candidates = selector.select_eligible_candidates(
            excluded_sectors=excluded_sectors,
            excluded_instruments=excluded_instruments,
            as_of_date=as_of_date,
        )

        if not candidates:
            return {
                "success": False,
                "error": "No eligible securities found after applying exclusions and freshness checks",
                "holdings": [],
                "validation": {"validation_status": "failed"},
            }

        # 2. Build mathematical constraints with deterministic precedence hierarchy:
        # effective_limit = min(HARD_POLICY_CEILING, RISK_PROFILE_CEILING, INVESTOR_REQUESTED_LIMIT)
        constraints = get_effective_constraints(
            risk_category=risk_category,
            requested_max_stock_pct=max_single_stock_pct,
            requested_max_sector_pct=max_sector_pct,
            min_stocks_count=min(3, len(candidates)),
        )

        # 3. Optimize allocations
        opt_success, raw_allocations, opt_msg = optimize_portfolio_allocations(
            candidates=candidates,
            risk_category=risk_category,
            constraints=constraints,
        )

        if not opt_success or not raw_allocations:
            return {
                "success": False,
                "error": f"Portfolio optimization failed: {opt_msg}",
                "holdings": [],
                "validation": {"validation_status": "failed"},
            }

        # 4. Round integer shares & calculate amounts
        enriched_holdings, total_invested, unallocated_cash = calculate_integer_shares_and_amounts(
            allocations=raw_allocations,
            total_investment_amount=investment_amount,
        )

        # 5. Compute risk & diversification metrics
        metrics = compute_portfolio_metrics(enriched_holdings)

        # 6. Run hard mathematical validation
        validator = PortfolioValidator(constraints=constraints)
        validation_output = validator.validate_portfolio(
            allocations=enriched_holdings,
            investment_amount=investment_amount,
        )

        # 7. Generate structured user-facing explanations
        explanations = self._build_explanations(
            enriched_holdings,
            risk_category,
            investment_amount,
            unallocated_cash,
            metrics,
        )

        return {
            "success": validation_output["all_passed"],
            "investment_amount": investment_amount,
            "total_invested": total_invested,
            "unallocated_cash": unallocated_cash,
            "risk_category": risk_category,
            "investment_horizon_months": investment_horizon_months,
            "metrics": metrics,
            "holdings": enriched_holdings,
            "validation": validation_output,
            "explanations": explanations,
            "as_of_date": as_of_date or date.today(),
        }

    def _build_explanations(
        self,
        holdings: List[Dict[str, Any]],
        risk_category: str,
        total_amount: Decimal,
        unallocated_cash: Decimal,
        metrics: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        """Generates evidence-backed structured explanation cards."""
        explanations = []

        # 1. Overall strategy explanation
        explanations.append({
            "explanation_type": "portfolio",
            "title": f"Tailored {risk_category.capitalize()} Portfolio Strategy",
            "explanation_text": (
                f"Constructed a diversified {len(holdings)}-instrument equity portfolio "
                f"targeting {metrics['expected_return_pct']:.2f}% expected annualized return with "
                f"{metrics['expected_volatility_pct']:.2f}% expected volatility, calibrated for "
                f"an investor with a {risk_category} risk profile."
            ),
            "display_order": 1,
        })

        # 2. Diversification explanation
        explanations.append({
            "explanation_type": "diversification",
            "title": "Risk Diversification and Concentration Control",
            "explanation_text": (
                f"Portfolio achieves a diversification score of {metrics['diversification_score']:.1f}/100 "
                f"(Herfindahl-Hirschman Index: {metrics['herfindahl_index']:.4f}). Exposure across sectors "
                f"is strictly capped to prevent over-concentration in any single market segment."
            ),
            "display_order": 2,
        })

        # 3. Security selection explanations
        for idx, h in enumerate(holdings, start=3):
            explanations.append({
                "explanation_type": "selection",
                "title": f"Selection: {h['symbol']} ({h['security_name']})",
                "explanation_text": (
                    f"Allocated {h['target_weight_pct']:.2f}% (₹{h['target_amount']:,.2f}, {h['shares_quantity']} shares "
                    f"at ₹{h['latest_price']:,.2f}). Selected for strong representation in the {h['sector_name']} sector "
                    f"and complementary risk-return profile within the portfolio."
                ),
                "display_order": idx,
                "security_id": h.get("security_id"),
            })

        # 4. Cash buffer explanation
        if unallocated_cash > 0:
            explanations.append({
                "explanation_type": "constraint",
                "title": "Unallocated Cash Buffer",
                "explanation_text": (
                    f"₹{unallocated_cash:,.2f} retained in liquid cash balance due to whole-share integer rounding at "
                    f"current market prices. Can be deployed on the next scheduled rebalancing."
                ),
                "display_order": len(explanations) + 1,
            })

        return explanations
