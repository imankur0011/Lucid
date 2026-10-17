"""
Authentication dependencies for FastAPI.
Provides request-scoped AppUser authentication with strict isolation and development fallbacks.
"""

import uuid
from typing import Optional
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

try:
    from backend.config import settings
    from backend.database import get_db
    from backend.models import AppUser
except ImportError:
    from config import settings
    from database import get_db
    from models import AppUser

# Demo investor UUID seeded in database
DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: Session = Depends(get_db),
) -> AppUser:
    """
    Retrieves the authenticated AppUser.
    - Decodes JWT bearer token if present.
    - In development mode (settings.app_env != 'production'), allows fallback to demo user if no token is provided.
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
                options={"verify_signature": settings.app_env == "production"},
            )
            sub = payload.get("sub") or payload.get("user_id")
            if sub:
                user_id = uuid.UUID(str(sub))
        except (jwt.PyJWTError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(exc)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # In development mode, allow fallback to seeded demo user
    if not user_id:
        if settings.app_env != "production":
            user_id = DEMO_USER_ID
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user = db.query(AppUser).filter(AppUser.user_id == user_id).first()
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
