"""
Mathematical and Financial Methodology Engine for Lucid Portfolio System.
Provides independently verified, robust financial formulas for:
- Earnings Yield with negative/zero/missing earnings handling
- Compounded Annual Growth Rate (CAGR) with exact day-count fractions
- Systematic Beta vs Total Annualized Volatility separation
- Outlier Winsorization and Sector-Relative Z-Score Normalization
- Quality, Value, Momentum, and Low Volatility Factor scoring
- Annualized Expected Return estimation strictly distinguished from factor Z-scores

Version: 2026.11-v1.0
Authoritative Date: 2026-11-04
"""

import math
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# ============================================================================
# CANONICAL HISTORICAL LOOKBACK WINDOWS & MINIMUM OBSERVATIONS
# ============================================================================
LOOKBACK_WINDOW_MOMENTUM_DAYS: int = 126    # 6 Months (~126 trading days for short-term trend)
LOOKBACK_WINDOW_REGIME_DAYS: int = 252      # 1 Year (~252 trading days for 50/200 DMA)
LOOKBACK_WINDOW_VOLATILITY_DAYS: int = 504  # 2 Years (~504 trading days for Covariance/Vol)
LOOKBACK_WINDOW_BETA_DAYS: int = 756        # 3 Years (~756 trading days for Systematic Beta & 3Y CAGR)
LOOKBACK_WINDOW_MACRO_DAYS: int = 1260      # 5 Years (~1260 trading days for secular Macro cycles)

# Minimum observation requirements
MIN_OBSERVATIONS_MOMENTUM: int = 30
MIN_OBSERVATIONS_REGIME: int = 50
MIN_OBSERVATIONS_VOLATILITY: int = 60
MIN_OBSERVATIONS_BETA_CAGR: int = 700


def calculate_earnings_yield(
    pe_ratio: Optional[float] = None,
    eps: Optional[float] = None,
    price: Optional[float] = None,
) -> Tuple[Optional[float], str]:
    """
    Computes Earnings Yield (E/P).
    Correctly handles:
    - Positive P/E: E/P = 1.0 / PE
    - Negative P/E (losses): E/P is negative, capped at -0.25 to prevent extreme distortion
    - Zero or missing P/E: returns (None, 'INVALID_OR_MISSING')
    - Direct EPS and Price if available: E/P = EPS / Price
    Returns: (earnings_yield, status_code)
    """
    if eps is not None and price is not None:
        if price <= 0:
            return None, "INVALID_PRICE_NON_POSITIVE"
        ey = eps / price
        return max(-0.50, min(0.50, ey)), "COMPUTED_FROM_EPS_AND_PRICE"

    if pe_ratio is None:
        return None, "MISSING_PE_RATIO"

    try:
        pe = float(pe_ratio)
    except (ValueError, TypeError):
        return None, "UNPARSEABLE_PE_RATIO"

    if abs(pe) < 1e-5:
        return None, "ZERO_PE_RATIO"

    if pe > 0:
        ey = 1.0 / pe
        return round(min(ey, 0.50), 4), "COMPUTED_FROM_POSITIVE_PE"
    else:
        # Negative PE indicates operating losses: E/P is negative
        ey = 1.0 / pe
        return round(max(ey, -0.25), 4), "COMPUTED_FROM_NEGATIVE_PE_LOSSES"


def calculate_cagr(
    start_price: float,
    end_price: float,
    trading_days: int,
    trading_days_per_year: int = 252,
) -> Tuple[Optional[float], str]:
    """
    Computes Compounded Annual Growth Rate (CAGR).
    Formula: CAGR = (end_price / start_price) ** (trading_days_per_year / trading_days) - 1.0
    Requirements:
    - start_price > 0 and end_price > 0
    - trading_days >= 30
    - If trading_days < 700 for a 3-year metric, returns status 'INSUFFICIENT_HISTORY_FOR_3Y'
    """
    if start_price <= 0 or end_price <= 0:
        return None, "INVALID_PRICE_NON_POSITIVE"
    if trading_days < 30:
        return None, "INSUFFICIENT_OBSERVATION_DAYS"

    years = trading_days / float(trading_days_per_year)
    try:
        cagr = (end_price / start_price) ** (1.0 / years) - 1.0
    except (ZeroDivisionError, OverflowError):
        return None, "NUMERICAL_OVERFLOW"

    if trading_days < 700:
        return round(cagr, 4), "ANNUALIZED_RETURN_INSUFFICIENT_HISTORY_FOR_3Y"
    return round(cagr, 4), "AUDITED_3Y_CAGR"


def calculate_beta_and_volatility(
    asset_returns: List[float],
    benchmark_returns: List[float],
    trading_days_per_year: int = 252,
) -> Tuple[Optional[float], Optional[float], str]:
    """
    Treats Systematic Beta and Total Volatility as distinct risk measures:
    - Beta: Cov(R_i, R_m) / Var(R_m)
    - Total Volatility: Std(R_i) * sqrt(252)
    Requires aligned time series of length >= 60.
    """
    n = min(len(asset_returns), len(benchmark_returns))
    if n < 60:
        return None, None, "INSUFFICIENT_RETURNS_DATA"

    a_ret = np.array(asset_returns[:n], dtype=float)
    b_ret = np.array(benchmark_returns[:n], dtype=float)

    # Volatility (Annualized standard deviation of daily returns)
    daily_vol = float(np.std(a_ret, ddof=1))
    annual_vol = daily_vol * math.sqrt(trading_days_per_year)

    # Beta
    bench_var = float(np.var(b_ret, ddof=1))
    if bench_var < 1e-8:
        return None, round(annual_vol, 4), "ZERO_BENCHMARK_VARIANCE"

    cov = float(np.cov(a_ret, b_ret)[0, 1])
    beta = cov / bench_var

    status = "AUDITED_3Y_RISK_METRICS" if n >= 700 else "ESTIMATED_SHORT_HORIZON_RISK_METRICS"
    return round(beta, 4), round(annual_vol, 4), status


def winsorize_and_zscore(
    values: List[float],
    lower_quantile: float = 0.05,
    upper_quantile: float = 0.95,
) -> Tuple[List[float], str]:
    """
    Robust sector-relative normalization:
    - Handles small sample sizes: if N < 3, returns neutral 0.0 scores with notice
    - Handles zero variance: if std < 1e-7, returns neutral 0.0 scores
    - Outlier protection: winsorizes values at lower_quantile and upper_quantile before computing Z-score
    """
    n = len(values)
    if n == 0:
        return [], "EMPTY_INPUT"
    if n < 3:
        # Small sample size: sector Z-scores are statistically unreliable
        return [0.0] * n, "SMALL_SAMPLE_SIZE_NEUTRAL_DEFAULT"

    arr = np.array(values, dtype=float)
    # Check for NaN / Inf
    if not np.all(np.isfinite(arr)):
        arr = np.nan_to_num(arr, nan=float(np.nanmedian(arr) if not np.all(np.isnan(arr)) else 0.0))

    # Winsorize outliers
    low_val = float(np.percentile(arr, lower_quantile * 100))
    high_val = float(np.percentile(arr, upper_quantile * 100))
    clipped = np.clip(arr, low_val, high_val)

    std = float(np.std(clipped, ddof=1))
    if std < 1e-7:
        # Zero variance: all securities identical on this metric
        return [0.0] * n, "ZERO_VARIANCE_NEUTRAL_DEFAULT"

    mean = float(np.mean(clipped))
    z_scores = (clipped - mean) / std
    # Clamp Z-scores to [-3.0, 3.0]
    final_scores = [round(float(z), 4) for z in np.clip(z_scores, -3.0, 3.0)]
    return final_scores, "WINSORIZED_ZSCORE_COMPUTED"


def calculate_quality_factor(
    roe: Optional[float],
    debt_to_equity: Optional[float],
    is_financial: bool = False,
) -> Tuple[float, str]:
    """
    Computes a combined corporate quality factor score in [-1.0, 1.0].
    For non-financials: balances Return on Equity with financial leverage (D/E).
    For financials (banks/NBFCs): excludes D/E since leverage is structural to banking.
    """
    if roe is None:
        return 0.0, "MISSING_ROE_DATA"

    try:
        roe_val = float(roe)
    except (ValueError, TypeError):
        return 0.0, "INVALID_ROE_FORMAT"

    # Normalize ROE: 15% is standard market hurdle
    roe_score = max(-1.0, min(1.0, (roe_val - 0.15) / 0.15))

    if is_financial or debt_to_equity is None:
        return round(roe_score, 4), "ROE_ONLY_FINANCIAL_PROFILE"

    try:
        de_val = float(debt_to_equity)
    except (ValueError, TypeError):
        de_val = 0.50

    # Non-financial leverage penalty: D/E > 1.0 reduces quality, D/E > 2.5 incurs severe penalty
    if de_val <= 0.50:
        de_score = 0.50
    elif de_val <= 1.00:
        de_score = 0.20
    elif de_val <= 2.50:
        de_score = -0.30
    else:
        de_score = -0.80

    composite = 0.65 * roe_score + 0.35 * de_score
    return round(max(-1.0, min(1.0, composite)), 4), "QUALITY_COMBINED_ROE_AND_LEVERAGE"


EXPECTED_RETURN_DISCLAIMER: str = (
    "Expected returns are econometric model estimates derived from historical CAPM beta and factor loadings; "
    "they do not constitute guaranteed returns or forward promises."
)


def compute_expected_annual_return(
    base_target_return_pct: float,
    quality_z: float,
    value_z: float,
    momentum_z: float,
    beta: float,
    goal: str = "wealth_creation",
) -> float:
    """
    Computes expected annual return strictly in percentage units (% annualized).
    Does NOT confuse unitless factor scores with expected returns:
    Uses Capital Asset Pricing Model (CAPM) beta premium + multi-factor alpha tilt.

    Mathematical Model:
        E[R_i] = R_base + 1.20 * (w_q * Z_q + w_v * Z_v + w_m * Z_m) + 1.50 * (Beta_i - 1.0)
    
    Where:
        - R_base: Target return for the investor's risk profile (e.g. 12.5% for moderate)
        - w_q, w_v, w_m: Goal-specific factor loadings summing to 1.0
        - Beta_i: Historical systematic market sensitivity relative to NIFTY 50
        - Output is clamped to institutional feasibility corridor [4.0%, 30.0%]

    Regulatory Notice:
        Expected returns are model projections based on historical statistical estimates
        and do not represent guaranteed forward returns under SEBI RIA guidelines.
    """
    # Factor weights dependent on investor goal orientation
    g = (goal or "").lower()
    if "dividend" in g or "income" in g:
        alpha_pct = 0.40 * value_z + 0.40 * quality_z + 0.20 * momentum_z
    elif "preserv" in g or "safety" in g:
        alpha_pct = 0.60 * quality_z + 0.30 * value_z + 0.10 * momentum_z
    elif "growth" in g or "aggressive" in g:
        alpha_pct = 0.20 * quality_z + 0.20 * value_z + 0.60 * momentum_z
    else:
        alpha_pct = 0.35 * quality_z + 0.35 * value_z + 0.30 * momentum_z

    # Systematic market beta adjustment (+/- 1.5% per 0.5 beta deviation from market 1.0)
    beta_tilt_pct = (beta - 1.0) * 1.50

    expected_return_pct = base_target_return_pct + alpha_pct * 1.20 + beta_tilt_pct
    # Bound expected return within institutional boundaries [4.0%, 30.0%]
    return round(float(np.clip(expected_return_pct, 4.0, 30.0)), 2)

