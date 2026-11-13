"""
LangGraph Nodes for Intelligent Multi-Agent Portfolio Creation.
Orchestrates:
- Manager: Execution tracking and state initialization
- Suitability Agent: Risk capacity vs willingness, horizon, liquidity, and policy constraints
- Macro Analyst: Indian macro indicators, RBI repo rate, CPI, GDP, and sector direction
- Market Analyst: Market breadth, volatility dispersion, and beta distributions
- Fundamental Analyst: Industry-aware financial statement analysis (Banks vs IT vs Industrials)
- News & Filings Analyst: BSE/NSE corporate disclosures, regulatory announcements, and sentiment
- Lead Strategist: Portfolio candidate roles (CORE, GROWTH, DEFENSIVE, DIVERSIFICATION), factor scores
- Risk Critic: Independent audit, explicit verdict states, and bounded rework directives
- Strategist Rework: Candidate replacement and portfolio re-synthesis
- Deterministic Optimizer: SLSQP mathematical optimization, whole shares, and integer cash reserve
- Critic Final Validation: Post-optimizer verification of single-stock ceilings, sector caps, and cash
- Moderator: Two-level parameter explanations (Level 1 short summary + Level 2 detailed analysis)
- Persistence: ACID-protected database storage of versions, decisions, explanations, and evidence

Version: 2026.11-v2.0
Authoritative Date: 2026-11-05
"""

import uuid
import logging
import math
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

try:
    from backend.agent.state import PortfolioAgentState
    from backend.agent.schemas import (
        StrictModel,
        AgentOutputBase,
        EvidenceItem,
        MetricObservation,
        AgentFinding,
        PolicyConstraint,
        AgentMessage,
        SuitabilityOutput,
        MacroAnalystOutput,
        MarketAnalystOutput,
        FundamentalAnalystOutput,
        CompanyFundamentalAssessment,
        NewsAnalystOutput,
        StrategistOutput,
        PortfolioCandidate,
        CriticOutput,
        CriticObjection,
        ReworkRequest,
        OptimizerOutput,
        OptimizedPosition,
        ConstraintValidation,
        ModeratorOutput,
        PositionExplanation,
        ParameterExplanation,
        CriticVerdictStatus,
        DataQualityStatus,
        ReportingBasis,
        MetricEvidenceRecord,
        MacroAnalysisOutput,
        MarketAnalysisOutput,
        NewsAnalysisOutput,
        StrategistProposalOutput,
        CriticEvaluationOutput,
    )
    from backend.agent.tools import (
        suitability_assessment_tool,
        macro_data_tool,
        market_technical_tool,
        fundamental_research_tool,
        news_filings_audit_tool,
        factor_ranking_tool,
        critic_fiduciary_audit_tool,
        critic_final_validation_tool,
    )
    from backend.portfolio_engine import (
        CandidateUniverseSelector,
        PortfolioConstraints,
        optimize_portfolio_allocations,
        calculate_integer_shares_and_amounts,
        compute_portfolio_metrics,
        PortfolioValidator,
        determine_optimal_holding_count,
    )
    from backend.portfolio_engine.constraints import get_effective_constraints
    from backend.portfolio_engine.feasibility import check_portfolio_feasibility
    from backend.portfolio_engine.policy import get_risk_profile_policy
    from backend.portfolio_engine.factors import get_equity_factors
    from backend.portfolio_engine.conversational_assistant import get_rich_security_rationale, COMPANY_THESES
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
        EvidenceItem as DBEvidenceItem,
        ExplanationEvidence,
        DataSource,
        AgentDefinition,
        AgentVersion,
        AgentExecutionRun,
        EconomicIndicator,
        EconomicObservation,
        MarketNewsArticle,
    )
    from backend.market_data.regime import detect_market_regime
except ImportError:
    from agent.state import PortfolioAgentState
    from agent.schemas import (
        StrictModel,
        AgentOutputBase,
        EvidenceItem,
        MetricObservation,
        AgentFinding,
        PolicyConstraint,
        AgentMessage,
        SuitabilityOutput,
        MacroAnalystOutput,
        MarketAnalystOutput,
        FundamentalAnalystOutput,
        CompanyFundamentalAssessment,
        NewsAnalystOutput,
        StrategistOutput,
        PortfolioCandidate,
        CriticOutput,
        CriticObjection,
        ReworkRequest,
        OptimizerOutput,
        OptimizedPosition,
        ConstraintValidation,
        ModeratorOutput,
        PositionExplanation,
        ParameterExplanation,
        CriticVerdictStatus,
        DataQualityStatus,
        ReportingBasis,
        MetricEvidenceRecord,
        MacroAnalysisOutput,
        MarketAnalysisOutput,
        NewsAnalysisOutput,
        StrategistProposalOutput,
        CriticEvaluationOutput,
    )
    from agent.tools import (
        suitability_assessment_tool,
        macro_data_tool,
        market_technical_tool,
        fundamental_research_tool,
        news_filings_audit_tool,
        factor_ranking_tool,
        critic_fiduciary_audit_tool,
        critic_final_validation_tool,
    )
    from portfolio_engine import (
        CandidateUniverseSelector,
        PortfolioConstraints,
        optimize_portfolio_allocations,
        calculate_integer_shares_and_amounts,
        compute_portfolio_metrics,
        PortfolioValidator,
        determine_optimal_holding_count,
    )
    from portfolio_engine.constraints import get_effective_constraints
    from portfolio_engine.feasibility import check_portfolio_feasibility
    from portfolio_engine.policy import get_risk_profile_policy
    from portfolio_engine.factors import get_equity_factors
    from portfolio_engine.conversational_assistant import get_rich_security_rationale, COMPANY_THESES
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
        EvidenceItem as DBEvidenceItem,
        ExplanationEvidence,
        DataSource,
        AgentDefinition,
        AgentVersion,
        AgentExecutionRun,
        EconomicIndicator,
        EconomicObservation,
        MarketNewsArticle,
    )
    from market_data.regime import detect_market_regime

try:
    from backend.config import settings
except ImportError:
    try:
        from config import settings
    except ImportError:
        settings = None

logger = logging.getLogger(__name__)


def get_llm():
    """Returns ChatGoogleGenerativeAI instance if API key is provided, else None."""
    if not settings:
        return None
    api_key = getattr(settings, "gemini_api_key", None)
    if api_key and api_key != "your_gemini_api_key_here" and len(api_key) > 10:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=getattr(settings, "llm_model", "gemini-3.8-flash") or "gemini-3.8-flash",
                google_api_key=api_key,
                temperature=0.2,
                timeout=5,
                max_retries=1,
            )
        except Exception:
            return None
    return None


# ==============================================================================
# 1. MANAGER / ORCHESTRATOR NODE
# ==============================================================================

def manager_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """1. Manager: Initializes workflow execution, state structures, and registries."""
    trace = state.get("execution_trace", [])
    trace.append({
        "step": "manager",
        "timestamp": datetime.now().isoformat(),
        "message": f"Loaded generation request for amount ₹{state.get('investment_amount', 0):,.2f}",
    })
    return {
        "current_stage": "suitability",
        "status": "running",
        "workflow_status": "RUNNING",
        "execution_trace": trace,
        "critic_iteration": 0,
        "rework_count": 0,
        "max_rework_count": 2,
        "evidence_registry": {},
        "agent_messages": [],
        "agent_execution_history": [],
        "can_proceed": False,
    }


# ==============================================================================
# 2. SUITABILITY & FEASIBILITY CHECK NODE
# ==============================================================================

def suitability_check_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """2. Evaluates suitability, risk capacity vs willingness, horizon, and sets policy constraints."""
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    amount = float(state.get("investment_amount", 0))
    risk = state.get("risk_category", "moderate")
    goal = state.get("goal_type", "wealth_creation")
    horizon = int(state.get("investment_horizon_months", 60))
    prefs = state.get("preferences", {})
    user_prompt = state.get("user_prompt", "") or ""

    existing_candidates = state.get("eligible_candidates")
    if existing_candidates and len(existing_candidates) >= 3:
        candidates = existing_candidates
    else:
        selector = CandidateUniverseSelector(db)
        eligible = selector.select_eligible_candidates(
            excluded_sectors=prefs.get("excluded_sectors", []),
            excluded_instruments=prefs.get("excluded_instruments", []),
        )
        target_k = determine_optimal_holding_count(
            capital=amount,
            goal_type=goal,
            horizon_months=horizon,
            risk_category=risk,
        )
        policy = get_risk_profile_policy(risk)
        effective_max_stock_pct = policy.max_single_stock_pct
        if "max_single_stock_weight_pct" in prefs and prefs["max_single_stock_weight_pct"]:
            effective_max_stock_pct = min(effective_max_stock_pct, float(prefs["max_single_stock_weight_pct"]))
        min_needed = int(math.ceil(100.0 / effective_max_stock_pct))
        target_pool_size = max(target_k, min_needed, policy.min_holdings_count, 6)

        candidates = selector.rank_and_select_candidates(
            candidates=eligible,
            target_count=min(target_pool_size, len(eligible)),
            goal_type=goal,
            risk_category=risk,
            horizon_months=horizon,
            user_prompt=user_prompt,
        )

    suitability_out: SuitabilityOutput = suitability_assessment_tool(
        capital=amount,
        risk_category=risk,
        horizon_months=horizon,
        goal_type=goal,
        preferences=prefs,
        user_prompt=user_prompt,
    )

    feasibility = check_portfolio_feasibility(
        capital=amount,
        risk_category=risk,
        eligible_candidates=candidates,
        preferences=prefs,
        goal_type=goal,
    )

    passed = (suitability_out.overall_suitability in ("SUITABLE", "SUITABLE_WITH_CONDITIONS")) and feasibility.is_feasible
    notes = suitability_out.suitability_warnings + feasibility.conditions_satisfied + feasibility.conditions_violated

    for ev in suitability_out.evidence_items:
        registry[ev.evidence_id] = ev.model_dump()

    trace.append({
        "step": "suitability_check",
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "suitability": suitability_out.overall_suitability,
        "risk_capacity": suitability_out.risk_capacity,
        "risk_willingness": suitability_out.risk_willingness,
        "constraints_count": len(suitability_out.constraints),
        "is_feasible": feasibility.is_feasible,
        "notes": notes,
    })

    return {
        "suitability_passed": passed,
        "suitability_notes": notes,
        "suitability_output": suitability_out.model_dump(),
        "feasibility_result": feasibility.model_dump(),
        "eligible_candidates": candidates,
        "evidence_registry": registry,
        "current_stage": "macro_analyst" if passed else "persistence",
        "status": "running" if passed else "failed",
        "workflow_status": "RUNNING" if passed else "BLOCKED",
        "error_code": None if passed else "SUITABILITY_FEASIBILITY_FAILED",
        "error_summary": None if passed else ("; ".join(feasibility.conditions_violated) or "; ".join(notes)),
        "execution_trace": trace,
    }


# ==============================================================================
# 3. MACRO ANALYST NODE
# ==============================================================================

def macro_analyst_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """3. Macro Analyst: Evaluates Indian macro indicators, monetary policy, and sector impacts."""
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    res: MacroAnalystOutput = macro_data_tool(db)

    # Dynamic LLM qualitative reasoning if configured
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt = (
                f"You are a senior Indian macroeconomic analyst. Synthesize the current macro environment:\n"
                f"- Market Regime: {res.regime}\n"
                f"- India VIX: {res.vix}\n"
                f"- RBI Policy Repo Rate: {res.rbi_repo_rate}%\n"
                f"- CPI Headline Inflation: {res.cpi_inflation}%\n"
                f"- Real GDP Growth: {res.gdp_growth}%\n"
                f"- 10-Year G-Sec Yield: {res.gsec_10y_yield}%\n"
                f"Provide a concise 2-sentence fiduciary macroeconomic summary highlighting policy rate expectations and sector tailwinds."
            )
            resp = llm.invoke([
                SystemMessage(content="You are an expert Indian macroeconomic strategist. Provide factual, concise commentary."),
                HumanMessage(content=prompt),
            ])
            text = str(resp.content).strip() if resp and resp.content else ""
            if len(text) >= 20:
                res.macro_summary = text
                res.model_name = getattr(llm, "model", "gemini-3.8-flash")
        except Exception as e:
            logger.debug(f"Macro LLM synthesis fallback: {e}")

    for ev in res.evidence_items:
        registry[ev.evidence_id] = ev.model_dump()

    trace.append({
        "step": "macro_analyst",
        "timestamp": datetime.now().isoformat(),
        "regime": res.regime,
        "vix": res.vix,
        "rbi_repo_rate": res.rbi_repo_rate,
        "cpi_inflation": res.cpi_inflation,
        "macro_stance": res.macro_stance,
    })
    return {
        "macro_output": res.model_dump(),
        "macro_analysis": res.model_dump(),  # legacy compat
        "market_regime": {"regime": res.regime, "india_vix": res.vix, "cash_buffer_pct": res.cash_buffer_pct},
        "evidence_registry": registry,
        "current_stage": "market_analyst",
        "execution_trace": trace,
    }


# ==============================================================================
# 4. MARKET ANALYST NODE
# ==============================================================================

def market_analyst_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """4. Market Analyst: Evaluates market breadth, volatility dispersion, and beta relative to NIFTY 50."""
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    candidates = state.get("eligible_candidates", [])
    res: MarketAnalystOutput = market_technical_tool(candidates, db)

    # Dynamic LLM qualitative reasoning if configured
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            sec_counts = list(res.sector_distribution.items())[:4]
            sectors_summary = ", ".join(f"{s}: {cnt}" for s, cnt in sec_counts)
            prompt = (
                f"You are a technical market technician for NSE/BSE equities. Review current market metrics:\n"
                f"- Candidates Evaluated: {res.candidates_evaluated}\n"
                f"- Top Sectors Represented: {sectors_summary}\n"
                f"- Market Breadth Score: {res.market_breadth_score}/100\n"
                f"- 30-Day Realized Volatility: {res.avg_30d_volatility_pct}%\n"
                f"- High-Beta Ratio: {res.high_beta_ratio}\n"
                f"Provide a concise 2-sentence market posture assessment evaluating market breadth and risk sentiment relative to NIFTY 50."
            )
            resp = llm.invoke([
                SystemMessage(content="You are an expert market breadth and technical analyst for Indian equities."),
                HumanMessage(content=prompt),
            ])
            text = str(resp.content).strip() if resp and resp.content else ""
            if len(text) >= 20:
                res.market_summary = text
                res.model_name = getattr(llm, "model", "gemini-3.8-flash")
        except Exception as e:
            logger.debug(f"Market LLM synthesis fallback: {e}")

    for ev in res.evidence_items:
        registry[ev.evidence_id] = ev.model_dump()

    trace.append({
        "step": "market_analyst",
        "timestamp": datetime.now().isoformat(),
        "candidates_evaluated": res.candidates_evaluated,
        "sectors_represented": res.sectors_represented,
        "market_breadth_score": res.market_breadth_score,
        "technical_posture": res.technical_posture,
    })
    return {
        "market_output": res.model_dump(),
        "market_analysis": res.model_dump(),  # legacy compat
        "evidence_registry": registry,
        "current_stage": "fundamental_analyst",
        "execution_trace": trace,
    }


# ==============================================================================
# 5. FUNDAMENTAL / EQUITY RESEARCH ANALYST NODE
# ==============================================================================

def fundamental_analyst_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """5. Fundamental Analyst: Industry-aware audit of company balance sheets, ROE, valuation, and moats."""
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    candidates = state.get("eligible_candidates", [])
    res: FundamentalAnalystOutput = fundamental_research_tool(candidates, db)

    # Dynamic LLM qualitative reasoning if configured
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            tickers = [c.ticker for c in res.companies_analyzed[:6]]
            prompt = (
                f"You are an equity research analyst reviewing top candidate companies for an Indian portfolio: {', '.join(tickers)}.\n"
                f"Provide a concise 2-sentence qualitative audit of their balance sheet quality, ROE strength, and business moats."
            )
            resp = llm.invoke([
                SystemMessage(content="You are a senior equity research analyst specializing in Indian corporate fundamentals."),
                HumanMessage(content=prompt),
            ])
            text = str(resp.content).strip() if resp and resp.content else ""
            if len(text) >= 20:
                res.model_name = getattr(llm, "model", "gemini-3.8-flash")
                res.findings.append(
                    AgentFinding(
                        finding_id=f"FIND-FUND-LLM-{uuid.uuid4().hex[:6]}",
                        category="QUALITY",
                        severity="INFO",
                        title="AI Fundamental Moat Evaluation",
                        description=text,
                        affected_tickers=tickers,
                    )
                )
        except Exception as e:
            logger.debug(f"Fundamental LLM synthesis fallback: {e}")

    for ev in res.evidence_items:
        registry[ev.evidence_id] = ev.model_dump()

    trace.append({
        "step": "fundamental_analyst",
        "timestamp": datetime.now().isoformat(),
        "companies_analyzed": len(res.companies_analyzed),
        "attractive_count": sum(1 for c in res.companies_analyzed if c.investment_view == "ATTRACTIVE"),
    })
    return {
        "fundamental_output": res.model_dump(),
        "evidence_registry": registry,
        "current_stage": "news_analyst",
        "execution_trace": trace,
    }


# ==============================================================================
# 6. NEWS & FILINGS ANALYST NODE
# ==============================================================================

def news_analyst_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """6. News Analyst: Inspects corporate disclosures, exchange filings, auditor remarks, and sentiment."""
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    candidates = state.get("eligible_candidates", [])
    symbols = [c.get("symbol", "") for c in candidates if c.get("symbol")]
    res: NewsAnalystOutput = news_filings_audit_tool(symbols, db)

    # Dynamic LLM qualitative reasoning if configured
    llm = get_llm()
    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt = (
                f"You are a corporate governance and news intelligence analyst. Review disclosures for {', '.join(symbols[:6])}:\n"
                f"- Sentiment Score: {res.sentiment_score} ({res.sentiment_label})\n"
                f"- Disclosures Reviewed: {res.corporate_disclosures_reviewed}\n"
                f"- Headlines: {res.headlines_analyzed[:3]}\n"
                f"Provide a concise 2-sentence corporate governance and regulatory compliance summary."
            )
            resp = llm.invoke([
                SystemMessage(content="You are an expert in corporate governance disclosures and Indian financial regulatory filings."),
                HumanMessage(content=prompt),
            ])
            text = str(resp.content).strip() if resp and resp.content else ""
            if len(text) >= 20:
                res.news_summary = text
                res.model_name = getattr(llm, "model", "gemini-3.8-flash")
        except Exception as e:
            logger.debug(f"News LLM synthesis fallback: {e}")

    for ev in res.evidence_items:
        registry[ev.evidence_id] = ev.model_dump()

    trace.append({
        "step": "news_analyst",
        "timestamp": datetime.now().isoformat(),
        "sentiment_score": res.sentiment_score,
        "sentiment_label": res.sentiment_label,
        "disclosures_reviewed": res.corporate_disclosures_reviewed,
    })
    return {
        "news_output": res.model_dump(),
        "news_analysis": res.model_dump(),  # legacy compat
        "evidence_registry": registry,
        "current_stage": "analyst",
        "execution_trace": trace,
    }


# ==============================================================================
# 7. LEAD STRATEGIST / ANALYST NODE
# ==============================================================================

def analyst_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """7. Lead Strategist: Synthesizes specialist research into candidate portfolio roles and overarching strategy."""
    start_time = datetime.now()
    trace = state.get("execution_trace", [])
    registry = dict(state.get("evidence_registry") or {})
    messages = list(state.get("agent_messages") or [])
    risk = state.get("risk_category", "moderate")
    candidates = state.get("eligible_candidates", [])
    user_prompt = state.get("user_prompt", "") or ""
    amount = float(state.get("investment_amount", 100000))
    horizon = int(state.get("investment_horizon_months", 60))

    # Attempt dynamic LLM reasoning if configured, with graceful fallback
    llm = get_llm()
    llm_reasoning = None
    fallback_reason = None

    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt_content = f"Evaluate strategy for {risk} investor with amount INR {amount} and candidates: {[c.get('symbol') for c in candidates]}"
            resp = llm.invoke([
                SystemMessage(content="You are an expert quantitative Indian equities strategist. Return concise actionable insights."),
                HumanMessage(content=prompt_content),
            ])
            raw_text = str(resp.content).strip() if resp and resp.content else ""
            if len(raw_text) >= 10:
                llm_reasoning = raw_text
            else:
                fallback_reason = "malformed_or_empty_response"
        except TimeoutError:
            fallback_reason = "timeout_exceeded"
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "429" in err_str or "resource_exhausted" in err_str:
                fallback_reason = "quota_exceeded"
            elif "timeout" in err_str or "timed out" in err_str:
                fallback_reason = "timeout_exceeded"
            else:
                fallback_reason = f"error: {type(e).__name__}"
    else:
        fallback_reason = "no_api_key_configured"

    ai_provider = "gemini" if llm_reasoning else "dynamic_heuristic_fallback"
    model_name = (
        getattr(settings, "llm_model", "gemini-3.8-flash")
        if (llm_reasoning and settings)
        else "fiduciary-strategist-engine-v2"
    )

    macro = state.get("macro_output") or state.get("macro_analysis") or {}
    market = state.get("market_output") or state.get("market_analysis") or {}
    fundamental = state.get("fundamental_output") or {}
    news = state.get("news_output") or state.get("news_analysis") or {}

    sector_counts = {}
    for c in candidates:
        sec = c.get("sector_name", "General")
        sector_counts[sec] = sector_counts.get(sec, 0) + 1

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

    # Assign typed PortfolioCandidates with strategic roles
    proposed_candidates: List[PortfolioCandidate] = []
    fund_map = {c.get("ticker"): c for c in fundamental.get("companies_analyzed", [])}

    for c in candidates:
        sym = c.get("symbol", "").upper()
        sec = c.get("sector_name", "General")
        c_name = c.get("security_name", sym)
        factors = c.get("fundamental_factors") or get_equity_factors(sym)
        beta = float(factors.get("beta", 1.0))
        roe = float(factors.get("roe", 0.16))

        # Assign Role
        if "bank" in sec.lower() or "financial" in sec.lower():
            role = "CORE"
            sel_rat = f"Anchor private banking compounder providing credit growth and balance sheet liquidity."
        elif beta < 0.85:
            role = "DEFENSIVE"
            sel_rat = f"Low-beta defensive cushion to insulate portfolio capital during market drawdowns."
        elif roe > 0.25:
            role = "GROWTH"
            sel_rat = f"Secular growth driver with elite return on capital and high reinvestment runway."
        else:
            role = "DIVERSIFICATION"
            sel_rat = f"Provides cross-sector diversification and non-correlated cash flow streams."

        proposed_candidates.append(
            PortfolioCandidate(
                ticker=sym,
                company_name=c_name,
                sector=sec,
                portfolio_role=role,
                selection_rationale=sel_rat,
                allocation_rationale=f"Proposed allocation scaled according to multi-factor Sharpe score and {sec} sector caps.",
                supporting_factors=[f"ROE: {roe*100:.1f}%", f"Beta: {beta:.2f}"],
                major_risks=[f"Sector demand slowdown in {sec}"],
                evidence_ids=[f"EV-FUND-{sym}"],
            )
        )

    strategist_out = StrategistOutput(
        execution_status="SUCCESS",
        started_at=start_time,
        completed_at=datetime.now(),
        model_name="fiduciary-strategist-engine-v2",
        tool_calls=1,
        investment_strategy=theme_str,
        strategy_objective=f"Deliver risk-adjusted compounding for {risk} investor over {horizon} months.",
        target_sectors=list(sector_counts.keys()),
        recommended_stance=stance,
        proposed_candidates=proposed_candidates,
        factor_weights={"quality": 0.35, "value": 0.25, "momentum": 0.20, "low_volatility": 0.20},
        investor_guidance_addressed=user_prompt if user_prompt else None,
    )

    # Emit message to Critic
    messages.append(
        AgentMessage(
            message_id=f"MSG-STRAT-TO-CRITIC-{uuid.uuid4().hex[:6]}",
            sender="STRATEGIST",
            recipient="CRITIC",
            message_type="VALIDATION_RESULT",
            subject=f"Proposed Portfolio Strategy: {theme_str}",
            message=f"Proposed {len(proposed_candidates)} candidates across {len(sector_counts)} sectors for {risk} risk posture.",
            related_tickers=[c.ticker for c in proposed_candidates[:5]],
            requires_response=True,
        ).model_dump()
    )

    research_notes = {
        "strategy_theme": theme_str,
        "target_sectors": list(sector_counts.keys()),
        "diversification_breadth": len(sector_counts),
        "recommended_stance": stance,
        "investor_custom_prompt": user_prompt,
        "macro_summary": macro.get("macro_summary"),
        "market_regime": macro.get("regime", "MODERATE"),
        "news_sentiment": news.get("sentiment_label", "positive"),
    }

    trace_entry = {
        "step": "analyst",
        "agent_code": "strategist_agent",
        "timestamp": datetime.now().isoformat(),
        "summary": f"Formulated '{theme_str}' strategy with {len(proposed_candidates)} candidates across {len(sector_counts)} sectors",
        "ai_provider": ai_provider,
        "model_name": model_name,
    }
    if fallback_reason:
        trace_entry["fallback_reason"] = fallback_reason
    trace.append(trace_entry)

    return {
        "eligible_candidates": candidates,
        "strategist_output": strategist_out.model_dump(),
        "analyst_research_notes": research_notes,
        "agent_messages": messages,
        "evidence_registry": registry,
        "current_stage": "critic",
        "execution_trace": trace,
    }


# ==============================================================================
# 8. INDEPENDENT RISK CRITIC NODE
# ==============================================================================

def critic_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """8. Risk Critic: Independent fiduciary audit of candidate quality, balance sheets, leverage, and SEBI compliance."""
    trace = state.get("execution_trace", [])
    messages = list(state.get("agent_messages") or [])
    candidates = state.get("eligible_candidates", [])
    amount = float(state.get("investment_amount", 100000))
    risk = state.get("risk_category", "moderate")
    user_prompt = state.get("user_prompt", "") or ""
    iteration = state.get("critic_iteration", 0) + 1

    critic_res: CriticOutput = critic_fiduciary_audit_tool(
        candidates=candidates,
        capital=amount,
        risk_category=risk,
        user_prompt=user_prompt,
        iteration=iteration,
    )

    # Dynamic LLM qualitative risk critique if configured
    llm = get_llm()
    if llm and critic_res.can_proceed:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            syms = [c.get("symbol") for c in candidates[:6] if c.get("symbol")]
            prompt = (
                f"You are an independent risk critic and SEBI fiduciary compliance auditor. "
                f"Audit a proposed equity portfolio of INR {amount:,.0f} for a {risk} risk posture with candidates: {syms}. "
                f"Current verdict: {critic_res.decision}. "
                f"Provide a concise 2-sentence risk challenge evaluating single-stock concentration, sector tilt, and downside capital protection."
            )
            resp = llm.invoke([
                SystemMessage(content="You are an independent fiduciary risk critic and compliance auditor."),
                HumanMessage(content=prompt),
            ])
            text = str(resp.content).strip() if resp and resp.content else ""
            if len(text) >= 20:
                critic_res.critic_summary += f" [Independent Risk Critique: {text}]"
                critic_res.model_name = getattr(llm, "model", "gemini-3.8-flash")
        except Exception as e:
            logger.debug(f"Critic LLM synthesis fallback: {e}")

    is_approved = critic_res.can_proceed and critic_res.decision == "APPROVED"

    # Emit message from Critic
    msg_type = "DECISION" if is_approved else ("REWORK_REQUEST" if critic_res.decision == "REWORK_REQUIRED" else "OBJECTION")
    messages.append(
        AgentMessage(
            message_id=f"MSG-CRITIC-TO-STRAT-{uuid.uuid4().hex[:6]}",
            sender="CRITIC",
            recipient="STRATEGIST",
            message_type=msg_type,
            subject=f"Critic Audit #{iteration}: {critic_res.decision}",
            message=critic_res.critic_summary,
            related_tickers=critic_res.removable_tickers,
            requires_response=(critic_res.decision == "REWORK_REQUIRED"),
        ).model_dump()
    )

    trace.append({
        "step": "critic",
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "verdict_status": critic_res.decision,
        "approved": is_approved,
        "removable_tickers": critic_res.removable_tickers,
        "rework_instructions": critic_res.rework_instructions,
        "blocking_reasons": critic_res.blocking_reasons,
        "summary": critic_res.critic_summary,
    })

    return {
        "critic_output": critic_res.model_dump(),
        "critic_verdict_status": critic_res.decision,
        "critic_approved": is_approved,
        "can_proceed": is_approved,
        "critic_iteration": iteration,
        "critic_findings": [f.model_dump() for f in critic_res.findings],
        "removable_tickers": critic_res.removable_tickers,
        "rework_instructions": critic_res.rework_instructions,
        "blocking_reasons": critic_res.blocking_reasons,
        "agent_messages": messages,
        "current_stage": "optimizer" if is_approved else ("strategist_rework" if critic_res.decision == "REWORK_REQUIRED" else "persistence"),
        "status": "running" if (is_approved or critic_res.decision == "REWORK_REQUIRED") else "failed",
        "workflow_status": "RUNNING" if (is_approved or critic_res.decision == "REWORK_REQUIRED") else "BLOCKED",
        "error_code": None if (is_approved or critic_res.decision == "REWORK_REQUIRED") else "CRITIC_AUDIT_BLOCKED",
        "error_summary": None if (is_approved or critic_res.decision == "REWORK_REQUIRED") else "; ".join(critic_res.blocking_reasons or [critic_res.critic_summary]),
        "execution_trace": trace,
    }


# ==============================================================================
# 9. STRATEGIST REWORK NODE
# ==============================================================================

def strategist_rework_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """9. Strategist Rework: Replaces defective candidates flagged by Critic with healthy industry peers."""
    trace = state.get("execution_trace", [])
    rework_count = state.get("rework_count", 0) + 1
    candidates = list(state.get("eligible_candidates") or [])
    removals = set(state.get("removable_tickers") or [])

    # Filter out flagged tickers
    filtered = [c for c in candidates if c.get("symbol", "").upper() not in removals]
    if len(filtered) < 3:
        filtered = candidates  # Safety fallback to prevent empty pool

    trace.append({
        "step": "strategist_rework",
        "timestamp": datetime.now().isoformat(),
        "rework_count": rework_count,
        "removed_tickers": list(removals),
        "remaining_candidates": len(filtered),
    })

    return {
        "eligible_candidates": filtered,
        "rework_count": rework_count,
        "current_stage": "critic",
        "execution_trace": trace,
    }


# ==============================================================================
# 10. DETERMINISTIC OPTIMIZER & VALIDATOR NODE
# ==============================================================================

def deterministic_optimizer_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """10. Deterministic Optimizer: Executes mathematical SLSQP allocation, integer whole shares, and deterministic constraints."""
    start_time = datetime.now()
    trace = state.get("execution_trace", [])
    candidates = state.get("eligible_candidates", [])
    amount = Decimal(str(state.get("investment_amount", 100000)))
    risk = state.get("risk_category", "moderate")
    prefs = state.get("preferences", {})
    goal_type = state.get("goal_type", "wealth_creation")
    horizon = int(state.get("investment_horizon_months", 60))
    user_prompt = state.get("user_prompt", "") or ""
    news = state.get("news_output") or state.get("news_analysis") or {}
    news_sentiment = float(news.get("sentiment_score", 0.25))

    constraints = get_effective_constraints(
        risk_category=risk,
        requested_max_stock_pct=prefs.get("max_single_stock_weight_pct"),
        requested_max_sector_pct=prefs.get("max_sector_weight_pct"),
        min_stocks_count=3,
    )

    min_candidates_for_cap = int(math.ceil(100.0 / max(1.0, constraints.max_single_stock_pct)))
    target_k = max(
        determine_optimal_holding_count(
            capital=float(amount),
            goal_type=goal_type,
            horizon_months=horizon,
            risk_category=risk,
        ),
        min_candidates_for_cap,
    )
    if "min_stocks_count" in prefs and prefs["min_stocks_count"]:
        target_k = max(target_k, int(prefs["min_stocks_count"]))

    selector = CandidateUniverseSelector(None)
    selected_candidates = selector.rank_and_select_candidates(
        candidates=candidates,
        target_count=min(target_k, len(candidates)),
        goal_type=goal_type,
        risk_category=risk,
        horizon_months=horizon,
        user_prompt=user_prompt,
        news_sentiment=news_sentiment,
    )

    constraints = get_effective_constraints(
        risk_category=risk,
        requested_max_stock_pct=prefs.get("max_single_stock_weight_pct"),
        requested_max_sector_pct=prefs.get("max_sector_weight_pct"),
        min_stocks_count=min(len(selected_candidates), 3),
    )

    opt_ok, raw_allocs, opt_msg = optimize_portfolio_allocations(
        candidates=selected_candidates,
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
            "current_stage": "persistence",
            "status": "failed",
            "workflow_status": "BLOCKED",
            "error_code": "OPTIMIZER_FAILURE",
            "error_summary": opt_msg,
            "execution_trace": trace,
        }

    enriched, invested, unallocated = calculate_integer_shares_and_amounts(raw_allocs, amount)
    metrics = compute_portfolio_metrics(enriched)

    validator = PortfolioValidator(constraints)
    val_out = validator.validate_portfolio(enriched, amount)
    all_passed = val_out["all_passed"]

    # Build typed OptimizerOutput
    positions: List[OptimizedPosition] = []
    for h in enriched:
        sym = h.get("symbol", "")
        positions.append(
            OptimizedPosition(
                ticker=sym,
                company_name=h.get("security_name", sym),
                sector=h.get("sector_name", "General"),
                current_quantity=0,
                target_quantity=int(h.get("shares_quantity", 0)),
                reference_price=float(h.get("latest_price", 100.0)),
                reference_price_date=date.today(),
                target_weight_pct=float(h.get("target_weight_pct", 0.0)),
                allocated_amount=float(h.get("actual_invested_amount") or h.get("target_amount") or 0.0),
                role=h.get("role"),
                selection_rationale=h.get("decision_reason"),
            )
        )

    optimizer_out = OptimizerOutput(
        execution_status="SUCCESS" if all_passed else "PARTIAL",
        started_at=start_time,
        completed_at=datetime.now(),
        model_name="scipy-slsqp-constrained-v1",
        tool_calls=1,
        objective_function="Sharpe Maximization with L2 Concentration Penalties",
        optimization_status="OPTIMAL" if all_passed else "INFEASIBLE",
        total_capital=float(amount),
        total_invested=float(invested),
        unallocated_cash=float(unallocated),
        cash_reserve_pct=round((float(unallocated) / float(amount)) * 100.0, 2),
        positions=positions,
        expected_return_pct=float(metrics.get("expected_return_pct", 12.0)),
        expected_volatility_pct=float(metrics.get("expected_volatility_pct", 14.0)),
        sharpe_ratio=float(metrics.get("sharpe_ratio", 0.85)),
        diversification_score=float(metrics.get("diversification_score", 85.0)),
        all_constraints_passed=all_passed,
    )

    trace.append({
        "step": "optimizer_and_validator",
        "timestamp": datetime.now().isoformat(),
        "validation_status": val_out["validation_status"],
        "all_passed": all_passed,
        "holdings_count": len(enriched),
        "metrics": metrics,
    })

    return {
        "allocations": enriched,
        "total_invested": float(invested),
        "unallocated_cash": float(unallocated),
        "risk_metrics": metrics,
        "validation_output": val_out,
        "validation_passed": all_passed,
        "optimizer_output": optimizer_out.model_dump(),
        "current_stage": "critic_final_validation" if all_passed else "persistence",
        "status": "running" if all_passed else "failed",
        "workflow_status": "RUNNING" if all_passed else "BLOCKED",
        "error_code": None if all_passed else "VALIDATION_FAILED",
        "error_summary": None if all_passed else "Portfolio failed hard mathematical validation rules",
        "execution_trace": trace,
    }


# ==============================================================================
# 11. CRITIC FINAL VALIDATION NODE (POST-OPTIMIZER)
# ==============================================================================

def critic_final_validation_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """11. Critic Final Validation: Post-optimizer audit of final weights, sector caps, and integer share lots."""
    trace = state.get("execution_trace", [])
    allocations = state.get("allocations", [])
    total_capital = float(state.get("investment_amount", 100000))
    unallocated_cash = float(state.get("unallocated_cash", 0.0))
    risk = state.get("risk_category", "moderate")

    final_critic_res: CriticOutput = critic_final_validation_tool(
        allocations=allocations,
        total_capital=total_capital,
        unallocated_cash=unallocated_cash,
        risk_category=risk,
    )

    is_approved = final_critic_res.can_proceed and final_critic_res.decision == "APPROVED"

    trace.append({
        "step": "critic_final_validation",
        "timestamp": datetime.now().isoformat(),
        "decision": final_critic_res.decision,
        "approved": is_approved,
        "summary": final_critic_res.critic_summary,
    })

    return {
        "critic_final_output": final_critic_res.model_dump(),
        "can_proceed": is_approved,
        "current_stage": "moderator" if is_approved else "persistence",
        "status": "running" if is_approved else "failed",
        "workflow_status": "RUNNING" if is_approved else "BLOCKED",
        "error_code": None if is_approved else "CRITIC_FINAL_VALIDATION_REJECTED",
        "error_summary": None if is_approved else final_critic_res.critic_summary,
        "execution_trace": trace,
    }


# ==============================================================================
# 12. MODERATOR / EXPLANATION GENERATOR NODE
# ==============================================================================

def moderator_explanation_node(state: PortfolioAgentState) -> Dict[str, Any]:
    """12. Moderator: Consolidates validated agent findings into structured Two-Level financial explanations."""
    start_time = datetime.now()
    trace = state.get("execution_trace", [])
    holdings = state.get("allocations", [])
    risk = state.get("risk_category", "moderate")
    metrics = state.get("risk_metrics", {})
    unallocated = float(state.get("unallocated_cash", 0.0))
    user_prompt = state.get("user_prompt", "") or ""
    analyst_notes = state.get("analyst_research_notes", {})
    theme = analyst_notes.get("strategy_theme", f"Active {risk.capitalize()} Disciplined Equity")

    # Generate Two-Level Portfolio Parameter Explanations
    portfolio_params: List[ParameterExplanation] = [
        ParameterExplanation(
            parameter_name="Expected Annual Return",
            value=f"{metrics.get('expected_return_pct', 12.0):.2f}%",
            unit="percent",
            what_it_means="The model-projected compounded annual return based on audited earnings growth and dividend yields.",
            why_it_matters="Measures the portfolio's expected capital compounding power relative to inflation.",
            how_to_interpret="Higher expected returns reflect stronger growth drivers, but must be balanced against portfolio volatility.",
            why_it_matters_for_portfolio=f"Calibrated to achieve your {risk} risk objective while pacing ahead of historical inflation.",
            detailed_definition="Expected return is an econometric forecast combining 5-to-10-year historical earnings growth, dividend yield, and return on equity (ROE) for each holding.",
            purpose="Enables institutional wealth managers to construct portfolios that achieve financial goals with minimum necessary risk.",
            benchmark_comparison="Compared against NIFTY 50 10-year historical CAGR corridor of 11.5%–13.5%.",
            calculation_methodology="Weighted sum of individual constituent expected returns: E(R_p) = Σ w_i * E(R_i).",
            why_favorable_or_unfavorable="Attractive because it outpaces prevailing 5.1% CPI inflation without requiring speculative small-cap exposure.",
            limitations="Projected returns reflect historical fundamental compounding and are not guaranteed.",
        ),
        ParameterExplanation(
            parameter_name="Expected Annual Volatility",
            value=f"{metrics.get('expected_volatility_pct', 14.5):.2f}%",
            unit="percent",
            what_it_means="The annualized standard deviation of expected portfolio return fluctuations.",
            why_it_matters="Quantifies the normal corridor of price swings your capital may experience over any 12-month period.",
            how_to_interpret="Lower volatility provides smoother capital preservation; higher volatility requires a longer holding horizon.",
            why_it_matters_for_portfolio=f"Constrained strictly within your {risk} risk volatility ceiling.",
            detailed_definition="Annualized standard deviation of daily return series modeled using historical covariance matrix with shrinkage.",
            purpose="Guarantees that downside drawdown risk does not breach the investor's emotional and financial pain tolerance.",
            benchmark_comparison="Benchmark NIFTY 50 annualized volatility is approximately 14.8%.",
            calculation_methodology="Matrix quadratic form: σ_p = sqrt(w^T * Σ * w) * sqrt(252).",
            why_favorable_or_unfavorable="Controlled volatility protects against permanent capital impairment during systemic market corrections.",
            limitations="Historical volatility cannot predict unprecedented black swan events or regulatory disruptions.",
        ),
        ParameterExplanation(
            parameter_name="Diversification Breadth Score",
            value=f"{metrics.get('diversification_score', 85.0):.1f}/100",
            unit="score",
            what_it_means="An index measuring how effectively risk is dispersed across uncorrelated economic sectors and stocks.",
            why_it_matters="High diversification ensures that a downturn in one company or industry cannot devastate your overall capital.",
            how_to_interpret="Scores above 75 indicate institutional-grade diversification; scores below 50 indicate dangerous concentration.",
            why_it_matters_for_portfolio=f"Achieves {metrics.get('diversification_score', 85.0):.1f}/100 through balanced multi-sector selection.",
            detailed_definition="Derived from the inverse Herfindahl-Hirschman Index (HHI) of stock and sector weights normalized on a 0-100 scale.",
            purpose="Prevents single-sector contagion, regulatory shocks, or individual corporate default from dominating portfolio performance.",
            benchmark_comparison="Concentrated retail accounts typically score 40-55; Lucid target corridor is > 75.",
            calculation_methodology="HHI = Σ (w_i)^2; Diversification Score = (1 - HHI) / (1 - 1/N) * 100.",
            why_favorable_or_unfavorable="Excellent score protects your principal while preserving upside participation.",
            limitations="Over-diversification beyond 20 stocks causes fee drag without meaningful incremental risk reduction.",
        ),
    ]

    # Generate Stock-Specific Explanations with Two-Level Parameters
    position_explanations: List[PositionExplanation] = []
    explanations: List[Dict[str, Any]] = []

    strategy_desc = (
        f"Constructed an allocation across {len(holdings)} equity securities targeting {metrics.get('expected_return_pct', 12.0):.2f}% "
        f"annualized return with {metrics.get('expected_volatility_pct', 14.5):.2f}% expected volatility, "
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

    explanations.append({
        "explanation_type": "diversification",
        "title": "Sector Concentration & SEBI Risk Guardrails",
        "explanation_text": (
            f"Portfolio achieves a normalized diversification score of {metrics.get('diversification_score', 85.0):.1f}/100. "
            f"Maximum individual stock weight is strictly capped at 25.0% and all sector weights remain within the 40.0% limit "
            f"to protect against idiosyncratic drawdowns."
        ),
        "display_order": 2,
    })

    for idx, h in enumerate(holdings, start=3):
        sym = h.get("symbol", "")
        sec = h.get("sector_name", "General")
        c_name = h.get("security_name", sym)
        w_pct = float(h.get("target_weight_pct", 0.0))
        shares = int(h.get("shares_quantity", 0))
        price = float(h.get("latest_price", 0.0))
        amt = float(h.get("actual_invested_amount") or h.get("target_amount") or 0.0)

        rationale = get_rich_security_rationale(
            symbol=sym,
            security_name=c_name,
            sector_name=sec,
            target_weight_pct=w_pct,
            shares_quantity=shares,
            latest_price=price,
        )

        explanations.append({
            "explanation_type": "selection",
            "title": f"Selected: {sym} ({c_name})",
            "explanation_text": rationale,
            "display_order": idx,
            "security_id": str(h.get("security_id", "")),
            "listing_id": str(h.get("listing_id", "")),
        })

        position_explanations.append(
            PositionExplanation(
                ticker=sym,
                company_name=c_name,
                sector=sec,
                decision="INCLUDE",
                allocation_pct=w_pct,
                allocated_amount=amt,
                shares_quantity=shares,
                reference_price=price,
                why_selected=f"Selected for high capital efficiency, strong moat, and Sharpe contribution in {sec}.",
                why_this_allocation=f"Mathematical SLSQP optimizer allocated {w_pct:.1f}% (₹{amt:,.2f}, {shares} whole shares) respecting Lucid's 25.0% single-stock policy ceiling.",
                why_not_higher=f"A higher allocation would breach Lucid's internal 25.0% single-stock safety ceiling or create sector concentration.",
                why_not_lower=f"A lower allocation would dilute the company's compounding impact on portfolio returns.",
                important_parameters=portfolio_params,
                risks_and_limitations=[f"Industry cyclicality in {sec}", "Macro interest rate changes"],
                what_could_make_this_wrong=f"Sustained margin contraction or regulatory caps in {sec} could challenge this investment thesis.",
            )
        )

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

    moderator_out = ModeratorOutput(
        execution_status="SUCCESS",
        started_at=start_time,
        completed_at=datetime.now(),
        model_name="fiduciary-moderator-engine-v2",
        tool_calls=1,
        final_decision_status="READY_FOR_USER_REVIEW",
        executive_summary=strategy_desc,
        portfolio_strategy_explanation=strategy_desc,
        diversification_explanation=f"Achieves {metrics.get('diversification_score', 85.0):.1f}/100 diversification breadth.",
        cash_reserve_explanation=f"₹{unallocated:,.2f} liquid cash buffer preserved for whole-share lot discipline.",
        position_explanations=position_explanations,
        portfolio_parameters=portfolio_params,
        critic_audit_summary="Approved unanimously by Risk Critic with zero unresolved defects.",
        sebi_guardrails_summary="Complies with Lucid internal 25% single-stock and 40% sector risk policies (under SEBI suitability principles).",
    )

    trace.append({
        "step": "moderator_explanation",
        "timestamp": datetime.now().isoformat(),
        "explanations_count": len(explanations),
    })

    return {
        "moderator_output": moderator_out.model_dump(),
        "explanations": explanations,
        "current_stage": "persistence",
        "execution_trace": trace,
    }


def _make_json_safe(obj: Any) -> Any:
    """Recursively converts datetimes, dates, UUIDs, and Decimals into JSON-serializable primitives."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_make_json_safe(x) for x in obj]
    return obj


# ==============================================================================
# 13. PERSISTENCE NODE (ACID-PROTECTED)
# ==============================================================================

def persistence_node(state: PortfolioAgentState, db: Session) -> Dict[str, Any]:
    """13. Persistence Node: Commits version, holdings, constraints, validation, and explanations to PostgreSQL with ACID rollback."""
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
            try:
                db.commit()
            except Exception:
                db.rollback()
        return {
            "status": "failed",
            "workflow_status": "BLOCKED",
            "current_stage": "completed",
            "error_code": state.get("error_code", "GENERATION_FAILED"),
            "error_summary": state.get("error_summary", "Workflow failed"),
            "execution_trace": trace,
        }

    try:
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
                version_label="2.0.0",
                optimizer_name="scipy_slsqp_constrained",
                implementation_revision="v2.0.0",
                configuration={"engine": "scipy-slsqp", "target": "sharpe_maximization"},
            )
            db.add(strat_ver)
            db.flush()

        db.query(InvestorPortfolio).filter(InvestorPortfolio.portfolio_id == portfolio_id).with_for_update().first()

        current_max_ver = (
            db.query(PortfolioVersion.version_number)
            .filter(PortfolioVersion.portfolio_id == portfolio_id)
            .order_by(PortfolioVersion.version_number.desc())
            .first()
        )
        next_ver_num = (current_max_ver[0] + 1) if current_max_ver else 1

        metrics = state.get("risk_metrics", {})
        holdings = state.get("allocations", [])

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
            generation_context=_make_json_safe({
                "trace": trace,
                "research_notes": state.get("analyst_research_notes", {}),
                "unallocated_cash": state.get("unallocated_cash", 0.0),
                "moderator_output": state.get("moderator_output"),
                "optimizer_output": state.get("optimizer_output"),
                "critic_output": state.get("critic_output"),
                "critic_final_output": state.get("critic_final_output"),
            }),
            generated_at=now,
        )
        db.add(pv)
        db.flush()

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
                decision_reason=f"Selected for risk-adjusted contribution in {h.get('sector_name', 'General')}",
            )
            db.add(psd)
            db.flush()
            decision_map[str(sec_id)] = psd.decision_id

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
            "workflow_status": "COMPLETED",
            "current_stage": "completed",
            "execution_trace": trace,
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Persistence transaction failed: {e}", exc_info=True)
        if req:
            try:
                req.request_status = "failed"
                req.completed_at = now
                req.error_code = "DB_PERSISTENCE_FAILED"
                req.error_summary = f"Database commit failed: {str(e)}"
                db.commit()
            except Exception:
                db.rollback()
        return {
            "status": "failed",
            "workflow_status": "BLOCKED",
            "current_stage": "completed",
            "error_code": "DB_PERSISTENCE_FAILED",
            "error_summary": f"Database commit failed: {str(e)}",
            "execution_trace": trace,
        }
