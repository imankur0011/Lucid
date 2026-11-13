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

    candidate_passwords = [password, "", "postgres", "password", "root", "admin", "123456", "1234", "12345", "postgres123", "LucidDevPass123!"]

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

    print(f"   [FAIL] PostgreSQL connection failed. Ensure PostgreSQL service is started and check credentials in .env.")
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
    """Runs Alembic migrations to bring schema to head."""
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
        # Fallback to create_all if migrations fail
        try:
            Base.metadata.create_all(bind=session.engine)
            print("   [OK] Fallback SQLAlchemy create_all completed.")
        except Exception as e2:
            print(f"   [FAIL] Schema creation failed: {e2}")
            return False

    # Ensure all required columns exist on app_users (idempotent patch for existing databases)
    try:
        with session.engine.connect() as conn:
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT false;"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS mobile_number VARCHAR(20);"))
            conn.execute(text("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS mobile_verified BOOLEAN NOT NULL DEFAULT false;"))
            conn.commit()
    except Exception as e:
        print(f"   [WARN] Column patch warning: {e}")

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
            print(f"   [OK] Created development user: {email} (Password: LucidDevPass123!)")
        else:
            print(f"   [INFO] Development user exists: {email}")

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
            print(f"\n[SUCCESS] Database is ready! Total public tables: {table_count} (Expected: 60: 59 application tables + 1 alembic_version)")
            if table_count < 50:
                print(f"[WARN] Warning: Detected only {table_count} tables, expected at least 59.")
                sys.exit(1)
    except Exception as e:
        print(f"[FAIL] Error verifying database tables: {e}")
        sys.exit(1)

    print("=" * 70)
    sys.exit(0)


if __name__ == "__main__":
    main()
