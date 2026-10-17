"""
Portfolio Constraints Management.
Defines and checks mathematical constraints (single-stock max, sector limits, weight sums, exclusions).
"""

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class PortfolioConstraints:
    max_single_stock_pct: float = 25.0
    min_single_stock_pct: float = 5.0
    max_sector_pct: float = 40.0
    min_stocks_count: int = 3
    max_stocks_count: int = 15
    target_sum_pct: float = 100.0
    tolerance_pct: float = 0.01  # tolerance for floating point sum


def check_allocation_constraints(
    allocations: List[Dict[str, Any]],
    constraints: PortfolioConstraints,
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validates a proposed allocation list against hard mathematical constraints.
    Returns: (all_passed, list_of_check_results)
    """
    results = []
    all_passed = True

    if not allocations:
        return False, [{
            "rule_code": "EMPTY_ALLOCATION",
            "passed": False,
            "severity": "critical",
            "message": "Allocation list is empty",
        }]

    # 1. Total Weight Sum Check: sum(w_i) == 100.0%
    total_weight = sum(a.get("target_weight_pct", 0.0) for a in allocations)
    diff = abs(total_weight - constraints.target_sum_pct)
    sum_passed = diff <= constraints.tolerance_pct
    results.append({
        "rule_code": "SUM_TO_100",
        "passed": sum_passed,
        "severity": "critical",
        "actual_value": round(total_weight, 4),
        "threshold_value": constraints.target_sum_pct,
        "message": f"Target weights sum to {total_weight:.4f}% (expected {constraints.target_sum_pct}%)",
    })
    if not sum_passed:
        all_passed = False

    # 2. Non-negative weights check
    for a in allocations:
        w = a.get("target_weight_pct", 0.0)
        sym = a.get("symbol", "UNKNOWN")
        if w < 0:
            all_passed = False
            results.append({
                "rule_code": "NON_NEGATIVE_WEIGHTS",
                "passed": False,
                "severity": "critical",
                "actual_value": w,
                "threshold_value": 0.0,
                "message": f"Security {sym} has negative allocation weight ({w}%)",
            })

    # 3. Maximum single-stock exposure check
    for a in allocations:
        w = a.get("target_weight_pct", 0.0)
        sym = a.get("symbol", "UNKNOWN")
        if w > constraints.max_single_stock_pct + constraints.tolerance_pct:
            all_passed = False
            results.append({
                "rule_code": "MAX_SINGLE_STOCK_EXPOSURE",
                "passed": False,
                "severity": "high",
                "actual_value": round(w, 4),
                "threshold_value": constraints.max_single_stock_pct,
                "message": f"Security {sym} weight ({w:.2f}%) exceeds maximum limit of {constraints.max_single_stock_pct}%",
            })

    # 4. Sector Exposure Check
    sector_weights: Dict[str, float] = {}
    for a in allocations:
        sec = a.get("sector_name") or "General"
        w = a.get("target_weight_pct", 0.0)
        sector_weights[sec] = sector_weights.get(sec, 0.0) + w

    for sec_name, sec_weight in sector_weights.items():
        if sec_weight > constraints.max_sector_pct + constraints.tolerance_pct:
            all_passed = False
            results.append({
                "rule_code": "MAX_SECTOR_EXPOSURE",
                "passed": False,
                "severity": "high",
                "actual_value": round(sec_weight, 4),
                "threshold_value": constraints.max_sector_pct,
                "message": f"Sector '{sec_name}' exposure ({sec_weight:.2f}%) exceeds limit of {constraints.max_sector_pct}%",
            })
        else:
            results.append({
                "rule_code": f"SECTOR_LIMIT_{sec_name.upper().replace(' ', '_')}",
                "passed": True,
                "severity": "info",
                "actual_value": round(sec_weight, 4),
                "threshold_value": constraints.max_sector_pct,
                "message": f"Sector '{sec_name}' exposure ({sec_weight:.2f}%) within limit",
            })

    # 5. Diversification count check
    stock_count = len(allocations)
    if stock_count < constraints.min_stocks_count:
        all_passed = False
        results.append({
            "rule_code": "MIN_INSTRUMENT_COUNT",
            "passed": False,
            "severity": "high",
            "actual_value": float(stock_count),
            "threshold_value": float(constraints.min_stocks_count),
            "message": f"Portfolio contains only {stock_count} instruments (minimum required is {constraints.min_stocks_count})",
        })
    else:
        results.append({
            "rule_code": "INSTRUMENT_COUNT_SATISFIED",
            "passed": True,
            "severity": "info",
            "actual_value": float(stock_count),
            "threshold_value": float(constraints.min_stocks_count),
            "message": f"Portfolio contains {stock_count} instruments, meeting diversification minimum",
        })

    return all_passed, results
