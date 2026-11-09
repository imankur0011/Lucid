#!/usr/bin/env python3
"""
Lucid — System Architecture Specification Generator.
Aligns SYSTEM_ARCHITECTURE.md with sections 5.1 through 5.10 from Part 5 of prompt.
"""

import sys
from pathlib import Path

ROOT_DIR = Path('/Users/ankur/Documents/MajorProject/app')
sys.path.insert(0, str(ROOT_DIR))

def build_system_architecture():
    print("Building enhanced SYSTEM_ARCHITECTURE.md...")
    out_file = ROOT_DIR / "SYSTEM_ARCHITECTURE.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("""# Lucid — Complete System Architecture Specification

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Target Audience:** System Architects, Principal Engineers, Security Auditors, DevOps & Infrastructure Leads  
**Scope:** Authoritative 8-layer architectural blueprint of **Lucid**, an intelligent investment portfolio creation, monitoring, and rebalancing platform for Indian retail equities listed on NSE and BSE.

---

## Architectural Blueprint (8 Layers)

![Lucid 8-Layer System Architecture](SYSTEM_ARCHITECTURE.png)

```mermaid
graph TD
    classDef l1 fill:#F8FAFC,stroke:#0EA5E9,stroke-width:2px,color:#0F172A;
    classDef l2 fill:#EFF6FF,stroke:#3B82F6,stroke-width:2px,color:#1E3A8A;
    classDef l3 fill:#F5F3FF,stroke:#8B5CF6,stroke-width:2px,color:#4C1D95;
    classDef l4 fill:#FAF5FF,stroke:#A855F7,stroke-width:2px,color:#581C87;
    classDef l5 fill:#ECFDF5,stroke:#10B981,stroke-width:2px,color:#065F46;
    classDef l6 fill:#FFFBEB,stroke:#F59E0B,stroke-width:2px,color:#78350F;
    classDef l7 fill:#F1F5F9,stroke:#64748B,stroke-width:2px,color:#0F172A;
    classDef l8 fill:#FEF2F2,stroke:#EF4444,stroke-width:2px,color:#991B1B;

    subgraph L1 ["Layer 1: Client Presentation Layer (Next.js 16.4.2 React UI)"]
        UI_Dash["Investor Dashboard & NAV View"]:::l1
        UI_Gen["Portfolio Wizard & Risk Profiler"]:::l1
        UI_Mon["Continuous Monitoring & Drift Radar"]:::l1
        UI_Reb["Rebalance Execution & Order Preview"]:::l1
        UI_Diag["Demat Statement Diagnostics (HHI)"]:::l1
        UI_Chat["Copilot Chat & Fiduciary Stock-Why"]:::l1
    end

    subgraph L2 ["Layer 2: API Gateway & Middleware Layer (FastAPI 0.115)"]
        API_GW["FastAPI Core Application (backend/main.py)"]:::l2
        API_Auth["JWT Authentication & RBAC (backend/auth/)"]:::l2
        API_Rate["In-Memory Sliding-Window Rate Limiter"]:::l2
        API_Sec["Strict HTTP Security Headers (CSP, HSTS, XFO)"]:::l2
        API_Cors["CORS Policy Validation (localhost:3000)"]:::l2
        API_Routes["Modular REST Routers (9 Routers, 82 Endpoints)"]:::l2
    end

    subgraph L3 ["Layer 3: Orchestration & State Management Layer (LangGraph)"]
        LG_Graph["StateGraph Orchestrator (backend/agent/graph.py)"]:::l3
        LG_State["PortfolioAgentState TypedDict (backend/agent/state.py)"]:::l3
        LG_Edges["Conditional Routing & Fiduciary Gate Logic"]:::l3
        LG_Trace["Full Step-by-Step Telemetry & LLM Audit Logging"]:::l3
    end

    subgraph L4 ["Layer 4: Agentic AI & Intelligence Layer (13 Specialized Nodes)"]
        A_Mgr["Manager Node (Task Decomposition)"]:::l4
        A_Suit["Suitability & Feasibility Node (SEBI Gate)"]:::l4
        A_Macro["Macro Analyst Node (RBI & Inflation)"]:::l4
        A_Mkt["Market Analyst Node (NIFTY 50 50/200 DMA)"]:::l4
        A_Fund["Fundamental Analyst Node (P/E, ROE, Factors)"]:::l4
        A_News["News & Corporate Filings Analyst Node"]:::l4
        A_Strat["Lead Strategist Node (Tactical Candidate Weights)"]:::l4
        A_Critic["Independent Risk Critic Node (Mandate Audit)"]:::l4
        A_Rewk["Strategist Bounded Rework Node (Max 2 Loops)"]:::l4
        A_Opt["Deterministic SLSQP Optimizer Node"]:::l4
        A_CritFin["Critic Final Validation Node (Constraint Audit)"]:::l4
        A_Mod["Fiduciary Moderator Node (Two-Level Stock-Why)"]:::l4
        A_Persist["ACID Persistence Node (PostgreSQL Transaction)"]:::l4
    end

    subgraph L5 ["Layer 5: Quantitative & Mathematical Engine Layer"]
        Q_SLSQP["SciPy SLSQP Optimizer (Markowitz Mean-Variance)"]:::l5
        Q_Lots["Whole-Share Integer Allocator & Cash Conservator"]:::l5
        Q_ZScore["Winsorized Z-Score Factor Models (Val/Qual/Mom/Vol)"]:::l5
        Q_Drift["Multi-Dimensional Drift Monitor (Asset & Sector)"]:::l5
        Q_Tax["Indian Statutory Friction Engine (STT, GST, Stamp)"]:::l5
        Q_HHI["Herfindahl-Hirschman Demat Concentration Analyzer"]:::l5
    end

    subgraph L6 ["Layer 6: Operational Services & Background Schedulers"]
        S_Sched["Unattended Monitoring Daemon (300s Cycle, Market Hours)"]:::l6
        S_Resolve["Levenshtein & Trigram Company Resolver"]:::l6
        S_Notify["Multi-Channel Notification Generator"]:::l6
        S_Parser["Indian Financial Number Parser (Cr, L, K, %)"]:::l6
    end

    subgraph L7 ["Layer 7: Data Access & Persistence Layer (PostgreSQL 16)"]
        DB_Core["PostgreSQL 16 Relational Engine (Port 5432)"]:::l7
        DB_Schema["62 Domain Application Tables (SQLAlchemy 2.0 ORM)"]:::l7
        DB_Auth["Argon2id Hashes & Revoked JWT Blacklist"]:::l7
        DB_Sec["Complete Security Master (2,639 Stored Equities)"]:::l7
    end

    subgraph L8 ["Layer 8: External Integrations & Market Data Layer"]
        EXT_NSE["NSE India Official Master (EQUITY_L.csv Bulk Feed)"]:::l8
        EXT_BSE["BSE India Corporate Filings & Disclosures"]:::l8
        EXT_YF["Yahoo Finance API (yfinance - Quotes & Historical Bars)"]:::l8
        EXT_GEM["Google Gemini 3.8 Flash (LLM Research & Synthesis)"]:::l8
        EXT_RBI["RBI & MoSPI (Macroeconomic Indicators)"]:::l8
    end

    L1 -->|REST HTTP / Bearer JWT| L2
    L2 -->|Dependency Injection| L3
    L3 -->|State Ingestion & Edge Evaluation| L4
    L4 -->|Quadratic Programming & Share Rounding| L5
    L2 -->|Direct RPC Invocation| L5
    L2 -->|Service Delegation| L6
    L6 -->|Continuous Drift Radar| L5
    L4 -->|SQLAlchemy Scoped Sessions| L7
    L5 -->|Historical Covariance & Pricing| L7
    L6 -->|Entity Matching & Notifications| L7
    L7 -->|Scheduled Sync & Ingestion Runs| L8
    L4 -->|Prompt Synthesis Context| L8
```

---

## Table of Contents

1. [Architecture Overview](#51-architecture-overview)
2. [Presentation Architecture](#52-presentation-architecture)
3. [Backend Architecture](#53-backend-architecture)
4. [Data Integration Architecture](#54-data-integration-architecture)
5. [Portfolio-Intelligence Architecture](#55-portfolio-intelligence-architecture)
6. [Quantitative Architecture](#56-quantitative-architecture)
7. [Monitoring & Rebalancing Architecture](#57-monitoring--rebalancing-architecture)
8. [Runtime Architecture](#58-runtime-architecture)
9. [Security Architecture](#59-security-architecture)
10. [Architecture Diagrams](#510-architecture-diagrams)

---

## 5.1 Architecture Overview

Lucid implements a decoupled, event-driven, 8-layer architecture designed specifically for the regulatory, economic, and computational realities of Indian retail investing.

### Authoritative Technology Stack
- **Frontend Presentation:** Next.js 16.4.2 (App Router), React 19, TypeScript, TailwindCSS, Recharts.
- **API Gateway & Core Backend:** FastAPI 0.115+, Uvicorn ASGI Server, Pydantic 2.0+.
- **Multi-Agent Orchestration:** LangGraph 0.2+, `langchain-google-genai`.
- **Primary LLM Model:** Google Gemini 3.8 Flash (`gemini-3.8-flash`) with deterministic rule fallbacks.
- **Quantitative Engine:** SciPy (`scipy.optimize.minimize` with SLSQP solver), NumPy, Pandas.
- **Database & Persistence:** PostgreSQL 16 via SQLAlchemy 2.0 and Alembic.
- **Authentication:** Canonical Argon2id password hashing (`argon2-cffi>=25.1.0`), HMAC-SHA256 JWT tokens.

---

## 5.2 Presentation Architecture

The client presentation layer is implemented in Next.js 16.4.2 using the modern React 19 App Router paradigm:
- **`app/page.tsx`:** Single-Page Application (SPA) shell orchestrating modular views via client-side state.
- **Modular Component Tree:** 24 reusable UI components (`HoldingsView`, `AllocationVisualizer`, `ExplainabilityView`, `StockWhyModal`, `RebalancePreviewModal`, `DiagnosisView`, `NotificationsPanel`).
- **State & Data Management:** Central Axios singleton (`lib/api.ts`) managing Bearer JWT lifecycle, request signing, and graceful 401 token refresh/eviction.

---

## 5.3 Backend Architecture

The backend layer is built on FastAPI and organized into:
- **`backend/main.py`:** Application factory configuring CORS policies, sliding-window rate limiters, security headers, and async lifespan background scheduler loops.
- **Modular Router Layer:** 9 versioned routers (`auth`, `diagnosis`, `goals`, `links`, `market_data`, `notifications`, `portfolios`, `profile`, `risk_assessments`) handling exactly 82 unique REST endpoints.
- **Service Layer:** 13 specialized Python services isolating business logic and database transactions.

---

## 5.4 Data Integration Architecture

Lucid integrates official exchange masters, real-time market feeds, and economic observations:
- **NSE Security Master:** Full exchange universe synchronization (`exchange_universe_sync.py`) ingesting 2,639 listed stocks from `EQUITY_L.csv`.
- **Market Data Retrieval:** Historical daily OHLCV price bars and intraday quotes retrieved via `yfinance` and cached in PostgreSQL `market_prices`.
- **Macro Data:** RBI repo rates, CPI inflation, and yield curves ingested into `economic_indicators`.
- **News & Filings:** BSE/NSE corporate disclosures and earnings announcements ingested into `market_news_articles`.

---

## 5.5 Portfolio-Intelligence Architecture

The intelligence pipeline employs a **13-node LangGraph StateGraph** enforcing fiduciary responsibility:
- **Task Decomposition:** The `manager` node initializes state and sets audit traces.
- **Suitability Gate:** Validates client risk profile against SEBI investor protection regulations and filters candidate universe (~504 liquid stocks).
- **Specialist Research:** Dedicated agents evaluate Macro, Market Breadth, Fundamentals, and News Filings.
- **Independent Risk Critic:** Audits the Lead Strategist's proposed allocations against single-stock (20%) and sector (30%) caps.
- **Bounded Rework:** Critic objections trigger bounded revisions (`max_rework_count = 2`).

---

## 5.6 Quantitative Architecture

To ensure mathematical precision and eliminate LLM hallucinations:
- **Convex Mean-Variance Optimization:** Uses SciPy Sequential Least Squares Programming (`SLSQP`) to maximize the Sharpe ratio subject to hard weight bounds.
- **Whole-Share Discrete Lot Sizing:** Converts continuous weights into whole share lots ($N_i \\in \\mathbb{Z}^+$).
- **Cash Conservation Invariant:** Enforces $\\text{Residual Cash} \\ge 0$ with zero fractional shares and zero leverage.
- **Statutory Friction Engine:** Computes Indian delivery taxes (STT 0.1%, GST 18%, exchange turnover fees, stamp duty 0.015%).

---

## 5.7 Monitoring & Rebalancing Architecture

- **Unattended Background Scheduler:** `BackgroundMonitoringScheduler` daemon wakes up every 300 seconds during market hours (09:15-15:30 IST).
- **Drift Radar:** Evaluates individual asset drift ($|w_{current} - w_{target}|$) and sector drift.
- **Alert Generation:** If asset drift $\\ge 5\\%$ or total drift $\\ge 15\\%$, creates in-app notifications and pending rebalancing proposals.
- **Order Preview:** Generates minimum-turnover BUY/SELL orders with transaction cost previews.

---

## 5.8 Runtime Architecture

Lucid runs as a clean, two-process runtime topology:
1. **Frontend Server:** Next.js Node.js server running on `http://localhost:3000`.
2. **Backend API Server:** FastAPI Uvicorn ASGI server running on `http://localhost:8000`.
3. **Database Engine:** PostgreSQL 16 running on port `5432`.
4. **Daemon Threads:** Background monitoring loop operating within the backend process space.

---

## 5.9 Security Architecture

- **Cryptographic Password Hashing:** Canonical Argon2id ($m=65536, t=3, p=4$) via `argon2-cffi`.
- **JWT Authorization:** HMAC-SHA256 tokens signed with a 64-character secret; invalidation tracked via PostgreSQL `revoked_tokens` table.
- **Multi-Tenant Isolation:** All database reads and writes enforce explicit `user_id` filtering.
- **Defensive Headers:** Strict Content-Security-Policy (CSP), HSTS, nosniff, and X-Frame-Options DENY headers on all responses.

---

## 5.10 Architecture Diagrams

The complete architecture diagrams are rendered and maintained in:
- [SYSTEM_ARCHITECTURE.mmd](file:///Users/ankur/Documents/MajorProject/app/SYSTEM_ARCHITECTURE.mmd)
- [SYSTEM_ARCHITECTURE.png](file:///Users/ankur/Documents/MajorProject/app/SYSTEM_ARCHITECTURE.png)
- [SYSTEM_ARCHITECTURE.svg](file:///Users/ankur/Documents/MajorProject/app/SYSTEM_ARCHITECTURE.svg)
- [COMPLETE_DATA_FLOW.mmd](file:///Users/ankur/Documents/MajorProject/app/COMPLETE_DATA_FLOW.mmd)
- [COMPLETE_DATA_FLOW.png](file:///Users/ankur/Documents/MajorProject/app/COMPLETE_DATA_FLOW.png)

---

## Architectural Exclusions

The following legacy infrastructure components have been **completely excised** from the active runtime:
- **No Neo4j Graph Database:** Company relations and sectors are normalized in PostgreSQL 16.
- **No Redis In-Memory Cache:** Handled via PostgreSQL memory buffers and in-memory rate-limiter middleware.
- **No Celery Distributed Queue:** Replaced with asyncio background tasks and daemon threads.
- **No FAISS Vector Index:** Handled via PostgreSQL relational queries.
- **No Local Ollama Daemon:** Primary LLM inference is standard Google Gemini 3.8 Flash (`gemini-3.8-flash`).
""")

    print(f"SYSTEM_ARCHITECTURE.md successfully built: {out_file.stat().st_size:,} bytes.")

if __name__ == "__main__":
    build_system_architecture()
