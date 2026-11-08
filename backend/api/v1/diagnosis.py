"""
Portfolio Diagnosis, Multi-Source Import (CSV, Manual, Paste), and Rebalancing Preview API Router.
Accepts existing investor investments, diagnoses concentration risks, and provides buy/sell/hold previews.
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import uuid
import csv
import io
import re
from datetime import datetime, date
from pydantic import BaseModel, Field

try:
    from backend.database import get_db
    from backend.auth.dependencies import get_current_user
    from backend.models import (
        AppUser,
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Security,
        InstrumentListing,
        MarketPrice,
    )
    from backend.diagnosis.service import PortfolioDiagnosisService
    from backend.services.account_deletion_service import delete_existing_portfolio
except ImportError:
    from database import get_db
    from auth.dependencies import get_current_user
    from models import (
        AppUser,
        ExistingPortfolio,
        ExistingPortfolioHolding,
        PortfolioDiagnosis,
        RebalanceSuggestion,
        Security,
        InstrumentListing,
        MarketPrice,
    )
    from diagnosis.service import PortfolioDiagnosisService
    from services.account_deletion_service import delete_existing_portfolio

router = APIRouter(prefix="/diagnosis", tags=["Portfolio Diagnosis & Rebalancing"])


class HoldingInput(BaseModel):
    symbol: str
    quantity: float = Field(..., gt=0)
    average_purchase_price: Optional[float] = Field(None, ge=0)


class ExistingPortfolioCreate(BaseModel):
    portfolio_name: str = Field(..., min_length=1, max_length=160)
    source_type: str = Field("manual", pattern="^(manual|file_import|broker_import|copy_paste)$")
    holdings: List[HoldingInput] = Field(..., min_length=1)


class ParsedHoldingPreview(BaseModel):
    row_number: int
    symbol: str
    security_name: str
    exchange: str = "NSE"
    quantity: float
    average_purchase_price: Optional[float] = None
    latest_market_price: float
    current_market_value: float
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    sector_name: str = "General"


class InvalidRowError(BaseModel):
    row_number: int
    raw_symbol: Optional[str] = None
    error: str


class PortfolioImportPreviewResponse(BaseModel):
    status: str
    source_type: str
    filename: Optional[str] = None
    total_rows: int
    valid_count: int
    error_count: int
    can_commit: bool
    total_estimated_value: float
    valid_holdings: List[ParsedHoldingPreview]
    invalid_rows: List[InvalidRowError]


class ParseTextRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_type: str = Field("copy_paste", pattern="^(manual|copy_paste|file_import|broker_import)$")


class RebalanceSuggestionRead(BaseModel):
    security_id: uuid.UUID
    symbol: str
    action: str
    current_quantity: int
    target_quantity: int
    quantity_change: int
    current_value: Decimal
    target_value: Decimal
    change_value: Decimal
    explanation: str
    current_weight_pct: Optional[float] = 0.0
    target_weight_pct: Optional[float] = 0.0
    latest_price: Optional[Decimal] = Decimal("0.0")


class CurrentHoldingDetail(BaseModel):
    symbol: str
    security_name: str
    sector_name: str
    quantity: float
    latest_price: Decimal
    current_value: Decimal
    weight_pct: float
    average_purchase_price: Optional[float] = None
    invested_amount: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None


class DiagnosisDetailRead(BaseModel):
    portfolio_diagnosis_id: uuid.UUID
    existing_portfolio_id: uuid.UUID
    portfolio_name: str
    total_market_value: Decimal
    warnings: List[str]
    current_metrics: Dict[str, Any]
    target_metrics: Dict[str, Any]
    rebalance_turnover_pct: float
    unallocated_cash: Decimal
    suggestions: List[RebalanceSuggestionRead]
    current_holdings: Optional[List[CurrentHoldingDetail]] = None
    rebalance_status: Optional[str] = "rebalance_proposed"
    trades_required_count: Optional[int] = 0
    created_at: datetime


def resolve_listing_and_price(raw_symbol: str, db: Session) -> Optional[Tuple[InstrumentListing, Security, float]]:
    """Normalizes symbol, strips broker/exchange artifacts, and retrieves active listing and closing price."""
    clean_sym = (raw_symbol or "").strip().upper()
    for pfx in ("NSE:", "BSE:"):
        if clean_sym.startswith(pfx):
            clean_sym = clean_sym[len(pfx):].strip()
    for sfx in (".NS", ".BO", ".IN"):
        if clean_sym.endswith(sfx):
            clean_sym = clean_sym[:-len(sfx)].strip()

    listing = (
        db.query(InstrumentListing)
        .filter(
            (InstrumentListing.symbol == clean_sym)
            | (InstrumentListing.symbol == raw_symbol.strip().upper())
        )
        .first()
    )
    if not listing or not listing.security:
        return None

    mp = (
        db.query(MarketPrice)
        .filter(MarketPrice.listing_id == listing.listing_id)
        .order_by(desc(MarketPrice.price_date))
        .first()
    )
    price = float(mp.close_price) if mp else 1000.0
    return listing, listing.security, price


@router.get("/csv-template")
async def download_csv_template():
    """Returns a downloadable CSV template with standard column headers for holdings import."""
    template_content = (
        "symbol,exchange,quantity,average_buy_price,purchase_date\n"
        "RELIANCE,NSE,40,2500.00,2024-01-15\n"
        "TCS,NSE,25,3200.00,2024-02-10\n"
        "HDFCBANK,NSE,60,1650.00,2024-03-01\n"
        "INFY,NSE,30,1400.00,2024-04-12\n"
    )
    return Response(
        content=template_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="lucid_portfolio_template.csv"'
        },
    )


@router.post("/upload-csv", response_model=PortfolioImportPreviewResponse)
async def upload_holdings_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Genuine CSV import workflow (FR-B01 & Part B).
    Parses CSV, validates required headers, normalizes symbol formats,
    checks data types, resolves instruments against active universe,
    and returns a structured preview with row-level validation errors.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Please upload a standard .csv file.",
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file is empty.",
        )
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5 MB limit.",
        )

    try:
        text_data = content.decode("utf-8")
    except UnicodeDecodeError:
        text_data = content.decode("latin1", errors="replace")

    reader = csv.reader(io.StringIO(text_data))
    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No rows found in CSV file.")

    # Header normalization
    header = [h.strip().lower() for h in rows[0]]
    col_map = {}
    for idx, h in enumerate(header):
        if h in ("symbol", "ticker", "scrip", "stock", "company", "instrument"):
            col_map["symbol"] = idx
        elif h in ("exchange", "mkt", "market"):
            col_map["exchange"] = idx
        elif h in ("quantity", "qty", "shares", "units", "count"):
            col_map["quantity"] = idx
        elif h in ("average_buy_price", "buy_price", "avg_price", "price", "purchase_price", "cost_price"):
            col_map["price"] = idx
        elif h in ("purchase_date", "date", "buy_date"):
            col_map["date"] = idx

    if "symbol" not in col_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required column 'symbol' (or 'ticker', 'stock') in CSV header.",
        )
    if "quantity" not in col_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required column 'quantity' (or 'qty', 'shares') in CSV header.",
        )

    valid_holdings: List[ParsedHoldingPreview] = []
    invalid_rows: List[InvalidRowError] = []
    total_val = 0.0

    for row_idx, r in enumerate(rows[1:], start=2):
        if not r or not any(field.strip() for field in r):
            continue

        sym_idx = col_map["symbol"]
        raw_sym = r[sym_idx].strip() if sym_idx < len(r) else ""
        if not raw_sym:
            invalid_rows.append(InvalidRowError(row_number=row_idx, raw_symbol="", error="Symbol is missing or empty."))
            continue

        qty_idx = col_map["quantity"]
        raw_qty = r[qty_idx].strip() if qty_idx < len(r) else ""
        try:
            qty_val = float(raw_qty)
            if qty_val <= 0:
                invalid_rows.append(InvalidRowError(row_number=row_idx, raw_symbol=raw_sym, error="Quantity must be greater than zero."))
                continue
        except ValueError:
            invalid_rows.append(InvalidRowError(row_number=row_idx, raw_symbol=raw_sym, error=f"Invalid numeric quantity '{raw_qty}'."))
            continue

        price_val = None
        if "price" in col_map and col_map["price"] < len(r):
            raw_p = r[col_map["price"]].strip()
            if raw_p:
                try:
                    price_val = float(raw_p.replace(",", "").replace("₹", ""))
                    if price_val < 0:
                        price_val = None
                except ValueError:
                    price_val = None

        res = resolve_listing_and_price(raw_sym, db)
        if not res:
            invalid_rows.append(InvalidRowError(
                row_number=row_idx,
                raw_symbol=raw_sym,
                error=f"Symbol '{raw_sym}' is not recognized in active NSE/BSE universe.",
            ))
            continue

        listing, sec, mkt_price = res
        cur_val = round(qty_val * mkt_price, 2)
        total_val += cur_val

        unrealized_pnl = None
        unrealized_pnl_pct = None
        if price_val is not None:
            inv_amt = round(qty_val * price_val, 2)
            unrealized_pnl = round(cur_val - inv_amt, 2)
            if inv_amt > 0:
                unrealized_pnl_pct = round(((cur_val / inv_amt) - 1.0) * 100.0, 2)

        sec_sector = "General Equity"
        if sec.company and sec.company.industries:
            ind = sec.company.industries[0].industry
            if ind and ind.sector:
                sec_sector = ind.sector.sector_name

        valid_holdings.append(ParsedHoldingPreview(
            row_number=row_idx,
            symbol=listing.symbol,
            security_name=sec.security_name,
            exchange=(listing.exchange.exchange_code if listing.exchange else "NSE") or "NSE",
            quantity=qty_val,
            average_purchase_price=price_val,
            latest_market_price=mkt_price,
            current_market_value=cur_val,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            sector_name=sec_sector,
        ))

    can_commit = len(valid_holdings) > 0 and len(invalid_rows) == 0

    return PortfolioImportPreviewResponse(
        status="parsed",
        source_type="file_import",
        filename=file.filename,
        total_rows=len(rows) - 1,
        valid_count=len(valid_holdings),
        error_count=len(invalid_rows),
        can_commit=can_commit,
        total_estimated_value=round(total_val, 2),
        valid_holdings=valid_holdings,
        invalid_rows=invalid_rows,
    )


@router.post("/parse-text", response_model=PortfolioImportPreviewResponse)
async def parse_holdings_text(
    payload: ParseTextRequest,
    db: Session = Depends(get_db),
    current_user: AppUser = Depends(get_current_user),
):
    """
    Parses copy-pasted spreadsheet or natural text holdings (comma, tab, or colon separated).
    Returns verified preview and row-level validation errors.
    """
    lines = [line.strip() for line in payload.text.replace(";", "\n").splitlines() if line.strip()]
    if not lines:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text contains no holdings.")

    valid_holdings: List[ParsedHoldingPreview] = []
    invalid_rows: List[InvalidRowError] = []
    total_val = 0.0

    for row_idx, line in enumerate(lines, start=1):
        # Format 1: SYMBOL: QTY (or SYMBOL: QTY @ PRICE)
        m_colon = re.match(r"^([A-Za-z0-9_\.]{2,15})\s*[:=]\s*(\d+(?:\.\d+)?)(?:\s*[@at]\s*(\d+(?:\.\d+)?))?", line)
        if m_colon:
            raw_sym = m_colon.group(1).strip()
            raw_qty = m_colon.group(2).strip()
            raw_price = m_colon.group(3)
        else:
            # Format 2: CSV / Tab / Comma delimited: SYMBOL, [EXCHANGE], QTY, [PRICE]
            parts = [p.strip() for p in re.split(r"[,\t]+", line) if p.strip()]
            if len(parts) >= 2:
                raw_sym = parts[0]
                if len(parts) >= 3 and parts[1].upper() in ("NSE", "BSE"):
                    raw_qty = parts[2]
                    raw_price = parts[3] if len(parts) >= 4 else None
                else:
                    raw_qty = parts[1]
                    raw_price = parts[2] if len(parts) >= 3 else None
            else:
                invalid_rows.append(InvalidRowError(
                    row_number=row_idx,
                    raw_symbol=line[:20],
                    error="Unrecognized row format. Expected 'SYMBOL: QTY' or 'SYMBOL, QTY'.",
                ))
                continue

        try:
            qty_val = float(raw_qty)
            if qty_val <= 0:
                invalid_rows.append(InvalidRowError(row_number=row_idx, raw_symbol=raw_sym, error="Quantity must be greater than zero."))
                continue
        except ValueError:
            invalid_rows.append(InvalidRowError(row_number=row_idx, raw_symbol=raw_sym, error=f"Invalid numeric quantity '{raw_qty}'."))
            continue

        price_val = None
        if raw_price:
            try:
                price_val = float(str(raw_price).replace(",", "").replace("₹", ""))
            except ValueError:
                price_val = None

        res = resolve_listing_and_price(raw_sym, db)
        if not res:
            invalid_rows.append(InvalidRowError(
                row_number=row_idx,
                raw_symbol=raw_sym,
                error=f"Symbol '{raw_sym}' is not recognized in active NSE/BSE universe.",
            ))
            continue

        listing, sec, mkt_price = res
        cur_val = round(qty_val * mkt_price, 2)
        total_val += cur_val

        unrealized_pnl = None
        unrealized_pnl_pct = None
        if price_val is not None:
            inv_amt = round(qty_val * price_val, 2)
            unrealized_pnl = round(cur_val - inv_amt, 2)
            if inv_amt > 0:
                unrealized_pnl_pct = round(((cur_val / inv_amt) - 1.0) * 100.0, 2)

        sec_sector = "General Equity"
        if sec.company and sec.company.industries:
            ind = sec.company.industries[0].industry
            if ind and ind.sector:
                sec_sector = ind.sector.sector_name

        valid_holdings.append(ParsedHoldingPreview(
            row_number=row_idx,
            symbol=listing.symbol,
            security_name=sec.security_name,
            exchange=(listing.exchange.exchange_code if listing.exchange else "NSE") or "NSE",
            quantity=qty_val,
            average_purchase_price=price_val,
            latest_market_price=mkt_price,
            current_market_value=cur_val,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_pct=unrealized_pnl_pct,
            sector_name=sec_sector,
        ))

    can_commit = len(valid_holdings) > 0 and len(invalid_rows) == 0

    return PortfolioImportPreviewResponse(
        status="parsed",
        source_type=payload.source_type,
        filename=None,
        total_rows=len(lines),
        valid_count=len(valid_holdings),
        error_count=len(invalid_rows),
        can_commit=can_commit,
        total_estimated_value=round(total_val, 2),
        valid_holdings=valid_holdings,
        invalid_rows=invalid_rows,
    )


@router.post("/portfolios", status_code=status.HTTP_201_CREATED)
async def create_existing_portfolio(
    payload: ExistingPortfolioCreate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Register an existing portfolio and its current holdings."""
    # Create existing portfolio record
    port = ExistingPortfolio(
        existing_portfolio_id=uuid.uuid4(),
        user_id=current_user.user_id,
        portfolio_name=payload.portfolio_name,
        source_type=payload.source_type,
        as_of_date=date.today(),
        currency_code="INR",
        portfolio_status="active",
    )
    db.add(port)
    db.flush()

    for h_input in payload.holdings:
        res = resolve_listing_and_price(h_input.symbol, db)
        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security symbol '{h_input.symbol}' is not recognized in active universe",
            )

        listing, sec, _ = res
        holding = ExistingPortfolioHolding(
            existing_portfolio_holding_id=uuid.uuid4(),
            existing_portfolio_id=port.existing_portfolio_id,
            security_id=listing.security_id,
            listing_id=listing.listing_id,
            quantity=Decimal(str(h_input.quantity)),
            average_purchase_price=Decimal(str(h_input.average_purchase_price)) if h_input.average_purchase_price else None,
            currency_code="INR",
        )
        db.add(holding)

    db.commit()
    db.refresh(port)
    return {
        "existing_portfolio_id": str(port.existing_portfolio_id),
        "portfolio_name": port.portfolio_name,
        "holdings_count": len(port.holdings),
        "status": "registered",
    }


@router.get("/portfolios")
async def list_existing_portfolios(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List existing registered portfolios for the authenticated investor."""
    ports = (
        db.query(ExistingPortfolio)
        .filter(ExistingPortfolio.user_id == current_user.user_id)
        .order_by(desc(ExistingPortfolio.updated_at))
        .all()
    )
    return [
        {
            "existing_portfolio_id": str(p.existing_portfolio_id),
            "portfolio_name": p.portfolio_name,
            "source_type": p.source_type,
            "holdings_count": len(p.holdings),
            "as_of_date": p.as_of_date.isoformat(),
            "created_at": p.created_at.isoformat(),
        }
        for p in ports
    ]


@router.delete("/portfolios/{existing_portfolio_id}")
async def delete_imported_portfolio(
    existing_portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes an imported/diagnosed portfolio and all its holdings,
    diagnoses, and rebalance suggestions.
    """
    return delete_existing_portfolio(
        db=db,
        existing_portfolio_id=existing_portfolio_id,
        user_id=current_user.user_id,
    )


@router.post("/analyze/{existing_portfolio_id}", response_model=DiagnosisDetailRead)
async def analyze_and_rebalance_portfolio(
    existing_portfolio_id: uuid.UUID,
    risk_category: str = "moderate",
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyzes an existing portfolio and returns concentration diagnosis and whole-share rebalance preview.
    Does not execute trades.
    """
    service = PortfolioDiagnosisService(db)
    try:
        res = service.diagnose_and_rebalance(
            existing_portfolio_id=existing_portfolio_id,
            user_id=current_user.user_id,
            target_risk_category=risk_category,
        )
        return res
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


class DiagnosisChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: Optional[List[Dict[str, str]]] = None


@router.get("/{existing_portfolio_id}/explanation")
async def get_diagnosis_explanation(
    existing_portfolio_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the comprehensive 7-part AI Copilot explanation for an imported portfolio's
    diagnostic findings and whole-share rebalancing proposals.
    """
    try:
        from backend.portfolio_engine.diagnosis_copilot_service import generate_diagnosis_explanation
        return generate_diagnosis_explanation(
            existing_portfolio_id=existing_portfolio_id,
            user_id=current_user.user_id,
            db=db,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/{existing_portfolio_id}/chat")
async def chat_diagnosis(
    existing_portfolio_id: uuid.UUID,
    payload: DiagnosisChatRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Context-aware interactive AI Copilot conversation for an imported portfolio's
    rebalancing proposals, stock trims, sector risks, and market crash scenarios.
    """
    try:
        from backend.portfolio_engine.diagnosis_copilot_service import chat_with_diagnosis_copilot
        return chat_with_diagnosis_copilot(
            existing_portfolio_id=existing_portfolio_id,
            query=payload.message,
            history=payload.history,
            user_id=current_user.user_id,
            db=db,
        )
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

