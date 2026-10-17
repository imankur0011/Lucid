"""
Typed State Definition for the Intelligent Portfolio LangGraph Agent Workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class PortfolioAgentState(TypedDict, total=False):
    # Workflow & Request Identity
    generation_request_id: str
    portfolio_id: str
    user_id: str
    goal_id: Optional[str]
    risk_assessment_id: Optional[str]
    portfolio_version_id: Optional[str]
    version_number: Optional[int]
    
    # Investor Inputs & Context
    investment_amount: float
    currency_code: str
    investment_horizon_months: int
    risk_category: str
    user_prompt: Optional[str]
    preferences: Dict[str, Any]
    investor_snapshot: Dict[str, Any]

    # Suitability & Eligibility Checks
    suitability_passed: bool
    suitability_notes: List[str]
    eligible_candidates: List[Dict[str, Any]]

    # Agent Analysis & Critique
    analyst_research_notes: Dict[str, Any]
    critic_findings: List[Dict[str, Any]]
    critic_approved: bool
    critic_iteration: int

    # Deterministic Optimization & Math Validation
    allocations: List[Dict[str, Any]]
    total_invested: float
    unallocated_cash: float
    risk_metrics: Dict[str, float]
    validation_output: Dict[str, Any]
    validation_passed: bool

    # User Explanations & Evidence
    explanations: List[Dict[str, Any]]
    evidence_items: List[Dict[str, Any]]

    # Workflow Execution Status
    current_stage: str
    status: str  # 'running' | 'succeeded' | 'failed'
    error_code: Optional[str]
    error_summary: Optional[str]
    execution_trace: List[Dict[str, Any]]
