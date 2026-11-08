"""
Dynamic NSE/BSE Company and Security Resolution Service for Lucid.

Replaces static stock dictionaries with a database-backed, indexed security master
supporting:
- Exact symbol and ISIN matching
- Exact and normalized company name matching
- Popular market aliases and abbreviations (L&T, SBI, Infy, M&M, etc.)
- Levenshtein-based fuzzy matching for spelling mistakes and typos
- Disambiguation of umbrella group names (Tata, HDFC, Reliance, Adani, ICICI)
- Extraction and resolution of multiple company mentions from unstructured natural language
"""

import re
import difflib
import logging
from enum import Enum
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

from backend.database.session import SessionLocal
from backend.models.security import Security, InstrumentListing, Company, Exchange, Sector
from backend.services.exchange_registry import VERIFIED_STOCKS, clean_equity_symbol, resolve_stock_filings

logger = logging.getLogger(__name__)


class MatchType(str, Enum):
    EXACT_SYMBOL = "EXACT_SYMBOL"
    EXACT_ISIN = "EXACT_ISIN"
    EXACT_NAME = "EXACT_NAME"
    NORMALIZED_NAME = "NORMALIZED_NAME"
    ALIAS = "ALIAS"
    FUZZY_NAME = "FUZZY_NAME"
    PARTIAL_NAME = "PARTIAL_NAME"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


class CandidateMatch(BaseModel):
    symbol: str
    company_name: str
    exchange: str = "NSE"
    bse_code: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    score: float = 1.0


class CompanyResolutionResult(BaseModel):
    query: str
    matched_symbol: Optional[str] = None
    company_name: Optional[str] = None
    exchange: str = "NSE"
    bse_code: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    confidence: float = 0.0
    match_type: MatchType = MatchType.UNRESOLVED
    is_ambiguous: bool = False
    candidate_matches: List[CandidateMatch] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None


class ResolvedCompanyEntity(BaseModel):
    raw_mention: str
    resolved_symbol: Optional[str] = None
    company_name: Optional[str] = None
    exchange: str = "NSE"
    bse_code: Optional[str] = None
    isin: Optional[str] = None
    sector: Optional[str] = None
    confidence: float = 0.0
    match_type: MatchType = MatchType.UNRESOLVED
    is_ambiguous: bool = False
    candidate_matches: List[CandidateMatch] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None


# Known umbrella conglomerate names that are ambiguous unless specified
AMBIGUOUS_UMBRELLA_GROUPS: Dict[str, List[str]] = {
    "tata": ["TATAMOTORS", "TCS", "TATASTEEL", "TATAPOWER", "TATACONSUM", "TITAN", "TRENT"],
    "hdfc": ["HDFCBANK", "HDFCLIFE"],
    "reliance": ["RELIANCE"], # In Nifty 500 Reliance Industries is primary, but Reliance Power / Infrastructure exist
    "adani": ["ADANIGREEN", "ADANIPORTS"],
    "icici": ["ICICIBANK"],
    "bajaj": ["BAJFINANCE", "BAJAJFINSV", "BAJAJ-AUTO"],
    "birla": ["HINDALCO", "ULTRACEMCO"],
}

# Common market aliases that map directly and unambiguously to specific equities
WELL_KNOWN_ALIASES: Dict[str, str] = {
    "l&t": "LT",
    "larsen": "LT",
    "larsen & toubro": "LT",
    "larsen and toubro": "LT",
    "sbi": "SBIN",
    "state bank": "SBIN",
    "state bank of india": "SBIN",
    "infy": "INFY",
    "infosys": "INFY",
    "m&m": "MNM",
    "mahindra": "MNM",
    "mahindra & mahindra": "MNM",
    "mahindra and mahindra": "MNM",
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "bajaj finance": "BAJFINANCE",
    "bajfinance": "BAJFINANCE",
    "bajaj finserv": "BAJAJFINSV",
    "bajaj auto": "BAJAJ-AUTO",
    "dmart": "DMART",
    "avenue supermarts": "DMART",
    "paytm": "PAYTM",
    "one97": "PAYTM",
    "one 97": "PAYTM",
    "bhel": "BHEL",
    "hal": "HAL",
    "bel": "BEL",
    "hindustan aeronautics": "HAL",
    "bharat electronics": "BEL",
    "zomato": "ZOMATO",
    "blinkit": "ZOMATO",
    "divis": "DIVISLAB",
    "divi's": "DIVISLAB",
    "divis lab": "DIVISLAB",
    "divi's lab": "DIVISLAB",
    "divis laboratories": "DIVISLAB",
    "sun pharma": "SUNPHARMA",
    "sun pharmaceuticals": "SUNPHARMA",
    "dr reddy": "DRREDDY",
    "dr reddy's": "DRREDDY",
    "dr reddys": "DRREDDY",
    "asian paints": "ASIANPAINT",
    "titan": "TITAN",
    "airtel": "BHARTIARTL",
    "bharti airtel": "BHARTIARTL",
    "jio": "RELIANCE",
    "reliance industries": "RELIANCE",
    "power grid": "POWERGRID",
    "powergrid": "POWERGRID",
    "coal india": "COALINDIA",
    "tata motors": "TATAMOTORS",
    "tata steel": "TATASTEEL",
    "tata power": "TATAPOWER",
    "tata consumer": "TATACONSUM",
    "tata consultancy": "TCS",
    "wipro": "WIPRO",
    "hcl": "HCLTECH",
    "hcl tech": "HCLTECH",
    "hcl technologies": "HCLTECH",
    "itc": "ITC",
    "kotak": "KOTAKBANK",
    "kotak bank": "KOTAKBANK",
    "kotak mahindra": "KOTAKBANK",
    "axis": "AXISBANK",
    "axis bank": "AXISBANK",
    "indusind": "INDUSINDBK",
    "indusind bank": "INDUSINDBK",
    "yes bank": "YESBANK",
    "suzlon": "SUZLON",
    "idea": "IDEA",
    "vodafone idea": "IDEA",
    "vi": "IDEA",
    "nestle": "NESTLEIND",
    "nestle india": "NESTLEIND",
}


def normalize_company_name(name: str) -> str:
    """
    Cleans company name for fuzzy and exact matching by stripping corporate suffixes,
    legal entity descriptors, and punctuation.
    """
    if not name:
        return ""
    clean = name.lower()
    # Strip common corporate suffixes
    clean = re.sub(
        r'\b(?:limited|ltd|corporation|corp|incorporated|inc|enterprises|industries|holdings|company|co|equity|ltd\.)\b',
        '',
        clean,
    )
    clean = re.sub(r'\(india\)', '', clean)
    clean = re.sub(r'[\(\)\[\]\{\}\-\.,/\\&]', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean


class SecurityMasterRepository:
    """
    In-memory indexed security master loaded from database and exchange registry.
    Thread-safe, sub-millisecond lookup across 500+ NSE/BSE securities.
    """

    def __init__(self):
        self._by_symbol: Dict[str, Dict[str, Any]] = {}
        self._by_isin: Dict[str, str] = {}
        self._by_normalized_name: Dict[str, str] = {}
        self._all_normalized_names: List[Tuple[str, str]] = [] # (normalized_name, symbol)
        self._is_initialized = False

    def ensure_initialized(self):
        if self._is_initialized:
            return
        self.refresh_index()

    def refresh_index(self):
        """Loads all active securities from PostgreSQL and builds search indexes."""
        logger.info("Initializing SecurityMasterRepository from database...")
        db = SessionLocal()
        try:
            records = (
                db.query(
                    InstrumentListing.symbol,
                    Security.security_name,
                    Security.isin,
                    Company.legal_name,
                    Company.common_name,
                    Exchange.exchange_code,
                )
                .join(Security, InstrumentListing.security_id == Security.security_id)
                .outerjoin(Company, Security.company_id == Company.company_id)
                .join(Exchange, InstrumentListing.exchange_id == Exchange.exchange_id)
                .filter(InstrumentListing.trading_status == "active")
                .all()
            )

            by_sym: Dict[str, Dict[str, Any]] = {}
            by_isin: Dict[str, str] = {}
            by_norm: Dict[str, str] = {}
            all_norm: List[Tuple[str, str]] = []

            for r in records:
                sym = r.symbol.upper()
                c_name = r.common_name or r.legal_name or r.security_name or sym
                if c_name.endswith(" Equity"):
                    c_name = c_name[:-7].strip()

                # Get verified BSE scrip from exchange registry if available
                v_entry = VERIFIED_STOCKS.get(sym, {})
                bse_code = v_entry.get("bse_code")

                data = {
                    "symbol": sym,
                    "company_name": c_name,
                    "legal_name": r.legal_name or c_name,
                    "isin": r.isin,
                    "exchange": r.exchange_code or "NSE",
                    "bse_code": bse_code,
                    "sector": "Indian Equities",
                }
                by_sym[sym] = data
                if r.isin:
                    isin_key = r.isin.upper()
                    # Prefer alphabetic NSE symbol over numeric BSE scrip code
                    if isin_key not in by_isin or (by_isin[isin_key].isdigit() and not sym.isdigit()):
                        by_isin[isin_key] = sym

                # Add normalized variations (prefer alphabetic NSE ticker over numeric BSE scrip code)
                for n in [c_name, r.legal_name, r.security_name]:
                    if n:
                        norm = normalize_company_name(n)
                        if norm and len(norm) >= 3:
                            if norm not in by_norm or (by_norm[norm].isdigit() and not sym.isdigit()):
                                by_norm[norm] = sym
                            all_norm.append((norm, sym))

            # Also enrich with VERIFIED_STOCKS to ensure full metadata coverage
            for sym, v in VERIFIED_STOCKS.items():
                if sym not in by_sym:
                    by_sym[sym] = {
                        "symbol": sym,
                        "company_name": v.get("name", f"{sym} Ltd."),
                        "legal_name": v.get("name", f"{sym} Ltd."),
                        "isin": None,
                        "exchange": "NSE",
                        "bse_code": v.get("bse_code"),
                        "sector": "Indian Equities",
                    }
                else:
                    if not by_sym[sym].get("bse_code"):
                        by_sym[sym]["bse_code"] = v.get("bse_code")

                norm_v = normalize_company_name(v.get("name", ""))
                if norm_v and len(norm_v) >= 3:
                    by_norm[norm_v] = sym
                    all_norm.append((norm_v, sym))

            self._by_symbol = by_sym
            self._by_isin = by_isin
            self._by_normalized_name = by_norm
            self._all_normalized_names = all_norm
            self._is_initialized = True
            logger.info(f"SecurityMasterRepository initialized with {len(by_sym)} securities.")

        except Exception as e:
            logger.error(f"Error initializing SecurityMasterRepository: {e}", exc_info=True)
            # Fallback to VERIFIED_STOCKS in case DB connection is transiently unreachable
            for sym, v in VERIFIED_STOCKS.items():
                self._by_symbol[sym] = {
                    "symbol": sym,
                    "company_name": v.get("name", f"{sym} Ltd."),
                    "legal_name": v.get("name", f"{sym} Ltd."),
                    "isin": None,
                    "exchange": "NSE",
                    "bse_code": v.get("bse_code"),
                    "sector": "Indian Equities",
                }
            self._is_initialized = True
        finally:
            db.close()

    def get_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        self.ensure_initialized()
        return self._by_symbol.get(symbol.upper())

    def get_by_isin(self, isin: str) -> Optional[Dict[str, Any]]:
        self.ensure_initialized()
        sym = self._by_isin.get(isin.upper())
        return self._by_symbol.get(sym) if sym else None

    def search_candidates(self, query: str, limit: int = 5) -> List[CandidateMatch]:
        """Performs token and substring search across all indexed securities."""
        self.ensure_initialized()
        clean_q = query.strip().upper()
        norm_q = normalize_company_name(query)
        matches: List[CandidateMatch] = []
        seen_syms: Set[str] = set()

        # 1. Exact symbol match
        if clean_q in self._by_symbol:
            d = self._by_symbol[clean_q]
            matches.append(CandidateMatch(**d, score=1.0))
            seen_syms.add(clean_q)

        # 2. Exact normalized match
        if norm_q in self._by_normalized_name:
            sym = self._by_normalized_name[norm_q]
            if sym not in seen_syms:
                d = self._by_symbol[sym]
                matches.append(CandidateMatch(**d, score=0.98))
                seen_syms.add(sym)

        # 3. Substring / Token matches
        for norm_name, sym in self._all_normalized_names:
            if sym in seen_syms:
                continue
            if norm_q in norm_name or norm_name in norm_q:
                d = self._by_symbol[sym]
                matches.append(CandidateMatch(**d, score=0.85))
                seen_syms.add(sym)
                if len(matches) >= limit:
                    break

        return matches[:limit]


# Global security master repository singleton
security_master_repo = SecurityMasterRepository()


# ---------------------------------------------------------------------------
# Company Resolution Service
# ---------------------------------------------------------------------------

class CompanyResolutionService:
    """
    High-level entity resolution engine for resolving user strings, company aliases,
    and natural-language mentions into validated security identifiers.
    """

    def __init__(self, repo: SecurityMasterRepository = security_master_repo):
        self.repo = repo

    def resolve_company(self, query: str, fuzzy_threshold: float = 0.75) -> CompanyResolutionResult:
        """
        Dynamically resolves a single company query into a validated security identity.
        Handles exact symbols, ISINs, aliases, umbrella group ambiguities, and fuzzy typos.
        """
        raw_q = query.strip()
        if not raw_q:
            return CompanyResolutionResult(query=query, match_type=MatchType.UNRESOLVED)

        clean_sym = clean_equity_symbol(raw_q)
        lower_q = raw_q.lower()
        norm_q = normalize_company_name(raw_q)

        # 1. Exact Symbol Match
        sym_match = self.repo.get_by_symbol(clean_sym)
        if sym_match:
            return CompanyResolutionResult(
                query=query,
                matched_symbol=sym_match["symbol"],
                company_name=sym_match["company_name"],
                exchange=sym_match["exchange"],
                bse_code=sym_match.get("bse_code"),
                isin=sym_match.get("isin"),
                sector=sym_match.get("sector"),
                confidence=1.0,
                match_type=MatchType.EXACT_SYMBOL,
            )

        # 2. ISIN Match
        if re.match(r'^[A-Z]{2}[A-Z0-9]{9}[0-9]$', clean_sym):
            isin_match = self.repo.get_by_isin(clean_sym)
            if isin_match:
                return CompanyResolutionResult(
                    query=query,
                    matched_symbol=isin_match["symbol"],
                    company_name=isin_match["company_name"],
                    exchange=isin_match["exchange"],
                    bse_code=isin_match.get("bse_code"),
                    isin=isin_match.get("isin"),
                    sector=isin_match.get("sector"),
                    confidence=1.0,
                    match_type=MatchType.EXACT_ISIN,
                )

        # 3. Well-Known Direct Aliases (e.g. "l&t" -> "LT", "sbi" -> "SBIN", "infy" -> "INFY")
        if lower_q in WELL_KNOWN_ALIASES:
            target_sym = WELL_KNOWN_ALIASES[lower_q]
            sec_data = self.repo.get_by_symbol(target_sym)
            if sec_data:
                return CompanyResolutionResult(
                    query=query,
                    matched_symbol=sec_data["symbol"],
                    company_name=sec_data["company_name"],
                    exchange=sec_data["exchange"],
                    bse_code=sec_data.get("bse_code"),
                    isin=sec_data.get("isin"),
                    sector=sec_data.get("sector"),
                    confidence=0.99,
                    match_type=MatchType.ALIAS,
                )

        # 4. Check for Ambiguous Umbrella Groups (e.g. "tata", "hdfc", "adani", "bajaj")
        if lower_q in AMBIGUOUS_UMBRELLA_GROUPS:
            candidate_syms = AMBIGUOUS_UMBRELLA_GROUPS[lower_q]
            candidates = []
            for cs in candidate_syms:
                d = self.repo.get_by_symbol(cs)
                if d:
                    candidates.append(CandidateMatch(**d, score=0.90))

            prompt = (
                f"Multiple companies match '{query}'. Did you mean "
                + ", ".join([f"{c.company_name} ({c.symbol})" for c in candidates[:4]])
                + "?"
            )
            return CompanyResolutionResult(
                query=query,
                is_ambiguous=True,
                match_type=MatchType.AMBIGUOUS,
                candidate_matches=candidates,
                clarification_prompt=prompt,
                confidence=0.5,
            )

        # 5. Exact Normalized Name Match
        candidates = self.repo.search_candidates(raw_q, limit=5)
        if candidates and candidates[0].score >= 0.95:
            top = candidates[0]
            return CompanyResolutionResult(
                query=query,
                matched_symbol=top.symbol,
                company_name=top.company_name,
                exchange=top.exchange,
                bse_code=top.bse_code,
                isin=top.isin,
                sector=top.sector,
                confidence=top.score,
                match_type=MatchType.NORMALIZED_NAME,
            )

        # 6. Fuzzy Match: whole-phrase and token-level SequenceMatcher
        all_norm_names = self.repo._all_normalized_names
        best_ratio = 0.0
        best_sym = None
        for n_name, s in all_norm_names:
            ratio_full = difflib.SequenceMatcher(None, norm_q, n_name).ratio()
            token_ratios = [difflib.SequenceMatcher(None, norm_q, w).ratio() for w in n_name.split() if len(w) >= 3]
            max_tok = max(token_ratios) if token_ratios else 0.0
            effective = max(ratio_full, max_tok)
            if effective > best_ratio:
                best_ratio = effective
                best_sym = s

        if best_ratio >= fuzzy_threshold and best_sym:
            d = self.repo.get_by_symbol(best_sym)
            if d:
                return CompanyResolutionResult(
                    query=query,
                    matched_symbol=d["symbol"],
                    company_name=d["company_name"],
                    exchange=d["exchange"],
                    bse_code=d.get("bse_code"),
                    isin=d.get("isin"),
                    sector=d.get("sector"),
                    confidence=round(best_ratio, 2),
                    match_type=MatchType.FUZZY_NAME,
                )

        # 7. Multiple Partial Candidates (Ambiguity Check)
        if len(candidates) > 1:
            prompt = (
                f"Found {len(candidates)} potential matches for '{query}': "
                + ", ".join([f"{c.company_name} ({c.symbol})" for c in candidates[:3]])
                + ". Please select one."
            )
            return CompanyResolutionResult(
                query=query,
                is_ambiguous=True,
                match_type=MatchType.AMBIGUOUS,
                candidate_matches=candidates,
                clarification_prompt=prompt,
                confidence=0.6,
            )
        elif len(candidates) == 1:
            top = candidates[0]
            return CompanyResolutionResult(
                query=query,
                matched_symbol=top.symbol,
                company_name=top.company_name,
                exchange=top.exchange,
                bse_code=top.bse_code,
                isin=top.isin,
                sector=top.sector,
                confidence=0.85,
                match_type=MatchType.PARTIAL_NAME,
            )

        # Unresolved
        return CompanyResolutionResult(
            query=query,
            match_type=MatchType.UNRESOLVED,
            confidence=0.0,
            clarification_prompt=f"Could not identify an NSE/BSE security matching '{query}'. Please verify the company name or symbol.",
        )

    def extract_and_resolve_companies_from_text(self, text: str) -> List[ResolvedCompanyEntity]:
        """
        Scans freeform natural language for company and ticker mentions,
        extracts candidate spans, and resolves each entity dynamically.
        """
        self.repo.ensure_initialized()
        clean = text.strip()
        if not clean:
            return []

        resolved_entities: List[ResolvedCompanyEntity] = []
        seen_symbols: Set[str] = set()

        # Phrases indicating security preferences or existing holdings
        triggers = [
            r'(?:include|invest in|exposure to|buy|holding|already own|already have|currently hold|portfolio of|stocks? in|shares? of)\s+([^.]+)',
            r'(?:analyse|analyze|evaluate|check|look at)\s+([^.]+)',
        ]

        # 1. Check full text against all indexed multi-word aliases and verified names first
        for alias, sym in sorted(WELL_KNOWN_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
            if sym in seen_symbols:
                continue
            pat = r'\b' + re.escape(alias) + r'\b'
            m = re.search(pat, clean, re.IGNORECASE)
            if m:
                sec = self.repo.get_by_symbol(sym)
                if sec:
                    seen_symbols.add(sym)
                    resolved_entities.append(ResolvedCompanyEntity(
                        raw_mention=m.group(0),
                        resolved_symbol=sec["symbol"],
                        company_name=sec["company_name"],
                        exchange=sec["exchange"],
                        bse_code=sec.get("bse_code"),
                        isin=sec.get("isin"),
                        sector=sec.get("sector"),
                        confidence=0.99,
                        match_type=MatchType.ALIAS,
                    ))

        # 2. Check explicit trigger phrases (e.g. "include ...", "invest in ...", "holding ...")
        for trig in triggers:
            for m in re.finditer(trig, clean, re.IGNORECASE):
                span = m.group(1)
                # Split by commas, semicolons, or 'and' (preserving 'L&T' / 'Larsen & Toubro')
                parts = re.split(r'[,;]|\b(?:and|also|plus)\b', span)
                for part in parts:
                    chunk = part.strip()
                    if not chunk or len(chunk) < 2 or chunk.lower() in [
                        "the", "a", "an", "all", "any", "some", "it", "more", "less",
                        "moderate", "conservative", "aggressive", "years", "months", "rupees", "crores", "lakhs"
                    ]:
                        continue

                    res = self.resolve_company(chunk)
                    if res.matched_symbol and res.matched_symbol not in seen_symbols:
                        seen_symbols.add(res.matched_symbol)
                        resolved_entities.append(ResolvedCompanyEntity(
                            raw_mention=chunk,
                            resolved_symbol=res.matched_symbol,
                            company_name=res.company_name,
                            exchange=res.exchange,
                            bse_code=res.bse_code,
                            isin=res.isin,
                            sector=res.sector,
                            confidence=res.confidence,
                            match_type=res.match_type,
                            is_ambiguous=res.is_ambiguous,
                            candidate_matches=res.candidate_matches,
                            clarification_prompt=res.clarification_prompt,
                        ))

        # 3. Direct uppercase symbols (e.g. "I hold 50 shares of BEL and 100 shares of TCS")
        for word in re.findall(r'\b[A-Z0-9_-]{2,12}\b', clean):
            if word in self.repo._by_symbol and word not in seen_symbols:
                # Avoid common English false positive capitalizations
                if word in ["IN", "AT", "OR", "ON", "AN", "AM", "IT", "GO", "DO", "NO", "SO", "MY", "ME", "WE", "US"]:
                    continue
                sec = self.repo.get_by_symbol(word)
                if sec:
                    seen_symbols.add(word)
                    resolved_entities.append(ResolvedCompanyEntity(
                        raw_mention=word,
                        resolved_symbol=sec["symbol"],
                        company_name=sec["company_name"],
                        exchange=sec["exchange"],
                        bse_code=sec.get("bse_code"),
                        isin=sec.get("isin"),
                        sector=sec.get("sector"),
                        confidence=1.0,
                        match_type=MatchType.EXACT_SYMBOL,
                    ))

        return resolved_entities


# Global company resolution service singleton
company_resolution_service = CompanyResolutionService()
