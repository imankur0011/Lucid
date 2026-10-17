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
    from backend.models import MarketPrice, InstrumentListing, DataIngestionRun, AppUser
    from backend.market_data.ingestion import MarketDataIngestionService
    from backend.market_data.adapter import SimulatedMarketProvider, YFinanceProvider
    from backend.schemas import IngestionRunRead
    from backend.auth.dependencies import get_current_user
    from backend.config import settings
except ImportError:
    from database import get_db
    from models import MarketPrice, InstrumentListing, DataIngestionRun, AppUser
    from market_data.ingestion import MarketDataIngestionService
    from market_data.adapter import SimulatedMarketProvider, YFinanceProvider
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


class IngestRequest(BaseModel):
    symbol: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    provider: str = "simulated"  # or "yfinance"


@router.post("/ingest", response_model=IngestionRunRead, status_code=status.HTTP_201_CREATED)
async def trigger_ingestion(
    payload: IngestRequest,
    db: Session = Depends(get_db),
    admin: AppUser = Depends(require_admin_or_dev),
):
    """Trigger an idempotent ingestion job for a stock symbol."""
    start = payload.start_date or (date.today() - timedelta(days=30))
    end = payload.end_date or date.today()

    if payload.provider == "yfinance":
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
