"""
Market Data Quality Rules and Freshness Verification.
Enforces mathematical consistency (positive prices, high >= low, valid ranges) and data currency.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc

try:
    from backend.models import MarketPrice, InstrumentListing
except ImportError:
    from models import MarketPrice, InstrumentListing


def validate_price_record(record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a single market price bar against mandatory quality rules.
    Returns: (is_valid, error_message)
    """
    close = record.get("close")
    if close is None or close <= 0:
        return False, f"Invalid or non-positive close price: {close}"

    high = record.get("high")
    low = record.get("low")
    open_price = record.get("open")

    if high is not None and low is not None:
        if high < low:
            return False, f"High price ({high}) cannot be lower than Low price ({low})"

        if open_price is not None:
            if open_price > high or open_price < low:
                return False, f"Open price ({open_price}) is outside high-low range [{low}, {high}]"

        if close > high or close < low:
            return False, f"Close price ({close}) is outside high-low range [{low}, {high}]"

    vol = record.get("volume")
    if vol is not None and vol < 0:
        return False, f"Volume cannot be negative: {vol}"

    price_date = record.get("price_date")
    if not price_date:
        return False, "Missing price_date"

    if isinstance(price_date, date) and price_date > date.today():
        return False, f"Price date {price_date} is in the future"

    return True, None


def verify_listing_freshness(
    db: Session,
    listing_id: Any,
    as_of_date: Optional[date] = None,
    max_stale_days: int = 7,
) -> Tuple[bool, Optional[date], Optional[float], str]:
    """
    Verifies that market prices for a given listing are sufficiently fresh for portfolio generation.
    Returns: (is_fresh, latest_date, latest_close, reason)
    """
    reference_date = as_of_date or date.today()

    latest_price = (
        db.query(MarketPrice)
        .filter(MarketPrice.listing_id == listing_id)
        .order_by(desc(MarketPrice.price_date))
        .first()
    )

    if not latest_price:
        return False, None, None, "No price records exist for this security listing"

    age_days = (reference_date - latest_price.price_date).days
    if age_days < 0:
        # Price is dated after reference date (or current)
        return True, latest_price.price_date, float(latest_price.close_price), "Up to date"

    if age_days > max_stale_days:
        return (
            False,
            latest_price.price_date,
            float(latest_price.close_price),
            f"Price data is stale ({age_days} days old, max allowed is {max_stale_days} days)",
        )

    return True, latest_price.price_date, float(latest_price.close_price), "Fresh"
