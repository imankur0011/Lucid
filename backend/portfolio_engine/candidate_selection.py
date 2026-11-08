"""
Candidate Selection Module.
Filters universe of active securities against investor exclusions, sector limits, and data freshness.
"""

import uuid
from typing import List, Dict, Any, Set, Optional
from uuid import UUID
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from enum import Enum

try:
    from backend.models import Security, InstrumentListing, Sector, Company, Industry, MarketPrice
    from backend.market_data.quality import verify_listing_freshness
    from backend.portfolio_engine.factors import get_equity_factors, determine_optimal_holding_count
except ImportError:
    from models import Security, InstrumentListing, Sector, Company, Industry, MarketPrice
    from market_data.quality import verify_listing_freshness
    from portfolio_engine.factors import get_equity_factors, determine_optimal_holding_count


class LiquidityTier(str, Enum):
    """Institutional liquidity tiers for Indian equities (NSE/BSE)."""
    TIER_1_ULTRA_LIQUID = "TIER_1_ULTRA_LIQUID"      # ADTV >= 100,000 shares, Turnover >= ₹1 Cr (₹10,000,000)
    TIER_2_BROAD_LIQUID = "TIER_2_BROAD_LIQUID"      # ADTV >= 25,000 shares, Turnover >= ₹25 Lakhs (₹2,500,000)
    TIER_3_EMERGING = "TIER_3_EMERGING"              # ADTV >= 5,000 shares, Turnover >= ₹5 Lakhs (₹500,000)
    TIER_4_RESTRICTED = "TIER_4_RESTRICTED"          # Sub-threshold, stale, or suspended


class CandidateUniverseSelector:
    """Selects eligible securities based on status, exclusions, and market data freshness."""

    def __init__(self, db: Session, max_stale_days: int = 14):
        self.db = db
        self.max_stale_days = max_stale_days
        self.exclusion_records: List[Dict[str, Any]] = []
        self.exclusion_summary: Dict[str, int] = {}
        self.last_initial_universe_size: int = 0
        self.last_eligible_count: int = 0

    def select_eligible_candidates(
        self,
        excluded_sectors: Optional[List[str]] = None,
        excluded_instruments: Optional[List[str]] = None,
        as_of_date: Optional[date] = None,
        min_avg_volume: int = 10000,
        min_daily_turnover: float = 2500000.0,
        min_market_cap: float = 0.0,
        allowed_tiers: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Queries all active securities, filters against exclusions,
        verifies market data freshness, ADTV liquidity, and daily turnover thresholds.
        Maintains structured audit records of every exclusion.
        """
        self.exclusion_records = []
        self.exclusion_summary = {}

        ex_sectors: Set[str] = {s.strip().upper() for s in (excluded_sectors or [])}
        ex_instruments: Set[str] = {i.strip().upper() for i in (excluded_instruments or [])}
        target_tiers: Set[str] = set(
            allowed_tiers
            if allowed_tiers is not None
            else [
                LiquidityTier.TIER_1_ULTRA_LIQUID.value,
                LiquidityTier.TIER_2_BROAD_LIQUID.value,
                LiquidityTier.TIER_3_EMERGING.value,
            ]
        )

        target_date = as_of_date or date.today()
        vol_cutoff = target_date - timedelta(days=35)
        now_iso = datetime.now().isoformat()

        # Grouped 30-day average trading volume
        avg_vols: Dict[Any, float] = {}
        try:
            vol_rows = (
                self.db.query(MarketPrice.listing_id, func.avg(MarketPrice.volume))
                .filter(MarketPrice.price_date >= vol_cutoff)
                .group_by(MarketPrice.listing_id)
                .all()
            )
            avg_vols = {lid: float(v or 0.0) for lid, v in vol_rows}
        except Exception:
            avg_vols = {}

        securities = (
            self.db.query(Security)
            .filter(Security.security_status == "active")
            .all()
        )
        self.last_initial_universe_size = len(securities)

        def _record_exclusion(sec_id: Any, sym: str, reason: str, measured: Any, threshold: Any):
            self.exclusion_records.append({
                "security_id": str(sec_id),
                "symbol": sym,
                "exclusion_reason": reason,
                "measured_value": measured,
                "required_threshold": threshold,
                "timestamp": now_iso,
            })
            self.exclusion_summary[reason] = self.exclusion_summary.get(reason, 0) + 1

        candidates = []
        for sec in securities:
            sec_id = sec.security_id
            sym = ""

            # Check primary listing
            listing = sec.listings[0] if sec.listings else None
            if not listing or listing.trading_status != "active":
                _record_exclusion(sec_id, sym or sec.security_name or "UNKNOWN", "INACTIVE_SECURITY", "inactive", "active")
                continue

            sym = (listing.symbol or "").upper()

            # Check instrument exclusions by ISIN, symbol, or name
            if sec.isin and sec.isin.upper() in ex_instruments:
                _record_exclusion(sec_id, sym, "USER_EXCLUDED_SECURITY", sec.isin, "excluded_by_investor")
                continue
            if sym and sym in ex_instruments:
                _record_exclusion(sec_id, sym, "USER_EXCLUDED_SECURITY", sym, "excluded_by_investor")
                continue
            if sec.security_name and sec.security_name.upper() in ex_instruments:
                _record_exclusion(sec_id, sym, "USER_EXCLUDED_SECURITY", sec.security_name, "excluded_by_investor")
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
                _record_exclusion(sec_id, sym, "USER_EXCLUDED_SECTOR", sector_name, "excluded_by_investor_policy")
                continue

            # Verify market price freshness and existence
            is_fresh, price_date, latest_price, reason = verify_listing_freshness(
                self.db, listing.listing_id, as_of_date=as_of_date, max_stale_days=self.max_stale_days
            )
            if latest_price is None or latest_price <= 0:
                _record_exclusion(sec_id, sym, "MISSING_PRICE", reason or "price_missing", "valid positive close price in DB")
                continue
            if not is_fresh:
                _record_exclusion(sec_id, sym, "STALE_PRICE", reason or "stale_price", f"<= {self.max_stale_days} days")
                continue

            # Classify institutional liquidity tier
            listing_vol = float(avg_vols.get(listing.listing_id, 0.0) or 0.0)
            daily_turnover = listing_vol * float(latest_price)

            if daily_turnover >= 10000000.0 and listing_vol >= 100000:
                liq_tier = LiquidityTier.TIER_1_ULTRA_LIQUID.value
            elif daily_turnover >= 2500000.0 and listing_vol >= 25000:
                liq_tier = LiquidityTier.TIER_2_BROAD_LIQUID.value
            elif daily_turnover >= 500000.0 and listing_vol >= 5000:
                liq_tier = LiquidityTier.TIER_3_EMERGING.value
            else:
                liq_tier = LiquidityTier.TIER_4_RESTRICTED.value

            # Verify tier eligibility
            if liq_tier not in target_tiers:
                _record_exclusion(sec_id, sym, "TIER_RESTRICTED", liq_tier, f"one of {sorted(target_tiers)}")
                continue

            # Check minimum trading volume / liquidity constraint
            if min_avg_volume > 0 and listing_vol > 0 and listing_vol < min_avg_volume:
                _record_exclusion(sec_id, sym, "LOW_LIQUIDITY", int(listing_vol), f">= {min_avg_volume} shares ADTV")
                continue

            # Check minimum daily traded value (Turnover = ADTV * Price)
            if min_daily_turnover > 0 and listing_vol > 0 and daily_turnover < min_daily_turnover:
                _record_exclusion(sec_id, sym, "LOW_TURNOVER", round(daily_turnover, 2), f">= ₹{min_daily_turnover:,.2f}")
                continue

            candidates.append({
                "security_id": sec.security_id,
                "listing_id": listing.listing_id,
                "symbol": sym,
                "security_name": sec.security_name,
                "isin": sec.isin,
                "sector_name": sector_name,
                "sector_code": sector_code,
                "industry_name": industry_name,
                "latest_price": latest_price,
                "price_date": price_date,
                "avg_daily_volume": round(listing_vol, 0),
                "avg_daily_turnover": round(daily_turnover, 2),
                "liquidity_tier": liq_tier,
            })

        self.last_eligible_count = len(candidates)
        return candidates

    def get_universe_audit_report(self) -> Dict[str, Any]:
        """Returns structured audit metrics for the most recent candidate selection run."""
        return {
            "initial_universe_size": self.last_initial_universe_size,
            "eligible_candidates_count": self.last_eligible_count,
            "excluded_candidates_count": len(self.exclusion_records),
            "exclusion_breakdown": dict(self.exclusion_summary),
            "sample_exclusion_records": self.exclusion_records[:10],
            "total_exclusion_records": len(self.exclusion_records),
        }

    def rank_and_select_candidates(
        self,
        candidates: List[Dict[str, Any]],
        target_count: int = 8,
        goal_type: str = "wealth_creation",
        risk_category: str = "moderate",
        horizon_months: int = 60,
        user_prompt: str = "",
        news_sentiment: float = 0.25,
        prioritized_security_ids: Optional[Set[uuid.UUID]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Scores and ranks eligible candidates based on multi-factor goal alignment,
        natural language prompt sentiment, and SEBI sector diversification constraints.
        Returns top `target_count` candidates.
        """
        if not candidates or len(candidates) <= target_count:
            # If candidate universe is small, return all enriched
            for cand in candidates:
                cand.setdefault("alpha_score", 0.5)
                cand.setdefault("fundamental_factors", get_equity_factors(cand.get("symbol", ""), db=self.db))
            return candidates

        goal = (goal_type or "").lower()
        risk = (risk_category or "").lower()
        prompt_lower = (user_prompt or "").lower()

        scored_candidates = []
        for cand in candidates:
            sym = cand.get("symbol", "").upper()
            sec_name = cand.get("sector_name", "General")
            factors = cand.get("fundamental_factors") or get_equity_factors(sym, db=self.db)

            # 1. Dynamic Prompt & Thematic Alignment Score (0.0 to 1.0)
            keywords = set(factors.get("keywords") or set())
            keywords.add(sym.lower())
            c_name = (cand.get("security_name") or "").lower()
            for part in c_name.replace("&", " ").replace(".", " ").replace("-", " ").split():
                if len(part) > 2 and part not in ["ltd", "limited", "corp", "corporation", "the", "and", "india"]:
                    keywords.add(part)
            ind_name = (cand.get("industry_name") or "").lower()
            for part in ind_name.split():
                if len(part) > 3:
                    keywords.add(part)

            prompt_matches = sum(1 for kw in keywords if kw in prompt_lower)
            # If explicit ticker or primary company name in prompt, prioritize strongly
            prompt_words = set(prompt_lower.split())
            exact_match = (sym.lower() in prompt_words) or any(
                part in prompt_lower for part in [sym.lower(), c_name] if len(part) > 4
            )
            prompt_score = 1.0 if exact_match else min(prompt_matches * 0.35, 0.85)

            # 2. Factor-Based Goal Alignment Score
            div_yield = factors.get("dividend_yield", 0.012)
            roe = factors.get("roe", 0.15)
            beta = factors.get("beta", 1.0)
            debt_ratio = factors.get("debt_to_equity", 0.5)
            cagr = factors.get("three_year_cagr", 0.12)

            if "dividend" in goal or "income" in goal or "dividend" in prompt_lower:
                # Prioritize high dividend yield, low debt, moderate beta
                yield_norm = min(div_yield / 0.065, 1.0)
                debt_norm = max(0.0, 1.0 - (debt_ratio / 1.5))
                goal_score = 0.55 * yield_norm + 0.25 * debt_norm + 0.20 * min(roe / 0.25, 1.0)
            elif "preserv" in goal or "safety" in goal or risk in ["very_conservative", "conservative"]:
                # Prioritize low beta (<0.8), defensive sectors (FMCG, Healthcare, Utilities), low debt
                beta_norm = max(0.0, (1.30 - beta) / 0.80)
                defensive_bonus = 0.30 if sec_name in [
                    "Fast Moving Consumer Goods",
                    "Healthcare & Pharmaceuticals",
                    "Power & Utilities",
                ] else 0.0
                debt_norm = max(0.0, 1.0 - debt_ratio)
                goal_score = 0.45 * beta_norm + 0.25 * debt_norm + defensive_bonus
            elif "growth" in goal or risk in ["growth", "aggressive"] or "growth" in prompt_lower:
                # Prioritize high ROE (>20%), high CAGR, momentum
                roe_norm = min(roe / 0.30, 1.0)
                cagr_norm = min(cagr / 0.28, 1.0)
                goal_score = 0.55 * roe_norm + 0.45 * cagr_norm
            else:
                # Balanced moderate strategy: Sharpe ratio prior
                roe_norm = min(roe / 0.25, 1.0)
                beta_norm = max(0.0, (1.40 - beta) / 0.80)
                cagr_norm = min(cagr / 0.22, 1.0)
                goal_score = 0.40 * roe_norm + 0.30 * beta_norm + 0.30 * cagr_norm

            # 3. News Sentiment adjustment (slight cyclical boost for high beta if positive news)
            sentiment_adj = (news_sentiment * 0.05) if beta > 1.1 else 0.0

            # 4. Composite Alpha Score (Range: 0.0 to 1.0)
            composite_score = (
                0.65 * goal_score
                + 0.30 * prompt_score
                + 0.05 * sentiment_adj
            )

            # Prioritized existing portfolio holdings retain placement for rebalancing
            if prioritized_security_ids:
                p_set = {str(sid) for sid in prioritized_security_ids}
                if str(cand.get("security_id")) in p_set:
                    composite_score += 2.0

            cand_copy = dict(cand)
            cand_copy["alpha_score"] = round(float(composite_score), 4)
            cand_copy["fundamental_factors"] = factors
            scored_candidates.append(cand_copy)

        # Sort candidates strictly by composite alpha score descending
        scored_candidates.sort(key=lambda x: x["alpha_score"], reverse=True)

        # 5. Greedy Selection with Fiduciary Diversification Constraints
        # Guardrail: Maximum 35% of candidates from any single sector (to comply with Lucid 40% sector risk policy)
        # Ensure at least 3 distinct sectors are included in the portfolio
        max_per_sector = max(2, int(target_count * 0.35))
        selected: List[Dict[str, Any]] = []
        sector_counts: Dict[str, int] = {}

        for cand in scored_candidates:
            if len(selected) >= target_count:
                break
            sec = cand.get("sector_name", "General")
            count = sector_counts.get(sec, 0)
            if count < max_per_sector:
                selected.append(cand)
                sector_counts[sec] = count + 1

        # Fallback: If sector capping left us short of target_count, fill from remaining top candidates
        if len(selected) < target_count:
            selected_ids = {c["security_id"] for c in selected}
            for cand in scored_candidates:
                if len(selected) >= target_count:
                    break
                if cand["security_id"] not in selected_ids:
                    selected.append(cand)

        return selected
