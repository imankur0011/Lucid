"""
Lucid Comprehensive NLP Investor Information Extraction & Evidence Engine.
Extracts structured financial parameters, risk suitability, goals, horizons,
multi-goal portfolios, SIP vs lump-sum, existing holdings, and sector preferences from natural language.
Features evidence traceability, conflict detection, and deterministic fallback.

Version: 2026.11-v2.0
Authoritative Date: 2026-11-04
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from sqlalchemy.orm import Session

try:
    from backend.config import settings
    from backend.agent.nodes import get_llm
    from backend.models import RiskQuestion, RiskQuestionOption
    from backend.schemas.nlp_profile import (
        ExtractionStatus,
        ValidationStatus,
        ContributionType,
        HorizonCategory,
        RiskCategoryEnum,
        ExtractedFieldMeta,
        ExtractedGoalItem,
        ExtractedExistingHolding,
        ExtractedSecurityPreference,
        ExtractedSectorConstraint,
        ExtractedCapitalDetails,
        ExtractedRiskDetails,
        ExtractedInvestmentPreferences,
        ExtractedInvestorExperience,
        MappedQuestionnaireAnswerItem,
        ContradictionItem,
        StructuredInvestorProfile,
    )
    from backend.services.financial_number_parser import financial_number_parser, words_to_number
    from backend.services.company_resolution_service import company_resolution_service
except ImportError:
    from config import settings
    from agent.nodes import get_llm
    from models import RiskQuestion, RiskQuestionOption
    from schemas.nlp_profile import (
        ExtractionStatus,
        ValidationStatus,
        ContributionType,
        HorizonCategory,
        RiskCategoryEnum,
        ExtractedFieldMeta,
        ExtractedGoalItem,
        ExtractedExistingHolding,
        ExtractedSecurityPreference,
        ExtractedSectorConstraint,
        ExtractedCapitalDetails,
        ExtractedRiskDetails,
        ExtractedInvestmentPreferences,
        ExtractedInvestorExperience,
        MappedQuestionnaireAnswerItem,
        ContradictionItem,
        StructuredInvestorProfile,
    )
    from services.financial_number_parser import financial_number_parser, words_to_number
    from services.company_resolution_service import company_resolution_service

logger = logging.getLogger(__name__)

# Sector normalization dictionary
CANONICAL_SECTORS = {
    "information technology": "Information Technology",
    "technology": "Information Technology",
    "tech": "Information Technology",
    "software": "Information Technology",
    "it": "Information Technology",
    "financial services": "Financial Services",
    "finance": "Financial Services",
    "banking": "Financial Services",
    "banks": "Financial Services",
    "bank": "Financial Services",
    "healthcare": "Healthcare & Pharmaceuticals",
    "pharma": "Healthcare & Pharmaceuticals",
    "pharmaceuticals": "Healthcare & Pharmaceuticals",
    "health": "Healthcare & Pharmaceuticals",
    "fmcg": "Fast Moving Consumer Goods",
    "consumer": "Fast Moving Consumer Goods",
    "consumer goods": "Fast Moving Consumer Goods",
    "energy": "Energy & Power",
    "power": "Energy & Power",
    "renewable": "Energy & Power",
    "renewables": "Energy & Power",
    "green energy": "Energy & Power",
    "clean energy": "Energy & Power",
    "automobile": "Automobile & Ancillaries",
    "auto": "Automobile & Ancillaries",
    "vehicles": "Automobile & Ancillaries",
    "ev": "Automobile & Ancillaries",
    "metals": "Metals & Mining",
    "mining": "Metals & Mining",
    "steel": "Metals & Mining",
    "telecom": "Telecommunication",
    "telecommunications": "Telecommunication",
    "construction": "Construction & Infrastructure",
    "infra": "Construction & Infrastructure",
    "infrastructure": "Construction & Infrastructure",
    "chemicals": "Specialty Chemicals",
    "tobacco": "Tobacco",
    "cigarettes": "Tobacco",
    "liquor": "Alcohol & Distilleries",
    "alcohol": "Alcohol & Distilleries",
    "breweries": "Alcohol & Distilleries",
    "defense": "Defense & Aerospace",
    "aerospace": "Defense & Aerospace",
    "betting": "Betting & Gambling",
    "gambling": "Betting & Gambling",
    "casinos": "Betting & Gambling",
}

EXCLUSION_KEYWORDS = [
    "avoid", "exclude", "do not want", "don't want", "no", "stay away from",
    "skip", "exclude tobacco", "exclude defense", "without", "hate", "strictly avoid"
]

HYPOTHETICAL_KEYWORDS = [
    "what if", "suppose i", "hypothetically", "if i had", "assume i", "just curious if", "what would happen if"
]


def is_hypothetical_query(text: str) -> bool:
    """Checks whether the user input is a hypothetical what-if question."""
    lower = text.lower()
    return any(hk in lower for hk in HYPOTHETICAL_KEYWORDS)


def parse_indian_currency_amount(text: str) -> Optional[float]:
    """
    Extracts monetary amounts from natural language text using the comprehensive
    financial number parser. Handles Indian & international scales:
    e.g. '2.5 lakh', '2.5L', '250000', '₹3,50,000', '50k', '1 crore', '10L',
    'one lakh twenty-five thousand', 'two crore fifty lakh', '1.5Cr'.
    """
    clean = text.strip()
    if not clean:
        return None

    # Priority 1: Currency-prefixed expressions (e.g. ₹2.5 lakh, Rs. 50,000, INR 1.5 crore)
    curr_matches = re.finditer(
        r'(?:₹|rs\.?|inr|rupees?)\s*([0-9\.,\s]+(?:\s*(?:cr|crore|crores|lakh|lakhs|lac|lacs|l|k|thousand|million))?|[a-z\s]+?(?:crore|lakh|thousand|hundred)?)',
        clean,
        re.IGNORECASE,
    )
    for cm in curr_matches:
        span = cm.group(0).strip()
        parsed = financial_number_parser.parse_expression(span)
        if parsed and parsed.normalized_value and 100.0 <= parsed.normalized_value <= 10_000_000_000.0:
            return float(parsed.normalized_value)

    # Priority 2: Indian Scale Phrases (e.g. '2.5 lakh', 'one lakh twenty-five thousand', '1.5 crore', '50k')
    scale_matches = re.finditer(
        r'\b([0-9\.,]+|\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|twenty-five|thirty|forty|fifty|hundred|thousand|lakh|crore|point)\b[\w\s\.-]*?)\s*(?:cr|crore|crores|lakh|lakhs|lac|lacs|l|k|thousand|million|billion)\b',
        clean,
        re.IGNORECASE,
    )
    for sm in scale_matches:
        span = sm.group(0).strip()
        parsed = financial_number_parser.parse_expression(span)
        if parsed and parsed.normalized_value and 100.0 <= parsed.normalized_value <= 10_000_000_000.0:
            return float(parsed.normalized_value)

    # Priority 3: Standalone numbers / comma-formatted digits (e.g. '50,000' or '250000')
    standalone_matches = re.finditer(r'\b(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})*|\d{4,9})\b', clean, re.IGNORECASE)
    for dm in standalone_matches:
        raw_val = dm.group(1).replace(",", "")
        try:
            val = float(raw_val)
            if 1_000.0 <= val <= 10_000_000_000.0:
                return val
        except ValueError:
            pass

    # Priority 4: Full-phrase financial number parser fallback
    parsed_full = financial_number_parser.parse_expression(clean)
    if parsed_full and parsed_full.semantic_type == "MONETARY_AMOUNT" and parsed_full.normalized_value:
        return float(parsed_full.normalized_value)

    return None


def parse_contribution_type(text: str) -> Tuple[ContributionType, Optional[float], Optional[float]]:
    """
    Distinguishes Monthly SIP vs Lump-Sum vs Both.
    Returns: (contribution_type, initial_lump_sum, monthly_contribution)
    """
    clean = text.lower()

    # Check for explicit monthly contribution phrases
    # Avoid matching 'experience in mutual fund sips' as an active monthly contribution!
    monthly_patterns = [
        r'(?:every month|per month|each month|monthly|p\.m\.)',
        r'(?:monthly sip|invest every month|invest monthly|sip of)\b',
    ]
    is_monthly = any(re.search(pat, clean) for pat in monthly_patterns)
    if is_monthly and ("experience" in clean or "familiar" in clean):
        if not any(w in clean for w in ["every month", "per month", "each month", "monthly contribution", "investing every month"]):
            is_monthly = False

    is_lump_sum = any(w in clean for w in ["lump sum", "one time", "upfront", "available for investment", "initial", "one-off", "lakhs inr to invest", "lakh to invest", "to invest as a lump sum"])

    amount = parse_indian_currency_amount(text)

    if is_monthly and is_lump_sum:
        return ContributionType.BOTH, amount, amount
    elif is_monthly:
        return ContributionType.MONTHLY_SIP, None, amount
    elif is_lump_sum or amount is not None:
        return ContributionType.LUMP_SUM, amount, None
    else:
        return ContributionType.NOT_SPECIFIED, None, None


def parse_investment_horizon(text: str) -> Optional[int]:
    """
    Extracts horizon in months from text using the comprehensive number parser:
    e.g. 'invest for 5 years' -> 60, '18 months' -> 18, '3 yrs' -> 36, 'five years' -> 60,
    'two point five years' -> 30, 'twenty-four months' -> 24.
    Carefully distinguishes investment timeframe from age (e.g. '28 years old').
    """
    clean = text.lower()

    # Priority 1: Explicit investment horizon / timeframe phrases
    horizon_phrases = [
        r'(?:for|over|horizon|timeframe|invest for|period of|span of|duration of|next|approximately|around|about)\s*(?:approximately\s*|around\s*|about\s*)?([a-zA-Z0-9\.\-]+)\s*(?:years?|yrs?|yr)\b(?!\s*old)',
        r'(?:for|over|horizon|timeframe|invest for|period of|span of|duration of|next|approximately|around|about)\s*(?:approximately\s*|around\s*|about\s*)?([a-zA-Z0-9\.\-]+)\s*(?:months?|mos?|mo)\b',
    ]
    for pat in horizon_phrases:
        m = re.search(pat, clean)
        if m:
            raw_val = m.group(1).strip()
            num_val = words_to_number(raw_val)
            if num_val is None:
                try:
                    num_val = float(raw_val)
                except ValueError:
                    pass
            if num_val is not None and 0.1 <= num_val <= 60.0:
                if "month" in pat or "mo" in pat:
                    return int(round(num_val))
                return int(round(num_val * 12))

    # Priority 2: General Years regex (excluding 'years old')
    for m in re.finditer(r'([a-zA-Z0-9\.\-]+)\s*(?:years?|yrs?|yr)\b(?!\s*old)', clean):
        raw_val = m.group(1).strip()
        num_val = words_to_number(raw_val)
        if num_val is None:
            try:
                num_val = float(raw_val)
            except ValueError:
                pass
        if num_val is not None and 0.5 <= num_val <= 40:
            return int(round(num_val * 12))

    # Priority 3: General Months regex
    for m in re.finditer(r'([a-zA-Z0-9\.\-]+)\s*(?:months?|mos?|mo)\b', clean):
        raw_val = m.group(1).strip()
        num_val = words_to_number(raw_val)
        if num_val is None:
            try:
                num_val = float(raw_val)
            except ValueError:
                pass
        if num_val is not None and 1 <= num_val <= 360:
            return int(round(num_val))

    # Priority 4: Qualitative phrases
    if "very long term" in clean or "10 year" in clean:
        return 120
    if "long term" in clean or "5 year" in clean:
        return 60
    if "medium term" in clean or "3 year" in clean:
        return 36
    if "short term" in clean or "1 year" in clean:
        return 12

    return None


def extract_sectors_and_restrictions(text: str) -> Tuple[List[str], List[str], List[str]]:
    """
    Extracts:
    1. preferred_sectors (positive affinity / allocation requests)
    2. excluded_sectors (strict prohibitions e.g. 'avoid tobacco, betting')
    3. soft_exposure_limits (e.g. 'avoid too much exposure to IT')
    """
    preferred = set()
    excluded = set()
    soft_limits = set()

    delimiters = r"(?:\.|\;|\n|\bbut\b|\bhowever\b|\balthough\b|\bexcept\b|\band\s+please\s+avoid\b|\band\s+avoid\b|\band\s+exclude\b|\band\s+want\b|\band\s+prefer\b|\band\s+love\b|\band\s+like\b)"
    clauses = re.split(delimiters, text, flags=re.IGNORECASE)

    excl_trigger_pattern = r"\b(?:avoid|exclude|stay\s+away\s+from|strictly\s+avoid|please\s+avoid|do\s+not\s+want|don\'t\s+want|without|skip|no\s+exposure\s+to|zero\s+exposure\s+to|hate|never\s+invest\s+in|ban)\b"
    soft_trigger_pattern = r"\b(?:avoid\s+too\s+much|don\'t\s+want\s+too\s+much|not\s+too\s+much|not\s+too\s+concentrated\s+in|don\'t\s+want.*concentrated\s+in|limit\s+exposure\s+to|minimize\s+exposure\s+to|less\s+exposure\s+to|do\s+not\s+allocate\s+more\s+than|don\'t\s+allocate\s+more\s+than|not\s+more\s+than|no\s+more\s+than|max(?:imum)?\s+(?:of\s+)?\d+|capped\s+at|up\s+to\s+\d+|ceiling\s+of)\b"
    pref_trigger_pattern = r"\b(?:want\s+strong\s+exposure\s+to|strong\s+exposure\s+to|high\s+exposure\s+to|exposure\s+to|prefer|preference\s+for|like|love|focus\s+on|interested\s+in|bullish\s+on|tilt\s+towards|lean\s+towards|overweight|heavy\s+on|more\s+of|want|looking\s+for|include|favour|favor|invest\s+in)\b"

    sorted_aliases = sorted(CANONICAL_SECTORS.keys(), key=lambda x: len(x), reverse=True)

    for clause in clauses:
        clause_low = clause.lower().strip()
        if not clause_low:
            continue

        found_in_clause = set()
        for alias in sorted_aliases:
            canon = CANONICAL_SECTORS[alias]
            if re.search(r"\b" + re.escape(alias) + r"\b", clause_low):
                if alias == "it":
                    # Disambiguate English pronoun "it" vs Information Technology
                    is_tech_context = bool(
                        re.search(r"\bIT\b", clause)
                        or re.search(r"\b(?:i\.t\.|software|tech|information\s+technology)\b", clause_low)
                        or re.search(r"\b(?:exposure\s+to|overweight|invest\s+in|preference\s+for)\s+it\b", clause_low)
                    )
                    if not is_tech_context:
                        continue
                found_in_clause.add((alias, canon))

        if not found_in_clause:
            continue

        has_soft = bool(re.search(soft_trigger_pattern, clause_low))
        has_excl = bool(re.search(excl_trigger_pattern, clause_low))
        has_pref = bool(re.search(pref_trigger_pattern, clause_low))

        for alias, canon in found_in_clause:
            no_sector = bool(re.search(r"\bno\s+(?:more\s+)?(?:\w+\s+)?" + re.escape(alias) + r"\b", clause_low))

            if has_soft:
                soft_limits.add(canon)
            elif has_excl or no_sector:
                excluded.add(canon)
            elif has_pref or (not has_excl and not no_sector):
                if canon not in excluded and canon not in soft_limits:
                    preferred.add(canon)

    preferred = preferred - excluded - soft_limits

    return sorted(list(preferred)), sorted(list(excluded)), sorted(list(soft_limits))


def extract_sectors_from_text(text: str) -> Tuple[List[str], List[str]]:
    """Helper returning (preferred_sectors, excluded_sectors)."""
    pref, excl, _ = extract_sectors_and_restrictions(text)
    return pref, excl


def extract_multiple_goals(text: str) -> List[ExtractedGoalItem]:
    """
    Detects and extracts multiple distinct financial goals and their separate horizons.
    e.g. 'child education in 10 years and save for a house in 5 years'.
    """
    clean = text.lower()
    goals = []

    goal_triggers = [
        (r'child(?:ren)?(?:\'s)?\s*education', "child_education", "Child Education Corpus"),
        (r'house|home|apartment|flat|property', "home_purchase", "Home Purchase / Down-Payment"),
        (r'car|vehicle|automobile|bike', "vehicle_purchase", "Vehicle / Car Purchase"),
        (r'marriage|wedding', "wedding", "Marriage / Wedding Expenses"),
        (r'vacation|travel|holiday', "travel", "Travel / Vacation Fund"),
        (r'retire(?:ment)?', "retirement", "Retirement Security"),
        (r'wealth|capital compounding|long term growth', "wealth_creation", "Long-Term Wealth Creation"),
        (r'income|dividend|regular cash', "income_generation", "Dividend Income Flow"),
        (r'\b(?:save\s+for|building|build|create|aim\s+for|investing\s+for|setting\s+aside)\s+(?:an?\s+)?(?:emergency|safety\s+buffer)\b|\b(?:goal\s+is|target\s+is)\s+(?:an?\s+)?(?:emergency|safety\s+buffer)\b', "emergency_fund", "Emergency Safety Reserve"),
    ]

    for pattern, g_type, default_name in goal_triggers:
        m = re.search(pattern, clean)
        if m:
            # Look for horizon and amount near this goal match
            start_pos = max(0, m.start() - 30)
            end_pos = min(len(clean), m.end() + 70)
            window = clean[start_pos:end_pos]

            horizon_m = parse_investment_horizon(window)
            target_amt = parse_indian_currency_amount(window)

            h_cat = HorizonCategory.NOT_SPECIFIED
            if horizon_m:
                if horizon_m <= 36:
                    h_cat = HorizonCategory.SHORT_TERM
                elif horizon_m <= 84:
                    h_cat = HorizonCategory.MEDIUM_TERM
                else:
                    h_cat = HorizonCategory.LONG_TERM

            goals.append(ExtractedGoalItem(
                goal_name=default_name,
                goal_type=g_type,
                target_amount=target_amt,
                horizon_months=horizon_m,
                horizon_years=round(horizon_m / 12, 1) if horizon_m else None,
                time_horizon_category=h_cat,
                source_span=m.group(0),
                extraction_status=ExtractionStatus.EXPLICIT,
            ))

    if not goals:
        horizon_m = parse_investment_horizon(text) or 60
        default_goal_name = "Long-Term Wealth Creation" if horizon_m > 36 else "Medium-Term Wealth Creation" if horizon_m >= 12 else "Short-Term Wealth Compounding"
        goals.append(ExtractedGoalItem(
            goal_name=default_goal_name,
            goal_type="wealth_creation",
            horizon_months=horizon_m,
            horizon_years=round(horizon_m / 12, 1) if horizon_m else 5.0,
            time_horizon_category=HorizonCategory.LONG_TERM if (horizon_m and horizon_m > 36) else HorizonCategory.MEDIUM_TERM,
            extraction_status=ExtractionStatus.NORMALIZED_FROM_TEXT,
        ))

    return goals


def extract_existing_holdings(text: str) -> List[ExtractedExistingHolding]:
    """
    Dynamically extracts mentioned existing stock holdings with quantities and values
    from freeform natural language text using database-backed SecurityMasterRepository.
    No hardcoded ticker whitelists.
    e.g. 'I already own 50 shares of TCS and 100 shares of Infosys'
    """
    clean = text.strip()
    if not clean:
        return []

    # Check for holding trigger phrases
    own_triggers = r'\b(?:already own|already have|currently hold|currently own|existing portfolio of|existing holdings|holding|hold|shares of|units of|my portfolio has)\b'
    m_trig = re.search(own_triggers, clean, re.IGNORECASE)
    if not m_trig and not re.search(r'\b\d+\s*(?:shares?|stocks?|units?)\s*(?:of|in)\b', clean, re.IGNORECASE):
        return []

    holdings: List[ExtractedExistingHolding] = []
    seen_symbols = set()

    # Split into clauses, protecting comma-formatted numbers like 25,000
    clauses = re.split(r'(?<!\d)[,;\n](?!\d)|\band\b', clean, flags=re.IGNORECASE)
    for c in clauses:
        c_str = c.strip()
        if not c_str:
            continue
        # Extract entities resolved against security master
        entities = company_resolution_service.extract_and_resolve_companies_from_text(c_str)
        if not entities:
            continue

        # Extract quantity if present
        qty = None
        qm = re.search(r'([a-zA-Z0-9\.\-]+)\s*(?:shares?|units?|stocks?|equities)\b', c_str, re.IGNORECASE)
        if qm:
            raw_q = qm.group(1).strip()
            v = words_to_number(raw_q)
            if v is None:
                try:
                    v = float(raw_q)
                except ValueError:
                    pass
            if v and v > 0:
                qty = int(round(v))

        # Extract monetary value if present (e.g. ₹25,000 in ITC)
        val = None
        vm = re.search(r'(?:₹|rs\.?|inr)\s*([0-9\.,]+|\b(?:one|two|three|four|five|ten|twenty|fifty|hundred|thousand|lakh)\b[\w\s\.-]*)', c_str, re.IGNORECASE)
        if vm:
            parsed = financial_number_parser.parse_expression(vm.group(0))
            if parsed and parsed.normalized_value:
                val = float(parsed.normalized_value)

        for entity in entities:
            if entity.resolved_symbol and entity.resolved_symbol not in seen_symbols:
                seen_symbols.add(entity.resolved_symbol)
                holdings.append(ExtractedExistingHolding(
                    symbol=entity.resolved_symbol,
                    company_name=entity.company_name,
                    exchange=entity.exchange,
                    quantity=qty,
                    current_value=val,
                    source_span=c_str,
                ))

    return holdings


def extract_preferred_securities(text: str, excluded_symbols: Optional[Set[str]] = None) -> List[ExtractedSecurityPreference]:
    """
    Extracts positive stock/equity preferences dynamically from text.
    Uses CompanyResolutionService against the active universe.
    Filters out existing holdings and explicit exclusions.
    """
    clean = text.strip()
    if not clean:
        return []

    excluded = excluded_symbols or set()
    pref_triggers = r'\b(?:include|invest in|exposure to|buy|prefer|interested in|tilt towards|favour|favor|like|love|want|looking for|add)\s+([^.]+)'
    matches = re.finditer(pref_triggers, clean, re.IGNORECASE)

    pref_list: List[ExtractedSecurityPreference] = []
    seen = set()

    for m in matches:
        span = m.group(1)
        entities = company_resolution_service.extract_and_resolve_companies_from_text(span)
        for e in entities:
            if e.resolved_symbol and e.resolved_symbol not in seen and e.resolved_symbol not in excluded:
                seen.add(e.resolved_symbol)
                pref_list.append(ExtractedSecurityPreference(
                    company_name=e.company_name,
                    resolved_symbol=e.resolved_symbol,
                    exchange=e.exchange,
                    bse_code=e.bse_code,
                    isin=e.isin,
                    confidence=e.confidence,
                    source_span=span.strip(),
                ))

    return pref_list


def extract_sector_constraints(text: str) -> List[ExtractedSectorConstraint]:
    """
    Extracts quantitative sector constraints, e.g.:
    - 'Do not allocate more than 20% to the banking sector.' -> sector='Financial Services', operator='LTE', value=20.0
    - 'At least 15% in IT.' -> sector='Information Technology', operator='GTE', value=15.0
    - 'Cap energy sector at 10%.' -> sector='Energy & Power', operator='LTE', value=10.0
    """
    clean = text.strip()
    if not clean:
        return []

    constraints: List[ExtractedSectorConstraint] = []
    clauses = re.split(r'[.;\n]', clean)
    sorted_aliases = sorted(CANONICAL_SECTORS.keys(), key=lambda x: len(x), reverse=True)

    seen_sectors = set()

    for c in clauses:
        c_low = c.lower().strip()
        if not c_low:
            continue

        matched_sectors = set()
        for alias in sorted_aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', c_low):
                if alias == 'it' and not (re.search(r'\bIT\b', c) or 'tech' in c_low or 'software' in c_low or 'information technology' in c_low):
                    continue
                matched_sectors.add(CANONICAL_SECTORS[alias])

        if not matched_sectors:
            continue

        # Check if the clause contains a percentage or comparison
        if '%' in c or 'percent' in c_low or 'pct' in c_low or any(op_w in c_low for op_w in ['more than', 'less than', 'at most', 'at least', 'cap', 'limit', 'exceed', 'up to']):
            parsed = financial_number_parser.parse_expression(c)
            if parsed and (parsed.semantic_type == "PERCENTAGE" or parsed.unit == "PERCENT" or '%' in c or 'percent' in c_low):
                val = parsed.normalized_value if parsed.normalized_value is not None else (parsed.max_value or 20.0)
                op = parsed.comparison_operator.value
                for sec in matched_sectors:
                    if sec not in seen_sectors:
                        seen_sectors.add(sec)
                        constraints.append(ExtractedSectorConstraint(
                            sector=sec,
                            operator=op,
                            value=val,
                            unit="PERCENT",
                            source_span=c.strip(),
                        ))

    return constraints


def detect_contradictions(text: str) -> List[ContradictionItem]:
    """
    Detects financial contradictions (e.g., high returns without taking any risk).
    """
    clean = text.lower()
    contradictions = []

    # Conflict 1: High Returns vs Zero Risk
    has_high_returns = any(w in clean for w in ["high return", "highest return", "maximum return", "aggressive return", "beat the market"])
    has_zero_risk = any(w in clean for w in ["no risk", "zero risk", "without losing money", "cannot afford to lose", "don't want to lose money", "protect all capital"])

    if has_high_returns and has_zero_risk:
        contradictions.append(ContradictionItem(
            conflict_code="CONFLICT_HIGH_RETURNS_ZERO_RISK",
            title="Conflicting Risk-Return Expectations",
            description="You indicated a desire for high returns while stating an unwillingness to take any investment risk.",
            conflicting_elements=["High returns", "Zero investment risk"],
            suggested_tradeoff_resolution="In financial markets, higher potential returns require absorbing market price fluctuations. Would you prefer a Moderate/Growth posture aiming for higher returns, or a Conservative posture prioritizing capital protection with lower returns?",
        ))

    return contradictions


def deterministic_extract_investor_profile(text: str) -> StructuredInvestorProfile:
    """
    High-fidelity deterministic rule-based extractor with full evidence traceability.
    """
    lower = text.lower()

    # 1. Capital & Contribution
    contrib_type, lump_sum, monthly = parse_contribution_type(text)
    field_evidence: Dict[str, ExtractedFieldMeta] = {}

    if lump_sum is not None:
        capital_details = ExtractedCapitalDetails(
            initial_lump_sum=lump_sum,
            monthly_contribution=monthly,
            contribution_type=contrib_type,
            currency_code="INR",
            source_span=f"₹{lump_sum:,.0f}",
        )
        field_evidence["investment_amount"] = ExtractedFieldMeta(
            field_name="investment_amount",
            value=lump_sum,
            data_type="number",
            extraction_status=ExtractionStatus.EXPLICIT,
            validation_status=ValidationStatus.VALID,
            source_span=f"₹{lump_sum:,.0f}",
        )
    elif monthly is not None:
        capital_details = ExtractedCapitalDetails(
            initial_lump_sum=None,
            monthly_contribution=monthly,
            contribution_type=ContributionType.MONTHLY_SIP,
            currency_code="INR",
            source_span=f"₹{monthly:,.0f}/month",
        )
        field_evidence["monthly_contribution"] = ExtractedFieldMeta(
            field_name="monthly_contribution",
            value=monthly,
            data_type="number",
            extraction_status=ExtractionStatus.EXPLICIT,
            validation_status=ValidationStatus.VALID,
            source_span=f"₹{monthly:,.0f} per month",
        )
        field_evidence["investment_amount"] = ExtractedFieldMeta(
            field_name="investment_amount",
            value=monthly,
            data_type="number",
            extraction_status=ExtractionStatus.EXPLICIT,
            validation_status=ValidationStatus.VALID,
            source_span=f"₹{monthly:,.0f} per month",
        )
    else:
        capital_details = ExtractedCapitalDetails(
            initial_lump_sum=None,
            contribution_type=ContributionType.NOT_SPECIFIED,
        )
        field_evidence["investment_amount"] = ExtractedFieldMeta(
            field_name="investment_amount",
            value=None,
            data_type="number",
            extraction_status=ExtractionStatus.NOT_PROVIDED,
            validation_status=ValidationStatus.REQUIRES_CONFIRMATION,
            clarification_prompt="How much capital do you plan to invest (e.g. ₹1,00,000 lump sum or ₹10,000/month)?",
        )

    # 2. Horizon
    horizon_months = parse_investment_horizon(text)
    if horizon_months:
        horizon_years = round(horizon_months / 12.0, 1)
        if horizon_months < 12:
            h_cat = HorizonCategory.SHORT_TERM
        elif horizon_months <= 36:
            h_cat = HorizonCategory.MEDIUM_TERM
        else:
            h_cat = HorizonCategory.LONG_TERM

        field_evidence["investment_horizon"] = ExtractedFieldMeta(
            field_name="investment_horizon",
            value=horizon_months,
            data_type="integer",
            extraction_status=ExtractionStatus.EXPLICIT if any(w in lower for w in ["year", "years", "month", "months"]) else ExtractionStatus.NORMALIZED_FROM_TEXT,
            validation_status=ValidationStatus.VALID,
            source_span=f"{horizon_years} years" if horizon_years >= 1 else f"{horizon_months} months",
        )
    else:
        horizon_years = None
        h_cat = HorizonCategory.NOT_SPECIFIED
        field_evidence["investment_horizon"] = ExtractedFieldMeta(
            field_name="investment_horizon",
            value=None,
            data_type="integer",
            extraction_status=ExtractionStatus.NOT_PROVIDED,
            validation_status=ValidationStatus.REQUIRES_CONFIRMATION,
            clarification_prompt="What is your planned investment timeframe or horizon (e.g., 3 years, 5 years)?",
        )

    # 3. Financial Goals
    goals = extract_multiple_goals(text)
    field_evidence["financial_goals"] = ExtractedFieldMeta(
        field_name="financial_goals",
        value=[g.goal_name for g in goals],
        data_type="list",
        extraction_status=ExtractionStatus.EXPLICIT if len(goals) > 1 else ExtractionStatus.NORMALIZED_FROM_TEXT,
        validation_status=ValidationStatus.VALID,
    )

    # 4. Risk Details & SEBI Guardrails
    has_no_emergency = any(w in lower for w in [
        "no emergency", "zero emergency", "without emergency", "haven't saved", "no backup", "no reserve",
        "do not have any emergency", "don't have any emergency", "not have an emergency", "not have any emergency",
    ])
    m_match = re.search(r'\b(\d+(?:\.\d+)?)[-\s]*months?\s*(?:emergency|reserve|living|savings|fund)', lower)
    months_mentioned = float(m_match.group(1)) if m_match else None

    has_partial_emergency = any(w in lower for w in [
        "1 month", "2 months", "3 months", "4 months", "partial emergency", "some reserve", "small emergency"
    ]) or bool(re.search(r'\b[1-4][-\s]*months?\s*(?:emergency|reserve|living|savings|fund)', lower)) or (months_mentioned is not None and 0 < months_mentioned < 6)

    has_full_emergency = any(w in lower for w in [
        "6 months", "6-month", "6+ months", "8 months", "8-month", "9 months", "9-month",
        "full emergency", "emergency reserve", "have emergency fund",
        "emergency fund covering", "emergency savings", "1 year emergency", "12 months", "dedicated emergency"
    ]) or bool(re.search(r'\b(?:full\s*)?([6-9]|\d{2})[-\s]*months?\s*(?:emergency|reserve|living|savings|fund)', lower)) or (months_mentioned is not None and months_mentioned >= 6)

    if has_no_emergency:
        emergency_status = "none"
        loss_months = 0.0
    elif has_partial_emergency:
        emergency_status = "partial"
        loss_months = months_mentioned if months_mentioned is not None else 3.0
    elif has_full_emergency:
        emergency_status = "full"
        loss_months = months_mentioned if months_mentioned is not None else 6.0
    else:
        emergency_status = "unspecified"
        loss_months = None

    # Stated Risk Tolerance
    stated_tolerance = None
    if any(w in lower for w in ["very conservative", "cannot lose", "no loss", "zero risk", "capital preservation", "retiree"]):
        risk_tier = RiskCategoryEnum.VERY_CONSERVATIVE
        target_vol = 8.0
        stated_tolerance = "Very Conservative (Capital Preservation)"
    elif any(w in lower for w in ["conservative", "low risk", "safety first", "defensive", "stable returns"]):
        risk_tier = RiskCategoryEnum.CONSERVATIVE
        target_vol = 10.0
        stated_tolerance = "Conservative (Low Volatility)"
    elif any(w in lower for w in ["aggressive", "maximum return", "high risk", "alpha", "risk seeker"]):
        risk_tier = RiskCategoryEnum.AGGRESSIVE
        target_vol = 18.0
        stated_tolerance = "Aggressive (High Return Seeking)"
    elif any(w in lower for w in ["growth", "high growth", "wealth compounding", "long term wealth"]):
        risk_tier = RiskCategoryEnum.GROWTH
        target_vol = 15.0
        stated_tolerance = "Growth (Capital Compounding)"
    elif any(w in lower for w in ["moderate", "balanced", "medium risk", "moderate risk"]):
        risk_tier = RiskCategoryEnum.MODERATE
        target_vol = 12.5
        stated_tolerance = "Moderate (Balanced Growth)"
    else:
        risk_tier = RiskCategoryEnum.MODERATE
        target_vol = 12.5
        stated_tolerance = None

    fiduciary_safeguards = []
    # SEBI Fiduciary Constraint Override:
    # Zero emergency fund strictly caps loss capacity to Conservative
    if emergency_status == "none":
        if risk_tier in [RiskCategoryEnum.GROWTH, RiskCategoryEnum.AGGRESSIVE, RiskCategoryEnum.MODERATE]:
            fiduciary_safeguards.append(
                "SEBI RIA Loss Capacity Rule: Zero emergency reserve detected: Risk capacity capped to CONSERVATIVE under SEBI RIA loss-protection rules (10.0% Target Volatility)."
            )
            risk_tier = RiskCategoryEnum.CONSERVATIVE
            target_vol = 10.0

    # Short Horizon Capping
    if horizon_months and horizon_months < 24:
        if risk_tier in [RiskCategoryEnum.GROWTH, RiskCategoryEnum.AGGRESSIVE]:
            fiduciary_safeguards.append(
                "Short investment horizon (<24 months) limits direct equity volatility corridor to CONSERVATIVE."
            )
            risk_tier = RiskCategoryEnum.CONSERVATIVE
            target_vol = 10.0

    contradictions = detect_contradictions(text)

    risk_details = ExtractedRiskDetails(
        stated_tolerance=stated_tolerance,
        loss_capacity_emergency_months=loss_months,
        emergency_fund_status=emergency_status,
        assessed_risk_category=risk_tier,
        target_volatility_pct=target_vol,
        is_conflict_detected=len(contradictions) > 0,
        conflict_description=contradictions[0].description if contradictions else None,
        fiduciary_safeguards_applied=fiduciary_safeguards,
    )

    field_evidence["risk_preference"] = ExtractedFieldMeta(
        field_name="risk_preference",
        value=risk_tier.value,
        data_type="string",
        extraction_status=ExtractionStatus.EXPLICIT if stated_tolerance else ExtractionStatus.INFERRED,
        validation_status=ValidationStatus.CONFLICT if contradictions else (ValidationStatus.VALID if stated_tolerance else ValidationStatus.REQUIRES_CONFIRMATION),
        source_span=stated_tolerance,
        clarification_prompt=contradictions[0].suggested_tradeoff_resolution if contradictions else None,
    )

    # 5. Preferences, Exclusions, Preferred Securities, & Sector Constraints
    pref_sec, excl_sec, soft_limits = extract_sectors_and_restrictions(text)
    company_chars = []
    if any(w in lower for w in ["fundamental", "strong balance sheet", "fundamentally strong", "quality"]):
        company_chars.append("Fundamentally strong balance sheets")
    if any(w in lower for w in ["reasonable valuation", "fair value", "low pe", "value"]):
        company_chars.append("Reasonable valuation multiples")
    if any(w in lower for w in ["dividend", "high dividend", "yield"]):
        company_chars.append("Consistent dividend track record")

    # 7. Existing Holdings & Preferred Securities
    existing_holdings = extract_existing_holdings(text)
    existing_syms = {h.symbol for h in existing_holdings}
    preferred_securities = extract_preferred_securities(text, excluded_symbols=existing_syms)
    sector_constraints = extract_sector_constraints(text)

    preferences = ExtractedInvestmentPreferences(
        preferred_sectors=pref_sec,
        excluded_sectors=excl_sec,
        preferred_securities=preferred_securities,
        sector_constraints=sector_constraints,
        company_characteristics=company_chars,
        soft_preferences_notes=f"Limit exposure to: {', '.join(soft_limits)}" if soft_limits else None,
    )

    field_evidence["preferred_sectors"] = ExtractedFieldMeta(
        field_name="preferred_sectors",
        value=pref_sec,
        data_type="list",
        extraction_status=ExtractionStatus.EXPLICIT if pref_sec else ExtractionStatus.NOT_PROVIDED,
        validation_status=ValidationStatus.VALID,
    )
    field_evidence["excluded_sectors"] = ExtractedFieldMeta(
        field_name="excluded_sectors",
        value=excl_sec,
        data_type="list",
        extraction_status=ExtractionStatus.EXPLICIT if excl_sec else ExtractionStatus.NOT_PROVIDED,
        validation_status=ValidationStatus.VALID,
    )
    if preferred_securities:
        field_evidence["preferred_securities"] = ExtractedFieldMeta(
            field_name="preferred_securities",
            value=[f"{p.company_name} ({p.resolved_symbol})" for p in preferred_securities],
            data_type="list",
            extraction_status=ExtractionStatus.EXPLICIT,
            validation_status=ValidationStatus.VALID,
        )
    if sector_constraints:
        field_evidence["sector_constraints"] = ExtractedFieldMeta(
            field_name="sector_constraints",
            value=[f"{sc.sector} {sc.operator} {sc.value}{sc.unit}" for sc in sector_constraints],
            data_type="list",
            extraction_status=ExtractionStatus.EXPLICIT,
            validation_status=ValidationStatus.VALID,
        )

    # 6. Experience & Knowledge
    # Explicit negative/beginner phrases override substrings like "mutual fund" in "no experience in mutual funds"
    has_no_experience = any(p in lower for p in [
        "no experience", "zero experience", "never invested", "first time", "first-time",
        "new to", "novice", "beginner", "no knowledge", "little to no experience",
        "fd only", "only bank fds", "only deposits", "only fixed deposit", "bank deposits only",
        "no previous investment"
    ])
    has_experienced = any(w in lower for w in ["experienced", "actively trade", "direct equity", "direct stocks", "seasoned", "advanced"])
    has_intermediate = (
        any(w in lower for w in ["invest in mutual fund", "have mutual fund", "some experience", "invested before", "intermediate"])
        or (any(w in lower for w in ["mutual fund", "sip", "sips", "index fund"]) and not has_no_experience)
    )
    has_beginner = has_no_experience or any(w in lower for w in ["beginner", "new to", "first time", "novice", "never invested", "fd only"])

    if has_experienced and not has_no_experience:
        exp_lvl = "experienced"
        know_lvl = "advanced"
        exp_status = ExtractionStatus.EXPLICIT
        exp_val = ValidationStatus.VALID
        exp_prompt = None
    elif has_intermediate:
        exp_lvl = "intermediate"
        know_lvl = "intermediate"
        exp_status = ExtractionStatus.EXPLICIT
        exp_val = ValidationStatus.VALID
        exp_prompt = None
    elif has_beginner:
        exp_lvl = "beginner"
        know_lvl = "basic"
        exp_status = ExtractionStatus.EXPLICIT
        exp_val = ValidationStatus.VALID
        exp_prompt = None
    else:
        exp_lvl = "unspecified"
        know_lvl = "unspecified"
        exp_status = ExtractionStatus.NOT_PROVIDED
        exp_val = ValidationStatus.REQUIRES_CONFIRMATION
        exp_prompt = "What is your investment knowledge and market experience level (e.g., beginner, mutual funds, direct stocks)?"

    experience = ExtractedInvestorExperience(
        experience_level=exp_lvl if exp_status != ExtractionStatus.NOT_PROVIDED else "unspecified",
        knowledge_level=know_lvl if exp_status != ExtractionStatus.NOT_PROVIDED else "unspecified",
        source_span=exp_lvl if exp_status != ExtractionStatus.NOT_PROVIDED else None,
    )
    field_evidence["investment_experience"] = ExtractedFieldMeta(
        field_name="investment_experience",
        value=exp_lvl if exp_status != ExtractionStatus.NOT_PROVIDED else None,
        data_type="string",
        extraction_status=exp_status,
        validation_status=exp_val,
        clarification_prompt=exp_prompt,
    )

    # 8. Check Missing Mandatory Fields
    missing_mandatory = []
    if capital_details.initial_lump_sum is None and capital_details.monthly_contribution is None:
        missing_mandatory.append("investment_amount")
    if horizon_months is None:
        missing_mandatory.append("investment_horizon")
    if stated_tolerance is None:
        missing_mandatory.append("risk_preference")
    if exp_status == ExtractionStatus.NOT_PROVIDED:
        missing_mandatory.append("investment_experience")

    # Generate targeted follow-up questions
    clarifications = []
    if "investment_horizon" in missing_mandatory:
        clarifications.append("How long are you planning to stay invested (e.g., 3 years, 5 years)?")
    if "investment_amount" in missing_mandatory:
        clarifications.append("How much capital do you plan to invest initially or per month?")
    if "risk_preference" in missing_mandatory:
        clarifications.append("What is your comfort level with market volatility (Conservative, Moderate, or Growth)?")
    if contradictions:
        clarifications.append(contradictions[0].suggested_tradeoff_resolution)

    # Fiduciary audit notes
    audit_notes = []
    if capital_details.initial_lump_sum:
        audit_notes.append(f"Identified capital: ₹{capital_details.initial_lump_sum:,.0f} (Lump-Sum contribution).")
    elif capital_details.monthly_contribution:
        audit_notes.append(f"Identified recurring SIP contribution: ₹{capital_details.monthly_contribution:,.0f} per month.")

    if horizon_months:
        audit_notes.append(f"Target horizon: {horizon_months} months ({round(horizon_months / 12, 1)} years).")
    else:
        audit_notes.append("Notice: Investment horizon not explicitly stated; requires investor clarification.")

    audit_notes.append(f"Assessed Risk Tier: {risk_tier.value.upper()} ({target_vol}% Target Volatility corridor).")
    audit_notes.extend(fiduciary_safeguards)

    if pref_sec:
        audit_notes.append(f"Recognized sector preferences: {', '.join(pref_sec)}.")
    if excl_sec:
        audit_notes.append(f"Active negative sector exclusions: {', '.join(excl_sec)}.")
    if soft_limits:
        audit_notes.append(f"Soft exposure limits noted: {', '.join(soft_limits)}.")
    if preferred_securities:
        pref_names = [f"{p.company_name} ({p.resolved_symbol})" for p in preferred_securities]
        audit_notes.append(f"Preferred equities identified: {', '.join(pref_names)}.")
    if sector_constraints:
        sc_descs = [f"{sc.sector} {sc.operator} {sc.value}{sc.unit}" for sc in sector_constraints]
        audit_notes.append(f"Quantitative sector exposure constraints: {', '.join(sc_descs)}.")
    if existing_holdings:
        syms = [h.symbol for h in existing_holdings]
        audit_notes.append(f"Existing holdings identified for separate portfolio diagnosis: {', '.join(syms)}.")

    is_ready = (len(missing_mandatory) == 0 and len(contradictions) == 0)

    profile = StructuredInvestorProfile(
        portfolio_name=f"AI {risk_tier.value.capitalize()} Equity Basket",
        capital=capital_details,
        horizon_months=horizon_months,
        horizon_years=horizon_years,
        horizon_category=h_cat,
        goals=goals,
        risk=risk_details,
        preferences=preferences,
        experience=experience,
        existing_holdings=existing_holdings,
        cleaned_user_prompt=text.strip(),
        is_ready_for_recommendation=is_ready,
        missing_mandatory_fields=missing_mandatory,
        contradictions=contradictions,
        clarification_questions=clarifications,
        fiduciary_audit_notes=audit_notes,
        field_evidence=field_evidence,
        extraction_method="dynamic_heuristic_nlp_extractor",
        confidence_score=0.90 if is_ready else 0.75,
    )

    return profile


def extract_investor_profile_nlp(text: str, db: Optional[Session] = None) -> StructuredInvestorProfile:
    """
    Main extraction pipeline:
    1. Runs Gemini 3.8 Flash structured reasoning with structured JSON prompt.
    2. Falls back gracefully to deterministic rule extractor upon rate limit, timeout, or failure.
    3. Maps extracted profile to active PostgreSQL RiskQuestion and RiskQuestionOption UUIDs.
    """
    if not text or len(text.strip()) < 3:
        raise ValueError("Natural language description must contain at least 3 characters.")

    llm = get_llm()
    profile = None

    if llm:
        try:
            from langchain_core.messages import SystemMessage, HumanMessage

            prompt = (
                "You are an expert SEBI-registered fiduciary financial adviser in India.\n"
                "Extract structured investor information from the user statement into valid JSON with this exact schema:\n"
                "{\n"
                '  "initial_lump_sum": float or null,\n'
                '  "monthly_contribution": float or null,\n'
                '  "contribution_type": "LUMP_SUM" | "MONTHLY_SIP" | "BOTH" | "NOT_SPECIFIED",\n'
                '  "horizon_months": int or null,\n'
                '  "stated_risk_tolerance": string or null,\n'
                '  "risk_category": "very_conservative" | "conservative" | "moderate" | "growth" | "aggressive",\n'
                '  "emergency_fund_status": "full" | "partial" | "none" | "unspecified",\n'
                '  "experience_level": "beginner" | "intermediate" | "experienced",\n'
                '  "knowledge_level": "basic" | "intermediate" | "advanced",\n'
                '  "goals": [{"goal_name": string, "goal_type": string, "horizon_months": int or null}],\n'
                '  "preferred_sectors": [string],\n'
                '  "excluded_sectors": [string],\n'
                '  "company_characteristics": [string],\n'
                '  "existing_holdings": [{"symbol": string, "company_name": string}],\n'
                '  "has_contradiction": bool,\n'
                '  "contradiction_notes": string or null\n'
                "}\n"
                "Rules:\n"
                "1. If user says '10k every month', set monthly_contribution=10000 and contribution_type='MONTHLY_SIP' (NOT lump sum).\n"
                "2. If user mentions 'no emergency fund', risk_category MUST NOT exceed 'conservative'.\n"
                "3. If user wants high returns with zero risk, set has_contradiction=true.\n"
                "4. Distinguish age (e.g. 30 years old) from investment horizon (5 years).\n"
            )

            resp = llm.invoke([
                SystemMessage(content=prompt),
                HumanMessage(content=f"Investor Text:\n'''{text}'''"),
            ])
            raw = resp.content if hasattr(resp, "content") else str(resp)
            clean_json = raw.strip()
            if clean_json.startswith("```"):
                clean_json = re.sub(r"^```(?:json)?\n?", "", clean_json)
                clean_json = re.sub(r"\n?```$", "", clean_json)

            data = json.loads(clean_json)

            # Build profile from model output using deterministic engine as validation backbone
            det_profile = deterministic_extract_investor_profile(text)

            # Apply model overrides where valid
            if data.get("initial_lump_sum") is not None:
                det_profile.capital.initial_lump_sum = float(data["initial_lump_sum"])
                det_profile.capital.contribution_type = ContributionType.LUMP_SUM
            if data.get("monthly_contribution") is not None:
                det_profile.capital.monthly_contribution = float(data["monthly_contribution"])
                det_profile.capital.contribution_type = ContributionType.MONTHLY_SIP

            if data.get("horizon_months") is not None:
                det_profile.horizon_months = int(data["horizon_months"])
                det_profile.horizon_years = round(int(data["horizon_months"]) / 12, 1)

            if data.get("preferred_sectors"):
                norm_pref = [CANONICAL_SECTORS.get(s.lower().strip(), s.strip()) for s in data["preferred_sectors"] if s]
                if norm_pref:
                    det_profile.preferences.preferred_sectors = sorted(list(set(norm_pref)))
                    if "preferred_sectors" in det_profile.field_evidence:
                        det_profile.field_evidence["preferred_sectors"].value = det_profile.preferences.preferred_sectors

            if data.get("excluded_sectors"):
                norm_excl = [CANONICAL_SECTORS.get(s.lower().strip(), s.strip()) for s in data["excluded_sectors"] if s]
                if norm_excl:
                    det_profile.preferences.excluded_sectors = sorted(list(set(norm_excl)))
                    if "excluded_sectors" in det_profile.field_evidence:
                        det_profile.field_evidence["excluded_sectors"].value = det_profile.preferences.excluded_sectors

            if data.get("risk_category"):
                rc_str = str(data["risk_category"]).lower().strip()
                for rc_enum in RiskCategoryEnum:
                    if rc_enum.value == rc_str:
                        det_profile.risk.assessed_risk_category = rc_enum
                        if "risk_preference" in det_profile.field_evidence:
                            det_profile.field_evidence["risk_preference"].value = rc_enum.value
                        break

            if data.get("emergency_fund_status"):
                emg_str = str(data["emergency_fund_status"]).lower().strip()
                if emg_str in ["full", "partial", "none", "unspecified"]:
                    det_profile.risk.emergency_fund_status = emg_str

            if data.get("experience_level"):
                exp_str = str(data["experience_level"]).lower().strip()
                if exp_str in ["beginner", "intermediate", "experienced"]:
                    det_profile.experience.experience_level = exp_str
                    if "investment_experience" in det_profile.field_evidence:
                        det_profile.field_evidence["investment_experience"].value = exp_str

            if data.get("knowledge_level"):
                know_str = str(data["knowledge_level"]).lower().strip()
                if know_str in ["basic", "intermediate", "advanced"]:
                    det_profile.experience.knowledge_level = know_str

            if data.get("goals") and isinstance(data["goals"], list) and len(data["goals"]) > 0:
                parsed_goals = []
                for g in data["goals"]:
                    if isinstance(g, dict) and g.get("goal_name"):
                        g_h = g.get("horizon_months") or det_profile.horizon_months
                        parsed_goals.append(ExtractedGoalItem(
                            goal_name=g["goal_name"],
                            goal_type=g.get("goal_type") or "wealth_creation",
                            horizon_months=g_h,
                            horizon_years=round(g_h / 12, 1) if g_h else None,
                            time_horizon_category=HorizonCategory.LONG_TERM if (g_h and g_h > 36) else HorizonCategory.MEDIUM_TERM,
                            extraction_status=ExtractionStatus.EXPLICIT,
                        ))
                if parsed_goals:
                    det_profile.goals = parsed_goals

            if data.get("has_contradiction"):
                det_profile.contradictions = detect_contradictions(text)

            det_profile.extraction_method = "gemini-3.8-flash"
            profile = det_profile
        except Exception as exc:
            logger.warning(f"LLM extraction error ({exc}); using deterministic extractor.")
            profile = None

    if not profile:
        profile = deterministic_extract_investor_profile(text)

    # Map to database question options if DB session provided
    if db:
        map_profile_to_questionnaire_options(profile, db)

    return profile


def map_profile_to_questionnaire_options(profile: StructuredInvestorProfile, db: Session):
    """
    Translates structured investor profile into exact RiskQuestion and RiskQuestionOption UUIDs.
    """
    mapped_answers: List[MappedQuestionnaireAnswerItem] = []
    active_questions = db.query(RiskQuestion).filter(RiskQuestion.is_active == True).all()

    # Determine target option codes
    target_codes: Dict[str, str] = {}

    # 1. Horizon
    h = profile.horizon_months or 60
    if h < 12:
        target_codes["INVESTMENT_HORIZON"] = "HORIZON_LESS_1YR"
    elif h <= 36:
        target_codes["INVESTMENT_HORIZON"] = "HORIZON_1_3YR"
    elif h <= 60:
        target_codes["INVESTMENT_HORIZON"] = "HORIZON_3_5YR"
    else:
        target_codes["INVESTMENT_HORIZON"] = "HORIZON_5PLUS"

    # 2. Objective
    risk_cat = profile.risk.assessed_risk_category
    if risk_cat == RiskCategoryEnum.VERY_CONSERVATIVE:
        target_codes["PRIMARY_OBJECTIVE"] = "OBJ_CAPITAL_PRESERVATION"
        target_codes["MARKET_DOWNTURN_REACTION"] = "REACT_SELL_ALL"
    elif risk_cat == RiskCategoryEnum.CONSERVATIVE:
        target_codes["PRIMARY_OBJECTIVE"] = "OBJ_INCOME"
        target_codes["MARKET_DOWNTURN_REACTION"] = "REACT_SELL_SOME"
    elif risk_cat == RiskCategoryEnum.MODERATE:
        target_codes["PRIMARY_OBJECTIVE"] = "OBJ_BALANCED_GROWTH"
        target_codes["MARKET_DOWNTURN_REACTION"] = "REACT_HOLD"
    elif risk_cat in [RiskCategoryEnum.GROWTH, RiskCategoryEnum.AGGRESSIVE]:
        target_codes["PRIMARY_OBJECTIVE"] = "OBJ_MAX_APPRECIATION"
        target_codes["MARKET_DOWNTURN_REACTION"] = "REACT_BUY_MORE" if risk_cat == RiskCategoryEnum.AGGRESSIVE else "REACT_HOLD"

    # 3. Experience
    exp = profile.experience.experience_level
    if exp == "experienced":
        target_codes["INVESTMENT_KNOWLEDGE"] = "EXP_DIRECT_EQUITY"
    elif exp == "intermediate":
        target_codes["INVESTMENT_KNOWLEDGE"] = "EXP_MUTUAL_FUNDS"
    else:
        target_codes["INVESTMENT_KNOWLEDGE"] = "EXP_NONE"

    # 4. Emergency fund
    emg = profile.risk.emergency_fund_status
    if emg == "none":
        target_codes["EMERGENCY_FUND_BUFFER"] = "EMERGENCY_NO"
    elif emg == "partial":
        target_codes["EMERGENCY_FUND_BUFFER"] = "EMERGENCY_PARTIAL"
    else:
        target_codes["EMERGENCY_FUND_BUFFER"] = "EMERGENCY_FULL"

    for q in active_questions:
        tgt_code = target_codes.get(q.question_code)
        selected_opt = None
        if tgt_code:
            selected_opt = next((o for o in q.options if o.option_code == tgt_code), None)
        if not selected_opt and q.options:
            selected_opt = q.options[len(q.options) // 2]

        if selected_opt:
            mapped_answers.append(MappedQuestionnaireAnswerItem(
                question_id=str(q.question_id),
                question_code=q.question_code,
                question_text=q.question_text,
                selected_option_id=str(selected_opt.option_id),
                selected_option_code=selected_opt.option_code,
                selected_option_label=selected_opt.option_label,
                score=float(selected_opt.score) if selected_opt.score is not None else 50.0,
                mapped_from_field=q.question_code.lower(),
                extraction_status=ExtractionStatus.NORMALIZED_FROM_TEXT,
            ))

    profile.mapped_questionnaire_answers = mapped_answers


def merge_profile_with_extracted_data(
    existing_profile: Dict[str, Any],
    new_extracted: StructuredInvestorProfile,
    manual_overrides: bool = False,
) -> StructuredInvestorProfile:
    """
    Combines existing manually entered questionnaire inputs with newly extracted conversational data.
    Preserves user-confirmed values and merges non-conflicting new fields.
    If manual_overrides=True, values in existing_profile take precedence over extracted values.
    """
    merged = new_extracted.model_copy(deep=True)

    # 1. Capital preservation / override
    if existing_profile.get("investment_amount"):
        if manual_overrides or not merged.capital.initial_lump_sum:
            merged.capital.initial_lump_sum = float(existing_profile["investment_amount"])
            merged.capital.contribution_type = ContributionType.LUMP_SUM
            merged.field_evidence["investment_amount"] = ExtractedFieldMeta(
                field_name="investment_amount",
                value=merged.capital.initial_lump_sum,
                data_type="number",
                extraction_status=ExtractionStatus.EXPLICIT,
                user_confirmed=True,
            )

    # 2. Horizon preservation / override
    if existing_profile.get("horizon_months"):
        if manual_overrides or not merged.horizon_months:
            merged.horizon_months = int(existing_profile["horizon_months"])
            merged.horizon_years = round(merged.horizon_months / 12, 1)
            merged.field_evidence["investment_horizon"] = ExtractedFieldMeta(
                field_name="investment_horizon",
                value=merged.horizon_months,
                data_type="integer",
                extraction_status=ExtractionStatus.EXPLICIT,
                user_confirmed=True,
            )

    # 3. Risk category override / preservation
    if existing_profile.get("risk_category"):
        raw_risk = str(existing_profile["risk_category"]).lower()
        for r_enum in RiskCategoryEnum:
            if r_enum.value == raw_risk:
                if manual_overrides or merged.risk.assessed_risk_category == RiskCategoryEnum.MODERATE:
                    merged.risk.assessed_risk_category = r_enum
                    vol_map = {
                        RiskCategoryEnum.VERY_CONSERVATIVE: 8.0,
                        RiskCategoryEnum.CONSERVATIVE: 10.0,
                        RiskCategoryEnum.MODERATE: 12.5,
                        RiskCategoryEnum.GROWTH: 15.0,
                        RiskCategoryEnum.AGGRESSIVE: 18.0,
                    }
                    merged.risk.target_volatility_pct = vol_map.get(r_enum, 12.5)
                    merged.field_evidence["risk_preference"] = ExtractedFieldMeta(
                        field_name="risk_preference",
                        value=r_enum.value,
                        data_type="string",
                        extraction_status=ExtractionStatus.EXPLICIT,
                        user_confirmed=True,
                    )
                break

    # 4. Sector preferences & exclusions merging
    existing_excluded = existing_profile.get("excluded_sectors") or []
    all_excluded = list(set(existing_excluded + merged.preferences.excluded_sectors))
    merged.preferences.excluded_sectors = sorted(all_excluded)

    existing_preferred = existing_profile.get("preferred_sectors") or []
    all_preferred = list(set(existing_preferred + merged.preferences.preferred_sectors))
    merged.preferences.preferred_sectors = sorted(all_preferred)

    # 5. Experience override / preservation
    if existing_profile.get("experience_level"):
        if manual_overrides or merged.experience.experience_level == "unspecified":
            merged.experience.experience_level = str(existing_profile["experience_level"])
            merged.field_evidence["investment_experience"] = ExtractedFieldMeta(
                field_name="investment_experience",
                value=merged.experience.experience_level,
                data_type="string",
                extraction_status=ExtractionStatus.EXPLICIT,
                user_confirmed=True,
            )

    return merged
