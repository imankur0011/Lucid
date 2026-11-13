"""
FastAPI Application Entry Point.
Integrates SQLAlchemy database, LangGraph orchestrator, and agent pipeline.
"""

import sys

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

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    from backend.middleware.rate_limit import InMemoryRateLimiterMiddleware
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
    from middleware.rate_limit import InMemoryRateLimiterMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    print(f"[+] Starting Lucid Backend ({settings.app_env})")
    print(f"   LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    print(f"   PostgreSQL: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

    # Validate Security Keys in non-dev environments
    settings.validate_security_keys()

    # Verify Database Connection
    try:
        with engine.connect() as conn:
            table_count = conn.execute(
                text("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")
            ).scalar()
            print(f"   [OK] PostgreSQL Connected: {table_count} tables active")
    except Exception as exc:
        print(f"   [WARN] PostgreSQL Connection warning: {exc}")

    # Launch Unattended Background Portfolio Monitoring Scheduler
    scheduler = None
    try:
        from backend.services.monitoring_scheduler import BackgroundMonitoringScheduler
        scheduler = BackgroundMonitoringScheduler(interval_seconds=300)
        scheduler.start()
        print("   [OK] Background Monitoring Scheduler Active (300s cycle, IST 09:15-15:30 window)")
    except Exception as exc:
        print(f"   [WARN] Background Monitoring Scheduler failed to start: {exc}")

    yield

    if scheduler:
        scheduler.stop()
    print("[-] Shutting down...")


app = FastAPI(
    title="Intelligent Portfolio Creation API",
    description=(
        "Agentic AI framework for intelligent portfolio creation "
        "by capturing the experience of Indian mutual fund managers."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware - allows both localhost and 127.0.0.1 on all development ports (3000, 3001, etc.)
allowed_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
for fallback_origin in ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"]:
    if fallback_origin not in allowed_origins:
        allowed_origins.append(fallback_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# In-Memory Rate Limiting middleware (protects auth and expensive AI generation)
app.add_middleware(InMemoryRateLimiterMiddleware, enabled=True)


def _cors_error_response(request: Request, status_code: int, detail: str) -> JSONResponse:
    """
    Returns a JSONResponse with CORS headers injected manually.
    FastAPI's CORSMiddleware only adds Access-Control-Allow-Origin on successful
    responses that pass through the middleware chain normally. When an unhandled
    exception propagates before a response is built (e.g. 500 Internal Server Error),
    Starlette sends a plain response with no CORS headers, causing the browser to
    report a CORS error instead of the actual 500. This helper injects the correct
    origin header on every error response so browsers always see the real error.
    """
    origin = request.headers.get("origin", "")
    response = JSONResponse(status_code=status_code, content={"detail": detail})
    is_local_origin = any(h in origin for h in ("localhost", "127.0.0.1", "[::1]")) if origin else False
    if origin and (origin in allowed_origins or is_local_origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    elif allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = allowed_origins[0]
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler that prints traceback to stderr and injects CORS headers on unhandled 500 errors."""
    import traceback
    traceback.print_exc(file=sys.stderr)
    err_detail = f"{type(exc).__name__}: {str(exc)}" if settings.app_env == "development" else f"{type(exc).__name__}"
    return _cors_error_response(request, 500, f"Internal server error: {err_detail}")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTPException handler that also injects CORS headers."""
    return _cors_error_response(request, exc.status_code, exc.detail)


@app.middleware("http")
async def add_security_headers(request, call_next):
    """Adds enterprise security headers to all HTTP responses, guaranteeing CORS headers on exceptions."""
    try:
        response = await call_next(request)
    except Exception as exc:
        import traceback
        traceback.print_exc(file=sys.stderr)
        err_detail = f"{type(exc).__name__}: {str(exc)}" if settings.app_env == "development" else f"{type(exc).__name__}"
        response = _cors_error_response(request, 500, f"Internal server error: {err_detail}")

    origin = request.headers.get("origin", "")
    if origin and "access-control-allow-origin" not in response.headers and "Access-Control-Allow-Origin" not in response.headers:
        is_local = any(h in origin for h in ("localhost", "127.0.0.1", "[::1]"))
        if is_local or origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if settings.app_env in ("production", "staging"):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


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


@app.get("/health")
@app.get("/api/health")
async def health(db: Session = Depends(get_db)):
    """Health check with database connectivity status. Serves both /health (ALB/Nginx) and /api/health."""
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

    # Only expose detailed infrastructure metadata in development environment
    if settings.app_env == "development":
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
    """Returns database summary statistics across core domain entities (dev diagnostic only)."""
    if settings.app_env in ("production", "staging"):
        raise HTTPException(status_code=403, detail="Diagnostic endpoint disabled in non-development environments.")

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
