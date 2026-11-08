"""
Market Data Provider Adapter Interface and Implementations.
Supports Yahoo Finance (yfinance) and deterministic simulated/demo data providers.
"""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta, timezone, time as dt_time
import pandas as pd


class MarketDataProvider(ABC):
    """Abstract interface decoupling provider APIs from application ingestion."""

    provider_name: str = "base"
    is_simulated: bool = False

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

    @abstractmethod
    def fetch_fundamental_metrics(self, symbol: str) -> Dict[str, Any]:
        """Fetch fundamental metrics (ROE, P/E, P/B, D/E, dividend yield, market cap, beta)."""
        pass

    def check_health(self) -> Dict[str, Any]:
        """Validates provider connectivity, latency, and sample quote retrieval."""
        return {
            "status": "HEALTHY",
            "provider": self.provider_name,
            "is_simulated": self.is_simulated,
            "latency_ms": 0.0,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def is_stale(quote: Dict[str, Any], max_age_minutes: int = 15) -> bool:
        """Determines if a market quote observation is stale or unverified."""
        if not quote or quote.get("close", 0.0) <= 0.0:
            return True
        if quote.get("is_stale", False):
            return True
        freshness = quote.get("data_freshness", "")
        if freshness == "STALE":
            return True
        return False


class YFinanceProvider(MarketDataProvider):
    """Implementation using yfinance for Indian equities (NSE .NS suffix)."""

    provider_name: str = "yfinance"
    is_simulated: bool = False

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
        last_price = float(getattr(info, "last_price", 0.0) or 0.0)

        now_utc = datetime.now(timezone.utc)
        ist_now = now_utc + timedelta(hours=5, minutes=30)
        is_weekday = ist_now.weekday() < 5
        is_market_hours = is_weekday and (dt_time(9, 15) <= ist_now.time() <= dt_time(15, 30))

        if last_price <= 0.0:
            freshness = "STALE"
            is_stale = True
        elif is_market_hours:
            freshness = "LIVE"
            is_stale = False
        else:
            freshness = "END_OF_DAY"
            is_stale = False

        return {
            "symbol": symbol,
            "price_date": date.today(),
            "close": last_price,
            "open": float(getattr(info, "open", 0.0) or last_price),
            "high": float(getattr(info, "day_high", 0.0) or last_price),
            "low": float(getattr(info, "day_low", 0.0) or last_price),
            "volume": int(getattr(info, "last_volume", 0) or 0),
            "currency": "INR",
            "provider": self.provider_name,
            "data_freshness": freshness,
            "is_stale": is_stale,
            "retrieval_timestamp": now_utc.isoformat(),
            "market_timestamp": now_utc.isoformat(),
        }

    def check_health(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            sample = self.fetch_latest_quote("RELIANCE")
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            valid = sample.get("close", 0.0) > 0
            return {
                "status": "HEALTHY" if valid else "DEGRADED",
                "provider": self.provider_name,
                "is_simulated": self.is_simulated,
                "latency_ms": latency_ms,
                "sample_symbol": "RELIANCE",
                "sample_price": sample.get("close"),
                "freshness": sample.get("data_freshness", "UNKNOWN"),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as exc:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "OFFLINE",
                "provider": self.provider_name,
                "is_simulated": self.is_simulated,
                "latency_ms": latency_ms,
                "error": str(exc),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }


    def fetch_fundamental_metrics(self, symbol: str) -> Dict[str, Any]:
        import yfinance as yf

        ticker_sym = self._normalize_symbol(symbol)
        ticker = yf.Ticker(ticker_sym)
        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        # Dividend yield: normalize percentage (e.g., 0.85 -> 0.0085 or 0.015 -> 0.015)
        div_yield_raw = info.get("dividendYield")
        div_yield = 0.012
        if div_yield_raw is not None:
            try:
                dy = float(div_yield_raw)
                div_yield = dy / 100.0 if dy > 0.5 else dy
            except (ValueError, TypeError):
                div_yield = 0.012

        # Return on Equity
        roe_raw = info.get("returnOnEquity")
        roe = 0.16
        if roe_raw is not None:
            try:
                roe = float(roe_raw)
            except (ValueError, TypeError):
                roe = 0.16

        # P/E ratio
        pe_raw = info.get("trailingPE") or info.get("forwardPE")
        pe = 22.0
        if pe_raw is not None:
            try:
                pe = max(1.0, float(pe_raw))
            except (ValueError, TypeError):
                pe = 22.0

        # P/B ratio
        pb_raw = info.get("priceToBook")
        pb = 3.5
        if pb_raw is not None:
            try:
                pb = max(0.5, float(pb_raw))
            except (ValueError, TypeError):
                pb = 3.5

        # Debt to Equity (yfinance returns e.g. 32.4 for 0.324 or 0.16)
        de_raw = info.get("debtToEquity")
        debt_to_equity = 0.40
        if de_raw is not None:
            try:
                de = float(de_raw)
                debt_to_equity = de / 100.0 if de > 5.0 else de
            except (ValueError, TypeError):
                debt_to_equity = 0.40

        # Beta vs benchmark
        beta_raw = info.get("beta")
        beta = 1.0
        if beta_raw is not None:
            try:
                beta = max(0.2, min(float(beta_raw), 3.0))
            except (ValueError, TypeError):
                beta = 1.0

        # Market Cap
        market_cap = float(info.get("marketCap") or 50000000000.0)

        # Profit Margins
        profit_margins = float(info.get("profitMargins") or 0.12)

        # Revenue Growth
        revenue_growth = float(info.get("revenueGrowth") or 0.10)

        sector = info.get("sector") or "General"
        industry = info.get("industry") or "Diversified"

        # Three year CAGR estimation
        cagr = round(max(0.04, min(0.35, (roe * 0.6) + (revenue_growth * 0.4))), 4)

        return {
            "symbol": symbol.strip().upper(),
            "roe": round(roe, 4),
            "pe": round(pe, 2),
            "pb": round(pb, 2),
            "debt_to_equity": round(debt_to_equity, 4),
            "dividend_yield": round(div_yield, 4),
            "beta": round(beta, 2),
            "market_cap": market_cap,
            "profit_margins": round(profit_margins, 4),
            "revenue_growth": round(revenue_growth, 4),
            "three_year_cagr": cagr,
            "sector": sector,
            "industry": industry,
            "retrieved_at": datetime.now().isoformat(),
        }


class SimulatedMarketProvider(MarketDataProvider):
    """
    Deterministic provider generating realistic market prices for testing and offline execution.
    Avoids live external dependencies during automated CI runs.
    """

    provider_name: str = "simulated"
    is_simulated: bool = True

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
        now_utc = datetime.now(timezone.utc)
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
            "provider": self.provider_name,
            "data_freshness": "SIMULATED",
            "is_stale": False,
            "retrieval_timestamp": now_utc.isoformat(),
            "market_timestamp": now_utc.isoformat(),
        }

    def check_health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.provider_name,
            "is_simulated": self.is_simulated,
            "latency_ms": 0.5,
            "sample_symbol": "RELIANCE",
            "sample_price": self.DEFAULT_BASE_PRICES.get("RELIANCE", 2850.0),
            "freshness": "SIMULATED",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

    def fetch_fundamental_metrics(self, symbol: str) -> Dict[str, Any]:
        """Deterministic fundamental metrics generation for testing and offline environments."""
        sym = symbol.strip().upper()
        h = abs(hash(sym))
        # Realistic ranges derived deterministically from symbol hash
        roe = round(0.10 + ((h % 22) / 100.0), 4)  # 10% to 31%
        pe = round(14.0 + (h % 35) + ((h % 10) / 10.0), 2)  # 14 to 49
        pb = round(1.5 + ((h % 70) / 10.0), 2)  # 1.5 to 8.5
        debt_to_equity = round(((h % 60) / 100.0), 4)  # 0.0 to 0.60
        div_yield = round(0.005 + ((h % 25) / 1000.0), 4)  # 0.5% to 3.0%
        beta = round(0.65 + ((h % 75) / 100.0), 2)  # 0.65 to 1.40
        market_cap = float((50000 + (h % 500000)) * 10000000.0)  # ₹5,000 Cr to ₹55,000 Cr
        profit_margins = round(0.08 + ((h % 16) / 100.0), 4)  # 8% to 24%
        revenue_growth = round(0.08 + ((h % 20) / 100.0), 4)  # 8% to 28%
        cagr = round((roe * 0.5) + (revenue_growth * 0.5), 4)

        return {
            "symbol": sym,
            "roe": roe,
            "pe": pe,
            "pb": pb,
            "debt_to_equity": debt_to_equity,
            "dividend_yield": div_yield,
            "beta": beta,
            "market_cap": market_cap,
            "profit_margins": profit_margins,
            "revenue_growth": revenue_growth,
            "three_year_cagr": cagr,
            "sector": "General",
            "industry": "Diversified",
            "retrieved_at": datetime.now().isoformat(),
        }


def get_market_data_provider(
    provider_name: Optional[str] = None,
    allow_simulated: bool = False,
) -> MarketDataProvider:
    """
    Factory resolving active market data provider.
    Fiduciary guardrail: Prevents accidental use of SimulatedMarketProvider in production.
    """
    try:
        from backend.config import settings
        env = getattr(settings, "app_env", "development").lower()
    except Exception:
        env = "development"

    req_name = (provider_name or "").lower().strip()
    if req_name == "simulated" or (not req_name and allow_simulated and env != "production"):
        if env == "production" and not allow_simulated:
            raise RuntimeError(
                "Fiduciary Guardrail Breach: SimulatedMarketProvider is strictly prohibited in production mode. "
                "Must use live exchange data provider (YFinanceProvider or authorized market feed)."
            )
        return SimulatedMarketProvider()

    # Default provider is live YFinance
    return YFinanceProvider()
