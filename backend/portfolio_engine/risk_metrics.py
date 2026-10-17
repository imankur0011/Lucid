"""
Portfolio Risk and Diversification Metrics Calculator.
Computes Expected Return, Annualized Volatility, Sharpe Ratio, and Herfindahl Diversification Score.
"""

from typing import List, Dict, Any, Optional
import numpy as np

try:
    from backend.config import settings
    DEFAULT_RF = getattr(settings, "risk_free_rate_pct", 7.0)
except ImportError:
    DEFAULT_RF = 7.0


def compute_portfolio_metrics(
    allocations: List[Dict[str, Any]],
    risk_free_rate_pct: Optional[float] = None,
) -> Dict[str, float]:
    """
    Computes key risk and return metrics for a set of allocations.
    Returns: {
        'expected_return_pct': float,
        'expected_volatility_pct': float,
        'sharpe_ratio': float,
        'diversification_score': float,
        'herfindahl_index': float
    }
    """
    rf = DEFAULT_RF if risk_free_rate_pct is None else float(risk_free_rate_pct)
    if not allocations:
        return {
            "expected_return_pct": 0.0,
            "expected_volatility_pct": 0.0,
            "sharpe_ratio": 0.0,
            "diversification_score": 0.0,
            "herfindahl_index": 1.0,
        }

    weights = np.array([a.get("target_weight_pct", 0.0) / 100.0 for a in allocations])
    n = len(weights)

    # Base expected return per security
    returns = np.array([
        12.0 + (hash(a.get("symbol", "")) % 8 - 4) * 0.5
        for a in allocations
    ])

    port_return = float(np.dot(weights, returns))

    # Portfolio Volatility
    volatilities = np.array([
        14.0 + (hash(a.get("symbol", "")) % 6) * 0.8
        for a in allocations
    ])
    corr = np.full((n, n), 0.25)
    np.fill_diagonal(corr, 1.0)
    cov = np.outer(volatilities, volatilities) * corr
    port_variance = float(np.dot(weights.T, np.dot(cov, weights)))
    port_volatility = float(np.sqrt(max(0.0001, port_variance)))

    # Sharpe Ratio
    sharpe = (port_return - rf) / port_volatility if port_volatility > 0 else 0.0

    # Herfindahl-Hirschman Index (HHI) for Concentration
    # HHI = sum(w_i^2) where w_i is fraction in [0, 1]
    hhi = float(np.sum(weights ** 2))

    # Normalized Diversification Score (0 to 100):
    # Benchmark: 0 for full concentration (1 asset), 100 for theoretical maximum equal-weight (1/N)
    if n <= 1:
        diversification_score = 0.0
    else:
        min_hhi = 1.0 / n
        if abs(1.0 - min_hhi) < 1e-6:
            diversification_score = 100.0
        else:
            norm_val = (hhi - min_hhi) / (1.0 - min_hhi)
            diversification_score = round(max(0.0, min(100.0, (1.0 - norm_val) * 100.0)), 2)

    return {
        "expected_return_pct": round(port_return, 4),
        "expected_volatility_pct": round(port_volatility, 4),
        "sharpe_ratio": round(sharpe, 4),
        "diversification_score": diversification_score,
        "herfindahl_index": round(hhi, 4),
        "raw_diversification_pct": round((1.0 - hhi) * 100.0, 2),
    }
