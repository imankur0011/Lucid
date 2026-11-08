"""
Pre-Execution Feasibility Checker for Lucid Portfolio Engine.
Evaluates mathematical, regulatory, and data feasibility prior to launching
the multi-agent research and optimization workflow.

Version: 2026.11-v1.0
Authoritative Date: 2026-11-04
"""

import math
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

try:
    from backend.portfolio_engine.policy import get_risk_profile_policy, POLICY_RULES
except ImportError:
    from portfolio_engine.policy import get_risk_profile_policy, POLICY_RULES


class FeasibilityCheckResult(BaseModel):
    is_feasible: bool
    risk_category: str
    investment_amount: float
    min_holdings_required: int
    available_holdings_count: int
    unique_sectors_count: int
    conditions_satisfied: List[str] = Field(default_factory=list)
    conditions_violated: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    recommended_action: str


def check_portfolio_feasibility(
    capital: float,
    risk_category: str,
    eligible_candidates: List[Dict[str, Any]],
    preferences: Optional[Dict[str, Any]] = None,
    goal_type: str = "wealth_creation",
) -> FeasibilityCheckResult:
    """
    Deterministically evaluates whether the requested portfolio can be constructed
    with the available data, eligible universe, and active policy constraints.
    """
    prefs = preferences or {}
    policy = get_risk_profile_policy(risk_category)
    satisfied: List[str] = []
    violated: List[str] = []
    missing: List[str] = []

    cap_val = float(capital)
    cands_count = len(eligible_candidates)
    sectors = {c.get("sector_name") for c in eligible_candidates if c.get("sector_name")}
    sectors_count = len(sectors)

    # 1. Capital Threshold Feasibility
    min_cap = float(POLICY_RULES["POL-MINCAP-01"].threshold)
    if cap_val >= min_cap:
        satisfied.append(f"Capital ₹{cap_val:,.2f} satisfies minimum requirement (₹{min_cap:,.2f})")
    else:
        violated.append(f"Capital ₹{cap_val:,.2f} is below minimum threshold of ₹{min_cap:,.2f}")

    # 2. Minimum Holdings Required by Allocation Ceiling
    effective_max_stock_pct = policy.max_single_stock_pct
    if "max_single_stock_weight_pct" in prefs and prefs["max_single_stock_weight_pct"]:
        effective_max_stock_pct = min(effective_max_stock_pct, float(prefs["max_single_stock_weight_pct"]))

    min_holdings_needed = int(math.ceil(100.0 / effective_max_stock_pct))
    if cands_count >= min_holdings_needed:
        satisfied.append(
            f"Available candidate pool ({cands_count}) satisfies mathematical minimum of {min_holdings_needed} "
            f"stocks required by the {effective_max_stock_pct:.1f}% single-stock ceiling"
        )
    else:
        violated.append(
            f"Insufficient candidates: {cands_count} available, but at least {min_holdings_needed} are required "
            f"to satisfy the {effective_max_stock_pct:.1f}% single-stock allocation ceiling"
        )

    # 3. Sector Diversity Breadth Feasibility
    effective_max_sector_pct = policy.max_sector_pct
    if "max_sector_weight_pct" in prefs and prefs["max_sector_weight_pct"]:
        effective_max_sector_pct = min(effective_max_sector_pct, float(prefs["max_sector_weight_pct"]))

    min_sectors_needed = int(math.ceil(100.0 / effective_max_sector_pct))
    min_sectors_needed = max(min_sectors_needed, 2)

    if sectors_count >= min_sectors_needed:
        satisfied.append(
            f"Candidate universe spans {sectors_count} sectors, satisfying the minimum {min_sectors_needed} "
            f"sectors required by the {effective_max_sector_pct:.1f}% sector exposure cap"
        )
    else:
        violated.append(
            f"Insufficient sector diversity: candidate universe has only {sectors_count} sector(s), "
            f"making the {effective_max_sector_pct:.1f}% sector exposure cap mathematically impossible"
        )

    # 4. Price & Valuation Data Availability
    unpriced_count = sum(1 for c in eligible_candidates if not c.get("latest_price") or c.get("latest_price") <= 0)
    if unpriced_count > 0:
        missing.append(f"{unpriced_count} candidate securities lack verified closing prices")

    # 5. Conflicting Investor Preferences
    user_exclusions = prefs.get("excluded_sectors", [])
    if len(user_exclusions) >= 7 and sectors_count < 3:
        violated.append("Excessive sector exclusions prevent construction of a fiduciary-compliant diversified portfolio")

    # Determine Overall Feasibility
    is_feasible = (len(violated) == 0)

    # Recommended Action
    if is_feasible:
        rec_action = "Proceed with specialized agent research and mathematical optimization workflow."
    elif cands_count < min_holdings_needed or sectors_count < min_sectors_needed:
        rec_action = "Expand eligible universe by relaxing sector exclusions or selecting a broader market benchmark."
    elif cap_val < min_cap:
        rec_action = f"Increase investment capital to at least ₹{min_cap:,.2f} for diversified whole-share allocation."
    else:
        rec_action = "Review and resolve active constraint conflicts before initiating portfolio generation."

    return FeasibilityCheckResult(
        is_feasible=is_feasible,
        risk_category=risk_category,
        investment_amount=cap_val,
        min_holdings_required=min_holdings_needed,
        available_holdings_count=cands_count,
        unique_sectors_count=sectors_count,
        conditions_satisfied=satisfied,
        conditions_violated=violated,
        missing_information=missing,
        recommended_action=rec_action,
    )

