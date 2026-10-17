"""
Idempotent Market Data Ingestion Pipeline.
Coordinates fetching, normalization, data quality validation, and PostgreSQL upsert.
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

try:
    from backend.models import (
        DataSource,
        DataIngestionRun,
        DataIngestionError,
        InstrumentListing,
        MarketPrice,
    )
    from backend.market_data.adapter import MarketDataProvider, SimulatedMarketProvider
    from backend.market_data.quality import validate_price_record
except ImportError:
    from models import (
        DataSource,
        DataIngestionRun,
        DataIngestionError,
        InstrumentListing,
        MarketPrice,
    )
    from market_data.adapter import MarketDataProvider, SimulatedMarketProvider
    from market_data.quality import validate_price_record


class MarketDataIngestionService:
    """Service executing robust, idempotent ingestion runs into PostgreSQL."""

    def __init__(self, db: Session, provider: Optional[MarketDataProvider] = None):
        self.db = db
        self.provider = provider or SimulatedMarketProvider()

    def get_or_create_data_source(self, source_code: str = "demo_source") -> DataSource:
        """Retrieves or creates the DataSource configuration."""
        source = self.db.query(DataSource).filter(DataSource.source_code == source_code).first()
        if not source:
            source = DataSource(
                data_source_id=uuid.uuid4(),
                source_code=source_code,
                display_name=f"Data Source ({source_code})",
                source_type="market_data",
                is_active=True,
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source

    def ingest_symbol_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        source_code: str = "demo_source",
    ) -> DataIngestionRun:
        """
        Fetches and ingests historical prices for a given listing symbol.
        Idempotent: updates existing dates without duplicate rows.
        """
        source = self.get_or_create_data_source(source_code)

        # Lookup instrument listing
        listing = self.db.query(InstrumentListing).filter(InstrumentListing.symbol == symbol).first()
        if not listing:
            raise ValueError(f"No InstrumentListing registered in database for symbol: {symbol}")

        # Start Ingestion Run
        run = DataIngestionRun(
            ingestion_run_id=uuid.uuid4(),
            data_source_id=source.data_source_id,
            data_type="market_prices",
            run_status="running",
            started_at=datetime.now(),
            records_seen=0,
            records_inserted=0,
            records_updated=0,
            metadata_={"symbol": symbol, "start_date": str(start_date), "end_date": str(end_date)},
        )
        self.db.add(run)
        self.db.commit()

        try:
            raw_records = self.provider.fetch_historical_prices(symbol, start_date, end_date)
            run.records_seen = len(raw_records)

            inserted_count = 0
            updated_count = 0
            error_count = 0

            for raw in raw_records:
                is_valid, err_msg = validate_price_record(raw)
                if not is_valid:
                    error_count += 1
                    err = DataIngestionError(
                        ingestion_error_id=uuid.uuid4(),
                        ingestion_run_id=run.ingestion_run_id,
                        error_code="DATA_QUALITY_VIOLATION",
                        error_message=err_msg or "Validation failure",
                        record_reference=f"{symbol}:{raw.get('price_date')}",
                        is_retryable=False,
                        error_details=raw,
                    )
                    self.db.add(err)
                    continue

                # Prepare PostgreSQL UPSERT
                stmt = insert(MarketPrice).values(
                    market_price_id=uuid.uuid4(),
                    listing_id=listing.listing_id,
                    data_source_id=source.data_source_id,
                    ingestion_run_id=run.ingestion_run_id,
                    price_date=raw["price_date"],
                    open_price=raw.get("open"),
                    high_price=raw.get("high"),
                    low_price=raw.get("low"),
                    close_price=raw["close"],
                    adjusted_close_price=raw.get("adj_close", raw["close"]),
                    volume=raw.get("volume"),
                    currency_code=raw.get("currency", "INR"),
                    retrieved_at=datetime.now(),
                )

                upsert_stmt = stmt.on_conflict_do_update(
                    constraint="uq_market_price_listing_date_source",
                    set_={
                        "open_price": stmt.excluded.open_price,
                        "high_price": stmt.excluded.high_price,
                        "low_price": stmt.excluded.low_price,
                        "close_price": stmt.excluded.close_price,
                        "adjusted_close_price": stmt.excluded.adjusted_close_price,
                        "volume": stmt.excluded.volume,
                        "ingestion_run_id": stmt.excluded.ingestion_run_id,
                        "retrieved_at": stmt.excluded.retrieved_at,
                    },
                )
                res = self.db.execute(upsert_stmt)
                # Check if it was an insert or update
                inserted_count += 1

            run.records_inserted = inserted_count
            run.records_updated = updated_count
            run.finished_at = datetime.now()
            if error_count == 0:
                run.run_status = "succeeded"
            elif error_count < len(raw_records):
                run.run_status = "partial"
                run.error_summary = f"{error_count} records failed quality validation"
            else:
                run.run_status = "failed"
                run.error_summary = "All fetched records failed quality validation"

            self.db.commit()
            return run

        except Exception as exc:
            self.db.rollback()
            run.run_status = "failed"
            run.error_code = "INGESTION_EXCEPTION"
            run.error_summary = str(exc)
            run.finished_at = datetime.now()
            self.db.add(run)
            self.db.commit()
            raise exc
