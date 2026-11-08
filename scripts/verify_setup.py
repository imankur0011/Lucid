#!/usr/bin/env python3
"""
Lucid — End-to-End Setup Verification Script.
Executes an automated health audit across Database, Models, API Routers, and Optimization.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database.session import SessionLocal, engine
from backend.models import Security, Company, InstrumentListing
from backend.portfolio_engine import optimize_portfolio_allocations, PortfolioConstraints
from backend.main import app

def main():
    print("=================================================================")
    print("🧪 Running Lucid End-to-End Setup Verification")
    print("=================================================================")

    # 1. Database & Security Universe
    db = SessionLocal()
    try:
        sec_count = db.query(Security).count()
        comp_count = db.query(Company).count()
        list_count = db.query(InstrumentListing).count()
        print(f"1. Database Master State:")
        print(f"   - Companies:       {comp_count} (Expected: ~2,639)")
        print(f"   - Securities:      {sec_count} (Expected: ~2,639)")
        print(f"   - Listings:        {list_count} (Expected: ~2,715)")
        assert sec_count >= 2600, "Security master underpopulated"
        print("   ✅ Security Master check PASSED")
    finally:
        db.close()

    # 2. FastAPI OpenAPI Route Compilation
    schema = app.openapi()
    paths = schema.get("paths", {})
    print(f"\n2. FastAPI OpenAPI Engine:")
    print(f"   - Total Endpoints: {len(paths)} unique paths compiled")
    assert len(paths) >= 80, "OpenAPI route count too low"
    print("   ✅ OpenAPI route compilation PASSED")

    # 3. Deterministic SciPy SLSQP Optimizer
    print(f"\n3. SciPy SLSQP Optimizer & Simplex Projection:")
    dummy_candidates = [
        {"symbol": "RELIANCE", "sector_name": "Energy", "latest_price": 2500.0, "alpha_score": 0.85},
        {"symbol": "TCS", "sector_name": "Technology", "latest_price": 3800.0, "alpha_score": 0.80},
        {"symbol": "HDFCBANK", "sector_name": "Financials", "latest_price": 1600.0, "alpha_score": 0.75},
        {"symbol": "INFY", "sector_name": "Technology", "latest_price": 1800.0, "alpha_score": 0.70},
        {"symbol": "ICICIBANK", "sector_name": "Financials", "latest_price": 1200.0, "alpha_score": 0.65},
    ]
    constraints = PortfolioConstraints(max_single_stock_pct=25.0, max_sector_pct=50.0, min_stocks_count=3)
    ok, allocs, msg = optimize_portfolio_allocations(dummy_candidates, "moderate", constraints)
    print(f"   - Optimizer Status: {ok} ({msg})")
    total_wt = sum(a["target_weight_pct"] for a in allocs)
    print(f"   - Sum of Weights:   {total_wt:.2f}% (Expected: 100.00%)")
    assert ok, "Optimization failed"
    assert abs(total_wt - 100.0) < 0.01, "Simplex budget invariant violated"
    print("   ✅ Deterministic SLSQP Optimization PASSED")

    print("\n=================================================================")
    print("🎉 ALL VERIFICATION CHECKS PASSED! System is 100% operational.")
    print("=================================================================")

if __name__ == "__main__":
    main()
