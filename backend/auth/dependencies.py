"""
Authentication dependencies for FastAPI.
Provides request-scoped AppUser authentication with strict isolation,
JWT verification, token creation, and development fallbacks.
"""

import uuid
from typing import Optional
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import hashlib

try:
    from backend.config import settings
    from backend.database import get_db
    from backend.models import AppUser, RevokedToken
except ImportError:
    from config import settings
    from database import get_db
    from models import AppUser, RevokedToken

def hash_token(token: str) -> str:
    """Returns SHA256 hex digest for token indexing and revocation lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

# Demo investor UUID seeded in database
DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")

security_bearer = HTTPBearer(auto_error=False)


def create_access_token(
    user_id: uuid.UUID,
    email: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a cryptographically signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(days=7))
    payload = {
        "sub": str(user_id),
        "email": email or "",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> AppUser:
    """
    Retrieves the authenticated AppUser.
    - Decodes JWT bearer token if present.
    - In staging and production (settings.app_env in ['staging', 'production']),
      strictly rejects unauthenticated requests (fail-closed).
    - In development mode only, allows fallback to seeded demo user if no token is provided.
    - Strictly isolates all operations to the authenticated user's user_id.
    """
    user_id: Optional[uuid.UUID] = None

    if credentials and credentials.credentials:
        token = credentials.credentials
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=["HS256"],
                options={"verify_exp": True},
            )
            sub = payload.get("sub") or payload.get("user_id")
            if sub:
                user_id = uuid.UUID(str(sub))

            # Verify token has not been revoked (e.g. via logout)
            thash = hash_token(token)
            revoked = db.query(RevokedToken).filter(RevokedToken.token_hash == thash).first()
            if revoked:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication token has been revoked / logged out. Please log in again.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except (jwt.PyJWTError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(exc)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # In non-development environments, require explicit authentication (fail-closed)
    if not user_id:
        if settings.app_env in ["staging", "production"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Bearer token missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            # Development-only fallback to seeded demo user
            user_id = DEMO_USER_ID

    user = db.query(AppUser).filter(AppUser.user_id == user_id).first()
    if not user and settings.app_env == "development":
        # Development fallback: try finding developer@lucid.local or any active user
        user = (
            db.query(AppUser).filter(AppUser.email == "developer@lucid.local").first()
            or db.query(AppUser).filter(AppUser.account_status == "active").first()
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user account not found in database",
        )

    if user.account_status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.account_status}",
        )

    return user
