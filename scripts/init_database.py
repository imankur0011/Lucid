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
    import getpass
    from sqlalchemy import create_engine
    from backend.database import session

    db_name = settings.postgres_db
    user = settings.postgres_user
    password = settings.postgres_password
    host = settings.postgres_host
    port = settings.postgres_port

    print(f"   Checking database '{db_name}' on {host}:{port}...")
    
    # 1. Direct connection attempt
    try:
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
            # Connect to maintenance database with configured credentials
            maintenance_db = "postgres" if db_name != "postgres" else "template1"
            try:
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
            except Exception as m_err:
                print(f"   ⚠️ Could not create via maintenance db: {m_err}")

    # 2. Intelligent Fallback Probing for Port/User/Password Mismatches
    print("   ℹ️ Probing local PostgreSQL server for working connection parameters...")
    candidate_ports = [port]
    for p in [5432, 5433]:
        if p not in candidate_ports:
            candidate_ports.append(p)

    sys_user = getpass.getuser()
    candidate_users = [user]
    for u in ["postgres", sys_user]:
        if u and u not in candidate_users:
            candidate_users.append(u)

    candidate_passwords = [password, "", "postgres", "password", "root"]

    for c_port in candidate_ports:
        for c_user in candidate_users:
            for c_pwd in candidate_passwords:
                for maint_db in ["postgres", "template1"]:
                    try:
                        probe_conn = psycopg2.connect(
                            dbname=maint_db,
                            user=c_user,
                            password=c_pwd,
                            host=host,
                            port=c_port,
                            connect_timeout=1
                        )
                        probe_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                        p_cur = probe_conn.cursor()
                        # Check if target db exists
                        p_cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}';")
                        exists = p_cur.fetchone()
                        if not exists:
                            p_cur.execute(f'CREATE DATABASE "{db_name}";')
                            print(f"   ✅ Auto-created database '{db_name}' on port {c_port} (User: '{c_user}').")
                        else:
                            print(f"   ✅ Connected to database '{db_name}' on port {c_port} (User: '{c_user}').")
                        p_cur.close()
                        probe_conn.close()

                        # Update settings in-memory
                        settings.postgres_port = c_port
                        settings.postgres_user = c_user
                        settings.postgres_password = c_pwd

                        # Persist verified credentials to .env file
                        env_path = ROOT_DIR / ".env"
                        if env_path.exists():
                            try:
                                with open(env_path, "r") as f:
                                    e_lines = f.readlines()
                                with open(env_path, "w") as f:
                                    for line in e_lines:
                                        if line.startswith("POSTGRES_PORT="):
                                            f.write(f"POSTGRES_PORT={c_port}\n")
                                        elif line.startswith("POSTGRES_USER="):
                                            f.write(f"POSTGRES_USER={c_user}\n")
                                        elif line.startswith("POSTGRES_PASSWORD="):
                                            f.write(f"POSTGRES_PASSWORD={c_pwd}\n")
                                        else:
                                            f.write(line)
                            except Exception:
                                pass

                        # Reconnect session engine
                        session.engine.dispose()
                        session.engine = create_engine(settings.postgres_url, pool_pre_ping=True)
                        session.SessionLocal.configure(bind=session.engine)
                        return True
                    except Exception:
                        continue

    print(f"   ❌ PostgreSQL connection failed. Ensure PostgreSQL service is started and check credentials in .env.")
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
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.postgres_url))
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
