"""
LangGraph StateGraph Definition for Intelligent Portfolio Generation.
Compiles the manager, suitability check, analyst, critic, deterministic optimizer,
moderator explanation, and PostgreSQL persistence nodes.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

try:
    from backend.agent.state import PortfolioAgentState
    from backend.agent.nodes import (
        manager_node,
        suitability_check_node,
        analyst_node,
        critic_node,
        deterministic_optimizer_node,
        moderator_explanation_node,
        persistence_node,
    )
except ImportError:
    from agent.state import PortfolioAgentState
    from agent.nodes import (
        manager_node,
        suitability_check_node,
        analyst_node,
        critic_node,
        deterministic_optimizer_node,
        moderator_explanation_node,
        persistence_node,
    )


def create_portfolio_graph(db: Session):
    """Builds and compiles the LangGraph workflow with request-scoped DB session injection."""
    builder = StateGraph(PortfolioAgentState)

    # Add Nodes
    builder.add_node("manager", manager_node)
    builder.add_node("suitability", lambda state: suitability_check_node(state, db))
    builder.add_node("analyst", analyst_node)
    builder.add_node("critic", critic_node)
    builder.add_node("optimizer", deterministic_optimizer_node)
    builder.add_node("moderator", moderator_explanation_node)
    builder.add_node("persistence", lambda state: persistence_node(state, db))

    # Define Conditional Transitions
    builder.set_entry_point("manager")
    builder.add_edge("manager", "suitability")

    builder.add_conditional_edges(
        "suitability",
        lambda state: "analyst" if state.get("suitability_passed", False) else "persistence",
        {"analyst": "analyst", "persistence": "persistence"},
    )

    builder.add_edge("analyst", "critic")

    builder.add_conditional_edges(
        "critic",
        lambda state: "optimizer" if state.get("critic_approved", False) else "persistence",
        {"optimizer": "optimizer", "persistence": "persistence"},
    )

    builder.add_conditional_edges(
        "optimizer",
        lambda state: "moderator" if state.get("validation_passed", False) else "persistence",
        {"moderator": "moderator", "persistence": "persistence"},
    )

    builder.add_edge("moderator", "persistence")
    builder.add_edge("persistence", END)

    return builder.compile()
