"""
Tests for Authentication, Cryptographic JWT Tokens, Staging/Production Fail-Closed Security,
and Multi-Tenant User Isolation.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import timedelta
from uuid import uuid4
import jwt

from backend.main import app
from backend.config import settings
from backend.auth.dependencies import create_access_token, DEMO_USER_ID
from backend.database import SessionLocal
from backend.models import AppUser, ExistingPortfolio

client = TestClient(app)


def test_real_jwt_token_issuance_and_access():
    """Verify that the API issues valid JWT tokens and accepts them in Authorization header."""
    # 1. Issue Token
    res = client.post("/api/v1/auth/token", json={"demo_user": True})
    assert res.status_code == 200, res.text
    token_data = res.json()
    token = token_data["access_token"]
    assert token_data["user_id"] == str(DEMO_USER_ID)

    # 2. Access Protected Endpoint with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200, me_res.text
    assert me_res.json()["user_id"] == str(DEMO_USER_ID)

    prof_res = client.get("/api/v1/profile", headers=headers)
    assert prof_res.status_code == 200
    assert prof_res.json()["user_id"] == str(DEMO_USER_ID)


def test_expired_jwt_token_fails_with_401():
    """Verify that expired JWT tokens are strictly rejected with HTTP 401."""
    # Create token expired 1 hour ago
    expired_token = create_access_token(
        user_id=DEMO_USER_ID,
        expires_delta=timedelta(hours=-1),
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    res = client.get("/api/v1/profile", headers=headers)
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_tampered_jwt_signature_fails_with_401():
    """Verify that tokens with altered payloads or invalid secrets are rejected."""
    # Encode with wrong secret
    tampered_token = jwt.encode(
        {"sub": str(DEMO_USER_ID)},
        "wrong-secret-key-that-does-not-match",
        algorithm="HS256",
    )
    headers = {"Authorization": f"Bearer {tampered_token}"}
    res = client.get("/api/v1/profile", headers=headers)
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_production_mode_fails_closed_without_token():
    """Verify that in staging and production modes, unauthenticated requests are strictly rejected with 401."""
    original_env = settings.app_env
    try:
        # Simulate production environment
        settings.app_env = "production"

        # Request with no Authorization header
        res = client.get("/api/v1/profile")
        assert res.status_code == 401
        assert "authentication required" in res.json()["detail"].lower()
    finally:
        settings.app_env = original_env


def test_user_data_isolation_on_existing_portfolios():
    """Verify that User A cannot analyze or view User B's portfolio records."""
    db = SessionLocal()
    try:
        unique_id = uuid4()
        user_b = AppUser(
            user_id=unique_id,
            identity_provider="test-auth",
            identity_subject=f"user-b-{unique_id}",
            email=f"user_b_{unique_id}@example.invalid",
            account_status="active",
        )
        db.add(user_b)
        db.flush()

        port_b = ExistingPortfolio(
            existing_portfolio_id=uuid4(),
            user_id=user_b.user_id,
            portfolio_name="User B Private Portfolio",
            source_type="manual",
            currency_code="INR",
            portfolio_status="active",
        )
        db.add(port_b)
        db.commit()

        # Token for Demo User (User A)
        token_a = create_access_token(DEMO_USER_ID)
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # User A attempts to analyze User B's portfolio -> Must return 400/404 unauthorized
        res = client.post(f"/api/v1/diagnosis/analyze/{port_b.existing_portfolio_id}", headers=headers_a)
        assert res.status_code in [400, 404]
        assert "unauthorized" in res.json()["detail"].lower() or "not found" in res.json()["detail"].lower()
    finally:
        db.close()
