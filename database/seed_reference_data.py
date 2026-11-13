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
import uuid
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
    UserProfile,
    EconomicIndicator,
)
from backend.seed.seed_questionnaire import seed_risk_questions
from backend.market_data.exchange_universe_sync import sync_full_exchange_universe
from backend.market_data.regime import seed_macro_and_news_data
from backend.api.v1.auth import hash_password

DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")


def seed_development_user(db):
    """Ensures a safe local development test user and profile exist."""
    email = "developer@lucid.local"
    user = (
        db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
        or db.query(AppUser).filter(AppUser.email == email).first()
    )
    if not user:
        user = AppUser(
            user_id=DEMO_USER_ID,
            identity_provider="local-demo",
            identity_subject="demo-investor@lucid.local",
            email=email,
            password_hash=hash_password("LucidDevPass123!"),
            email_verified=True,
            mobile_verified=True,
            account_status="active",
        )
        db.add(user)
        db.flush()
        print(f"   ✅ Created development user: {email} (Password: LucidDevPass123!)")
    else:
        print(f"   ℹ️ Development user already exists: {email} ({user.user_id})")

    # Ensure UserProfile exists for this user
    prof = db.query(UserProfile).filter(UserProfile.user_id == user.user_id).first()
    if not prof:
        prof = UserProfile(
            user_id=user.user_id,
            display_name="Senior Investor",
            country_code="IN",
            preferred_currency="INR",
            investment_experience="intermediate",
            investment_knowledge_level="intermediate",
            version_number=1,
        )
        db.add(prof)
        print("   ✅ UserProfile initialized for development user.")

    # Also ensure canonical DEMO_USER_ID has UserProfile
    if user.user_id != DEMO_USER_ID:
        canon_prof = db.query(UserProfile).filter(UserProfile.user_id == DEMO_USER_ID).first()
        if not canon_prof:
            try:
                canon_prof = UserProfile(
                    user_id=DEMO_USER_ID,
                    display_name="Senior Investor",
                    country_code="IN",
                    preferred_currency="INR",
                    investment_experience="intermediate",
                    investment_knowledge_level="intermediate",
                    version_number=1,
                )
                db.add(canon_prof)
            except Exception:
                pass
    db.commit()


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

        # 2. Seed Local Development User (prioritized before long-running network sync)
        print("\n[2/4] Ensuring Local Development User Account and Profile...")
        seed_development_user(db)

        # 3. Seed Macroeconomic Indicators & News
        print("\n[3/4] Seeding Macro Indicators, Policy Rates, and Market News...")
        seed_macro_and_news_data(db)
        print("   ✅ RBI Repo Rate, India VIX, and market news baseline seeded.")

        # 4. Synchronize Full Exchange Universe (NSE + BSE)
        print("\n[4/4] Synchronizing Full NSE/BSE Equity Security Master...")
        sync_res = sync_full_exchange_universe(db)
        print(f"   ✅ Security Master Synchronized: {sync_res['status']}")

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

