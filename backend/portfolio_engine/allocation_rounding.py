"""
Allocation Rounding & Integer Share Purchase Engine.
Translates percentage weights into integer-share quantities and computes unallocated cash.
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
import math


def calculate_integer_shares_and_amounts(
    allocations: List[Dict[str, Any]],
    total_investment_amount: Decimal,
) -> Tuple[List[Dict[str, Any]], Decimal, Decimal]:
    """
    Computes exact integer shares, actual invested capital, and unallocated cash.
    Returns: (enriched_allocations, total_invested, unallocated_cash)
    """
    total_invested = Decimal("0.0")
    enriched = []

    for item in allocations:
        weight_pct = Decimal(str(item.get("target_weight_pct", 0.0)))
        target_amt = round((total_investment_amount * weight_pct) / Decimal("100.0"), 2)

        price = Decimal(str(item.get("latest_price", 1.0)))
        if price <= 0:
            price = Decimal("1.0")

        # Floor division to get integer shares
        shares = math.floor(target_amt / price)
        actual_amt = round(Decimal(shares) * price, 2)
        total_invested += actual_amt

        enriched_item = dict(item)
        enriched_item["target_amount"] = target_amt
        enriched_item["shares_quantity"] = int(shares)
        enriched_item["actual_invested_amount"] = actual_amt
        enriched_item["holding_unallocated_cash"] = round(target_amt - actual_amt, 2)
        enriched.append(enriched_item)

    unallocated_cash = round(total_investment_amount - total_invested, 2)
    return enriched, total_invested, unallocated_cash
