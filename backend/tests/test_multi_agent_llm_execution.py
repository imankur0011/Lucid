"""
Multi-Agent LLM Execution and Specialist Node Verification Test Suite.
Validates:
1. Dedicated execution of all 6 specialist agents:
   - Macro Analyst (macro_analyst_node)
   - Market Analyst (market_analyst_node)
   - Fundamental Analyst (fundamental_analyst_node)
   - News & Corporate Filings Analyst (news_analyst_node)
   - Lead Strategist (analyst_node)
   - Independent Risk Critic (critic_node)
2. Strict Pydantic output schemas and financial evidence models.
3. Deterministic fallback mode without API keys.
4. Genuine LLM invocation path with financial context delivery and model identification.
5. End-to-end LangGraph execution with optimizer and Critic final validation.
"""

import uuid
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from backend.database import SessionLocal
from backend.agent.graph import create_portfolio_graph
from backend.agent.schemas import (
    MacroAnalystOutput,
    MarketAnalystOutput,
    FundamentalAnalystOutput,
    NewsAnalystOutput,
    StrategistOutput,
    CriticOutput,
    CriticVerdictStatus,
)
from backend.agent.nodes import (
    manager_node,
    suitability_check_node,
    macro_analyst_node,
    market_analyst_node,
    fundamental_analyst_node,
    news_analyst_node,
    analyst_node,
    critic_node,
    deterministic_optimizer_node,
    critic_final_validation_node,
    moderator_explanation_node,
)


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for agent verification."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def base_test_state():
    """Constructs a standard, valid PortfolioAgentState for specialist testing."""
    return {
        "portfolio_id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "investment_amount": 200000.0,
        "risk_category": "moderate",
        "investment_horizon_months": 60,
        "user_prompt": "I want a diversified, long-term wealth creation portfolio with bluechip Indian stocks.",
        "critic_iteration": 0,
        "rework_count": 0,
        "max_rework_count": 2,
        "agent_messages": [],
        "evidence_registry": {},
        "execution_trace": [],
        "eligible_candidates": [
            {
                "symbol": "RELIANCE",
                "security_name": "Reliance Industries Ltd.",
                "sector_name": "Energy",
                "latest_price": 2500.0,
                "composite_score": 85.0,
                "pe_ratio": 24.5,
                "roe_pct": 14.2,
                "market_cap": 1700000.0,
            },
            {
                "symbol": "TCS",
                "security_name": "Tata Consultancy Services Ltd.",
                "sector_name": "Information Technology",
                "latest_price": 3500.0,
                "composite_score": 88.0,
                "pe_ratio": 28.0,
                "roe_pct": 38.5,
                "market_cap": 1300000.0,
            },
            {
                "symbol": "HDFCBANK",
                "security_name": "HDFC Bank Ltd.",
                "sector_name": "Financial Services",
                "latest_price": 1600.0,
                "composite_score": 86.0,
                "pe_ratio": 19.5,
                "roe_pct": 16.8,
                "market_cap": 1200000.0,
            },
            {
                "symbol": "ITC",
                "security_name": "ITC Ltd.",
                "sector_name": "Fast Moving Consumer Goods",
                "latest_price": 420.0,
                "composite_score": 82.0,
                "pe_ratio": 26.0,
                "roe_pct": 29.0,
                "market_cap": 520000.0,
            },
            {
                "symbol": "LT",
                "security_name": "Larsen & Toubro Ltd.",
                "sector_name": "Capital Goods",
                "latest_price": 3400.0,
                "composite_score": 84.0,
                "pe_ratio": 32.0,
                "roe_pct": 15.5,
                "market_cap": 460000.0,
            },
        ],
    }


class MockLLMResponse:
    """Mock LangChain AIMessage response."""
    def __init__(self, content: str):
        self.content = content


class MockLangChainLLM:
    """Mock LangChain chat model implementing invoke."""
    def __init__(self, model_name: str = "gemini-3.8-flash"):
        self.model = model_name
        self.invocations = []

    def invoke(self, messages):
        self.invocations.append(messages)
        # Return intelligent fiduciary commentary
        prompt_str = " ".join([m.content for m in messages if hasattr(m, "content")])
        if "macro" in prompt_str.lower():
            return MockLLMResponse("Indian macroeconomic backdrop demonstrates resilient domestic GDP growth amidst steady policy rates and moderated headline CPI.")
        elif "breadth" in prompt_str.lower() or "technical" in prompt_str.lower():
            return MockLLMResponse("Market breadth exhibits broad-market accumulation above the 50-DMA with moderate dispersion and favorable risk-reward.")
        elif "governance" in prompt_str.lower() or "disclosures" in prompt_str.lower():
            return MockLLMResponse("Regulatory disclosures and corporate filings reflect clean auditor certifications with zero adverse statutory observations.")
        elif "balance sheet" in prompt_str.lower() or "equity research" in prompt_str.lower():
            return MockLLMResponse("Candidate equity universe displays robust return on equity, prudent net debt-to-EBITDA, and durable competitive moats.")
        elif "strategist" in prompt_str.lower() or "strategy" in prompt_str.lower():
            return MockLLMResponse("Recommend core-satellite asset allocation with high-conviction large-cap leaders balancing growth and defensiveness.")
        elif "critic" in prompt_str.lower() or "compliance" in prompt_str.lower():
            return MockLLMResponse("Independent fiduciary risk review confirms all holdings satisfy single-stock ≤25% and sector ≤40% safety caps.")
        return MockLLMResponse("Fiduciary analysis completed in compliance with internal risk limits and SEBI suitability standards.")


class TestSpecialistAgentExecution:
    """Validates individual agent execution in both deterministic and LLM-enriched modes."""

    def test_macro_analyst_deterministic_mode(self, db_session, base_test_state):
        with patch("backend.agent.nodes.get_llm", return_value=None):
            out = macro_analyst_node(base_test_state, db_session)
            assert "macro_output" in out
            macro = MacroAnalystOutput.model_validate(out["macro_output"])
            assert macro.regime in ("BULL", "BEAR", "SIDEWAYS", "HIGH_VOLATILITY")
            assert macro.vix > 0
            assert macro.rbi_repo_rate > 0
            assert len(macro.evidence_items) > 0
            assert "evidence_registry" in out

    def test_macro_analyst_llm_mode(self, db_session, base_test_state):
        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out = macro_analyst_node(base_test_state, db_session)
            macro = MacroAnalystOutput.model_validate(out["macro_output"])
            assert len(mock_llm.invocations) == 1
            assert macro.model_name == "gemini-3.8-flash"
            assert "resilient domestic GDP growth" in macro.macro_summary

    def test_market_analyst_deterministic_and_llm(self, db_session, base_test_state):
        # 1. Deterministic
        with patch("backend.agent.nodes.get_llm", return_value=None):
            out_det = market_analyst_node(base_test_state, db_session)
            market_det = MarketAnalystOutput.model_validate(out_det["market_output"])
            assert market_det.candidates_evaluated == len(base_test_state["eligible_candidates"])
            assert market_det.market_breadth_score > 0

        # 2. LLM Enriched
        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out_llm = market_analyst_node(base_test_state, db_session)
            market_llm = MarketAnalystOutput.model_validate(out_llm["market_output"])
            assert len(mock_llm.invocations) == 1
            assert market_llm.model_name == "gemini-3.8-flash"
            assert "Market breadth exhibits" in market_llm.market_summary

    def test_fundamental_analyst_execution(self, db_session, base_test_state):
        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out = fundamental_analyst_node(base_test_state, db_session)
            fund = FundamentalAnalystOutput.model_validate(out["fundamental_output"])
            assert len(fund.companies_analyzed) > 0
            assert len(mock_llm.invocations) == 1
            assert fund.model_name == "gemini-3.8-flash"
            assert any(f.category == "QUALITY" for f in fund.findings)

    def test_news_analyst_execution(self, db_session, base_test_state):
        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out = news_analyst_node(base_test_state, db_session)
            news = NewsAnalystOutput.model_validate(out["news_output"])
            assert news.sentiment_score >= 0
            assert news.model_name == "gemini-3.8-flash"
            assert "auditor certifications" in news.news_summary

    def test_lead_strategist_execution(self, base_test_state):
        # Provide previous specialist outputs in state
        state = dict(base_test_state)
        state["macro_output"] = {"regime": "BULL", "vix": 14.5}
        state["market_output"] = {"technical_posture": "ACCUMULATION"}
        state["fundamental_output"] = {"companies_analyzed": []}
        state["news_output"] = {"sentiment_score": 75.0}

        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out = analyst_node(state)
            assert "strategist_output" in out
            strat = StrategistOutput.model_validate(out["strategist_output"])
            assert strat.execution_status == "SUCCESS"
            assert strat.investment_strategy is not None
            assert len(strat.proposed_candidates) > 0
            assert len(mock_llm.invocations) == 1

    def test_critic_fiduciary_audit_execution(self, base_test_state):
        mock_llm = MockLangChainLLM("gemini-3.8-flash")
        with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
            out = critic_node(base_test_state)
            assert "critic_output" in out
            critic = CriticOutput.model_validate(out["critic_output"])
            assert critic.decision in ("APPROVED", "REWORK_REQUIRED", "BLOCKED_VIOLATION")
            assert out["critic_approved"] is True or out["critic_approved"] is False
            assert "agent_messages" in out
            assert len(out["agent_messages"]) > 0


class TestFullAgentWorkflowAndDecoupling:
    """Verifies end-to-end LangGraph pipeline execution, deterministic constraint validation, and non-custodial separation."""

    def test_end_to_end_graph_execution(self, db_session, base_test_state):
        from backend.models.users import AppUser
        from backend.models.portfolio import InvestorPortfolio, PortfolioGenerationRequest
        from backend.models.security import Security, InstrumentListing

        # Ensure test user, portfolio, and request exist in DB for persistence node
        test_email = f"agent_test_{uuid.uuid4().hex[:6]}@example.com"
        user = AppUser(
            user_id=uuid.uuid4(),
            identity_subject=f"sub_{uuid.uuid4().hex[:8]}",
            email=test_email,
            password_hash="test_hash",
            email_verified=True,
            account_status="active",
        )
        db_session.add(user)
        db_session.flush()

        port = InvestorPortfolio(
            portfolio_id=uuid.uuid4(),
            user_id=user.user_id,
            portfolio_name="Multi-Agent Execution Test Portfolio",
            portfolio_status="active",
        )
        db_session.add(port)
        db_session.flush()

        gen_req = PortfolioGenerationRequest(
            generation_request_id=uuid.uuid4(),
            portfolio_id=port.portfolio_id,
            user_id=user.user_id,
            requested_amount=200000.0,
            user_prompt="I want a diversified, long-term wealth creation portfolio with bluechip Indian stocks.",
            request_type="create",
            request_status="queued",
            investment_horizon_months=60,
            currency_code="INR",
            normalized_inputs={},
            investor_snapshot={},
        )
        db_session.add(gen_req)
        db_session.commit()

        # Wire valid IDs and securities into state
        state = dict(base_test_state)
        state["generation_request_id"] = str(gen_req.generation_request_id)
        state["portfolio_id"] = str(port.portfolio_id)
        state["user_id"] = str(user.user_id)
        state["current_stage"] = "manager"
        state["status"] = "starting"

        # Populate security_id from DB if present
        for c in state["eligible_candidates"]:
            sym = c["symbol"]
            sec = db_session.query(Security).join(InstrumentListing).filter(InstrumentListing.symbol == sym).first()
            if sec:
                c["security_id"] = str(sec.security_id)
            else:
                c["security_id"] = str(uuid.uuid4())

        graph = create_portfolio_graph(db_session)
        final_state = graph.invoke(state)

        # Assert lifecycle stages completed
        trace_steps = [s["step"] for s in final_state.get("execution_trace", [])]
        assert "manager" in trace_steps
        assert "suitability_check" in trace_steps or "suitability" in trace_steps
        assert "macro_analyst" in trace_steps
        assert "market_analyst" in trace_steps
        assert "fundamental_analyst" in trace_steps
        assert "news_analyst" in trace_steps
        assert "lead_strategist" in trace_steps or "analyst" in trace_steps
        assert "critic" in trace_steps

        # Assert deterministic optimizer executed mathematical weights
        assert "optimizer_output" in final_state
        opt = final_state["optimizer_output"]
        assert opt["optimization_status"] == "OPTIMAL"
        assert opt["execution_status"] == "SUCCESS"
        assert len(opt["positions"]) >= 3
        # Strict integer whole shares invariant
        for p in opt["positions"]:
            assert isinstance(p["target_quantity"], int)
            assert p["target_quantity"] >= 0
            # Strict single-stock limit invariant (≤25.0%)
            assert p["target_weight_pct"] <= 25.001

        # Assert cash conservation
        assert float(opt["unallocated_cash"]) >= 0.0

        # Assert post-optimizer Critic Final Validation executed
        assert "critic_final_output" in final_state
        assert final_state["critic_final_output"]["decision"] == "APPROVED"

        # Assert plain-language explanations produced by Moderator
        assert "explanations" in final_state
        exps = final_state["explanations"]
        assert len(exps) >= 3
        portfolio_exp = next((e for e in exps if e.get("explanation_type") == "portfolio"), None)
        assert portfolio_exp is not None
        assert "Disciplined" in portfolio_exp["title"]
        assert "moderator_output" in final_state
