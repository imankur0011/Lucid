"""
Tests for LLM Resilience, Graceful Fallback, and Deterministic Gate Enforcement.
Verifies that:
1. No-key fallback produces dynamic heuristic synthesis with explicit trace tags.
2. Timeout exceptions trigger graceful fallback with 'timeout_exceeded' in trace.
3. Quota (429) errors trigger graceful fallback with 'quota_exceeded' in trace.
4. Malformed/empty LLM outputs trigger fallback with 'malformed_or_empty_response' in trace.
5. In all cases, deterministic optimization and hard mathematical validation gates cannot be bypassed.
"""

import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal

from backend.agent.nodes import analyst_node, deterministic_optimizer_node
from backend.agent.state import PortfolioAgentState


def _make_dummy_state():
    return {
        "investment_amount": 100000.0,
        "risk_category": "moderate",
        "investment_horizon_months": 36,
        "user_prompt": "I want exposure to high growth technology and dividend leaders",
        "eligible_candidates": [
            {"security_id": "sec-1", "symbol": "INFY", "company_name": "Infosys", "sector_name": "Technology", "latest_price": 1500.0},
            {"security_id": "sec-2", "symbol": "TCS", "company_name": "Tata Consultancy", "sector_name": "Technology", "latest_price": 3800.0},
            {"security_id": "sec-3", "symbol": "HDFCBANK", "company_name": "HDFC Bank", "sector_name": "Financial Services", "latest_price": 1650.0},
            {"security_id": "sec-4", "symbol": "ICICIBANK", "company_name": "ICICI Bank", "sector_name": "Financial Services", "latest_price": 1100.0},
            {"security_id": "sec-5", "symbol": "ITC", "company_name": "ITC Ltd", "sector_name": "Consumer Defensive", "latest_price": 440.0},
        ],
        "execution_trace": [],
        "preferences": {},
    }


def test_no_key_fallback():
    """Verify trace and behavior when no Gemini API key is configured."""
    state = _make_dummy_state()
    with patch("backend.agent.nodes.get_llm", return_value=None):
        out = analyst_node(state)
        trace = out["execution_trace"]
        analyst_entry = next(t for t in trace if t["step"] == "analyst")

        assert analyst_entry["ai_provider"] == "dynamic_heuristic_fallback"
        assert analyst_entry["fallback_reason"] == "no_api_key_configured"
        assert "Technology" in out["analyst_research_notes"]["strategy_theme"]
        assert "Dividend" in out["analyst_research_notes"]["strategy_theme"]


def test_llm_timeout_fallback():
    """Verify graceful recovery when LLM call times out."""
    state = _make_dummy_state()
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = TimeoutError("Request timed out after 15 seconds")

    with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
        out = analyst_node(state)
        trace = out["execution_trace"]
        analyst_entry = next(t for t in trace if t["step"] == "analyst")

        assert analyst_entry["ai_provider"] == "dynamic_heuristic_fallback"
        assert analyst_entry["fallback_reason"] == "timeout_exceeded"
        # Strategy theme is still successfully synthesized
        assert out["analyst_research_notes"]["strategy_theme"] is not None


def test_llm_quota_error_fallback():
    """Verify graceful recovery when LLM quota is exhausted (HTTP 429)."""
    state = _make_dummy_state()
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("429 ResourceExhausted: Quota exceeded for model gemini-2.5-flash")

    with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
        out = analyst_node(state)
        trace = out["execution_trace"]
        analyst_entry = next(t for t in trace if t["step"] == "analyst")

        assert analyst_entry["ai_provider"] == "dynamic_heuristic_fallback"
        assert analyst_entry["fallback_reason"] == "quota_exceeded"


def test_llm_malformed_empty_output_fallback():
    """Verify graceful recovery when LLM returns an empty or whitespace response."""
    state = _make_dummy_state()
    mock_llm = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "   "  # whitespace only
    mock_llm.invoke.return_value = mock_resp

    with patch("backend.agent.nodes.get_llm", return_value=mock_llm):
        out = analyst_node(state)
        trace = out["execution_trace"]
        analyst_entry = next(t for t in trace if t["step"] == "analyst")

        assert analyst_entry["ai_provider"] == "dynamic_heuristic_fallback"
        assert analyst_entry["fallback_reason"] == "malformed_or_empty_response"


def test_deterministic_validation_gate_cannot_be_bypassed():
    """Verify that regardless of LLM output, deterministic optimizer and validator enforce hard constraints."""
    state = _make_dummy_state()
    # Execute deterministic optimizer node
    out = deterministic_optimizer_node(state)

    assert out["validation_passed"] is True
    val_out = out["validation_output"]
    assert val_out["all_passed"] is True
    # Ensure all allocations strictly adhere to max 25% single-stock cap
    for alloc in out["allocations"]:
        assert alloc["target_weight_pct"] <= 25.01
        # Realized whole-share percentage must also respect bound
        realized_pct = (alloc["shares_quantity"] * alloc["latest_price"] / 100000.0) * 100.0
        assert realized_pct <= 25.01
