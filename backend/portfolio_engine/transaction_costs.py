"""
Indian Equity Capital Markets Transaction Cost Engine for Lucid Platform.
Authoritative source-verified calculation of statutory, exchange, and broker-related transaction costs
under SEBI circulars, Finance Acts, Indian Stamp Act, and exchange tariff schedules.

Statutory and Regulatory References:
1. STT (Securities Transaction Tax):
   - Finance (No. 2) Act, 2004 read with Finance Act, 2024.
   - Delivery Equity BUY: 0.10% (0.001) on purchase value.
   - Delivery Equity SELL: 0.10% (0.001) on sale value.
2. Exchange Transaction Charges (Uniform 'True-to-Label' Schedule):
   - Mandated by SEBI Circular SEBI/HO/MRD/MRD-PoD-1/P/CIR/2024/90 dated July 1, 2024.
   - Effective Date: October 1, 2024.
   - NSE Cash Market (Equities): ₹2.97 per lakh of traded value (0.00297%).
   - BSE Cash Market (Group A & B Equities): ₹3.75 per lakh of traded value (0.00375%).
3. SEBI Turnover Fees:
   - SEBI (Stock Brokers) Regulations, 1992, Schedule IV (as amended).
   - Flat ₹10 per crore of turnover (0.0001% or 0.000001).
4. Stamp Duty (Uniform National Duty):
   - Indian Stamp Act, 1899 (Part I of Chapter IV, Finance Act, 2019).
   - Effective Date: July 1, 2020.
   - Delivery Equity BUY: 0.015% (0.00015) on purchase value.
   - Delivery Equity SELL: 0.000% (NIL on seller).
5. GST (Goods & Services Tax):
   - Integrated / Central & State GST Act, 2017: 18% on financial services.
   - Levied strictly on: Brokerage + Exchange Transaction Charges + SEBI Turnover Fees.
   - Sovereign taxes (STT and Stamp Duty) are exempt from GST.
6. Brokerage & Depository Participant (DP) Charges:
   - Brokerage is broker-specific and commercial, NEVER a statutory charge.
   - DP charges apply per scrip debited on delivery SELL (CDSL/NSDL charge ~₹13.50 + GST = ₹15.93).
"""

from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ExchangeCode(str, Enum):
    NSE = "NSE"
    BSE = "BSE"


class TransactionSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class BrokerageModel(str, Enum):
    ZERO_DELIVERY = "ZERO_DELIVERY"                # e.g., Zerodha, Angel One equity delivery
    FLAT_PER_ORDER = "FLAT_PER_ORDER"              # e.g., Flat ₹20 per executed trade
    DISCOUNT_CAPPED = "DISCOUNT_CAPPED"            # e.g., Groww: min(₹20, 0.05%)
    PERCENTAGE_FULL_SERVICE = "PERCENTAGE_FULL_SERVICE" # e.g., 0.15% or 0.25%


class BrokerProfile(BaseModel):
    broker_id: str
    broker_name: str
    model: BrokerageModel
    flat_rate_per_order: Decimal = Decimal("20.00")
    percentage_rate: Decimal = Decimal("0.0005") # 0.05%
    max_cap_per_order: Decimal = Decimal("20.00")
    dp_charge_per_sell_scrip: Decimal = Decimal("15.93") # Standard CDSL/NSDL + GST
    is_statutory: bool = False
    notes: str = ""


# Standard Pre-Configured Broker Tariff Profiles
DEFAULT_BROKER_PROFILES: Dict[str, BrokerProfile] = {
    "zerodha": BrokerProfile(
        broker_id="zerodha",
        broker_name="Zerodha (Discount Broker)",
        model=BrokerageModel.ZERO_DELIVERY,
        flat_rate_per_order=Decimal("0.00"),
        dp_charge_per_sell_scrip=Decimal("15.93"),
        notes="₹0 delivery brokerage on NSE/BSE. ₹15.93 DP charge per scrip debited on sell.",
    ),
    "groww": BrokerProfile(
        broker_id="groww",
        broker_name="Groww (Discount Broker)",
        model=BrokerageModel.DISCOUNT_CAPPED,
        percentage_rate=Decimal("0.0005"), # 0.05%
        max_cap_per_order=Decimal("20.00"), # max ₹20
        dp_charge_per_sell_scrip=Decimal("15.93"),
        notes="0.05% or ₹20 (whichever is lower) per executed delivery order.",
    ),
    "flat_20": BrokerProfile(
        broker_id="flat_20",
        broker_name="Standard Flat Rate Broker",
        model=BrokerageModel.FLAT_PER_ORDER,
        flat_rate_per_order=Decimal("20.00"),
        dp_charge_per_sell_scrip=Decimal("15.93"),
        notes="Standard estimate of flat ₹20 per executed trade.",
    ),
    "full_service": BrokerProfile(
        broker_id="full_service",
        broker_name="Traditional Full-Service Broker",
        model=BrokerageModel.PERCENTAGE_FULL_SERVICE,
        percentage_rate=Decimal("0.0015"), # 0.15%
        max_cap_per_order=Decimal("500.00"),
        dp_charge_per_sell_scrip=Decimal("25.00"),
        notes="0.15% delivery brokerage with higher DP transaction debit fee.",
    ),
}

# Statutory Fee Schedule (Authoritative Constants)
STT_RATE_DELIVERY_BUY = Decimal("0.001")          # 0.10%
STT_RATE_DELIVERY_SELL = Decimal("0.001")         # 0.10%

NSE_TRANSACTION_CHARGE_RATE = Decimal("0.0000297") # ₹2.97 per lakh = 0.00297% (SEBI true-to-label Oct 2024)
BSE_TRANSACTION_CHARGE_RATE = Decimal("0.0000375") # ₹3.75 per lakh = 0.00375% (Group A & B Equities Oct 2024)

SEBI_TURNOVER_FEE_RATE = Decimal("0.000001")       # ₹10 per crore = 0.0001% (SEBI Stock Broker Regs)
STAMP_DUTY_BUY_RATE = Decimal("0.00015")           # 0.015% on BUY delivery only (Indian Stamp Act)
STAMP_DUTY_SELL_RATE = Decimal("0.00000")          # 0% on SELL

GST_RATE = Decimal("0.18")                         # 18% on financial services


def _round2(val: Decimal) -> Decimal:
    """Rounds a decimal value strictly to 2 decimal places using standard half-up rounding."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ItemizedTradeCost(BaseModel):
    symbol: str
    action: str
    quantity: int
    price: float
    trade_value: float
    exchange: str
    stt: float
    exchange_charges: float
    sebi_charges: float
    stamp_duty: float
    brokerage: float
    dp_charges: float
    gst: float
    total_costs: float


class TransactionCostBreakdown(BaseModel):
    # Turnovers
    buy_turnover: float
    sell_turnover: float
    total_turnover: float

    # Category A: Statutory Charges
    stt: float
    stamp_duty: float
    sebi_charges: float
    statutory_subtotal: float

    # Category B: Exchange Charges
    exchange_code: str
    exchange_charges: float
    exchange_rate_pct: float
    exchange_subtotal: float

    # Category C: Broker-Related Charges
    broker_id: str
    broker_name: str
    brokerage: float
    dp_charges: float
    broker_subtotal: float

    # GST on eligible components (Brokerage + Exchange Charges + SEBI Charges)
    gst_taxable_base: float
    gst: float

    # Totals
    total_estimated_costs: float
    effective_cost_bps: float

    # Net Cash Impact
    gross_trade_value: float
    net_cash_impact: float # Sell proceeds - Buy consideration - Total costs

    # Disclosures & Line Items
    is_estimate: bool = True
    disclosures: List[str] = Field(default_factory=list)
    trades: List[ItemizedTradeCost] = Field(default_factory=list)


class TransactionCostEngine:
    """Computes exact, broker-aware, exchange-aware equity transaction costs."""

    @classmethod
    def calculate_transaction_costs(
        cls,
        trades: List[Dict[str, Any]],
        exchange: ExchangeCode = ExchangeCode.NSE,
        broker_profile: Optional[BrokerProfile] = None,
        include_dp_charges: bool = True,
    ) -> TransactionCostBreakdown:
        """
        Calculates itemized and aggregate Indian equity transaction costs across statutory,
        exchange, and broker charge categories.
        """
        profile = broker_profile or DEFAULT_BROKER_PROFILES["flat_20"]

        d_buy_turnover = Decimal("0.00")
        d_sell_turnover = Decimal("0.00")
        d_stt = Decimal("0.00")
        d_stamp_duty = Decimal("0.00")
        d_exchange_charges = Decimal("0.00")
        d_sebi_charges = Decimal("0.00")
        d_brokerage = Decimal("0.00")
        d_dp_charges = Decimal("0.00")

        # Exchange rate selection
        if exchange == ExchangeCode.BSE:
            exch_rate = BSE_TRANSACTION_CHARGE_RATE
            exch_rate_pct = 0.00375
            exch_label = "BSE"
        else:
            exch_rate = NSE_TRANSACTION_CHARGE_RATE
            exch_rate_pct = 0.00297
            exch_label = "NSE"

        trade_line_items: List[ItemizedTradeCost] = []
        sell_symbols_seen = set()

        for t in trades:
            action = str(t.get("action", "")).upper()
            if action not in ("BUY", "SELL"):
                continue

            sym = str(t.get("symbol", "UNKNOWN")).upper()
            qty = abs(int(t.get("trade_quantity", t.get("quantity_change", 0))))
            if qty == 0:
                continue

            price = Decimal(str(t.get("latest_price", t.get("reference_price", 0.0))))
            if price <= 0:
                continue

            trade_val = Decimal(str(t.get("trade_value", 0.0)))
            if trade_val <= 0:
                trade_val = Decimal(qty) * price

            # Per-trade cost components
            t_stt = Decimal("0.00")
            t_stamp = Decimal("0.00")
            t_exch = trade_val * exch_rate
            t_sebi = trade_val * SEBI_TURNOVER_FEE_RATE
            t_brokerage = Decimal("0.00")
            t_dp = Decimal("0.00")

            if action == "BUY":
                d_buy_turnover += trade_val
                t_stt = trade_val * STT_RATE_DELIVERY_BUY
                t_stamp = trade_val * STAMP_DUTY_BUY_RATE

                # Brokerage on BUY
                if profile.model == BrokerageModel.ZERO_DELIVERY:
                    t_brokerage = Decimal("0.00")
                elif profile.model == BrokerageModel.FLAT_PER_ORDER:
                    t_brokerage = profile.flat_rate_per_order
                elif profile.model == BrokerageModel.DISCOUNT_CAPPED:
                    t_brokerage = min(trade_val * profile.percentage_rate, profile.max_cap_per_order)
                elif profile.model == BrokerageModel.PERCENTAGE_FULL_SERVICE:
                    t_brokerage = min(trade_val * profile.percentage_rate, profile.max_cap_per_order)

            elif action == "SELL":
                d_sell_turnover += trade_val
                t_stt = trade_val * STT_RATE_DELIVERY_SELL
                t_stamp = Decimal("0.00") # No stamp duty on sell

                # Brokerage on SELL
                if profile.model == BrokerageModel.ZERO_DELIVERY:
                    t_brokerage = Decimal("0.00")
                elif profile.model == BrokerageModel.FLAT_PER_ORDER:
                    t_brokerage = profile.flat_rate_per_order
                elif profile.model == BrokerageModel.DISCOUNT_CAPPED:
                    t_brokerage = min(trade_val * profile.percentage_rate, profile.max_cap_per_order)
                elif profile.model == BrokerageModel.PERCENTAGE_FULL_SERVICE:
                    t_brokerage = min(trade_val * profile.percentage_rate, profile.max_cap_per_order)

                # DP charge applies once per scrip debited per day
                if include_dp_charges and sym not in sell_symbols_seen:
                    t_dp = profile.dp_charge_per_sell_scrip
                    sell_symbols_seen.add(sym)

            # GST on taxable financial services for this trade
            t_taxable_base = t_brokerage + t_exch + t_sebi
            t_gst = t_taxable_base * GST_RATE
            t_total = t_stt + t_stamp + t_exch + t_sebi + t_brokerage + t_dp + t_gst

            # Accumulate aggregates
            d_stt += t_stt
            d_stamp_duty += t_stamp
            d_exchange_charges += t_exch
            d_sebi_charges += t_sebi
            d_brokerage += t_brokerage
            d_dp_charges += t_dp

            trade_line_items.append(
                ItemizedTradeCost(
                    symbol=sym,
                    action=action,
                    quantity=qty,
                    price=float(_round2(price)),
                    trade_value=float(_round2(trade_val)),
                    exchange=exch_label,
                    stt=float(_round2(t_stt)),
                    exchange_charges=float(_round2(t_exch)),
                    sebi_charges=float(_round2(t_sebi)),
                    stamp_duty=float(_round2(t_stamp)),
                    brokerage=float(_round2(t_brokerage)),
                    dp_charges=float(_round2(t_dp)),
                    gst=float(_round2(t_gst)),
                    total_costs=float(_round2(t_total)),
                )
            )

        d_total_turnover = d_buy_turnover + d_sell_turnover

        # Round all aggregates with high financial precision
        r_buy_turnover = _round2(d_buy_turnover)
        r_sell_turnover = _round2(d_sell_turnover)
        r_total_turnover = _round2(d_total_turnover)

        r_stt = _round2(d_stt)
        r_stamp_duty = _round2(d_stamp_duty)
        r_exchange_charges = _round2(d_exchange_charges)
        r_sebi_charges = _round2(d_sebi_charges)
        r_brokerage = _round2(d_brokerage)
        r_dp_charges = _round2(d_dp_charges)

        # Taxable base for GST: Brokerage + Exchange Charges + SEBI Charges
        d_gst_base = r_brokerage + r_exchange_charges + r_sebi_charges
        r_gst = _round2(d_gst_base * GST_RATE)

        # Category subtotals
        r_statutory_subtotal = _round2(r_stt + r_stamp_duty + r_sebi_charges)
        r_exchange_subtotal = r_exchange_charges
        r_broker_subtotal = _round2(r_brokerage + r_dp_charges)

        r_total_costs = _round2(
            r_statutory_subtotal + r_exchange_subtotal + r_broker_subtotal + r_gst
        )

        effective_bps = (
            _round2((r_total_costs / r_total_turnover) * Decimal("10000.0"))
            if r_total_turnover > 0
            else Decimal("0.00")
        )

        # Net cash impact: Sell consideration - Buy consideration - Total transaction costs
        d_net_cash_impact = r_sell_turnover - r_buy_turnover - r_total_costs

        disclosures = [
            f"Statutory STT (0.10% delivery BUY & SELL) computed under Finance Act, 2024.",
            f"Exchange transaction charges ({exch_rate_pct:.5f}%) reflect {exch_label} circular effective October 1, 2024 (SEBI 'True to Label' circular CIR/2024/90).",
            f"Stamp Duty (0.015% on BUY) computed under Indian Stamp Act (amended July 1, 2020).",
            f"SEBI turnover fee (₹10/crore = 0.0001%) computed under SEBI (Stock Brokers) Regulations, 1992.",
            f"GST (18%) levied strictly on brokerage, exchange charges, and SEBI fee; sovereign taxes are exempt.",
            f"Brokerage based on selected profile: {profile.broker_name}. Actual broker tariffs may vary.",
        ]
        if include_dp_charges and d_sell_turnover > 0:
            disclosures.append(f"Depository Participant (DP) charges (~₹15.93 per scrip) included for sell transactions.")

        return TransactionCostBreakdown(
            buy_turnover=float(r_buy_turnover),
            sell_turnover=float(r_sell_turnover),
            total_turnover=float(r_total_turnover),
            stt=float(r_stt),
            stamp_duty=float(r_stamp_duty),
            sebi_charges=float(r_sebi_charges),
            statutory_subtotal=float(r_statutory_subtotal),
            exchange_code=exch_label,
            exchange_charges=float(r_exchange_charges),
            exchange_rate_pct=exch_rate_pct,
            exchange_subtotal=float(r_exchange_subtotal),
            broker_id=profile.broker_id,
            broker_name=profile.broker_name,
            brokerage=float(r_brokerage),
            dp_charges=float(r_dp_charges),
            broker_subtotal=float(r_broker_subtotal),
            gst_taxable_base=float(_round2(d_gst_base)),
            gst=float(r_gst),
            total_estimated_costs=float(r_total_costs),
            effective_cost_bps=float(effective_bps),
            gross_trade_value=float(r_total_turnover),
            net_cash_impact=float(_round2(d_net_cash_impact)),
            is_estimate=True,
            disclosures=disclosures,
            trades=trade_line_items,
        )


def estimate_indian_equity_transaction_costs(
    trades: List[Dict[str, Any]],
    exchange: str = "NSE",
    broker_profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Backwards-compatible helper function for existing services and test callers.
    Wraps TransactionCostEngine and returns dictionary compatible with legacy format
    while providing extended statutory, exchange, and broker breakdowns.
    """
    exch_code = ExchangeCode.BSE if str(exchange).upper() == "BSE" else ExchangeCode.NSE
    profile = (
        DEFAULT_BROKER_PROFILES.get(broker_profile_id or "flat_20")
        or DEFAULT_BROKER_PROFILES["flat_20"]
    )
    breakdown = TransactionCostEngine.calculate_transaction_costs(
        trades=trades,
        exchange=exch_code,
        broker_profile=profile,
    )
    res = breakdown.model_dump()
    return res

