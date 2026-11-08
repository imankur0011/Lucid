"""
Production-Grade Financial Number Parser & Semantic Normalizer for Lucid.

Parses natural-language numerical expressions including:
- Indian numbering system (Lakh / Lac / L, Crore / Cr, Thousand / K)
- Western numbering system (Million / M, Billion / B)
- Word-form numbers ("one lakh twenty-five thousand", "two crore fifty lakh")
- Decimal magnitude expressions ("1.5 crore", "2.5 lakh", "75K")
- Indian currency formats ("₹3,50,000", "Rs. 2 lakh", "INR 50,000", "3.5L")
- Comparative operators & ranges ("between 1 lakh and 2 lakh", "not more than 20%", "at least 50 shares")
- Disambiguates semantics: Currency vs Percentages vs Share Quantities vs Horizons.
"""

import re
import math
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Core Numerical Constants and Dictionaries
# ---------------------------------------------------------------------------

ONES: Dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
}

TENS: Dict[str, int] = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}

# Multiplier scales in both Indian and International finance
SCALES: Dict[str, float] = {
    "hundred": 100.0,
    "thousand": 1_000.0,
    "k": 1_000.0,
    "lakh": 100_000.0,
    "lakhs": 100_000.0,
    "lac": 100_000.0,
    "lacs": 100_000.0,
    "l": 100_000.0,
    "million": 1_000_000.0,
    "m": 1_000_000.0,
    "crore": 10_000_000.0,
    "crores": 10_000_000.0,
    "cr": 10_000_000.0,
    "billion": 1_000_000_000.0,
    "b": 1_000_000_000.0,
}

FRACTION_WORDS: Dict[str, float] = {
    "half": 0.5,
    "quarter": 0.25,
    "three-quarters": 0.75,
}

class SemanticUnit(str, Enum):
    INR = "INR"
    PERCENT = "PERCENT"
    SHARES = "SHARES"
    YEARS = "YEARS"
    MONTHS = "MONTHS"
    COUNT = "COUNT"
    RATIO = "RATIO"
    UNKNOWN = "UNKNOWN"

class SemanticType(str, Enum):
    MONETARY_AMOUNT = "MONETARY_AMOUNT"
    PERCENTAGE = "PERCENTAGE"
    SHARE_QUANTITY = "SHARE_QUANTITY"
    INVESTMENT_HORIZON = "INVESTMENT_HORIZON"
    METRIC_RATIO = "METRIC_RATIO"
    GENERIC_NUMBER = "GENERIC_NUMBER"

class ComparisonOperator(str, Enum):
    EQ = "EQ"               # Exact value
    LTE = "LTE"             # Not more than / at most / maximum / capped at
    GTE = "GTE"             # At least / minimum of / not less than
    LT = "LT"               # Less than / strictly under
    GT = "GT"               # More than / strictly above
    BETWEEN = "BETWEEN"     # Range (min_value, max_value)
    APPROX = "APPROX"       # Approximately / around / about
    DELTA_NEGATIVE = "DELTA_NEGATIVE" # Reduce by / minus / down by
    DELTA_POSITIVE = "DELTA_POSITIVE" # Increase by / up by / plus


class ParsedNumericValue(BaseModel):
    raw_text: str
    normalized_value: float
    unit: SemanticUnit = SemanticUnit.UNKNOWN
    semantic_type: SemanticType = SemanticType.GENERIC_NUMBER
    currency: Optional[str] = None
    magnitude: Optional[str] = None
    comparison_operator: ComparisonOperator = ComparisonOperator.EQ
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    confidence: float = 1.0
    source_start: Optional[int] = None
    source_end: Optional[int] = None
    requires_clarification: bool = False
    clarification_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Word-to-Number Mathematical Evaluator
# ---------------------------------------------------------------------------

def words_to_number(text: str) -> Optional[float]:
    """
    Parses complex natural-language word numbers like:
    - 'one lakh twenty-five thousand' -> 125,000
    - 'two crore fifty lakh' -> 25,000,000
    - 'three hundred and fifty' -> 350
    - 'forty-two' -> 42
    - 'one point five lakh' -> 150,000
    - 'two point five crores' -> 25,000,000
    """
    clean = text.lower().strip().replace("-", " ").replace(" and ", " ")
    if clean in FRACTION_WORDS:
        return FRACTION_WORDS[clean]

    tokens = clean.split()
    if not tokens:
        return None

    # Handle direct decimal phrases like "one point five lakh" or "two point five crores"
    if "point" in tokens:
        pt_idx = tokens.index("point")
        whole_part_words = " ".join(tokens[:pt_idx])
        dec_part_tokens = tokens[pt_idx + 1:]

        multiplier = 1.0
        dec_digits = []
        for dt in dec_part_tokens:
            dt_clean = dt.rstrip(".,;")
            if dt_clean in ["lakh", "lakhs", "lac", "lacs"]:
                multiplier *= 100_000.0
            elif dt_clean in ["crore", "crores", "cr"]:
                multiplier *= 10_000_000.0
            elif dt_clean in ["thousand", "k"]:
                multiplier *= 1_000.0
            elif dt_clean in ["million", "m"]:
                multiplier *= 1_000_000.0
            elif dt_clean in ["billion", "b"]:
                multiplier *= 1_000_000_000.0
            elif dt_clean in ONES:
                dec_digits.append(str(ONES[dt_clean]))
            elif dt_clean.isdigit():
                dec_digits.append(dt_clean)

        whole_val = words_to_number(whole_part_words) if whole_part_words else 0.0
        if whole_val is not None and dec_digits:
            base_dec = float(f"{int(whole_val)}.{''.join(dec_digits)}")
            return base_dec * multiplier

    total = 0.0
    current = 0.0
    found_any = False

    for token in tokens:
        token = token.rstrip(".,;")
        if token in ONES:
            current += ONES[token]
            found_any = True
        elif token in TENS:
            current += TENS[token]
            found_any = True
        elif token == "hundred":
            current = (current if current != 0 else 1.0) * 100.0
            found_any = True
        elif token in ["thousand", "k"]:
            current = (current if current != 0 else 1.0) * 1_000.0
            total += current
            current = 0.0
            found_any = True
        elif token in ["lakh", "lakhs", "lac", "lacs"]:
            current = (current if current != 0 else 1.0) * 100_000.0
            total += current
            current = 0.0
            found_any = True
        elif token in ["million", "m"]:
            current = (current if current != 0 else 1.0) * 1_000_000.0
            total += current
            current = 0.0
            found_any = True
        elif token in ["crore", "crores", "cr"]:
            current = (current if current != 0 else 1.0) * 10_000_000.0
            total += current
            current = 0.0
            found_any = True
        elif token in ["billion", "b"]:
            current = (current if current != 0 else 1.0) * 1_000_000_000.0
            total += current
            current = 0.0
            found_any = True
        elif token.isdigit():
            current += float(token)
            found_any = True
        else:
            try:
                num = float(token)
                current += num
                found_any = True
            except ValueError:
                pass

    if not found_any:
        return None

    return total + current


# ---------------------------------------------------------------------------
# Comprehensive Financial Expression Normalizer
# ---------------------------------------------------------------------------

class FinancialNumberParser:
    """
    Context-aware financial number parser for Indian and global retail fintech.
    """

    # Currency indicators
    CURRENCY_REGEX = re.compile(r'(?:₹|rs\.?|inr|rupees?|bucks?)', re.IGNORECASE)

    # Percentage indicators - Note: % does not have word boundary \b
    PERCENT_REGEX = re.compile(r'(?:%|\b(?:percent|percentage|pct|basis\s+points?|bps)\b)', re.IGNORECASE)

    # Share quantity indicators
    SHARE_REGEX = re.compile(r'\b(?:shares?|stocks?|units?|lots?|equities)\b', re.IGNORECASE)

    # Horizon indicators
    YEAR_REGEX = re.compile(r'\b(?:years?|yrs?|yr)\b', re.IGNORECASE)
    MONTH_REGEX = re.compile(r'\b(?:months?|mos?|mo)\b', re.IGNORECASE)

    # Comparison Operator Regex
    BETWEEN_REGEX = re.compile(
        r'\bbetween\s+([₹\w\.\,\s]+?)\s+and\s+([₹\w\.\,\s]+)',
        re.IGNORECASE,
    )
    LTE_REGEX = re.compile(
        r'\b(?:(?:do\s+not|don\'t|not|never|no)\s+(?:\w+\s+)?(?:more\s+than|exceed|exceeding)|at\s+most|maximum\s+(?:of\s+)?|max\s+|capped\s+at|less\s+than\s+or\s+equal\s+to|no\s+more\s+than|up\s+to|ceiling\s+of)\s+([₹\w\.\,\s%]+)',
        re.IGNORECASE,
    )
    GTE_REGEX = re.compile(
        r'\b(?:(?:do\s+not|don\'t|not|never|no)\s+(?:\w+\s+)?(?:less\s+than|under|below)|at\s+least|minimum\s+(?:of\s+)?|min\s+|greater\s+than\s+or\s+equal\s+to|not\s+less\s+than|floor\s+of)\s+([₹\w\.\,\s%]+)',
        re.IGNORECASE,
    )
    LT_REGEX = re.compile(r'\b(?:less\s+than|under|below|strictly\s+less\s+than)\s+([₹\w\.\,\s%]+)', re.IGNORECASE)
    GT_REGEX = re.compile(r'\b(?:more\s+than|over|above|exceeding)\s+([₹\w\.\,\s%]+)', re.IGNORECASE)
    APPROX_REGEX = re.compile(r'\b(?:approx(?:imately)?|around|about|nearly)\s+([₹\w\.\,\s%]+)', re.IGNORECASE)
    DELTA_NEG_REGEX = re.compile(r'\b(?:reduce\s+by|down\s+by|trim\s+by|minus)\s+([₹\w\.\,\s%]+)', re.IGNORECASE)

    def parse_single_magnitude_expression(self, text: str) -> Optional[Tuple[float, Optional[str]]]:
        """
        Parses a standalone or currency-prefixed magnitude expression, e.g.:
        - '2.5 lakh' -> (250000.0, 'Lakh')
        - '1.5 crore' -> (15000000.0, 'Crore')
        - '75k' -> (75000.0, 'Thousand')
        - '25,000' -> (25000.0, None)
        - '₹1,50,00,000' -> (15000000.0, None)
        - 'one lakh twenty-five thousand' -> (125000.0, 'Lakh')
        - '20%' -> (20.0, None)
        """
        clean = text.strip()
        # Remove currency symbols and formatting for mathematical evaluation
        clean_no_curr = self.CURRENCY_REGEX.sub('', clean).strip().replace(',', '')
        clean_no_curr = self.PERCENT_REGEX.sub('', clean_no_curr).strip()
        clean_no_curr = self.SHARE_REGEX.sub('', clean_no_curr).strip()
        clean_no_curr = self.YEAR_REGEX.sub('', clean_no_curr).strip()
        clean_no_curr = self.MONTH_REGEX.sub('', clean_no_curr).strip()

        # Check for direct word numbers first (e.g. 'one lakh twenty-five thousand')
        words_val = words_to_number(clean_no_curr)
        if words_val is not None and not clean_no_curr.replace('.', '').isdigit():
            # Determine magnitude label
            mag = None
            low = clean_no_curr.lower()
            if "crore" in low or "cr" in low:
                mag = "Crore"
            elif "lakh" in low or "lac" in low:
                mag = "Lakh"
            elif "thousand" in low or "k" in low:
                mag = "Thousand"
            elif "million" in low:
                mag = "Million"
            return (words_val, mag)

        # Regex for [number] [scale]
        m = re.match(r'^(\d+(?:\.\d+)?)\s*([a-zA-Z]+)?$', clean_no_curr)
        if m:
            num = float(m.group(1))
            scale_str = (m.group(2) or "").lower()
            if not scale_str:
                return (num, None)
            if scale_str in SCALES:
                multiplier = SCALES[scale_str]
                mag = "Crore" if multiplier >= 10_000_000 else ("Lakh" if multiplier >= 100_000 else ("Thousand" if multiplier >= 1_000 else "Standard"))
                return (num * multiplier, mag)

        # Direct digit parse
        try:
            num = float(clean_no_curr)
            return (num, None)
        except ValueError:
            return None

    def extract_numerical_context(self, raw_text: str, surrounding_text: str = "") -> Tuple[SemanticType, SemanticUnit, Optional[str]]:
        """
        Infers whether a number represents a currency amount, percentage,
        share quantity, or investment horizon.
        """
        combined = f"{raw_text} {surrounding_text}".lower()

        if self.CURRENCY_REGEX.search(combined) or any(w in combined for w in ["invest", "capital", "portfolio", "corpus", "budget", "salary", "fd", "savings", "lump sum", "sip", "deposit"]):
            if not self.SHARE_REGEX.search(raw_text) and not self.PERCENT_REGEX.search(raw_text) and not self.YEAR_REGEX.search(raw_text):
                return (SemanticType.MONETARY_AMOUNT, SemanticUnit.INR, "INR")

        if self.PERCENT_REGEX.search(combined):
            return (SemanticType.PERCENTAGE, SemanticUnit.PERCENT, None)

        if self.SHARE_REGEX.search(combined):
            return (SemanticType.SHARE_QUANTITY, SemanticUnit.SHARES, None)

        if self.YEAR_REGEX.search(combined):
            return (SemanticType.INVESTMENT_HORIZON, SemanticUnit.YEARS, None)

        if self.MONTH_REGEX.search(combined):
            return (SemanticType.INVESTMENT_HORIZON, SemanticUnit.MONTHS, None)

        return (SemanticType.GENERIC_NUMBER, SemanticUnit.UNKNOWN, None)

    def parse_expression(self, text: str) -> Optional[ParsedNumericValue]:
        """
        Main entry point for parsing any financial or quantitative expression.
        Handles comparison operators, ranges, scales, and semantics.
        """
        raw = text.strip()
        if not raw:
            return None

        # 1. Range checking: "between X and Y"
        between_m = self.BETWEEN_REGEX.search(raw)
        if between_m:
            span_a = between_m.group(1).strip()
            span_b = between_m.group(2).strip()
            res_a = self.parse_single_magnitude_expression(span_a)
            res_b = self.parse_single_magnitude_expression(span_b)
            if res_a and res_b:
                val_a = res_a[0]
                val_b = res_b[0]
                # If unit omitted on first operand (e.g. "between 1 and 2 lakh")
                if val_a < 100.0 and val_b >= 100_000.0 and res_b[1] == "Lakh":
                    val_a = val_a * 100_000.0
                elif val_a < 100.0 and val_b >= 10_000_000.0 and res_b[1] == "Crore":
                    val_a = val_a * 10_000_000.0

                min_val = min(val_a, val_b)
                max_val = max(val_a, val_b)
                sem_type, sem_unit, curr = self.extract_numerical_context(raw)
                return ParsedNumericValue(
                    raw_text=raw,
                    normalized_value=min_val,
                    unit=sem_unit,
                    semantic_type=sem_type,
                    currency=curr,
                    magnitude=res_b[1] or res_a[1],
                    comparison_operator=ComparisonOperator.BETWEEN,
                    min_value=min_val,
                    max_value=max_val,
                    confidence=0.98,
                )

        # 2. Operator checking: "not more than X" / "at most X"
        for reg, op in [
            (self.LTE_REGEX, ComparisonOperator.LTE),
            (self.GTE_REGEX, ComparisonOperator.GTE),
            (self.LT_REGEX, ComparisonOperator.LT),
            (self.GT_REGEX, ComparisonOperator.GT),
            (self.APPROX_REGEX, ComparisonOperator.APPROX),
            (self.DELTA_NEG_REGEX, ComparisonOperator.DELTA_NEGATIVE),
        ]:
            m = reg.search(raw)
            if m:
                target_str = m.group(1).strip()
                res = self.parse_single_magnitude_expression(target_str)
                if res:
                    val, mag = res
                    if op == ComparisonOperator.DELTA_NEGATIVE and val > 0:
                        val = -val
                    sem_type, sem_unit, curr = self.extract_numerical_context(raw)
                    return ParsedNumericValue(
                        raw_text=raw,
                        normalized_value=val,
                        unit=sem_unit,
                        semantic_type=sem_type,
                        currency=curr,
                        magnitude=mag,
                        comparison_operator=op,
                        max_value=val if op == ComparisonOperator.LTE else None,
                        min_value=val if op == ComparisonOperator.GTE else None,
                        confidence=0.95,
                    )

        # 3. Standard single value parse
        # If text contains percentage symbol or keyword
        has_percent = bool(self.PERCENT_REGEX.search(raw))
        clean_num_text = self.PERCENT_REGEX.sub('', raw).strip()
        has_shares = bool(self.SHARE_REGEX.search(raw))
        clean_num_text = self.SHARE_REGEX.sub('', clean_num_text).strip()
        has_year = bool(self.YEAR_REGEX.search(raw))
        clean_num_text = self.YEAR_REGEX.sub('', clean_num_text).strip()

        res = self.parse_single_magnitude_expression(clean_num_text)
        if res:
            val, mag = res
            sem_type, sem_unit, curr = self.extract_numerical_context(raw)
            if has_percent:
                sem_type = SemanticType.PERCENTAGE
                sem_unit = SemanticUnit.PERCENT
                curr = None
            elif has_shares:
                sem_type = SemanticType.SHARE_QUANTITY
                sem_unit = SemanticUnit.SHARES
                curr = None
            elif has_year:
                sem_type = SemanticType.INVESTMENT_HORIZON
                sem_unit = SemanticUnit.YEARS
                curr = None

            return ParsedNumericValue(
                raw_text=raw,
                normalized_value=val,
                unit=sem_unit,
                semantic_type=sem_type,
                currency=curr,
                magnitude=mag,
                comparison_operator=ComparisonOperator.EQ,
                confidence=1.0,
            )

        # Fallback words to number
        word_val = words_to_number(raw)
        if word_val is not None:
            sem_type, sem_unit, curr = self.extract_numerical_context(raw)
            return ParsedNumericValue(
                raw_text=raw,
                normalized_value=word_val,
                unit=sem_unit,
                semantic_type=sem_type,
                currency=curr,
                comparison_operator=ComparisonOperator.EQ,
                confidence=0.90,
            )

        return None


# Global singleton instance
financial_number_parser = FinancialNumberParser()
