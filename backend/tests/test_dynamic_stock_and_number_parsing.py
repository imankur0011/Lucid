"""
Dynamic Stock Discovery and Intelligent Financial Number Parsing Test Suite.
Tests database-backed NSE/BSE security resolution, fuzzy matching, ambiguity detection,
comprehensive word/scale number parsing, quantitative sector constraints, and end-to-end NLP integration.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.financial_number_parser import (
    financial_number_parser,
    words_to_number,
    ComparisonOperator,
    SemanticType,
    SemanticUnit,
)
from backend.services.company_resolution_service import (
    company_resolution_service,
    MatchType,
)
from backend.portfolio_engine.nlp_profile_extractor import (
    deterministic_extract_investor_profile,
    extract_existing_holdings,
    extract_preferred_securities,
    extract_sector_constraints,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# 1. Financial Number Parsing & Word Grammar Tests
# ---------------------------------------------------------------------------

def test_word_to_number_grammar():
    """Validates word-to-number mathematical parsing for Indian and Western expressions."""
    assert words_to_number("one") == 1.0
    assert words_to_number("five") == 5.0
    assert words_to_number("ten") == 10.0
    assert words_to_number("fifteen") == 15.0
    assert words_to_number("twenty") == 20.0
    assert words_to_number("twenty-five") == 25.0
    assert words_to_number("forty-two") == 42.0
    assert words_to_number("one hundred") == 100.0
    assert words_to_number("three hundred and fifty") == 350.0

    # Indian and Western scale words
    assert words_to_number("one lakh") == 100_000.0
    assert words_to_number("two lakh fifty thousand") == 250_000.0
    assert words_to_number("one crore") == 10_000_000.0
    assert words_to_number("two crore fifty lakh") == 25_000_000.0
    assert words_to_number("one point five lakh") == 150_000.0
    assert words_to_number("two point five crores") == 25_000_000.0
    assert words_to_number("half") == 0.5
    assert words_to_number("quarter") == 0.25


def test_financial_number_parser_shorthand_and_currencies():
    """Validates financial shorthand (L, Cr, K, M) and Indian currency notation."""
    p1 = financial_number_parser.parse_expression("2.5 lakh")
    assert p1 is not None and p1.normalized_value == 250_000.0
    assert p1.magnitude == "Lakh"

    p2 = financial_number_parser.parse_expression("2.5L")
    assert p2 is not None and p2.normalized_value == 250_000.0

    p3 = financial_number_parser.parse_expression("1.5 crore")
    assert p3 is not None and p3.normalized_value == 15_000_000.0
    assert p3.magnitude == "Crore"

    p4 = financial_number_parser.parse_expression("1.5Cr")
    assert p4 is not None and p4.normalized_value == 15_000_000.0

    p5 = financial_number_parser.parse_expression("75k")
    assert p5 is not None and p5.normalized_value == 75_000.0

    p6 = financial_number_parser.parse_expression("1M")
    assert p6 is not None and p6.normalized_value == 1_000_000.0

    p7 = financial_number_parser.parse_expression("₹25,000")
    assert p7 is not None and p7.normalized_value == 25_000.0
    assert p7.currency == "INR"

    p8 = financial_number_parser.parse_expression("₹1,50,00,000")
    assert p8 is not None and p8.normalized_value == 15_000_000.0


def test_financial_number_parser_operators_and_ranges():
    """Validates comparative operators (LTE, GTE, BETWEEN, DELTA_NEGATIVE)."""
    # LTE: "not more than 20%"
    p_lte = financial_number_parser.parse_expression("not more than 20%")
    assert p_lte is not None
    assert p_lte.normalized_value == 20.0
    assert p_lte.comparison_operator == ComparisonOperator.LTE
    assert p_lte.unit == SemanticUnit.PERCENT

    # LTE: "do not allocate more than 20% to the banking sector"
    p_lte2 = financial_number_parser.parse_expression("do not allocate more than 20% to the banking sector")
    assert p_lte2 is not None
    assert p_lte2.normalized_value == 20.0
    assert p_lte2.comparison_operator == ComparisonOperator.LTE

    # GTE: "at least 50000"
    p_gte = financial_number_parser.parse_expression("at least 50000")
    assert p_gte is not None
    assert p_gte.normalized_value == 50_000.0
    assert p_gte.comparison_operator == ComparisonOperator.GTE

    # Range: "between 1 lakh and 2 lakh"
    p_rng = financial_number_parser.parse_expression("between 1 lakh and 2 lakh")
    assert p_rng is not None
    assert p_rng.comparison_operator == ComparisonOperator.BETWEEN
    assert p_rng.min_value == 100_000.0
    assert p_rng.max_value == 200_000.0

    # Negative delta: "reduce by 5%"
    p_del = financial_number_parser.parse_expression("reduce by 5%")
    assert p_del is not None
    assert p_del.normalized_value == -5.0
    assert p_del.comparison_operator == ComparisonOperator.DELTA_NEGATIVE


# ---------------------------------------------------------------------------
# 2. Dynamic Company & Security Resolution Tests
# ---------------------------------------------------------------------------

def test_company_resolution_exact_and_isin():
    """Tests exact symbol, ISIN, and legal name resolution from PostgreSQL security master."""
    # Exact NSE Symbol
    r1 = company_resolution_service.resolve_company("BEL")
    assert r1.matched_symbol == "BEL"
    assert "Bharat Electronics" in (r1.company_name or "")
    assert r1.match_type == MatchType.EXACT_SYMBOL

    # Exact ISIN
    r2 = company_resolution_service.resolve_company("INE263A01024")
    assert r2.matched_symbol == "BEL"
    assert r2.match_type == MatchType.EXACT_ISIN

    # Normalized Name
    r3 = company_resolution_service.resolve_company("Bharat Electronics Limited")
    assert r3.matched_symbol == "BEL"
    assert r3.match_type in [MatchType.NORMALIZED_NAME, MatchType.ALIAS]


def test_company_resolution_aliases_and_fuzzy():
    """Tests well-known fintech aliases (L&T, SBI, Infy) and fuzzy typo resolution."""
    # Common Aliases
    r_lt = company_resolution_service.resolve_company("L&T")
    assert r_lt.matched_symbol == "LT"
    assert r_lt.match_type == MatchType.ALIAS

    r_sbi = company_resolution_service.resolve_company("SBI")
    assert r_sbi.matched_symbol == "SBIN"

    r_infy = company_resolution_service.resolve_company("Infy")
    assert r_infy.matched_symbol == "INFY"

    # Typo / Fuzzy match: "Relience" -> RELIANCE
    r_typo = company_resolution_service.resolve_company("Relience")
    assert r_typo.matched_symbol == "RELIANCE"
    assert r_typo.match_type == MatchType.FUZZY_NAME
    assert r_typo.confidence >= 0.80


def test_ambiguous_conglomerate_resolution():
    """Verifies that conglomerate names like 'Tata' are never arbitrarily resolved, but flagged as ambiguous."""
    r_tata = company_resolution_service.resolve_company("Tata")
    assert r_tata.is_ambiguous is True
    assert r_tata.match_type == MatchType.AMBIGUOUS
    assert r_tata.clarification_prompt is not None
    assert "Multiple companies match 'Tata'" in r_tata.clarification_prompt
    candidate_syms = [c.symbol for c in r_tata.candidate_matches]
    assert "TATAMOTORS" in candidate_syms
    assert "TCS" in candidate_syms
    assert "TATASTEEL" in candidate_syms


def test_extract_and_resolve_companies_from_text():
    """Verifies scanning freeform text for multiple distinct securities."""
    text = "I would like to include Bharat Electronics, ITC and Larsen & Toubro."
    entities = company_resolution_service.extract_and_resolve_companies_from_text(text)
    symbols = {e.resolved_symbol for e in entities}
    assert "BEL" in symbols
    assert "ITC" in symbols
    assert "LT" in symbols


# ---------------------------------------------------------------------------
# 3. End-to-End NLP Extraction Integration Tests
# ---------------------------------------------------------------------------

def test_extract_investor_profile_user_sample_prompt():
    """
    Validates the user's primary prompt:
    'I have ₹2.5 lakh to invest for five years. I want a moderate-risk portfolio and would like to
    include Bharat Electronics, ITC and Larsen & Toubro. Do not allocate more than 20% to the banking sector.'
    """
    prompt = (
        "I have ₹2.5 lakh to invest for five years. I want a moderate-risk portfolio and would like to "
        "include Bharat Electronics, ITC and Larsen & Toubro. Do not allocate more than 20% to the banking sector."
    )
    profile = deterministic_extract_investor_profile(prompt)

    # Capital
    assert profile.capital.initial_lump_sum == 250_000.0

    # Horizon
    assert profile.horizon_months == 60
    assert profile.horizon_years == 5.0

    # Risk Tier
    assert profile.risk.assessed_risk_category.value == "moderate"

    # Preferred Securities
    pref_syms = {p.resolved_symbol for p in profile.preferences.preferred_securities}
    assert pref_syms == {"BEL", "LT", "ITC"}

    # Sector Constraints
    assert len(profile.preferences.sector_constraints) == 1
    sc = profile.preferences.sector_constraints[0]
    assert sc.sector == "Financial Services"
    assert sc.operator == "LTE"
    assert sc.value == 20.0
    assert sc.unit == "PERCENT"


def test_extract_existing_holdings_with_quantities():
    """Verifies that existing holdings extract company tickers, share quantities, and monetary values."""
    text = "I already own 50 shares of BEL and 100 shares of TCS, and ₹25,000 worth of Infosys."
    holdings = extract_existing_holdings(text)

    holdings_dict = {h.symbol: h for h in holdings}
    assert "BEL" in holdings_dict
    assert holdings_dict["BEL"].quantity == 50

    assert "TCS" in holdings_dict
    assert holdings_dict["TCS"].quantity == 100

    assert "INFY" in holdings_dict
    assert holdings_dict["INFY"].current_value == 25_000.0


def test_onboarding_extraction_accuracy_and_negative_exclusions():
    """
    Validates extraction of investor Ankur's onboarding text:
    Ensures preferred sectors includes Financial Services & IT, while Betting and Tobacco are excluded.
    """
    text = (
        "Hey I am Ankur, i am a 26 year old with 50,000 to invest for 2 years. I have a moderate risk appetite "
        "and a full 1-month emergency fund in bank FDs. I have no experience in mutual funds and want strong exposure "
        "to Information Technology and Banking, but please avoid Tobacco, and Betting."
    )
    profile = deterministic_extract_investor_profile(text)

    assert profile.capital.initial_lump_sum == 50_000.0
    assert profile.horizon_months == 24
    assert profile.risk.assessed_risk_category.value == "moderate"
    assert profile.risk.emergency_fund_status == "partial"
    assert profile.experience.experience_level == "beginner"

    assert "Information Technology" in profile.preferences.preferred_sectors
    assert "Financial Services" in profile.preferences.preferred_sectors
    assert "Tobacco" in profile.preferences.excluded_sectors
    assert "Betting & Gambling" in profile.preferences.excluded_sectors


# ---------------------------------------------------------------------------
# 4. API Endpoints Integration Tests
# ---------------------------------------------------------------------------

def test_api_security_search_typo_fuzzy(client: TestClient):
    """GET /api/v1/market-data/securities/search with typo."""
    response = client.get("/api/v1/market-data/securities/search", params={"q": "Relience"})
    assert response.status_code == 200
    data = response.json()
    assert data["matched_symbol"] == "RELIANCE"
    assert data["match_type"] == "FUZZY_NAME"
    assert data["is_ambiguous"] is False


def test_api_security_search_ambiguity(client: TestClient):
    """GET /api/v1/market-data/securities/search with ambiguous conglomerate 'Tata'."""
    response = client.get("/api/v1/market-data/securities/search", params={"q": "Tata"})
    assert response.status_code == 200
    data = response.json()
    assert data["is_ambiguous"] is True
    assert "Multiple companies match 'Tata'" in data["clarification_prompt"]
    symbols = [c["symbol"] for c in data["candidate_matches"]]
    assert "TCS" in symbols


def test_api_parse_financial_expression(client: TestClient):
    """POST /api/v1/market-data/parse-financial-expression."""
    response = client.post(
        "/api/v1/market-data/parse-financial-expression",
        json={"text": "not more than 20%"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["normalized_value"] == 20.0
    assert data["comparison_operator"] == "LTE"
    assert data["unit"] == "PERCENT"


def test_api_profile_extract_from_text(client: TestClient):
    """POST /api/v1/profile/extract-from-text with full user prompt."""
    payload = {
        "text": (
            "I have ₹2.5 lakh to invest for five years. I want a moderate-risk portfolio and would like to "
            "include Bharat Electronics, ITC and Larsen & Toubro. Do not allocate more than 20% to the banking sector."
        )
    }
    response = client.post("/api/v1/profile/extract-from-text", json=payload)
    assert response.status_code == 200
    data = response.json()

    extracted = data["extracted_profile"]
    assert extracted["investment_amount"] == 250_000.0
    assert extracted["horizon_months"] == 60
    assert extracted["risk_category"] == "moderate"

    pref_secs = {s["resolved_symbol"] for s in extracted["preferred_securities"]}
    assert pref_secs == {"BEL", "LT", "ITC"}

    assert len(extracted["sector_constraints"]) == 1
    assert extracted["sector_constraints"][0]["sector"] == "Financial Services"
    assert extracted["sector_constraints"][0]["operator"] == "LTE"
    assert extracted["sector_constraints"][0]["value"] == 20.0

