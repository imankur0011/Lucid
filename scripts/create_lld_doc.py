#!/usr/bin/env python3
"""
Generates the comprehensive LOW_LEVEL_DESIGN.md document for Lucid.
Extracts live schema details from SQLAlchemy models and OpenAPI routes from FastAPI.
"""

import sys
from pathlib import Path

ROOT_DIR = Path('/Users/ankur/Documents/MajorProject/app')
sys.path.insert(0, str(ROOT_DIR))

from backend.models import Base
from backend.main import app

def generate_lld():
    print("Generating LOW_LEVEL_DESIGN.md...")
    output_path = ROOT_DIR / "LOW_LEVEL_DESIGN.md"

    # Gather database metadata
    tables = Base.metadata.tables
    print(f"Extracted {len(tables)} tables from SQLAlchemy Base.metadata.")

    # Gather OpenAPI routes
    openapi = app.openapi()
    paths = openapi.get("paths", {})
    print(f"Extracted {len(paths)} unique paths from FastAPI openapi.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Lucid — Complete Low-Level Design (LLD) Specification\n\n")
        f.write("**Document Version:** 2026.11-v2.0  \n")
        f.write("**Authoritative Date:** 2026-11-08  \n")
        f.write("**Target Audience:** Software Engineers, Backend/AI Developers, Database Administrators, System Integrators  \n")
        f.write("**Scope:** Module-, class-, function-, API-, schema-, algorithm-, and database-level implementation specification for the Lucid Indian Equity Portfolio Management Platform.  \n\n")
        f.write("---\n\n")

        # Table of Contents
        f.write("## Table of Contents\n\n")
        f.write("1. [Codebase Structure & Repository Layout](#1-codebase-structure--repository-layout)\n")
        f.write("2. [Backend Entry Point & Application Initialization](#2-backend-entry-point--application-initialization)\n")
        f.write("3. [API Design & Implementation (82 Endpoints Inventory)](#3-api-design--implementation-82-endpoints-inventory)\n")
        f.write("4. [Frontend Architecture & Component Implementation](#4-frontend-architecture--component-implementation)\n")
        f.write("5. [Service-Layer Design & Class Specifications](#5-service-layer-design--class-specifications)\n")
        f.write("6. [Agent Node Implementation & Execution Mechanics](#6-agent-node-implementation--execution-mechanics)\n")
        f.write("7. [Database Low-Level Design (62-Table Specification)](#7-database-low-level-design-62-table-specification)\n")
        f.write("8. [Detailed API Contracts & Pydantic Schemas](#8-detailed-api-contracts--pydantic-schemas)\n")
        f.write("9. [Algorithm & Quantitative Business-Logic Design](#9-algorithm--quantitative-business-logic-design)\n")
        f.write("10. [Error Handling, Validation & Exception Design](#10-error-handling-validation--exception-design)\n")
        f.write("11. [Security Implementation Details & Cryptographic Guardrails](#11-security-implementation-details--cryptographic-guardrails)\n")
        f.write("12. [Concurrency, Background Processing & Session Scoping](#12-concurrency-background-processing--session-scoping)\n")
        f.write("13. [LLD Sequence & Component Interaction Diagrams](#13-lld-sequence--component-interaction-diagrams)\n\n")
        f.write("---\n\n")

        # Section 1
        f.write("## 1. Codebase Structure & Repository Layout\n\n")
        f.write("The Lucid codebase follows a strictly modular monorepo architecture separating the backend service layer, multi-agent intelligence pipeline, quantitative math engine, relational persistence layer, and React 19 presentation layer.\n\n")
        f.write("```\n")
        f.write("app/\n")
        f.write("├── backend/                        # FastAPI Core Backend & Services\n")
        f.write("│   ├── main.py                     # Application entry point, lifespan, CORS, middleware\n")
        f.write("│   ├── config.py                   # Pydantic BaseSettings, env vars, Argon2id/JWT params\n")
        f.write("│   ├── database.py                 # SQLAlchemy engine, sessionmaker, scoped session dependency\n")
        f.write("│   ├── api/v1/                     # Modular API Routers (9 Routers, 82 Endpoints)\n")
        f.write("│   │   ├── auth.py                 # Argon2id authentication, JWT, token revocation, profile\n")
        f.write("│   │   ├── diagnosis.py            # Demat statement upload, CSV parser, HHI analysis, copilot\n")
        f.write("│   │   ├── goals.py                # Financial goals CRUD and horizon tracking\n")
        f.write("│   │   ├── links.py                # External regulatory link verification and audit\n")
        f.write("│   │   ├── market_data.py          # Exchange universe sync, live price feed, macro indicators\n")
        f.write("│   │   ├── notifications.py        # System alerts, drift warnings, unread counters\n")
        f.write("│   │   ├── portfolios.py           # Portfolio generation, versioning, monitoring, rebalancing\n")
        f.write("│   │   ├── profile.py              # Investor profile extraction, risk history, account deletion\n")
        f.write("│   │   └── risk_assessments.py     # 8-question psychometric evaluation, risk score computation\n")
        f.write("│   ├── agent/                      # LangGraph Multi-Agent Orchestration\n")
        f.write("│   │   ├── graph.py                # StateGraph assembly, conditional routing, rework loops\n")
        f.write("│   │   ├── nodes.py                # 13 agent node implementations (Manager to Persistence)\n")
        f.write("│   │   ├── schemas.py              # Strict Pydantic agent input/output schemas & evidence models\n")
        f.write("│   │   ├── state.py                # PortfolioAgentState TypedDict (35 typed state fields)\n")
        f.write("│   │   └── tools.py                # Fiduciary research tools, DB query tools, factor filters\n")
        f.write("│   ├── portfolio_engine/           # Quantitative & Financial Computation Services\n")
        f.write("│   │   ├── optimizer.py            # SciPy SLSQP mean-variance numerical optimizer\n")
        f.write("│   │   ├── allocation_rounding.py  # Whole-share integer rounding & residual cash allocator\n")
        f.write("│   │   ├── candidate_selection.py  # Liquidity, market-cap, and financial health screening\n")
        f.write("│   │   ├── constraints.py          # Single-stock, sector, cash, and turnover bounds\n")
        f.write("│   │   ├── factors.py              # Winsorized Z-score multi-factor composite models\n")
        f.write("│   │   ├── feasibility.py          # Pre-optimization feasibility and capital checks\n")
        f.write("│   │   ├── math_engine.py          # Covariance matrix, volatility, Sharpe, Sortino computation\n")
        f.write("│   │   ├── monitoring_service.py   # NAV valuation, asset/sector drift, tracking error\n")
        f.write("│   │   ├── policy.py               # SEBI-aligned risk capacity vs willingness constraints\n")
        f.write("│   │   ├── rebalancing_service.py  # Minimum turnover trade generator, transaction friction preview\n")
        f.write("│   │   ├── risk_metrics.py         # Value at Risk (VaR), Conditional VaR, Max Drawdown\n")
        f.write("│   │   ├── service.py              # High-level portfolio generation orchestrator\n")
        f.write("│   │   ├── stock_why_service.py    # Two-level stock-specific justification synthesis\n")
        f.write("│   │   ├── transaction_costs.py    # Indian statutory friction (STT, GST, SEBI fee, Stamp Duty)\n")
        f.write("│   │   └── validators.py           # Post-optimization hard constraint verification\n")
        f.write("│   ├── market_data/                # Market Ingestion & Regime Detection\n")
        f.write("│   │   ├── exchange_universe_sync.py # NSE EQUITY_L.csv full universe synchronization (2,639 stocks)\n")
        f.write("│   │   └── regime.py               # India VIX & Nifty 50 moving-average regime classifier\n")
        f.write("│   ├── services/                   # Utility & Supporting Micro-Services\n")
        f.write("│   │   ├── account_deletion_service.py # Cascading GDPR/DPDP compliant user account purge\n")
        f.write("│   │   ├── company_resolution_service.py # Trigram/Levenshtein company name to ISIN resolver\n")
        f.write("│   │   ├── exchange_registry.py    # Exchange trading calendars and holiday schedules\n")
        f.write("│   │   ├── financial_number_parser.py # Indian numeric notation parser (Crore, Lakh, K, %)\n")
        f.write("│   │   ├── link_verification_service.py # Official regulatory URL integrity validator\n")
        f.write("│   │   ├── monitoring_scheduler.py # Background APScheduler/asyncio monitoring loop (300s cycle)\n")
        f.write("│   │   └── notification_service.py # System alert generator, read receipt tracker\n")
        f.write("│   ├── middleware/                 # Custom HTTP Middlewares\n")
        f.write("│   │   └── rate_limit.py           # In-memory sliding-window token bucket rate limiter\n")
        f.write("│   └── models/                     # SQLAlchemy 2.0 Relational Data Models (62 Domain Tables)\n")
        f.write("├── frontend/                       # Next.js 16.4.2 React 19 Client Application\n")
        f.write("│   ├── src/\n")
        f.write("│   │   ├── app/                    # Next.js App Router (layout.tsx, page.tsx)\n")
        f.write("│   │   ├── components/             # React 19 UI Components (24 Modular Views & Modals)\n")
        f.write("│   │   └── lib/                    # API client (Axios), design tokens, link helpers\n")
        f.write("├── database/                       # PostgreSQL Migrations & Seed Dumps\n")
        f.write("│   └── migrations/                 # Alembic versioned migration scripts\n")
        f.write("├── scripts/                        # Automated Verification & Operations Tooling\n")
        f.write("│   ├── validate_documentation.py   # Multi-step repo consistency validator\n")
        f.write("│   ├── verify_setup.py             # System dependency and database connectivity check\n")
        f.write("│   └── validate_env.py             # Environment variable and secret auditor\n")
        f.write("└── docs/                           # Architecture, Methodology, and Design Documentation\n")
        f.write("```\n\n")

        print("Section 1 written.")
    print("Base LLD generated.")

if __name__ == "__main__":
    generate_lld()
