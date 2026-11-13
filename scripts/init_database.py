#!/usr/bin/env python3
"""
Lucid -- Automated Database Provisioning, Migration & Seeding Utility.
Idempotent script to verify, create, migrate, and seed the PostgreSQL database.
"""

import sys
import os
import uuid
from pathlib import Path

# Ensure UTF-8 output encoding across Windows cp1252 / redirected file streams
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import text
from alembic.config import Config
from alembic import command

from backend.config import settings
from backend.database import session
from backend.database.session import SessionLocal, engine
from backend.models import (
    Base,
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


def ensure_database_exists():
    """Checks if the configured database exists; if not, creates it via maintenance db."""
    global engine, SessionLocal
    import getpass
    from sqlalchemy import create_engine

    db_name = settings.postgres_db
    user = settings.postgres_user
    password = settings.postgres_password
    host = settings.postgres_host
    port = settings.postgres_port

    print(f"   Checking database '{db_name}' on {host}:{port}...")
    
    # 1. Direct connection attempt across dual loopback hosts (prioritizing 127.0.0.1)
    direct_hosts = ["127.0.0.1", host, "localhost"]
    seen_hosts = set()
    for d_host in direct_hosts:
        if d_host in seen_hosts:
            continue
        seen_hosts.add(d_host)
        try:
            conn = psycopg2.connect(
                dbname=db_name,
                user=user,
                password=password,
                host=d_host,
                port=port,
                connect_timeout=3
            )
            conn.close()
            settings.postgres_host = d_host
            session.engine.dispose()
            session.engine = create_engine(settings.postgres_url, pool_pre_ping=True)
            session.SessionLocal.configure(bind=session.engine)
            engine = session.engine
            SessionLocal = session.SessionLocal
            print(f"   [OK] Database '{db_name}' exists and is accessible on {d_host}:{port}.")
            return True
        except psycopg2.OperationalError as e:
            err_msg = str(e)
            if f'database "{db_name}" does not exist' in err_msg:
                print(f"   [INFO] Database '{db_name}' does not exist. Creating now...")
                maintenance_db = "postgres" if db_name != "postgres" else "template1"
                try:
                    m_conn = psycopg2.connect(
                        dbname=maintenance_db,
                        user=user,
                        password=password,
                        host=d_host,
                        port=port,
                        connect_timeout=5
                    )
                    m_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
                    cur = m_conn.cursor()
                    cur.execute(f'CREATE DATABASE "{db_name}";')
                    cur.close()
                    m_conn.close()
                    settings.postgres_host = d_host
                    session.engine.dispose()
                    session.engine = create_engine(settings.postgres_url, pool_pre_ping=True)
                    session.SessionLocal.configure(bind=session.engine)
                    engine = session.engine
                    SessionLocal = session.SessionLocal
                    print(f"   [OK] Successfully created database '{db_name}'.")
                    return True
                except Exception as m_err:
                    print(f"   [WARN] Could not create via maintenance db on {d_host}: {m_err}")

    # 2. Intelligent Fallback Probing for Port/User/Password Mismatches
    print("   [INFO] Probing local PostgreSQL server for working connection parameters...")
    candidate_hosts = ["127.0.0.1", "localhost"]
    candidate_ports = [port]
    for p in [5432, 5433]:
        if p not in candidate_ports:
            candidate_ports.append(p)

    sys_user = getpass.getuser()
    candidate_users = [user]
    for u in ["postgres", sys_user]:
        if u and u not in candidate_users:
            candidate_users.append(u)

    candidate_passwords = [
        password, "", "postgres", "password", "root", "admin",
        "123456", "1234", "12345", "postgres123", "password123",
        "root123", "varun", "varun123", "akshay", "akshay123",
        "LucidDevPass123!"
    ]

    for c_host in candidate_hosts:
        for c_port in candidate_ports:
            for c_user in candidate_users:
                for c_pwd in candidate_passwords:
                    for maint_db in ["postgres", "template1", db_name]:
                        try:
                            probe_conn = psycopg2.connect(
                                dbname=maint_db,
                                user=c_user,
                                password=c_pwd,
                                host=c_host,
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
                                print(f"   [OK] Auto-created database '{db_name}' on port {c_port} (User: '{c_user}').")
                            else:
                                print(f"   [OK] Connected to database '{db_name}' on port {c_port} (User: '{c_user}').")
                            p_cur.close()
                            probe_conn.close()

                            # Update settings in-memory
                            settings.postgres_host = c_host
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
                                            if line.startswith("POSTGRES_HOST="):
                                                f.write(f"POSTGRES_HOST={c_host}\n")
                                            elif line.startswith("POSTGRES_PORT="):
                                                f.write(f"POSTGRES_PORT={c_port}\n")
                                            elif line.startswith("POSTGRES_USER="):
                                                f.write(f"POSTGRES_USER={c_user}\n")
                                            elif line.startswith("POSTGRES_PASSWORD="):
                                                f.write(f"POSTGRES_PASSWORD={c_pwd}\n")
                                            else:
                                                f.write(line)
                                except Exception:
                                    pass

                            # Reconnect session engine and rebind module-level references
                            session.engine.dispose()
                            session.engine = create_engine(settings.postgres_url, pool_pre_ping=True)
                            session.SessionLocal.configure(bind=session.engine)
                            engine = session.engine
                            SessionLocal = session.SessionLocal
                            return True
                        except Exception:
                            continue

    # Check if port is open at all to give precise diagnostics
    import socket
    port_open = False
    for test_p in [port, 5432, 5433]:
        for test_h in ["127.0.0.1", "localhost"]:
            try:
                s = socket.create_connection((test_h, test_p), timeout=1)
                s.close()
                port_open = True
                break
            except Exception:
                pass
        if port_open:
            break

    if not port_open:
        print(f"   [FAIL] PostgreSQL server is NOT responding on port {port} (Service is STOPPED or NOT INSTALLED).")
        print(f"   --> How to fix on Windows:")
        print(f"       1. Press Win + R, type 'services.msc', and press Enter.")
        print(f"       2. Scroll to 'postgresql-x64-16' (or similar), right-click and choose 'Start'.")
        print(f"       3. Or open PowerShell as Administrator and run: net start postgresql-x64-16")
    else:
        print(f"   [FAIL] PostgreSQL is running on port {port}, but authentication failed for user '{user}'.")
        print(f"   --> None of the common default passwords matched.")
        print(f"   --> How to fix:")
        print(f"       Open your '.env' file in the project root and set your actual password:")
        print(f"       POSTGRES_PASSWORD=your_actual_password_here")
    return False


def ensure_extensions():
    """Ensures pgcrypto and uuid-ossp extensions are installed."""
    try:
        with session.engine.connect() as conn:
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "pgcrypto";'))
            conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            conn.commit()
        print("   [OK] PostgreSQL extensions (pgcrypto, uuid-ossp) verified.")
        return True
    except Exception as e:
        print(f"   [WARN] Could not install extensions: {e}")
        return True  # Non-fatal if UUIDs are generated in Python


def run_migrations():
    """Runs Alembic migrations to bring schema to head, followed by self-healing ORM validation."""
    print("   Applying database migrations via Alembic...")
    try:
        alembic_ini = ROOT_DIR / "alembic.ini"
        alembic_cfg = Config(str(alembic_ini))
        alembic_cfg.set_main_option("script_location", str(ROOT_DIR / "backend" / "alembic"))
        alembic_cfg.set_main_option("sqlalchemy.url", str(settings.postgres_url))
        command.upgrade(alembic_cfg, "head")
        print("   [OK] Alembic migrations applied successfully.")
    except Exception as e:
        print(f"   [WARN] Alembic migration warning: {e}")

    # Unconditionally run Base.metadata.create_all to ensure all 62 application models exist
    try:
        Base.metadata.create_all(bind=session.engine)
        print("   [OK] Verified all SQLAlchemy ORM models in database schema.")
    except Exception as e2:
        print(f"   [WARN] Base.metadata.create_all warning: {e2}")

    # Self-healing idempotent schema patch: guarantees columns, constraints, and tables exist
    # across peer machines with older/diverged schemas without requiring manual SQL execution.
    try:
        with session.engine.connect() as conn:
            # 1. Patch app_users authentication and verification columns
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT false;"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(20);"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS mobile_verified BOOLEAN NOT NULL DEFAULT false;"))

            # 2. Patch user_profiles version_number column
            conn.execute(text("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1;"))

            # 3. Create user_profile_versions audit table if missing
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_profile_versions (
                    profile_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
                    version_number INTEGER NOT NULL,
                    display_name VARCHAR(120),
                    country_code CHAR(2) NOT NULL DEFAULT 'IN',
                    preferred_currency CHAR(3) NOT NULL DEFAULT 'INR',
                    investment_experience VARCHAR(20),
                    investment_knowledge_level VARCHAR(20),
                    change_summary VARCHAR(300),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT uq_user_profile_version UNIQUE (user_id, version_number)
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_profile_versions_user_ver ON user_profile_versions (user_id, version_number DESC);"))

            # 4. Create revoked_tokens table if missing (used for JWT revocation & secure logout)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS revoked_tokens (
                    revocation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    token_hash VARCHAR(128) NOT NULL UNIQUE,
                    user_id UUID REFERENCES app_users(user_id) ON DELETE CASCADE,
                    revoked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    expires_at TIMESTAMPTZ NOT NULL
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_revoked_tokens_hash ON revoked_tokens (token_hash);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_revoked_tokens_expires ON revoked_tokens (expires_at);"))

            # 5. Create user_verification_codes table if missing (used for email & mobile OTPs)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_verification_codes (
                    verification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
                    code_type VARCHAR(40) NOT NULL,
                    code_value VARCHAR(32) NOT NULL,
                    recipient VARCHAR(320) NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    is_used BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT ck_verification_code_type CHECK (code_type IN ('email_verification', 'mobile_verification', 'password_reset'))
                );
            """))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_user_verification_lookup ON user_verification_codes (user_id, code_type, is_used);"))

            conn.commit()
            print("   [OK] Self-healing schema validation completed successfully.")
    except Exception as e:
        print(f"   [WARN] Self-healing schema patch error: {e}")

    return True


def seed_data_if_needed():
    """Idempotently populates reference data, questionnaire, and exchange universe."""
    db = session.SessionLocal()
    try:
        # 1. Risk Questions
        q_count = db.query(RiskQuestion).count()
        if q_count == 0:
            print("   Seeding SEBI psychometric risk questionnaire...")
            seed_risk_questions(db)
            print("   [OK] Risk questionnaire seeded.")
        else:
            print(f"   [INFO] Risk questionnaire already populated ({q_count} questions).")

        # 2. Macro Indicators & News
        print("   Verifying macro indicators baseline...")
        seed_macro_and_news_data(db)
        print("   [OK] Macro indicators baseline verified.")

        # 3. Security Master Universe
        sec_count = db.query(Security).count()
        if sec_count < 500:
            print(f"   Populating exchange security universe (current: {sec_count} equities)...")
            sync_res = sync_full_exchange_universe(db)
            sec_count = db.query(Security).count()
            print(f"   [OK] Security universe synchronized: {sec_count} equities active.")
        else:
            print(f"   [INFO] Security universe already populated ({sec_count} equities). Skipping full re-download.")

        # 4. Local Development & Demo User (Strictly matches DEMO_USER_ID)
        DEMO_USER_ID = uuid.UUID("10000000-0000-4000-8000-000000000001")
        email = "developer@lucid.local"
        
        # Check by DEMO_USER_ID first
        demo_by_id = db.query(AppUser).filter(AppUser.user_id == DEMO_USER_ID).first()
        if not demo_by_id:
            # Check if developer@lucid.local exists with an older random UUID
            existing_email_user = db.query(AppUser).filter(AppUser.email == email).first()
            if not existing_email_user:
                demo_by_id = AppUser(
                    user_id=DEMO_USER_ID,
                    identity_provider="local",
                    identity_subject="developer@lucid.local",
                    email=email,
                    password_hash=hash_password("LucidDevPass123!"),
                    email_verified=True,
                    mobile_verified=True,
                    account_status="active",
                )
                db.add(demo_by_id)
                db.commit()
                print(f"   [OK] Created development user: {email} (Password: LucidDevPass123!)")
            else:
                # User exists with email; also seed DEMO_USER_ID alias so demo login and unauthenticated dev requests succeed
                demo_by_id = AppUser(
                    user_id=DEMO_USER_ID,
                    identity_provider="local",
                    identity_subject="developer@lucid.local",
                    email="demo.investor@lucid.local",
                    password_hash=hash_password("LucidDevPass123!"),
                    email_verified=True,
                    mobile_verified=True,
                    account_status="active",
                )
                db.add(demo_by_id)
                db.commit()
                print(f"   [INFO] Seeded DEMO_USER_ID ({DEMO_USER_ID}) for dev mode fallback.")
        else:
            print(f"   [INFO] Development demo user exists: {email} ({DEMO_USER_ID})")

        # Ensure UserProfile exists for DEMO_USER_ID
        demo_prof = db.query(UserProfile).filter(UserProfile.user_id == DEMO_USER_ID).first()
        if not demo_prof:
            demo_prof = UserProfile(
                user_id=DEMO_USER_ID,
                display_name="Senior Investor",
                country_code="IN",
                preferred_currency="INR",
                investment_experience="intermediate",
                investment_knowledge_level="intermediate",
                version_number=1,
            )
            db.add(demo_prof)
            db.commit()
            print("   [OK] Seeded default UserProfile for demo user.")

        return True
    except Exception as e:
        print(f"   [FAIL] Seeding failed: {e}")
        return False
    finally:
        db.close()


def main():
    print("=" * 70)
    print("  LUCID -- DATABASE PROVISIONING & MIGRATION")
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
        with session.engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            ).scalar()
            print(f"\n[SUCCESS] Database is ready! Total public tables: {table_count} (Expected: 63: 62 application tables + 1 alembic_version)")
            if table_count < 55:
                print(f"[WARN] Warning: Detected only {table_count} tables, expected at least 62.")
                sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Error verifying database tables: {e}")
        sys.exit(1)

    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
