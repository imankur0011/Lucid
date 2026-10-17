"""
LangGraph Nodes for the Intelligent Portfolio Creation Workflow.
Orchestrates Manager, Suitability Checks, Analyst, Critic, Deterministic Optimizer, Moderator, and DB Persistence.
"""

import uuid
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List
from sqlalchemy.orm import Session

try:
    from backend.agent.state import PortfolioAgentState
    from backend.portfolio_engine import (
        CandidateUniverseSelector,
        PortfolioConstraints,
        optimize_portfolio_allocations,
        calculate_integer_shares_and_amounts,
        compute_portfolio_metrics,
        PortfolioValidator,
    )
    from backend.models import (
        PortfolioGenerationRequest,
        InvestorPortfolio,
        PortfolioVersion,
        StrategyVersion,
        StrategyDefinition,
        PortfolioSecurityDecision,
        PortfolioVersionConstraint,
        PortfolioValidationRun,
        PortfolioValidationResult,
        RecommendationExplanation,
        EvidenceItem,
        ExplanationEvidence,
        DataSource,
    )
except ImportError:
    from agent.state import PortfolioAgentState
    from portfolio_engine import (
        CandidateUniverseSelector,
        PortfolioConstraints,
        optimize_portfolio_allocations,
        calculate_integer_shares_and_amounts,
        compute_portfolio_metrics,
        PortfolioValidator,
    )
    from models import (
        PortfolioGenerationRequest,
        InvestorPortfolio,
        PortfolioVersion,
        StrategyVersion,
        StrategyDefinition,
        PortfolioSecurityDecision,
        PortfolioVersionConstraint,
        PortfolioValidationRun,
        PortfolioValidationResult,
        RecommendationExplanation,
        EvidenceItem,
        ExplanationEvidence,
        DataSource,
    )


def manager_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """1. Manager / Orchestrator: Initializes workflow, logs request parameters."""
    trace = state.get("execution_trace", [])
    trace.append({
        "step": "manager",
        "timestamp": datetime.now().isoformat(),
        "message": f"Loaded generation request for amount ₹{state.get('investment_amount', 0):,.2f}",
    })
    return {
        "current_stage": "input_suitability_check",
        "status": "running",
        "execution_trace": trace,
        "critic_iteration": 0,
    }


def suitability_check_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """2. Deterministic suitability and candidate eligibility validation."""
    trace = state.get("execution_trace", [])
    amount = Decimal(str(state.get("investment_amount", 0)))
    notes = []
    passed = True

    if amount < Decimal("1000"):
        passed = False
        notes.append("Investment amount is below minimum threshold of ₹1,000")

    prefs = state.get("preferences", {})
    selector = CandidateUniverseSelector(db)
    candidates = selector.select_eligible_candidates(
        excluded_sectors=prefs.get("excluded_sectors", []),
        excluded_instruments=prefs.get("excluded_instruments", []),
    )

    if not candidates:
        passed = False
        notes.append("No active candidate securities available after applying investor exclusions")
    else:
        notes.append(f"Selected {len(candidates)} eligible candidate securities from active universe")

    trace.append({
        "step": "suitability_check",
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "notes": notes,
    })

    return {
        "suitability_passed": passed,
        "suitability_notes": notes,
        "eligible_candidates": candidates,
        "current_stage": "analyst" if passed else "failed",
        "status": "running" if passed else "failed",
        "error_code": None if passed else "SUITABILITY_FAILED",
        "error_summary": None if passed else "; ".join(notes),
        "execution_trace": trace,
    }


def analyst_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """3. Analyst / Strategist: Analyzes eligible candidates and aligns with risk profile."""
    trace = state.get("execution_trace", [])
    risk = state.get("risk_category", "moderate")
    candidates = state.get("eligible_candidates", [])

    sector_counts = {}
    for c in candidates:
        sec = c.get("sector_name", "General")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    research_notes = {
        "strategy_theme": f"Active {risk.capitalize()} Equity Allocation",
        "target_sectors": list(sector_counts.keys()),
        "diversification_breadth": len(sector_counts),
        "recommended_stance": (
            "Capital preservation with defensive sector bias" if risk in ["very_conservative", "conservative"]
            else "Balanced growth across core banking, technology, and industry leaders"
        ),
    }

    trace.append({
        "step": "analyst",
        "timestamp": datetime.now().isoformat(),
        "summary": f"Completed research for {len(candidates)} candidates across {len(sector_counts)} sectors",
    })

    return {
        "analyst_research_notes": research_notes,
        "current_stage": "critic",
        "execution_trace": trace,
    }


def critic_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """4. Critic: Validates analyst assumptions, checks constraint consistency."""
    trace = state.get("execution_trace", [])
    candidates = state.get("eligible_candidates", [])
    iteration = state.get("critic_iteration", 0) + 1

    findings = []
    approved = True

    if len(candidates) < 3:
        approved = False
        findings.append({
            "code": "INSUFFICIENT_BREADTH",
            "message": f"Only {len(candidates)} candidates available. Minimum recommended is 3.",
            "severity": "critical",
        })

    trace.append({
        "step": "critic",
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "approved": approved,
        "findings": findings,
    })

    return {
        "critic_findings": findings,
        "critic_approved": approved,
        "critic_iteration": iteration,
        "current_stage": "optimizer" if approved else "failed",
        "status": "running" if approved else "failed",
        "error_code": None if approved else "CRITIC_REJECTED",
        "error_summary": None if approved else "Critic identified unresolvable candidate deficiencies",
        "execution_trace": trace,
    }


def deterministic_optimizer_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """5. Deterministic Optimizer & Risk Validator: Executes mathematical SLSQP allocation & hard checks."""
    trace = state.get("execution_trace", [])
    candidates = state.get("eligible_candidates", [])
    amount = Decimal(str(state.get("investment_amount", 100000)))
    risk = state.get("risk_category", "moderate")
    prefs = state.get("preferences", {})

    constraints = PortfolioConstraints(
        max_single_stock_pct=prefs.get("max_single_stock_weight_pct", 25.0),
        max_sector_pct=prefs.get("max_sector_weight_pct", 40.0),
        min_stocks_count=min(3, len(candidates)),
    )

    opt_ok, raw_allocs, opt_msg = optimize_portfolio_allocations(
        candidates=candidates,
        risk_category=risk,
        constraints=constraints,
    )

    if not opt_ok or not raw_allocs:
        trace.append({
            "step": "optimizer",
            "timestamp": datetime.now().isoformat(),
            "passed": False,
            "error": opt_msg,
        })
        return {
            "validation_passed": False,
            "current_stage": "failed",
            "status": "failed",
            "error_code": "OPTIMIZER_FAILURE",
            "error_summary": opt_msg,
            "execution_trace": trace,
        }

    # Integer rounding & cash computation
    enriched, invested, unallocated = calculate_integer_shares_and_amounts(raw_allocs, amount)
    metrics = compute_portfolio_metrics(enriched)

    # Hard mathematical validation
    validator = PortfolioValidator(constraints)
    val_out = validator.validate_portfolio(enriched, amount)

    trace.append({
        "step": "optimizer_and_validator",
        "timestamp": datetime.now().isoformat(),
        "validation_status": val_out["validation_status"],
        "all_passed": val_out["all_passed"],
        "holdings_count": len(enriched),
        "metrics": metrics,
    })

    return {
        "allocations": enriched,
        "total_invested": float(invested),
        "unallocated_cash": float(unallocated),
        "risk_metrics": metrics,
        "validation_output": val_out,
        "validation_passed": val_out["all_passed"],
        "current_stage": "moderator" if val_out["all_passed"] else "failed",
        "status": "running" if val_out["all_passed"] else "failed",
        "error_code": None if val_out["all_passed"] else "VALIDATION_FAILED",
        "error_summary": None if val_out["all_passed"] else "Portfolio failed hard mathematical validation rules",
        "execution_trace": trace,
    }


def moderator_explanation_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """6. Moderator / Explanation Generator: Translates mathematical results into investor explanations."""
    trace = state.get("execution_trace", [])
    holdings = state.get("allocations", [])
    risk = state.get("risk_category", "moderate")
    metrics = state.get("risk_metrics", {})
    unallocated = state.get("unallocated_cash", 0.0)

    explanations = []

    # Portfolio Strategy Overview
    explanations.append({
        "explanation_type": "portfolio",
        "title": f"Disciplined {risk.capitalize()} Portfolio Architecture",
        "explanation_text": (
            f"Allocated across {len(holdings)} equity securities targeting {metrics.get('expected_return_pct', 0):.2f}% "
            f"annualized return with {metrics.get('expected_volatility_pct', 0):.2f}% expected volatility, "
            f"optimized for a {risk} risk profile."
        ),
        "display_order": 1,
    })

    # Diversification Overview
    explanations.append({
        "explanation_type": "diversification",
        "title": "Sector and Risk Concentration Control",
        "explanation_text": (
            f"Diversification score is {metrics.get('diversification_score', 0):.1f}/100. "
            f"Maximum single stock weight capped at 25% and sector weights capped at 40% to maintain "
            f"resilience against sector-specific downturns."
        ),
        "display_order": 2,
    })

    # Holding Explanations
    for idx, h in enumerate(holdings, start=3):
        explanations.append({
            "explanation_type": "selection",
            "title": f"Holding: {h['symbol']} ({h['security_name']})",
            "explanation_text": (
                f"Assigned target weight of {h['target_weight_pct']:.2f}% (₹{h['target_amount']:,.2f}, {h['shares_quantity']} shares "
                f"at ₹{h['latest_price']:,.2f}). Anchors exposure in the {h['sector_name']} sector."
            ),
            "display_order": idx,
            "security_id": str(h["security_id"]),
            "listing_id": str(h["listing_id"]),
        })

    if unallocated > 0:
        explanations.append({
            "explanation_type": "constraint",
            "title": "Whole Share Integer Cash Reserve",
            "explanation_text": (
                f"₹{unallocated:,.2f} preserved in liquid reserve as Indian equities require integer-share purchases. "
                f"Available for subsequent SIP or rebalancing increments."
            ),
            "display_order": len(explanations) + 1,
        })

    trace.append({
        "step": "moderator_explanation",
        "timestamp": datetime.now().isoformat(),
        "explanations_count": len(explanations),
    })

    return {
        "explanations": explanations,
        "current_stage": "persistence",
        "execution_trace": trace,
    }


def persistence_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """7. Persistence Node: Commits version, holdings, constraints, validation, and explanations to PostgreSQL."""
    trace = state.get("execution_trace", [])
    now = datetime.now()

    request_id = uuid.UUID(state["generation_request_id"])
    portfolio_id = uuid.UUID(state["portfolio_id"])
    user_id = uuid.UUID(state["user_id"])

    req = db.query(PortfolioGenerationRequest).filter(PortfolioGenerationRequest.generation_request_id == request_id).first()

    if state.get("status") == "failed" or not state.get("validation_passed", False):
        if req:
            req.request_status = "failed"
            req.completed_at = now
            req.error_code = state.get("error_code", "GENERATION_FAILED")
            req.error_summary = state.get("error_summary", "Workflow failed")
            db.commit()
        return {
            "status": "failed",
            "current_stage": "completed",
            "execution_trace": trace,
        }

    # Retrieve or create default StrategyVersion
    strat_ver = db.query(StrategyVersion).first()
    if not strat_ver:
        strat_def = StrategyDefinition(
            strategy_id=uuid.uuid4(),
            strategy_code="ai_disciplined_mf",
            strategy_name="AI Disciplined Mutual Fund Manager Strategy",
            description="Agentic portfolio creation capturing top Indian fund manager methodologies.",
        )
        db.add(strat_def)
        db.flush()

        strat_ver = StrategyVersion(
            strategy_version_id=uuid.uuid4(),
            strategy_id=strat_def.strategy_id,
            version_label="1.0.0",
            optimizer_name="scipy_slsqp_constrained",
            implementation_revision="v1.0.0",
            configuration={"engine": "scipy-slsqp", "target": "sharpe_maximization"},
        )
        db.add(strat_ver)
        db.flush()

    # Lock parent portfolio to serialize version numbering under concurrency
    db.query(InvestorPortfolio).filter(InvestorPortfolio.portfolio_id == portfolio_id).with_for_update().first()

    # Determine next portfolio version number
    current_max_ver = (
        db.query(PortfolioVersion.version_number)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(PortfolioVersion.version_number.desc())
        .first()
    )
    next_ver_num = (current_max_ver[0] + 1) if current_max_ver else 1

    metrics = state.get("risk_metrics", {})
    holdings = state.get("allocations", [])

    # Create PortfolioVersion
    pv = PortfolioVersion(
        portfolio_version_id=uuid.uuid4(),
        portfolio_id=portfolio_id,
        generation_request_id=request_id,
        strategy_version_id=strat_ver.strategy_version_id,
        version_number=next_ver_num,
        version_status="generated",
        investment_amount=Decimal(str(state.get("investment_amount", 100000))),
        currency_code=state.get("currency_code", "INR"),
        investment_horizon_months=state.get("investment_horizon_months", 60),
        risk_category=state.get("risk_category", "moderate"),
        expected_return_pct=Decimal(str(metrics.get("expected_return_pct", 12.0))),
        expected_volatility_pct=Decimal(str(metrics.get("expected_volatility_pct", 15.0))),
        diversification_score=Decimal(str(metrics.get("diversification_score", 85.0))),
        market_context_as_of=now,
        generation_context={
            "trace": trace,
            "research_notes": state.get("analyst_research_notes", {}),
            "unallocated_cash": state.get("unallocated_cash", 0.0),
        },
        generated_at=now,
    )
    db.add(pv)
    db.flush()

    # Persist security decisions
    decision_map = {}
    for h in holdings:
        sec_id = uuid.UUID(str(h["security_id"]))
        list_id = uuid.UUID(str(h["listing_id"])) if h.get("listing_id") else None
        psd = PortfolioSecurityDecision(
            decision_id=uuid.uuid4(),
            portfolio_version_id=pv.portfolio_version_id,
            security_id=sec_id,
            listing_id=list_id,
            decision_status="selected",
            target_weight_pct=Decimal(str(h["target_weight_pct"])),
            decision_reason=f"Selected for risk-adjusted contribution in {h['sector_name']}",
        )
        db.add(psd)
        db.flush()
        decision_map[str(sec_id)] = psd.decision_id

    # Persist validation run and results
    val_out = state.get("validation_output", {})
    val_run = PortfolioValidationRun(
        validation_run_id=uuid.uuid4(),
        portfolio_version_id=pv.portfolio_version_id,
        rule_set_version=val_out.get("rule_set_version", "sebi-in-diversified-v1.0"),
        calculation_engine_version=val_out.get("calculation_engine_version", "scipy-slsqp-v1.0"),
        validation_status=val_out.get("validation_status", "passed"),
        started_at=now,
        completed_at=now,
        summary=val_out.get("summary", {}),
    )
    db.add(val_run)
    db.flush()

    for r in val_out.get("results", []):
        vr = PortfolioValidationResult(
            validation_result_id=uuid.uuid4(),
            validation_run_id=val_run.validation_run_id,
            rule_code=r["rule_code"],
            result_status=r["result_status"],
            severity=r["severity"],
            actual_value=Decimal(str(r["actual_value"])) if r.get("actual_value") is not None else None,
            threshold_value=Decimal(str(r["threshold_value"])) if r.get("threshold_value") is not None else None,
            result_message=r["result_message"],
            details=r.get("details", {}),
        )
        db.add(vr)

    # Persist explanations
    for exp in state.get("explanations", []):
        dec_id = decision_map.get(exp.get("security_id")) if exp.get("security_id") else None
        rec_exp = RecommendationExplanation(
            explanation_id=uuid.uuid4(),
            portfolio_version_id=pv.portfolio_version_id,
            decision_id=dec_id,
            explanation_type=exp["explanation_type"],
            title=exp["title"],
            explanation_text=exp["explanation_text"],
            display_order=exp["display_order"],
        )
        db.add(rec_exp)

    # Update generation request status
    if req:
        req.request_status = "succeeded"
        req.completed_at = now
        req.error_code = None
        req.error_summary = None

    db.commit()

    trace.append({
        "step": "persistence",
        "timestamp": datetime.now().isoformat(),
        "portfolio_version_id": str(pv.portfolio_version_id),
        "version_number": next_ver_num,
        "status": "succeeded",
    })

    return {
        "portfolio_version_id": str(pv.portfolio_version_id),
        "version_number": next_ver_num,
        "status": "succeeded",
        "current_stage": "completed",
        "execution_trace": trace,
    }
