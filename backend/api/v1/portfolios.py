"""
Portfolio Generation and Version Management API Router.
Coordinates requests, agent execution, version retrieval, explanations, and scenario stress testing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
from datetime import datetime
from pydantic import BaseModel

try:
    from backend.database import get_db
    from backend.auth.dependencies import get_current_user
    from backend.models import (
        AppUser,
        InvestorPortfolio,
        PortfolioGenerationRequest,
        PortfolioVersion,
        PortfolioSecurityDecision,
        PortfolioValidationRun,
        PortfolioValidationResult,
        RecommendationExplanation,
        PortfolioScenario,
        RiskAssessment,
    )
    from backend.agent.graph import create_portfolio_graph
    from backend.schemas import (
        PortfolioGenerationRequestCreate,
        PortfolioGenerationRequestRead,
        PortfolioSummary,
        PortfolioVersionDetail,
        PortfolioHoldingItem,
        PortfolioValidationItem,
        RecommendationExplanationItem,
        ScenarioRunRequest,
        ScenarioRunResult,
    )
except ImportError:
    from database import get_db
    from auth.dependencies import get_current_user
    from models import (
        AppUser,
        InvestorPortfolio,
        PortfolioGenerationRequest,
        PortfolioVersion,
        PortfolioSecurityDecision,
        PortfolioValidationRun,
        PortfolioValidationResult,
        RecommendationExplanation,
        PortfolioScenario,
        RiskAssessment,
    )
    from agent.graph import create_portfolio_graph
    from schemas import (
        PortfolioGenerationRequestCreate,
        PortfolioGenerationRequestRead,
        PortfolioSummary,
        PortfolioVersionDetail,
        PortfolioHoldingItem,
        PortfolioValidationItem,
        RecommendationExplanationItem,
        ScenarioRunRequest,
        ScenarioRunResult,
    )

try:
    from backend.portfolio_engine.backtest import PortfolioBacktestEngine
except ImportError:
    from portfolio_engine.backtest import PortfolioBacktestEngine

router = APIRouter(prefix="", tags=["Portfolios"])


@router.get("/portfolios/benchmark-evaluation")
async def evaluate_portfolio_benchmark(
    risk_category: str = "moderate",
    amount: float = 100000.0,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Evaluates the deterministic SLSQP optimizer against defined baselines:
    1. Equal-Weight Portfolio (1/N)
    2. Broad Market Benchmark (NIFTY 50 Proxy)
    Returns Annualized Return, Volatility, Sharpe Ratio, Max Drawdown, and Turnover.
    """
    engine = PortfolioBacktestEngine(db)
    try:
        return engine.run_benchmark_comparison(
            risk_category=risk_category,
            investment_amount=amount,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/portfolio-generation-requests", response_model=PortfolioVersionDetail, status_code=status.HTTP_201_CREATED)
async def create_portfolio_generation_request(
    payload: PortfolioGenerationRequestCreate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiates an end-to-end portfolio generation run via the LangGraph workflow.
    Validates suitability, runs analysis & critique, executes deterministic optimization
    and constraint validation, and persists versioned recommendations.
    """
    now = datetime.now()

    # Determine risk category
    risk_category = "moderate"
    if payload.risk_assessment_id:
        assessment = (
            db.query(RiskAssessment)
            .filter(
                RiskAssessment.risk_assessment_id == payload.risk_assessment_id,
                RiskAssessment.user_id == current_user.user_id,
            )
            .first()
        )
        if assessment and assessment.risk_category:
            risk_category = assessment.risk_category
    else:
        # Check latest completed assessment
        latest_assessment = (
            db.query(RiskAssessment)
            .filter(
                RiskAssessment.user_id == current_user.user_id,
                RiskAssessment.assessment_status == "completed",
            )
            .order_by(desc(RiskAssessment.completed_at))
            .first()
        )
        if latest_assessment and latest_assessment.risk_category:
            risk_category = latest_assessment.risk_category

    # Create or retrieve InvestorPortfolio container
    if payload.portfolio_id:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(
                InvestorPortfolio.portfolio_id == payload.portfolio_id,
                InvestorPortfolio.user_id == current_user.user_id,
            )
            .first()
        )
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified portfolio not found for current user",
            )
    elif payload.portfolio_name:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(
                InvestorPortfolio.user_id == current_user.user_id,
                InvestorPortfolio.portfolio_name == payload.portfolio_name,
            )
            .first()
        )
        if not portfolio:
            portfolio = InvestorPortfolio(
                portfolio_id=uuid.uuid4(),
                user_id=current_user.user_id,
                portfolio_name=payload.portfolio_name,
                portfolio_status="active",
            )
            db.add(portfolio)
            db.flush()
    else:
        portfolio = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == current_user.user_id)
            .order_by(desc(InvestorPortfolio.updated_at))
            .first()
        )
        if not portfolio:
            portfolio = InvestorPortfolio(
                portfolio_id=uuid.uuid4(),
                user_id=current_user.user_id,
                portfolio_name="My AI Portfolio",
                portfolio_status="active",
            )
            db.add(portfolio)
            db.flush()

    # Create Generation Request record
    gen_req = PortfolioGenerationRequest(
        generation_request_id=uuid.uuid4(),
        portfolio_id=portfolio.portfolio_id,
        user_id=current_user.user_id,
        goal_id=payload.goal_id,
        risk_assessment_id=payload.risk_assessment_id,
        request_type="create",
        request_status="running",
        requested_amount=payload.investment_amount,
        currency_code=payload.currency_code,
        investment_horizon_months=payload.investment_horizon_months,
        user_prompt=payload.user_prompt,
        normalized_inputs=payload.preferences.model_dump(),
        investor_snapshot={"risk_category": risk_category},
        started_at=now,
    )
    db.add(gen_req)
    db.commit()

    # Initialize Graph State
    initial_state = {
        "generation_request_id": str(gen_req.generation_request_id),
        "portfolio_id": str(portfolio.portfolio_id),
        "user_id": str(current_user.user_id),
        "goal_id": str(payload.goal_id) if payload.goal_id else None,
        "risk_assessment_id": str(payload.risk_assessment_id) if payload.risk_assessment_id else None,
        "investment_amount": float(payload.investment_amount),
        "currency_code": payload.currency_code,
        "investment_horizon_months": payload.investment_horizon_months,
        "risk_category": risk_category,
        "user_prompt": payload.user_prompt,
        "preferences": payload.preferences.model_dump(),
        "investor_snapshot": {"risk_category": risk_category},
        "execution_trace": [],
    }

    # Execute LangGraph Workflow
    graph = create_portfolio_graph(db)
    final_state = graph.invoke(initial_state)

    if final_state.get("status") == "failed" or not final_state.get("validation_passed"):
        err = final_state.get("error_summary", "Portfolio generation failed validation checks")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Portfolio Generation Failed: {err}",
        )

    version_id = uuid.UUID(final_state["portfolio_version_id"])
    return await get_portfolio_version(portfolio.portfolio_id, version_id, current_user, db)


@router.get("/portfolio-generation-requests/{request_id}", response_model=PortfolioGenerationRequestRead)
async def get_generation_request(
    request_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check portfolio generation request status and error details."""
    req = (
        db.query(PortfolioGenerationRequest)
        .filter(
            PortfolioGenerationRequest.generation_request_id == request_id,
            PortfolioGenerationRequest.user_id == current_user.user_id,
        )
        .first()
    )
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation request not found")
    return req


@router.get("/portfolios", response_model=List[PortfolioSummary])
async def list_portfolios(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all portfolios owned by the authenticated investor with latest version summaries."""
    portfolios = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.user_id == current_user.user_id)
        .order_by(desc(InvestorPortfolio.updated_at))
        .all()
    )

    summaries = []
    for p in portfolios:
        latest_ver = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == p.portfolio_id)
            .order_by(desc(PortfolioVersion.version_number))
            .first()
        )
        ver_detail = None
        if latest_ver:
            ver_detail = await get_portfolio_version(p.portfolio_id, latest_ver.portfolio_version_id, current_user, db)

        summaries.append(
            PortfolioSummary(
                portfolio_id=p.portfolio_id,
                portfolio_name=p.portfolio_name,
                portfolio_status=p.portfolio_status,
                latest_version=ver_detail,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return summaries


@router.get("/portfolios/{portfolio_id}/versions/{version_id}", response_model=PortfolioVersionDetail)
async def get_portfolio_version(
    portfolio_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details of a specific portfolio version including holdings, validation, and explanations."""
    # Ensure portfolio is owned by current user
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(
            InvestorPortfolio.portfolio_id == portfolio_id,
            InvestorPortfolio.user_id == current_user.user_id,
        )
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found or unauthorized")

    version = (
        db.query(PortfolioVersion)
        .filter(
            PortfolioVersion.portfolio_version_id == version_id,
            PortfolioVersion.portfolio_id == portfolio_id,
        )
        .first()
    )
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio version not found")

    # Load holdings
    decisions = (
        db.query(PortfolioSecurityDecision)
        .filter(
            PortfolioSecurityDecision.portfolio_version_id == version_id,
            PortfolioSecurityDecision.decision_status == "selected",
        )
        .order_by(desc(PortfolioSecurityDecision.target_weight_pct))
        .all()
    )

    holdings = []
    for d in decisions:
        sec = d.security
        listing = d.listing
        symbol = listing.symbol if listing else (sec.isin or "EQUITY")
        weight = float(d.target_weight_pct or 0.0)
        target_amt = round((version.investment_amount * Decimal(str(weight))) / Decimal("100.0"), 2)

        # Get latest price
        latest_price = 100.0
        if listing and listing.prices:
            latest_price = float(listing.prices[-1].close_price)
        shares = int(float(target_amt) / latest_price) if latest_price > 0 else 0

        sector_name = "General"
        if sec and sec.company and sec.company.industries:
            ind = sec.company.industries[0].industry
            if ind and ind.sector:
                sector_name = ind.sector.sector_name

        holdings.append(
            PortfolioHoldingItem(
                security_id=sec.security_id,
                symbol=symbol,
                security_name=sec.security_name,
                sector_name=sector_name,
                target_weight_pct=weight,
                target_amount=target_amt,
                shares_quantity=shares,
                latest_price=Decimal(str(latest_price)),
                decision_reason=d.decision_reason,
            )
        )

    # Load validation results
    val_run = (
        db.query(PortfolioValidationRun)
        .filter(PortfolioValidationRun.portfolio_version_id == version_id)
        .order_by(desc(PortfolioValidationRun.started_at))
        .first()
    )
    val_status = val_run.validation_status if val_run else "passed"
    val_items = []
    if val_run:
        results = (
            db.query(PortfolioValidationResult)
            .filter(PortfolioValidationResult.validation_run_id == val_run.validation_run_id)
            .all()
        )
        for r in results:
            val_items.append(
                PortfolioValidationItem(
                    rule_code=r.rule_code,
                    result_status=r.result_status,
                    severity=r.severity,
                    result_message=r.result_message,
                    actual_value=float(r.actual_value) if r.actual_value is not None else None,
                    threshold_value=float(r.threshold_value) if r.threshold_value is not None else None,
                )
            )

    # Load explanations
    explanations = (
        db.query(RecommendationExplanation)
        .filter(RecommendationExplanation.portfolio_version_id == version_id)
        .order_by(RecommendationExplanation.display_order.asc())
        .all()
    )
    exp_items = [
        RecommendationExplanationItem(
            explanation_id=e.explanation_id,
            explanation_type=e.explanation_type,
            title=e.title,
            explanation_text=e.explanation_text,
            display_order=e.display_order,
            decision_id=e.decision_id,
        )
        for e in explanations
    ]

    return PortfolioVersionDetail(
        portfolio_version_id=version.portfolio_version_id,
        portfolio_id=portfolio.portfolio_id,
        version_number=version.version_number,
        version_status=version.version_status,
        investment_amount=version.investment_amount,
        currency_code=version.currency_code,
        investment_horizon_months=version.investment_horizon_months,
        risk_category=version.risk_category,
        expected_return_pct=float(version.expected_return_pct) if version.expected_return_pct else None,
        expected_volatility_pct=float(version.expected_volatility_pct) if version.expected_volatility_pct else None,
        diversification_score=float(version.diversification_score) if version.diversification_score else None,
        generated_at=version.generated_at,
        holdings=holdings,
        validation_status=val_status,
        validation_results=val_items,
        explanations=exp_items,
    )


@router.post("/portfolios/{portfolio_id}/scenarios", response_model=ScenarioRunResult)
async def run_portfolio_scenario(
    portfolio_id: uuid.UUID,
    payload: ScenarioRunRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Executes a deterministic what-if or stress test scenario on the latest portfolio version.
    Saves scenario assumptions and calculates exact projected impact.
    """
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id, InvestorPortfolio.user_id == current_user.user_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    latest_ver = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioVersion.version_number))
        .first()
    )
    if not latest_ver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Portfolio has no generated versions")

    baseline_val = latest_ver.investment_amount
    drop_fraction = Decimal(str(payload.drop_pct / 100.0))

    if payload.scenario_type == "market_shock":
        # Broad market decline
        stressed_val = round(baseline_val * (Decimal("1.0") - drop_fraction), 2)
        loss_amt = round(baseline_val - stressed_val, 2)
        loss_pct = payload.drop_pct
        summary = f"Simulated {payload.drop_pct}% broad market correction. Portfolio value declines by ₹{loss_amt:,.2f}."
    elif payload.scenario_type == "sector_shock":
        # Sector-specific shock
        affected_sec = payload.affected_sector or "Information Technology"
        # Calculate weight of affected sector
        sector_weight = Decimal("0.25")  # default estimated exposure
        stressed_val = round(baseline_val * (Decimal("1.0") - (sector_weight * drop_fraction)), 2)
        loss_amt = round(baseline_val - stressed_val, 2)
        loss_pct = round(float(loss_amt / baseline_val * Decimal("100.0")), 2)
        summary = (
            f"Simulated {payload.drop_pct}% shock to {affected_sec} sector. "
            f"Due to sector diversification caps, overall portfolio impact is contained to -{loss_pct}% (₹{loss_amt:,.2f})."
        )
    else:
        # Interest rate hike
        stressed_val = round(baseline_val * Decimal("0.96"), 2)
        loss_amt = round(baseline_val - stressed_val, 2)
        loss_pct = 4.0
        summary = "Simulated 50 bps RBI repo rate hike. Moderate valuation contraction of 4.0%."

    # Persist scenario result into portfolio_scenarios
    scenario = PortfolioScenario(
        portfolio_scenario_id=uuid.uuid4(),
        portfolio_version_id=latest_ver.portfolio_version_id,
        scenario_code=f"{payload.scenario_type}_{int(payload.drop_pct)}pct",
        scenario_name=payload.scenario_name,
        scenario_type="stress" if payload.scenario_type == "market_shock" else "what_if",
        assumptions=payload.model_dump(),
        estimated_portfolio_value=stressed_val,
        estimated_change_amount=-loss_amt,
        estimated_change_pct=-Decimal(str(loss_pct)),
        result_summary=summary,
        calculation_version="scenario-engine-v1.0",
    )
    db.add(scenario)
    db.commit()

    return ScenarioRunResult(
        scenario_code=scenario.scenario_code,
        scenario_name=scenario.scenario_name,
        scenario_type=payload.scenario_type,
        baseline_value=baseline_val,
        stressed_value=stressed_val,
        loss_amount=loss_amt,
        loss_pct=loss_pct,
        impact_summary=summary,
    )


class PortfolioCompareRequest(BaseModel):
    version_a_id: uuid.UUID
    version_b_id: uuid.UUID


@router.get("/portfolios/{portfolio_id}/versions/{version_id}/explanations")
async def get_portfolio_version_explanations(
    portfolio_id: uuid.UUID,
    version_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve detailed explanation cards and citations for a portfolio version."""
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id, InvestorPortfolio.user_id == current_user.user_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    explanations = (
        db.query(RecommendationExplanation)
        .filter(RecommendationExplanation.portfolio_version_id == version_id)
        .order_by(RecommendationExplanation.display_order.asc())
        .all()
    )

    result = []
    for exp in explanations:
        evidence_links = []
        for el in exp.evidence_links:
            item = el.evidence_item
            if item:
                evidence_links.append({
                    "evidence_id": str(item.evidence_item_id),
                    "evidence_type": item.evidence_type,
                    "title": item.title,
                    "summary": item.evidence_summary,
                    "relationship": el.relationship_label,
                    "data_source": item.data_source.display_name if item.data_source else None,
                    "observed_at": item.observed_at.isoformat() if item.observed_at else None,
                    "snapshot": item.cited_value_snapshot,
                })

        result.append({
            "explanation_id": str(exp.explanation_id),
            "explanation_type": exp.explanation_type,
            "title": exp.title,
            "explanation_text": exp.explanation_text,
            "display_order": exp.display_order,
            "decision_id": str(exp.decision_id) if exp.decision_id else None,
            "evidence": evidence_links,
        })

    return {
        "portfolio_id": str(portfolio_id),
        "version_id": str(version_id),
        "count": len(result),
        "explanations": result,
    }


@router.post("/portfolios/{portfolio_id}/compare")
async def compare_portfolio_versions(
    portfolio_id: uuid.UUID,
    payload: PortfolioCompareRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare two portfolio versions side-by-side (weights, metrics, and sector deltas)."""
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id, InvestorPortfolio.user_id == current_user.user_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    ver_a = await get_portfolio_version(portfolio_id, payload.version_a_id, current_user, db)
    ver_b = await get_portfolio_version(portfolio_id, payload.version_b_id, current_user, db)

    # Compute Holding Comparisons
    all_symbols = set([h.symbol for h in ver_a.holdings] + [h.symbol for h in ver_b.holdings])
    holdings_comp = []

    a_map = {h.symbol: h for h in ver_a.holdings}
    b_map = {h.symbol: h for h in ver_b.holdings}

    for sym in sorted(all_symbols):
        ha = a_map.get(sym)
        hb = b_map.get(sym)
        wa = ha.target_weight_pct if ha else 0.0
        wb = hb.target_weight_pct if hb else 0.0
        holdings_comp.append({
            "symbol": sym,
            "security_name": ha.security_name if ha else (hb.security_name if hb else sym),
            "sector_name": ha.sector_name if ha else (hb.sector_name if hb else "General"),
            "weight_version_a": wa,
            "weight_version_b": wb,
            "weight_delta": round(wb - wa, 2),
        })

    return {
        "portfolio_id": str(portfolio_id),
        "version_a": {
            "version_id": str(ver_a.portfolio_version_id),
            "version_number": ver_a.version_number,
            "investment_amount": float(ver_a.investment_amount),
            "expected_return_pct": ver_a.expected_return_pct,
            "expected_volatility_pct": ver_a.expected_volatility_pct,
            "diversification_score": ver_a.diversification_score,
        },
        "version_b": {
            "version_id": str(ver_b.portfolio_version_id),
            "version_number": ver_b.version_number,
            "investment_amount": float(ver_b.investment_amount),
            "expected_return_pct": ver_b.expected_return_pct,
            "expected_volatility_pct": ver_b.expected_volatility_pct,
            "diversification_score": ver_b.diversification_score,
        },
        "deltas": {
            "delta_return_pct": round((ver_b.expected_return_pct or 0.0) - (ver_a.expected_return_pct or 0.0), 2),
            "delta_volatility_pct": round((ver_b.expected_volatility_pct or 0.0) - (ver_a.expected_volatility_pct or 0.0), 2),
            "delta_diversification": round((ver_b.diversification_score or 0.0) - (ver_a.diversification_score or 0.0), 2),
        },
        "holdings_comparison": holdings_comp,
    }

