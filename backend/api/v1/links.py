"""
External Link Verification and Filing Gateway Endpoints.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from backend.services.link_verification_service import link_verifier, LinkStatus
from backend.services.exchange_registry import (
    resolve_stock_filings,
    REGULATORY_REGISTRY,
    VERIFIED_STOCKS,
    clean_equity_symbol,
)

router = APIRouter(prefix="/links", tags=["Link Verification & Disclosures"])


@router.get("/verify")
def verify_external_url(
    url: str = Query(..., description="Target external URL to verify"),
    fallback_url: Optional[str] = Query(None, description="Optional fallback URL"),
):
    """
    Verify reachability, HTTP status code, redirect path, and soft-404 status of any URL.
    """
    res = link_verifier.verify_url(url=url, fallback_url=fallback_url)
    return res.to_dict()


@router.get("/filings/{symbol}")
def get_equity_filings(
    symbol: str,
    bse_code: Optional[str] = Query(None, description="Optional verified BSE scrip code"),
):
    """
    Retrieve verified exchange filing URLs (NSE corporate filings, BSE corporate announcements, IR portal)
    for any Indian equity.
    """
    clean_sym = clean_equity_symbol(symbol)
    if not clean_sym:
        raise HTTPException(status_code=400, detail="Invalid equity symbol")

    filing_data = resolve_stock_filings(clean_sym, bse_code)

    # Health-verify primary URL
    primary_meta = link_verifier.verify_url(
        url=filing_data["primary_filing_url"],
        display_label=filing_data["primary_filing_label"],
        fallback_url=filing_data["nse_announcements_url"],
    )

    filing_data["primary_verification"] = primary_meta.to_dict()
    return filing_data


@router.get("/regulatory")
def get_regulatory_portals():
    """
    Returns official, verified Indian regulatory and grievance redressal portals.
    """
    results = []
    for key, reg in REGULATORY_REGISTRY.items():
        meta = link_verifier.verify_url(
            url=reg["url"],
            display_label=reg["title"],
        )
        results.append({
            "key": key,
            "title": reg["title"],
            "url": reg["url"],
            "description": reg["description"],
            "category": reg["category"],
            "verification": meta.to_dict(),
        })
    return {"regulatory_portals": results}


@router.get("/audit-report")
def get_system_link_audit():
    """
    Returns comprehensive inventory of all system-governed external links across
    regulatory bodies, exchanges, and the top-tier equity universe.
    """
    # 1. Regulatory
    reg_items = [
        {"url": reg["url"], "display_label": reg["title"], "category": "REGULATORY"}
        for reg in REGULATORY_REGISTRY.values()
    ]

    # 2. Key Stock Filings (sample top 10 for fast report)
    stock_sample = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "DIVISLAB", "TATAMOTORS", "SUNPHARMA"]
    stock_items = []
    for sym in stock_sample:
        filing_info = resolve_stock_filings(sym)
        stock_items.append({
            "url": filing_info["primary_filing_url"],
            "display_label": filing_info["primary_filing_label"],
            "category": "EXCHANGE_FILING",
        })

    all_items = reg_items + stock_items
    verified_results = link_verifier.verify_batch(all_items)

    status_counts = {}
    for r in verified_results:
        st = r.status.value
        status_counts[st] = status_counts.get(st, 0) + 1

    return {
        "summary": {
            "total_links_audited": len(verified_results),
            "status_breakdown": status_counts,
            "healthy": status_counts.get("VERIFIED", 0) + status_counts.get("REDIRECTED_AND_VERIFIED", 0),
            "broken": status_counts.get("BROKEN", 0),
            "access_restricted": status_counts.get("ACCESS_RESTRICTED", 0),
        },
        "links": [r.to_dict() for r in verified_results],
    }

