"""
Portfolio Diagnosis and Rebalance Preview API Router.
Accepts existing investor investments, diagnoses concentration risks, and provides buy/sell/hold previews.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from decimal import Decimal
import uuid
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
    )
    from backend.diagnosis.service import PortfolioDiagnosisService
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
    )
    from diagnosis.service import PortfolioDiagnosisService

router = APIRouter(prefix="/diagnosis", tags=["Portfolio Diagnosis & Rebalancing"])


class HoldingInput(BaseModel):
    symbol: str
    quantity: float = Field(..., gt=0)
    average_purchase_price: Optional[float] = Field(None, ge=0)


class ExistingPortfolioCreate(BaseModel):
    portfolio_name: str = Field(..., min_length=1, max_length=160)
    source_type: str = Field("manual", pattern="^(manual|file_import|broker_import)$")
    holdings: List[HoldingInput] = Field(..., min_length=1)


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
    created_at: datetime


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

    # Match symbols to securities in database
    for h_input in payload.holdings:
        listing = (
            db.query(InstrumentListing)
            .filter(InstrumentListing.symbol == h_input.symbol.strip().upper())
            .first()
        )
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Security symbol '{h_input.symbol}' is not recognized in active universe",
            )

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
