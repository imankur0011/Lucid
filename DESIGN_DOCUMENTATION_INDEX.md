# Lucid — Technical Design Documentation Master Index

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Scope:** Master Index and Navigation Guide for the Lucid Design & Documentation Suite.

---

## 1. Documentation Suite Overview

The Lucid platform technical documentation suite is organized into **six authoritative primary design documents**, supported by cross-cutting traceability matrices, visual diagram assets, and verified database schemas.

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
├───────────────────────────────┴───────────────────────────────────────────────┤
│ Supporting Documentation & Governance Assets                                  │
│ - DESIGN_TRACEABILITY_MATRIX.md : Requirements-to-code traceability           │
│ - FUNCTIONAL_REQUIREMENT_MAPPING.md : Functional requirement mappings         │
│ - DATABASE_ARCHITECTURE.md : Relational schema & normalization                │
│ - SECURITY_AND_RELIABILITY.md : Argon2id, JWT, audit, reliability             │
│ - OPTIMIZATION_METHODOLOGY.md : Mathematical formulation of SLSQP             │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Primary Design Documents Navigation

### [1. HIGH_LEVEL_DESIGN.md](file:///Users/ankur/Documents/MajorProject/app/HIGH_LEVEL_DESIGN.md)
- **Primary Purpose:** Specifies the overarching business problem, system boundaries, stakeholder personas, architectural trade-offs, and high-level decomposition into 12 core subsystems.
- **Main Audience:** Project evaluators, software architects, engineering leadership, academic review committees.
- **Key Sections:** Product Overview, System Boundaries, Functional Traceability (FR-C01 to FR-C12, FR-A01 to FR-A08), NFRs (Latency, Security, Reliability), 12 Subsystems, Major Design Decisions, Deployment Topology, High-Level Data Model.

### [2. LOW_LEVEL_DESIGN.md](file:///Users/ankur/Documents/MajorProject/app/LOW_LEVEL_DESIGN.md)
- **Primary Purpose:** Detailed module-, class-, function-, method-, and algorithm-level implementation guide.
- **Main Audience:** Software engineers, full-stack developers, quantitative analysts, database administrators.
- **Key Sections:** Codebase Structure, FastAPI Initialization (`main.py`, lifespan, CORS), 82 API Endpoints Inventory with Schemas, Next.js React 19 Frontend Components, 13 Backend Services, 13 LangGraph Nodes, 62 Database Tables Specification, 17 Algorithms with Pseudocode, Error Handling, Argon2id & JWT Security, Concurrency & Schedulers, Mermaid Sequence Diagrams.

### [3. SYSTEM_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/SYSTEM_ARCHITECTURE.md)
- **Primary Purpose:** 8-layer architectural blueprint detailing runtime topology, network flows, and component interactions from user browser to PostgreSQL persistence.
- **Main Audience:** Systems architects, infrastructure engineers, DevOps, security auditors.
- **Key Sections:** 8 Architectural Layers (Client Presentation to External Market Feeds), Presentation Architecture, Backend Architecture, Data Integration, Portfolio Intelligence, Quantitative Engine, Monitoring & Rebalancing, Runtime Topology, Security Trust Boundaries, Architecture Diagrams, Architectural Exclusions.

### [4. AGENT_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/AGENT_ARCHITECTURE.md)
- **Primary Purpose:** Architectural and implementation specification of the LangGraph multi-agent cognitive reasoning engine.
- **Main Audience:** AI/ML researchers, LLM application engineers, compliance officers.
- **Key Sections:** Agent Workflow Motivation, Compiled Graph Topology, Shared Agent State (`PortfolioAgentState` 35 fields), 13 Individual Node Profiles (using the rigorous 11-field specification format), Agent-Specific Data Flow, Agent Communication, Reasoning Trace Persistence, Fiduciary Safeguards & Non-Numerical LLM Boundaries.

### [5. METHODOLOGY.md](file:///Users/ankur/Documents/MajorProject/app/METHODOLOGY.md)
- **Primary Purpose:** Step-by-step operational methodology detailing how data progresses from raw user input to final portfolio recommendations, continuous monitoring, and trade execution.
- **Main Audience:** Quantitative developers, portfolio managers, financial evaluators.
- **Key Sections:** 22-Step Application Lifecycle, Flow A (New Portfolio Creation), Flow B (Demat Diagnosis & HHI Concentration), Flow C (Continuous Monitoring & Drift Radar), Flow D (Minimum-Turnover Rebalancing), Flow E (Two-Level Stock-Why Explanations), Flow F (Market Regime Detection), Flow G (Candidate Selection & Liquidity Tiers), Flow H (Alerting & Notifications), Methodology Diagrams.

### [6. DATASET_USED.md](file:///Users/ankur/Documents/MajorProject/app/DATASET_USED.md)
- **Primary Purpose:** Comprehensive data dictionary, external API audit, extraction analysis, and data-lineage documentation.
- **Main Audience:** Data engineers, quantitative researchers, AI developers, regulatory reviewers.
- **Key Sections:** Executive Summary, Complete External API Inventory (NSE, BSE, Yahoo Finance, Gemini, RBI/MoSPI), The 504 vs 2,639 Securities Investigation & Fix, API Request & Response Samples, Field-Level Extraction Inventory, Data Transformation & Normalization, Database Tables & Lineage, Exact Payloads Passed to Each Agent, Data Quality & Freshness, Rate Limits & Fallback Mechanics, Analytical Lookback Windows.

---

## 3. Supporting Documentation

- **[DESIGN_TRACEABILITY_MATRIX.md](file:///Users/ankur/Documents/MajorProject/app/DESIGN_TRACEABILITY_MATRIX.md):** Complete end-to-end matrix mapping all functional requirements to code, UI, APIs, models, and docs.
- **[DATABASE_ARCHITECTURE.md](file:///Users/ankur/Documents/MajorProject/app/DATABASE_ARCHITECTURE.md):** PostgreSQL schema design, ER models, normalization, indexing strategy.
- **[SECURITY_AND_RELIABILITY.md](file:///Users/ankur/Documents/MajorProject/app/SECURITY_AND_RELIABILITY.md):** Argon2id parameterization, JWT revocation blacklist, multi-tenant isolation.
- **[OPTIMIZATION_METHODOLOGY.md](file:///Users/ankur/Documents/MajorProject/app/OPTIMIZATION_METHODOLOGY.md):** Mathematical formulation of SLSQP, integer rounding, cash conservation.
- **[README.md](file:///Users/ankur/Documents/MajorProject/app/README.md):** Step-by-step developer onboarding, installation, and environment configuration.

---

## 4. Visual Diagrams & Vector Assets

All visual architecture and methodology diagrams are maintained as editable Mermaid source (`.mmd`), scalable vector graphics (`.svg`), and high-DPI raster images (`.png`):
- `SYSTEM_ARCHITECTURE.mmd`, `.svg`, `.png`
- `METHODOLOGY_FLOW.mmd`, `.svg`, `.png`
- `AGENTIC_AI_ARCHITECTURE.mmd`, `.svg`, `.png`
- `COMPLETE_DATA_FLOW.mmd`, `.svg`, `.png`
