"""
Notification and Alert Management API Router.
Provides authenticated access to in-app alerts, unread counts, read acknowledgements, and dismissals.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid

try:
    from backend.database import get_db
    from backend.auth.dependencies import get_current_user
    from backend.models.users import AppUser
    from backend.services.notification_service import NotificationService
except ImportError:
    from database import get_db
    from auth.dependencies import get_current_user
    from models.users import AppUser
    from services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications & Alerts"])


class NotificationResponse(BaseModel):
    notification_id: str
    notification_type: str
    title: str
    message: str
    delivery_channel: str
    delivery_status: str
    created_at: str
    sent_at: Optional[str] = None
    read_at: Optional[str] = None
    dismissed_at: Optional[str] = None
    metadata: Dict[str, Any] = {}


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get("", response_model=List[NotificationResponse])
def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves in-app notifications scoped strictly to the authenticated user."""
    notifs = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return [
        NotificationResponse(
            notification_id=str(n.notification_id),
            notification_type=n.notification_type,
            title=n.title,
            message=n.message,
            delivery_channel=n.delivery_channel,
            delivery_status=n.delivery_status,
            created_at=n.created_at.isoformat() if n.created_at else "",
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
            read_at=n.read_at.isoformat() if n.read_at else None,
            dismissed_at=n.dismissed_at.isoformat() if n.dismissed_at else None,
            metadata=n.metadata_ or {},
        )
        for n in notifs
    ]


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the total number of unread alerts for the active user badge."""
    count = NotificationService.get_unread_count(db=db, user_id=current_user.user_id)
    return UnreadCountResponse(unread_count=count)


@router.put("/{notification_id}/read")
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marks a single alert as read."""
    success = NotificationService.mark_as_read(
        db=db,
        user_id=current_user.user_id,
        notification_id=notification_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied",
        )
    return {"success": True, "notification_id": str(notification_id), "status": "read"}


@router.put("/mark-all-read")
def mark_all_notifications_read(
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Marks all unread alerts for the user as read."""
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.user_id)
    return {"success": True, "marked_count": count}


@router.delete("/{notification_id}")
def dismiss_notification(
    notification_id: uuid.UUID,
    current_user: AppUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismisses an alert (removes it from the active inbox)."""
    success = NotificationService.dismiss_notification(
        db=db,
        user_id=current_user.user_id,
        notification_id=notification_id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied",
        )
    return {"success": True, "notification_id": str(notification_id), "status": "dismissed"}

