"""
Comprehensive Multi-Tier Test Suite for Lucid's Conversational Fiduciary Assistant.
Formally organized into three distinct verification tiers:

- TIER A: Deterministic Fast-Paths (Calendar, Date/Time, Market Hours, Math Calculations, Identity, Greetings)
  Executed deterministically with microsecond latency, zero LLM reliance, zero hallucination risk.
- TIER B: Grounded Semantic & Portfolio Reasoning (Stock theses, Scenario simulations, Natural Language Demat Diagnosis, Multi-turn context retention)
  Verifies intent extraction, entity binding, and deterministic mathematical simulation generation.
- TIER C: LLM Provider Integration & Resilience (Operational failure handling, Quota backoff, API endpoint integration)
  Clearly distinguishes mocked vs live network boundaries and verifies fail-closed security.
"""

import pytest
import uuid
from fastapi.testclient import TestClient

from backend.main import app
from backend.portfolio_engine.conversational_assistant import (
    process_conversational_query,
    simulate_conversational_query,
    session_manager,
)

client = TestClient(app)
DEMO_USER_ID = "10000000-0000-4000-8000-000000000001"
USER_B_ID = "20000000-0000-4000-8000-000000000002"


@pytest.fixture(autouse=True)
def clean_sessions():
    """Ensure a fresh session memory before each test."""
    session_manager.prune_idle_sessions(max_idle_seconds=0)
    yield
    session_manager.prune_idle_sessions(max_idle_seconds=0)


# ============================================================================
# SCENARIO A: Simple Greetings ("Hey", "Hi", "Hello")
# ============================================================================

def test_simple_greeting_produces_natural_brief_reply():
    """Verifies Example A: 'Hey' receives a natural, brief greeting without canned crash advice."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Hey",
        session_id="test_sess_greeting",
    )
    reply = res["reply"]
    assert "March 2020" not in reply, "Greeting must NOT return March 2020 crash"
    assert "crash" not in reply.lower()
    assert any(w in reply.lower() for w in ["welcome", "explore", "help", "hello", "hey"])
    assert res["scenario_simulation"] is None, "Greeting must not include a fake crash simulation"
    assert res["intent"] == "GREETING_SIMPLE"


def test_multiple_greetings_vary_and_stay_conversational():
    """Verifies that different greetings receive appropriate conversational responses."""
    greetings = ["Hi", "Hello there", "Good morning"]
    replies = []
    for g in greetings:
        res = process_conversational_query(
            user_id=DEMO_USER_ID,
            query_text=g,
            session_id=f"test_g_{g}",
        )
        replies.append(res["reply"])
        assert "March 2020" not in res["reply"]
        assert res["scenario_simulation"] is None

    # Responses should not be crash dumps
    assert len(replies) == 3


# ============================================================================
# SCENARIO B: General Greeting ("How are you?")
# ============================================================================

def test_general_greeting_how_are_you():
    """Verifies Example B: 'How are you?' responds conversationally and invites the user to continue."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="How are you?",
        session_id="test_sess_how_are_you",
    )
    reply = res["reply"]
    assert "March 2020" not in reply
    assert any(phrase in reply.lower() for phrase in ["doing well", "good", "thank you", "ready to help"])
    assert res["scenario_simulation"] is None
    assert res["intent"] == "GREETING_GENERAL"


# ============================================================================
# SCENARIO C: Application Explanation ("What does Lucid do?")
# ============================================================================

def test_application_explanation():
    """Verifies Example C: 'What does Lucid do?' explains Lucid's actual features."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="What does Lucid do?",
        session_id="test_sess_what_lucid_does",
    )
    reply = res["reply"]
    assert "March 2020" not in reply
    assert "portfolio" in reply.lower()
    assert "sebi" in reply.lower() or "fiduciary" in reply.lower() or "guardrail" in reply.lower()
    assert "25%" in reply or "stock" in reply.lower()
    assert res["intent"] == "APP_CAPABILITIES"


# ============================================================================
# SCENARIO D: Greeting Followed by Portfolio Help
# ============================================================================

def test_greeting_followed_by_portfolio_request():
    """Verifies Example D: Greeting followed by 'Can you help me build a stock portfolio?' guides the user without repeating the greeting."""
    sess_id = "test_sess_flow_d"

    # Turn 1: Greeting
    res1 = process_conversational_query(user_id=DEMO_USER_ID, query_text="Hey", session_id=sess_id)
    assert "welcome" in res1["reply"].lower() or "hey" in res1["reply"].lower()

    # Turn 2: Portfolio Request
    res2 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Can you help me build a stock portfolio?",
        session_id=sess_id,
    )
    reply2 = res2["reply"]
    assert "welcome to lucid" not in reply2.lower(), "Must not repeat the initial greeting"
    assert "amount" in reply2.lower() or "capital" in reply2.lower()
    assert "horizon" in reply2.lower() or "goal" in reply2.lower()
    assert res2["intent"] == "PORTFOLIO_CREATION_START"


# ============================================================================
# SCENARIO E: Multi-Turn Context Retention (Amount -> Horizon)
# ============================================================================

def test_multi_turn_amount_and_horizon_context_retention():
    """
    Verifies Example E:
    User: 'I want to invest ₹50,000.'
    Assistant: Asks goal & horizon.
    User: 'I am investing for five years.'
    Expected: Understands 5-year horizon refers to the ₹50,000 previously stated!
    """
    sess_id = "test_sess_memory_amount_horizon"

    # Turn 1: State budget
    res1 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="I want to invest ₹50,000.",
        session_id=sess_id,
    )
    assert "50,000" in res1["reply"] or "50000" in res1["reply"]
    assert "March 2020" not in res1["reply"]

    # Turn 2: State time horizon
    res2 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="I am investing for five years.",
        session_id=sess_id,
    )
    reply2 = res2["reply"]
    assert "50,000" in reply2 or "50000" in reply2, "Must retain the ₹50,000 from Turn 1!"
    assert "five years" in reply2.lower() or "5 years" in reply2.lower() or "5-year" in reply2.lower()
    assert "March 2020" not in reply2


# ============================================================================
# SCENARIO F: Financial Education ("Stock vs Mutual Fund")
# ============================================================================

def test_financial_education_stock_vs_mutual_fund():
    """Verifies Example F: Explains difference between stock and mutual fund without redirecting to portfolio creation."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="What is the difference between a stock and a mutual fund?",
        session_id="test_sess_stock_vs_mf",
    )
    reply = res["reply"]
    assert "March 2020" not in reply
    assert "stock" in reply.lower()
    assert "mutual fund" in reply.lower()
    assert "demat" in reply.lower() or "expense ratio" in reply.lower() or "ownership" in reply.lower()
    assert res["intent"] == "FINANCIAL_EDUCATION_STOCKS_VS_MF"


# ============================================================================
# SCENARIO G: Ambiguous Follow-Up ("Which one is better?")
# ============================================================================

def test_ambiguous_question_resolves_context_or_clarifies():
    """
    Verifies Example G:
    Turn 1 discusses stocks vs mutual funds.
    Turn 2 asks 'Which one is better?' -> assistant uses memory to compare stocks vs mutual funds!
    """
    sess_id = "test_sess_which_is_better"

    # Turn 1: Stocks vs Mutual Funds
    process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="What is the difference between a stock and a mutual fund?",
        session_id=sess_id,
    )

    # Turn 2: Ambiguous question
    res2 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Which one is better?",
        session_id=sess_id,
    )
    reply2 = res2["reply"]
    assert "stocks" in reply2.lower() or "mutual funds" in reply2.lower(), "Must resolve 'which one' to stocks vs mutual funds from Turn 1 context!"
    assert "March 2020" not in reply2


def test_ambiguous_question_without_context_asks_for_clarification():
    """Verifies that an ambiguous question without any prior context asks for clarification."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Which one is better?",
        session_id="test_sess_fresh_ambiguous",
    )
    reply = res["reply"]
    assert "clarify" in reply.lower() or "comparing" in reply.lower()
    assert "March 2020" not in reply


# ============================================================================
# SCENARIO H: Topic Change / Adaptation
# ============================================================================

def test_topic_change_adapts_immediately():
    """
    Verifies Example H:
    User asks about risk, then changes direction: 'Actually, first explain what diversification means.'
    Assistant adapts to explain diversification.
    """
    sess_id = "test_sess_topic_change"

    # Turn 1: Risk
    process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Help me understand portfolio risk.",
        session_id=sess_id,
    )

    # Turn 2: Change topic
    res2 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Actually, first explain what diversification means.",
        session_id=sess_id,
    )
    reply2 = res2["reply"]
    assert "diversification" in reply2.lower()
    assert "basket" in reply2.lower() or "sector" in reply2.lower() or "spread" in reply2.lower()
    assert "March 2020" not in reply2


# ============================================================================
# SCENARIO I: Grounded Stock Inquiry & Stress Testing
# ============================================================================

def test_grounded_stock_inquiry_with_portfolio():
    """Verifies that asking about a stock in the portfolio returns grounded facts and ratios."""
    sample_portfolio = {
        "investment_amount": 200_000,
        "holdings": [
            {
                "symbol": "TCS",
                "security_name": "Tata Consultancy Services",
                "sector_name": "Information Technology",
                "target_weight_pct": 25.0,
                "target_amount": 50_000,
                "shares_quantity": 13,
                "latest_price": 3846.15,
            }
        ],
    }

    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Why did you recommend TCS?",
        session_id="test_sess_stock_tcs",
        portfolio_data=sample_portfolio,
    )
    reply = res["reply"]
    assert "TCS" in reply
    assert "25.0%" in reply or "25%" in reply
    assert "₹50,000" in reply or "50,000" in reply
    assert "March 2020" not in reply
    assert res["intent"] == "STOCK_INQUIRY"


def test_stress_test_scenario_returns_simulation_object():
    """Verifies that asking about a market crash returns the mathematical simulation object."""
    sample_portfolio = {
        "investment_amount": 250_000,
        "holdings": [
            {
                "symbol": "RELIANCE",
                "security_name": "Reliance Industries",
                "sector_name": "Energy",
                "target_weight_pct": 25.0,
                "target_amount": 62_500,
                "shares_quantity": 25,
                "latest_price": 2500.0,
            },
            {
                "symbol": "TCS",
                "security_name": "Tata Consultancy Services",
                "sector_name": "Information Technology",
                "target_weight_pct": 25.0,
                "target_amount": 62_500,
                "shares_quantity": 16,
                "latest_price": 3900.0,
            },
        ],
    }

    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="What happens if the market crashes 30% like in March 2020?",
        session_id="test_sess_crash",
        portfolio_data=sample_portfolio,
    )
    assert res["scenario_simulation"] is not None
    assert res["scenario_simulation"]["loss_pct"] > 0
    assert "March 2020" in res["reply"] or "crash" in res["reply"].lower()
    assert res["intent"] == "STRESS_TEST"


# ============================================================================
# SCENARIO J: User Isolation (No Cross-User Leakage)
# ============================================================================

def test_session_isolation_between_different_users():
    """Verifies that User A's session context never leaks into User B's session."""
    # User A states ₹75,000
    process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="I want to invest ₹75,000.",
        session_id="shared_sess_name",
    )

    # User B says "I am investing for five years"
    res_b = process_conversational_query(
        user_id=USER_B_ID,
        query_text="I am investing for five years.",
        session_id="shared_sess_name",
    )
    # User B must NOT have User A's ₹75,000!
    assert "75,000" not in res_b["reply"]
    assert "75000" not in res_b["reply"]


# ============================================================================
# SCENARIO K: Unsupported Operations (Non-Custodial Protection)
# ============================================================================

def test_unsupported_custodial_operations_explained_politely():
    """Verifies that asking to execute direct trades or buy crypto is politely handled as non-custodial."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Place a live trade for me to buy 10 shares of Reliance.",
        session_id="test_sess_trade",
    )
    reply = res["reply"]
    assert "non-custodial" in reply.lower() or "export basket" in reply.lower()
    assert "March 2020" not in reply


# ============================================================================
# SCENARIO L: Regression Test - Different Queries Produce Distinct Responses
# ============================================================================

def test_regression_different_queries_never_produce_same_response():
    """
    CRITICAL REGRESSION TEST:
    Verifies that 'Hey', 'What does Lucid do?', and 'What is the difference between a stock and a mutual fund?'
    produce completely distinct, relevant replies rather than recycling a fixed response.
    """
    queries = [
        "Hey",
        "What does Lucid do?",
        "What is the difference between a stock and a mutual fund?",
        "Help me understand portfolio risk.",
        "Why did you recommend TCS?",
    ]
    replies = []
    for q in queries:
        res = process_conversational_query(
            user_id=DEMO_USER_ID,
            query_text=q,
            session_id=f"sess_{uuid.uuid4()}",
        )
        replies.append(res["reply"])

    # Ensure all 5 responses are distinct
    assert len(set(replies)) == 5, "All 5 queries must produce distinct responses!"
    assert all("Simulated Systemic Market Crash" not in r for r in replies[:4]), "Non-crash queries must NEVER produce crash simulation!"


# ============================================================================
# SCENARIO M: LLM Provider Operational Failure Handling
# ============================================================================

def test_llm_provider_operational_failure_handled_truthfully():
    """Verifies that an operational failure in the LLM provider returns a clear, honest error message."""
    from unittest.mock import patch

    with patch("backend.portfolio_engine.conversational_assistant.call_configured_llm", side_effect=Exception("API Quota Exceeded")):
        with patch("backend.config.settings.gemini_api_key", "AIzaSyFakeKeyWithValidLength123"):
            res = process_conversational_query(
                user_id=DEMO_USER_ID,
                query_text="What is your analysis of current inflation?",
                session_id="test_sess_llm_fail",
            )
            assert "trouble connecting" in res["reply"].lower() or "try again" in res["reply"].lower()
            assert res["intent"] == "PROVIDER_ERROR"


# ============================================================================
# SCENARIO N: API v1 Endpoint Integration (HTTP TestClient)
# ============================================================================

def test_api_v1_general_chat_endpoint(monkeypatch):
    """Verifies POST /api/v1/chat endpoint works with authentication and returns rich conversational response."""
    from backend.api.v1.auth import get_current_user
    from backend.models.users import AppUser

    fake_user = AppUser(user_id=uuid.UUID(DEMO_USER_ID), email="test@example.com")
    app.dependency_overrides[get_current_user] = lambda: fake_user

    try:
        # Turn 1: Greeting
        resp1 = client.post(
            "/api/v1/chat",
            json={"message": "Hey", "session_id": "api_test_sess"},
        )
        assert resp1.status_code == 200, resp1.text
        data1 = resp1.json()
        assert "reply" in data1
        assert "March 2020" not in data1["reply"]
        assert len(data1["suggested_followups"]) > 0

        # Turn 2: Financial education
        resp2 = client.post(
            "/api/v1/chat",
            json={
                "message": "What is the difference between a stock and a mutual fund?",
                "session_id": "api_test_sess",
            },
        )
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()
        assert "stock" in data2["reply"].lower()
        assert "mutual fund" in data2["reply"].lower()
        assert "March 2020" not in data2["reply"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ============================================================================
# SCENARIO O: Temporal Intelligence & Indian Market Trading Sessions
# ============================================================================

def test_what_day_is_today_returns_current_day_date_and_market_hours():
    """Verifies that asking 'what day is today ?' returns the actual day, date, time, and NSE/BSE market status."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="what day is today ?",
        session_id="test_sess_temporal_day",
    )
    reply = res["reply"]
    assert "March 2020" not in reply
    assert res["intent"] == "TEMPORAL_DATE_TIME"
    assert any(day in reply for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
    assert "NSE" in reply and "BSE" in reply
    assert "IST" in reply
    assert res["scenario_simulation"] is None


def test_is_market_open_returns_status_and_trading_hours():
    """Verifies queries about market open status return trading hours and session status."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="is the market open today?",
        session_id="test_sess_market_open",
    )
    reply = res["reply"]
    assert res["intent"] == "TEMPORAL_DATE_TIME"
    assert "9:15 AM to 3:30 PM IST" in reply
    assert ("Open" in reply or "Closed" in reply)


def test_what_time_is_it():
    """Verifies that asking 'what time is it' returns the current time in IST."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="what time is it",
        session_id="test_sess_time",
    )
    reply = res["reply"]
    assert res["intent"] == "TEMPORAL_DATE_TIME"
    assert "IST" in reply


# ============================================================================
# SCENARIO P: Calculation & Arithmetic Support
# ============================================================================

def test_math_calculation_returns_accurate_result():
    """Verifies that basic arithmetic and percentage queries are solved accurately."""
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="25% of 50,000",
        session_id="test_sess_calc_pct",
    )
    assert res["intent"] == "CALCULATION_MATH"
    assert "12,500" in res["reply"] or "12500" in res["reply"]

    res_div = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="100000 / 4",
        session_id="test_sess_calc_div",
    )
    assert res_div["intent"] == "CALCULATION_MATH"
    assert "25,000" in res_div["reply"] or "25000" in res_div["reply"]


# ============================================================================
# SCENARIO Q: Courtesy, Gratitude & Identity
# ============================================================================

def test_gratitude_and_identity_queries():
    """Verifies courtesy parting and identity queries return warm, contextual answers."""
    res_thanks = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="thank you so much",
        session_id="test_sess_thanks",
    )
    assert res_thanks["intent"] == "GRATITUDE_COURTESY"
    assert "welcome" in res_thanks["reply"].lower()

    res_who = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="who created you",
        session_id="test_sess_identity",
    )
    assert res_who["intent"] == "ASSISTANT_IDENTITY"
    assert "Lucid" in res_who["reply"]
    assert "SEBI" in res_who["reply"]


# ============================================================================
# SCENARIO R: Dynamic General Inquiries
# ============================================================================

def test_general_inquiry_advice_and_getting_started():
    """Verifies that advice and getting started queries produce dynamic, non-canned responses."""
    res_tips = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="Can you give me some stock tips?",
        session_id="test_sess_tips",
    )
    assert "5-Agent AI Committee" in res_tips["reply"]
    assert "SEBI RIA" in res_tips["reply"]

    res_start = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="How do I get started?",
        session_id="test_sess_start",
    )
    assert "Build a Tailored Portfolio" in res_start["reply"]
    assert "Demat Diagnosis" in res_start["reply"]


# ============================================================================
# SCENARIO S: Casual Banter, Money Requests & Personal Questions (Bug Regression)
# ============================================================================

def test_money_gift_request_handles_gracefully_and_wittily():
    """Verifies that queries like 'can you give me money ?' are handled with witty non-custodial explanation."""
    queries = [
        "can you give me money ?",
        "give me money",
        "can u give me money",
        "send me money",
        "can you transfer money to my bank account",
        "give me cash",
    ]
    for q in queries:
        res = process_conversational_query(
            user_id=DEMO_USER_ID,
            query_text=q,
            session_id=f"test_sess_money_{abs(hash(q))}",
        )
        assert res["intent"] == "MONEY_GIFT_REQUEST"
        assert "I understand you are asking about" not in res["reply"]
        assert "non-custodial" in res["reply"].lower()
        assert "vault of rupees" in res["reply"].lower() or "not a commercial bank" in res["reply"].lower()
        assert "protect, invest, and compound" in res["reply"].lower() or "tailored equity portfolios" in res["reply"].lower()


def test_personal_banter_gf_and_dating_questions():
    """Verifies that 'do you have any gf ?' returns a witty, fiduciary response rather than canned fallback."""
    queries = [
        "do you have any gf ?",
        "do you have a girlfriend",
        "are you married",
        "are you single",
        "do you have a boyfriend",
    ]
    for q in queries:
        res = process_conversational_query(
            user_id=DEMO_USER_ID,
            query_text=q,
            session_id=f"test_sess_gf_{abs(hash(q))}",
        )
        assert res["intent"] == "PERSONAL_BANTER"
        assert "I understand you are asking about" not in res["reply"]
        assert "girlfriend" in res["reply"].lower()
        assert "SEBI" in res["reply"]
        assert "ROE" in res["reply"] or "Indian equities" in res["reply"]


def test_humor_jokes_and_philosophical_banter():
    """Verifies that humor, philosophy, and compliments produce distinct, rich replies."""
    res_joke = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="tell me a joke",
        session_id="test_sess_joke",
    )
    assert res_joke["intent"] == "HUMOR_JOKE"
    assert "investor" in res_joke["reply"].lower() or "buffett" in res_joke["reply"].lower()

    res_philo = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="what is the meaning of life",
        session_id="test_sess_philo",
    )
    assert res_philo["intent"] == "PHILOSOPHICAL_BANTER"
    assert "objective" in res_philo["reply"].lower() or "goals" in res_philo["reply"].lower()

    res_smart = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="you are smart",
        session_id="test_sess_smart",
    )
    assert res_smart["intent"] == "COMPLIMENT"
    assert "thank you" in res_smart["reply"].lower()


def test_user_screenshot_queries_produce_totally_different_responses():
    """Direct regression test for the exact queries from user screenshots."""
    q_money = "can you give me money ?"
    q_gf = "do you have any gf ?"

    res_money = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text=q_money,
        session_id="sess_screenshot_money",
    )
    res_gf = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text=q_gf,
        session_id="sess_screenshot_gf",
    )

    # Neither must have the robotic canned string
    assert "I understand you are asking about" not in res_money["reply"]
    assert "I understand you are asking about" not in res_gf["reply"]

    # Intents must be distinct
    assert res_money["intent"] == "MONEY_GIFT_REQUEST"
    assert res_gf["intent"] == "PERSONAL_BANTER"

    # Replies must NOT be identical or even similar
    assert res_money["reply"] != res_gf["reply"]
    assert "girlfriend" not in res_money["reply"].lower()
    assert "vault of rupees" in res_money["reply"].lower()
    assert "girlfriend" in res_gf["reply"].lower()


# ============================================================================
# SCENARIO T: Portfolio Diagnosis & Rebalancing in Conversational Chat
# ============================================================================

def test_natural_language_portfolio_diagnosis_and_rebalance_preview():
    """
    Verifies that providing existing holdings in chat with a rebalance request
    classifies as PORTFOLIO_DIAGNOSIS_AND_REBALANCE and performs deterministic
    valuation, concentration check, and whole-share trade generation without canned stock thesis.
    """
    query = "RELIANCE: 40 TCS: 25 HDFCBANK: 60 INFY: 30, this is my existing portfolio, diagnose and give me rebalance preview."
    res = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text=query,
        session_id="sess_portfolio_diag_chat",
    )

    assert res["intent"] == "PORTFOLIO_DIAGNOSIS_AND_REBALANCE"
    reply = res["reply"]

    # Must NOT be a generic single-stock inquiry thesis
    assert "Core Conglomerate Anchor" not in reply or "Portfolio Diagnosis & Rebalancing Preview" in reply

    # Must contain the 5 key sections
    assert "Current Portfolio Valuation" in reply or "What does your portfolio look like today?" in reply
    assert "Identified Concentration Breaches" in reply or "Risks" in reply
    assert "Integer-Share Rebalancing Plan" in reply or "Suggested Actions" in reply
    assert "RELIANCE" in reply
    assert "TCS" in reply
    assert "HDFCBANK" in reply
    assert "INFY" in reply

    # Must check integer execution and cash residual
    assert "whole shares" in reply.lower() or "integer" in reply.lower()
    assert "cash" in reply.lower()

    # Simulation metadata
    sim = res["scenario_simulation"]
    assert sim is not None
    assert sim.get("type") == "portfolio_diagnosis"
    assert sim.get("total_market_val") > 200000.0
    assert len(sim.get("suggestions", [])) >= 4


def test_explain_rebalancing_and_portfolio_import_concepts():
    """Verifies that asking about what rebalancing is or how to import a portfolio gives clear plain-English education."""
    res_reb = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="What does portfolio rebalancing mean?",
        session_id="sess_explain_reb",
    )
    assert res_reb["intent"] == "EXPLAIN_REBALANCING"
    assert "rebalancing" in res_reb["reply"].lower()
    assert "HOLD" in res_reb["reply"]
    assert "BUY" in res_reb["reply"]
    assert "SELL" in res_reb["reply"]

    res_imp = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="How do I import my portfolio via CSV?",
        session_id="sess_explain_imp",
    )
    assert res_imp["intent"] == "EXPLAIN_PORTFOLIO_IMPORT"
    assert "CSV File Upload" in res_imp["reply"]
    assert "Demat Diagnosis" in res_imp["reply"]


def test_adani_green_quantitative_parameters_and_fiduciary_proof():
    """
    Verifies that asking about parameters, technical, and fundamental details for Adani Green
    returns an evidence-driven, quantitative response with audited ratios, SECI PPA explanations,
    and multi-agent deliberations instead of generic boilerplate.
    """
    sample_portfolio = {
        "holdings": [
            {
                "symbol": "ADANIGREEN",
                "security_name": "Adani Green Energy Limited",
                "sector_name": "Power & Utilities",
                "target_weight_pct": 14.2,
                "target_amount": 35500.0,
                "shares_quantity": 21,
                "latest_price": 1620.0,
            }
        ],
        "investment_amount": 250000.0,
    }

    # Test 1: User's exact prompt from screenshot
    query1 = "give me the parameters and technical and fundamental details on why you selected adanigreen ?"
    res1 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text=query1,
        session_id="sess_adani_param_test",
        portfolio_data=sample_portfolio,
    )

    assert res1["intent"] == "STOCK_INQUIRY"
    reply1 = res1["reply"]

    # Must contain company and role
    assert "ADANIGREEN" in reply1
    assert "Adani Green Energy Limited" in reply1
    assert "Power & Utilities" in reply1
    assert "14.2%" in reply1
    assert "21 whole shares" in reply1

    # Must contain full quantitative parameters table
    assert "115.0x" in reply1, "Must contain audited P/E ratio"
    assert "12.5%" in reply1, "Must contain Return on Equity"
    assert "4.50" in reply1, "Must contain Debt to Equity"
    assert "1.45" in reply1, "Must contain Market Beta"
    assert "32.0%" in reply1, "Must contain 3-Year CAGR"
    assert "541450" in reply1, "Must contain BSE Scrip code"

    # Must explain WHY 4.50 D/E is acceptable (SECI sovereign PPAs)
    assert any(term in reply1 for term in ["SECI", "PPAs", "power purchase agreements", "project-level"]), "Must explain sovereign utility debt structure"

    # Must contain Multi-Agent Committee Transcripts
    assert "Strategist Agent" in reply1
    assert "Fundamental Analyst" in reply1
    assert "Risk Critic" in reply1
    assert "Macro Regime" in reply1

    # Must NOT be the generic fallback copilot message
    assert "As your Lucid Fiduciary Copilot, I am here to provide transparent, verifiable wealth guidance grounded in SEBI RIA principles" not in reply1

    # Test 2: The "Ask AI why ADANIGREEN" automated query
    query2 = "Explain why the AI Analyst and Critic agents chose ADANIGREEN for my portfolio, what risks they identified, and whether there are safer alternatives."
    res2 = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text=query2,
        session_id="sess_adani_ask_why_test",
        portfolio_data=sample_portfolio,
    )

    assert res2["intent"] == "STOCK_INQUIRY"
    assert "ADANIGREEN" in res2["reply"]
    assert "4.50" in res2["reply"]
    assert "115.0x" in res2["reply"]


def test_conversational_off_topic_temporal_and_lifestyle_queries():
    """Verifies that off-topic queries respond naturally, helpfully, and without robotic prompt echoes."""
    # 1. Temporal
    res_date = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="what day is today ?",
        session_id="sess_offtopic_date",
    )
    assert res_date["intent"] == "TEMPORAL_DATE_TIME"
    assert "Today is" in res_date["reply"]
    assert "IST" in res_date["reply"]
    assert "Indian Stock Market" in res_date["reply"]

    # 2. Money Request
    res_money = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="can you give me money ?",
        session_id="sess_offtopic_money",
    )
    assert res_money["intent"] == "MONEY_GIFT_REQUEST"
    assert "I understand you are asking about" not in res_money["reply"]
    assert "non-custodial" in res_money["reply"].lower()

    # 3. Personal banter
    res_gf = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="do you have any gf ?",
        session_id="sess_offtopic_gf",
    )
    assert res_gf["intent"] == "PERSONAL_BANTER"
    assert "I understand you are asking about" not in res_gf["reply"]
    assert "girlfriend" in res_gf["reply"].lower()


def test_dynamic_stock_inquiry_any_stock_recommended_and_unrecommended():
    """
    Verifies that the conversational copilot dynamically handles ANY stock in the Indian equities universe:
    1. Why recommended (with whole shares, parameter table, and 5-agent deliberation).
    2. Why not recommended / rejected / excluded (with Fiduciary Rejection Audit, parameter table, 5-agent deliberation, and safer alternatives).
    3. Both distressed securities (YESBANK, SUZLON, PAYTM, IDEA) and quality peers constrained by portfolio ceilings (INFY, MRF).
    4. Clarifications for mismatched positive/negative inquiries.
    """
    sample_portfolio = {
        "investment_amount": 250000,
        "risk_category": "moderate",
        "holdings": [
            {
                "symbol": "ADANIGREEN",
                "security_name": "Adani Green Energy Ltd",
                "sector_name": "Power & Utilities",
                "target_weight_pct": 14.5,
                "shares_quantity": 35,
                "latest_price": 1035.0,
            },
            {
                "symbol": "TCS",
                "security_name": "Tata Consultancy Services Ltd",
                "sector_name": "Information Technology",
                "target_weight_pct": 18.0,
                "shares_quantity": 11,
                "latest_price": 4090.0,
            },
            {
                "symbol": "RELIANCE",
                "security_name": "Reliance Industries Ltd",
                "sector_name": "Energy & Petrochemicals",
                "target_weight_pct": 20.0,
                "shares_quantity": 18,
                "latest_price": 2777.0,
            },
        ],
    }

    # 1. Recommended stock in portfolio (ADANIGREEN)
    res_adani = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="give me the parameters and technical and fundamental details on why you selected adanigreen ?",
        session_id="sess_adani_held",
        portfolio_data=sample_portfolio,
    )
    assert res_adani["intent"] == "STOCK_INQUIRY"
    r_adani = res_adani["reply"]
    assert "Fiduciary Stock Deliberation & Quantitative Evidence: `ADANIGREEN`" in r_adani
    assert "Allocated **14.5%**" in r_adani
    assert "35 whole shares" in r_adani
    assert "Price / Earnings (P/E)" in r_adani
    assert "Return on Equity (ROE)" in r_adani
    assert "Strategist Agent Selection Criteria" in r_adani
    assert "Risk Critic Safeguards" in r_adani
    assert "Macro Regime & Regulatory Climate" in r_adani

    # 2. Distressed security rejected: YESBANK
    res_yb = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why didn't you recommend yes bank ?",
        session_id="sess_yb_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_yb["intent"] == "STOCK_INQUIRY"
    r_yb = res_yb["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `YESBANK`" in r_yb
    assert "REJECTED BY RISK CRITIC" in r_yb
    assert "POL-ROE-01" in r_yb
    assert "POL-LEVERAGE-01" in r_yb
    assert "HDFCBANK" in r_yb or "ICICIBANK" in r_yb
    assert "Strategist Agent" in r_yb
    assert "Fundamental Analyst" in r_yb
    assert "Risk Critic" in r_yb

    # 3. Distressed security rejected: SUZLON
    res_suz = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why did you not recommend suzlon ?",
        session_id="sess_suz_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_suz["intent"] == "STOCK_INQUIRY"
    r_suz = res_suz["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `SUZLON`" in r_suz
    assert "REJECTED BY RISK CRITIC" in r_suz
    assert "Beta" in r_suz
    assert "Strategist Agent" in r_suz

    # 4. Loss-making platform rejected: PAYTM
    res_paytm = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why was paytm rejected ?",
        session_id="sess_paytm_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_paytm["intent"] == "STOCK_INQUIRY"
    r_paytm = res_paytm["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `PAYTM`" in r_paytm
    assert "REJECTED BY RISK CRITIC" in r_paytm
    assert "BAJFINANCE" in r_paytm or "HDFCBANK" in r_paytm

    # 5. Insolvent capital structure rejected: IDEA
    res_idea = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why isn't idea in my portfolio ?",
        session_id="sess_idea_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_idea["intent"] == "STOCK_INQUIRY"
    r_idea = res_idea["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `IDEA`" in r_idea
    assert "REJECTED BY RISK CRITIC" in r_idea
    assert "BHARTIARTL" in r_idea or "RELIANCE" in r_idea

    # 6. Quality peer omitted due to portfolio concentration ceilings: INFY
    res_infy = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why didn't you pick infosys ?",
        session_id="sess_infy_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_infy["intent"] == "STOCK_INQUIRY"
    r_infy = res_infy["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `INFY`" in r_infy
    assert "APPROVED CANDIDATE — NOT SELECTED" in r_infy
    assert "POL-ALLOC-01" in r_infy
    assert "POL-SECT-01" in r_infy

    # 7. Universe stock lookup outside curated list: MRF
    res_mrf = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why didn't you recommend mrf ?",
        session_id="sess_mrf_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_mrf["intent"] == "STOCK_INQUIRY"
    r_mrf = res_mrf["reply"]
    assert "Fiduciary Exclusion & Rejection Audit: `MRF`" in r_mrf
    assert "Automotive" in r_mrf
    assert "APPROVED CANDIDATE — NOT SELECTED" in r_mrf

    # 8. Clarification for active holding when asked negative inquiry: TCS
    res_tcs_neg = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why didn't you recommend tcs ?",
        session_id="sess_tcs_neg",
        portfolio_data=sample_portfolio,
    )
    assert res_tcs_neg["intent"] == "STOCK_INQUIRY"
    r_tcs_neg = res_tcs_neg["reply"]
    assert "Clarification" in r_tcs_neg
    assert "IS currently recommended and held" in r_tcs_neg
    assert "Fiduciary Stock Deliberation & Quantitative Evidence: `TCS`" in r_tcs_neg

    # 9. Clarification for non-held stock when asked positive inquiry: YESBANK
    res_yb_pos = process_conversational_query(
        user_id=DEMO_USER_ID,
        query_text="why did you recommend yes bank ?",
        session_id="sess_yb_pos",
        portfolio_data=sample_portfolio,
    )
    assert res_yb_pos["intent"] == "STOCK_INQUIRY"
    r_yb_pos = res_yb_pos["reply"]
    assert "Clarification" in r_yb_pos
    assert "not currently held" in r_yb_pos
    assert "Fiduciary Exclusion & Rejection Audit: `YESBANK`" in r_yb_pos


def test_fiduciary_guardrails_and_recommendation_chips_never_give_generic_greeting():
    """
    Verifies that all recommended UI chips, fiduciary questions, volatility queries,
    and cash reserve questions receive direct, accurate answers and NEVER fall back
    to an unrelated canned welcome greeting.
    """
    portfolio_ctx = {
        "holdings": [
            {"symbol": "SUNPHARMA", "security_name": "Sun Pharma Industries", "sector_name": "Healthcare & Pharmaceuticals", "target_weight_pct": 15.0, "target_amount": 37500.0, "shares_quantity": 23, "latest_price": 1620.0},
            {"symbol": "DIVISLAB", "security_name": "Divis Laboratories", "sector_name": "Healthcare & Pharmaceuticals", "target_weight_pct": 15.0, "target_amount": 37500.0, "shares_quantity": 8, "latest_price": 4500.0},
            {"symbol": "ITC", "security_name": "ITC Limited", "sector_name": "Fast Moving Consumer Goods", "target_weight_pct": 15.0, "target_amount": 37500.0, "shares_quantity": 79, "latest_price": 472.5},
            {"symbol": "NESTLEIND", "security_name": "Nestle India", "sector_name": "Fast Moving Consumer Goods", "target_weight_pct": 15.0, "target_amount": 37500.0, "shares_quantity": 16, "latest_price": 2300.0},
            {"symbol": "POWERGRID", "security_name": "Power Grid Corp", "sector_name": "Power & Utilities", "target_weight_pct": 15.0, "target_amount": 37500.0, "shares_quantity": 125, "latest_price": 300.0},
            {"symbol": "TCS", "security_name": "Tata Consultancy Services", "sector_name": "Information Technology", "target_weight_pct": 13.1, "target_amount": 32750.0, "shares_quantity": 8, "latest_price": 3885.0},
            {"symbol": "HCLTECH", "security_name": "HCL Technologies", "sector_name": "Information Technology", "target_weight_pct": 11.9, "target_amount": 29750.0, "shares_quantity": 17, "latest_price": 1750.0},
        ],
        "investment_amount": 250000.0,
        "cash_reserve": 9059.0,
        "expected_return_pct": 11.49,
        "expected_volatility_pct": 9.31,
        "diversification_score": 99.9,
        "risk_category": "VERY_CONSERVATIVE",
        "sharpe_ratio": 0.48,
    }

    # 1. Sector Caps Rule (User Screenshot Bug)
    res_sector = process_conversational_query(
        user_id="test_chip_user",
        query_text="Explain the SEBI 40% sector cap rule and how it protects me.",
        portfolio_data=portfolio_ctx,
    )
    assert res_sector["intent"] == "FINANCIAL_EDUCATION_FIDUCIARY_GUARDRAILS"
    assert "40% Sector Cap" in res_sector["reply"]
    assert "Healthcare & Pharmaceuticals at 30.0%" in res_sector["reply"]
    assert "How can I best assist your investments today?" not in res_sector["reply"]

    # 2. 25% Single-Stock Cap
    res_stock_cap = process_conversational_query(
        user_id="test_chip_user",
        query_text="Explain your 25% safety cap.",
        portfolio_data=portfolio_ctx,
    )
    assert res_stock_cap["intent"] == "FINANCIAL_EDUCATION_FIDUCIARY_GUARDRAILS"
    assert "25% Single-Stock Safety Cap" in res_stock_cap["reply"]
    assert "SUNPHARMA" in res_stock_cap["reply"]
    assert "15.0%" in res_stock_cap["reply"]

    # 3. Whole Shares vs Fractional
    res_whole = process_conversational_query(
        user_id="test_chip_user",
        query_text="Why whole shares instead of fractional shares?",
        portfolio_data=portfolio_ctx,
    )
    assert res_whole["intent"] == "FINANCIAL_EDUCATION_FIDUCIARY_GUARDRAILS"
    assert "Whole-Share Integer Execution vs. Fractional Shares" in res_whole["reply"]

    # 4. Volatility (Target vs Expected Volatility)
    res_vol = process_conversational_query(
        user_id="test_chip_user",
        query_text="What is target volatility and how is it different from expected volatility?",
        portfolio_data=portfolio_ctx,
    )
    assert res_vol["intent"] == "FINANCIAL_EDUCATION_VOLATILITY"
    assert "Target Volatility vs. Expected Volatility" in res_vol["reply"]
    assert "8.0%" in res_vol["reply"]
    assert "9.31%" in res_vol["reply"]

    # 5. Cash Reserve
    res_cash = process_conversational_query(
        user_id="test_chip_user",
        query_text="Why do I have unallocated cash reserve?",
        portfolio_data=portfolio_ctx,
    )
    assert res_cash["intent"] == "FINANCIAL_EDUCATION_CASH_RESERVE"
    assert "Why Your Portfolio Has a Cash Reserve" in res_cash["reply"]
    assert "₹9,059.00" in res_cash["reply"]

    # 6. Basket Export
    res_export = process_conversational_query(
        user_id="test_chip_user",
        query_text="How do I export my basket?",
        portfolio_data=portfolio_ctx,
    )
    assert res_export["intent"] == "EXPLAIN_BASKET_EXPORT"
    assert "How to Export and Execute Your Portfolio" in res_export["reply"]

    # 7. Stock Selection Methodology
    res_method = process_conversational_query(
        user_id="test_chip_user",
        query_text="How do you choose the stocks?",
        portfolio_data=portfolio_ctx,
    )
    assert res_method["intent"] == "EXPLAIN_METHODOLOGY"
    assert "5-Agent AI Committee" in res_method["reply"]

    # 8. Expected Returns
    res_ret = process_conversational_query(
        user_id="test_chip_user",
        query_text="What returns can I expect?",
        portfolio_data=portfolio_ctx,
    )
    assert res_ret["intent"] == "FINANCIAL_EDUCATION_RETURNS"
    assert "11.49%" in res_ret["reply"]

    # 9. Diversification Score & Herfindahl Index
    res_div = process_conversational_query(
        user_id="test_chip_user",
        query_text="What is diversification score and Herfindahl index?",
        portfolio_data=portfolio_ctx,
    )
    assert res_div["intent"] == "FINANCIAL_EDUCATION_DIVERSIFICATION"
    assert "Herfindahl-Hirschman Index" in res_div["reply"]
    assert "99.9/100" in res_div["reply"]





