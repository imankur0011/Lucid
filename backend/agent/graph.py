"""
LangGraph StateGraph Definition for Intelligent Multi-Agent Portfolio Generation.
Compiles:
1. Manager Node
2. Suitability & Feasibility Node
3. Macro Analyst Node
4. Market Analyst Node
5. Fundamental / Equity Research Analyst Node
6. News & Corporate Filings Analyst Node
7. Lead Strategist Node
8. Independent Risk Critic Node
9. Strategist Bounded Rework Node
10. Deterministic SLSQP Optimizer & Integer Lot Node
11. Critic Final Validation Node (Post-Optimizer Allocation & Constraint Audit)
12. Fiduciary Moderator Node (Two-Level Explanations)
13. ACID PostgreSQL Persistence Node

Version: 2026.11-v2.0
Authoritative Date: 2026-11-05
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

try:
    from backend.agent.state import PortfolioAgentState
    from backend.agent.schemas import CriticVerdictStatus
    from backend.agent.nodes import (
        manager_node,
        suitability_check_node,
        macro_analyst_node,
        market_analyst_node,
        fundamental_analyst_node,
        news_analyst_node,
        analyst_node,
        critic_node,
        strategist_rework_node,
        deterministic_optimizer_node,
        critic_final_validation_node,
        moderator_explanation_node,
        persistence_node,
    )
except ImportError:
    from agent.state import PortfolioAgentState
    from agent.schemas import CriticVerdictStatus
    from agent.nodes import (
        manager_node,
        suitability_check_node,
        macro_analyst_node,
        market_analyst_node,
        fundamental_analyst_node,
        news_analyst_node,
        analyst_node,
        critic_node,
        strategist_rework_node,
        deterministic_optimizer_node,
        critic_final_validation_node,
        moderator_explanation_node,
        persistence_node,
    )


def create_portfolio_graph(db: Session):
    """Builds and compiles the multi-agent LangGraph workflow with request-scoped DB session injection."""
    builder = StateGraph(PortfolioAgentState)

    # 1. Add All Workflow Nodes
    builder.add_node("manager", manager_node)
    builder.add_node("suitability", lambda state: suitability_check_node(state, db))
    builder.add_node("macro_analyst", lambda state: macro_analyst_node(state, db))
    builder.add_node("market_analyst", lambda state: market_analyst_node(state, db))
    builder.add_node("fundamental_analyst", lambda state: fundamental_analyst_node(state, db))
    builder.add_node("news_analyst", lambda state: news_analyst_node(state, db))
    builder.add_node("analyst", analyst_node)
    builder.add_node("critic", critic_node)
    builder.add_node("strategist_rework", strategist_rework_node)
    builder.add_node("optimizer", deterministic_optimizer_node)
    builder.add_node("critic_final_validation", critic_final_validation_node)
    builder.add_node("moderator", moderator_explanation_node)
    builder.add_node("persistence", lambda state: persistence_node(state, db))

    # 2. Define Transitions
    builder.set_entry_point("manager")
    builder.add_edge("manager", "suitability")

    # Suitability & Feasibility check: routes to Macro Agent or aborts to persistence
    builder.add_conditional_edges(
        "suitability",
        lambda state: "macro_analyst" if state.get("suitability_passed", False) else "persistence",
        {"macro_analyst": "macro_analyst", "persistence": "persistence"},
    )

    # Specialized research agents pipeline: Macro -> Market -> Fundamental -> News -> Lead Strategist
    builder.add_edge("macro_analyst", "market_analyst")
    builder.add_edge("market_analyst", "fundamental_analyst")
    builder.add_edge("fundamental_analyst", "news_analyst")
    builder.add_edge("news_analyst", "analyst")

    # Lead Strategist -> Critic
    builder.add_edge("analyst", "critic")

    # Critic decision routing:
    def route_critic(state: PortfolioAgentState) -> str:
        verdict = state.get("critic_verdict_status")
        approved = state.get("critic_approved", False)
        rework_count = state.get("rework_count", 0)
        max_rework = state.get("max_rework_count", 2)

        # Fiduciary Invariant: Missing, malformed, or unverified outputs NEVER count as approval
        if approved and verdict in (CriticVerdictStatus.APPROVED.value, "APPROVED"):
            return "optimizer"

        if verdict in (CriticVerdictStatus.REWORK_REQUIRED.value, "REWORK_REQUIRED") and rework_count < max_rework:
            return "strategist_rework"

        # If iteration >= max_rework or blocked or data insufficient, route directly to persistence (Stop and Report)
        return "persistence"

    builder.add_conditional_edges(
        "critic",
        route_critic,
        {"optimizer": "optimizer", "strategist_rework": "strategist_rework", "persistence": "persistence"},
    )

    # Strategist rework routes back to Critic for re-audit
    builder.add_edge("strategist_rework", "critic")

    # Mathematical optimizer routes to post-optimizer Critic Final Validation, rework, or persistence
    def route_optimizer(state: PortfolioAgentState) -> str:
        val_passed = state.get("validation_passed", False)
        rework_count = state.get("rework_count", 0)
        max_rework = state.get("max_rework_count", 2)

        if val_passed:
            return "critic_final_validation"
        if rework_count < max_rework:
            return "strategist_rework"
        return "persistence"

    builder.add_conditional_edges(
        "optimizer",
        route_optimizer,
        {"critic_final_validation": "critic_final_validation", "strategist_rework": "strategist_rework", "persistence": "persistence"},
    )

    # Post-Optimizer Critic Final Validation routes to Moderator or persistence (Stop and Report)
    def route_final_critic(state: PortfolioAgentState) -> str:
        critic_final = state.get("critic_final_output", {})
        decision = critic_final.get("decision", "BLOCKED_VIOLATION")
        can_proceed = critic_final.get("can_proceed", False)

        if can_proceed and decision in ("APPROVED", CriticVerdictStatus.APPROVED.value):
            return "moderator"
        return "persistence"

    builder.add_conditional_edges(
        "critic_final_validation",
        route_final_critic,
        {"moderator": "moderator", "persistence": "persistence"},
    )

    # Moderator -> Persistence -> End
    builder.add_edge("moderator", "persistence")
    builder.add_edge("persistence", END)

    return builder.compile()
