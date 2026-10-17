"""
Financial Goals API endpoints (GET, POST, PATCH, DELETE).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

try:
    from backend.database import get_db
    from backend.models import AppUser, FinancialGoal
    from backend.auth.dependencies import get_current_user
    from backend.schemas import (
        FinancialGoalCreate,
        FinancialGoalUpdate,
        FinancialGoalRead,
    )
except ImportError:
    from database import get_db
    from models import AppUser, FinancialGoal
    from auth.dependencies import get_current_user
    from schemas import (
        FinancialGoalCreate,
        FinancialGoalUpdate,
        FinancialGoalRead,
    )

router = APIRouter(prefix="/goals", tags=["Financial Goals"])


@router.get("", response_model=List[FinancialGoalRead])
async def list_goals(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all financial goals for the authenticated investor."""
    return (
        db.query(FinancialGoal)
        .filter(FinancialGoal.user_id == current_user.user_id)
        .order_by(FinancialGoal.priority.asc(), FinancialGoal.created_at.desc())
        .all()
    )


@router.post("", response_model=FinancialGoalRead, status_code=status.HTTP_201_CREATED)
async def create_goal(
    payload: FinancialGoalCreate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new financial goal for the authenticated investor."""
    goal = FinancialGoal(
        goal_id=uuid.uuid4(),
        user_id=current_user.user_id,
        goal_name=payload.goal_name,
        goal_type=payload.goal_type,
        target_amount=payload.target_amount,
        amount_already_saved=payload.amount_already_saved,
        currency_code=payload.currency_code,
        target_date=payload.target_date,
        priority=payload.priority,
        notes=payload.notes,
        goal_status="active",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.patch("/{goal_id}", response_model=FinancialGoalRead)
async def update_goal(
    goal_id: uuid.UUID,
    payload: FinancialGoalUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing goal owned by the authenticated investor."""
    goal = (
        db.query(FinancialGoal)
        .filter(FinancialGoal.goal_id == goal_id, FinancialGoal.user_id == current_user.user_id)
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or unauthorized",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(goal, field, val)

    goal.updated_at = datetime.now()
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete or archive a financial goal owned by the authenticated investor."""
    goal = (
        db.query(FinancialGoal)
        .filter(FinancialGoal.goal_id == goal_id, FinancialGoal.user_id == current_user.user_id)
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial goal not found or unauthorized",
        )

    db.delete(goal)
    db.commit()
    return None
