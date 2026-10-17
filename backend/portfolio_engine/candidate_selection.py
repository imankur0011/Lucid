"""
Candidate Selection Module.
Filters universe of active securities against investor exclusions, sector limits, and data freshness.
"""

from typing import List, Dict, Any, Set
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from backend.models import Security, InstrumentListing, Sector, Company, Industry, MarketPrice
    from backend.market_data.quality import verify_listing_freshness
except ImportError:
    from models import Security, InstrumentListing, Sector, Company, Industry, MarketPrice
    from market_data.quality import verify_listing_freshness


class CandidateUniverseSelector:
    """Selects eligible securities based on status, exclusions, and market data freshness."""

    def __init__(self, db: Session, max_stale_days: int = 14):
        self.db = db
        self.max_stale_days = max_stale_days

    def select_eligible_candidates(
        self,
        excluded_sectors: Optional[List[str]] = None,
        excluded_instruments: Optional[List[str]] = None,
        as_of_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries all active securities, filters against exclusions,
        and verifies market data freshness.
        """
        ex_sectors: Set[str] = {s.strip().upper() for s in (excluded_sectors or [])}
        ex_instruments: Set[str] = {i.strip().upper() for i in (excluded_instruments or [])}

        securities = (
            self.db.query(Security)
            .filter(Security.security_status == "active")
            .all()
        )

        candidates = []
        for sec in securities:
            # Check instrument exclusions by ISIN or name
            if sec.isin and sec.isin.upper() in ex_instruments:
                continue
            if sec.security_name and sec.security_name.upper() in ex_instruments:
                continue

            # Check primary listing
            listing = sec.listings[0] if sec.listings else None
            if not listing or listing.trading_status != "active":
                continue

            if listing.symbol and listing.symbol.upper() in ex_instruments:
                continue

            # Check company sector
            company = sec.company
            sector_name = "General"
            sector_code = "GENERAL"
            industry_name = "Diversified"

            if company and company.industries:
                ind = company.industries[0].industry
                if ind:
                    industry_name = ind.industry_name
                    if ind.sector:
                        sector_name = ind.sector.sector_name
                        sector_code = ind.sector.sector_code

            if sector_code.upper() in ex_sectors or sector_name.upper() in ex_sectors:
                continue

            # Verify market price freshness
            is_fresh, price_date, latest_price, reason = verify_listing_freshness(
                self.db, listing.listing_id, as_of_date=as_of_date, max_stale_days=self.max_stale_days
            )
            if not is_fresh or latest_price is None or latest_price <= 0:
                continue

            candidates.append({
                "security_id": sec.security_id,
                "listing_id": listing.listing_id,
                "symbol": listing.symbol,
                "security_name": sec.security_name,
                "isin": sec.isin,
                "sector_name": sector_name,
                "sector_code": sector_code,
                "industry_name": industry_name,
                "latest_price": latest_price,
                "price_date": price_date,
            })

        return candidates
