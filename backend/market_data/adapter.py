"""
Market Data Provider Adapter Interface and Implementations.
Supports Yahoo Finance (yfinance) and deterministic simulated/demo data providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import pandas as pd


class MarketDataProvider(ABC):
    """Abstract interface decoupling provider APIs from application ingestion."""

    @abstractmethod
    def fetch_historical_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch daily historical price bars between start_date and end_date."""
        pass

    @abstractmethod
    def fetch_latest_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch latest market quote for an instrument."""
        pass


class YFinanceProvider(MarketDataProvider):
    """Implementation using yfinance for Indian equities (NSE .NS suffix)."""

    def _normalize_symbol(self, symbol: str) -> str:
        clean = symbol.strip().upper()
        if not clean.endswith(".NS") and not clean.endswith(".BO"):
            return f"{clean}.NS"
        return clean

    def fetch_historical_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        import yfinance as yf

        ticker_sym = self._normalize_symbol(symbol)
        ticker = yf.Ticker(ticker_sym)
        df = ticker.history(
            start=start_date.isoformat(),
            end=(end_date + timedelta(days=1)).isoformat(),
            interval="1d",
            auto_adjust=False,
        )

        records = []
        if df.empty:
            return records

        for idx, row in df.iterrows():
            price_date = idx.date() if hasattr(idx, "date") else idx
            records.append({
                "symbol": symbol,
                "price_date": price_date,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "adj_close": float(row.get("Adj Close", row["Close"])),
                "volume": int(row.get("Volume", 0)),
                "currency": "INR",
            })
        return records

    def fetch_latest_quote(self, symbol: str) -> Dict[str, Any]:
        import yfinance as yf

        ticker_sym = self._normalize_symbol(symbol)
        ticker = yf.Ticker(ticker_sym)
        info = ticker.fast_info
        return {
            "symbol": symbol,
            "price_date": date.today(),
            "close": float(getattr(info, "last_price", 0.0)),
            "open": float(getattr(info, "open", 0.0) or getattr(info, "last_price", 0.0)),
            "high": float(getattr(info, "day_high", 0.0) or getattr(info, "last_price", 0.0)),
            "low": float(getattr(info, "day_low", 0.0) or getattr(info, "last_price", 0.0)),
            "volume": int(getattr(info, "last_volume", 0) or 0),
            "currency": "INR",
        }


class SimulatedMarketProvider(MarketDataProvider):
    """
    Deterministic provider generating realistic market prices for testing and offline execution.
    Avoids live external dependencies during automated CI runs.
    """

    DEFAULT_BASE_PRICES = {
        "DEMO-CONS": 105.0,
        "DEMO-TECH": 210.0,
        "DEMO-HEALTH": 150.0,
        "RELIANCE": 2850.0,
        "TCS": 3950.0,
        "INFY": 1820.0,
        "HDFCBANK": 1680.0,
        "ICICIBANK": 1240.0,
        "TATAMOTORS": 940.0,
    }

    def fetch_historical_prices(
        self, symbol: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        base_price = self.DEFAULT_BASE_PRICES.get(symbol.upper(), 100.0)
        curr = start_date
        records = []
        day_offset = 0

        while curr <= end_date:
            # Skip weekends (5: Saturday, 6: Sunday)
            if curr.weekday() < 5:
                # Deterministic pseudo-random variation based on date and symbol
                seed_val = (hash(symbol) + curr.toordinal()) % 1000
                delta_pct = (seed_val - 500) / 10000.0  # -5% to +5%
                daily_close = round(base_price * (1.0 + delta_pct + (day_offset * 0.0005)), 2)
                daily_high = round(daily_close * 1.015, 2)
                daily_low = round(daily_close * 0.985, 2)
                daily_open = round((daily_high + daily_low) / 2.0, 2)
                volume = 10000 + (seed_val * 25)

                records.append({
                    "symbol": symbol,
                    "price_date": curr,
                    "open": daily_open,
                    "high": daily_high,
                    "low": daily_low,
                    "close": daily_close,
                    "adj_close": daily_close,
                    "volume": volume,
                    "currency": "INR",
                })
            curr += timedelta(days=1)
            day_offset += 1

        return records

    def fetch_latest_quote(self, symbol: str) -> Dict[str, Any]:
        base_price = self.DEFAULT_BASE_PRICES.get(symbol.upper(), 100.0)
        return {
            "symbol": symbol,
            "price_date": date.today(),
            "open": base_price * 0.995,
            "high": base_price * 1.015,
            "low": base_price * 0.99,
            "close": base_price,
            "adj_close": base_price,
            "volume": 25000,
            "currency": "INR",
        }
