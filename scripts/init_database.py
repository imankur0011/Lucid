#!/usr/bin/env python3
"""
Lucid — Automated Database Provisioning, Migration & Seeding Utility.
Idempotent script to verify, create, migrate, and seed the PostgreSQL database.
"""

import sys
import os
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from backend.config import settings
from backend.database.session import SessionLocal, engine
from backend.models import (
    Base,
    Security,
    Company,
    InstrumentListing,
    RiskQuestion,
    AppUser,
    EconomicIndicator,
)
from backend.seed.seed_questionnaire import seed_risk_questions
from backend.market_data.exchange_universe_sync import sync_full_exchange_universe
from backend.market_data.regime import seed_macro_and_news_data
from backend.api.v1.auth import hash_password


def ensure_database_exists():
    """Checks if the configured database exists; if not, creates it via maintenance db."""
    db_name = settings.postgres_db
    user = settings.postgres_user
    password = settings.postgres_password
    host = settings.postgres_host
    port = settings.postgres_port

    print(f"   Checking database '{db_name}' on {host}:{port}...")
    try:
        # First try direct connection
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=3
        )
        conn.close()
        print(f"   ✅ Database '{db_name}' exists and is accessible.")
        return True
    except psycopg2.OperationalError as e:
        err_msg = str(e)
        if f'database "{db_name}" does not exist' in err_msg:
            print(f"   ℹ️ Database '{db_name}' does not exist. Creating now...")
            # Connect to maintenance database
            maintenance_db = "postgres" if db_name != "postgres" else "template1"
            m_conn = psycopg2.connect(
                dbname=maintenance_db,
                user=user,
                password=password,
                host=host,
                port=port,
                connect_timeout=5
            )
            m_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cur = m_conn.cursor()
            cur.execute(f'CREATE DATABASE "{db_name}";')
            cur.close()
            m_conn.close()
            print(f"   ✅ Successfully created database '{db_name}'.")
            return True
        else:
            print(f"   ❌ PostgreSQL connection failed: {e}")
            return False


def ensure_extensions():
    """Ensures pgcrypto and uuid-ossp extensions are installed."""
    try:
        with engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.commit()
        print("   ✅ PostgreSQL extensions (pgcrypto, uuid-ossp) verified.")
        return True
    except Exception as e:
        print(f"   ⚠️ Could not install extensions: {e}")
        return True  # Non-fatal if UUIDs are generated in Python


def run_migrations():
    """Runs Alembic migrations to bring schema to head."""
    print("   Applying database migrations via Alembic...")
    try:
        alembic_ini = ROOT_DIR / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "backend" / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.database_url))
        command.upgrade(alembic_cfg, "head")
        print("   ✅ Alembic migrations applied successfully.")
        return True
    except Exception as e:
        print(f"   ⚠️ Alembic migration warning: {e}")
        # Fallback to create_all if migrations fail
        try:
            Base.metadata.create_all(bind=engine)
            print("   ✅ Fallback SQLAlchemy create_all completed.")
            return True
        except Exception as e2:
            print(f"   ❌ Schema creation failed: {e2}")
            return False


def seed_data_if_needed():
    """Idempotently populates reference data, questionnaire, and exchange universe."""
    db = SessionLocal()
    try:
        # 1. Risk Questions
        q_count = db.query(RiskQuestion).count()
        if q_count == 0:
            print("   Seeding SEBI psychometric risk questionnaire...")
            seed_risk_questions(db)
            print("   ✅ Risk questionnaire seeded.")
        else:
            print(f"   ℹ️ Risk questionnaire already populated ({q_count} questions).")

        # 2. Macro Indicators & News
        print("   Verifying macro indicators baseline...")
        seed_macro_and_news_data(db)
        print("   ✅ Macro indicators baseline verified.")

        # 3. Security Master Universe
        sec_count = db.query(Security).count()
        if sec_count < 500:
            print(f"   Populating exchange security universe (current: {sec_count} equities)...")
            sync_res = sync_full_exchange_universe(db)
            sec_count = db.query(Security).count()
            print(f"   ✅ Security universe synchronized: {sec_count} equities active.")
        else:
            print(f"   ℹ️ Security universe already populated ({sec_count} equities). Skipping full re-download.")

        # 4. Local Development User
        email = "developer@lucid.local"
        user = db.query(AppUser).filter(AppUser.email == email).first()
        if not user:
            user = AppUser(
                user_id=uuid.uuid4(),
                identity_provider="local",
                identity_subject="developer@lucid.local",
                email=email,
                password_hash=hash_password("LucidDevPass123!"),
                email_verified=True,
                mobile_verified=True,
                account_status="active",
            )
            db.add(user)
            db.commit()
            print(f"   ✅ Created development user: {email} (Password: LucidDevPass123!)")
        else:
            print(f"   ℹ️ Development user exists: {email}")

        return True
    except Exception as e:
        print(f"   ❌ Seeding failed: {e}")
        return False
    finally:
        db.close()


def main():
    print("=" * 70)
    print("  LUCID — DATABASE PROVISIONING & MIGRATION")
    print("=" * 70)

    if not ensure_database_exists():
        sys.exit(1)

    if not ensure_extensions():
        sys.exit(1)

    if not run_migrations():
        sys.exit(1)

    if not seed_data_if_needed():
        sys.exit(1)

    # Final table verification
    try:
        with engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            ).scalar()
            print(f"\n🎉 Database is ready! Total public tables: {table_count} (Expected: 62+1)")
            if table_count < 60:
                print(f"⚠️ Warning: Detected {table_count} tables, expected at least 62.")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Error verifying database tables: {e}")
        sys.exit(1)

    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
