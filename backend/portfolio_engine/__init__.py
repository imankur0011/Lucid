"""
Portfolio Engine Package.
Deterministic candidate selection, constraints enforcement, mathematical optimization,
integer share rounding, risk metrics, and validation.
"""

from backend.portfolio_engine.candidate_selection import CandidateUniverseSelector
from backend.portfolio_engine.constraints import PortfolioConstraints, check_allocation_constraints
from backend.portfolio_engine.optimizer import optimize_portfolio_allocations
from backend.portfolio_engine.allocation_rounding import calculate_integer_shares_and_amounts
from backend.portfolio_engine.risk_metrics import compute_portfolio_metrics
from backend.portfolio_engine.validators import PortfolioValidator
from backend.portfolio_engine.service import PortfolioEngineService
from backend.portfolio_engine.factors import get_equity_factors, determine_optimal_holding_count

__all__ = [
    "CandidateUniverseSelector",
    "PortfolioConstraints",
    "check_allocation_constraints",
    "optimize_portfolio_allocations",
    "calculate_integer_shares_and_amounts",
    "compute_portfolio_metrics",
    "PortfolioValidator",
    "PortfolioEngineService",
    "get_equity_factors",
    "determine_optimal_holding_count",
]
