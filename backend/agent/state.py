"""
Typed State Definition for the Intelligent Portfolio LangGraph Multi-Agent Workflow.
Enforces strict Pydantic output schemas, evidence tracking, and structured agent communication.

Version: 2026.11-v2.0
Authoritative Date: 2026-11-05
"""

from typing import TypedDict, List, Dict, Any, Optional


class PortfolioAgentState(TypedDict, total=False):
    # ==========================================================================
    # 1. INVESTOR PROFILE & PORTFOLIO CONTEXT
    # ==========================================================================
    generation_request_id: str
    portfolio_id: str
    user_id: str
    goal_id: Optional[str]
    goal_type: Optional[str]
    risk_assessment_id: Optional[str]
    portfolio_version_id: Optional[str]
    version_number: Optional[int]
    user_profile: Dict[str, Any]
    existing_portfolio: Optional[Dict[str, Any]]
    investment_amount: float
    currency_code: str
    investment_horizon_months: int
    risk_category: str
    user_prompt: Optional[str]
    preferences: Dict[str, Any]
    investor_snapshot: Dict[str, Any]

    # Pre-Execution Suitability & Mathematical Feasibility Checks
    suitability_passed: bool
    suitability_notes: List[str]
    feasibility_result: Optional[Dict[str, Any]]
    eligible_candidates: List[Dict[str, Any]]

    # ==========================================================================
    # 2. SPECIALIST AGENT STRUCTURED OUTPUTS (Strict Pydantic Schemas)
    # ==========================================================================
    suitability_output: Optional[Dict[str, Any]]
    macro_output: Optional[Dict[str, Any]]
    market_output: Optional[Dict[str, Any]]
    fundamental_output: Optional[Dict[str, Any]]
    news_output: Optional[Dict[str, Any]]
    strategist_output: Optional[Dict[str, Any]]
    critic_output: Optional[Dict[str, Any]]
    optimizer_output: Optional[Dict[str, Any]]
    critic_final_output: Optional[Dict[str, Any]]
    moderator_output: Optional[Dict[str, Any]]

    # Legacy Compatibility Dicts
    macro_analysis: Optional[Dict[str, Any]]
    market_analysis: Optional[Dict[str, Any]]
    news_analysis: Optional[Dict[str, Any]]
    market_regime: Optional[Dict[str, Any]]
    analyst_research_notes: Dict[str, Any]

    # Independent Risk Critic States & Bounded Rework
    critic_verdict_status: Optional[str]
    critic_approved: bool
    critic_iteration: int
    critic_findings: List[Dict[str, Any]]
    removable_tickers: Optional[List[str]]
    rework_instructions: Optional[List[str]]
    blocking_reasons: Optional[List[str]]
    can_proceed: bool

    # Deterministic Optimization & Math Validation
    allocations: List[Dict[str, Any]]
    total_invested: float
    unallocated_cash: float
    risk_metrics: Dict[str, float]
    validation_output: Dict[str, Any]
    validation_passed: bool

    # User Explanations & Evidence Provenance
    explanations: List[Dict[str, Any]]
    evidence_items: List[Dict[str, Any]]
    evidence_registry: Dict[str, Any]  # Keyed by evidence_id
    agent_messages: List[Dict[str, Any]]  # Inter-agent structured communication
    agent_execution_history: List[Dict[str, Any]]

    # ==========================================================================
    # 3. WORKFLOW CONTROL & AUDIT STATUS
    # ==========================================================================
    current_stage: str
    status: str  # 'running' | 'succeeded' | 'failed'
    workflow_status: str  # 'RUNNING' | 'COMPLETED' | 'BLOCKED' | 'DATA_INSUFFICIENT'
    rework_count: int
    max_rework_count: int
    error_code: Optional[str]
    error_summary: Optional[str]
    validation_errors: List[str]
    final_recommendation: Optional[Dict[str, Any]]
    execution_trace: List[Dict[str, Any]]


# Shared alias matching architectural specifications
LucidGraphState = PortfolioAgentState
