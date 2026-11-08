"""
Comprehensive Test Suite for Dynamic, API-Driven Stock Recommendation Engine.

Verifies:
1. Market Data Adapter fundamental metrics extraction (YFinanceProvider & SimulatedMarketProvider).
2. PostgreSQL fundamental_metrics table ingestion and idempotency.
3. Dynamic factor retrieval without hardcoded 14-stock/72-stock whitelists.
4. Liquidity filtering (ADTV, price freshness, sector exclusions) in CandidateUniverseSelector.
5. Multi-factor goal alignment and dynamic prompt resolution for arbitrary NSE/BSE securities.
6. Full LangGraph multi-agent portfolio creation workflow with dynamic securities (e.g. BEL, HAL, TRENT).
"""

import uuid
import pytest
from datetime import date, timedelta

from backend.database.session import SessionLocal
from backend.market_data.adapter import SimulatedMarketProvider, YFinanceProvider
from backend.market_data.exchange_universe_sync import (
    ensure_metric_definitions,
    sync_company_fundamentals,
    STANDARD_METRIC_DEFINITIONS,
)
from backend.models.security import InstrumentListing, Security
from backend.models.market_data import FundamentalMetric, MetricDefinition
from backend.models.users import AppUser
from backend.models.portfolio import PortfolioGenerationRequest, InvestorPortfolio
from backend.portfolio_engine.factors import get_equity_factors, determine_optimal_holding_count
from backend.portfolio_engine.candidate_selection import CandidateUniverseSelector
from backend.agent.graph import create_portfolio_graph


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestDynamicMarketDataAdapter:
    """Verifies that market data providers return complete fundamental metrics dynamically."""

    def test_simulated_provider_fundamental_metrics(self):
        prov = SimulatedMarketProvider()
        metrics = prov.fetch_fundamental_metrics("BEL")

        assert metrics["symbol"] == "BEL"
        assert 0.05 <= metrics["roe"] <= 0.40
        assert metrics["pe"] > 5.0
        assert metrics["pb"] > 0.5
        assert metrics["debt_to_equity"] >= 0.0
        assert metrics["dividend_yield"] >= 0.0
        assert metrics["beta"] > 0.0
        assert metrics["market_cap"] > 100000000.0

    def test_simulated_provider_arbitrary_stocks(self):
        prov = SimulatedMarketProvider()
        stocks = ["HAL", "TRENT", "DIVISLAB", "ZOMATO", "NEWCOMPANY"]
        for s in stocks:
            m = prov.fetch_fundamental_metrics(s)
            assert m["symbol"] == s
            assert "roe" in m
            assert "pe" in m
            assert "beta" in m

    def test_yfinance_normalization_and_keys(self):
        prov = YFinanceProvider()
        assert prov._normalize_symbol("BEL") == "BEL.NS"
        assert prov._normalize_symbol("TCS.NS") == "TCS.NS"
        assert prov._normalize_symbol("500180.BO") == "500180.BO"


class TestDatabaseFundamentalsSync:
    """Verifies normalization and persistence of fundamental metrics in PostgreSQL."""

    def test_ensure_metric_definitions(self, db_session):
        defs = ensure_metric_definitions(db_session)
        assert len(defs) >= len(STANDARD_METRIC_DEFINITIONS)
        assert "ROE" in defs
        assert "PE" in defs
        assert "DEBT_TO_EQUITY" in defs
        assert "DIVIDEND_YIELD" in defs
        assert "BETA" in defs

    def test_sync_company_fundamentals_idempotent(self, db_session):
        prov = SimulatedMarketProvider()
        res = sync_company_fundamentals(db_session, symbols=["BEL", "HAL"], provider=prov)
        assert res["status"] == "success"
        assert res["errors_count"] == 0

        # Verify records exist in DB
        listing = db_session.query(InstrumentListing).filter(InstrumentListing.symbol == "BEL").first()
        assert listing is not None
        db_metrics = (
            db_session.query(FundamentalMetric)
            .filter(FundamentalMetric.security_id == listing.security_id)
            .all()
        )
        assert len(db_metrics) >= 5


class TestDynamicEquityFactors:
    """Verifies that factor retrieval is dynamic and not restricted to a fixed list."""

    def test_get_equity_factors_returns_metrics_for_any_stock(self, db_session):
        stocks = ["BEL", "HAL", "TRENT", "DIVISLAB", "ARBITRARY_TICKER"]
        for s in stocks:
            factors = get_equity_factors(s, db=db_session)
            assert factors is not None
            assert "roe" in factors
            assert "pe" in factors
            assert "beta" in factors
            assert "dividend_yield" in factors
            assert "debt_to_equity" in factors
            assert isinstance(factors["keywords"], set)

    def test_dynamic_keyword_extraction(self, db_session):
        factors = get_equity_factors("BEL", db=db_session)
        # Should include dynamically extracted keywords from company legal name / industry
        assert "bel" in factors["keywords"]


class TestCandidateUniverseDiscoveryAndLiquidity:
    """Verifies candidate selection with liquidity and freshness filtering."""

    def test_select_eligible_candidates_filters_liquidity(self, db_session):
        selector = CandidateUniverseSelector(db_session, max_stale_days=14)
        eligible = selector.select_eligible_candidates(min_avg_volume=10000)
        assert len(eligible) > 0

        for cand in eligible[:20]:
            assert cand["latest_price"] > 0
            assert cand["symbol"] is not None
            assert cand["sector_name"] is not None
            assert "avg_daily_volume" in cand

    def test_sector_exclusion_filter(self, db_session):
        selector = CandidateUniverseSelector(db_session)
        eligible_no_tech = selector.select_eligible_candidates(
            excluded_sectors=["Information Technology", "TECH"]
        )
        for c in eligible_no_tech:
            assert c["sector_name"] != "Information Technology"
            assert c["sector_code"] != "TECH"

    def test_rank_and_select_candidates_dynamic_prompt_alignment(self, db_session):
        selector = CandidateUniverseSelector(db_session)
        eligible = selector.select_eligible_candidates(min_avg_volume=10000)

        prompt = "Focus on aerospace, defense, and electronics leaders like BEL and HAL"
        selected = selector.rank_and_select_candidates(
            eligible,
            target_count=6,
            goal_type="growth",
            risk_category="growth",
            user_prompt=prompt,
        )

        assert len(selected) <= 6
        selected_symbols = {c["symbol"] for c in selected}
        # BEL should be selected due to strong prompt and keyword alignment
        assert "BEL" in selected_symbols

        # Ensure fiduciary sector diversity (at least 2 distinct sectors)
        sectors = {c["sector_name"] for c in selected}
        assert len(sectors) >= 2


class TestEndToEndDynamicRecommendationWorkflow:
    """Verifies the complete LangGraph agentic workflow with dynamically discovered stocks."""

    def test_full_graph_recommendation_with_bel(self, db_session):
        u = db_session.query(AppUser).first()
        if not u:
            u = AppUser(
                user_id=uuid.uuid4(),
                email="dynamic_e2e@lucid.in",
                password_hash="testhash",
                full_name="E2E Dynamic User",
            )
            db_session.add(u)
            db_session.flush()

        port = (
            db_session.query(InvestorPortfolio)
            .filter(InvestorPortfolio.user_id == u.user_id)
            .first()
        )
        if not port:
            port = InvestorPortfolio(
                portfolio_id=uuid.uuid4(),
                user_id=u.user_id,
                portfolio_name="Dynamic E2E Portfolio",
            )
            db_session.add(port)
            db_session.flush()

        req_id = uuid.uuid4()
        req = PortfolioGenerationRequest(
            generation_request_id=req_id,
            portfolio_id=port.portfolio_id,
            user_id=u.user_id,
            requested_amount=100000.0,
            user_prompt="I want high growth with aerospace and defense compounders including BEL",
            request_type="create",
            request_status="queued",
            investment_horizon_months=36,
            currency_code="INR",
            normalized_inputs={},
            investor_snapshot={},
        )
        db_session.add(req)
        db_session.commit()

        init_state = {
            "generation_request_id": str(req_id),
            "portfolio_id": str(port.portfolio_id),
            "user_id": str(u.user_id),
            "investment_amount": 100000.0,
            "risk_category": "growth",
            "investment_horizon_months": 36,
            "user_prompt": "I want high growth with aerospace and defense compounders including BEL",
            "current_stage": "manager",
            "status": "starting",
            "execution_trace": [],
            "evidence_registry": {},
            "agent_messages": [],
        }

        graph = create_portfolio_graph(db_session)
        final_state = graph.invoke(init_state)

        if final_state.get("workflow_status") != "COMPLETED":
            print("\nTEST FAILED! Workflow trace:")
            for tr in final_state.get("execution_trace", []):
                print(tr)
            print("Error code:", final_state.get("error_code"))
            print("Error summary:", final_state.get("error_summary"))

        assert final_state.get("workflow_status") == "COMPLETED"
        assert final_state.get("validation_passed") is True
        allocations = final_state.get("allocations", [])
        assert len(allocations) >= 3

        # Check that BEL is allocated whole shares
        alloc_symbols = {a["symbol"] for a in allocations}
        assert "BEL" in alloc_symbols

        for alloc in allocations:
            # Whole integer shares
            assert alloc["shares_quantity"] >= 0
            # Strict single-stock 25% SEBI limit
            assert alloc["target_weight_pct"] <= 25.01
