"""
Tests for Failure Recovery, Concurrent Generation Requests, and Edge Case Rejection.
"""

import pytest
import concurrent.futures
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_zero_and_negative_amounts_rejected():
    """Verify that requests with invalid, zero, or negative amounts fail with 422 Unprocessable Entity."""
    # Zero amount
    res_zero = client.post(
        "/api/v1/portfolio-generation-requests",
        json={"investment_amount": 0.0, "investment_horizon_months": 36},
    )
    assert res_zero.status_code == 422

    # Negative amount
    res_neg = client.post(
        "/api/v1/portfolio-generation-requests",
        json={"investment_amount": -50000.0, "investment_horizon_months": 36},
    )
    assert res_neg.status_code == 422

    # Below minimum capital (< 1000)
    res_min = client.post(
        "/api/v1/portfolio-generation-requests",
        json={"investment_amount": 500.0, "investment_horizon_months": 36},
    )
    assert res_min.status_code == 422


def test_conflicting_constraints_handled_gracefully():
    """Verify that contradictory or impossible constraint sets produce clean 422 failures rather than server crashes."""
    # Exclude all sectors
    res = client.post(
        "/api/v1/portfolio-generation-requests",
        json={
            "investment_amount": 100000.0,
            "preferences": {
                "excluded_sectors": [
                    "Energy & Petrochemicals",
                    "Information Technology",
                    "Banking & Financial Services",
                    "Automotive",
                    "Healthcare & Pharmaceuticals",
                    "Fast Moving Consumer Goods",
                    "Consumer Discretionary",
                    "Infrastructure & Capital Goods",
                    "Metals & Mining",
                    "Power & Utilities",
                    "Specialty Chemicals",
                    "Telecommunications",
                    "Illustrative Consumer Sector",
                    "Illustrative Technology Sector",
                    "Illustrative Healthcare Sector",
                ],
                "max_single_stock_weight_pct": 5.0,
            },
        },
    )
    # Must fail gracefully with 422 without raising an unhandled 500
    assert res.status_code == 422
    assert "failed" in res.json()["detail"].lower()


def test_concurrent_portfolio_generation_requests():
    """Verify that concurrent portfolio generation requests execute atomically and produce unique versions."""
    def send_request(index):
        c = TestClient(app)
        return c.post(
            "/api/v1/portfolio-generation-requests",
            json={
                "portfolio_name": f"Concurrent Portfolio {index}",
                "investment_amount": 100000.0 + (index * 10000),
                "investment_horizon_months": 36,
                "preferences": {"max_single_stock_weight_pct": 25.0, "max_sector_weight_pct": 40.0},
            },
        )

    # Launch 4 concurrent requests in a thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(send_request, i) for i in range(4)]
        responses = [f.result() for f in futures]

    for r in responses:
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["version_status"] == "generated"
        assert len(data["holdings"]) >= 3

    # All generated version IDs must be distinct
    version_ids = [r.json()["portfolio_version_id"] for r in responses]
    assert len(set(version_ids)) == 4, "Concurrent requests must produce distinct version IDs"
