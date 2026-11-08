"""
Comprehensive Automated Unit and Integration Tests for External Links and URL Verification in Lucid.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.link_verification_service import (
    LinkVerificationService,
    LinkStatus,
    ResourceType,
    link_verifier,
)
from backend.services.exchange_registry import (
    resolve_stock_filings,
    get_canonical_nse_announcements_url,
    get_canonical_bse_announcements_url,
    clean_equity_symbol,
    VERIFIED_STOCKS,
    REGULATORY_REGISTRY,
)
from backend.portfolio_engine.conversational_assistant import (
    get_security_market_info,
    format_comprehensive_unrecommended_evidence,
    get_rich_security_rationale,
    COMPANY_THESES,
)

client = TestClient(app)


def test_clean_equity_symbol():
    assert clean_equity_symbol("RELIANCE.NS") == "RELIANCE"
    assert clean_equity_symbol("tcs.bo") == "TCS"
    assert clean_equity_symbol("  infy  ") == "INFY"
    assert clean_equity_symbol("") == ""


def test_canonical_nse_url_builder():
    url = get_canonical_nse_announcements_url("RELIANCE")
    assert url == "https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol=RELIANCE"
    assert "StockPrcStk" not in url


def test_canonical_bse_url_builder():
    # With verified scrip code
    bse_url = get_canonical_bse_announcements_url("TCS", "532540")
    assert bse_url == "https://www.bseindia.com/stock-share-price/tcs/532540/corp-announcements/"

    # Without scrip code fallback
    fallback_url = get_canonical_bse_announcements_url("UNKNOWN_SYM", None)
    assert fallback_url == "https://www.bseindia.com/corporates/ann.html"
    assert "StockPrcStk.html" not in fallback_url


def test_resolve_stock_filings_structure():
    filings = resolve_stock_filings("TCS")
    assert filings["symbol"] == "TCS"
    assert filings["bse_code"] == "532540"
    assert filings["is_bse_verified"] is True
    assert filings["primary_exchange"] == "BSE"
    assert filings["primary_filing_url"] == "https://www.bseindia.com/stock-share-price/tcs/532540/corp-announcements/"
    assert "https://www.nseindia.com" in filings["nse_announcements_url"]
    assert filings["is_safe_canonical"] is True


def test_resolve_stock_filings_unlisted_fallback():
    filings = resolve_stock_filings("NEWCO_UNLISTED_SYM")
    assert filings["symbol"] == "NEWCO_UNLISTED_SYM"
    assert filings["is_bse_verified"] is False
    assert filings["primary_exchange"] == "NSE"
    assert "nseindia.com/companies-listing" in filings["primary_filing_url"]


def test_all_72_verified_stocks_generate_clean_filing_descriptors():
    for sym in VERIFIED_STOCKS.keys():
        desc = resolve_stock_filings(sym)
        assert desc["symbol"] == sym
        assert desc["primary_filing_url"].startswith("https://")
        assert "StockPrcStk.html" not in desc["primary_filing_url"]
        assert desc["bse_code"] is not None and desc["bse_code"].isdigit()


def test_link_verifier_invalid_scheme():
    res = link_verifier.verify_url("ftp://example.com/file")
    assert res.status == LinkStatus.BROKEN
    assert "Invalid URL scheme" in res.error_message


def test_link_verifier_dead_domain():
    res = link_verifier.verify_url("https://this-is-a-completely-non-existent-subdomain-123456.gov.in")
    assert res.status == LinkStatus.BROKEN


def test_agent_guardrail_no_hash_bse_codes():
    """Verify that agent security resolution never fabricates pseudo-random BSE scrip codes."""
    # Test for unlisted symbol
    data = get_security_market_info("NONEXISTENT_XYZ")
    assert data["bse_code"] != "500000"
    assert not (data["bse_code"].isdigit() and len(data["bse_code"]) == 6 and data["bse_code"] not in [v.get("bse_code") for v in VERIFIED_STOCKS.values()])
    assert data["nse_symbol"] == "NONEXISTENT_XYZ"


def test_rejection_rationale_has_verified_provenance_link():
    """Verify that AI Copilot rejection explanations cite verified canonical links, not hallucinated strings."""
    reply, followups = format_comprehensive_unrecommended_evidence(
        "DIVISLAB",
        {"company_name": "Divi's Laboratories", "sector_name": "Healthcare"},
        "Why was DIVISLAB rejected?",
    )
    assert "https://www.nseindia.com" in reply or "https://www.bseindia.com" in reply
    assert "StockPrcStk.html" not in reply


def test_api_links_filings_endpoint():
    resp = client.get("/api/v1/links/filings/INFY")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "INFY"
    assert data["bse_code"] == "500209"
    assert "corp-announcements" in data["primary_filing_url"]
    assert data["primary_verification"]["status"] in ["VERIFIED", "REDIRECTED_AND_VERIFIED"]


def test_api_links_regulatory_endpoint():
    resp = client.get("/api/v1/links/regulatory")
    assert resp.status_code == 200
    data = resp.json()
    assert "regulatory_portals" in data
    keys = [p["key"] for p in data["regulatory_portals"]]
    assert "SEBI_MAIN" in keys
    assert "SEBI_SCORES" in keys
    assert "SMART_ODR" in keys
