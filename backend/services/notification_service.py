"""
Notification Service for Lucid Portfolio Platform.
Handles in-app alert generation, deduplication, cooldown policies, and read/dismiss lifecycles.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

try:
    from backend.models.agent import Notification
except ImportError:
    from models.agent import Notification


class NotificationService:
    """Manages user-scoped notifications and alert delivery."""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: uuid.UUID,
        notification_type: str,
        title: str,
        message: str,
        delivery_channel: str = "in_app",
        metadata: Optional[Dict[str, Any]] = None,
        cooldown_minutes: int = 60,
    ) -> Optional[Notification]:
        """
        Creates and persists a notification with deduplication cooldown.
        If a notification of the same type with identical key metadata exists within cooldown, skips creation.
        """
        now = datetime.now(timezone.utc)
        meta = metadata or {}

        # Deduplication check: check if identical notification was sent recently
        if cooldown_minutes > 0:
            cutoff = now - timedelta(minutes=cooldown_minutes)
            recent_q = (
                db.query(Notification)
                .filter(
                    Notification.user_id == user_id,
                    Notification.notification_type == notification_type,
                    Notification.created_at >= cutoff,
                )
            )
            # If metadata specifies an entity_id (e.g. portfolio_id or symbol), check it
            entity_id = meta.get("portfolio_id") or meta.get("symbol")
            if entity_id:
                for notif in recent_q.all():
                    existing_entity = (notif.metadata_ or {}).get("portfolio_id") or (notif.metadata_ or {}).get("symbol")
                    if str(existing_entity) == str(entity_id):
                        return notif  # Skip creating duplicate within cooldown
            else:
                existing = recent_q.first()
                if existing:
                    return existing

        notif = Notification(
            notification_id=uuid.uuid4(),
            user_id=user_id,
            notification_type=notification_type[:40],
            title=title[:200],
            message=message,
            delivery_channel=delivery_channel,
            delivery_status="sent",
            created_at=now,
            sent_at=now,
            metadata_=meta,
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: uuid.UUID,
        unread_only: bool = False,
        include_dismissed: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """Fetches notifications scoped strictly to the authenticated user."""
        q = db.query(Notification).filter(Notification.user_id == user_id)

        if not include_dismissed:
            q = q.filter(Notification.dismissed_at.is_(None))

        if unread_only:
            q = q.filter(Notification.read_at.is_(None))

        return q.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: uuid.UUID) -> int:
        """Returns the number of unread, non-dismissed notifications for the user."""
        return (
            db.query(func.count(Notification.notification_id))
            .filter(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                Notification.dismissed_at.is_(None),
            )
            .scalar()
            or 0
        )

    @staticmethod
    def mark_as_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        """Marks a single notification as read if owned by the user."""
        notif = (
            db.query(Notification)
            .filter(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )
        if not notif:
            return False

        if notif.read_at is None:
            notif.read_at = datetime.now(timezone.utc)
            db.commit()
        return True

    @staticmethod
    def mark_all_as_read(db: Session, user_id: uuid.UUID) -> int:
        """Marks all unread notifications for the user as read."""
        now = datetime.now(timezone.utc)
        updated = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.read_at.is_(None),
                Notification.dismissed_at.is_(None),
            )
            .update({"read_at": now}, synchronize_session="fetch")
        )
        db.commit()
        return updated

    @staticmethod
    def dismiss_notification(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> bool:
        """Marks a notification as dismissed (soft delete from active view)."""
        notif = (
            db.query(Notification)
            .filter(
                Notification.notification_id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )
        if not notif:
            return False

        notif.dismissed_at = datetime.now(timezone.utc)
        db.commit()
        return True

