#!/usr/bin/env python3
"""
Lucid — Reference Data & Security Master Seeder.
Populates:
1. SEBI-aligned Psychometric Risk Assessment Questionnaire
2. Full Exchange Security Master (NSE EQUITY_L 2,639 listed equities)
3. Benchmark Economic Indicators & India VIX
4. Development Sandbox Demo User
"""

import sys
import os
from pathlib import Path

# Add project root to path
APP_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(APP_DIR))

from backend.database.session import SessionLocal, engine
from backend.models import (
    Security,
    Company,
    InstrumentListing,
    RiskQuestion,
    AppUser,
    EconomicIndicator,
)
from backend.seed.seed_questionnaire import seed_risk_questions
from backend.market_data.exchange_universe_sync import sync_full_exchange_universe
from backend.market_data.regime import seed_market_indicators_and_news
from backend.auth.utils import get_password_hash


def seed_development_user(db):
    """Ensures a safe local development test user exists."""
    email = "developer@lucid.local"
    user = db.query(AppUser).filter(AppUser.email == email).first()
    if not user:
        user = AppUser(
            email=email,
            hashed_password=get_password_hash("LucidDevPass123!"),
            full_name="Lucid Local Developer",
            is_active=True,
            is_verified=True,
            role="investor",
        )
        db.add(user)
        db.commit()
        print(f"   ✅ Created development user: {email} (Password: LucidDevPass123!)")
    else:
        print(f"   ℹ️ Development user already exists: {email}")


def main():
    print("=================================================================")
    print("🚀 Seeding Lucid Reference Data & Full Security Master")
    print("=================================================================")

    db = SessionLocal()
    try:
        # 1. Seed Risk Assessment Questionnaire
        print("\n[1/4] Seeding SEBI Risk Assessment Questionnaire...")
        q_count = db.query(RiskQuestion).count()
        if q_count == 0:
            seed_risk_questions(db)
            print("   ✅ Risk assessment questions and weighted scoring options seeded.")
        else:
            print(f"   ℹ️ Risk questionnaire already populated ({q_count} questions present).")

        # 2. Seed Macroeconomic Indicators & News
        print("\n[2/4] Seeding Macro Indicators, Policy Rates, and Market News...")
        seed_market_indicators_and_news(db)
        print("   ✅ RBI Repo Rate, India VIX, and market news baseline seeded.")

        # 3. Synchronize Full Exchange Universe (NSE + BSE)
        print("\n[3/4] Synchronizing Full NSE/BSE Equity Security Master...")
        sync_res = sync_full_exchange_universe(db)
        print(f"   ✅ Security Master Synchronized: {sync_res['status']}")

        # 4. Seed Local Development User
        print("\n[4/4] Ensuring Local Development User Account...")
        seed_development_user(db)

        # Print Database Verification Summary
        total_sec = db.query(Security).count()
        total_comp = db.query(Company).count()
        total_list = db.query(InstrumentListing).count()

        print("\n=================================================================")
        print("🎉 Database Reference Seeding Complete!")
        print(f"   - Total Companies:       {total_comp}")
        print(f"   - Total Securities:      {total_sec}")
        print(f"   - Total Listings:        {total_list}")
        print("=================================================================")
    except Exception as exc:
        print(f"\n❌ Error during seeding: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

