"""
Seed a realistic universe of Indian equities (Reliance, TCS, HDFC Bank, Infosys, etc.)
along with sectors, industries, exchange listings, and initial prices.
Idempotent and safe to run multiple times.
"""

import uuid
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

try:
    from backend.database import SessionLocal
    from backend.models import (
        Exchange,
        Sector,
        Industry,
        Company,
        CompanyIndustry,
        Security,
        InstrumentListing,
        DataSource,
        MarketPrice,
    )
    from backend.market_data.adapter import SimulatedMarketProvider
    from backend.market_data.ingestion import MarketDataIngestionService
except ImportError:
    from database import SessionLocal
    from models import (
        Exchange,
        Sector,
        Industry,
        Company,
        CompanyIndustry,
        Security,
        InstrumentListing,
        DataSource,
        MarketPrice,
    )
    from market_data.adapter import SimulatedMarketProvider
    from market_data.ingestion import MarketDataIngestionService

NSE_EXCHANGE_ID = uuid.UUID("30000000-0000-4000-8000-000000000002")

UNIVERSE_DATA = [
    {
        "symbol": "RELIANCE",
        "company_name": "Reliance Industries Limited",
        "isin": "INE002A01018",
        "sector_code": "ENERGY",
        "sector_name": "Energy & Petrochemicals",
        "industry_code": "OIL_GAS_REFINING",
        "industry_name": "Oil & Gas Refining & Marketing",
        "base_price": 2850.0,
    },
    {
        "symbol": "TCS",
        "company_name": "Tata Consultancy Services Limited",
        "isin": "INE467B01029",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Consulting",
        "base_price": 3950.0,
    },
    {
        "symbol": "HDFCBANK",
        "company_name": "HDFC Bank Limited",
        "isin": "INE040A01034",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1680.0,
    },
    {
        "symbol": "INFY",
        "company_name": "Infosys Limited",
        "isin": "INE009A01021",
        "sector_code": "TECH",
        "sector_name": "Information Technology",
        "industry_code": "IT_SERVICES",
        "industry_name": "IT Services & Consulting",
        "base_price": 1820.0,
    },
    {
        "symbol": "ICICIBANK",
        "company_name": "ICICI Bank Limited",
        "isin": "INE090A01021",
        "sector_code": "FINANCIALS",
        "sector_name": "Banking & Financial Services",
        "industry_code": "PRIVATE_BANKS",
        "industry_name": "Private Sector Banks",
        "base_price": 1240.0,
    },
    {
        "symbol": "TATAMOTORS",
        "company_name": "Tata Motors Limited",
        "isin": "INE155A01022",
        "sector_code": "AUTO",
        "sector_name": "Automotive",
        "industry_code": "COMMERCIAL_VEHICLES",
        "industry_name": "Automobiles & Commercial Vehicles",
        "base_price": 940.0,
    },
    {
        "symbol": "SUNPHARMA",
        "company_name": "Sun Pharmaceutical Industries Limited",
        "isin": "INE044A01036",
        "sector_code": "HEALTH",
        "sector_name": "Healthcare & Pharmaceuticals",
        "industry_code": "PHARMACEUTICALS",
        "industry_name": "Pharmaceuticals",
        "base_price": 1720.0,
    },
    {
        "symbol": "HINDUNILVR",
        "company_name": "Hindustan Unilever Limited",
        "isin": "INE030A01027",
        "sector_code": "FMCG",
        "sector_name": "Fast Moving Consumer Goods",
        "industry_code": "PACKAGED_FOODS",
        "industry_name": "Diversified FMCG",
        "base_price": 2480.0,
    },
]


def seed_market_universe(db: Session) -> int:
    """Seeds Indian equities universe and populates price history."""
    # Ensure NSE Exchange exists
    exchange = db.query(Exchange).filter(Exchange.exchange_code == "NSE").first()
    if not exchange:
        exchange = Exchange(
            exchange_id=NSE_EXCHANGE_ID,
            exchange_code="NSE",
            exchange_name="National Stock Exchange of India",
            country_code="IN",
            currency_code="INR",
        )
        db.add(exchange)
        db.flush()

    source = db.query(DataSource).filter(DataSource.source_code == "demo_source").first()
    if not source:
        source = DataSource(
            data_source_id=uuid.uuid4(),
            source_code="demo_source",
            display_name="Illustrative Indian Equities Data",
            source_type="market_data",
            is_active=True,
        )
        db.add(source)
        db.flush()

    created_securities = 0
    sim_provider = SimulatedMarketProvider()

    for item in UNIVERSE_DATA:
        # 1. Sector
        sector = db.query(Sector).filter(Sector.sector_code == item["sector_code"]).first()
        if not sector:
            sector = Sector(
                sector_id=uuid.uuid4(),
                sector_code=item["sector_code"],
                sector_name=item["sector_name"],
            )
            db.add(sector)
            db.flush()

        # 2. Industry
        industry = db.query(Industry).filter(Industry.industry_code == item["industry_code"]).first()
        if not industry:
            industry = Industry(
                industry_id=uuid.uuid4(),
                sector_id=sector.sector_id,
                industry_code=item["industry_code"],
                industry_name=item["industry_name"],
            )
            db.add(industry)
            db.flush()

        # 3. Company
        company = db.query(Company).filter(Company.legal_name == item["company_name"]).first()
        if not company:
            company = Company(
                company_id=uuid.uuid4(),
                legal_name=item["company_name"],
                common_name=item["company_name"].replace(" Limited", ""),
                country_code="IN",
            )
            db.add(company)
            db.flush()

            comp_ind = CompanyIndustry(
                company_id=company.company_id,
                industry_id=industry.industry_id,
                effective_from=date(2020, 1, 1),
            )
            db.add(comp_ind)
            db.flush()

        # 4. Security
        security = db.query(Security).filter(Security.isin == item["isin"]).first()
        if not security:
            security = Security(
                security_id=uuid.uuid4(),
                company_id=company.company_id,
                security_name=item["company_name"].replace(" Limited", " Equity"),
                isin=item["isin"],
                security_type="stock",
                currency_code="INR",
                security_status="active",
            )
            db.add(security)
            db.flush()
            created_securities += 1

        # 5. Instrument Listing
        listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == item["symbol"]).first()
        if not listing:
            listing = InstrumentListing(
                listing_id=uuid.uuid4(),
                security_id=security.security_id,
                exchange_id=exchange.exchange_id,
                symbol=item["symbol"],
                trading_status="active",
            )
            db.add(listing)
            db.flush()

        # 6. Seed recent daily prices (last 30 days)
        today = date.today()
        start_date = today - timedelta(days=30)
        curr = start_date
        while curr <= today:
            if curr.weekday() < 5:
                existing_price = (
                    db.query(MarketPrice)
                    .filter(
                        MarketPrice.listing_id == listing.listing_id,
                        MarketPrice.price_date == curr,
                        MarketPrice.data_source_id == source.data_source_id,
                    )
                    .first()
                )
                if not existing_price:
                    seed_val = (hash(item["symbol"]) + curr.toordinal()) % 1000
                    delta_pct = (seed_val - 500) / 10000.0
                    close_p = round(item["base_price"] * (1.0 + delta_pct), 2)
                    high_p = round(close_p * 1.015, 2)
                    low_p = round(close_p * 0.985, 2)
                    open_p = round((high_p + low_p) / 2.0, 2)

                    p_rec = MarketPrice(
                        market_price_id=uuid.uuid4(),
                        listing_id=listing.listing_id,
                        data_source_id=source.data_source_id,
                        price_date=curr,
                        open_price=open_p,
                        high_price=high_p,
                        low_price=low_p,
                        close_price=close_p,
                        adjusted_close_price=close_p,
                        volume=25000 + (seed_val * 10),
                        currency_code="INR",
                        retrieved_at=datetime.now(),
                    )
                    db.add(p_rec)
            curr += timedelta(days=1)

    db.commit()
    return created_securities


if __name__ == "__main__":
    db = SessionLocal()
    try:
        cnt = seed_market_universe(db)
        print(f"✅ Successfully seeded market universe ({cnt} new securities added).")
    finally:
        db.close()
