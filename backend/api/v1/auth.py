"""
Authentication Token Issuance and Verification API Router.
Provides real JWT tokens for frontend sessions and programmatic API authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
from pydantic import BaseModel
import uuid
import jwt

try:
    from backend.config import settings
    from backend.database import get_db
    from backend.models import AppUser
    from backend.auth.dependencies import get_current_user, create_access_token, DEMO_USER_ID
    from backend.schemas import AppUserRead
except ImportError:
    from config import settings
    from database import get_db
    from models import AppUser
    from auth.dependencies import get_current_user, create_access_token, DEMO_USER_ID
    from schemas import AppUserRead

router = APIRouter(prefix="/auth", tags=["Authentication"])


class TokenRequest(BaseModel):
    email: Optional[str] = None
    demo_user: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: Optional[str] = None
    expires_in_seconds: int


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    payload: TokenRequest,
    db: Session = Depends(get_db),
):
    """
    Issues a cryptographically signed JWT access token.
    - If `demo_user=True` or no email provided, issues token for seeded demo user.
    - If email provided, retrieves user by email or creates user in development.
    """
    user = None
    if payload.demo_user or not payload.email:
        user = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
    else:
        user = db.query(AppUser).filter(AppUser.email == payload.email.lower()).first()
        if not user and settings.app_env == "development":
            # Auto-provision user in dev mode
            user = AppUser(
                user_id=uuid.uuid4(),
                identity_provider="local-auth",
                identity_subject=payload.email.lower(),
                email=payload.email.lower(),
                account_status="active",
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found for provided credentials",
        )

    expires_delta = timedelta(days=7)
    token = create_access_token(user.user_id, user.email, expires_delta=expires_delta)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        expires_in_seconds=int(expires_delta.total_seconds()),
    )


@router.get("/me", response_model=AppUserRead)
async def get_current_user_profile(
    current_user: AppUser = Depends(get_current_user),
):
    """Get current authenticated user profile and account status."""
    return current_user
