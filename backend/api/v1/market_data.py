"""
Market Data API endpoints (Fetch prices, trigger ingestion, view ingestion history).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from pydantic import BaseModel

try:
    from backend.database import get_db
    from backend.models import (
        MarketPrice,
        InstrumentListing,
        DataIngestionRun,
        AppUser,
        EconomicIndicator,
        EconomicObservation,
        MarketNewsArticle,
        NewsArticleSecurity,
    )
    from backend.market_data.ingestion import MarketDataIngestionService
    from backend.market_data.adapter import SimulatedMarketProvider, YFinanceProvider
    from backend.market_data.regime import detect_market_regime, seed_macro_and_news_data
    from backend.schemas import IngestionRunRead
    from backend.auth.dependencies import get_current_user
    from backend.config import settings
except ImportError:
    from database import get_db
    from models import (
        MarketPrice,
        InstrumentListing,
        DataIngestionRun,
        AppUser,
        EconomicIndicator,
        EconomicObservation,
        MarketNewsArticle,
        NewsArticleSecurity,
    )
    from market_data.ingestion import MarketDataIngestionService
    from market_data.adapter import SimulatedMarketProvider, YFinanceProvider
    from market_data.regime import detect_market_regime, seed_macro_and_news_data
    from schemas import IngestionRunRead
    from auth.dependencies import get_current_user
    from config import settings

router = APIRouter(prefix="/market-data", tags=["Market Data"])


def require_admin_or_dev(user: AppUser = Depends(get_current_user)) -> AppUser:
    """Restricts access in staging/production to authorized administrators."""
    if settings.app_env in ("staging", "production"):
        is_admin = (
            getattr(user, "is_admin", False)
            or "admin" in (user.email or "").lower()
            or (user.identity_subject or "").startswith("admin-")
        )
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrator authorization required for data ingestion operations.",
            )
    return user


@router.get("/health")
async def market_data_health():
    """
    Evaluates market data provider connectivity, quote latency, freshness,
    and returns provider inventory status.
    """
    yf = YFinanceProvider()
    sim = SimulatedMarketProvider()

    yf_health = yf.check_health()
    sim_health = sim.check_health()

    return {
        "status": yf_health.get("status", "UNKNOWN"),
        "primary_provider": yf.provider_name,
        "environment": settings.app_env,
        "providers": {
            "yfinance": yf_health,
            "simulated": sim_health,
        },
        "disclaimer": "Simulated data is restricted to offline testing and isolated CI environments.",
    }


class IngestRequest(BaseModel):
    symbol: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    provider: Optional[str] = None


@router.post("/ingest", response_model=IngestionRunRead, status_code=status.HTTP_201_CREATED)
async def trigger_ingestion(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin_or_dev),
):
    """Trigger an idempotent ingestion job for a stock symbol."""
    start = payload.start_date or (date.today() - timedelta(days=30))
    end = payload.end_date or date.today()

    # In production, strictly enforce live provider
    is_prod = settings.app_env == "production"
    use_yfinance = payload.provider == "yfinance" or is_prod or (payload.provider is None and settings.app_env != "test")

    if use_yfinance:
        provider = YFinanceProvider()
        source_code = "yfinance_source"
    else:
        provider = SimulatedMarketProvider()
        source_code = "demo_source"

    service = MarketDataIngestionService(db=db, provider=provider)
    try:
        run = service.ingest_symbol_history(
            symbol=payload.symbol,
            start_date=start,
            end_date=end,
            source_code=source_code,
        )
        return IngestionRunRead(
            ingestion_run_id=run.ingestion_run_id,
            source_code=source_code,
            data_type=run.data_type,
            run_status=run.run_status,
            records_seen=run.records_seen,
            records_inserted=run.records_inserted,
            records_updated=run.records_updated,
            started_at=run.started_at,
            finished_at=run.finished_at,
            error_summary=run.error_summary,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/ingestion-runs", response_model=List[IngestionRunRead])
async def list_ingestion_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin_or_dev),
):
    """List recent data ingestion pipeline runs."""
    runs = (
        db.query(DataIngestionRun)
        .order_by(DataIngestionRun.started_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for r in runs:
        result.append(
            IngestionRunRead(
                ingestion_run_id=r.ingestion_run_id,
                source_code=r.data_source.source_code if r.data_source else "unknown",
                data_type=r.data_type,
                run_status=r.run_status,
                records_seen=r.records_seen,
                records_inserted=r.records_inserted,
                records_updated=r.records_updated,
                started_at=r.started_at,
                finished_at=r.finished_at,
                error_summary=r.error_summary,
            )
        )
    return result


@router.get("/prices/{symbol}")
async def get_symbol_prices(
    symbol: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Retrieve historical market prices for an exchange symbol."""
    listing = db.query(InstrumentListing).filter(InstrumentListing.symbol == symbol).first()
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Symbol {symbol} not found")

    start_date = date.today() - timedelta(days=days)
    prices = (
        db.query(MarketPrice)
        .filter(MarketPrice.listing_id == listing.listing_id, MarketPrice.price_date >= start_date)
        .order_by(MarketPrice.price_date.desc())
        .all()
    )
    return {
        "symbol": symbol,
        "security_name": listing.security.security_name if listing.security else None,
        "count": len(prices),
        "prices": [
            {
                "date": p.price_date.isoformat(),
                "open": float(p.open_price) if p.open_price else None,
                "high": float(p.high_price) if p.high_price else None,
                "low": float(p.low_price) if p.low_price else None,
                "close": float(p.close_price),
                "adjusted_close": float(p.adjusted_close_price) if p.adjusted_close_price else None,
                "volume": p.volume,
            }
            for p in prices
        ],
    }


@router.get("/regime")
async def get_market_regime(
    vix: Optional[float] = Query(None, ge=5.0, le=90.0, description="Optional override for India VIX level"),
    db: Session = Depends(get_db),
):
    """
    6.11 Evaluates live market regime (CALM, MODERATE, VOLATILE, EXTREME)
    using India VIX and realized equity volatility to guide portfolio risk parameters.
    """
    return detect_market_regime(db=db, current_vix=vix)


@router.get("/macro-indicators")
async def get_macro_indicators(
    db: Session = Depends(get_db),
):
    """
    6.5 Retrieves key Indian macroeconomic indicators (RBI Repo Rate, CPI Inflation,
    GDP Growth, 10Y Sovereign Yield, India VIX) from the database.
    """
    # Ensure baseline data is seeded
    seed_macro_and_news_data(db)

    indicators = db.query(EconomicIndicator).all()
    results = []
    for ind in indicators:
        latest_obs = (
            db.query(EconomicObservation)
            .filter(EconomicObservation.economic_indicator_id == ind.economic_indicator_id)
            .order_by(EconomicObservation.observation_date.desc())
            .first()
        )
        results.append({
            "indicator_code": ind.indicator_code,
            "indicator_name": ind.indicator_name,
            "unit": ind.unit_code,
            "frequency": ind.frequency,
            "description": ind.description,
            "latest_value": float(latest_obs.observation_value) if latest_obs else None,
            "as_of_date": latest_obs.observation_date.isoformat() if latest_obs else None,
        })
    return {"count": len(results), "indicators": results}


@router.get("/news")
async def get_market_news(
    symbol: Optional[str] = Query(None, description="Optional stock symbol filter"),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """
    6.4 Retrieves structured market news articles with sentiment scores and security links.
    """
    seed_macro_and_news_data(db)

    query = db.query(MarketNewsArticle)
    if symbol:
        sym_clean = symbol.upper().strip()
        query = (
            query.join(NewsArticleSecurity, MarketNewsArticle.news_article_id == NewsArticleSecurity.news_article_id)
            .join(InstrumentListing, NewsArticleSecurity.security_id == InstrumentListing.security_id)
            .filter(InstrumentListing.symbol == sym_clean)
        )

    articles = query.order_by(MarketNewsArticle.published_at.desc()).limit(limit).all()
    results = []
    for art in articles:
        related_symbols = [
            link.security.listings[0].symbol
            for link in art.security_links
            if link.security and link.security.listings
        ]
        results.append({
            "news_article_id": str(art.news_article_id),
            "headline": art.headline,
            "summary": art.summary,
            "source": art.data_source.display_name if art.data_source else "Financial News",
            "article_url": art.article_url,
            "sentiment_score": float(art.sentiment_score) if art.sentiment_score is not None else 0.0,
            "sentiment_label": art.sentiment_label,
            "published_at": art.published_at.isoformat() if art.published_at else None,
            "related_symbols": related_symbols,
        })
    return {"count": len(results), "articles": results}


@router.get("/universe-stats")
async def get_market_universe_stats(db: Session = Depends(get_db)):
    """
    Returns live statistics on the active listed securities universe,
    including sector distribution, active listings count, and price freshness.
    """
    from backend.models import Security, Sector, Company
    total_active_securities = db.query(Security).filter(Security.security_status == "active").count()
    total_companies = db.query(Company).count()
    total_listings = db.query(InstrumentListing).filter(InstrumentListing.trading_status == "active").count()

    sectors = db.query(Sector).filter(Sector.is_active == True).all()
    sector_summary = [{"code": s.sector_code, "name": s.sector_name} for s in sectors]

    return {
        "status": "healthy",
        "exchange": "National Stock Exchange of India (NSE)",
        "total_active_securities": total_active_securities,
        "total_companies": total_companies,
        "total_active_listings": total_listings,
        "sectors_count": len(sector_summary),
        "sectors": sector_summary,
    }


@router.post("/sync-universe")
async def sync_exchange_universe(
    mode: str = Query("full", description="Sync scope: 'full' (all 2,630+ NSE/BSE equities) or 'benchmark' (Nifty 500)"),
    populate_prices: bool = Query(True, description="Whether to populate recent historical prices for benchmark equities"),
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin_or_dev),
):
    """
    Trigger live synchronization with official National Stock Exchange (NSE) archives:
    - 'full': Synchronizes all 2,630+ active listed equity securities from EQUITY_L.csv
    - 'benchmark': Synchronizes the 501 liquid Nifty 500 constituents
    """
    if mode == "benchmark":
        from backend.market_data.exchange_universe_sync import sync_nifty500_universe
        return sync_nifty500_universe(db, populate_prices=populate_prices)
    else:
        from backend.market_data.exchange_universe_sync import sync_full_exchange_universe
        return sync_full_exchange_universe(db, populate_benchmark_prices=populate_prices)


@router.get("/reconcile-universe")
async def reconcile_exchange_universe(
    db: Session = Depends(get_db),
):
    """
    Performs live architectural reconciliation between PostgreSQL security master
    and official NSE & BSE exchange archives, reporting coverage and eligibility stats.
    """
    from backend.market_data.exchange_universe_sync import reconcile_universe_against_exchanges
    return reconcile_universe_against_exchanges(db)


class TextExpressionRequest(BaseModel):
    text: str


@router.get("/securities/search")
async def search_securities(
    q: str = Query(..., min_length=1, description="Company name, ticker, alias, or ISIN to resolve"),
    limit: int = Query(10, ge=1, le=50),
):
    """
    Dynamically searches and resolves companies, NSE/BSE tickers, and ISINs.
    Identifies exact symbols, normalized names, aliases, typos, and conglomerate ambiguities.
    """
    try:
        from backend.services.company_resolution_service import company_resolution_service
    except ImportError:
        from services.company_resolution_service import company_resolution_service

    resolution = company_resolution_service.resolve_company(q)
    candidates = company_resolution_service.repo.search_candidates(q, limit=limit)
    return {
        "query": q,
        "is_ambiguous": resolution.is_ambiguous,
        "matched_symbol": resolution.matched_symbol,
        "company_name": resolution.company_name,
        "exchange": resolution.exchange,
        "isin": resolution.isin,
        "bse_code": resolution.bse_code,
        "sector": resolution.sector,
        "match_type": resolution.match_type.value,
        "confidence": resolution.confidence,
        "clarification_prompt": resolution.clarification_prompt,
        "candidate_matches": [c.model_dump() for c in resolution.candidate_matches] if resolution.candidate_matches else [c.model_dump() for c in candidates],
    }


@router.post("/securities/resolve-text")
async def resolve_text_entities(payload: TextExpressionRequest):
    """
    Extracts all company and security mentions from freeform natural language text.
    Resolves each entity against the dynamic NSE/BSE security master repository.
    """
    try:
        from backend.services.company_resolution_service import company_resolution_service
    except ImportError:
        from services.company_resolution_service import company_resolution_service

    entities = company_resolution_service.extract_and_resolve_companies_from_text(payload.text)
    return {
        "text": payload.text,
        "count": len(entities),
        "entities": [e.model_dump() for e in entities],
    }


@router.post("/parse-financial-expression")
async def parse_financial_expression(payload: TextExpressionRequest):
    """
    Parses complex natural language financial expressions into structured values.
    Supports Indian & international scales, comparison operators (LTE, GTE, BETWEEN),
    currency amounts, percentages, horizons, and share quantities.
    """
    try:
        from backend.services.financial_number_parser import financial_number_parser
    except ImportError:
        from services.financial_number_parser import financial_number_parser

    parsed = financial_number_parser.parse_expression(payload.text)
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse a numeric or financial value from: '{payload.text}'",
        )
    return parsed.model_dump()

