"""
Unit and integration tests for Lucid Notification System (FR-C09).
Validates:
- User-scoped alert generation
- Unread count aggregation
- Mark single notification as read
- Mark all notifications as read
- Delete / dismiss notification
- User isolation (no cross-tenant leakage)
"""

import pytest
import uuid
from decimal import Decimal
from fastapi.testclient import TestClient
from backend.main import app
from backend.database.session import SessionLocal
from backend.models import AppUser, Notification
from backend.services.notification_service import NotificationService

client = TestClient(app)
DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")


def test_notification_service_crud_and_isolation():
    db = SessionLocal()
    try:
        user = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
        assert user is not None, "Demo user must exist in the database"

        # Create a second arbitrary user ID to verify tenant isolation
        other_user_id = uuid.uuid4()

        # 2. Dispatch a notification
        notif = NotificationService.create_notification(
            db=db,
            user_id=DEMO_USER_ID,
            notification_type="drift_alert",
            title="Portfolio Drift Breached 5.2%",
            message="RELIANCE has drifted from target weight 15.0% to 20.2%.",
            delivery_channel="in_app",
            metadata={"drift_pct": 5.2, "symbol": "RELIANCE", "severity": "warning"},
            cooldown_minutes=0,
        )
        assert notif is not None
        assert notif.notification_id is not None
        assert notif.read_at is None

        # 3. Check unread count
        count = NotificationService.get_unread_count(db, DEMO_USER_ID)
        assert count >= 1

        # Check other user has 0 unread
        other_count = NotificationService.get_unread_count(db, other_user_id)
        assert other_count == 0

        # 4. Mark read
        success = NotificationService.mark_as_read(db, user_id=DEMO_USER_ID, notification_id=notif.notification_id)
        assert success is True

        refreshed = db.query(Notification).filter(Notification.notification_id == notif.notification_id).first()
        assert refreshed.read_at is not None

        # 5. Verify dismissal (soft delete from active notifications)
        deleted = NotificationService.dismiss_notification(db, user_id=DEMO_USER_ID, notification_id=notif.notification_id)
        assert deleted is True

        refreshed_after_dismiss = db.query(Notification).filter(Notification.notification_id == notif.notification_id).first()
        assert refreshed_after_dismiss.dismissed_at is not None

        # Verify it no longer appears in active user notifications
        active_notifs = NotificationService.get_user_notifications(db, DEMO_USER_ID)
        assert notif.notification_id not in [n.notification_id for n in active_notifs]
    finally:
        db.close()


def test_notification_api_endpoints():
    db = SessionLocal()
    try:
        user = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
        assert user is not None

        # Seed a test notification for API check
        notif = NotificationService.create_notification(
            db=db,
            user_id=DEMO_USER_ID,
            notification_type="rebalance_available",
            title="Whole-Share Rebalance Available",
            message="Trade execution basket is ready for review.",
            delivery_channel="in_app",
            metadata={"severity": "info"},
            cooldown_minutes=0,
        )
        notif_id = str(notif.notification_id)

        # GET /api/v1/notifications
        res = client.get("/api/v1/notifications")
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        matching = [n for n in data if n["notification_id"] == notif_id]
        assert len(matching) == 1

        # GET /api/v1/notifications/unread-count
        res_count = client.get("/api/v1/notifications/unread-count")
        assert res_count.status_code == 200
        assert res_count.json()["unread_count"] >= 1

        # PUT /api/v1/notifications/{id}/read
        res_read = client.put(f"/api/v1/notifications/{notif_id}/read")
        assert res_read.status_code == 200
        assert res_read.json()["success"] is True

        # PUT /api/v1/notifications/mark-all-read
        res_all = client.put("/api/v1/notifications/mark-all-read")
        assert res_all.status_code == 200

        # DELETE /api/v1/notifications/{id}
        res_del = client.delete(f"/api/v1/notifications/{notif_id}")
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True
    finally:
        db.close()
