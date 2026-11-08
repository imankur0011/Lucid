"""
Deterministic Portfolio Allocation Optimizer.
Uses scipy.optimize (SLSQP) to find risk-adjusted weights subject to hard individual and sector constraints.
Integrates with centralized policy configurations and guarantees that all fallback solutions
strictly satisfy both single-stock and sector exposure ceilings, returning explicit infeasibility otherwise.

Version: 2026.11-v1.0
Authoritative Date: 2026-11-04
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from scipy.optimize import minimize

try:
    from backend.portfolio_engine.constraints import PortfolioConstraints
    from backend.portfolio_engine.factors import get_equity_factors
    from backend.portfolio_engine.policy import get_risk_profile_policy, POLICY_RULES, RISK_PROFILE_POLICIES
except ImportError:
    from portfolio_engine.constraints import PortfolioConstraints
    from portfolio_engine.factors import get_equity_factors
    from portfolio_engine.policy import get_risk_profile_policy, POLICY_RULES, RISK_PROFILE_POLICIES


RISK_CATEGORY_BENCHMARKS = {
    cat: {
        "target_return": b.target_return_pct,
        "max_stock_pct": b.max_single_stock_pct,
        "max_sector_pct": b.max_sector_pct,
        "risk_aversion": b.risk_aversion,
    }
    for cat, b in RISK_PROFILE_POLICIES.items()
}


def _sector_constrained_fallback(
    candidates: List[Dict[str, Any]],
    max_stock_frac: float,
    max_sector_frac: float,
) -> Tuple[bool, np.ndarray]:
    """
    Deterministically computes an equal/balanced allocation that strictly satisfies
    BOTH individual stock bounds (w_i <= max_stock_frac) AND sector limits (sum(w_s) <= max_sector_frac).
    Returns: (is_feasible, weights_array)
    """
    n = len(candidates)
    if n == 0:
        return False, np.array([])

    sectors: Dict[str, List[int]] = {}
    for idx, c in enumerate(candidates):
        sec = c.get("sector_name") or "General"
        sectors.setdefault(sec, []).append(idx)

    # Check minimum sector diversity: if 1 / len(sectors) > max_sector_frac, impossible
    if len(sectors) < int(np.ceil(1.0 / max_sector_frac)):
        return False, np.zeros(n)

    weights = np.zeros(n, dtype=float)
    remaining_sum = 1.0
    sector_sums = {sec: 0.0 for sec in sectors}

    # Iterative water-filling with sector caps
    rounds = 0
    while remaining_sum > 1e-6 and rounds < 100:
        rounds += 1
        # Find candidates whose stock weight < max_stock_frac and whose sector < max_sector_frac
        eligible_indices = []
        for idx, c in enumerate(candidates):
            sec = c.get("sector_name") or "General"
            if weights[idx] < (max_stock_frac - 1e-6) and sector_sums[sec] < (max_sector_frac - 1e-6):
                eligible_indices.append(idx)

        if not eligible_indices:
            # Cannot allocate remaining weight without violating a cap
            break

        delta_per_stock = remaining_sum / float(len(eligible_indices))
        # Clamp delta so no stock or sector exceeds limit
        max_possible_delta = delta_per_stock
        for idx in eligible_indices:
            sec = candidates[idx].get("sector_name") or "General"
            stock_room = max_stock_frac - weights[idx]
            sector_room = max_sector_frac - sector_sums[sec]
            max_possible_delta = min(max_possible_delta, stock_room, sector_room)

        if max_possible_delta < 1e-7:
            break

        for idx in eligible_indices:
            sec = candidates[idx].get("sector_name") or "General"
            weights[idx] += max_possible_delta
            sector_sums[sec] += max_possible_delta
            remaining_sum -= max_possible_delta

    if abs(remaining_sum) > 1e-4:
        return False, np.zeros(n)

    return True, weights


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
    """
    if not candidates:
        return False, [], "No eligible candidate securities available for optimization"

    profile_policy = get_risk_profile_policy(risk_category)
    c = constraints or PortfolioConstraints()
    n = len(candidates)
    if n < c.min_stocks_count:
        return False, [], f"Insufficient candidates ({n}) to satisfy minimum count of {c.min_stocks_count}"

    # Precedence rule: most restrictive cap wins, bounded by mathematical feasibility
    min_feasible_cap = 100.0 / n if n > 0 else 100.0
    effective_cap = max(profile_policy.max_single_stock_pct, min_feasible_cap)
    max_stock_pct = min(c.max_single_stock_pct, effective_cap)
    max_stock_frac = max_stock_pct / 100.0
    num_sectors = len(set(cand.get("sector_name") or "General" for cand in candidates))
    min_feasible_sector = 100.0 / num_sectors if num_sectors > 0 else 35.0
    effective_sector = max(profile_policy.max_sector_pct, min_feasible_sector)
    max_sector_pct = min(c.max_sector_pct, effective_sector)
    max_sector_frac = max_sector_pct / 100.0

    returns_pct_list = []
    volatilities_pct_list = []
    sectors_list = []

    for cand in candidates:
        sym = cand.get("symbol", "")
        factors = cand.get("fundamental_factors") or get_equity_factors(sym)
        alpha = float(cand.get("alpha_score", 0.5))
        beta = float(factors.get("beta", 1.0))
        sec = cand.get("sector_name") or "General"
        sectors_list.append(sec)

        exp_ret = profile_policy.target_return_pct + (alpha - 0.5) * 6.0 + (beta - 1.0) * 1.5
        returns_pct_list.append(exp_ret)

        vol = max(9.0, min(10.0 + beta * 4.0, 22.0))
        volatilities_pct_list.append(vol)

    returns_pct = np.array(returns_pct_list)
    returns_dec = returns_pct / 100.0

    volatilities_pct = np.array(volatilities_pct_list)
    volatilities_dec = volatilities_pct / 100.0

    corr = np.full((n, n), 0.20)
    for i in range(n):
        for j in range(n):
            if i != j and sectors_list[i] == sectors_list[j]:
                corr[i, j] = 0.50
    np.fill_diagonal(corr, 1.0)

    cov_dec = np.outer(volatilities_dec, volatilities_dec) * corr
    cov_dec += np.eye(n) * 1e-6

    risk_aversion = profile_policy.risk_aversion

    def objective(w_frac):
        port_return = float(np.dot(w_frac, returns_dec))
        port_var = float(np.dot(w_frac.T, np.dot(cov_dec, w_frac)))
        return 0.5 * risk_aversion * port_var - port_return

    w0 = np.full(n, 1.0 / n)
    bounds = [(0.0, max_stock_frac) for _ in range(n)]

    scipy_constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0}
    ]

    sectors: Dict[str, List[int]] = {}
    for idx, cand in enumerate(candidates):
        sec = cand.get("sector_name") or "General"
        sectors.setdefault(sec, []).append(idx)

    for sec_name, indices in sectors.items():
        scipy_constraints.append({
            "type": "ineq",
            "fun": lambda w, idxs=indices: max_sector_frac - np.sum(w[idxs]),
        })

    res = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=scipy_constraints,
        options={"maxiter": 250, "ftol": 1e-7},
    )

    if res.success and np.all(res.x >= -1e-6) and np.all(res.x <= (max_stock_frac + 1e-4)):
        w_res_frac = res.x
        convergence_mode = "SLSQP_OPTIMAL_CONVERGED"
    else:
        # Constrained Fallback: Run sector-constrained water-filling
        fallback_ok, fallback_weights = _sector_constrained_fallback(candidates, max_stock_frac, max_sector_frac)
        if not fallback_ok:
            return False, [], f"Optimization infeasible: constraints (max_stock={max_stock_pct}%, max_sector={max_sector_pct}%) cannot be satisfied with provided candidates."
        w_res_frac = fallback_weights
        convergence_mode = "SECTOR_CONSTRAINED_FALLBACK"

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

    # Iterative projection onto simplex with bounds [0.0, max_stock_pct] and sector caps
    weights = np.array([a["target_weight_pct"] for a in filtered_allocations], dtype=float)
    cap = float(max_stock_pct)
    sector_cap = float(max_sector_pct)
    target_sum = 100.0

    sec_names = [a.get("sector_name") or "General" for a in filtered_allocations]
    unique_secs = list(set(sec_names))

    for _ in range(100):
        weights = np.clip(weights, 0.0, cap)
        # Enforce sector caps iteratively
        for s in unique_secs:
            s_mask = np.array([name == s for name in sec_names], dtype=bool)
            s_sum = float(np.sum(weights[s_mask]))
            if s_sum > sector_cap:
                weights[s_mask] *= (sector_cap / s_sum)

        current_sum = float(np.sum(weights))
        deficit = target_sum - current_sum
        if abs(deficit) < 1e-7:
            break
        if deficit > 0:
            free_mask = np.zeros(len(weights), dtype=bool)
            for idx in range(len(weights)):
                s = sec_names[idx]
                s_mask = np.array([name == s for name in sec_names], dtype=bool)
                s_sum = float(np.sum(weights[s_mask]))
                if weights[idx] < (cap - 1e-4) and s_sum < (sector_cap - 1e-4):
                    free_mask[idx] = True
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
            placed = False
            for i in range(len(rounded)):
                s = sec_names[i]
                s_sum = sum(rounded[j] for j, name in enumerate(sec_names) if name == s)
                if (rounded[i] + diff <= cap + 1e-6) and (s_sum + diff <= sector_cap + 1e-6):
                    rounded[i] = round(rounded[i] + diff, 4)
                    placed = True
                    break
            if not placed:
                best_i = min(range(len(rounded)), key=lambda i: sum(rounded[j] for j, name in enumerate(sec_names) if name == sec_names[i]))
                rounded[best_i] = round(rounded[best_i] + diff, 4)
        else:
            for i in range(len(rounded)):
                if rounded[i] + diff >= 0.0:
                    rounded[i] = round(rounded[i] + diff, 4)
                    break

    for idx, a in enumerate(filtered_allocations):
        a["target_weight_pct"] = float(rounded[idx])
        a["optimization_provenance"] = convergence_mode

    # Final post-optimization validation
    sector_sums_final: Dict[str, float] = {}
    for a in filtered_allocations:
        s = a.get("sector_name") or "General"
        sector_sums_final[s] = sector_sums_final.get(s, 0.0) + a["target_weight_pct"]
        if a["target_weight_pct"] > (max_stock_pct + 0.15):
            return False, [], f"Post-optimization check failed: {a.get('symbol')} weight {a['target_weight_pct']}% exceeds cap of {max_stock_pct}%"

    for s_name, s_sum in sector_sums_final.items():
        if s_sum > (max_sector_pct + 0.25):
            return False, [], f"Post-optimization check failed: sector {s_name} weight {s_sum:.2f}% exceeds sector cap of {max_sector_pct}%"

    return True, filtered_allocations, f"Optimization succeeded via {convergence_mode}"
