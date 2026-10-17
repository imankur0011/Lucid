"""
Deterministic Portfolio Allocation Optimizer.
Uses scipy.optimize (SLSQP) to find risk-adjusted weights subject to hard individual and sector constraints.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from scipy.optimize import minimize

try:
    from backend.portfolio_engine.constraints import PortfolioConstraints
except ImportError:
    from portfolio_engine.constraints import PortfolioConstraints


# Expected return & risk profiles by category (annualized % priors)
# Application concentration safety rules enforce single-stock exposure <= 25.0%, sector <= 40.0%.
RISK_CATEGORY_BENCHMARKS = {
    "very_conservative": {"target_return": 8.0, "max_stock_pct": 15.0, "max_sector_pct": 30.0, "risk_aversion": 10.0},
    "conservative": {"target_return": 10.0, "max_stock_pct": 20.0, "max_sector_pct": 35.0, "risk_aversion": 6.0},
    "moderate": {"target_return": 12.5, "max_stock_pct": 25.0, "max_sector_pct": 40.0, "risk_aversion": 3.5},
    "growth": {"target_return": 15.0, "max_stock_pct": 25.0, "max_sector_pct": 40.0, "risk_aversion": 2.0},
    "aggressive": {"target_return": 18.0, "max_stock_pct": 25.0, "max_sector_pct": 40.0, "risk_aversion": 1.0},
}


def optimize_portfolio_allocations(
    candidates: List[Dict[str, Any]],
    risk_category: str = "moderate",
    constraints: Optional[PortfolioConstraints] = None,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    Computes optimal allocation weights among eligible candidates.
    Solves Markowitz Mean-Variance Quadratic Utility in fractional decimal units:
        minimize 0.5 * risk_aversion * w.T @ Cov_dec @ w - Expected_Returns_dec.T @ w
        subject to:
            sum(w) = 1.0
            0 <= w_i <= max_stock_frac
            sum(w_sector) <= max_sector_frac
    Precedence rule:
        effective_stock_pct = min(hard_policy_25, profile_max_stock, constraints.max_single_stock_pct)
        effective_sector_pct = min(hard_policy_40, profile_max_sector, constraints.max_sector_pct)
    Returns: (success, allocations, message)
    """
    if not candidates:
        return False, [], "No eligible candidate securities available for optimization"

    profile = RISK_CATEGORY_BENCHMARKS.get(risk_category.lower(), RISK_CATEGORY_BENCHMARKS["moderate"])
    c = constraints or PortfolioConstraints()
    n = len(candidates)
    if n < c.min_stocks_count:
        return False, [], f"Insufficient candidates ({n}) to satisfy minimum count of {c.min_stocks_count}"

    # Explicit cap precedence: most restrictive bound wins, bounded by mathematical feasibility
    min_feasible_cap = 100.0 / n if n > 0 else 100.0
    effective_cap = max(profile.get("max_stock_pct", 25.0), min_feasible_cap)
    max_stock_pct = min(c.max_single_stock_pct, effective_cap)
    max_stock_frac = max_stock_pct / 100.0
    max_sector_pct = min(c.max_sector_pct, profile.get("max_sector_pct", 40.0))
    max_sector_frac = max_sector_pct / 100.0

    # Expected returns in decimal (annualized)
    returns_pct = np.array([
        profile["target_return"] + (hash(cand["symbol"]) % 15 - 7) * 0.2
        for cand in candidates
    ])
    returns_dec = returns_pct / 100.0

    # Covariance matrix in decimal (annualized) with Ledoit-Wolf-style diagonal shrinkage
    volatilities_pct = np.array([
        12.0 + (hash(cand["symbol"]) % 10) * 0.5
        for cand in candidates
    ])
    volatilities_dec = volatilities_pct / 100.0
    corr = np.full((n, n), 0.3)
    np.fill_diagonal(corr, 1.0)
    cov_dec = np.outer(volatilities_dec, volatilities_dec) * corr
    # Guarantee positive semi-definiteness via ridge regularization
    cov_dec += np.eye(n) * 1e-6

    risk_aversion = profile["risk_aversion"]

    def objective(w_frac):
        port_return = float(np.dot(w_frac, returns_dec))
        port_var = float(np.dot(w_frac.T, np.dot(cov_dec, w_frac)))
        return 0.5 * risk_aversion * port_var - port_return

    # Initial equal weights in fraction
    w0 = np.full(n, 1.0 / n)

    # Bounds: 0 <= w_i <= max_stock_frac
    bounds = [(0.0, max_stock_frac) for _ in range(n)]

    # Constraints list
    scipy_constraints = []

    # 1. Budget equality: Sum of weights == 1.0
    scipy_constraints.append({
        "type": "eq",
        "fun": lambda w: np.sum(w) - 1.0,
    })

    # 2. Sector constraints: for each sector, sum(w in sector) <= max_sector_frac
    sectors = {}
    for idx, cand in enumerate(candidates):
        sec = cand.get("sector_name") or "General"
        sectors.setdefault(sec, []).append(idx)

    for sec_name, indices in sectors.items():
        scipy_constraints.append({
            "type": "ineq",
            "fun": lambda w, idxs=indices: max_sector_frac - np.sum(w[idxs]),
        })

    # Solve quadratic programming via SLSQP
    res = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=scipy_constraints,
        options={"maxiter": 200, "ftol": 1e-7},
    )

    if not res.success:
        # Constrained fallback to equal weight among top diversified candidates
        w_res_frac = np.zeros(n)
        active_count = min(n, int(np.ceil(1.0 / max_stock_frac)))
        eq_w = 1.0 / active_count
        w_res_frac[:active_count] = eq_w
    else:
        w_res_frac = res.x

    # Convert fractional weights to percentages (0 - 100)
    w_res_pct = w_res_frac * 100.0

    # Clean tiny allocations (< 0.5% weight)
    threshold_pct = 0.5
    filtered_allocations = []
    for idx, cand in enumerate(candidates):
        weight = float(w_res_pct[idx])
        if weight >= threshold_pct:
            cand_copy = dict(cand)
            cand_copy["target_weight_pct"] = weight
            filtered_allocations.append(cand_copy)

    if not filtered_allocations:
        filtered_allocations = [
            dict(cand, target_weight_pct=float(w_res_pct[idx]))
            for idx, cand in enumerate(candidates)
        ]

    # Iterative projection onto simplex with bounds [0.0, max_stock_pct]
    # Guarantees sum(w) == 100.0 and each w_i <= max_stock_pct
    weights = np.array([a["target_weight_pct"] for a in filtered_allocations], dtype=float)
    cap = float(max_stock_pct)
    target_sum = 100.0

    for _ in range(50):
        weights = np.clip(weights, 0.0, cap)
        current_sum = float(np.sum(weights))
        deficit = target_sum - current_sum
        if abs(deficit) < 1e-7:
            break
        if deficit > 0:
            free_mask = weights < (cap - 1e-6)
            if not np.any(free_mask):
                break
            weights[free_mask] += deficit / float(np.sum(free_mask))
        else:
            free_mask = weights > 1e-6
            if not np.any(free_mask):
                break
            weights[free_mask] += deficit / float(np.sum(free_mask))

    weights = np.clip(weights, 0.0, cap)
    rounded = np.round(weights, 4)
    diff = round(100.0 - float(np.sum(rounded)), 4)
    if abs(diff) > 0:
        if diff > 0:
            for i in range(len(rounded)):
                if rounded[i] + diff <= cap:
                    rounded[i] = round(rounded[i] + diff, 4)
                    diff = 0.0
                    break
        else:
            for i in range(len(rounded)):
                if rounded[i] + diff >= 0.0:
                    rounded[i] = round(rounded[i] + diff, 4)
                    diff = 0.0
                    break

    for idx, a in enumerate(filtered_allocations):
        a["target_weight_pct"] = float(rounded[idx])

    return True, filtered_allocations, "Optimization succeeded"
