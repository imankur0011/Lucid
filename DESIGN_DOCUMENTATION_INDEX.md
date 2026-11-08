# Lucid — Technical Design Documentation Master Index

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
