"""
Tests for Natural Language Investor Profile & Preference Extraction.
Verifies that:
1. Freeform natural language extracts capital, horizon, risk, goals, and sectors accurately.
2. Indian currency denominations (Lakhs, Crores, K, numbers) are parsed correctly.
3. Distinguishes investor age (e.g. 28 years old) from investment horizon (5 years).
4. Enforces SEBI RIA fiduciary rules (zero emergency fund capping risk capacity).
5. Resolves active RiskQuestion and RiskQuestionOption UUIDs for regulatory audit trail.
6. Handles offline / fallback mode deterministically with high accuracy.
7. Validates the API endpoint POST /api/v1/profile/extract-from-text.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal
from backend.portfolio_engine.nlp_profile_extractor import (
    extract_investor_profile_nlp,
    parse_indian_currency_amount,
    parse_investment_horizon,
    extract_sectors_from_text,
)


@pytest.fixture
def client():
    return TestClient(app)


def test_parse_indian_currency_amounts():
    assert parse_indian_currency_amount("I have 2.5 lakh to invest") == 250_000.0
    assert parse_indian_currency_amount("Allocating 5 lakhs for growth") == 500_000.0
    assert parse_indian_currency_amount("Starting with ₹3,50,000") == 350_000.0
    assert parse_indian_currency_amount("Investing 1 crore") == 10_000_000.0
    assert parse_indian_currency_amount("Budget of 75k") == 75_000.0
    assert parse_indian_currency_amount("₹100000") == 100_000.0


def test_parse_investment_horizon_ignores_age():
    # Age vs Horizon
    h1 = parse_investment_horizon("I am 29 years old and want to invest for 5 years")
    assert h1 == 60

    h2 = parse_investment_horizon("62 years old retiree looking to invest over 3 yrs")
    assert h2 == 36

    h3 = parse_investment_horizon("Investing for 18 months")
    assert h3 == 18

    h4 = parse_investment_horizon("Looking at very long term compounding")
    assert h4 == 120


def test_extract_sectors_and_exclusions():
    pref, excl = extract_sectors_from_text(
        "I like Information Technology, Banking and Clean Energy stocks, but strictly avoid tobacco and defense"
    )
    assert "Information Technology" in pref
    assert "Financial Services" in pref
    assert "Energy & Power" in pref
    assert "Tobacco" in excl
    assert "Defense & Aerospace" in excl
    assert "Tobacco" not in pref


def test_extract_investor_profile_full():
    db = SessionLocal()
    try:
        text = (
            "I am 31 years old software developer with 4.5 lakhs INR to invest for 5 years. "
            "I have an aggressive risk profile, 8 months emergency reserve in bank FD, "
            "and intermediate experience with mutual fund SIPs. "
            "I prefer tech, healthcare, and auto stocks, but please exclude tobacco."
        )
        res = extract_investor_profile_nlp(text, db=db)

        p = res["extracted_profile"]
        assert p["investment_amount"] == 450_000.0
        assert p["horizon_months"] == 60
        assert p["risk_category"] == "aggressive"
        assert p["emergency_fund_status"] == "full"
        assert p["experience_level"] == "intermediate"
        assert "Information Technology" in p["preferred_sectors"]
        assert "Healthcare & Pharmaceuticals" in p["preferred_sectors"]
        assert "Tobacco" in p["excluded_sectors"]

        # Ensure question options are resolved
        answers = res.get("resolved_questionnaire_answers", [])
        assert len(answers) == 5
        q_codes = {a["question_code"] for a in answers}
        assert "INVESTMENT_HORIZON" in q_codes
        assert "EMERGENCY_FUND_BUFFER" in q_codes
    finally:
        db.close()


def test_sebi_zero_emergency_fund_capping():
    db = SessionLocal()
    try:
        text = (
            "I have 2 lakhs to invest for 5 years. I want high risk and aggressive growth, "
            "but I do not have any emergency fund saved yet."
        )
        res = extract_investor_profile_nlp(text, db=db)

        p = res["extracted_profile"]
        # Fiduciary rule: Cannot be aggressive or growth with zero emergency fund
        assert p["risk_category"] == "conservative"
        assert p["emergency_fund_status"] == "none"

        # Check audit note
        fiduciary_notes = " ".join(res["fiduciary_notes"])
        assert "Zero emergency reserve" in fiduciary_notes
    finally:
        db.close()


def test_nlp_profile_api_endpoint(client):
    payload = {
        "text": "I am looking to invest ₹3,00,000 for 4 years with moderate risk, full 6-month emergency reserve, prefer IT and banking."
    }
    response = client.post("/api/v1/profile/extract-from-text", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "extracted_profile" in data
    assert data["extracted_profile"]["investment_amount"] == 300_000.0
    assert data["extracted_profile"]["risk_category"] == "moderate"
    assert data["extracted_profile"]["emergency_fund_status"] == "full"
    assert len(data.get("resolved_questionnaire_answers", [])) == 5


def test_ankur_profile_extraction_sectors_and_experience():
    db = SessionLocal()
    try:
        text = (
            "Hey I am Ankur, i am a 26 year old with 50,000 to invest for 2 years. "
            "I have a moderate risk appetite and a full 1-month emergency fund in bank FDs. "
            "I have no experience in mutual funds and want strong exposure to Information Technology and Banking, "
            "but please avoid Tobacco, and Betting."
        )
        res = extract_investor_profile_nlp(text, db=db)
        p = res["extracted_profile"]

        assert p["investment_amount"] == 50_000.0
        assert p["horizon_months"] == 24
        assert p["risk_category"] == "moderate"
        assert p["emergency_fund_status"] == "partial"
        assert p["experience_level"] == "beginner"
        assert p["knowledge_level"] == "basic"

        # Preferred must contain IT and Banking (Financial Services)
        assert "Information Technology" in p["preferred_sectors"]
        assert "Financial Services" in p["preferred_sectors"]

        # Excluded must contain Tobacco and Betting & Gambling, and NOT have IT or Financial Services!
        assert "Tobacco" in p["excluded_sectors"]
        assert "Betting & Gambling" in p["excluded_sectors"]
        assert "Information Technology" not in p["excluded_sectors"]
        assert "Financial Services" not in p["excluded_sectors"]

        # Goal should be wealth creation, NOT emergency reserve
        assert p["goal_type"] == "wealth_creation"
        assert "Wealth Creation" in p["goal_name"]
    finally:
        db.close()


