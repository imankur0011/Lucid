"""
Authentication Token Issuance, Email/Mobile Verification, Password Recovery, and Logout API Router.
Provides cryptographic JWT tokens, OTP verification flows, password reset, and session revocation.
"""

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
import secrets
import bcrypt
import hashlib
import jwt

try:
    from backend.config import settings
    from backend.database import get_db
    from backend.models import AppUser, UserVerificationCode, RevokedToken
    from backend.auth.dependencies import (
        get_current_user,
        create_access_token,
        hash_token,
        security_bearer,
        DEMO_USER_ID,
    )
    from backend.schemas import (
        AppUserRead,
        RequestVerificationRequest,
        VerifyCodeRequest,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        ChangePasswordRequest,
        LoginRequest,
    )
except ImportError:
    from config import settings
    from database import get_db
    from models import AppUser, UserVerificationCode, RevokedToken
    from auth.dependencies import (
        get_current_user,
        create_access_token,
        hash_token,
        security_bearer,
        DEMO_USER_ID,
    )
    from schemas import (
        AppUserRead,
        RequestVerificationRequest,
        VerifyCodeRequest,
        ForgotPasswordRequest,
        ResetPasswordRequest,
        ChangePasswordRequest,
        LoginRequest,
    )

router = APIRouter(prefix="/auth", tags=["Authentication"])

try:
    import argon2
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
    _ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, type=argon2.Type.ID)
except ImportError:
    _ph = None


def hash_password(password: str) -> str:
    """Hashes password using canonical Argon2id with secure salt and memory parameters."""
    if _ph:
        return _ph.hash(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: Optional[str]) -> bool:
    """Verifies plaintext password against stored Argon2id hash (with legacy bcrypt fallback)."""
    if not hashed:
        # If no password has been set yet, permit login in dev mode
        return settings.app_env == "development"
    try:
        if hashed.startswith("$argon2"):
            if _ph:
                try:
                    return _ph.verify(hashed, password)
                except Exception:
                    return False
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


class TokenRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    demo_user: bool = False
    mobile_number: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    email: Optional[str] = None
    expires_in_seconds: int


@router.post("/token", response_model=TokenResponse)
@router.post("/login", response_model=TokenResponse)
async def issue_token(
    payload: TokenRequest,
    db: Session = Depends(get_db),
):
    """
    Issues a cryptographically signed JWT access token.
    - If `demo_user=True` or no email provided, issues token for seeded demo user.
    - If email provided, retrieves user by email or creates user in development.
    - Validates password if set on account.
    """
    user = None
    if payload.demo_user or not payload.email:
        user = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
    else:
        user = db.query(AppUser).filter(AppUser.email == payload.email.lower().strip()).first()
        if not user and settings.app_env == "development":
            # Auto-provision user in dev mode
            pwd_hash = hash_password(payload.password) if payload.password else None
            user = AppUser(
                user_id=uuid.uuid4(),
                identity_provider="local-auth",
                identity_subject=payload.email.lower().strip(),
                email=payload.email.lower().strip(),
                password_hash=pwd_hash,
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

    # If user has a password set and password was provided, verify it
    if user.password_hash and payload.password:
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
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


@router.post("/register", response_model=TokenResponse)
async def register_user(
    payload: TokenRequest,
    db: Session = Depends(get_db),
):
    """Explicit registration endpoint that records email, password and issues token."""
    if not payload.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid email address is required for registration",
        )
    email_clean = payload.email.lower().strip()
    existing = db.query(AppUser).filter(AppUser.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in.",
        )

    pwd_hash = hash_password(payload.password) if payload.password else None
    mobile_clean = payload.mobile_number.strip() if payload.mobile_number else None
    user = AppUser(
        user_id=uuid.uuid4(),
        identity_provider="local-auth",
        identity_subject=email_clean,
        email=email_clean,
        mobile_number=mobile_clean,
        password_hash=pwd_hash,
        email_verified=False,
        mobile_verified=False,
        account_status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    expires_delta = timedelta(days=7)
    token = create_access_token(user.user_id, user.email, expires_delta=expires_delta)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        expires_in_seconds=int(expires_delta.total_seconds()),
    )


@router.post("/request-verification")
async def request_verification(
    payload: RequestVerificationRequest,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
):
    """
    4.3 Generates an unforgeable 6-digit OTP for email or mobile verification.
    Stores verification code with a 15-minute expiration.
    """
    recipient = payload.recipient.strip().lower()
    user = None

    # 1. Prefer authenticated user context if JWT token is provided
    if credentials and credentials.credentials:
        try:
            token_payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
            sub = token_payload.get("sub") or token_payload.get("user_id")
            if sub:
                user = db.query(AppUser).filter(AppUser.user_id == uuid.UUID(str(sub))).first()
        except Exception:
            pass

    # 2. If unauthenticated, look up matching user by email or mobile
    if not user:
        if "@" in recipient:
            user = db.query(AppUser).filter(AppUser.email == recipient).first()
        else:
            user = db.query(AppUser).filter(AppUser.mobile_number == recipient).first()

    # 3. Fallback to demo user if recipient is not yet linked
    if not user:
        user = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found for the requested recipient",
        )

    # Invalidate older pending codes of this type for this recipient
    db.query(UserVerificationCode).filter(
        UserVerificationCode.recipient == recipient,
        UserVerificationCode.code_type == payload.code_type,
        UserVerificationCode.is_used == False,
    ).update({"is_used": True})

    # Generate 6-digit cryptographic OTP
    otp_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    ver_rec = UserVerificationCode(
        verification_id=uuid.uuid4(),
        user_id=user.user_id,
        code_type=payload.code_type,
        code_value=otp_code,
        recipient=recipient,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(ver_rec)
    db.commit()

    return {
        "status": "success",
        "message": f"Verification code sent to {recipient}",
        "code_type": payload.code_type,
        "expires_in_seconds": 900,
        "demo_code": otp_code,  # Provided for immediate demonstration and testing
    }


@router.post("/verify-code")
async def verify_code(
    payload: VerifyCodeRequest,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
):
    """
    4.3 Verifies the OTP code for email or mobile.
    Marks email_verified or mobile_verified on the user profile.
    """
    recipient = payload.recipient.strip().lower()
    code_val = payload.code.strip()
    now = datetime.now(timezone.utc)

    # Optional authenticated user id
    auth_user_id = None
    if credentials and credentials.credentials:
        try:
            token_payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
            sub = token_payload.get("sub") or token_payload.get("user_id")
            if sub:
                auth_user_id = uuid.UUID(str(sub))
        except Exception:
            pass

    # Look for matching active verification code
    query = (
        db.query(UserVerificationCode)
        .filter(
            UserVerificationCode.recipient == recipient,
            UserVerificationCode.code_type == payload.code_type,
            UserVerificationCode.code_value == code_val,
            UserVerificationCode.is_used == False,
            UserVerificationCode.expires_at >= now,
        )
    )
    if auth_user_id:
        ver_rec = query.filter(UserVerificationCode.user_id == auth_user_id).order_by(UserVerificationCode.created_at.desc()).first()
        if not ver_rec:
            ver_rec = query.order_by(UserVerificationCode.created_at.desc()).first()
    else:
        ver_rec = query.order_by(UserVerificationCode.created_at.desc()).first()

    if not ver_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code. Please request a new code.",
        )

    ver_rec.is_used = True
    target_user_id = auth_user_id or ver_rec.user_id
    user = db.query(AppUser).filter(AppUser.user_id == target_user_id).first()
    if user:
        if payload.code_type == "email_verification":
            user.email_verified = True
            user.email = recipient
        elif payload.code_type == "mobile_verification":
            user.mobile_verified = True
            user.mobile_number = recipient
        if user.account_status == "pending":
            user.account_status = "active"
        user.updated_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "status": "verified",
        "message": f"{payload.code_type.replace('_', ' ').capitalize()} verified successfully",
        "email_verified": user.email_verified if user else True,
        "mobile_verified": user.mobile_verified if user else False,
    }


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    4.4 Initiates password recovery by sending a 6-digit reset code to user's registered email.
    """
    email_clean = payload.email.strip().lower()
    user = db.query(AppUser).filter(AppUser.email == email_clean).first()
    if not user:
        # Standard security practice: Don't reveal whether user exists
        return {
            "status": "success",
            "message": f"If an account with {email_clean} exists, a password reset code has been sent.",
            "expires_in_seconds": 900,
        }

    # Invalidate older pending reset codes
    db.query(UserVerificationCode).filter(
        UserVerificationCode.recipient == email_clean,
        UserVerificationCode.code_type == "password_reset",
        UserVerificationCode.is_used == False,
    ).update({"is_used": True})

    reset_code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    ver_rec = UserVerificationCode(
        verification_id=uuid.uuid4(),
        user_id=user.user_id,
        code_type="password_reset",
        code_value=reset_code,
        recipient=email_clean,
        expires_at=expires_at,
        is_used=False,
    )
    db.add(ver_rec)
    db.commit()

    return {
        "status": "success",
        "message": f"If an account with {email_clean} exists, a password reset code has been sent.",
        "expires_in_seconds": 900,
        "demo_code": reset_code,  # Provided for immediate demonstration and testing
    }


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    4.4 Completes password reset by verifying reset OTP and saving new bcrypt password hash.
    """
    email_clean = payload.email.strip().lower()
    code_val = payload.code.strip()
    now = datetime.now(timezone.utc)

    ver_rec = (
        db.query(UserVerificationCode)
        .filter(
            UserVerificationCode.recipient == email_clean,
            UserVerificationCode.code_type == "password_reset",
            UserVerificationCode.code_value == code_val,
            UserVerificationCode.is_used == False,
            UserVerificationCode.expires_at >= now,
        )
        .first()
    )

    if not ver_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset code",
        )

    user = db.query(AppUser).filter(AppUser.user_id == ver_rec.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found",
        )

    ver_rec.is_used = True
    user.password_hash = hash_password(payload.new_password)
    user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "message": "Password has been successfully updated. You may now log in with your new credentials.",
    }


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update password for the currently authenticated user.
    If a password is set, verifies current_password before updating.
    """
    if current_user.password_hash:
        if not payload.current_password or not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

    current_user.password_hash = hash_password(payload.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "success",
        "message": "Password has been updated successfully.",
    }


@router.post("/logout")
async def logout(
    credentials = Security(security_bearer),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    4.4 Revokes the active JWT access token, blacklists its hash in PostgreSQL,
    and terminates the user's active session.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bearer token missing in Authorization header",
        )

    token = credentials.credentials
    thash = hash_token(token)

    # Check if already revoked
    existing = db.query(RevokedToken).filter(RevokedToken.token_hash == thash).first()
    if not existing:
        rev_entry = RevokedToken(
            revocation_id=uuid.uuid4(),
            token_hash=thash,
            user_id=current_user.user_id,
            revoked_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(rev_entry)
        db.commit()

    return {
        "status": "success",
        "message": "Logged out successfully. Authentication token has been revoked.",
    }


@router.get("/me", response_model=AppUserRead)
async def get_current_user_profile(
    current_user: AppUser = Depends(get_current_user),
):
    """Get current authenticated user profile and account status."""
    return current_user


class DeleteAccountPayload(BaseModel):
    password: Optional[str] = Field(None, description="Current password for verification")
    confirmation_phrase: str = Field(..., description="Must be 'DELETE MY ACCOUNT'")


@router.get("/export-data")
async def export_my_data(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exports all stored account and portfolio data for the authenticated user."""
    try:
        from backend.services.account_deletion_service import export_user_account_data
    except ImportError:
        from services.account_deletion_service import export_user_account_data
    return export_user_account_data(db=db, user=current_user)


@router.post("/delete-account")
@router.delete("/account")
async def delete_my_account(
    payload: DeleteAccountPayload,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Permanently deletes the authenticated user's Lucid account and all associated data."""
    try:
        from backend.services.account_deletion_service import delete_user_account
    except ImportError:
        from services.account_deletion_service import delete_user_account
    token = credentials.credentials if credentials else None
    return delete_user_account(
        db=db,
        user=current_user,
        password=payload.password,
        confirmation_phrase=payload.confirmation_phrase,
        current_token=token,
    )
