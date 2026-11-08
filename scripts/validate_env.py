#!/usr/bin/env python3
"""
Lucid — Developer Environment Validation Utility.
Verifies Python runtime, required packages, PostgreSQL connection,
database schema tables, and configuration settings before launching the application.
"""

import sys
import os
from pathlib import Path

# Set working directory to project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"

def check_python_version():
    v = sys.version_info
    print(f"\n[1/5] Checking Python Runtime...")
    if v.major == 3 and v.minor >= 11:
        print(f"   {PASS} Python {v.major}.{v.minor}.{v.micro} meets requirements (>= 3.11).")
        return True
    else:
        print(f"   {FAIL} Python {v.major}.{v.minor}.{v.micro} is unsupported. Python 3.11+ is required.")
        return False

def check_python_dependencies():
    print(f"\n[2/5] Checking Core Python Dependencies...")
    required = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn ASGI Server"),
        ("sqlalchemy", "SQLAlchemy 2.0 ORM"),
        ("psycopg2", "PostgreSQL Binary Driver"),
        ("pydantic", "Pydantic V2"),
        ("scipy", "SciPy Optimization Library"),
        ("numpy", "NumPy Numerical Engine"),
        ("pandas", "Pandas DataFrames"),
        ("yfinance", "Yahoo Finance Market Data"),
        ("langgraph", "LangGraph Agent Framework"),
        ("jwt", "PyJWT Token Handler"),
        ("passlib", "Passlib Password Security"),
    ]
    all_ok = True
    for module_name, display_name in required:
        try:
            __import__(module_name)
            print(f"   {PASS} {display_name} ({module_name}) installed.")
        except ImportError:
            print(f"   {FAIL} {display_name} ({module_name}) is MISSING. Run 'pip install -r backend/requirements.txt'.")
            all_ok = False
    return all_ok

def check_environment_file():
    print(f"\n[3/5] Checking Configuration & .env File...")
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        print(f"   {PASS} Found '.env' configuration file.")
    else:
        print(f"   {WARN} '.env' file not found. Copying from .env.example is recommended:")
        print("          cp .env.example .env")

    try:
        from backend.config import settings
        print(f"   {PASS} Settings loaded successfully:")
        print(f"          - Environment: {settings.app_env}")
        print(f"          - LLM Provider: {settings.llm_provider} ({settings.llm_model})")
        print(f"          - Database Host: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
        return True
    except Exception as exc:
        print(f"   {FAIL} Failed to parse configuration: {exc}")
        return False

def check_postgresql_connectivity():
    print(f"\n[4/5] Checking PostgreSQL Connectivity...")
    try:
        from sqlalchemy import text
        from backend.database.session import engine
        with engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            ).scalar()
            print(f"   {PASS} PostgreSQL connected successfully. Active public tables: {table_count}")
            if table_count < 60:
                print(f"   {WARN} Only {table_count} tables detected (expected 62). Run 'cd backend && alembic upgrade head'.")
            return True
    except Exception as exc:
        print(f"   {FAIL} Could not connect to PostgreSQL: {exc}")
        print("          Troubleshooting: Run 'brew services start postgresql@16' or verify POSTGRES_PORT and POSTGRES_PASSWORD.")
        return False

def check_security_master():
    print(f"\n[5/5] Checking Security Master & Reference Data...")
    try:
        from backend.database.session import SessionLocal
        from backend.models import Security, RiskQuestion
        db = SessionLocal()
        sec_count = db.query(Security).count()
        q_count = db.query(RiskQuestion).count()
        db.close()

        if sec_count >= 2600:
            print(f"   {PASS} Security Master populated with {sec_count} equities.")
        elif sec_count > 0:
            print(f"   {WARN} Security Master contains {sec_count} equities. To synchronize full 2,639 equities, run 'python database/seed_reference_data.py'.")
        else:
            print(f"   {FAIL} Security Master is empty (0 securities). Run 'python database/seed_reference_data.py'.")

        if q_count > 0:
            print(f"   {PASS} Risk assessment questions populated ({q_count} questions).")
        else:
            print(f"   {FAIL} Risk questionnaire empty. Run 'python database/seed_reference_data.py'.")

        return sec_count > 0 and q_count > 0
    except Exception as exc:
        print(f"   {FAIL} Could not query database entities: {exc}")
        return False

def main():
    print("=================================================================")
    print("🔍 Lucid — Developer Environment & Dependency Validator")
    print("=================================================================")

    ok1 = check_python_version()
    ok2 = check_python_dependencies()
    ok3 = check_environment_file()
    ok4 = check_postgresql_connectivity()
    ok5 = check_security_master()

    print("\n=================================================================")
    if ok1 and ok2 and ok3 and ok4 and ok5:
        print("🎉 ALL CHECKS PASSED! Lucid is ready to launch.")
        print("   - Start Backend:   cd backend && uvicorn backend.main:app --reload")
        print("   - Start Frontend:  cd frontend && npm run dev")
        print("=================================================================")
        sys.exit(0)
    else:
        print("⚠️  SOME CHECKS FAILED. Please review the diagnostic log above.")
        print("=================================================================")
        sys.exit(1)

if __name__ == "__main__":
    main()
