"""
Deterministic Portfolio Validation Runner.
Executes all hard mathematical gates and produces database-ready validation records.
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
import uuid
from datetime import datetime

try:
    from backend.portfolio_engine.constraints import PortfolioConstraints, check_allocation_constraints
except ImportError:
    from portfolio_engine.constraints import PortfolioConstraints, check_allocation_constraints


class PortfolioValidator:
    """Validates candidate allocations against all mathematical, diversification, and regulatory constraints."""

    RULE_SET_VERSION = "in-diversified-safety-v1.0"
    CALCULATION_ENGINE_VERSION = "scipy-slsqp-v1.0"

    def __init__(self, constraints: Optional[PortfolioConstraints] = None):
        self.constraints = constraints or PortfolioConstraints()

    def validate_portfolio(
        self,
        allocations: List[Dict[str, Any]],
        investment_amount: Decimal,
    ) -> Dict[str, Any]:
        """
        Runs comprehensive validation.
        Returns: {
            'validation_status': 'passed' | 'passed_with_warnings' | 'failed',
            'summary': dict,
            'results': list of result records,
            'all_passed': bool
        }
        """
        now = datetime.now()
        results = []
        overall_passed = True
        has_warnings = False

        # 1. Investment amount validation
        if investment_amount <= Decimal("0.0"):
            overall_passed = False
            results.append({
                "rule_code": "INVESTMENT_AMOUNT_POSITIVE",
                "result_status": "fail",
                "severity": "critical",
                "actual_value": float(investment_amount),
                "threshold_value": 0.0,
                "result_message": f"Investment amount must be positive, got {investment_amount}",
                "details": {},
            })
        else:
            results.append({
                "rule_code": "INVESTMENT_AMOUNT_POSITIVE",
                "result_status": "pass",
                "severity": "info",
                "actual_value": float(investment_amount),
                "threshold_value": 0.0,
                "result_message": "Investment amount is valid and positive",
                "details": {},
            })

        # 2. Allocation constraints check
        constraints_passed, check_items = check_allocation_constraints(allocations, self.constraints)
        if not constraints_passed:
            overall_passed = False

        for c_res in check_items:
            res_status = "pass" if c_res["passed"] else ("warning" if c_res.get("severity") == "warning" else "fail")
            if res_status == "warning":
                has_warnings = True
            results.append({
                "rule_code": c_res["rule_code"],
                "result_status": res_status,
                "severity": c_res.get("severity", "info"),
                "actual_value": c_res.get("actual_value"),
                "threshold_value": c_res.get("threshold_value"),
                "result_message": c_res.get("message", ""),
                "details": {},
            })

        # 3. Post-Rounding Realized Allocation Validation
        if investment_amount > Decimal("0.0"):
            inv_amt_float = float(investment_amount)
            realized_total = 0.0
            realized_sectors: Dict[str, float] = {}

            for a in allocations:
                shares = a.get("shares_quantity")
                price = a.get("latest_price")
                if shares is not None and price is not None:
                    holding_val = float(shares) * float(price)
                    realized_total += holding_val
                    realized_w = (holding_val / inv_amt_float) * 100.0
                    sec = a.get("sector_name") or "General"
                    realized_sectors[sec] = realized_sectors.get(sec, 0.0) + realized_w

                    # Verify realized single stock exposure does not exceed bound
                    if realized_w > self.constraints.max_single_stock_pct + self.constraints.tolerance_pct:
                        overall_passed = False
                        results.append({
                            "rule_code": "POST_ROUNDING_STOCK_CAP",
                            "result_status": "fail",
                            "severity": "critical",
                            "actual_value": round(realized_w, 2),
                            "threshold_value": self.constraints.max_single_stock_pct,
                            "result_message": (
                                f"Realized post-rounding weight for {a.get('symbol')} ({realized_w:.2f}%) "
                                f"exceeds safety limit of {self.constraints.max_single_stock_pct}%"
                            ),
                            "details": {},
                        })

            # Verify realized sector exposure
            for sec_name, sec_w in realized_sectors.items():
                if sec_w > self.constraints.max_sector_pct + self.constraints.tolerance_pct:
                    overall_passed = False
                    results.append({
                        "rule_code": "POST_ROUNDING_SECTOR_CAP",
                        "result_status": "fail",
                        "severity": "critical",
                        "actual_value": round(sec_w, 2),
                        "threshold_value": self.constraints.max_sector_pct,
                        "result_message": (
                            f"Realized sector weight for '{sec_name}' ({sec_w:.2f}%) "
                            f"exceeds safety limit of {self.constraints.max_sector_pct}%"
                        ),
                        "details": {},
                    })

            # Verify unallocated cash reserve is non-negative and budget is preserved
            unallocated_cash = inv_amt_float - realized_total
            if unallocated_cash < -0.01:
                overall_passed = False
                results.append({
                    "rule_code": "BUDGET_OVERRUN_PROTECTION",
                    "result_status": "fail",
                    "severity": "critical",
                    "actual_value": round(unallocated_cash, 2),
                    "threshold_value": 0.0,
                    "result_message": f"Realized share purchase exceeded investment budget by ₹{abs(unallocated_cash):.2f}",
                    "details": {},
                })
            elif realized_total > 0:
                results.append({
                    "rule_code": "POST_ROUNDING_BUDGET_VERIFIED",
                    "result_status": "pass",
                    "severity": "info",
                    "actual_value": round(unallocated_cash, 2),
                    "threshold_value": 0.0,
                    "result_message": f"Whole-share integer allotment verified with ₹{unallocated_cash:.2f} unallocated cash preserved",
                    "details": {},
                })

        # Determine overall status
        if not overall_passed:
            status = "failed"
        elif has_warnings:
            status = "passed_with_warnings"
        else:
            status = "passed"

        total_weight = sum(a.get("target_weight_pct", 0.0) for a in allocations)
        summary = {
            "all_passed": overall_passed,
            "total_weight_pct": round(total_weight, 4),
            "instruments_count": len(allocations),
            "rules_evaluated": len(results),
            "rules_failed": sum(1 for r in results if r["result_status"] == "fail"),
            "rules_passed": sum(1 for r in results if r["result_status"] == "pass"),
        }

        return {
            "validation_status": status,
            "rule_set_version": self.RULE_SET_VERSION,
            "calculation_engine_version": self.CALCULATION_ENGINE_VERSION,
            "summary": summary,
            "results": results,
            "all_passed": overall_passed,
        }
