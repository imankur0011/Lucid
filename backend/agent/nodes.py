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

try:
    from backend.config import settings
except ImportError:
    try:
        from config import settings
    except ImportError:
        settings = None


def get_llm():
    """Returns ChatGoogleGenerativeAI instance if API key is provided, else None."""
    if not settings:
        return None
    api_key = getattr(settings, "gemini_api_key", None)
    if api_key and api_key != "your_gemini_api_key_here" and len(api_key) > 10:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=getattr(settings, "llm_model", "gemini-2.5-flash") or "gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.2,
                timeout=15,
            )
        except Exception:
            return None
    return None


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
    """3. Analyst / Strategist: Analyzes eligible candidates, investor prompt, and aligns with risk profile."""
    trace = state.get("execution_trace", [])
    risk = state.get("risk_category", "moderate")
    candidates = state.get("eligible_candidates", [])
    user_prompt = state.get("user_prompt", "") or ""
    amount = float(state.get("investment_amount", 100000))
    horizon = int(state.get("investment_horizon_months", 60))

    sector_counts = {}
    for c in candidates:
        sec = c.get("sector_name", "General")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

    # Attempt dynamic LLM reasoning if configured
    llm = get_llm()
    llm_reasoning = None
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt_content = (
                f"You are an Indian SEBI-registered portfolio strategist.\n"
                f"Investor Risk Profile: {risk}, Investment Horizon: {horizon} months, Capital: ₹{amount:,.2f}.\n"
                f"Investor Custom Request: '{user_prompt}'\n"
                f"Candidate Universe: {len(candidates)} stocks across sectors: {list(sector_counts.keys())}.\n"
                f"Provide a concise strategy theme, recommended market stance, and priority focus."
            )
            resp = llm.invoke([
                SystemMessage(content="You are an expert quantitative Indian equities strategist. Return concise actionable insights."),
                HumanMessage(content=prompt_content),
            ])
            llm_reasoning = str(resp.content)
        except Exception:
            llm_reasoning = None

    # Contextual dynamic rule-based synthesis
    prompt_lower = user_prompt.lower()
    themes = []
    if "dividend" in prompt_lower or "yield" in prompt_lower:
        themes.append("High Dividend Yield & Cash Generation")
    if "tech" in prompt_lower or "it" in prompt_lower or "software" in prompt_lower:
        themes.append("Technology & Digital Transformation")
    if "bank" in prompt_lower or "finan" in prompt_lower:
        themes.append("Core Banking & Financial Deepening")
    if "growth" in prompt_lower:
        themes.append("High Return-on-Equity Secular Growth")
    if "defensive" in prompt_lower or "preserv" in prompt_lower:
        themes.append("Defensive Capital Preservation")

    theme_str = " & ".join(themes) if themes else f"Active {risk.capitalize()} Disciplined Equity"

    if horizon <= 24:
        stance = f"Near-term ({horizon}m) liquidity with focus on low-beta cash-rich bluechips"
    elif horizon >= 60:
        stance = f"Long-term ({horizon}m) compounding across high-ROE market leaders"
    else:
        stance = f"Medium-term ({horizon}m) balanced risk-adjusted equity expansion"

    if user_prompt:
        trunc_prompt = user_prompt[:80] + "..." if len(user_prompt) > 80 else user_prompt
        stance += f" aligned with: '{trunc_prompt}'"

    research_notes = {
        "strategy_theme": theme_str,
        "target_sectors": list(sector_counts.keys()),
        "diversification_breadth": len(sector_counts),
        "recommended_stance": stance,
        "llm_reasoning_summary": llm_reasoning,
        "investor_custom_prompt": user_prompt,
    }

    ai_provider = "gemini" if llm_reasoning else "dynamic_heuristic_fallback"
    model_name = getattr(settings, "llm_model", "gemini-2.5-flash") if llm_reasoning else "builtin-rule-synthesizer"

    trace.append({
        "step": "analyst",
        "timestamp": datetime.now().isoformat(),
        "summary": f"Analyzed {len(candidates)} candidates across {len(sector_counts)} sectors with theme '{theme_str}'",
        "ai_provider": ai_provider,
        "model_name": model_name,
        "prompt_version": "v1.2",
    })

    return {
        "analyst_research_notes": research_notes,
        "current_stage": "critic",
        "execution_trace": trace,
    }


def critic_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """4. Critic: Validates analyst assumptions, checks constraint consistency, cash drag, and prompt alignment."""
    trace = state.get("execution_trace", [])
    candidates = state.get("eligible_candidates", [])
    amount = float(state.get("investment_amount", 100000))
    user_prompt = state.get("user_prompt", "") or ""
    iteration = state.get("critic_iteration", 0) + 1

    findings = []
    approved = True

    if len(candidates) < 3:
        approved = False
        findings.append({
            "code": "INSUFFICIENT_BREADTH",
            "message": f"Only {len(candidates)} candidates available. Minimum recommended is 3 for regulatory diversification.",
            "severity": "critical",
        })

    # Cash drag check
    if amount < 15000:
        findings.append({
            "code": "HIGH_CASH_DRAG_RISK",
            "message": f"Investment capital of ₹{amount:,.2f} may experience higher percentage cash drag due to whole-share purchases of large-cap stocks.",
            "severity": "info",
        })

    # Sector breadth check
    sectors = {c.get("sector_name") for c in candidates if c.get("sector_name")}
    if len(sectors) < 2:
        findings.append({
            "code": "LIMITED_SECTOR_VARIETY",
            "message": "Universe has limited sector diversity; single-sector exposure limit of 40% must be monitored strictly.",
            "severity": "warning",
        })

    # Prompt alignment check
    prompt_lower = user_prompt.lower()
    if ("tech" in prompt_lower or "it" in prompt_lower) and not any("tech" in s.lower() or "information" in s.lower() for s in sectors):
        findings.append({
            "code": "PROMPT_SECTOR_UNAVAILABLE",
            "message": "Investor requested technology focus, but active candidate universe contains limited technology listings.",
            "severity": "info",
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
    """6. Moderator / Explanation Generator: Translates mathematical results and user prompt into structured explanations."""
    trace = state.get("execution_trace", [])
    holdings = state.get("allocations", [])
    risk = state.get("risk_category", "moderate")
    metrics = state.get("risk_metrics", {})
    unallocated = state.get("unallocated_cash", 0.0)
    user_prompt = state.get("user_prompt", "") or ""
    analyst_notes = state.get("analyst_research_notes", {})
    theme = analyst_notes.get("strategy_theme", f"Active {risk.capitalize()} Disciplined Equity")

    explanations = []

    # Attempt dynamic LLM explanation generation if configured
    llm = get_llm()
    custom_macro_text = None
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            holdings_summary = ", ".join([f"{h['symbol']} ({h['target_weight_pct']:.1f}%)" for h in holdings[:5]])
            prompt_content = (
                f"You are a SEBI-registered portfolio manager explaining an investment recommendation to a client.\n"
                f"Strategy: {theme}, Risk: {risk}, Expected Return: {metrics.get('expected_return_pct', 0):.2f}%, Volatility: {metrics.get('expected_volatility_pct', 0):.2f}%.\n"
                f"Allocations: {holdings_summary}.\n"
                f"Client Prompt: '{user_prompt}'.\n"
                f"Provide a 2-sentence executive summary explaining how this allocation directly achieves the client's stated intent."
            )
            resp = llm.invoke([
                SystemMessage(content="You are a transparent, disciplined portfolio manager in India."),
                HumanMessage(content=prompt_content),
            ])
            custom_macro_text = str(resp.content).strip()
        except Exception:
            custom_macro_text = None

    # Portfolio Strategy Overview
    if custom_macro_text:
        strategy_desc = custom_macro_text
    else:
        strategy_desc = (
            f"Constructed an allocation across {len(holdings)} equity securities targeting {metrics.get('expected_return_pct', 0):.2f}% "
            f"annualized return with {metrics.get('expected_volatility_pct', 0):.2f}% expected volatility, "
            f"optimized for a {risk} risk posture under the theme '{theme}'."
        )
        if user_prompt:
            strategy_desc += f" Directly addresses investor guidance: '{user_prompt}'."

    explanations.append({
        "explanation_type": "portfolio",
        "title": f"Disciplined {risk.capitalize()} Strategy: {theme}",
        "explanation_text": strategy_desc,
        "display_order": 1,
    })

    # Diversification Overview
    explanations.append({
        "explanation_type": "diversification",
        "title": "Sector Concentration & SEBI Risk Guardrails",
        "explanation_text": (
            f"Portfolio achieves a normalized diversification score of {metrics.get('diversification_score', 0):.1f}/100. "
            f"Maximum individual stock weight is strictly capped at 25% and all sector weights remain within the 40% limit "
            f"to protect against idiosyncratic drawdowns."
        ),
        "display_order": 2,
    })

    # Holding Explanations
    for idx, h in enumerate(holdings, start=3):
        explanations.append({
            "explanation_type": "selection",
            "title": f"Selected: {h['symbol']} ({h['security_name']})",
            "explanation_text": (
                f"Assigned {h['target_weight_pct']:.2f}% allocation (₹{h['target_amount']:,.2f}, {h['shares_quantity']} shares "
                f"at ₹{h['latest_price']:,.2f}). Selected for superior risk-adjusted contribution in the {h['sector_name']} sector."
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
                f"₹{unallocated:,.2f} preserved in liquid unallocated cash. Indian stock exchanges (NSE/BSE) require integer-share "
                f"execution with no fractional shares. This cash remains uninvested to maintain liquidity for subsequent SIP increments."
            ),
            "display_order": len(explanations) + 1,
        })

    ai_provider = "gemini" if custom_macro_text else "dynamic_heuristic_fallback"
    model_name = getattr(settings, "llm_model", "gemini-2.5-flash") if custom_macro_text else "builtin-rule-synthesizer"

    trace.append({
        "step": "moderator_explanation",
        "timestamp": datetime.now().isoformat(),
        "explanations_count": len(explanations),
        "ai_provider": ai_provider,
        "model_name": model_name,
        "prompt_version": "v1.2",
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
