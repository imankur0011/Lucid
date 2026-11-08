"""
Centralized Policy and Configuration System for Lucid Portfolio Engine.
Authoritative, versioned repository of regulatory guidelines, fiduciary thresholds,
and mathematical constraints across all AI agents and deterministic engines.

Version: 2026.11-v1.0
Effective Date: 2026-11-04
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class RuleCategory(str, Enum):
    HARD_CONSTRAINT = "HARD_CONSTRAINT"               # Blocks generation / fails validation if violated
    CRITIC_FIDUCIARY_DEFECT = "CRITIC_FIDUCIARY_DEFECT" # Requires candidate replacement or bounded rework
    SOFT_DISCLOSURE_WARNING = "SOFT_DISCLOSURE_WARNING" # Informational disclosure presented to investor
    EMPIRICAL_SELECTION_CRITERIA = "EMPIRICAL_SELECTION_CRITERIA" # Multi-factor scoring weights


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    name: str
    category: RuleCategory
    threshold: Any
    unit: str
    regulatory_basis: str
    rationale: str
    effective_version: str = "2026.11-v1.0"


# ==============================================================================
# AUTHORITATIVE VERSIONED POLICIES
# ==============================================================================

# Centralized default thresholds for Lucid internal risk policies.
# Note: These values represent Lucid's internal risk management and fiduciary diversification
# policies. They are inspired by institutional standards and SEBI Regulation 17 suitability principles,
# but are NOT statutory universal SEBI mandates for retail client portfolios.
DEFAULT_MAX_SINGLE_STOCK_PCT: float = 25.0   # Configurable Lucid internal single-stock ceiling
DEFAULT_MAX_SECTOR_PCT: float = 40.0         # Configurable Lucid internal sector concentration cap
DEFAULT_MIN_HOLDINGS_COUNT: int = 3          # Minimum holdings breadth
DEFAULT_DRIFT_THRESHOLD_STOCK_PCT: float = 5.0     # Stock rebalancing drift threshold
DEFAULT_DRIFT_THRESHOLD_SECTOR_PCT: float = 10.0   # Sector rebalancing drift threshold

POLICY_RULES: Dict[str, PolicyRule] = {
    # 1. HARD CONSTRAINTS (Deterministic Non-Negotiable Ceilings)
    "POL-ALLOC-01": PolicyRule(
        rule_id="POL-ALLOC-01",
        name="Maximum Single-Stock Allocation Ceiling",
        category=RuleCategory.HARD_CONSTRAINT,
        threshold=DEFAULT_MAX_SINGLE_STOCK_PCT,
        unit="percent",
        regulatory_basis="Lucid Internal Fiduciary Risk Policy (Aligned with SEBI IA Reg 17 Suitability Principles)",
        rationale="Prevents idiosyncratic single-company ruin in retail investment accounts. No single stock can exceed 25.0% of portfolio capital.",
    ),
    "POL-SECT-01": PolicyRule(
        rule_id="POL-SECT-01",
        name="Maximum Sector Exposure Ceiling",
        category=RuleCategory.HARD_CONSTRAINT,
        threshold=DEFAULT_MAX_SECTOR_PCT,
        unit="percent",
        regulatory_basis="Lucid Internal Fiduciary Risk Policy (Sector Risk Containment)",
        rationale="Limits concentration risk in any single economic sector. Aggregate exposure to any sector must not exceed 40.0%.",
    ),
    "POL-SUM-01": PolicyRule(
        rule_id="POL-SUM-01",
        name="Exact Portfolio Full-Investment Sum",
        category=RuleCategory.HARD_CONSTRAINT,
        threshold=100.0,
        unit="percent",
        regulatory_basis="Markowitz Mean-Variance Budget Feasibility Criterion",
        rationale="Target portfolio weights must sum exactly to 100.0% within a 0.01% floating-point tolerance.",
    ),
    "POL-BUDGET-01": PolicyRule(
        rule_id="POL-BUDGET-01",
        name="Zero-Deficit Cash Residual Invariant",
        category=RuleCategory.HARD_CONSTRAINT,
        threshold=0.0,
        unit="INR",
        regulatory_basis="NSE/BSE Retail Cash Market Non-Leverage Rules",
        rationale="Post-rounding cash residual must be >= 0. Integer lot execution cannot exceed total allocated capital or demand leverage.",
    ),
    "POL-MINCAP-01": PolicyRule(
        rule_id="POL-MINCAP-01",
        name="Minimum Investable Portfolio Capital",
        category=RuleCategory.HARD_CONSTRAINT,
        threshold=1000.0,
        unit="INR",
        regulatory_basis="SEBI Investment Advisers Regulations, 2013, Regulation 17 (Suitability)",
        rationale="Minimum capital required to construct a diversified multi-stock basket with integer lot sizing without prohibitive cash drag.",
    ),

    # 2. CRITIC FIDUCIARY DEFECTS (Requires Candidate Replacement / Bounded Rework)
    "POL-LEVERAGE-01": PolicyRule(
        rule_id="POL-LEVERAGE-01",
        name="Non-Financial Corporate Leverage Ceiling",
        category=RuleCategory.CRITIC_FIDUCIARY_DEFECT,
        threshold=2.50,
        unit="ratio (D/E)",
        regulatory_basis="Companies Act 2013, Section 186 & Institutional Credit Appraisal Standards",
        rationale="Non-financial manufacturing/industrial companies with D/E > 2.50 carry elevated default vulnerability during interest-rate tightening. Excludes banks/NBFCs where leverage is structural.",
    ),
    "POL-ROE-01": PolicyRule(
        rule_id="POL-ROE-01",
        name="Minimum Corporate Profitability Quality",
        category=RuleCategory.CRITIC_FIDUCIARY_DEFECT,
        threshold=0.0,
        unit="percent",
        regulatory_basis="Fundamental Equity Quality Factor Standards",
        rationale="Companies reporting negative Return on Equity (ROE < 0%) indicate persistent operating losses or capital erosion.",
    ),
    "POL-DIVBREADTH-01": PolicyRule(
        rule_id="POL-DIVBREADTH-01",
        name="Minimum Candidate Breadth",
        category=RuleCategory.CRITIC_FIDUCIARY_DEFECT,
        threshold=3,
        unit="stocks",
        regulatory_basis="SEBI IA Regulations, 2013, Regulation 17(1) Diversification Mandate",
        rationale="A minimum of 3 eligible candidate securities is required to construct a valid diversified equity portfolio.",
    ),
    "POL-SECTBREADTH-01": PolicyRule(
        rule_id="POL-SECTBREADTH-01",
        name="Minimum Sector Diversity Breadth",
        category=RuleCategory.CRITIC_FIDUCIARY_DEFECT,
        threshold=2,
        unit="sectors",
        regulatory_basis="SEBI Diversification Framework",
        rationale="A portfolio must span at least 2 distinct economic sectors to respect the 40% maximum sector concentration ceiling.",
    ),

    # 3. SOFT DISCLOSURE WARNINGS (Informational Transparency)
    "POL-CASH-DRAG-01": PolicyRule(
        rule_id="POL-CASH-DRAG-01",
        name="Small Capital Cash Drag Advisory",
        category=RuleCategory.SOFT_DISCLOSURE_WARNING,
        threshold=15000.0,
        unit="INR",
        regulatory_basis="Retail Investor Disclosure Guidelines",
        rationale="Portfolios below ₹15,000 may experience cash drag of 2-5% because high-priced bluechips cannot be bought in fractional lots.",
    ),
    "POL-DATA-STALE-01": PolicyRule(
        rule_id="POL-DATA-STALE-01",
        name="Market Price Freshness Limit",
        category=RuleCategory.SOFT_DISCLOSURE_WARNING,
        threshold=14,
        unit="days",
        regulatory_basis="Market Data Quality & Audit Standards",
        rationale="Security prices older than 14 trading days must be flagged as stale and require market sync before live execution.",
    ),
    "POL-HISTORY-3Y-01": PolicyRule(
        rule_id="POL-HISTORY-3Y-01",
        name="3-Year Statistical History Requirement",
        category=RuleCategory.SOFT_DISCLOSURE_WARNING,
        threshold=700,
        unit="trading days",
        regulatory_basis="Quantitative Factor Estimation Standards",
        rationale="Estimating 3-year beta or 3-year CAGR with fewer than 700 trading days yields unreliable statistical estimators; must be labeled INSUFFICIENT_HISTORY or use short-term metrics.",
    ),
}


# ==============================================================================
# AUTHORITATIVE RISK PROFILE SPECIFICATIONS
# ==============================================================================

@dataclass(frozen=True)
class RiskProfileBenchmark:
    risk_category: str
    target_return_pct: float
    max_single_stock_pct: float
    max_sector_pct: float
    risk_aversion: float
    max_portfolio_beta: float
    min_holdings_count: int
    regulatory_suitability: str


RISK_PROFILE_POLICIES: Dict[str, RiskProfileBenchmark] = {
    "very_conservative": RiskProfileBenchmark(
        risk_category="very_conservative",
        target_return_pct=8.0,
        max_single_stock_pct=15.0,
        max_sector_pct=35.0,
        risk_aversion=10.0,
        max_portfolio_beta=0.90,
        min_holdings_count=7,
        regulatory_suitability="Capital preservation focus; low tolerance for drawdown; high defensive bluechip allocation.",
    ),
    "conservative": RiskProfileBenchmark(
        risk_category="conservative",
        target_return_pct=10.0,
        max_single_stock_pct=20.0,
        max_sector_pct=35.0,
        risk_aversion=6.0,
        max_portfolio_beta=1.05,
        min_holdings_count=5,
        regulatory_suitability="Income and moderate capital preservation; controlled market beta.",
    ),
    "moderate": RiskProfileBenchmark(
        risk_category="moderate",
        target_return_pct=12.5,
        max_single_stock_pct=25.0,
        max_sector_pct=40.0,
        risk_aversion=3.5,
        max_portfolio_beta=1.25,
        min_holdings_count=4,
        regulatory_suitability="Balanced long-term wealth compounding; market-neutral to slight beta tilt.",
    ),
    "growth": RiskProfileBenchmark(
        risk_category="growth",
        target_return_pct=15.0,
        max_single_stock_pct=25.0,
        max_sector_pct=40.0,
        risk_aversion=2.0,
        max_portfolio_beta=1.45,
        min_holdings_count=4,
        regulatory_suitability="Capital appreciation orientation; willing to absorb cyclical volatility.",
    ),
    "aggressive": RiskProfileBenchmark(
        risk_category="aggressive",
        target_return_pct=18.0,
        max_single_stock_pct=25.0,
        max_sector_pct=40.0,
        risk_aversion=1.0,
        max_portfolio_beta=1.65,
        min_holdings_count=4,
        regulatory_suitability="Maximum capital appreciation; high momentum and beta tolerance; extended horizon.",
    ),
}


def get_policy_rule(rule_id: str) -> Optional[PolicyRule]:
    """Retrieves an authoritative policy rule by its ID."""
    return POLICY_RULES.get(rule_id)


def get_risk_profile_policy(risk_category: str) -> RiskProfileBenchmark:
    """Retrieves the authoritative risk profile benchmark policy."""
    cat = (risk_category or "moderate").lower()
    return RISK_PROFILE_POLICIES.get(cat, RISK_PROFILE_POLICIES["moderate"])


def get_portfolio_policy_limits(
    preferences: Optional[Dict[str, Any]] = None,
    risk_category: str = "moderate",
) -> Dict[str, Any]:
    """
    Returns unified, configurable risk policy limits for portfolio generation,
    monitoring, diagnosis, Critic, and rebalancing.
    User preferences override internal defaults within safe fiduciary bounds (10% to 35% single-stock, 20% to 50% sector).
    """
    prefs = preferences or {}
    profile = get_risk_profile_policy(risk_category)

    # 1. Single stock ceiling: user preference > risk profile default > system default
    user_single = prefs.get("max_single_stock_weight_pct") or prefs.get("max_single_stock_pct")
    if user_single is not None:
        max_single = max(10.0, min(float(user_single), 35.0))
    else:
        max_single = profile.max_single_stock_pct

    # 2. Sector cap: user preference > risk profile default > system default
    user_sector = prefs.get("max_sector_weight_pct") or prefs.get("max_sector_pct")
    if user_sector is not None:
        max_sector = max(20.0, min(float(user_sector), 50.0))
    else:
        max_sector = profile.max_sector_pct

    return {
        "max_single_stock_pct": max_single,
        "max_sector_pct": max_sector,
        "stock_drift_threshold_pct": float(prefs.get("stock_drift_threshold_pct", DEFAULT_DRIFT_THRESHOLD_STOCK_PCT)),
        "sector_drift_threshold_pct": float(prefs.get("sector_drift_threshold_pct", DEFAULT_DRIFT_THRESHOLD_SECTOR_PCT)),
        "min_holdings_count": profile.min_holdings_count,
        "policy_type": "LUCID_INTERNAL_RISK_POLICY",
        "regulatory_context": "SEBI Investment Advisers Regulations, 2013, Regulation 17 (Fiduciary Suitability Mandate)",
        "regulatory_clarification": (
            "25% single-stock and 40% sector limits are Lucid internal risk policies. "
            "SEBI IA Regulations require suitability and fiduciary diversification, but do not specify fixed numerical percentages for retail direct equity."
        ),
    }
