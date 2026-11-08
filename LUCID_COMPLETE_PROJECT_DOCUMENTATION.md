# Lucid — Intelligent Investment Portfolio Creation, Analysis and Rebalancing Platform
## Complete Technical Architecture & System Documentation (Comprehensive Master Reference)

---

## Table of Contents
1. [Executive Summary & Fiduciary Problem Statement](#1-executive-summary--fiduciary-problem-statement)
2. [Architectural Principles & Design Philosophy](#2-architectural-principles--design-philosophy)
3. [High-Level End-to-End System Architecture](#3-high-level-end-to-end-system-architecture)
4. [Complete Directory & Codebase Inventory](#4-complete-directory--codebase-inventory)
5. [Agentic AI Architecture: The 13-Node LangGraph Engine](#5-agentic-ai-architecture-the-13-node-langgraph-engine)
6. [Quantitative Engine & Portfolio Mathematics](#6-quantitative-engine--portfolio-mathematics)
7. [External Data Integrations & Live Market Adapters](#7-external-data-integrations--live-market-adapters)
8. [Database Architecture & Entity Relationships](#8-database-architecture--entity-relationships)
9. [Frontend Application Architecture & Component Hierarchy](#9-frontend-application-architecture--component-hierarchy)
10. [Verification, Quality Assurance & Test Suite Matrix](#10-verification-quality-assurance--test-suite-matrix)
11. [Security, Non-Custodial Safeguards & Regulatory Alignment](#11-security-non-custodial-safeguards--regulatory-alignment)
12. [Current System Limitations & Production Roadmap](#12-current-system-limitations--production-roadmap)

---

## 1. Executive Summary & Fiduciary Problem Statement

### 1.1 The Indian Retail Equity Conundrum
The Indian retail equity landscape has witnessed exponential growth in Demat accounts (surpassing 160 million in recent years). However, regulatory analyses by the Securities and Exchange Board of India (SEBI) and academic studies reveal severe structural deficiencies in retail outcomes:
1. **Uninformed Speculation and "Finfluencer" Dependence**: Retail investors frequently chase speculative social media tips, leading to severe capital erosion in derivatives and concentrated micro-cap bets. Over 90% of active retail traders incur net financial losses.
2. **Extreme Sector & Single-Stock Concentration**: Retail portfolios often concentrate upwards of 60–80% of total capital in 1–2 trending stocks or sectors, lacking mathematical diversification.
3. **Inability to Rebalance Due to Whole-Share Frictions**: Indian stock exchanges (NSE and BSE) trade exclusively in integer share quantities ($Q_i \in \mathbb{Z}_{\ge 0}$). Fractional shares are not legally supported under Indian corporate law. Most academic and commercial portfolio optimizers output continuous decimal weights that cannot be executed in cash-constrained accounts without creating large residual cash drag or violating risk caps.
4. **Black-Box Robo-Advisors**: Traditional robo-advisors provide static, opaque risk buckets ("Aggressive", "Conservative") without transparent economic explanations, factor auditing, or verifiable source citations.

### 1.2 The Lucid Platform Solution
**Lucid** is an intelligent, non-custodial, fiduciary-first investment portfolio creation, analysis, and rebalancing platform engineered specifically for Indian retail equity markets. Lucid bridges the gap between sophisticated institutional quantitative finance and retail accessibility through three core pillars:
- **Autonomous Agentic Research (LangGraph & Gemini)**: Specialized AI agents analyze macroeconomic regimes, fundamental balance sheet metrics, market breadth, and corporate filings.
- **Deterministic Mathematical Execution (SciPy SLSQP & NumPy)**: Allocations are calculated using constrained Markowitz Mean-Variance Quadratic Programming with integer whole-share lot rounding. Language models never guess or hallucinate financial numbers or asset weights.
- **Explainable Fiduciary Intelligence**: Every portfolio decision is validated by an independent adversarial Critic agent and explained at both the macro-portfolio level and individual stock level ("Why This Stock?"), backed by live exchange filings and verified URLs.

---

## 2. Architectural Principles & Design Philosophy

Lucid is engineered around five inviolable architectural principles:

```
+---------------------------------------------------------------------------------------------------+
|                                 LUCID CORE ARCHITECTURAL PILLARS                                  |
+---------------------------------------------------------------------------------------------------+
|  1. Strict Decoupling of Qualitative LLM Reasoning from Deterministic Portfolio Mathematics       |
|  2. Adversarial Self-Correction via Multi-Agent Critic Nodes with Bounded Iteration Loops          |
|  3. Real-World Execution Fidelity: Integer Lots Only (Zero Fractional Shares, Non-Negative Cash)  |
|  4. Absolute Non-Custodial Operation: Fiduciary Decision Support Without Custody or Auto-Brokerage |
|  5. Cryptographic Multi-Tenant Isolation via Composite Key Database Architecture                 |
+---------------------------------------------------------------------------------------------------+
```

### Principle 1: Strict Decoupling of LLM Qualitative Reasoning from Mathematics
Large Language Models excel at contextual synthesis, unstructured text extraction, and fiduciary explanation. However, LLMs are fundamentally non-deterministic and prone to arithmetic hallucinations. In Lucid:
- **LLM Scope**: Natural language profile extraction, sentiment analysis, qualitative factor scoring, and narrative justification.
- **Deterministic Math Scope**: Covariance matrix calculation, SciPy SLSQP utility optimization, Sharpe ratio maximization, portfolio variance, drift tracking, and statutory transaction cost calculation (STT, GST, SEBI turnover fees, stamp duty).
- **Rule**: No LLM prompt ever calculates or adjusts numerical portfolio percentages or share counts directly.

### Principle 2: Adversarial Self-Correction via Critic Nodes
Rather than relying on a single prompt or monolithic agent chain, Lucid employs an independent **Critic Agent** that evaluates proposed portfolios against strict house risk policies:
- Single-Stock Concentration Ceiling: $\le 25.0\%$ of portfolio equity.
- Sector Concentration Ceiling: $\le 40.0\%$ of portfolio equity.
- Liquidity Floor: Minimum average daily turnover constraints.
- Ethical & Exclusion Compliance: Tobacco, gambling, defense, alcohol, or user-specified custom exclusions.
If the Critic detects a breach, it issues a structured `REWORK_REQUIRED` verdict, triggering a bounded iteration loop ($N \le 2$) that forces the Lead Strategist to prune violating securities before optimization.

### Principle 3: Integer Whole-Share Execution Fidelity
In Indian equity trading:
$$\text{Shares Owned } Q_i \in \{0, 1, 2, 3, \dots\} \quad (\forall i \in \{1, \dots, N\})$$
$$\text{Unallocated Cash } C = V_{\text{total}} - \sum_{i=1}^{N} Q_i \cdot P_i \ge 0$$
Lucid incorporates an integer lot rounding algorithm that satisfies budget constraints while guaranteeing that cash never drops below zero and risk caps are never breached post-rounding.

### Principle 4: Non-Custodial Architecture
Lucid never holds client funds, does not manage pooled demat accounts, and never initiates automated broker transactions. It produces SEBI-aligned execution previews and order slips that the investor reviews and executes manually through their preferred SEBI-registered broker (Zerodha, Groww, AngelOne, Upstox).

### Principle 5: Composite Multi-Tenant Isolation
All sensitive portfolio mutations and queries enforce composite tenant isolation at the database layer:
$$\text{Query Filter: } \texttt{portfolio\_id} = P_{\text{target}} \land \texttt{user\_id} = U_{\text{auth}}$$
This guarantees that even in the presence of malicious client requests, cross-tenant data leakage is cryptographically impossible.

---

## 3. High-Level End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Next.js 16 / TypeScript / Tailwind)"]
        UI[Responsive Modern Interface]
        Wiz[Onboarding / Natural Language Wizard]
        PortView[Portfolio Holdings & Health View]
        WhyModal[Interactive 'Why This Stock' Modal]
        RebalModal[Whole-Share Drift & Rebalance Modal]
        DiagModal[Demat Diagnosis & AI Copilot]
    end

    subgraph Gateway["API Gateway Layer (FastAPI / Starlette)"]
        Router[API v1 Router]
        AuthMW[JWT Bearer & Composite Tenant Authorization]
        RateLimit[IP & Token Bucket Rate Limiter]
    end

    subgraph AgenticAI["Multi-Agent Reasoning Core (LangGraph)"]
        Manager[1. Manager Node]
        Suitability[2. Suitability Node]
        Macro[3. Macro Analyst Node]
        Market[4. Market Analyst Node]
        Fund[5. Fundamental Analyst Node]
        News[6. News Analyst Node]
        Strategist[7. Lead Strategist Node]
        Critic[8. Adversarial Critic Node]
        Rework[9. Strategist Rework Node]
        OptimizerNode[10. Deterministic Optimizer & Validator]
        CriticVal[11. Post-Optimization Critic Validation]
        Moderator[12. Fiduciary Moderator Node]
        Persistence[13. ACID DB Persistence Node]
    end

    subgraph QuantEngine["Quantitative & Mathematical Engines"]
        SLSQP[SciPy SLSQP Quadratic Optimizer]
        IntRound[Whole-Share Integer Lot Rounder]
        CovEngine[Ledoit-Wolf & Historical Covariance]
        DriftEngine[Dynamic Drift & Trigger Auditor]
        TaxEngine[Indian Statutory Transaction Cost Engine]
    end

    subgraph DataIntegrations["Live Market & Data Adapters"]
        YFin[Yahoo Finance Adapter (.NS / .BO)]
        MacroFeed[FRED / RBI Macroeconomic Data]
        NewsFeed[NewsAPI & NSE/BSE Filings]
        RegimeClassifier[India VIX & Nifty 50 Regime Engine]
        SecSync[Exchange Universe & ISIN Reconciler]
    end

    subgraph Database["Relational Persistence Layer (PostgreSQL 17 / SQLAlchemy 2.0)"]
        Schema[58 Normalized Relational Tables]
        Audit[ACID Audit Trails & Generation Traces]
    end

    UI --> Router
    Wiz --> Router
    PortView --> Router
    WhyModal --> Router
    RebalModal --> Router
    DiagModal --> Router

    Router --> AuthMW --> RateLimit
    RateLimit --> AgenticAI
    AgenticAI <--> QuantEngine
    AgenticAI <--> DataIntegrations
    AgenticAI --> Database
```

---

## 4. Complete Directory & Codebase Inventory

```
/Users/ankur/Documents/MajorProject/app/
├── backend/
│   ├── main.py                          # FastAPI ASGI application entry point & CORS configuration
│   ├── config.py                        # Centralized Pydantic application settings & environment keys
│   ├── agent/
│   │   ├── graph.py                     # LangGraph StateGraph compilation & execution pipeline
│   │   ├── nodes.py                     # 13 agent nodes implementation with LLM/deterministic logic
│   │   ├── state.py                     # TypedDict shared state definition (PortfolioAgentState)
│   │   ├── schemas.py                   # Pydantic validation schemas for agent inputs and outputs
│   │   └── tools.py                     # Financial tools for database queries and indicator lookup
│   ├── api/v1/
│   │   ├── auth.py                      # JWT authentication, login, registration, password hashing
│   │   ├── portfolios.py                # Portfolio generation, versioning, drift, rebalance execution
│   │   ├── diagnosis.py                 # Demat portfolio diagnosis, health scoring, copilot chat
│   │   ├── investor.py                  # Investor profiles, risk preference questionnaires, KYC status
│   │   ├── market_data.py               # Stock quotes, regime indicators, live India VIX lookup
│   │   ├── notifications.py             # User notification dispatch, unread alerts, dismissal
│   │   ├── benchmark.py                 # Nifty 50 comparison and alpha/beta calculation
│   │   └── verification.py              # Exchange announcement link verification and security checks
│   ├── database/
│   │   ├── base.py                      # SQLAlchemy DeclarativeBase configuration
│   │   └── session.py                   # Thread-safe PostgreSQL connection pooling and session makers
│   ├── models/                          # 58 normalized SQLAlchemy relational models
│   │   ├── users.py                     # AppUser, UserProfile, UserPreference, RevokedToken
│   │   ├── security.py                  # Security, Company, InstrumentListing, Sector, Industry
│   │   ├── portfolio.py                 # InvestorPortfolio, PortfolioVersion, PortfolioSecurityDecision
│   │   ├── market_data.py               # MarketPrice, MarketIndex, EconomicIndicator
│   │   ├── broker.py                    # BrokerAccount, PortfolioPerformanceSnapshot
│   │   ├── diagnosis.py                 # ExistingPortfolio, ExistingPortfolioHolding
│   │   ├── agent.py                     # GenerationRequest, AgentTrace, AgentExecutionLog
│   │   └── investor.py                  # InvestorSuitabilityAssessment, RiskProfileRecord
│   ├── portfolio_engine/
│   │   ├── optimizer.py                 # SciPy SLSQP Markowitz optimizer & whole-share lot rounder
│   │   ├── factors.py                   # Multi-factor equity scoring (Value, Quality, Momentum, Low Vol)
│   │   ├── policy.py                    # Lucid internal risk policies (25% stock, 40% sector caps)
│   │   ├── monitoring_service.py        # Real-time portfolio valuation, price tracking, drift detection
│   │   ├── rebalancing_service.py       # Whole-share rebalancing trade generation & tax previews
│   │   ├── transaction_costs.py         # Statutory Indian costs (STT, GST, Stamp, Exchange, SEBI)
│   │   ├── candidate_selection.py       # Multi-stage universe filtering & ethical exclusions
│   │   ├── nlp_profile_extractor.py     # Deterministic NLP parser for investor prompts
│   │   ├── stock_why_service.py         # Deep explainability generator for individual stock rationale
│   │   └── conversational_assistant.py  # Conversational diagnosis copilot with context memory
│   ├── market_data/
│   │   ├── adapter.py                   # Yahoo Finance (.NS/.BO) adapter & SimulatedMarketProvider
│   │   ├── regime.py                    # India VIX & 50-day SMA market regime classification
│   │   └── exchange_universe_sync.py   # NSE/BSE security master sync & ISIN resolution
│   ├── services/
│   │   ├── monitoring_scheduler.py      # Background daemon for periodic drift evaluation
│   │   ├── company_resolution_service.py# Dynamic stock resolution across NSE/BSE ticker catalog
│   │   ├── financial_number_parser.py   # Indian numeral words parser ("50k", "2.5 lakh", "1 crore")
│   │   ├── link_verification_service.py # Live HTTP verification of corporate filing citations
│   │   ├── notification_service.py      # In-app alert dispatch for drift breaches and rebalance orders
│   │   └── account_deletion_service.py  # Strict GDPR/DPDP-compliant cascading account deletion
│   └── tests/                           # Comprehensive 209-test verification suite
│       ├── test_agent_and_portfolio_api.py
│       ├── test_auth_and_security.py
│       ├── test_conversational_ai.py
│       ├── test_dynamic_stock_recommendation.py
│       ├── test_fiduciary_integrity.py
│       ├── test_portfolio_monitoring_and_rebalance.py
│       └── ...
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── page.tsx                 # Main dashboard view coordinating active portfolio state
    │   │   └── layout.tsx               # Root HTML structure, navigation bar, footer, font imports
    │   ├── components/
    │   │   ├── HoldingsView.tsx         # Comprehensive portfolio table with metrics and drift alerts
    │   │   ├── RebalancePreviewModal.tsx# 2-tab rebalance modal (Execution Trades vs Post-Rebalance)
    │   │   ├── StockWhyModal.tsx        # Multi-tab explanation modal (Factors, Filings, Health, Peer)
    │   │   ├── DematDiagnosisModal.tsx  # Demat portfolio audit and AI Copilot dialogue interface
    │   │   ├── OnboardingWizard.tsx     # Natural language onboarding and conversational wizard
    │   │   ├── RiskProfileSelector.tsx  # Risk tolerance assessment cards
    │   │   ├── PortfolioHealthBar.tsx   # Visual progress meters for stock and sector concentration
    │   │   └── icons.tsx                # Clean, lightweight SVG icon primitives
    │   └── lib/
    │       └── api.ts                   # Strongly-typed Axios/fetch API client with error handling
    ├── e2e/                             # Playwright end-to-end browser test specifications
    │   ├── onboarding.spec.ts
    │   ├── rebalancing.spec.ts
    │   ├── demat_diagnosis.spec.ts
    │   └── account_lifecycle.spec.ts
    └── package.json                     # Frontend dependencies (Next.js 16, React 19, Tailwind CSS)
```

---

## 5. Agentic AI Architecture: The 13-Node LangGraph Engine

The core reasoning engine of Lucid is modeled as a compiled state graph using **LangGraph**. The workflow enforces a structured state machine with cyclical revision loops and post-optimization verification:

```
[1. Manager Node]
       │
       ▼
[2. Suitability Assessment]
       │
       ▼
┌───────────────────────────────┐
│ 3. Macroeconomic Analyst      │
│ 4. Market / Breadth Analyst   │ ◄── [Specialist Analysts evaluate live market & fundamentals]
│ 5. Fundamental Analyst        │
│ 6. News & Filings Analyst     │
└──────────────┬────────────────┘
               │
               ▼
[7. Lead Strategist (Synthesis)]
               │
               ▼
      [8. Critic Node] ◄─────────────────────────────────┐
       /              \                                   │
(REWORK_REQUIRED)   (APPROVED)                            │
     /                  \                                 │
[9. Strategist Rework]   ▼                                │
     │            [10. Deterministic Optimizer (SLSQP)]   │
     │                           │                        │
     └───────────────────────────┼────────────────────────┘ (Bounded loop: max 2 rework iterations)
                                 ▼
                 [11. Post-Optimization Critic Validation]
                                 │
                                 ▼
                     [12. Fiduciary Moderator]
                                 │
                                 ▼
                     [13. ACID DB Persistence]
```

### Detailed Breakdown of the 13 Nodes:

| Node Index | Node Identifier | Core Responsibility & Mechanics | Input State Fields | Output State Fields |
|:---:|:---|:---|:---|:---|
| **1** | `manager` | Pre-flight validation, investor parameter sanity checks, currency defaults. | `user_prompt`, `investment_amount`, `risk_category` | `current_stage`, `status`, `execution_trace` |
| **2** | `suitability` | Assesses investor suitability against SEBI retail guidelines, liquidity horizon, ethical exclusions. | `risk_category`, `investment_horizon_months`, `excluded_sectors` | `suitability_assessment`, `ethical_filters` |
| **3** | `macro_analyst` | Evaluates macroeconomic indicators: RBI repo rate, India 10Y G-Sec yield, inflation rate. | `macro_indicators`, `regime_hint` | `macro_regime_classification`, `macro_summary` |
| **4** | `market_analyst` | Evaluates live India VIX (`^INDIAVIX`), Nifty 50 trend, 50-day SMA, advance-decline ratio. | `india_vix`, `nifty_50_trend` | `market_sentiment`, `momentum_bias` |
| **5** | `fundamental_analyst` | Screen candidate stocks on ROE, Debt/Equity, P/E, Operating Margin, 3Y Revenue CAGR. | `eligible_candidates`, `fundamental_factors` | `fundamental_scores`, `quality_rankings` |
| **6** | `news_analyst` | Scans official exchange corporate disclosures, SEBI filings, legal notices, sentiment. | `candidate_symbols`, `news_headlines` | `news_sentiment_score`, `regulatory_flags` |
| **7** | `analyst` (Strategist) | Synthesizes specialist findings into proposed asset allocation and candidate universe. | All analyst outputs, `investment_amount` | `proposed_allocations`, `asset_weights` |
| **8** | `critic` | Adversarial auditor verifying $\le 25\%$ single-stock cap, $\le 40\%$ sector cap, liquidity, exclusions. | `proposed_allocations`, `ethical_filters` | `critic_verdict` (`APPROVED` or `REWORK_REQUIRED`) |
| **9** | `strategist_rework` | Bounded iteration loop ($N \le 2$). Removes flagged securities and selects substitutes. | `critic_issues`, `eligible_candidates` | `eligible_candidates`, `rework_count` |
| **10** | `optimizer` | Executes SciPy SLSQP Markowitz optimization, integer whole-share rounding, cash reserve calculation. | `eligible_candidates`, `investment_amount`, `constraints` | `optimizer_output`, `allocations`, `unallocated_cash` |
| **11** | `critic_final_validation` | Audits post-rounding allocations to guarantee no rounding violation breached risk policies. | `allocations`, `unallocated_cash` | `validation_output`, `all_constraints_passed` |
| **12** | `moderator` | Synthesizes plain-English fiduciary explanations, risks, and stock-level rationale. | `allocations`, `analyst_research_notes` | `moderator_output`, `portfolio_explanation` |
| **13** | `persistence` | Commits atomic ACID transaction creating `PortfolioVersion`, decisions, and audit runs. | All state outputs, database session | `portfolio_version_id`, `version_number` |

---

## 6. Quantitative Engine & Portfolio Mathematics

### 6.1 Markowitz Mean-Variance Quadratic Programming
Lucid formulates portfolio optimization as a constrained quadratic utility maximization problem solved using SciPy's Sequential Least Squares Programming (`SLSQP`):

$$\min_{\mathbf{w}} \; \frac{1}{2} \lambda \, \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} - \mathbf{\mu}^T \mathbf{w}$$

Subject to the following linear constraints and simplex bounds:
$$\sum_{i=1}^{N} w_i = 1.0 \quad \text{(Full Investment Simplex)}$$
$$0.0 \le w_i \le w_{\text{max}} \quad \text{where } w_{\text{max}} = 0.25 \; (25.0\% \text{ House Single-Stock Cap})$$
$$\sum_{i \in S_k} w_i \le s_{\text{max}} \quad \text{where } s_{\text{max}} = 0.40 \; (40.0\% \text{ House Sector Cap})$$

Where:
- $\mathbf{w} = [w_1, w_2, \dots, w_N]^T$ is the continuous weight vector.
- $\mathbf{\Sigma} \in \mathbb{R}^{N \times N}$ is the annualized sample covariance matrix of historical log-returns.
- $\mathbf{\mu} \in \mathbb{R}^N$ is the vector of expected annualized returns derived from fundamental factor models.
- $\lambda > 0$ is the risk-aversion parameter mapped from the investor's risk profile:
  - Very Conservative: $\lambda = 8.0$
  - Conservative: $\lambda = 5.0$
  - Moderate: $\lambda = 3.0$
  - Aggressive: $\lambda = 1.5$
  - Very Aggressive: $\lambda = 0.8$

### 6.2 Whole-Share Integer Rounding Algorithm
To bridge continuous weights $w_i$ and the real-world Indian exchange requirement of integer shares ($Q_i \in \mathbb{Z}_{\ge 0}$), Lucid executes an integer floor-and-greedy rounding algorithm:

1. **Continuous Target Capital Allocation**:
   $$V_i^* = w_i \cdot V_{\text{total}}$$
2. **Floor Integer Share Quantities**:
   $$Q_i = \left\lfloor \frac{V_i^*}{P_i} \right\rfloor \quad (\forall i \in \{1, \dots, N\})$$
   $$\text{Invested Capital: } V_{\text{invested}} = \sum_{i=1}^{N} Q_i \cdot P_i$$
   $$\text{Residual Cash: } C_{\text{residual}} = V_{\text{total}} - V_{\text{invested}} \ge 0$$
3. **Greedy Residual Allocation**:
   While $C_{\text{residual}} \ge \min_i(P_i)$:
   - Identify candidate stock $j = \arg\max_{i} (\mu_i / P_i)$ such that $(Q_j + 1) \cdot P_j / V_{\text{total}} \le w_{\text{max}}$ and adding a share does not breach sector cap $s_{\text{max}}$.
   - If found: $Q_j \leftarrow Q_j + 1$, $C_{\text{residual}} \leftarrow C_{\text{residual}} - P_j$.
   - If no candidate satisfies risk caps without breach, terminate and retain residual as liquid unallocated cash reserve.

### 6.3 Real-Time Drift Detection Mechanics
At any evaluation timestamp $t$:
$$V_i(t) = Q_i \cdot P_i(t)$$
$$V_{\text{total}}(t) = C_{\text{cash}} + \sum_{i=1}^{N} V_i(t)$$
$$\text{Current Holding Weight: } w_i(t) = \frac{V_i(t)}{V_{\text{total}}(t)} \times 100\%$$
$$\text{Single-Stock Weight Drift: } \Delta w_i(t) = w_i(t) - w_i^{\text{target}}$$
$$\text{Sector Weight Drift: } \Delta s_k(t) = \left( \sum_{i \in S_k} w_i(t) \right) - s_k^{\text{target}}$$

**Rebalancing Trigger Conditions**:
A rebalancing event is flagged if:
$$\max_i |\Delta w_i(t)| \ge 5.0\% \quad \lor \quad \max_k |\Delta s_k(t)| \ge 10.0\% \quad \lor \quad w_i(t) > 25.0\% \quad \lor \quad s_k(t) > 40.0\%$$

### 6.4 Statutory Indian Transaction Cost Breakdown
Lucid calculates exact statutory Indian equity transaction levies for delivery equity trades:
- **Securities Transaction Tax (STT)**: $0.10\%$ on both Buy and Sell turnover.
- **Exchange Turnover Charges (NSE/BSE)**: $0.00325\%$ of gross trade value.
- **SEBI Turnover Charges**: $0.0001\%$ of gross trade value (₹10 per crore).
- **Goods and Services Tax (GST)**: $18\%$ on brokerage and exchange charges.
- **Stamp Duty**: $0.015\%$ on Buy trade value only.

---

## 7. External Data Integrations & Live Market Adapters

```
+--------------------------------------------------------------------------------------------------+
|                                EXTERNAL DATA PROVIDER INVENTORY                                  |
+----------------------+--------------------------+-----------------------+------------------------+
| Provider / Source    | Primary Endpoints / Syms | Role in Lucid         | Fallback Behavior      |
+----------------------+--------------------------+-----------------------+------------------------+
| Yahoo Finance        | .NS / .BO tickers,       | Live quotes, 1Y OHLCV | SimulatedMarketProvider|
| (yfinance)           | ^INDIAVIX, ^NSEI         | historical returns,   | (deterministic offline |
|                      |                          | beta, market cap      | fixture quotes)        |
+----------------------+--------------------------+-----------------------+------------------------+
| Google Gemini        | gemini-3.8-flash         | LLM agent reasoning,  | Rule-based heuristic   |
| (google-genai SDK)   |                          | NLP parsing, summaries| deterministic fallback |
+----------------------+--------------------------+-----------------------+------------------------+
| Federal Reserve FRED | DFF, GS10, CPIAUCSL      | Global macro yields,  | Domestic RBI baseline  |
| (FRED API)           |                          | currency strength     | benchmark constants    |
+----------------------+--------------------------+-----------------------+------------------------+
| NewsAPI & Feeds      | /v2/everything           | News sentiment, event | Cached filings & BSE   |
|                      |                          | discovery, disclosures| official rss feed      |
+----------------------+--------------------------+-----------------------+------------------------+
| NSE / BSE Security   | equity_master.json       | Authoritative scrip   | Seeded static equity   |
| Master Registries    | nse_bse_reconciled.json  | codes, ISINs, sectors | master DB table        |
+----------------------+--------------------------+-----------------------+------------------------+
```

---

## 8. Database Architecture & Entity Relationships

The Lucid relational schema is built on **PostgreSQL 17** using **SQLAlchemy 2.0** ORM. It comprises **62 normalized tables** partitioned across 8 cohesive functional domains:

1. **User Identity & Security (`IDENTITY` — 7 Tables)**:
   `app_users`, `revoked_tokens`, `user_consents`, `user_preferences`, `user_profiles`, `user_profile_versions`, `user_verification_codes`.
2. **Investor Suitability & Goals (`INVESTOR` — 5 Tables)**:
   `financial_goals`, `risk_assessments`, `risk_assessment_answers`, `risk_questions`, `risk_question_options`.
3. **Security Master & Taxonomies (`SECURITY` — 9 Tables)**:
   `companies`, `company_industries`, `exchanges`, `industries`, `instrument_listings`, `sectors`, `securities`, `user_sector_preferences`, `user_security_preferences`.
4. **Market Data, Prices & News (`MARKET` — 11 Tables)**:
   `data_ingestion_errors`, `data_ingestion_runs`, `data_sources`, `economic_indicators`, `economic_observations`, `fundamental_metrics`, `market_news_articles`, `market_prices`, `metric_definitions`, `news_article_securities`, `source_instrument_mappings`.
5. **Core Portfolios, Decisions & Scenarios (`PORTFOLIO` — 13 Tables)**:
   `evidence_items`, `explanation_evidence`, `investor_portfolios`, `portfolio_generation_requests`, `portfolio_scenarios`, `portfolio_security_decisions`, `portfolio_validation_results`, `portfolio_validation_runs`, `portfolio_version_constraints`, `portfolio_versions`, `recommendation_explanations`, `strategy_definitions`, `strategy_versions`.
6. **Broker Accounts & Demat Holdings (`BROKER` — 6 Tables)**:
   `broker_executions`, `broker_order_events`, `broker_orders`, `broker_providers`, `portfolio_performance_snapshots`, `user_broker_accounts`.
7. **Demat Diagnosis & Rebalancing (`DIAGNOSIS` — 4 Tables)**:
   `existing_portfolios`, `existing_portfolio_holdings`, `portfolio_diagnoses`, `rebalance_suggestions`.
8. **Multi-Agent Execution & Operations (`OPERATIONS` — 7 Tables)**:
   `agent_definitions`, `agent_execution_runs`, `agent_versions`, `audit_events`, `knowledge_documents`, `notifications`, `user_feedback`.

---

## 9. Frontend Application Architecture & Component Hierarchy

The client application is built with **Next.js 16 (App Router)**, **React 19**, and **Tailwind CSS**, emphasizing responsive typography, high-contrast accessible visual cues, and zero layout shift:

- **State Management**: React state hooks (`useState`, `useEffect`, `useCallback`) backed by optimistic UI updates and resilient polling hooks.
- **Visual Design System**: Soft ivory background (`#F7F6F1`), deep forest green fiduciary accents (`#285C4D`), rich midnight text (`#142A3B`), and subtle border dividers (`#E5E3DA`).
- **Modal System**: Accessible keyboard-trapped overlay modals with smooth fade-in animations for `RebalancePreviewModal`, `StockWhyModal`, and `DematDiagnosisModal`.

---

## 10. Verification, Quality Assurance & Test Suite Matrix

```
========================================================================================
                              LUCID VERIFICATION TEST SUITE
========================================================================================
Test Type         Framework / Tool    Total Tests   Passing Status   Execution Time
----------------------------------------------------------------------------------------
Backend Unit      Pytest / Pytest-Async    209           209 / 209          ~47s
Frontend E2E      Playwright (Chromium)     24            24 / 24          ~180s
Type Integrity    TypeScript (tsc)        0 Errors       0 Errors           ~2s
Production Build  Next.js Compiler       Success        Success            ~400ms
========================================================================================
```

All 209 backend tests and 24 Playwright browser tests pass deterministically on every release gate, validating:
- Multi-agent LangGraph workflow execution and Critic rework loops.
- Markowitz SLSQP optimization, integer whole-share math, and non-negative cash balances.
- Natural language input extraction across complex Indian currency formats ("₹5 Lakhs", "2.5 Cr").
- Real-time India VIX market regime switching.
- Cascade deletion, account data export, and composite-key tenant isolation.

---

## 11. Security, Non-Custodial Safeguards & Regulatory Alignment

### 11.1 Non-Custodial Guarantee
Lucid adheres strictly to the non-custodial model:
- The system generates fiduciary decision support and mathematical trade previews.
- Lucid never holds client depository accounts or bank credentials.
- Users execute trades independently through their brokers.

### 11.2 Authentication & Cryptographic Security
- **Passwords**: Hashed using **Argon2id** (`argon2-cffi`), the state-of-the-art memory-hard hashing algorithm resistant to GPU cracking.
- **Session Tokens**: Cryptographically signed stateless **JWT tokens** with expiration and server-side token revocation tracking (`revoked_tokens` table).
- **Network Boundaries**: Strict CORS middleware configured for authenticated frontend origins with credentials allowed.

---

## 12. Current System Limitations & Production Roadmap

### 12.1 Current System Limitations
1. **Intraday Trading Unsupported**: Lucid is strictly a medium-to-long-term delivery equity platform; intraday F&O trading is intentionally out of scope.
2. **Offline Data Latency**: When external APIs encounter rate-limits, prices fall back to cached daily close quotes rather than tick-by-tick order book depth.
3. **Execution Friction**: As a non-custodial platform, execution depends on the investor manually submitting trades on their broker terminal.

### 12.2 Future Production Roadmap
1. **SEBI Account Aggregator (AA) Integration**: Direct live demat sync via licensed Account Aggregators (Setu, Finvu) without manual statement uploads.
2. **Direct Smallcase / Broker Webhook Execution**: One-click basket order dispatch to Zerodha Kite and Groww API via official OAuth partner gateways.
3. **Multi-Asset Class Support**: Expanding optimizer beyond equities to Sovereign Gold Bonds (SGBs), REITs, and Liquid ETFs.

---
*Lucid Platform Technical Documentation — Version 2026.11-v2.0*

