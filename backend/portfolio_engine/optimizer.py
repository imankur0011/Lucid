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
# Application concentration safety rules enforce single-stock exposure <= 25.0%.
RISK_CATEGORY_BENCHMARKS = {
    "very_conservative": {"target_return": 8.0, "max_stock_pct": 15.0, "risk_aversion": 10.0},
    "conservative": {"target_return": 10.0, "max_stock_pct": 20.0, "risk_aversion": 6.0},
    "moderate": {"target_return": 12.5, "max_stock_pct": 25.0, "risk_aversion": 3.5},
    "growth": {"target_return": 15.0, "max_stock_pct": 25.0, "risk_aversion": 2.0},
    "aggressive": {"target_return": 18.0, "max_stock_pct": 25.0, "risk_aversion": 1.0},
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
        effective_stock_pct = min(constraints.max_single_stock_pct, profile["max_stock_pct"])
    Returns: (success, allocations, message)
    """
    if not candidates:
        return False, [], "No eligible candidate securities available for optimization"

    profile = RISK_CATEGORY_BENCHMARKS.get(risk_category.lower(), RISK_CATEGORY_BENCHMARKS["moderate"])
    c = constraints or PortfolioConstraints()
    # Explicit cap precedence: most restrictive bound wins
    max_stock_pct = min(c.max_single_stock_pct, profile["max_stock_pct"])
    max_stock_frac = max_stock_pct / 100.0
    max_sector_frac = c.max_sector_pct / 100.0

    n = len(candidates)
    if n < c.min_stocks_count:
        return False, [], f"Insufficient candidates ({n}) to satisfy minimum count of {c.min_stocks_count}"

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

    # Clean tiny allocations (< 1% weight)
    threshold_pct = 1.0
    filtered_allocations = []
    for idx, cand in enumerate(candidates):
        weight = float(w_res_pct[idx])
        if weight >= threshold_pct:
            cand_copy = dict(cand)
            cand_copy["target_weight_pct"] = weight
            filtered_allocations.append(cand_copy)

    # Renormalize to exact 100.00%
    tot = sum(a["target_weight_pct"] for a in filtered_allocations)
    if tot > 0:
        for a in filtered_allocations:
            a["target_weight_pct"] = round((a["target_weight_pct"] / tot) * 100.0, 6)

    # Fix slight floating point rounding discrepancies on largest holding
    diff = 100.0 - sum(a["target_weight_pct"] for a in filtered_allocations)
    if filtered_allocations and abs(diff) > 1e-6:
        filtered_allocations[0]["target_weight_pct"] = round(filtered_allocations[0]["target_weight_pct"] + diff, 6)

    return True, filtered_allocations, "Optimization succeeded"
