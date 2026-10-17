"""
FastAPI Application Entry Point.
Integrates SQLAlchemy database, LangGraph orchestrator, and agent pipeline.
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List

try:
    from backend.config import settings
    from backend.database import engine, get_db
    from backend.models import (
        Security,
        Company,
        InstrumentListing,
        Sector,
        Industry,
        InvestorPortfolio,
        AppUser,
    )
    from backend.api.v1 import api_v1_router
except ImportError:
    from config import settings
    from database import engine, get_db
    from models import (
        Security,
        Company,
        InstrumentListing,
        Sector,
        Industry,
        InvestorPortfolio,
        AppUser,
    )
    from api.v1 import api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print(f"🚀 Starting Major Project Backend ({settings.app_env})")
    print(f"   LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    print(f"   Neo4j: {settings.neo4j_uri}")
    print(f"   PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    # Verify Database Connection
    try:
        with engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            ).scalar()
            print(f"   ✅ PostgreSQL Connected: {table_count} tables active")
    except Exception as exc:
        print(f"   ⚠️ PostgreSQL Connection warning: {exc}")

    yield

    print("👋 Shutting down...")


app = FastAPI(
    title="Intelligent Portfolio Creation API",
    description=(
        "Agentic AI framework for intelligent portfolio creation "
        "by capturing the experience of Indian mutual fund managers."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 Routes
app.include_router(api_v1_router)


@app.get("/")
async def root():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "Major Project API",
        "version": "0.1.0",
        "environment": settings.app_env,
    }


@app.get("/api/health")
async def health(db: Session = Depends(get_db)):
    """Health check with database connectivity status."""
    db_status = "unhealthy"
    table_count = 0
    try:
        table_count = db.execute(
            text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
        ).scalar() or 0
        db_status = "healthy"
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    response = {
        "api": "up",
        "environment": settings.app_env,
        "database": {"status": db_status},
    }

    # Only expose detailed infrastructure metadata in non-production environments
    if settings.app_env != "production":
        response["database"].update({
            "host": settings.postgres_host,
            "port": settings.postgres_port,
            "database": settings.postgres_db,
            "total_tables": table_count,
        })
        response["llm_provider"] = settings.llm_provider
        response["llm_model"] = settings.llm_model

    return response


@app.get("/api/db/stats")
async def db_stats(db: Session = Depends(get_db)):
    """Returns database summary statistics across core domain entities (dev diagnostic)."""
    if settings.app_env == "production":
        raise HTTPException(status_code=403, detail="Diagnostic endpoint disabled in production.")

    return {
        "users": db.query(AppUser).count(),
        "securities": db.query(Security).count(),
        "companies": db.query(Company).count(),
        "listings": db.query(InstrumentListing).count(),
        "sectors": db.query(Sector).count(),
        "industries": db.query(Industry).count(),
        "portfolios": db.query(InvestorPortfolio).count(),
    }


@app.get("/api/securities")
async def list_securities(db: Session = Depends(get_db)):
    """List securities with company details and exchange listings."""
    securities = db.query(Security).all()
    result = []
    for sec in securities:
        result.append({
            "security_id": str(sec.security_id),
            "security_name": sec.security_name,
            "isin": sec.isin,
            "security_type": sec.security_type,
            "currency": sec.currency_code,
            "status": sec.security_status,
            "company_name": sec.company.legal_name if sec.company else None,
            "listings": [
                {
                    "listing_id": str(l.listing_id),
                    "symbol": l.symbol,
                    "trading_status": l.trading_status,
                }
                for l in sec.listings
            ],
        })
    return {"count": len(result), "securities": result}
