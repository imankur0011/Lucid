"""
Investor Profile API endpoints (GET, PATCH).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

try:
    from backend.database import get_db
    from backend.models import AppUser, UserProfile
    from backend.auth.dependencies import get_current_user
    from backend.schemas import UserProfileRead, UserProfileUpdate
except ImportError:
    from database import get_db
    from models import AppUser, UserProfile
    from auth.dependencies import get_current_user
    from schemas import UserProfileRead, UserProfileUpdate

router = APIRouter(prefix="/profile", tags=["Investor Profile"])


@router.get("", response_model=UserProfileRead)
async def get_profile(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the authenticated investor's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not profile:
        # Create a default profile if none exists
        profile = UserProfile(
            user_id=current_user.user_id,
            display_name=current_user.email.split("@")[0] if current_user.email else "Investor",
            country_code="IN",
            preferred_currency="INR",
            investment_experience="beginner",
            investment_knowledge_level="basic",
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.patch("", response_model=UserProfileRead)
async def update_profile(
    payload: UserProfileUpdate,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile fields for the authenticated investor."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.user_id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.user_id)
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(profile, field, val)

    profile.updated_at = datetime.now()
    db.commit()
    db.refresh(profile)
    return profile
