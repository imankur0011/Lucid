"""
Acceptance Test Suite for Natural-Language Investor Onboarding and Intelligent Information Extraction (Tests A through J).

Fulfills all requirements from Section 11:
- Test A: Complete Information
- Test B: Incomplete Information
- Test C: Monthly Contribution vs Lump-Sum
- Test D: Multiple Financial Goals
- Test E: Ambiguous / Contradictory Risk Preference
- Test F: Sector Preference vs Sector Exclusion
- Test G: Mixed Manual and Natural-Language Inputs
- Test H: Conversational Hypothetical Scenario Identification
- Test I: Model Output Resilience & Fallback Integrity
- Test J: End-to-End Portfolio Generation from Natural Language Profile
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import SessionLocal
from backend.schemas.nlp_profile import (
    ExtractionStatus,
    ValidationStatus,
    ContributionType,
    RiskCategoryEnum,
    HorizonCategory,
    StructuredInvestorProfile,
)
from backend.portfolio_engine.nlp_profile_extractor import (
    extract_investor_profile_nlp,
    parse_indian_currency_amount,
    parse_investment_horizon,
    parse_contribution_type,
    extract_multiple_goals,
    detect_contradictions,
    extract_sectors_and_restrictions,
    extract_sectors_from_text,
    merge_profile_with_extracted_data,
    is_hypothetical_query,
    deterministic_extract_investor_profile,
)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_a_complete_information(db):
    """
    Test A: Complete Information
    User provides all required details in natural language.
    Asserts complete profile creation, proper normalization, and question option mapping.
    """
    narrative = (
        "I have ₹2 lakh available for investment. I want to invest for approximately five years "
        "to build long-term wealth. I am comfortable with moderate risk, but I don't want my portfolio "
        "to be too concentrated in technology stocks. I have some experience investing in stocks, "
        "and I prefer fundamentally strong companies with reasonable valuations."
    )
    profile = extract_investor_profile_nlp(narrative, db=db)

    # 1. Capital verification
    assert profile.capital.initial_lump_sum == 200_000.0
    assert profile.capital.contribution_type == ContributionType.LUMP_SUM
    assert profile.field_evidence["investment_amount"].extraction_status in [
        ExtractionStatus.EXPLICIT,
        ExtractionStatus.NORMALIZED_FROM_TEXT,
    ]

    # 2. Horizon verification
    assert profile.horizon_months == 60
    assert profile.horizon_years == 5.0
    assert profile.field_evidence["investment_horizon"].extraction_status in [
        ExtractionStatus.EXPLICIT,
        ExtractionStatus.NORMALIZED_FROM_TEXT,
    ]

    # 3. Risk verification
    assert profile.risk.assessed_risk_category == RiskCategoryEnum.MODERATE
    assert profile.risk.target_volatility_pct == 12.5

    # 4. Sector constraint verification (Soft concentration restriction recognized)
    assert profile.preferences.soft_preferences_notes is not None
    assert "Information Technology" in profile.preferences.soft_preferences_notes

    # 5. Experience verification
    assert profile.experience.experience_level in ["intermediate", "experienced"]

    # 6. Database Question Option mapping
    assert len(profile.mapped_questionnaire_answers) >= 1
    target_q_types = [a.question_text for a in profile.mapped_questionnaire_answers]
    assert any("horizon" in q.lower() or "time" in q.lower() for q in target_q_types)


def test_b_incomplete_information():
    """
    Test B: Incomplete Information
    User provides only an investment amount ("I want to invest ₹50,000.").
    System must extract the amount, flag missing fields, and not fabricate arbitrary values.
    """
    narrative = "I want to invest ₹50,000."
    profile = deterministic_extract_investor_profile(narrative)

    # Capital is extracted
    assert profile.capital.initial_lump_sum == 50_000.0

    # Horizon is missing and flagged for confirmation
    horizon_meta = profile.field_evidence["investment_horizon"]
    assert horizon_meta.extraction_status == ExtractionStatus.NOT_PROVIDED
    assert horizon_meta.validation_status == ValidationStatus.REQUIRES_CONFIRMATION
    assert horizon_meta.clarification_prompt is not None

    # Experience is missing
    exp_meta = profile.field_evidence["investment_experience"]
    assert exp_meta.extraction_status == ExtractionStatus.NOT_PROVIDED
    assert exp_meta.validation_status == ValidationStatus.REQUIRES_CONFIRMATION
    assert exp_meta.clarification_prompt is not None

    # Missing fields list contains the unprovided fields
    missing_names = [f.field_name for f in profile.missing_fields]
    assert "investment_horizon" in missing_names
    assert "investment_experience" in missing_names


def test_c_monthly_contribution():
    """
    Test C: Monthly Contribution (SIP)
    User specifies a recurring monthly contribution ("I can invest around ₹10,000 every month for 10 years.").
    System must identify monthly SIP, calculate annual commitment, and not treat it as a one-time lump sum.
    """
    narrative = "I can invest around ₹10,000 every month for the next 10 years."
    profile = deterministic_extract_investor_profile(narrative)

    assert profile.capital.contribution_type == ContributionType.MONTHLY_SIP
    assert profile.capital.monthly_contribution == 10_000.0
    assert profile.capital.initial_lump_sum is None

    # Horizon is 10 years = 120 months
    assert profile.horizon_months == 120
    assert profile.horizon_years == 10.0

    # Check evidence data type and prompt
    cap_meta = profile.field_evidence["investment_amount"]
    assert cap_meta.extraction_status in [ExtractionStatus.EXPLICIT, ExtractionStatus.NORMALIZED_FROM_TEXT]
    assert cap_meta.value == 10_000.0


def test_d_multiple_goals():
    """
    Test D: Multiple Financial Goals
    User mentions both short-term and long-term goals.
    System must extract multiple distinct goals without collapsing them into one.
    """
    narrative = (
        "I want to buy a car in 2 years for which I need ₹5 lakh, "
        "and also save for retirement in 20 years."
    )
    goals = extract_multiple_goals(narrative)

    assert len(goals) >= 2

    # Verify Car purchase goal
    car_goals = [g for g in goals if "car" in g.goal_name.lower() or "vehicle" in g.goal_name.lower()]
    assert len(car_goals) == 1
    assert car_goals[0].target_amount == 500_000.0
    assert car_goals[0].target_horizon_months == 24
    assert car_goals[0].time_horizon_category == HorizonCategory.SHORT_TERM

    # Verify Retirement goal
    ret_goals = [g for g in goals if "retirement" in g.goal_name.lower()]
    assert len(ret_goals) == 1
    assert ret_goals[0].horizon_months == 240
    assert ret_goals[0].time_horizon_category == HorizonCategory.LONG_TERM


def test_e_ambiguous_risk_preference():
    """
    Test E: Ambiguous / Contradictory Risk Preference
    User states contradictory goals: "I want high returns with zero risk of losing money."
    System must detect the conflict, flag CONFLICT_HIGH_RETURNS_ZERO_RISK, and request clarification.
    """
    narrative = "I want high returns with zero risk of losing money."
    contradictions = detect_contradictions(narrative)

    assert len(contradictions) >= 1
    conflict_codes = [c.code for c in contradictions]
    assert "CONFLICT_HIGH_RETURNS_ZERO_RISK" in conflict_codes

    # Profile extraction must reflect this conflict
    profile = deterministic_extract_investor_profile(narrative)
    assert profile.risk.is_conflict_detected is True
    assert profile.risk.conflict_description is not None
    assert len(profile.contradictions) >= 1


def test_f_sector_preference_vs_exclusion():
    """
    Test F: Sector Preference vs Sector Exclusion
    User specifies both positive affinities and strict negative exclusions.
    System must cleanly distinguish preferred sectors from excluded sectors.
    """
    narrative = (
        "I like technology and healthcare companies, "
        "but I definitely do not want any tobacco or defense stocks."
    )
    pref, excl = extract_sectors_from_text(narrative)

    # Preferences
    assert any("tech" in s.lower() or "it" in s.lower() for s in pref)
    assert any("health" in s.lower() or "pharma" in s.lower() for s in pref)

    # Exclusions
    assert any("tobacco" in s.lower() for s in excl)
    assert any("defense" in s.lower() for s in excl)

    # Ensure no overlap
    assert set(pref).isdisjoint(set(excl))


def test_g_mixed_manual_and_natural_language():
    """
    Test G: Mixed Manual and Natural-Language Inputs
    User extracts baseline via natural language, then manually modifies parameters in questionnaire.
    System must merge both without overwriting unedited extracted fields.
    """
    # 1. User starts with natural language
    nl_text = "I want to invest ₹3,00,000 for 5 years with moderate risk."
    extracted = deterministic_extract_investor_profile(nl_text)
    assert extracted.capital.initial_lump_sum == 300_000.0
    assert extracted.horizon_months == 60
    assert extracted.risk.assessed_risk_category == RiskCategoryEnum.MODERATE

    # 2. User manually overrides amount to ₹3,50,000 and risk to Aggressive in the questionnaire
    manual_edits = {
        "investment_amount": 350_000.0,
        "risk_category": "aggressive",
    }
    merged = merge_profile_with_extracted_data(manual_edits, extracted, manual_overrides=True)

    # Overridden fields reflect manual user edits
    assert merged.capital.initial_lump_sum == 350_000.0
    assert merged.risk.assessed_risk_category == RiskCategoryEnum.AGGRESSIVE
    assert merged.risk.target_volatility_pct == 18.0

    # Unedited fields remain intact from natural language extraction
    assert merged.horizon_months == 60
    assert merged.horizon_years == 5.0


def test_h_hypothetical_scenario():
    """
    Test H: Conversational Hypothetical Scenario Identification
    System must distinguish what-if exploration from genuine profile updates.
    """
    # What-if queries must be identified as hypothetical
    assert is_hypothetical_query("What if I invested ₹5 lakh instead of ₹2 lakh?") is True
    assert is_hypothetical_query("Suppose I retire in 10 years?") is True
    assert is_hypothetical_query("Hypothetically, what happens if I take more risk?") is True
    assert is_hypothetical_query("If I had 10 lakhs, how would my returns change?") is True

    # Genuine onboarding / profile updates must NOT be classified as hypothetical
    assert is_hypothetical_query("I want to invest ₹5 lakh for 10 years") is False
    assert is_hypothetical_query("Please update my budget to ₹3,50,000") is False
    assert is_hypothetical_query("My risk preference is conservative") is False


def test_i_invalid_model_output_resilience(db):
    """
    Test I: Model Output Resilience & Fallback Integrity
    When the LLM generates invalid JSON, markdown gibberish, or encounters an API error,
    the deterministic fallback must guarantee graceful degradation with full extraction.
    """
    text = (
        "I am looking to invest ₹4,00,000 for 3 years. Moderate risk, "
        "full 6-month emergency reserve, prefer banking and automobile."
    )

    # Simulate Gemini API failure / malformed response
    with patch("google.genai.Client") as mock_client:
        mock_instance = mock_client.return_value
        mock_instance.models.generate_content.side_effect = RuntimeError("API Quota Exceeded / Malformed Response")

        # The function should NOT throw an unhandled exception
        profile = extract_investor_profile_nlp(text, db=db)

        # Verified fallback extraction
        assert profile is not None
        assert profile.capital.initial_lump_sum == 400_000.0
        assert profile.horizon_months == 36
        assert profile.risk.assessed_risk_category == RiskCategoryEnum.MODERATE
        assert profile.risk.emergency_fund_status == "full"
        assert any("auto" in s.lower() for s in profile.preferences.preferred_sectors)
        assert any("financial" in s.lower() or "bank" in s.lower() for s in profile.preferences.preferred_sectors)


def test_j_end_to_end_portfolio_generation(client):
    """
    Test J: End-to-End Portfolio Generation from Natural Language Profile
    Verifies that the extracted profile parameters pass through the exact same
    portfolio generation engine as the structured questionnaire and produce a
    valid, SEBI-compliant portfolio.
    """
    # 1. Natural language input
    text = (
        "I have ₹2,50,000 to invest for 5 years. I prefer conservative risk, "
        "have a full emergency reserve, and prefer consumer and pharma stocks, but exclude tobacco."
    )
    profile = deterministic_extract_investor_profile(text)

    # 2. Construct Portfolio Generation payload using extracted profile data
    payload = {
        "portfolio_name": "NLP Onboarding Generated Portfolio",
        "investment_amount": profile.capital.initial_lump_sum,
        "currency_code": "INR",
        "investment_horizon_months": profile.horizon_months,
        "preferences": {
            "excluded_sectors": profile.preferences.excluded_sectors,
            "excluded_instruments": profile.preferences.excluded_instruments,
            "max_single_stock_weight_pct": 25.0,
            "max_sector_weight_pct": 40.0,
            "target_stock_count": 6,
        },
        "user_prompt": text,
    }

    # 3. Trigger LangGraph generation workflow
    res = client.post("/api/v1/portfolio-generation-requests", json=payload)
    assert res.status_code == 201, res.text
    data = res.json()

    # 4. Verify portfolio output & SEBI compliance
    assert data["version_status"] == "generated"
    assert data["validation_status"] in ["passed", "passed_with_warnings"]
    assert float(data["investment_amount"]) == 250_000.0

    holdings = data["holdings"]
    assert len(holdings) >= 3

    # Check SEBI single-stock guardrail (<= 25%)
    for h in holdings:
        assert h["target_weight_pct"] <= 25.01, f"Stock {h['ticker']} exceeds 25% cap"

    # Check that tobacco was excluded
    for h in holdings:
        assert "tobacco" not in h.get("sector", "").lower()
