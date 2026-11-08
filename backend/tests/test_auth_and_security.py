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


def test_admin_authorization_enforced_on_ingestion_in_staging(monkeypatch):
    """Verify that in staging, market data ingestion requires admin credentials."""
    from backend.config import settings
    monkeypatch.setattr(settings, "app_env", "staging")

    # Regular non-admin user
    reg_token = create_access_token(DEMO_USER_ID)
    reg_headers = {"Authorization": f"Bearer {reg_token}"}

    res = client.post(
        "/api/v1/market-data/ingest",
        json={"symbol": "RELIANCE", "provider": "simulated"},
        headers=reg_headers,
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for regular user, got {res.status_code}"
    assert "admin" in res.json()["detail"].lower()


def test_insecure_jwt_secret_rejected_in_staging(monkeypatch):
    """Verify that startup fails if an insecure/default secret key is configured in staging."""
    from backend.config import Settings
    import pytest

    insecure_settings = Settings(
        app_env="staging",
        jwt_secret_key="change-me-short",
    )
    with pytest.raises(ValueError, match="CRITICAL SECURITY CONFIGURATION ERROR"):
        insecure_settings.validate_security_keys()


def test_rate_limiting_on_auth_endpoint():
    """Verify that excessive authentication requests are rate limited with HTTP 429."""
    from backend.middleware.rate_limit import InMemoryRateLimiterMiddleware
    InMemoryRateLimiterMiddleware.reset()

    for _ in range(20):
        res = client.post("/api/v1/auth/token", json={"demo_user": True})
        assert res.status_code == 200

    # 21st request should trigger HTTP 429 Too Many Requests
    limit_res = client.post("/api/v1/auth/token", json={"demo_user": True})
    assert limit_res.status_code == 429
    assert "rate limit exceeded" in limit_res.json()["detail"].lower()
    assert "retry-after" in limit_res.headers


def test_email_and_mobile_verification_flow():
    """Verify requesting and submitting OTP codes for email and mobile."""
    # 1. Request verification code for email
    req_email = client.post(
        "/api/v1/auth/request-verification",
        json={"recipient": "investor.verify@example.com", "code_type": "email_verification"},
    )
    assert req_email.status_code == 200, req_email.text
    email_code = req_email.json()["demo_code"]
    assert len(email_code) == 6

    # 2. Verify with valid code
    verify_email = client.post(
        "/api/v1/auth/verify-code",
        json={"recipient": "investor.verify@example.com", "code": email_code, "code_type": "email_verification"},
    )
    assert verify_email.status_code == 200, verify_email.text
    assert verify_email.json()["status"] == "verified"

    # 3. Request verification code for mobile
    req_mobile = client.post(
        "/api/v1/auth/request-verification",
        json={"recipient": "+919876543210", "code_type": "mobile_verification"},
    )
    assert req_mobile.status_code == 200, req_mobile.text
    mobile_code = req_mobile.json()["demo_code"]

    # 4. Verify invalid code fails
    invalid_verify = client.post(
        "/api/v1/auth/verify-code",
        json={"recipient": "+919876543210", "code": "000000", "code_type": "mobile_verification"},
    )
    assert invalid_verify.status_code == 400

    # 5. Verify valid code succeeds
    verify_mobile = client.post(
        "/api/v1/auth/verify-code",
        json={"recipient": "+919876543210", "code": mobile_code, "code_type": "mobile_verification"},
    )
    assert verify_mobile.status_code == 200
    assert verify_mobile.json()["status"] == "verified"


def test_password_recovery_and_logout_revocation():
    """Verify forgot-password OTP, reset password with bcrypt, login with new password, and logout token revocation."""
    test_email = f"investor.reset.{uuid4().hex[:8]}@example.com"
    # 0. Register initial test user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": test_email, "password": "OldPassword#123"},
    )
    assert reg_res.status_code == 200, reg_res.text

    # 1. Request forgot password code
    forgot_res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": test_email},
    )
    assert forgot_res.status_code == 200, forgot_res.text
    reset_code = forgot_res.json()["demo_code"]

    # 2. Reset password using the code
    reset_res = client.post(
        "/api/v1/auth/reset-password",
        json={
            "email": test_email,
            "code": reset_code,
            "new_password": "NewSecurePassword#2026",
        },
    )
    assert reset_res.status_code == 200, reset_res.text
    assert reset_res.json()["status"] == "success"

    # 3. Login with newly reset password
    login_res = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_email,
            "password": "NewSecurePassword#2026",
        },
    )
    assert login_res.status_code == 200, login_res.text
    new_token = login_res.json()["access_token"]
    assert new_token

    # 4. Access protected endpoint with token
    auth_headers = {"Authorization": f"Bearer {new_token}"}
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200

    # 5. Logout and verify token revocation
    logout_res = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert logout_res.status_code == 200, logout_res.text
    assert logout_res.json()["status"] == "success"

    # 6. Reusing revoked token must fail with 401
    revoked_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["detail"].lower()


def test_change_password_and_mobile_profile_update():
    """Verify that authenticated users can update their profile mobile number and change their password."""
    test_email = f"investor.profile.{uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": test_email, "password": "OriginalPassword#123"},
    )
    assert reg_res.status_code == 200, reg_res.text
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update mobile number and display name
    prof_patch = client.patch(
        "/api/v1/profile",
        headers=headers,
        json={"mobile_number": "+919876543210", "display_name": "Test Investor"},
    )
    assert prof_patch.status_code == 200, prof_patch.text
    prof_data = prof_patch.json()
    assert prof_data["mobile_number"] == "+919876543210"
    assert prof_data["display_name"] == "Test Investor"

    # 2. Change password with wrong current password should fail
    wrong_pwd = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "WrongPassword", "new_password": "NewDirectPassword#2026"},
    )
    assert wrong_pwd.status_code == 400

    # 3. Change password with correct current password succeeds
    change_res = client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": "OriginalPassword#123", "new_password": "NewDirectPassword#2026"},
    )
    assert change_res.status_code == 200, change_res.text
    assert change_res.json()["status"] == "success"




