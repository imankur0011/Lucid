# Lucid — Intelligent Investment Portfolio Platform for Indian Retail Equities

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4.2-black.svg?logo=next.js&logoColor=white)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.3.0-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.11_--_3.14-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-orange.svg)](https://langchain-ai.github.io/langgraph/)
[![SciPy](https://img.shields.io/badge/SciPy-SLSQP_Optimization-8CAAE6.svg?logo=scipy&logoColor=black)](https://scipy.org)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

Lucid is an institutional-grade, agentic AI-driven equity portfolio construction, continuous monitoring, and rebalancing platform engineered specifically for Indian retail investors across the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**.

---

## ⚡ Quick Start — One-Command Automated Setup & Launcher

Run Lucid with a **single command**. The launcher automatically detects your operating system, configures Python `.venv`, installs frontend dependencies, generates cryptographically secure `.env` secrets, initializes PostgreSQL, executes Alembic migrations, seeds the 2,639-stock NSE/BSE universe, starts both backend and frontend servers, and launches your browser:

### macOS / Linux
```bash
git clone https://github.com/imankur0011/Lucid.git
cd Lucid
chmod +x start_lucid.sh
./start_lucid.sh
```

### Windows (PowerShell)
```powershell
git clone https://github.com/imankur0011/Lucid.git
cd Lucid
powershell -ExecutionPolicy Bypass -File .\start_lucid.ps1
```

### Service Lifecycle Commands
| Command | Purpose |
|---|---|
| `./start_lucid.sh` | Full automated setup and application launcher (FastAPI + Next.js) |
| `./status_lucid.sh` | Real-time diagnostic status of database, backend, and frontend |
| `./logs_lucid.sh [backend\|frontend\|all]` | Stream live application logs |
| `./stop_lucid.sh` | Gracefully terminate all Lucid background services |

> **Default Demo Login**: `developer@lucid.local` / `LucidDevPass123!`  
> **Frontend**: [http://localhost:3000](http://localhost:3000) | **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)  
> **Detailed Documentation**: See [SETUP_AND_INSTALLATION.md](SETUP_AND_INSTALLATION.md) for full architecture and manual setup guide.

---

## Table of Contents
0. [⚡ Quick Start — One-Command Automated Setup & Launcher](#-quick-start--one-command-automated-setup--launcher)
1. [Overview & What Problem Lucid Solves](#1-overview--what-problem-lucid-solves)
2. [Core Application Capabilities](#2-core-application-capabilities)
3. [Technology Stack & System Architecture](#3-technology-stack--system-architecture)
4. [Prerequisites & System Requirements](#4-prerequisites--system-requirements)
5. [Downloading the Project from GitHub](#5-downloading-the-project-from-github)
6. [Environment Variables Configuration](#6-environment-variables-configuration)
7. [PostgreSQL Database Setup & Distribution](#7-postgresql-database-setup--distribution)
8. [Backend Setup from Scratch (FastAPI)](#8-backend-setup-from-scratch-fastapi)
9. [Frontend Setup from Scratch (Next.js)](#9-frontend-setup-from-scratch-nextjs)
10. [Correct Multi-Terminal Startup Sequence](#10-correct-multi-terminal-startup-sequence)
11. [Exact URLs & Service Ports](#11-exact-urls--service-ports)
12. [First-Time Setup Verification Checklist](#12-first-time-setup-verification-checklist)
13. [Postman API Testing Guide](#13-postman-api-testing-guide)
14. [Troubleshooting & Frequently Asked Questions](#14-troubleshooting--frequently-asked-questions)
15. [One-Page Developer Quick-Start](#15-one-page-developer-quick-start)

---

## 1. Overview & What Problem Lucid Solves

### The Problem
Indian retail investors face severe structural challenges in direct equity investing:
- **Information Fragmentation**: Annual reports, quarterly earnings, and regulatory disclosures are scattered across exchanges, PDFs, and news outlets.
- **Emotional & Behavioral Traps**: Retail capital routinely chases momentum near market tops or panics into lower circuits.
- **Mutual Fund Inefficiencies**: Actively managed funds charge 1.5% to 2.5% recurring annual expense ratios while frequently underperforming the Nifty 50.
- **Unattended Demat Drift**: Portfolios established with good intentions drift significantly over time, creating hidden single-stock and sector concentration risks.
- **Illiquidity & Fractional Lot Pitfalls**: Retail robo-advisors often recommend decimal shares (e.g. 3.42 shares of MRF), which is legally impossible on Indian exchanges.

### The Solution: Lucid
Lucid combines the **fiduciary rigor of Indian mutual fund managers** with **deterministic mathematical optimization**:
- **Agentic AI Research Gang**: 13 specialized LangGraph agent nodes synthesize macroeconomic monetary policy (RBI), market regimes (Nifty 50), fundamental balance sheets (ROE > 15%, D/E), and corporate disclosures.
- **Hallucination-Free Optimization**: Numerical optimization is strictly decoupled from the LLM. SciPy's Sequential Least Squares Programming (SLSQP) solver determines Markowitz risk-adjusted weights subject to hard SEBI diversification bounds.
- **Discrete Integer Shares & Cash Conservation**: Every allocation is translated into executable whole-share quantities:
  $$\text{Shares}_i = \left\lfloor \frac{\text{Capital} \times w_i}{\text{Price}_i} \right\rfloor, \quad \sum (\text{Shares}_i \times \text{Price}_i) + \text{Cash} \equiv \text{Capital}$$
- **Continuous Unattended Monitoring**: Background cron evaluates holding drift ($\ge 5\%$) and sector drift ($\ge 8\%$) every 5 minutes during Indian market hours (09:15–15:30 IST).
- **Statutory Indian Transaction Costs**: Synthesizes whole-share BUY/SELL trade previews calculating Securities Transaction Tax (STT), Exchange Turnover charges, SEBI fees, GST (18%), and stamp duty.
- **Fiduciary "Stock-Why" Explanations**: Toggleable dual-level explanations providing plain English for retail clients and verifiable econometric factor scores for institutional scrutiny.

---

## 2. Core Application Capabilities

```mermaid
graph LR
    A["Investor Profiling & Goals"] --> B["13-Node LangGraph Research Gang"]
    B --> C["Deterministic SciPy SLSQP Solver"]
    C --> D["Whole-Share Portfolio (Active NAV)"]
    D --> E["5-Minute Drift Radar Monitoring"]
    E --> F["Friction-Aware Rebalance Preview"]
    G["Demat Holdings Entry / CAS Import"] --> H["HHI Overlap & Health Diagnosis"]
    H --> F
```

1. **Intelligent Goal-Driven Creation**: Generates customized equity portfolios tailored to investor risk capacity (Conservative, Moderate, Aggressive) and specific financial milestones.
2. **Full NSE/BSE Universe Directory**: Houses 2,639 listed equities and 2,715 listings, with 504 liquid candidates eligible for recommendations across 4 institutional liquidity tiers.
3. **Continuous Background Monitoring**: Tracks asset and sector drift automatically during market hours.
4. **Friction-Aware Rebalancing**: Produces executable whole-share trade orders with exact net cash calculations.
5. **Demat Statement (CAS) Health Diagnosis**: Ingests CDSL/NSDL PDF statements to detect hidden stock overlaps, sector skews, and Herfindahl-Hirschman (HHI) concentration risks.
6. **Dual-Level Explainability**: Transparent justification for every holding with zero financial hallucinations.

---

## 3. Technology Stack & System Architecture

### Technology Stack
- **Frontend**: Next.js 16.4.2 (App Router), React 19.3.0, TypeScript 5, Tailwind CSS v4.
- **Backend API**: FastAPI 0.115, Uvicorn ASGI Server, Pydantic v2, Python 3.11 – 3.14.
- **Database (Exclusive Source of Truth)**: PostgreSQL 16+ (62 tables across 8 functional domains).
- **Multi-Agent Orchestration**: LangGraph 0.4 StateGraph, LangChain Google GenAI (Gemini 3.8 Flash).
- **Mathematical Engine**: SciPy 1.15 (SLSQP solver), NumPy 2.2, Pandas 2.2.
- **Market Data Feeds**: NSE India Archives (`EQUITY_L.csv`), Yahoo Finance (`yfinance`), RBI Bulletins.
- **Statement Parsing**: `pdfplumber`, regular expression tokenizers.

### Architecture Overview
Lucid operates across 8 decoupled architectural layers:
```text
Layer 1: Client Presentation Layer (Next.js 16.4 / React 19 UI)
Layer 2: API Gateway & Security Middleware (FastAPI, JWT, Rate Limiting, CORS)
Layer 3: Orchestration & State Management Layer (LangGraph StateGraph, 13 Nodes)
Layer 4: Agentic AI & Intelligence Layer (Macro, Market, Fundamental, News, Critic)
Layer 5: Quantitative & Mathematical Engine Layer (SciPy SLSQP, Integer Lot Rounding)
Layer 6: Operational Services & Scheduler Layer (Continuous Monitoring Cron, Notifications)
Layer 7: Data Access & Persistence Layer (PostgreSQL 16 Master, SQLAlchemy 2.0)
Layer 8: External Integrations & Market Feeds (NSE, BSE, Yahoo Finance, RBI)
```

---

## 4. Prerequisites & System Requirements

Verify that your local workstation meets the following prerequisites:

| Software | Required Version | Why Lucid Needs It | How to Verify | Installation Guide |
|---|---|---|---|---|
| **Git** | `v2.30+` | Source control and version synchronization | `git --version` | Pre-installed or `brew install git` |
| **Python** | `3.11 – 3.14` | Backend runtime (FastAPI, SciPy, SQLAlchemy) | `python3 --version` | `brew install python@3.14` or `pyenv install 3.12.7` |
| **Node.js** | `v20.x or v25.x` | Frontend runtime (Next.js 16.4.2) | `node --version` | `brew install node` |
| **npm** | `v10.x+` | Frontend package manager | `npm --version` | Bundled with Node.js |
| **PostgreSQL** | `v15+ or v16+` | **Sole operational database** (62 tables) | `psql --version` | `brew install postgresql@16` |

### Infrastructure Clarifications (Code Reality):
> [!NOTE]
> - **PostgreSQL 16**: The **exclusive runtime database**. All 62 domain application tables reside here.
> - **Excluded Legacy Infrastructure**: Neo4j, Redis, Celery, FAISS, and Ollama are not used and have been completely removed from active configuration and runtime dependencies. Do NOT install or run external graph, cache, or vector infrastructure to run Lucid.
> - **Docker**: Optional for containerization; direct native terminal execution is faster and recommended for local development.

---

## 5. Downloading the Project from GitHub

Clone the repository from GitHub:

```bash
# 1. Clone repository
git clone https://github.com/imankur0011/Lucid.git

# 2. Enter project directory
cd Lucid

# 3. Confirm Git branch (must be 'main')
git branch --show-current
```

---

## 6. Environment Variables Configuration

Copy the provided `.env.example` template to `.env` in the project root:

```bash
cp .env.example .env
```

### Key Environment Variables Table:

| Variable | Required? | Default / Example Value | Description |
|---|---|---|---|
| `POSTGRES_HOST` | **Yes** | `localhost` | PostgreSQL server hostname |
| `POSTGRES_PORT` | **Yes** | `5432` | PostgreSQL server port |
| `POSTGRES_DB` | **Yes** | `majorproject` | Database name |
| `POSTGRES_USER` | **Yes** | `postgres` | Database username |
| `POSTGRES_PASSWORD` | **Yes** | `password` | Database user password |
| `DATABASE_URL` | Optional | `postgresql+psycopg2://postgres:password@localhost:5432/majorproject` | Full database connection string (overrides individual postgres settings) |
| `APP_ENV` | Optional | `development` | Runtime environment (`development`, `staging`, `production`) |
| `APP_PORT` | Optional | `8000` | Port for FastAPI backend |
| `APP_SECRET_KEY` | **Yes** | `change-me-app-secret-32-chars` | Secret key for session security |
| `JWT_SECRET_KEY` | **Yes** | `change-me-jwt-secret-min-32-chars` | HMAC-SHA256 signing key (min 32 chars in staging/production) |
| `CORS_ORIGINS` | Optional | `http://localhost:3000` | Whitelisted frontend origins |
| `GEMINI_API_KEY` | Optional | `AIzaSy...` | Google Gemini key for LLM agents (has rule-based fallback if omitted) |
| `LLM_PROVIDER` | Optional | `gemini` | LLM provider (`gemini` or `ollama`) |
| `LLM_MODEL` | Optional | `gemini-3.8-flash` | LLM model identifier |
| `RISK_FREE_RATE_PCT` | Optional | `7.0` | Benchmark yield for Sharpe ratio (India 10Y G-Sec) |

> [!CAUTION]
> In `staging` or `production` environments, `JWT_SECRET_KEY` **must** be at least 32 characters long and cannot contain `"change-me"`. Lucid validates keys on startup and fails closed if insecure credentials are used.

---

## 7. PostgreSQL Database Setup & Distribution

### Step 7.1: Start PostgreSQL Service
```bash
# macOS (Homebrew)
brew services start postgresql@16

# Linux (systemd)
sudo systemctl start postgresql
```

### Step 7.2: Create Database and Extensions
Run the initialization script:
```bash
psql -U postgres -f database/create_database.sql
```
*Or execute manually in `psql`:*
```sql
CREATE DATABASE majorproject;
\c majorproject;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Step 7.3: Run Database Migrations
Apply Alembic migrations to create all 62 relational tables:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```

### Step 7.4: Seed Reference Data & Full Security Master
Populate the SEBI risk questionnaires, economic indicators, and the complete 2,639 listed equities from NSE:
```bash
# From project root:
python database/seed_reference_data.py
```

### Step 7.5: Verify Database
```bash
psql -U postgres -d majorproject -c "
SELECT 
    (SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE') AS tables,
    (SELECT count(*) FROM securities) AS securities,
    (SELECT count(*) FROM companies) AS companies,
    (SELECT count(*) FROM instrument_listings) AS listings;
"
```
*Expected Output: `tables: 62`, `securities: 2639`, `companies: 2639`, `listings: 2715`.*

---

## 8. Backend Setup from Scratch (FastAPI)

```bash
# 1. Enter backend directory
cd backend

# 2. Create virtual environment
python3 -m venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Validate environment
cd ..
python scripts/validate_env.py

# 6. Start FastAPI development server
cd backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Backend Availability Checks:
- Root API Ping: `curl http://localhost:8000/`
- Health Endpoint: `curl http://localhost:8000/health`
- Interactive OpenAPI Swagger UI: Open `http://localhost:8000/docs` in your browser.

---

## 9. Frontend Setup from Scratch (Next.js)

Open a **separate terminal**:

```bash
# 1. Enter frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start Next.js development server
npm run dev
```

### Frontend Availability:
Open `http://localhost:3000` in your web browser.

### Production Build Verification (Optional):
```bash
npm run build
npm run start
```

---

## 10. Correct Multi-Terminal Startup Sequence

To ensure clean dependency resolution, start services across 3 dedicated terminals:

```text
┌────────────────────────────────────────────────────────────┐
│ TERMINAL 1: PostgreSQL Database                            │
│ $ brew services start postgresql@16                        │
│ $ psql -U postgres -f database/create_database.sql         │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│ TERMINAL 2: FastAPI Backend API Server                     │
│ $ cd backend && source .venv/bin/activate                  │
│ $ uvicorn backend.main:app --host 0.0.0.0 --port 8000     │
└────────────────────────────┬───────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────┐
│ TERMINAL 3: Next.js Frontend UI                            │
│ $ cd frontend                                              │
│ $ npm run dev                                              │
└────────────────────────────────────────────────────────────┘
```

---

## 11. Exact URLs & Service Ports

| Service / Interface | URL | Purpose | Authentication |
|---|---|---|---|
| **Lucid Web UI** | `http://localhost:3000` | Investor Dashboard & Portfolio Journey | Browser Session |
| **Backend REST API** | `http://localhost:8000` | Core API Root | Public |
| **API Health Check** | `http://localhost:8000/health` | Service & PostgreSQL Health | Public |
| **Database Diagnostics** | `http://localhost:8000/api/db/stats` | Entity Count Summary (Dev mode) | Public |
| **Swagger UI Documentation**| `http://localhost:8000/docs` | Interactive OpenAPI Testbed | Public |
| **ReDoc Documentation** | `http://localhost:8000/redoc` | Static Technical API Reference | Public |
| **PostgreSQL Database** | `localhost:5432` | Relational Storage (`majorproject`) | DB User / Password |

---

## 12. First-Time Setup Verification Checklist

Run the automated self-test script from the project root:

```bash
python scripts/verify_setup.py
```

### Manual Verification Checklist:
- [x] **Database Connectivity**: `curl http://localhost:8000/health` returns `{"api": "up", "database": {"status": "healthy"}}`.
- [x] **Security Universe**: `curl http://localhost:8000/api/v1/market-data/universe-stats` returns 2,639 securities and 504 recommendation candidates.
- [x] **User Registration**: `POST /api/v1/auth/register` creates a new investor and returns JWT tokens.
- [x] **Market Regime**: `GET /api/v1/market-data/regime` returns Nifty 50 DMA trend and India VIX volatility regime.
- [x] **Portfolio Creation**: `POST /api/v1/portfolio-generation-requests` runs the 13-node LangGraph pipeline and outputs whole-share allocations.
- [x] **Continuous Monitoring**: `GET /api/v1/portfolios/{id}/monitoring` computes holding and sector drift.
- [x] **Rebalancing Preview**: `GET /api/v1/portfolios/{id}/rebalance-preview` generates BUY/SELL orders with statutory transaction fees.
- [x] **Frontend Rendering**: Dashboard at `http://localhost:3000` displays holdings, charts, and drift radar.

---

## 13. Postman API Testing Guide

Lucid includes an importable, pre-configured Postman suite in the `postman/` directory:

1. Open Postman desktop app.
2. Click **Import** and select:
   - `postman/Lucid_API_Collection.json` (96 requests across 16 functional folders)
   - `postman/Lucid_Development_Environment.json` (Environment variables)
3. Select **"Lucid Local Development Environment"** in the top-right environment dropdown.
4. Execute `02 - Authentication -> Login`. The test script automatically saves `{{accessToken}}` to your environment.
5. All subsequent requests automatically attach `Authorization: Bearer {{accessToken}}`.
6. Refer to [`postman/README.md`](./postman/README.md) for detailed folder walkthroughs and Newman CLI instructions.

---

## 14. Troubleshooting & Frequently Asked Questions

| Symptom / Error | Root Cause | Exact Resolution |
|---|---|---|
| `psycopg2.OperationalError: Connection refused` | PostgreSQL daemon is not running on port 5432 | Run `brew services start postgresql@16` or check status with `pg_isready`. |
| `FATAL: database "majorproject" does not exist` | Database not created | Run `psql -U postgres -f database/create_database.sql`. |
| `CRITICAL SECURITY CONFIGURATION ERROR` | Insecure/default secrets used in staging/production | Set `JWT_SECRET_KEY` in `.env` to at least 32 characters. |
| `Port 8000 or 3000 already in use` | Another process is holding the port | Free the port: `lsof -ti:8000 \| xargs kill -9` or `lsof -ti:3000 \| xargs kill -9`. |
| `Yahoo Finance HTTP 429 Rate limit` | Rapid sequential requests to free tier | Normal; Lucid caches prices in PostgreSQL and retries with backoff. |
| `ModuleNotFoundError: No module named 'backend'` | Virtualenv not activated or PYTHONPATH unset | Run `source .venv/bin/activate` or `export PYTHONPATH=.`. |

---

## 15. One-Page Developer Quick-Start

For developers returning to Lucid after initial setup:

```bash
# 1. Start Database
brew services start postgresql@16

# 2. Start Backend (Terminal 1)
cd backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000

# 3. Start Frontend (Terminal 2)
cd frontend
npm run dev

# 4. Open in Browser
open http://localhost:3000
open http://localhost:8000/docs
```
