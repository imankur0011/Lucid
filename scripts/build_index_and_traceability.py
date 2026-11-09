#!/usr/bin/env python3
"""
Lucid — Design Documentation Index and Traceability Matrix Generator.
Builds DESIGN_DOCUMENTATION_INDEX.md and DESIGN_TRACEABILITY_MATRIX.md,
indexing all 7 primary design documents and supporting assets.
"""

import sys
from pathlib import Path

ROOT_DIR = Path('/Users/ankur/Documents/MajorProject/app')
sys.path.insert(0, str(ROOT_DIR))

def build_index_and_matrix():
    print("Building updated DESIGN_DOCUMENTATION_INDEX.md...")
    index_file = ROOT_DIR / "DESIGN_DOCUMENTATION_INDEX.md"
    matrix_file = ROOT_DIR / "DESIGN_TRACEABILITY_MATRIX.md"

    with open(index_file, "w", encoding="utf-8") as f:
        f.write("""# Lucid — Technical Design Documentation Master Index

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Scope:** Master Index and Navigation Guide for the Lucid Design & Documentation Suite.

---

## 1. Documentation Suite Overview

The Lucid platform technical documentation suite is organized into **seven authoritative primary design documents**, supported by cross-cutting traceability matrices, visual diagram assets, postman collections, and verified database schemas.

Every document describes the **actual production implementation** in `/Users/ankur/Documents/MajorProject/app`, with obsolete technologies (Neo4j, Redis, Celery, FAISS, Ollama) strictly excised.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                  LUCID DESIGN & DOCUMENTATION SUITE (2026)                    │
├───────────────────────────────┬───────────────────────────────────────────────┤
│ Primary Document              │ Scope & Target Audience                       │
├───────────────────────────────┼───────────────────────────────────────────────┤
│ 1. HIGH_LEVEL_DESIGN.md       │ Executive design, scope, NFRs, 12 subsystems  │
│ 2. LOW_LEVEL_DESIGN.md        │ Classes, functions, 82 APIs, 62 DB tables     │
│ 3. SYSTEM_ARCHITECTURE.md     │ 8-layer architecture, runtime topology        │
│ 4. AGENT_ARCHITECTURE.md      │ LangGraph 13 nodes, state schema, safeguards  │
│ 5. METHODOLOGY.md             │ 22-step lifecycle, Flows A through H          │
│ 6. DATASET_USED.md            │ External APIs, data lineage, field payloads   │
│ 7. API_CONTRACT.md            │ Every backend API's contract, schema & errors │
├───────────────────────────────┴───────────────────────────────────────────────┤
│ Supporting Documentation & Governance Assets                                  │
│ - API_INVENTORY.md : Searchable master inventory of all 88 HTTP operations    │
│ - DESIGN_TRACEABILITY_MATRIX.md : Requirements-to-code traceability           │
│ - FUNCTIONAL_REQUIREMENT_MAPPING.md : Functional requirement mappings         │
│ - DATABASE_ARCHITECTURE.md : Relational schema & normalization                │
│ - SECURITY_AND_RELIABILITY.md : Argon2id, JWT, audit, reliability             │
│ - OPTIMIZATION_METHODOLOGY.md : Mathematical formulation of SLSQP             │
│ - postman/README.md : Postman suite execution guide                           │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Seven Primary Design Documents Navigation

### [1. HIGH_LEVEL_DESIGN.md](file:///Users/ankur/Documents/MajorProject/app/HIGH_LEVEL_DESIGN.md)
- **Primary Purpose:** Specifies the overarching business problem, system boundaries, stakeholder personas, architectural trade-offs, and high-level decomposition into 12 core subsystems.
- **Main Audience:** Project evaluators, software architects, engineering leadership, academic review committees.

### [2. LOW_LEVEL_DESIGN.md](file:///Users/ankur/Documents/MajorProject/app/LOW_LEVEL_DESIGN.md)
- **Primary Purpose:** Detailed module-, class-, function-, method-, and algorithm-level implementation guide.
- **Main Audience:** Software engineers, full-stack developers, quantitative analysts, database administrators.

### [3. SYSTEM_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/SYSTEM_ARCHITECTURE.md)
- **Primary Purpose:** 8-layer architectural blueprint detailing runtime topology, network flows, and component interactions from user browser to PostgreSQL persistence.
- **Main Audience:** Systems architects, infrastructure engineers, DevOps, security auditors.

### [4. AGENT_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/AGENT_ARCHITECTURE.md)
- **Primary Purpose:** Architectural and implementation specification of the LangGraph multi-agent cognitive reasoning engine.
- **Main Audience:** AI/ML researchers, LLM application engineers, compliance officers.

### [5. METHODOLOGY.md](file:///Users/ankur/Documents/MajorProject/app/METHODOLOGY.md)
- **Primary Purpose:** Step-by-step operational methodology detailing how data progresses from raw user input to final portfolio recommendations, continuous monitoring, and trade execution.
- **Main Audience:** Quantitative developers, portfolio managers, financial evaluators.

### [6. DATASET_USED.md](file:///Users/ankur/Documents/MajorProject/app/DATASET_USED.md)
- **Primary Purpose:** Comprehensive data dictionary, external API audit, extraction analysis, and data-lineage documentation.
- **Main Audience:** Data engineers, quantitative researchers, AI developers, regulatory reviewers.

### [7. API_CONTRACT.md](file:///Users/ankur/Documents/MajorProject/app/API_CONTRACT.md)
- **Primary Purpose:** Exhaustive field-level API contract specification for every endpoint implemented in Lucid.
- **Main Audience:** Frontend developers, backend engineers, QA automation testers, API integrators.

---

## 3. Supporting Documentation

- **[API_INVENTORY.md](file:///Users/ankur/Documents/MajorProject/app/API_INVENTORY.md):** Searchable inventory of all 82 paths and 88 operations.
- **[DESIGN_TRACEABILITY_MATRIX.md](file:///Users/ankur/Documents/MajorProject/app/DESIGN_TRACEABILITY_MATRIX.md):** Complete end-to-end matrix mapping all functional requirements to code, UI, APIs, models, and docs.
- **[DATABASE_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/DATABASE_ARCHITECTURE.md):** PostgreSQL schema design, ER models, normalization, indexing strategy.
- **[SECURITY_AND_RELIABILITY.md](file:///Users/ankur/Documents/MajorProject/app/SECURITY_AND_RELIABILITY.md):** Argon2id parameterization, JWT revocation blacklist, multi-tenant isolation.
- **[OPTIMIZATION_METHODOLOGY.md](file:///Users/ankur/Documents/MajorProject/app/OPTIMIZATION_METHODOLOGY.md):** Mathematical formulation of SLSQP, integer rounding, cash conservation.
- **[postman/README.md](file:///Users/ankur/Documents/MajorProject/app/postman/README.md):** Postman collection guide.

---

## 4. Visual Diagrams & Vector Assets

All visual architecture and methodology diagrams are maintained as editable Mermaid source (`.mmd`), scalable vector graphics (`.svg`), and high-DPI raster images (`.png`):
- `SYSTEM_ARCHITECTURE.mmd`, `.svg`, `.png`
- `METHODOLOGY_FLOW.mmd`, `.svg`, `.png`
- `AGENTIC_AI_ARCHITECTURE.mmd`, `.svg`, `.png`
- `COMPLETE_DATA_FLOW.mmd`, `.svg`, `.png`
- `docs/diagrams/api/API_AUTH_FLOW.mmd`, `.svg`, `.png`
- `docs/diagrams/api/API_PORTFOLIO_GENERATION_FLOW.mmd`, `.svg`, `.png`
- `docs/diagrams/api/API_MONITORING_REBALANCE_FLOW.mmd`, `.svg`, `.png`
- `docs/diagrams/api/API_DIAGNOSIS_FLOW.mmd`, `.svg`, `.png`
""")

    print("Building updated DESIGN_TRACEABILITY_MATRIX.md...")
    with open(matrix_file, "w", encoding="utf-8") as f:
        f.write("""# Lucid — Complete Design Traceability Matrix

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Scope:** Complete End-to-End Requirements Traceability Matrix mapping every Functional Requirement (FR) to its UI Component, REST Endpoint, Backend Service, LangGraph Node, Database Table, External API, and Primary Design Documentation.

---

## Traceability Matrix (Requirements to Code Implementation)

| Req ID | Requirement Name | UI Component (React 19) | API Endpoint (FastAPI) | Service Module | Agent Node (LangGraph) | Database Table(s) | External Data Source | Output / Result | Primary Doc Reference |
|---|---|---|---|---|---|---|---|---|---|
| **FR-C01** | User Registration & Argon2id Auth | `AuthView.tsx`, `ProfileAuthModal.tsx` | `POST /api/v1/auth/register`, `POST /api/v1/auth/login` | `backend/api/v1/auth.py` | None | `app_users`, `revoked_tokens` | None | JWT Bearer Token, Argon2id Hash | `API_CONTRACT.md §3`, `LLD.md §11` |
| **FR-C02** | Investor Profiling & Demographics | `OnboardingWizard.tsx`, `ProfileAuthModal.tsx` | `GET/PATCH /api/v1/profile`, `POST /api/v1/profile/extract-from-text` | `profile.py`, `nlp_profile_extractor.py` | `manager` | `user_profiles`, `user_profile_versions` | None | Structured Investor Profile | `API_CONTRACT.md §5`, `LLD.md §3` |
| **FR-C03** | Psychometric Risk Assessment | `RiskQuestionnaireView.tsx` | `GET /api/v1/risk-questions`, `POST /api/v1/risk-assessments` | `risk_assessments.py`, `policy.py` | `suitability` | `risk_questions`, `risk_assessments` | None | Risk Score (0-100), Risk Category | `API_CONTRACT.md §6`, `METHODOLOGY.md §1` |
| **FR-C04** | Financial Goals Management | `OnboardingWizard.tsx` | `GET/POST /api/v1/goals`, `PATCH /api/v1/goals/{id}` | `goals.py` | None | `financial_goals` | None | Financial Goal Tracking | `API_CONTRACT.md §4`, `HLD.md §6` |
| **FR-C05** | Security Master Synchronization | None (Admin / Ingestion) | `POST /api/v1/market-data/sync-universe` | `exchange_universe_sync.py` | None | `companies`, `securities`, `instrument_listings` | NSE Official (`EQUITY_L.csv`) | 2,639 Listed Equities Ingested | `DATASET_USED.md §3`, `API_CONTRACT.md §9` |
| **FR-C06** | Liquidity Screening & Universe Tiers | None (Internal Service) | `GET /api/v1/market-data/reconcile-universe` | `candidate_selection.py` | `suitability` | `securities`, `market_prices` | NSE / Yahoo Finance | ~504 Liquid Candidates Selected | `DATASET_USED.md §26`, `METHODOLOGY.md §8` |
| **FR-C07** | Market Regime Classification | `PortfolioGenerator.tsx`, `HoldingsView.tsx` | `GET /api/v1/market-data/regime` | `backend/market_data/regime.py` | `market_analyst` | `market_prices`, `economic_observations` | NSE India, India VIX | Regime Token (`BULL_TREND`, etc.) | `METHODOLOGY.md §7`, `API_CONTRACT.md §9` |
| **FR-C08** | Multi-Agent Portfolio Formulation | `PortfolioGenerator.tsx` | `POST /api/v1/portfolio-generation-requests` | `portfolio_engine/service.py`, `graph.py` | All 13 LangGraph Nodes | `portfolio_generation_requests`, `agent_execution_runs` | Gemini 3.8 Flash, BSE/NSE | Completed Multi-Agent State | `AGENT_ARCHITECTURE.md §2`, `API_CONTRACT.md §7` |
| **FR-C09** | SLSQP Mean-Variance Optimization | None (Quantitative Engine) | None (Internal Service) | `portfolio_engine/optimizer.py` | `optimizer` | `market_prices` (Historical Returns) | Yahoo Finance / Historical Bars | Optimal Continuous Weights | `LLD.md §9`, `HLD.md §9.1` |
| **FR-C10** | Whole-Share Lot Allocation & Cash | `HoldingsView.tsx`, `AllocationVisualizer.tsx` | None (Internal Service) | `portfolio_engine/allocation_rounding.py` | `optimizer` | `portfolio_versions` | Current Stock Prices | Discrete Integer Shares, Residual Cash | `LLD.md §9`, `HLD.md §9.2` |
| **FR-C11** | Two-Level Fiduciary Stock-Why | `StockWhyModal.tsx` | `GET /api/v1/portfolios/{id}/versions/{vid}/stocks/{sym}/why` | `stock_why_service.py`, `conversational_assistant.py` | `moderator` | `recommendation_explanations`, `evidence_items` | BSE/NSE Disclosures | Executive Thesis & Factor Citations | `METHODOLOGY.md §6`, `API_CONTRACT.md §7` |
| **FR-C12** | Continuous Unattended Monitoring | `HoldingsView.tsx`, `NotificationsPanel.tsx` | `GET /api/v1/portfolios/{id}/monitoring` | `monitoring_scheduler.py`, `monitoring_service.py` | None | `portfolio_performance_snapshots`, `notifications` | Live Market Feeds | Live NAV, Asset & Sector Drift Radar | `METHODOLOGY.md §4`, `API_CONTRACT.md §7` |
| **FR-A01** | Minimum-Turnover Rebalancing | `RebalancePreviewModal.tsx` | `GET /api/v1/portfolios/{id}/rebalance-preview`, `POST .../apply-rebalance` | `rebalancing_service.py` | None | `rebalance_suggestions`, `portfolio_versions` | Live Stock Prices | Proposed BUY/SELL Orders | `METHODOLOGY.md §5`, `API_CONTRACT.md §7` |
| **FR-A02** | Indian Statutory Friction Preview | `RebalancePreviewModal.tsx` | None (Internal Service) | `portfolio_engine/transaction_costs.py` | None | None | None | Exact STT, GST, Stamp Duty in INR | `LLD.md §9`, `METHODOLOGY.md §5` |
| **FR-A03** | Demat Statement CSV Import | `DiagnosisView.tsx` | `POST /api/v1/diagnosis/upload-csv` | `backend/diagnosis/service.py` | None | `existing_portfolios`, `existing_portfolio_holdings` | User Demat CSV | Ingested External Demat Holdings | `METHODOLOGY.md §3`, `API_CONTRACT.md §8` |
| **FR-A04** | Demat Concentration & HHI Diagnosis | `DiagnosisView.tsx` | `POST /api/v1/diagnosis/analyze/{id}` | `backend/diagnosis/service.py` | None | `portfolio_diagnoses` | Live Stock Prices | Health Score (0-100), HHI Index | `METHODOLOGY.md §3`, `API_CONTRACT.md §8` |
| **FR-A05** | Diagnosis AI Copilot Chat | `DiagnosisCopilotModal.tsx` | `POST /api/v1/diagnosis/{id}/chat` | `diagnosis_copilot_service.py` | None | `portfolio_diagnoses`, `existing_portfolios` | Gemini 3.8 Flash | Interactive Demat Diagnostics Chat | `API_CONTRACT.md §8`, `HLD.md §2.1` |
| **FR-A06** | Historical Version Comparison | `VersionComparisonModal.tsx` | `GET /api/v1/portfolios/{id}/versions` | `portfolio_engine/service.py` | None | `portfolio_versions` | None | Side-by-Side Version Diff | `API_CONTRACT.md §7`, `HLD.md §2.1` |
| **FR-A07** | Macroeconomic Stress-Testing | `StressScenariosView.tsx` | `POST /api/v1/portfolios/{id}/scenarios` | `portfolio_engine/service.py` | None | `portfolio_scenarios` | None | Simulated Loss in Macro Shocks | `API_CONTRACT.md §7`, `HLD.md §2.1` |
| **FR-A08** | In-App Drift & System Notifications | `NotificationsPanel.tsx` | `GET /api/v1/notifications`, `PUT .../mark-all-read` | `notification_service.py` | None | `notifications` | System Monitoring Alerts | Real-Time Flyout Notifications | `API_CONTRACT.md §10`, `METHODOLOGY.md §9` |
""")

    print("Copying updated index and matrix to docs/design/...")
    (ROOT_DIR / "docs" / "design" / "DESIGN_DOCUMENTATION_INDEX.md").write_text(index_file.read_text(encoding="utf-8"), encoding="utf-8")
    (ROOT_DIR / "docs" / "design" / "DESIGN_TRACEABILITY_MATRIX.md").write_text(matrix_file.read_text(encoding="utf-8"), encoding="utf-8")
    print("Done!")

if __name__ == "__main__":
    build_index_and_matrix()
