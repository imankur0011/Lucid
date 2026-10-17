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
