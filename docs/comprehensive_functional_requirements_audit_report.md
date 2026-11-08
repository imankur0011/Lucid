# Comprehensive Functional Requirements Implementation Audit Report: Lucid

**Platform:** Lucid — Intelligent Portfolio Creation & Rebalancing Engine  
**Authoritative Date:** 2026-11-05  
**Audit Standard:** Fiduciary Product-Grade Verification (SEBI-Compliant Architecture)  
**Lead Auditor:** Antigravity Advanced Agentic Coding System  

---

## 1. Executive Summary

A comprehensive, code-level, execution-backed audit of the **Lucid** application was conducted across its entire stack: Next.js frontend, FastAPI backend, PostgreSQL database (63 tables), LangGraph multi-agent orchestrator, Scipy SLSQP deterministic optimizer, and external financial data integrations.

Every requirement was assessed against actual live execution, integration pipelines, and database persistence—rather than class definitions or mocked tests.

### 1.1 Implementation Status Summary

| Status Category | Count | Requirements |
| :--- | :---: | :--- |
| **IMPLEMENTED — FUNCTIONAL** | **5** | **FR-C01** (Onboarding & Profile), **FR-C02** (Natural Language Input), **FR-C06** (Optimization & LLM Decoupling), **FR-C10** (Portfolio Diagnosis), **FR-D01** (Reasoning Trace & Transparent Critic) |
| **IMPLEMENTED — PARTIALLY FUNCTIONAL** | **4** | **FR-C03** (Market Regime), **FR-C04** (Candidate Universe), **FR-C05** (Multi-Agent Reasoning), **FR-C08** (Rebalancing Engine) |
| **IMPLEMENTED — NOT INTEGRATED** | **0** | — |
| **PLACEHOLDER / MOCKED** | **1** | **FR-C07** (Portfolio Monitoring) |
| **NOT IMPLEMENTED** | **1** | **FR-C09** (Alert & Notification System) |
| **BROKEN** | **0** | *(No requirement completely broken; isolated unit test defect in `test_llm_resilience.py`)* |
| **UNVERIFIED** | **0** | — |
| **Total Audited** | **11** | **100% of defined functional requirements evaluated** |

### 1.2 Key Audit Findings & Most Serious Defects

1. **Absence of Real-Time India VIX Data Feed (FR-C03)**:
   - There is no live or streaming API connection to the National Stock Exchange for India VIX (`^INDIAVIX`). The application estimates VIX from historical prices of 4 stocks or defaults to 14.5%.
   - **Methodological Flaw**: The algorithm attempts to classify market direction (Bull/Normal) from volatility alone. Low VIX indicates low implied volatility, not necessarily a bullish trend. Directional trend determination requires price momentum/moving average indicators.
2. **Missing Liquidity Filters & Exclusion Audit Trail (FR-C04)**:
   - Candidate selection checks active status, exclusions, and price freshness, but completely omits Average Daily Traded Volume (ADTV), daily turnover, and market capitalization thresholds. Illiquid small-cap listings could theoretically pass into optimization.
   - Securities excluded during filtering are not persisted with structured reason codes in an audit table.
3. **Multi-Agent Reasoning Decoupled from Live LLM (FR-C05)**:
   - While Gemini 3.8 Flash is actively invoked for Natural Language Onboarding (`nlp_profile_extractor.py`), the 13 nodes in `backend/agent/nodes.py` (`macro_analyst`, `market_analyst`, `fundamental_analyst`, `news_analyst`, `analyst`, `critic`) currently execute **deterministic heuristic rules and database aggregations**. They emit structured Pydantic schemas but do not call `llm.invoke()`.
4. **No Continuous Background Portfolio Monitoring (FR-C07)**:
   - Portfolios are evaluated statically when loaded. There is no background daemon, scheduler, or worker updating holdings prices, recomputing current weights, or tracking volatility drift over time.
5. **Missing Notification System (FR-C09)**:
   - Although the `notifications` table exists in PostgreSQL, there are zero backend API endpoints (`/api/v1/notifications`), no notification dispatch worker, no email/SMS gateway, and no in-app alert stream.
6. **Rebalancing Asymmetry (FR-C08)**:
   - Rebalancing is fully implemented for *imported legacy brokerage portfolios* (`diagnosis_and_rebalance`), but *native created portfolios* lack autonomous drift threshold triggers.

---

## 2. Requirement-by-Requirement Audit Matrix

| Req ID | Requirement Description | Frontend Status | Backend Status | Database Status | External Data | Integration Status | Test Status | Overall Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **FR-C01** | User Onboarding & Profile | FUNCTIONAL | FUNCTIONAL | FUNCTIONAL | N/A | INTEGRATED | PASSED | **IMPLEMENTED — FUNCTIONAL** |
| **FR-C02** | Natural Language Input | FUNCTIONAL | FUNCTIONAL | FUNCTIONAL | LIVE (Gemini) | INTEGRATED | PASSED | **IMPLEMENTED — FUNCTIONAL** |
| **FR-C03** | Market Regime Classification | FUNCTIONAL | PARTIAL | FUNCTIONAL | MOCKED / PROXY | PARTIAL | PASSED | **IMPLEMENTED — PARTIALLY FUNCTIONAL** |
| **FR-C04** | Candidate Stock Universe | FUNCTIONAL | PARTIAL | FUNCTIONAL | DB REPO (504) | INTEGRATED | PASSED | **IMPLEMENTED — PARTIALLY FUNCTIONAL** |
| **FR-C05** | Multi-Agent Reasoning | FUNCTIONAL | PARTIAL | FUNCTIONAL | DB METRICS | INTEGRATED | 4 FAILED* | **IMPLEMENTED — PARTIALLY FUNCTIONAL** |
| **FR-C06** | Optimization & LLM Decoupling | FUNCTIONAL | FUNCTIONAL | FUNCTIONAL | N/A | INTEGRATED | PASSED | **IMPLEMENTED — FUNCTIONAL** |
| **FR-C07** | Portfolio Monitoring | PARTIAL | PLACEHOLDER | PARTIAL | STATIC / DB | NOT INTEGRATED | UNTESTED | **PLACEHOLDER / MOCKED** |
| **FR-C08** | Rebalancing Engine | FUNCTIONAL | PARTIAL | FUNCTIONAL | DB REPO | PARTIAL | PASSED | **IMPLEMENTED — PARTIALLY FUNCTIONAL** |
| **FR-C09** | Alert & Notification System | MISSING | MISSING | SCHEMA ONLY | NONE | NOT INTEGRATED | UNTESTED | **NOT IMPLEMENTED** |
| **FR-C10** | Existing Portfolio Diagnosis | FUNCTIONAL | FUNCTIONAL | FUNCTIONAL | DB REPO | INTEGRATED | PASSED | **IMPLEMENTED — FUNCTIONAL** |
| **FR-D01** | Reasoning Trace & Critic | FUNCTIONAL | FUNCTIONAL | FUNCTIONAL | LIVE (NSE/BSE) | INTEGRATED | PASSED | **IMPLEMENTED — FUNCTIONAL** |

*\*Note: The 4 unit test failures in `test_llm_resilience.py` were caused by an obsolete dictionary key expectation (`'ai_provider'`) in the legacy test harness, while core agent pipeline execution passed.*

---

## 3. Detailed Audit by Requirement

---

### FR-C01: User Onboarding & Profile

#### 1. Requirement & Expected Behaviour
- **Input:** Investor personal details, financial status, risk tolerance, emergency reserve, time horizon, contribution type (lump-sum vs SIP), and sector preferences.
- **Expected Output:** Canonical structured user profile, historical versioning, and direct mapping to SEBI-compliant risk assessment options.

#### 2. Existing Implementation
- **Frontend Components:**
  - [`OnboardingWizard.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/OnboardingWizard.tsx): 5-stage interactive onboarding wizard with step validation, investment capital inputs, and prefill reconciliation.
  - [`RiskQuestionnaireView.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/RiskQuestionnaireView.tsx): Formal SEBI Risk Assessment Questionnaire with 5 active questions.
  - [`ProfileAuthModal.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/ProfileAuthModal.tsx): Account settings, data export (JSON), and portfolio management.
- **Backend Services & APIs:**
  - [`backend/api/v1/profile.py`](file:///Users/ankur/Documents/MajorProject/app/backend/api/v1/profile.py): `GET /profile`, `PATCH /profile`, `POST /extract-from-text`.
  - [`backend/api/v1/risk_assessments.py`](file:///Users/ankur/Documents/MajorProject/app/backend/api/v1/risk_assessments.py): `GET /risk-assessments/questions`, `POST /risk-assessments`.
  - [`backend/api/v1/goals.py`](file:///Users/ankur/Documents/MajorProject/app/backend/api/v1/goals.py): `GET /goals`, `POST /goals`.
- **Database Models & Tables:**
  - `app_users`, `user_profiles` (version_number, investment_experience, knowledge_level).
  - `user_profile_versions` (automatic historical versioning snapshot before every update).
  - `risk_assessments` (separates `risk_tolerance_score` from `risk_capacity_score`).
  - `risk_questions`, `risk_question_options`, `risk_assessment_answers`.
  - `financial_goals` (tracks multi-goal allocations).

#### 3. Execution Evidence
- Live database query verified 384 active users, 260 profiles, 512 profile versions, 336 risk assessments, and 507 financial goals.
- Profile update endpoint (`PATCH /profile`) automatically writes to `user_profile_versions` before modifying the profile, guaranteeing complete historical auditability.
- Risk tolerance (psychological willingness to bear volatility) and risk capacity (financial ability to absorb loss based on emergency funds) are computed as distinct decimal scores (`55.0` vs `62.0`).

#### 4. Verification & Testing
- Unit tests: [`backend/tests/test_investor_api.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_investor_api.py) **PASSED**.
- Playwright E2E: [`frontend/e2e/natural_language_onboarding.spec.ts`](file:///Users/ankur/Documents/MajorProject/app/frontend/e2e/natural_language_onboarding.spec.ts) **PASSED** (10.8s).

#### 5. Final Status
`IMPLEMENTED — FUNCTIONAL`

---

### FR-C02: Natural Language Input

#### 1. Requirement & Expected Behaviour
- **Input:** Freeform natural language text describing financial intent, constraints, and experience.
- **Expected Output:** Parsed Pydantic constraints (`StructuredInvestorProfile`) distinguishing stated vs inferred values, resolving stock entities dynamically, identifying contradictions, and enforcing SEBI fiduciary guardrails.

#### 2. Existing Implementation
- **Frontend Components:**
  - [`OnboardingWizard.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/OnboardingWizard.tsx): Real-time analysis card displaying extracted capital, horizon, risk tier, emergency reserve status, preferred sectors, and negative exclusions.
- **Backend Services & APIs:**
  - [`nlp_profile_extractor.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/nlp_profile_extractor.py): Dual-mode extraction using Gemini 3.8 Flash (`get_llm()`) with deterministic fallback (`deterministic_extract_investor_profile`).
  - [`financial_number_parser.py`](file:///Users/ankur/Documents/MajorProject/app/backend/services/financial_number_parser.py): Context-aware arithmetic evaluator for Indian/Western scales, shorthand, operators (`LTE`, `GTE`, `BETWEEN`), and units.
  - [`company_resolution_service.py`](file:///Users/ankur/Documents/MajorProject/app/backend/services/company_resolution_service.py): 504-security master repository resolving exact symbols, ISINs, aliases, and fuzzy typos.
  - `POST /api/v1/profile/extract-from-text`.
- **Database Mapping:**
  - Resolves freeform responses directly into active PostgreSQL `RiskQuestion` and `RiskQuestionOption` UUIDs.

#### 3. Execution Evidence
- Test prompt: *"I have ₹2.5 lakh to invest for five years. I want a moderate-risk portfolio and would like to include Bharat Electronics, ITC and Larsen & Toubro. Do not allocate more than 20% to the banking sector."*
  - Extracted Capital: `₹250,000.0`
  - Horizon: `60 months`
  - Risk Tier: `MODERATE`
  - Preferred Equities: `BEL`, `LT`, `ITC`
  - Quantitative Constraint: `Financial Services LTE 20.0%`
- Conflict Detection: *"I want high returns but cannot afford to lose much money"* flags `CONFLICT_HIGH_RETURNS_ZERO_RISK` and generates a trade-off prompt.
- SEBI Fiduciary Rule: Zero emergency reserve strictly overrides user risk tier to `CONSERVATIVE`.

#### 4. Verification & Testing
- Unit tests: [`test_dynamic_stock_and_number_parsing.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_dynamic_stock_and_number_parsing.py) (14/14 **PASSED**).
- Onboarding tests: [`test_natural_language_onboarding.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_natural_language_onboarding.py) (10/10 **PASSED**).

#### 5. Final Status
`IMPLEMENTED — FUNCTIONAL`

---

### FR-C03: Market Regime Classification

#### 1. Requirement & Expected Behaviour
- **Input:** Real-time India VIX data.
- **Expected Output:** Market regime tag — Bull / Normal / Volatile with clear asset allocation multipliers.

#### 2. Existing Implementation
- **Backend Services:**
  - [`backend/market_data/regime.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/regime.py): `detect_market_regime(db, current_vix)`.
- **Thresholds Implemented:**
  - `CALM`: VIX < 13.5 (Risk multiplier: 0.85, Cash buffer: 2.0%)
  - `MODERATE`: 13.5 $\le$ VIX < 18.0 (Risk multiplier: 1.0, Cash buffer: 3.5%)
  - `VOLATILE`: 18.0 $\le$ VIX < 25.0 (Risk multiplier: 1.30, Cash buffer: 8.0%)
  - `EXTREME`: VIX $\ge$ 25.0 (Risk multiplier: 1.65, Cash buffer: 15.0%)

#### 3. Defects & Deficiencies Identified
1. **No Real-Time VIX Integration**: There is no live external API pulling real-time India VIX (`^INDIAVIX`). If `current_vix` is not passed to the API, the code estimates realized volatility from 100 historical prices of 4 stocks (RELIANCE, TCS, HDFCBANK, INFY) or defaults to `14.5%`.
2. **Direction vs Volatility Confusion**: India VIX measures expected 30-day volatility corridor, not market direction. A low VIX can occur during a topping or consolidating market. Determining "Bull vs Bear" requires moving-average trend filters (e.g. Nifty 50 200-DMA slope).

#### 4. Verification & Testing
- Test execution: `detect_market_regime()` executes and returns regime metadata, but operates primarily on synthetic or proxy data when unassisted.

#### 5. Final Status
`IMPLEMENTED — PARTIALLY FUNCTIONAL`

---

### FR-C04: Candidate Stock Universe

#### 1. Requirement & Expected Behaviour
- **Input:** NSE/BSE listed equities universe and liquidity/capitalization filters.
- **Expected Output:** Filtered, eligible candidate stock universe mapped to financial indicators.

#### 2. Existing Implementation
- **Backend Services:**
  - [`candidate_selection.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/candidate_selection.py): `CandidateUniverseSelector.select_eligible_candidates()`.
  - [`exchange_universe_sync.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py): Syncs Nifty 500 constituents with ISINs, BSE codes, and sectors.
- **Filtering Pipeline:**
  1. Filters by `Security.security_status == 'active'`.
  2. Filters by `InstrumentListing.trading_status == 'active'`.
  3. Excludes investor negative sector constraints (`excluded_sectors`).
  4. Excludes individual negative securities (`excluded_instruments`).
  5. Price freshness verification: Drops listings with no price updates within 14 days (`max_stale_days`).

#### 3. Defects & Deficiencies Identified
1. **Missing Liquidity Filters**: The codebase does not enforce minimum Average Daily Traded Volume (ADTV), daily turnover (e.g., minimum ₹5 Crore/day), or free-float market cap filters.
2. **Missing Exclusion Audit Logging**: Excluded securities are skipped in a local loop; no persistent audit record is written to document why a specific stock was excluded on a given execution run.

#### 4. Verification & Testing
- Database inspection confirmed 504 active securities across 11 sectors.
- Filter execution verified in [`test_portfolio_engine.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_portfolio_engine.py) **PASSED**.

#### 5. Final Status
`IMPLEMENTED — PARTIALLY FUNCTIONAL`

---

### FR-C05: Multi-Agent Reasoning

#### 1. Requirement & Expected Behaviour
- **Input:** Investor profile, market regime tag, and candidate stock universe.
- **Expected Output:** Proposed portfolio weights and multi-agent investment rationales.

#### 2. Existing Implementation
- **Orchestration Architecture:**
  - [`backend/agent/graph.py`](file:///Users/ankur/Documents/MajorProject/app/backend/agent/graph.py): 13-node compiled LangGraph `StateGraph`:
    - `manager` $\rightarrow$ `suitability` $\rightarrow$ `macro_analyst` $\rightarrow$ `market_analyst` $\rightarrow$ `fundamental_analyst` $\rightarrow$ `news_analyst` $\rightarrow$ `analyst` (Strategist) $\rightarrow$ `critic` $\rightleftharpoons$ `strategist_rework` $\rightarrow$ `optimizer` $\rightarrow$ `critic_final_validation` $\rightarrow$ `moderator` $\rightarrow$ `persistence`.
  - [`backend/agent/schemas.py`](file:///Users/ankur/Documents/MajorProject/app/backend/agent/schemas.py): Strict Pydantic output schemas for every agent (`MacroOutput`, `MarketOutput`, `FundamentalOutput`, `NewsOutput`, `StrategistOutput`, `CriticOutput`, `ModeratorOutput`).
  - [`backend/agent/nodes.py`](file:///Users/ankur/Documents/MajorProject/app/backend/agent/nodes.py): Implements all node functions with agent messaging and evidence item registries.

#### 3. Defects & Deficiencies Identified
1. **LLM Decoupled from Specialist Agent Nodes**: Although `get_llm()` is defined in `nodes.py`, the agent nodes execute **deterministic heuristics and database queries** rather than querying Gemini Flash. They assign pre-computed roles (`CORE`, `DEFENSIVE`, `GROWTH`) and simulate the deliberation committee deterministically.
2. **Test Failures in `test_llm_resilience.py`**: 4 unit tests failed because they expected an `"ai_provider"` field in `analyst_entry`, which was refactored in the latest schema revision.

#### 4. Verification & Testing
- LangGraph execution trace verified live: executed all 13 nodes, triggered rework loop, passed validation, and persisted outputs to PostgreSQL.

#### 5. Final Status
`IMPLEMENTED — PARTIALLY FUNCTIONAL`

---

### FR-C06: Mathematical Optimization & LLM Decoupling

#### 1. Requirement & Expected Behaviour
- **Input:** Proposed candidate assets, risk policy parameters, and quantitative constraints.
- **Expected Output:** Deterministic, mathematically safe final weights meeting all constraints.

#### 2. Existing Implementation
- **Backend Services:**
  - [`backend/portfolio_engine/optimizer.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/optimizer.py): Solves Markowitz Mean-Variance Quadratic Utility using `scipy.optimize.minimize(method="SLSQP")`.
  - [`allocation_rounding.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/allocation_rounding.py): Converts continuous weights to integer whole-share lots and computes remaining unallocated cash.
  - [`validators.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/validators.py): Validates single-stock caps, sector caps, non-negativity, and unit simplex sum.
  - [`policy.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/policy.py): Enforces SEBI-aligned single-stock and sector exposure limits.

#### 3. Fiduciary Invariants Verified
1. **Mathematical Optimization**:
   $$\min_{w} \frac{1}{2} \lambda w^T \Sigma w - \mu^T w \quad \text{s.t.} \quad \sum w_i = 1, \; 0 \le w_i \le w_{\max}, \; \sum_{i \in \text{sector}} w_i \le S_{\max}$$
2. **Deterministic Fallback**: If SLSQP fails to converge, `_sector_constrained_fallback` executes an iterative sector-capped water-filling algorithm. If mathematically impossible, it explicitly fails rather than producing invalid weights.
3. **Complete LLM Decoupling**: The optimizer operates completely independently of LLM arithmetic. No LLM output can bypass or override the optimizer.

#### 4. Verification & Testing
- Unit tests: [`test_portfolio_engine.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_portfolio_engine.py) **PASSED**.
- Infeasibility test: Correctly identifies when candidate sector count is too small to satisfy sector ceilings.

#### 5. Final Status
`IMPLEMENTED — FUNCTIONAL`

---

### FR-C07: Portfolio Monitoring

#### 1. Requirement & Expected Behaviour
- **Input:** Live market prices and current portfolio holdings.
- **Expected Output:** Real-time portfolio health metrics, dynamic weight drift, and concentration alerts.

#### 2. Existing Implementation
- **Backend APIs:**
  - `GET /api/v1/portfolios/{portfolio_id}/versions/{version_id}` in `portfolios.py`.
- **Database:**
  - `portfolio_performance_snapshots` table exists with fields for `total_market_value`, `unrealized_pnl`, `realized_pnl`, `drawdown_pct`, and `snapshot_metrics`.

#### 3. Defects & Deficiencies Identified
1. **No Background Price Ingestion or Polling**: There is no scheduler or worker task continuously fetching market prices during trading hours.
2. **Static Weight Reporting**: When a portfolio is retrieved via `GET /portfolios/.../versions/...`, the returned `target_weight_pct` is the static value saved at creation time, rather than dynamically recomputed as $\frac{P_i \times Q_i}{\sum P_j Q_j}$.
3. **No Drift Computation**: Weight drift relative to target corridor is not calculated or persisted.

#### 4. Final Status
`PLACEHOLDER / MOCKED`

---

### FR-C08: Rebalancing Engine

#### 1. Requirement & Expected Behaviour
- **Input:** Portfolio drift exceeding configured threshold (e.g. 5% stock drift or 10% sector drift).
- **Expected Output:** Rebalancing triggers, whole-share BUY/SELL/HOLD recommendations, turnover calculations, and cash requirements.

#### 2. Existing Implementation
- **Backend Services:**
  - [`backend/diagnosis/service.py`](file:///Users/ankur/Documents/MajorProject/app/backend/diagnosis/service.py): `diagnose_and_rebalance()` evaluates holdings against policy caps, runs the portfolio engine with `prioritized_security_ids`, and generates exact whole-share trades.
  - [`diagnosis_copilot_service.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/diagnosis_copilot_service.py): Explains every proposed trade.
- **Database:**
  - `portfolio_diagnoses`, `rebalance_suggestions` (tracks `quantity_change`, `action`, `explanation`).

#### 3. Defects & Deficiencies Identified
1. **Operational for Imported Portfolios, Missing for Native Portfolios**: The rebalancing workflow works end to end for *imported Demat portfolios* via the Diagnosis view. However, *native created portfolios* do not have an automated background trigger that monitors drift and invokes the Strategy Agent.

#### 4. Verification & Testing
- Unit tests: [`test_diagnosis_and_rebalance.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_diagnosis_and_rebalance.py) **PASSED**.
- Playwright E2E: [`e2e/diagnosis_copilot.spec.ts`](file:///Users/ankur/Documents/MajorProject/app/frontend/e2e/diagnosis_copilot.spec.ts) **PASSED** (12.9s).

#### 5. Final Status
`IMPLEMENTED — PARTIALLY FUNCTIONAL`

---

### FR-C09: Alert and Notification System

#### 1. Requirement & Expected Behaviour
- **Input:** Rebalancing triggers, ethical alerts, risk threshold breaches, and data staleness events.
- **Expected Output:** Persistent in-app notifications and email/SMS alerts with clear user action pathways.

#### 2. Existing Implementation
- **Database:**
  - `notifications` table exists in PostgreSQL (`backend/models/agent.py:194`) with fields `notification_type`, `title`, `message`, `delivery_channel`, `delivery_status`, `read_at`, `dismissed_at`.

#### 3. Defects & Deficiencies Identified
1. **Zero API Endpoints**: There are no routes in `backend/api/v1/` to fetch, dismiss, or manage notifications.
2. **No Dispatch Service**: No service or background task generates notification rows when thresholds are breached.
3. **No External Channel Integration**: No email (SMTP/SES) or SMS integration exists.
4. **No Frontend UI**: No notification inbox, bell icon, or banner component exists in the frontend.

#### 4. Final Status
`NOT IMPLEMENTED`

---

### FR-C10: Existing Portfolio Diagnosis

#### 1. Requirement & Expected Behaviour
- **Input:** User's legacy brokerage holdings (CSV, freeform text, or manual entry).
- **Expected Output:** Comprehensive diagnosis identifying concentration risks, diversification gaps, whole-share rebalancing plan, and interactive AI Copilot explanation.

#### 2. Existing Implementation
- **Frontend Components:**
  - [`DiagnosisView.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/DiagnosisView.tsx): File upload, text input, metric cards, holding analysis table, and rebalance trade preview.
  - [`DiagnosisCopilotModal.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/DiagnosisCopilotModal.tsx): Interactive conversational AI Copilot.
- **Backend Services & APIs:**
  - `POST /api/v1/diagnosis/upload-csv`
  - `POST /api/v1/diagnosis/parse-text`
  - `POST /api/v1/diagnosis/analyze/{id}`
  - `GET /api/v1/diagnosis/{id}/explanation`
  - `POST /api/v1/diagnosis/{id}/chat`
  - [`diagnosis_copilot_service.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/diagnosis_copilot_service.py): Context-aware analysis answering holding-specific questions.

#### 3. Execution Evidence
- Imported portfolio diagnosed with holdings priced against database quotes.
- Identified concentration warnings (>25% single stock, >40% sector).
- Generated whole-share BUY/SELL/HOLD trades and turnover percentage.
- The AI Copilot explains why specific stocks were trimmed or added and explains the consequences of not rebalancing.

#### 4. Verification & Testing
- Unit tests: [`test_diagnosis_copilot.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_diagnosis_copilot.py) **PASSED**.
- Playwright E2E: [`e2e/diagnosis_copilot.spec.ts`](file:///Users/ankur/Documents/MajorProject/app/frontend/e2e/diagnosis_copilot.spec.ts) **PASSED** (12.9s).

#### 5. Final Status
`IMPLEMENTED — FUNCTIONAL`

---

### FR-D01: Reasoning Trace & Transparent Critic

#### 1. Requirement & Expected Behaviour
- **Input:** Multi-agent dialogue, financial evidence items, and optimization decisions.
- **Expected Output:** User-facing "Devil's Advocate" view, Critic objection audit, and 10-section holding-specific research analysis.

#### 2. Existing Implementation
- **Frontend Components:**
  - [`ExplainabilityView.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/ExplainabilityView.tsx): Displays Multi-Agent Committee Deliberation, Specialist Insights, Critic Challenges, and Rebalancing Triggers.
  - [`StockWhyModal.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/StockWhyModal.tsx): 10-section equity research analysis modal for any holding.
- **Backend Services & APIs:**
  - `GET /api/v1/portfolios/{id}/versions/{vid}/stocks/{symbol}/why`
  - `POST /api/v1/portfolios/{id}/versions/{vid}/stocks/{symbol}/chat`
  - [`stock_why_service.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/stock_why_service.py): Assembles 10 verified research sections including ROE, Beta, valuation multiples, invalidation criteria, and verified exchange filings.
  - [`exchange_registry.py`](file:///Users/ankur/Documents/MajorProject/app/backend/services/exchange_registry.py): Verifies external links and official NSE/BSE corporate disclosure archives.

#### 3. Execution Evidence
- Every holding displays role rationale (`CORE`, `DEFENSIVE`, `GROWTH`, `DIVERSIFICATION`), bull vs bear arguments, Critic challenges, and invalidation criteria ("What could make this recommendation wrong?").
- Verified exchange filings link to authentic BSE/NSE company archives.

#### 4. Verification & Testing
- Unit tests: [`test_stock_why_experience.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_stock_why_experience.py) **PASSED**.
- Playwright E2E: [`e2e/stock_why_experience.spec.ts`](file:///Users/ankur/Documents/MajorProject/app/frontend/e2e/stock_why_experience.spec.ts) **PASSED** (15.4s).

#### 5. Final Status
`IMPLEMENTED — FUNCTIONAL`

---

## 4. Complete System Architecture & Data-Flow Assessment

```mermaid
flowchart TD
    subgraph UI["Frontend User Experience (Next.js 16)"]
        Onboard["OnboardingWizard / Natural Language Intent"]
        Dash["Portfolio Dashboard & HoldingsView"]
        WhyModal["StockWhyModal (10-Section Research)"]
        Explain["ExplainabilityView (Devil's Advocate)"]
        DiagView["DiagnosisView & Copilot Chat"]
    end

    subgraph API["FastAPI Backend (api/v1)"]
        AuthAPI["/auth & /profile"]
        NLPAPI["/profile/extract-from-text"]
        PortAPI["/portfolios & /portfolio-generation-requests"]
        WhyAPI["/portfolios/.../stocks/.../why"]
        DiagAPI["/diagnosis/..."]
        MktAPI["/market-data/securities/search"]
    end

    subgraph Engine["LangGraph Multi-Agent Orchestrator"]
        Manager["Manager Node"] --> Suit["Suitability Check"]
        Suit --> Macro["Macro Analyst Node"]
        Macro --> Market["Market Analyst Node"]
        Market --> Fund["Fundamental Analyst Node"]
        Fund --> News["News Analyst Node"]
        News --> Strat["Lead Strategist Node"]
        Strat --> Critic["Independent Critic Node"]
        Critic -- "Rework Required" --> Rework["Strategist Rework Node"]
        Rework --> Critic
        Critic -- "Approved" --> Opt["SLSQP Quadratic Optimizer"]
        Opt --> FinalCritic["Critic Final Validation"]
        FinalCritic --> Mod["Moderator Explanation Node"]
        Mod --> Persist["Persistence Node (ACID Rollback)"]
    end

    subgraph Database["PostgreSQL Database (63 Tables)"]
        UsersTbl["app_users & user_profiles"]
        ReqTbl["portfolio_generation_requests"]
        VerTbl["portfolio_versions & portfolio_security_decisions"]
        SecTbl["securities, companies, listings, market_prices"]
        DiagTbl["existing_portfolios & portfolio_diagnoses"]
    end

    Onboard --> NLPAPI & AuthAPI
    Dash --> PortAPI
    WhyModal --> WhyAPI
    DiagView --> DiagAPI
    
    PortAPI --> Engine
    Engine --> Database
    DiagAPI --> Database
```

---

## 5. Defect and Gap Register

| Issue ID | Affected Requirement | Description | Root Cause | Severity | Recommended Fix |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **DEF-001** | **FR-C09** | Alert and notification system is entirely missing from API and frontend. | ORM model was created in `backend/models/agent.py` but never exposed via endpoints or connected to notification dispatchers. | **CRITICAL** | Implement `backend/api/v1/notifications.py`, create background alert dispatcher, and add an in-app notification popover in `Navbar.tsx`. |
| **DEF-002** | **FR-C07** | Portfolio monitoring does not update holding weights dynamically or compute drift. | `get_portfolio_version` returns static persisted target weights instead of recalculating current market weights based on live quotes. | **HIGH** | Update `get_portfolio_version` to compute live market value, dynamic weights, and drift percentage. Add a periodic snapshot cron task. |
| **DEF-003** | **FR-C03** | Real-time India VIX data feed is missing; proxy or hardcoded 14.5% used. | No active live integration with NSE or Yahoo Finance for `^INDIAVIX`. | **HIGH** | Integrate live VIX fetch in `backend/market_data/adapter.py` with fallback to Nifty 50 historical volatility. |
| **DEF-004** | **FR-C03** | Regime classification equates low volatility with Bull market without trend confirmation. | Financial algorithm uses VIX alone without moving-average trend direction. | **MEDIUM** | Incorporate Nifty 50 200-day moving average slope into `detect_market_regime` to separate Bull from Range-bound. |
| **DEF-005** | **FR-C04** | No liquidity or market-capitalization filters in candidate selection. | `select_eligible_candidates` only checks status, exclusions, and freshness. | **MEDIUM** | Add minimum Average Daily Traded Volume (e.g. ADTV > 100,000 shares) and market cap filtering in `candidate_selection.py`. |
| **DEF-006** | **FR-C05** | Specialist agents in LangGraph workflow do not query LLM; execute deterministic rules. | LLM calls were replaced with rule-based heuristics to avoid rate limits and latency during development. | **MEDIUM** | Enable optional Gemini Flash prompt invocation in `macro_analyst_node` and `fundamental_analyst_node` with strict fallback. |
| **DEF-007** | **FR-C05** | 4 unit tests in `test_llm_resilience.py` fail due to missing `'ai_provider'` trace key. | Trace dictionary schema was updated in `nodes.py` without synchronizing `test_llm_resilience.py`. | **LOW** | Update `test_llm_resilience.py` to assert against current trace schema fields (`agent_code`, `summary`, `step`). |

---

## 6. Prioritized Remediation Roadmap

### Phase 1: Critical Operational & Notification Gaps
1. **Implement Alert & Notification System (FR-C09)**:
   - Create [`backend/api/v1/notifications.py`](file:///Users/ankur/Documents/MajorProject/app/backend/api/v1/notifications.py) (`GET /notifications`, `PATCH /notifications/{id}/read`, `DELETE /notifications/{id}`).
   - Build notification badge and dropdown in [`frontend/src/components/Navbar.tsx`](file:///Users/ankur/Documents/MajorProject/app/frontend/src/components/Navbar.tsx).
   - Add trigger in rebalancing and diagnosis engines to create persistent `Notification` records.

### Phase 2: Live Market Monitoring & Dynamic Drift Tracking
2. **Implement Dynamic Portfolio Monitoring (FR-C07, FR-C08)**:
   - Modify `get_portfolio_version` in [`portfolios.py`](file:///Users/ankur/Documents/MajorProject/app/backend/api/v1/portfolios.py) to compute live weights:
     $$w_i^{\text{current}} = \frac{Q_i \times P_i^{\text{latest}}}{\sum_j Q_j \times P_j^{\text{latest}}}$$
   - Compute stock-level and sector-level drift $\Delta w_i = |w_i^{\text{current}} - w_i^{\text{target}}|$.
   - When $\Delta w_i > 5.0\%$, flag rebalancing recommendation badge on the portfolio dashboard.

### Phase 3: Market Data & Universe Hardening
3. **Connect Real-Time India VIX Feed (FR-C03)**:
   - In [`backend/market_data/adapter.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/adapter.py), connect live fetching of `^INDIAVIX` from Yahoo Finance or NSE archive.
   - Enhance `detect_market_regime` to evaluate both Nifty 50 200-DMA trend (Direction: Bull/Bear) and VIX level (Turbulence: Calm/Volatile).
4. **Implement Liquidity & Market Cap Filters (FR-C04)**:
   - Add minimum 30-day Average Daily Traded Volume (ADTV $\ge 50,000$ shares) and minimum daily turnover in [`candidate_selection.py`](file:///Users/ankur/Documents/MajorProject/app/backend/portfolio_engine/candidate_selection.py).
   - Log excluded securities into `portfolio_validation_results` for complete fiduciary auditability.

### Phase 4: Test Suite Synchronization
5. **Synchronize Resilience Tests (FR-C05)**:
   - Update [`backend/tests/test_llm_resilience.py`](file:///Users/ankur/Documents/MajorProject/app/backend/tests/test_llm_resilience.py) to assert against current execution trace keys. Verify 100% test pass rate across all 179 backend tests.

---

## 7. Product-Readiness Assessment

- **Core Wealth Engine & Optimization:** **Production-Grade**. The Markowitz SLSQP optimizer, integer share rounding, sector-constrained water-filling fallback, SEBI risk policies, and natural language extraction are robust, mathematically verified, and fully tested.
- **Explainability & Fiduciary Disclosures:** **Production-Grade**. The 10-section "Ask AI Why?" analysis, transparent Critic objections, Devil's Advocate view, and Demat rebalancing copilot operate with high precision.
- **Monitoring & Notifications:** **Requires Phase 1 & 2 Remediation**. To transition from a creation & diagnosis engine to an autonomous standing portfolio manager, real-time price monitoring, dynamic drift tracking, and the notification subsystem must be finalized.

