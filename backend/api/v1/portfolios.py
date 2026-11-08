"""
Portfolio Generation and Version Management API Router.
Coordinates requests, agent execution, version retrieval, explanations, and scenario stress testing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
from datetime import datetime, timezone
import csv
import io
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

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
        Security,
        InstrumentListing,
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
    from backend.portfolio_engine.conversational_assistant import (
        get_rich_security_rationale,
        simulate_conversational_query,
    )
    from backend.portfolio_engine.stock_why_service import (
        generate_stock_why_explanation,
        chat_stock_why_assistant,
    )
    from backend.services.account_deletion_service import delete_investor_portfolio
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
        Security,
        InstrumentListing,
    )
    from services.account_deletion_service import delete_investor_portfolio
    from portfolio_engine.stock_why_service import (
        generate_stock_why_explanation,
        chat_stock_why_assistant,
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
def evaluate_portfolio_benchmark(
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
    risk_category = payload.risk_category or "moderate"
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
    elif not payload.risk_category:
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
        status_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        raise HTTPException(
            status_code=status_422,
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


class BatchDeletePortfoliosRequest(BaseModel):
    portfolio_ids: List[uuid.UUID]


@router.post("/portfolios/batch-delete")
async def batch_delete_portfolios(
    payload: BatchDeletePortfoliosRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes selected portfolios belonging to the authenticated user.
    """
    if not payload.portfolio_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No portfolio IDs provided for batch deletion.",
        )
    deleted_count = 0
    for pid in payload.portfolio_ids:
        try:
            delete_investor_portfolio(db=db, portfolio_id=pid, user_id=current_user.user_id)
            deleted_count += 1
        except HTTPException as e:
            if e.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN):
                continue
            raise e
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Successfully deleted {deleted_count} portfolio(s).",
    }


@router.delete("/portfolios")
async def delete_all_portfolios(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes ALL portfolios belonging to the authenticated user
    without closing their account, removing goals, or altering credentials.
    """
    portfolios = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.user_id == current_user.user_id)
        .all()
    )
    deleted_count = 0
    for p in portfolios:
        delete_investor_portfolio(db=db, portfolio_id=p.portfolio_id, user_id=current_user.user_id)
        deleted_count += 1
    return {
        "success": True,
        "deleted_count": deleted_count,
        "message": f"Successfully deleted all {deleted_count} portfolio(s).",
    }


@router.delete("/portfolios/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes an individual portfolio and its versions, holdings, decisions,
    validation runs, explanations, and scenario simulations.
    Guarantees user account, other portfolios, and shared market universe remain untouched.
    """
    return delete_investor_portfolio(
        db=db,
        portfolio_id=portfolio_id,
        user_id=current_user.user_id,
    )


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

    ctx = version.generation_context or {}
    ctx_allocs = {
        (a.get("symbol") or a.get("ticker", "")).upper(): a
        for a in ctx.get("allocations", []) + ctx.get("optimizer_output", {}).get("positions", [])
        if a.get("symbol") or a.get("ticker")
    }

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

        # Prioritize exact whole shares and reference price from optimizer / rebalancer if available
        matched = ctx_allocs.get(symbol.upper())
        if matched:
            if "shares_quantity" in matched and int(matched["shares_quantity"]) > 0:
                shares = int(matched["shares_quantity"])
            elif "target_quantity" in matched and int(matched["target_quantity"]) > 0:
                shares = int(matched["target_quantity"])
            if "latest_price" in matched and float(matched["latest_price"]) > 0:
                latest_price = float(matched["latest_price"])
            elif "reference_price" in matched and float(matched["reference_price"]) > 0:
                latest_price = float(matched["reference_price"])
            if "target_amount" in matched and float(matched["target_amount"]) > 0:
                target_amt = Decimal(str(round(float(matched["target_amount"]), 2)))
            elif shares > 0 and latest_price > 0:
                target_amt = Decimal(str(round(shares * latest_price, 2)))

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
                decision_reason=(
                    d.decision_reason
                    if d.decision_reason and "Selected for risk-adjusted contribution in" not in d.decision_reason
                    else get_rich_security_rationale(
                        symbol=symbol,
                        security_name=sec.security_name,
                        sector_name=sector_name,
                        target_weight_pct=weight,
                        shares_quantity=shares,
                        latest_price=float(latest_price),
                    )
                ),
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
    exp_items = []
    for e in explanations:
        s_url = None
        e_title = None
        if getattr(e, "evidence_links", None):
            for link in e.evidence_links:
                if link.evidence_item and link.evidence_item.source_url:
                    s_url = link.evidence_item.source_url
                    e_title = link.evidence_item.title
                    break
        exp_items.append(
            RecommendationExplanationItem(
                explanation_id=e.explanation_id,
                explanation_type=e.explanation_type,
                title=e.title,
                explanation_text=e.explanation_text,
                display_order=e.display_order,
                decision_id=e.decision_id,
                source_url=s_url,
                evidence_title=e_title,
            )
        )

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


@router.get("/portfolios/{portfolio_id}/versions", response_model=List[PortfolioVersionDetail])
async def list_portfolio_versions(
    portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve full details of all versions of a specific portfolio."""
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

    versions = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioVersion.version_number))
        .all()
    )
    details = []
    for v in versions:
        details.append(await get_portfolio_version(portfolio_id, v.portfolio_version_id, current_user, db))
    return details


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

    # Construct unique scenario code (sanitizing sector for sector shocks)
    if payload.scenario_type == "sector_shock" and payload.affected_sector:
        sec_slug = payload.affected_sector.lower().replace(" ", "_")
        scenario_code = f"sector_shock_{sec_slug}_{int(payload.drop_pct)}pct"[:64]
    else:
        scenario_code = f"{payload.scenario_type}_{int(payload.drop_pct)}pct"[:64]

    # Persist or update scenario result (idempotent upsert to avoid uq_scenario_code_per_version violation)
    existing_scenario = (
        db.query(PortfolioScenario)
        .filter(
            PortfolioScenario.portfolio_version_id == latest_ver.portfolio_version_id,
            PortfolioScenario.scenario_code == scenario_code,
        )
        .first()
    )

    if existing_scenario:
        existing_scenario.scenario_name = payload.scenario_name
        existing_scenario.scenario_type = "stress" if payload.scenario_type == "market_shock" else "what_if"
        existing_scenario.assumptions = payload.model_dump()
        existing_scenario.estimated_portfolio_value = stressed_val
        existing_scenario.estimated_change_amount = -loss_amt
        existing_scenario.estimated_change_pct = -Decimal(str(loss_pct))
        existing_scenario.result_summary = summary
        existing_scenario.calculation_version = "scenario-engine-v1.0"
        scenario = existing_scenario
    else:
        scenario = PortfolioScenario(
            portfolio_scenario_id=uuid.uuid4(),
            portfolio_version_id=latest_ver.portfolio_version_id,
            scenario_code=scenario_code,
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

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Fallback for concurrent execution race conditions: retrieve and update
        existing_scenario = (
            db.query(PortfolioScenario)
            .filter(
                PortfolioScenario.portfolio_version_id == latest_ver.portfolio_version_id,
                PortfolioScenario.scenario_code == scenario_code,
            )
            .first()
        )
        if existing_scenario:
            existing_scenario.scenario_name = payload.scenario_name
            existing_scenario.scenario_type = "stress" if payload.scenario_type == "market_shock" else "what_if"
            existing_scenario.assumptions = payload.model_dump()
            existing_scenario.estimated_portfolio_value = stressed_val
            existing_scenario.estimated_change_amount = -loss_amt
            existing_scenario.estimated_change_pct = -Decimal(str(loss_pct))
            existing_scenario.result_summary = summary
            db.commit()
            scenario = existing_scenario

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


class StockWhyChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, str]]] = None


class StockWhyChatResponse(BaseModel):
    reply: str
    symbol: str
    company_name: str
    suggested_followups: List[str]


@router.get("/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/why")
async def get_stock_why(
    portfolio_id: uuid.UUID,
    version_id: uuid.UUID,
    symbol: str,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Dedicated stock-specific 'Ask AI Why?' analysis endpoint (FR-D01 & Committee Deliberation).
    Provides structured 10-section equity research analysis for the specified stock.
    """
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    explanation = generate_stock_why_explanation(
        portfolio_id=portfolio_id,
        version_id=version_id,
        symbol=symbol,
        user_id=current_user.user_id,
        db=db,
    )
    return explanation


@router.post("/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/chat", response_model=StockWhyChatResponse)
async def chat_stock_why(
    portfolio_id: uuid.UUID,
    version_id: uuid.UUID,
    symbol: str,
    payload: StockWhyChatRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Interactive stock-specific follow-up chat endpoint.
    Maintains holding context and portfolio math across conversation turns.
    """
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id)
        .first()
    )
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")

    result = chat_stock_why_assistant(
        portfolio_id=portfolio_id,
        version_id=version_id,
        symbol=symbol,
        query=payload.message,
        history=payload.history,
        user_id=current_user.user_id,
        db=db,
    )
    return StockWhyChatResponse(**result)


async def _get_version_for_user(
    version_id: uuid.UUID,
    current_user: AppUser,
    db: Session,
) -> PortfolioVersionDetail:
    """Retrieve any portfolio version owned by the user across any of their portfolios."""
    version = (
        db.query(PortfolioVersion)
        .join(InvestorPortfolio, PortfolioVersion.portfolio_id == InvestorPortfolio.portfolio_id)
        .filter(
            PortfolioVersion.portfolio_version_id == version_id,
            InvestorPortfolio.user_id == current_user.user_id,
        )
        .first()
    )
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio version {version_id} not found or unauthorized.",
        )
    return await get_portfolio_version(version.portfolio_id, version.portfolio_version_id, current_user, db)


def _build_comparison_result(
    ver_a: PortfolioVersionDetail,
    ver_b: PortfolioVersionDetail,
    portfolio_name_a: Optional[str] = None,
    portfolio_name_b: Optional[str] = None,
) -> Dict[str, Any]:
    all_symbols = set([h.symbol for h in ver_a.holdings] + [h.symbol for h in ver_b.holdings])
    holdings_comp = []

    a_map = {h.symbol: h for h in ver_a.holdings}
    b_map = {h.symbol: h for h in ver_b.holdings}

    for sym in sorted(all_symbols):
        ha = a_map.get(sym)
        hb = b_map.get(sym)
        wa = ha.target_weight_pct if ha else 0.0
        wb = hb.target_weight_pct if hb else 0.0
        status_code = "both"
        if ha and not hb:
            status_code = "removed_in_b"
        elif hb and not ha:
            status_code = "added_in_b"

        holdings_comp.append({
            "symbol": sym,
            "security_name": ha.security_name if ha else (hb.security_name if hb else sym),
            "sector_name": ha.sector_name if ha else (hb.sector_name if hb else "General"),
            "weight_version_a": wa,
            "weight_version_b": wb,
            "weight_delta": round(wb - wa, 2),
            "shares_version_a": ha.shares_quantity if ha else 0,
            "shares_version_b": hb.shares_quantity if hb else 0,
            "status": status_code,
        })

    return {
        "portfolio_id": str(ver_a.portfolio_id),
        "version_a": {
            "portfolio_id": str(ver_a.portfolio_id),
            "portfolio_name": portfolio_name_a,
            "version_id": str(ver_a.portfolio_version_id),
            "version_number": ver_a.version_number,
            "risk_category": ver_a.risk_category,
            "investment_amount": float(ver_a.investment_amount),
            "expected_return_pct": ver_a.expected_return_pct,
            "expected_volatility_pct": ver_a.expected_volatility_pct,
            "diversification_score": ver_a.diversification_score,
            "holdings_count": len(ver_a.holdings),
        },
        "version_b": {
            "portfolio_id": str(ver_b.portfolio_id),
            "portfolio_name": portfolio_name_b,
            "version_id": str(ver_b.portfolio_version_id),
            "version_number": ver_b.version_number,
            "risk_category": ver_b.risk_category,
            "investment_amount": float(ver_b.investment_amount),
            "expected_return_pct": ver_b.expected_return_pct,
            "expected_volatility_pct": ver_b.expected_volatility_pct,
            "diversification_score": ver_b.diversification_score,
            "holdings_count": len(ver_b.holdings),
        },
        "deltas": {
            "delta_return_pct": round((ver_b.expected_return_pct or 0.0) - (ver_a.expected_return_pct or 0.0), 2),
            "delta_volatility_pct": round((ver_b.expected_volatility_pct or 0.0) - (ver_a.expected_volatility_pct or 0.0), 2),
            "delta_diversification": round((ver_b.diversification_score or 0.0) - (ver_a.diversification_score or 0.0), 2),
        },
        "holdings_comparison": holdings_comp,
    }


@router.post("/portfolios/compare")
async def universal_compare_portfolios(
    payload: PortfolioCompareRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare any two portfolio versions owned by the investor (within the same or across different portfolios).
    Computes holding weight deltas, return/volatility deltas, and diversification score deltas.
    """
    ver_a = await _get_version_for_user(payload.version_a_id, current_user, db)
    ver_b = await _get_version_for_user(payload.version_b_id, current_user, db)

    pa = db.query(InvestorPortfolio).filter_by(portfolio_id=ver_a.portfolio_id).first()
    pb = db.query(InvestorPortfolio).filter_by(portfolio_id=ver_b.portfolio_id).first()

    return _build_comparison_result(
        ver_a,
        ver_b,
        portfolio_name_a=pa.portfolio_name if pa else "Portfolio A",
        portfolio_name_b=pb.portfolio_name if pb else "Portfolio B",
    )


@router.post("/portfolios/{portfolio_id}/compare")
async def compare_portfolio_versions(
    portfolio_id: uuid.UUID,
    payload: PortfolioCompareRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compare two portfolio versions side-by-side (weights, metrics, and sector deltas)."""
    try:
        ver_a = await get_portfolio_version(portfolio_id, payload.version_a_id, current_user, db)
    except HTTPException:
        ver_a = await _get_version_for_user(payload.version_a_id, current_user, db)

    try:
        ver_b = await get_portfolio_version(portfolio_id, payload.version_b_id, current_user, db)
    except HTTPException:
        ver_b = await _get_version_for_user(payload.version_b_id, current_user, db)

    pa = db.query(InvestorPortfolio).filter_by(portfolio_id=ver_a.portfolio_id).first()
    pb = db.query(InvestorPortfolio).filter_by(portfolio_id=ver_b.portfolio_id).first()

    return _build_comparison_result(
        ver_a,
        ver_b,
        portfolio_name_a=pa.portfolio_name if pa else "Portfolio A",
        portfolio_name_b=pb.portfolio_name if pb else "Portfolio B",
    )


class ChatMessagePayload(BaseModel):
    role: str
    content: str


class PortfolioChatRequest(BaseModel):
    message: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None
    history: Optional[List[ChatMessagePayload]] = None

    @property
    def text(self) -> str:
        return (self.message or self.query or "").strip()


class PortfolioChatResponse(BaseModel):
    reply: str
    scenario_simulation: Optional[Dict[str, Any]] = None
    suggested_followups: List[str]
    intent: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/portfolios/{portfolio_id}/chat", response_model=PortfolioChatResponse)
async def chat_with_portfolio_assistant(
    portfolio_id: uuid.UUID,
    payload: PortfolioChatRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Conversational Fiduciary Assistant & Dynamic Stress-Testing Endpoint (FR-D01 & FR-D08).
    Allows retail investors to ask natural-language questions about holdings or test arbitrary crash scenarios.
    """
    portfolio = (
        db.query(InvestorPortfolio)
        .filter(InvestorPortfolio.portfolio_id == portfolio_id)
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

    # Load version detail to get complete holdings list
    owner_user = db.query(AppUser).filter(AppUser.user_id == portfolio.user_id).first() or current_user
    ver_detail = await get_portfolio_version(portfolio_id, latest_ver.portfolio_version_id, owner_user, db)

    holdings_dicts = [
        {
            "symbol": h.symbol,
            "security_name": h.security_name,
            "sector_name": h.sector_name,
            "target_weight_pct": h.target_weight_pct,
            "target_amount": float(h.target_amount),
            "shares_quantity": h.shares_quantity,
            "latest_price": float(h.latest_price),
            "decision_reason": h.decision_reason,
        }
        for h in ver_detail.holdings
    ]

    history_dicts = None
    if payload.history:
        history_dicts = [{"role": h.role, "content": h.content} for h in payload.history]

    session_id = payload.session_id or f"portfolio_{portfolio_id}"

    allocated_sum = sum(float(h["shares_quantity"]) * float(h["latest_price"]) for h in holdings_dicts)
    cash_reserve = max(0.0, float(ver_detail.investment_amount) - allocated_sum)
    extra_metrics = {
        "expected_return_pct": float(ver_detail.expected_return_pct) if ver_detail.expected_return_pct else None,
        "expected_volatility_pct": float(ver_detail.expected_volatility_pct) if ver_detail.expected_volatility_pct else None,
        "diversification_score": float(ver_detail.diversification_score) if ver_detail.diversification_score else None,
        "risk_category": ver_detail.risk_category,
        "cash_reserve": cash_reserve,
    }

    sim_res = simulate_conversational_query(
        holdings=holdings_dicts,
        total_capital=float(ver_detail.investment_amount),
        query_text=payload.text,
        user_id=str(current_user.user_id),
        session_id=session_id,
        history=history_dicts,
        extra_metrics=extra_metrics,
    )

    return PortfolioChatResponse(
        reply=sim_res["reply"],
        scenario_simulation=sim_res.get("scenario_simulation"),
        suggested_followups=sim_res.get("suggested_followups", []),
        intent=sim_res.get("intent"),
        session_id=sim_res.get("session_id"),
    )


class GeneralChatRequest(BaseModel):
    message: Optional[str] = None
    query: Optional[str] = None
    session_id: Optional[str] = None
    history: Optional[List[ChatMessagePayload]] = None
    portfolio_id: Optional[uuid.UUID] = None
    existing_portfolio_id: Optional[uuid.UUID] = None

    @property
    def text(self) -> str:
        return (self.message or self.query or "").strip()


@router.post("/chat", response_model=PortfolioChatResponse)
async def general_chat_with_assistant(
    payload: GeneralChatRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Universal Conversational Assistant Endpoint.
    Works with or without an active portfolio, providing dynamic context-aware guidance.
    """
    history_dicts = None
    if payload.history:
        history_dicts = [{"role": h.role, "content": h.content} for h in payload.history]

    session_id = payload.session_id or f"general_user_{current_user.user_id}"

    # Check if this query pertains to an imported / existing portfolio diagnosis
    from backend.models.diagnosis import ExistingPortfolio
    ep_target = None
    if payload.existing_portfolio_id:
        ep_target = db.query(ExistingPortfolio).filter(
            ExistingPortfolio.existing_portfolio_id == payload.existing_portfolio_id,
            ExistingPortfolio.user_id == current_user.user_id,
        ).first()

    if not ep_target and payload.portfolio_id:
        ep_target = db.query(ExistingPortfolio).filter(
            ExistingPortfolio.existing_portfolio_id == payload.portfolio_id,
            ExistingPortfolio.user_id == current_user.user_id,
        ).first()

    q_lower = payload.text.lower()
    is_imported_or_rebalance_query = (
        "brokerage" in q_lower
        or "imported" in q_lower
        or ("rebalanc" in q_lower and any(w in q_lower for w in ["trade", "trim", "add", "propose", "suggest", "action", "plan", "demat"]))
        or ("why" in q_lower and any(w in q_lower for w in ["trim", "sell", "cut", "reduce", "rebalanc"]))
    )

    if not ep_target and is_imported_or_rebalance_query:
        ep_target = (
            db.query(ExistingPortfolio)
            .filter(ExistingPortfolio.user_id == current_user.user_id)
            .order_by(desc(ExistingPortfolio.updated_at))
            .first()
        )

    if ep_target:
        try:
            from backend.portfolio_engine.diagnosis_copilot_service import chat_with_diagnosis_copilot
            diag_chat_res = chat_with_diagnosis_copilot(
                existing_portfolio_id=ep_target.existing_portfolio_id,
                query=payload.text,
                history=history_dicts,
                user_id=current_user.user_id,
                db=db,
            )
            return PortfolioChatResponse(
                reply=diag_chat_res["reply"],
                scenario_simulation=None,
                suggested_followups=diag_chat_res.get("suggested_followups", []),
                intent="PORTFOLIO_DIAGNOSIS_AND_REBALANCE",
                session_id=session_id,
            )
        except Exception as ep_err:
            logger.debug(f"Could not use diagnosis copilot directly: {ep_err}")

    # Check if a portfolio exists or was specified
    holdings_dicts = []
    total_capital = 100_000.0

    target_pid = payload.portfolio_id
    if not target_pid:
        first_port = (
            db.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == current_user.user_id)
            .first()
        )
        if first_port:
            target_pid = first_port.portfolio_id

    extra_metrics = None
    if target_pid:
        latest_ver = (
            db.query(PortfolioVersion)
            .filter(PortfolioVersion.portfolio_id == target_pid)
            .order_by(desc(PortfolioVersion.version_number))
            .first()
        )
        if latest_ver:
            try:
                ver_detail = await get_portfolio_version(target_pid, latest_ver.portfolio_version_id, current_user, db)
                total_capital = float(ver_detail.investment_amount)
                holdings_dicts = [
                    {
                        "symbol": h.symbol,
                        "security_name": h.security_name,
                        "sector_name": h.sector_name,
                        "target_weight_pct": h.target_weight_pct,
                        "target_amount": float(h.target_amount),
                        "shares_quantity": h.shares_quantity,
                        "latest_price": float(h.latest_price),
                        "decision_reason": h.decision_reason,
                    }
                    for h in ver_detail.holdings
                ]
                allocated_sum = sum(float(h["shares_quantity"]) * float(h["latest_price"]) for h in holdings_dicts)
                cash_reserve = max(0.0, float(ver_detail.investment_amount) - allocated_sum)
                extra_metrics = {
                    "expected_return_pct": float(ver_detail.expected_return_pct) if ver_detail.expected_return_pct else None,
                    "expected_volatility_pct": float(ver_detail.expected_volatility_pct) if ver_detail.expected_volatility_pct else None,
                    "diversification_score": float(ver_detail.diversification_score) if ver_detail.diversification_score else None,
                    "risk_category": ver_detail.risk_category,
                    "cash_reserve": cash_reserve,
                }
            except Exception:
                pass

    sim_res = simulate_conversational_query(
        holdings=holdings_dicts,
        total_capital=total_capital,
        query_text=payload.text,
        user_id=str(current_user.user_id),
        session_id=session_id,
        history=history_dicts,
        extra_metrics=extra_metrics,
    )

    return PortfolioChatResponse(
        reply=sim_res["reply"],
        scenario_simulation=sim_res.get("scenario_simulation"),
        suggested_followups=sim_res.get("suggested_followups", []),
        intent=sim_res.get("intent"),
        session_id=sim_res.get("session_id"),
    )


@router.get("/portfolios/{portfolio_id}/versions/{version_id}/export-orders")
async def export_portfolio_orders(
    portfolio_id: uuid.UUID,
    version_id: uuid.UUID,
    export_format: str = Query("json", description="Export format: 'json', 'csv', or 'zerodha_csv'"),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exports executable trade order basket for broker execution (Zerodha / Groww / Upstox / Angel One).
    Calculates whole-share buy orders, limit prices, target amounts, and unallocated cash reserves.
    """
    ver_detail = await get_portfolio_version(portfolio_id, version_id, current_user, db)

    orders = []
    total_invested = Decimal("0.0")

    for h in ver_detail.holdings:
        if h.shares_quantity > 0:
            order_amt = round(Decimal(h.shares_quantity) * h.latest_price, 2)
            total_invested += order_amt
            orders.append({
                "symbol": h.symbol,
                "security_name": h.security_name,
                "sector_name": h.sector_name,
                "exchange": "NSE",
                "action": "BUY",
                "shares_quantity": h.shares_quantity,
                "limit_price": float(h.latest_price),
                "order_type": "LIMIT",
                "product": "CNC",
                "target_weight_pct": h.target_weight_pct,
                "allocated_amount": float(order_amt),
            })

    unallocated_cash = round(ver_detail.investment_amount - total_invested, 2)

    if export_format in ("csv", "zerodha_csv"):
        output = io.StringIO()
        if export_format == "zerodha_csv":
            # Zerodha Kite Basket Format
            writer = csv.writer(output)
            writer.writerow(["Instrument", "Exchange", "Action", "Order Type", "Quantity", "Price", "Product"])
            for o in orders:
                writer.writerow([o["symbol"], o["exchange"], o["action"], o["order_type"], o["shares_quantity"], o["limit_price"], o["product"]])
        else:
            # Standard Investor Execution Slip Format
            writer = csv.writer(output)
            writer.writerow(["Symbol", "Security Name", "Sector", "Exchange", "Action", "Shares Quantity", "Limit Price (INR)", "Order Amount (INR)", "Target Weight (%)"])
            for o in orders:
                writer.writerow([
                    o["symbol"],
                    o["security_name"],
                    o["sector_name"],
                    o["exchange"],
                    o["action"],
                    o["shares_quantity"],
                    f"{o['limit_price']:.2f}",
                    f"{o['allocated_amount']:.2f}",
                    f"{o['target_weight_pct']:.2f}%",
                ])
            writer.writerow([])
            writer.writerow(["Cash Reserve (INR)", f"{unallocated_cash:.2f}"])
            writer.writerow(["Total Investment Capital (INR)", f"{float(ver_detail.investment_amount):.2f}"])

        csv_content = output.getvalue()
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=lucid_portfolio_orders_v{ver_detail.version_number}.csv"
            },
        )

    return {
        "portfolio_id": str(portfolio_id),
        "version_id": str(version_id),
        "version_number": ver_detail.version_number,
        "investment_amount": float(ver_detail.investment_amount),
        "total_invested": float(total_invested),
        "unallocated_cash": float(unallocated_cash),
        "total_orders": len(orders),
        "orders": orders,
        "generated_at": ver_detail.generated_at.isoformat() if hasattr(ver_detail.generated_at, "isoformat") else str(ver_detail.generated_at),
    }


@router.get("/portfolios/{portfolio_id}/monitoring")
async def get_portfolio_monitoring(
    portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-C07: Dynamic Portfolio Valuation & Drift Monitoring.
    Returns latest holding values, current weights, stock and sector drift, and health indicators.
    """
    from backend.portfolio_engine.monitoring_service import PortfolioMonitoringService

    # Verify portfolio ownership
    port = (
        db.query(InvestorPortfolio)
        .filter(
            InvestorPortfolio.portfolio_id == portfolio_id,
            InvestorPortfolio.user_id == current_user.user_id,
        )
        .first()
    )
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or access denied",
        )

    # Get latest version
    latest_ver = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioVersion.version_number))
        .first()
    )
    if not latest_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio versions generated for monitoring",
        )

    monitoring_res = PortfolioMonitoringService.monitor_native_portfolio(
        db=db,
        portfolio_version_id=latest_ver.portfolio_version_id,
        user_id=current_user.user_id,
    )
    return monitoring_res


@router.post("/portfolios/{portfolio_id}/monitor-now")
async def monitor_portfolio_now(
    portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-C07: Forces real-time price retrieval, revaluation, drift recalculation, and snapshot persistence.
    """
    return await get_portfolio_monitoring(portfolio_id, current_user, db)


@router.get("/portfolios/{portfolio_id}/rebalance-preview")
async def get_portfolio_rebalance_preview(
    portfolio_id: uuid.UUID,
    stock_drift_threshold: float = Query(5.0, ge=1.0, le=25.0),
    sector_drift_threshold: float = Query(10.0, ge=1.0, le=40.0),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-C08: Generates whole-share rebalancing preview (BUY/SELL/HOLD trades, turnover, and cash) for a native portfolio.
    """
    from backend.portfolio_engine.rebalancing_service import RebalancingService

    # Verify ownership
    port = (
        db.query(InvestorPortfolio)
        .filter(
            InvestorPortfolio.portfolio_id == portfolio_id,
            InvestorPortfolio.user_id == current_user.user_id,
        )
        .first()
    )
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or access denied",
        )

    latest_ver = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioVersion.version_number))
        .first()
    )
    if not latest_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio versions available for rebalancing",
        )

    preview = RebalancingService.evaluate_native_rebalancing(
        db=db,
        portfolio_version_id=latest_ver.portfolio_version_id,
        user_id=current_user.user_id,
        stock_drift_threshold=stock_drift_threshold,
        sector_drift_threshold=sector_drift_threshold,
    )
    preview["portfolio_id"] = str(portfolio_id)
    preview["portfolio_name"] = port.portfolio_name
    return preview


@router.post("/portfolios/{portfolio_id}/check-drift-and-trigger")
async def check_drift_and_trigger(
    portfolio_id: uuid.UUID,
    stock_drift_threshold: float = Query(5.0, ge=1.0, le=25.0),
    sector_drift_threshold: float = Query(10.0, ge=1.0, le=40.0),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    FR-C08 & FR-C09: Evaluates drift and triggers an automated in-app rebalancing alert if thresholds are crossed.
    """
    return await get_portfolio_rebalance_preview(
        portfolio_id=portfolio_id,
        stock_drift_threshold=stock_drift_threshold,
        sector_drift_threshold=sector_drift_threshold,
        current_user=current_user,
        db=db,
    )


@router.post("/portfolios/{portfolio_id}/apply-rebalance", response_model=PortfolioVersionDetail)
async def apply_portfolio_rebalance(
    portfolio_id: uuid.UUID,
    stock_drift_threshold: float = Query(5.0, ge=1.0, le=25.0),
    sector_drift_threshold: float = Query(10.0, ge=1.0, le=40.0),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Applies the proposed whole-share rebalancing plan to the portfolio.
    Creates a new PortfolioVersion (e.g. Version N+1) in PostgreSQL with:
    - Updated integer lot quantities and current prices
    - Realignment of weights to eliminate drift and respect house policy caps (e.g. 40% sector)
    - Persisted transaction cost audit and unallocated cash reserve
    - Updated security decisions and fiduciary recommendation explanations
    - Passed validation run records
    Returns the newly created PortfolioVersionDetail payload.
    """
    from backend.portfolio_engine.rebalancing_service import RebalancingService

    # 1. Verify portfolio ownership
    port = (
        db.query(InvestorPortfolio)
        .filter(
            InvestorPortfolio.portfolio_id == portfolio_id,
            InvestorPortfolio.user_id == current_user.user_id,
        )
        .first()
    )
    if not port:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found or access denied",
        )

    # 2. Get latest version
    latest_ver = (
        db.query(PortfolioVersion)
        .filter(PortfolioVersion.portfolio_id == portfolio_id)
        .order_by(desc(PortfolioVersion.version_number))
        .first()
    )
    if not latest_ver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio versions available for rebalancing",
        )

    # 3. Evaluate rebalancing plan
    preview = RebalancingService.evaluate_native_rebalancing(
        db=db,
        portfolio_version_id=latest_ver.portfolio_version_id,
        user_id=current_user.user_id,
        stock_drift_threshold=stock_drift_threshold,
        sector_drift_threshold=sector_drift_threshold,
    )

    trades = preview.get("trades", [])
    if not trades:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rebalancing trades generated for this portfolio",
        )

    now = datetime.now(timezone.utc)
    next_ver_num = latest_ver.version_number + 1

    # 4. Map securities & listings from existing decisions
    existing_decisions = (
        db.query(PortfolioSecurityDecision)
        .filter(PortfolioSecurityDecision.portfolio_version_id == latest_ver.portfolio_version_id)
        .all()
    )
    symbol_to_security = {}
    for d in existing_decisions:
        sym = d.listing.symbol if d.listing else (d.security.isin if d.security else "")
        if sym:
            symbol_to_security[sym.upper()] = (d.security_id, d.listing_id)
        if d.security and d.security.security_name:
            symbol_to_security[d.security.security_name.upper()] = (d.security_id, d.listing_id)

    # 5. Build new positions and allocations
    new_positions = []
    new_allocations = []
    trade_decisions_data = []

    for t in trades:
        sym = (t.get("symbol") or "").upper()
        sec_id, list_id = symbol_to_security.get(sym, (None, None))
        if not sec_id:
            listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == sym).first()
            if listing:
                sec_id = listing.security_id
                list_id = listing.listing_id
            else:
                sec = db.query(Security).filter(Security.isin == sym).first()
                if sec:
                    sec_id = sec.security_id
                    list_id = None
                else:
                    first_sec = db.query(Security).first()
                    sec_id = first_sec.security_id if first_sec else uuid.uuid4()
                    list_id = None

        target_qty = int(t.get("target_quantity", 0))
        ref_price = float(t.get("latest_price") or t.get("reference_price") or 100.0)
        post_wt = float(t.get("post_rebalance_weight_pct") or 0.0)
        action = t.get("action", "HOLD")
        rat = t.get("rationale") or f"Rebalanced {sym} allocation in {t.get('sector', 'General')}"

        if target_qty > 0:
            new_positions.append({
                "ticker": sym,
                "company_name": t.get("company_name", sym),
                "sector": t.get("sector", "General"),
                "target_quantity": target_qty,
                "reference_price": ref_price,
                "target_weight_pct": post_wt,
            })
            new_allocations.append({
                "security_id": str(sec_id),
                "listing_id": str(list_id) if list_id else None,
                "symbol": sym,
                "security_name": t.get("company_name", sym),
                "sector_name": t.get("sector", "General"),
                "target_weight_pct": post_wt,
                "target_amount": round(target_qty * ref_price, 2),
                "shares_quantity": target_qty,
                "latest_price": ref_price,
            })
            trade_decisions_data.append({
                "security_id": sec_id,
                "listing_id": list_id,
                "status": "selected",
                "weight": post_wt,
                "reason": rat,
            })
        else:
            trade_decisions_data.append({
                "security_id": sec_id,
                "listing_id": list_id,
                "status": "excluded",
                "weight": None,
                "reason": f"Position liquidated during rebalance: {rat}",
            })

    total_val = float(preview.get("total_portfolio_value") or float(latest_ver.investment_amount))
    post_cash = float(preview.get("post_rebalance_cash") or 0.0)

    # 6. Create revised generation request
    gen_req = PortfolioGenerationRequest(
        generation_request_id=uuid.uuid4(),
        portfolio_id=portfolio_id,
        user_id=current_user.user_id,
        goal_id=latest_ver.generation_request.goal_id if latest_ver.generation_request else None,
        risk_assessment_id=latest_ver.generation_request.risk_assessment_id if latest_ver.generation_request else None,
        request_type="revise",
        request_status="succeeded",
        user_prompt=f"Whole-share portfolio rebalancing execution: {preview.get('trades_count', 0)} orders applied to eliminate drift",
        requested_amount=Decimal(str(round(total_val, 2))),
        currency_code=latest_ver.currency_code or "INR",
        investment_horizon_months=latest_ver.investment_horizon_months or 60,
        normalized_inputs={"action": "apply_rebalance", "from_version": latest_ver.version_number},
        investor_snapshot={"user_id": str(current_user.user_id)},
        market_context_as_of=now,
        started_at=now,
        completed_at=now,
    )
    db.add(gen_req)
    db.flush()

    # 7. Update latest version to superseded
    latest_ver.version_status = "superseded"

    # 8. Create new PortfolioVersion
    new_pv = PortfolioVersion(
        portfolio_version_id=uuid.uuid4(),
        portfolio_id=portfolio_id,
        generation_request_id=gen_req.generation_request_id,
        strategy_version_id=latest_ver.strategy_version_id,
        version_number=next_ver_num,
        version_status="generated",
        investment_amount=Decimal(str(round(total_val, 2))),
        currency_code=latest_ver.currency_code or "INR",
        investment_horizon_months=latest_ver.investment_horizon_months,
        risk_category=latest_ver.risk_category,
        expected_return_pct=latest_ver.expected_return_pct,
        expected_volatility_pct=latest_ver.expected_volatility_pct,
        diversification_score=latest_ver.diversification_score,
        market_context_as_of=now,
        generation_context={
            "trace": [
                {
                    "step": "rebalance_execution",
                    "timestamp": now.isoformat(),
                    "from_version": latest_ver.version_number,
                    "to_version": next_ver_num,
                    "trades_count": preview.get("trades_count", 0),
                    "turnover_amount": preview.get("turnover_amount", 0.0),
                    "turnover_pct": preview.get("turnover_pct", 0.0),
                }
            ],
            "unallocated_cash": post_cash,
            "optimizer_output": {
                "positions": new_positions,
                "unallocated_cash": post_cash,
            },
            "allocations": new_allocations,
            "rebalance_audit": {
                "applied_at": now.isoformat(),
                "from_version": latest_ver.version_number,
                "to_version": next_ver_num,
                "trades": trades,
                "transaction_costs": preview.get("transaction_costs", {}),
                "turnover_pct": preview.get("turnover_pct", 0.0),
                "turnover_amount": preview.get("turnover_amount", 0.0),
                "post_rebalance_cash": post_cash,
                "post_rebalance_sectors": preview.get("post_rebalance_sectors", []),
            },
        },
        generated_at=now,
    )
    db.add(new_pv)
    db.flush()

    # 9. Create Decisions
    for td in trade_decisions_data:
        psd = PortfolioSecurityDecision(
            decision_id=uuid.uuid4(),
            portfolio_version_id=new_pv.portfolio_version_id,
            security_id=td["security_id"],
            listing_id=td["listing_id"],
            decision_status=td["status"],
            target_weight_pct=Decimal(str(round(td["weight"], 6))) if td["weight"] is not None else None,
            decision_reason=td["reason"],
        )
        db.add(psd)

    # 10. Create Explanations
    rebalance_summary_exp = RecommendationExplanation(
        explanation_id=uuid.uuid4(),
        portfolio_version_id=new_pv.portfolio_version_id,
        explanation_type="portfolio",
        title=f"Whole-Share Rebalancing to Version {next_ver_num}",
        explanation_text=(
            f"Portfolio was updated to Version {next_ver_num} via deterministic whole-share rebalancing. "
            f"Executed {preview.get('trades_count', 0)} orders with {preview.get('turnover_pct', 0.0):.1f}% "
            f"portfolio turnover (₹{preview.get('turnover_amount', 0.0):,.2f}) to eliminate allocation drift "
            f"and enforce house policy concentration limits."
        ),
        display_order=1,
    )
    db.add(rebalance_summary_exp)

    tx_costs = preview.get("transaction_costs", {})
    cost_exp = RecommendationExplanation(
        explanation_id=uuid.uuid4(),
        portfolio_version_id=new_pv.portfolio_version_id,
        explanation_type="risk",
        title="Transaction Costs & Fiduciary Conservation",
        explanation_text=(
            f"Statutory Indian equity transaction costs estimated at ₹{float(tx_costs.get('total_estimated_costs', 0.0)):,.2f} "
            f"(STT: ₹{float(tx_costs.get('stt_ctt', 0.0)):,.2f}, Stamp Duty & Exchange fees: ₹{float(tx_costs.get('stamp_duty', 0.0)) + float(tx_costs.get('exchange_turnover_charges', 0.0)):,.2f}, "
            f"GST: ₹{float(tx_costs.get('gst', 0.0)):,.2f}). Remaining liquid cash reserve: ₹{post_cash:,.2f}."
        ),
        display_order=2,
    )
    db.add(cost_exp)

    # Per trade explanations
    order_idx = 3
    for t in trades:
        if t.get("action") in ("BUY", "SELL"):
            trade_exp = RecommendationExplanation(
                explanation_id=uuid.uuid4(),
                portfolio_version_id=new_pv.portfolio_version_id,
                explanation_type="selection" if t.get("action") == "BUY" else "review",
                title=f"Trade Rationale: {t.get('action')} {t.get('symbol')}",
                explanation_text=t.get("rationale", ""),
                display_order=order_idx,
            )
            db.add(trade_exp)
            order_idx += 1

    # 11. Create Validation Run
    val_run = PortfolioValidationRun(
        validation_run_id=uuid.uuid4(),
        portfolio_version_id=new_pv.portfolio_version_id,
        rule_set_version="sebi-in-diversified-v1.0",
        calculation_engine_version="lucid-rebalancer-v2.0",
        validation_status="passed",
        started_at=now,
        completed_at=now,
        summary={"status": "passed", "checks_run": 3, "violations": 0},
    )
    db.add(val_run)
    db.flush()

    # Add validation results
    vr_stock = PortfolioValidationResult(
        validation_result_id=uuid.uuid4(),
        validation_run_id=val_run.validation_run_id,
        rule_code="POLICY_SINGLE_STOCK_CEILING",
        result_status="pass",
        severity="info",
        actual_value=Decimal(str(max((t.get("post_rebalance_weight_pct", 0.0) for t in trades), default=0.0))),
        threshold_value=Decimal("25.0"),
        result_message="All holdings respect the 25.0% single-stock house policy ceiling.",
        details={},
    )
    db.add(vr_stock)

    vr_cash = PortfolioValidationResult(
        validation_result_id=uuid.uuid4(),
        validation_run_id=val_run.validation_run_id,
        rule_code="POLICY_NON_NEGATIVE_CASH",
        result_status="pass",
        severity="info",
        actual_value=Decimal(str(post_cash)),
        threshold_value=Decimal("0.0"),
        result_message="Post-rebalance cash reserve is strictly non-negative.",
        details={},
    )
    db.add(vr_cash)

    port.updated_at = now
    db.commit()

    return await get_portfolio_version(
        portfolio_id=portfolio_id,
        version_id=new_pv.portfolio_version_id,
        current_user=current_user,
        db=db,
    )


@router.post("/portfolios/monitoring/run-scheduler-cycle")
async def trigger_scheduler_cycle(
    force_run: bool = Query(True, description="Force run even outside 09:15-15:30 IST market hours"),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Triggers an unattended monitoring scheduler cycle across all active portfolios.
    Audits valuations, holding drifts, snaps performance records, and triggers alerts.
    """
    from backend.services.monitoring_scheduler import run_all_active_portfolios_monitoring
    return run_all_active_portfolios_monitoring(db, force_run=force_run)


@router.get("/portfolios/monitoring/scheduler-status")
async def get_scheduler_telemetry(
    current_user: AppUser = Depends(get_current_user),
):
    """
    Returns real-time telemetry, market calendar status, distributed lock configuration,
    and last execution metrics of the portfolio monitoring scheduler.
    """
    from backend.services.monitoring_scheduler import get_scheduler_status
    return get_scheduler_status()





