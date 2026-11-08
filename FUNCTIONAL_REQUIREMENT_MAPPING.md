# Lucid — Functional Requirement to Implementation Traceability Mapping

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Scope:** Complete end-to-end trace from User Input to API, Backend Service, Agent/Engine, PostgreSQL Database, and Frontend Output for all Functional Requirements in Lucid.

---

## 1. Traceability Methodology

Every functional requirement in Lucid is mapped strictly through the 6-stage execution chain:
$$\text{User Input} \longrightarrow \text{FastAPI Endpoint} \longrightarrow \text{Backend Service} \longrightarrow \text{Agent / Engine} \longrightarrow \text{PostgreSQL Storage} \longrightarrow \text{UI Output}$$

### Implementation Status Classifications
- **IMPLEMENTED**: Active in runtime, verified by automated test suites.
- **PARTIALLY IMPLEMENTED**: Functional in core backend, but limited in automated frontend presentation.
- **SIMULATED / DECISION SUPPORT**: Data structures present, but non-custodial decision support provided in lieu of real-money custody.
- **PLANNED / OUT OF SCOPE**: Explicitly excluded from active runtime or deferred to future roadmap.

---

## 2. Core Functional Requirements (FR-C01 to FR-C10)

### FR-C01: User Onboarding & SEBI Risk Profiling
- **Status:** **IMPLEMENTED**
- **User Input:** Investor completes 5 psychometric risk questions (investment horizon, risk tolerance, financial knowledge, net worth fraction, reaction to 20% drawdown) via onboarding wizard.
- **API Endpoint:** `GET /api/v1/risk-questions`, `POST /api/v1/risk-assessments`
- **Backend Service:** `backend/api/v1/risk_assessments.py:calculate_risk_profile`
- **Agent / Engine:** `suitability_check_node` (`backend/agent/nodes.py`)
- **Database Tables:** `risk_questions`, `risk_question_options`, `risk_assessments`, `risk_assessment_answers`, `user_profiles`
- **Output:** Categorized risk profile (`conservative`, `moderate`, `aggressive`), quantitative risk score (0-100), and policy parameter ceilings.
- **Verification:** `backend/tests/test_investor_api.py`, `frontend/src/components/RiskQuestionnaireView.tsx`

---

### FR-C02: Conversational Strategy & Exclusion Parsing
- **Status:** **IMPLEMENTED**
- **User Input:** Freeform text input specifying sector exclusions (e.g., "no tobacco, no defense"), investment horizon, or capital adjustments in conversational chat.
- **API Endpoint:** `POST /api/v1/profile/nlp-extract`, `POST /api/v1/portfolios/{portfolio_id}/chat`
- **Backend Service:** `backend/portfolio_engine/nlp_profile_extractor.py`, `backend/portfolio_engine/conversational_assistant.py`
- **Agent / Engine:** `manager_node`, `nlp_profile_extractor`
- **Database Tables:** `user_sector_preferences`, `user_security_preferences`, `user_preferences`
- **Output:** Structured sector exclusion arrays, extracted investment horizon, and conversational clarification response.
- **Verification:** `backend/tests/test_nlp_profile_extraction.py`, `backend/tests/test_conversational_ai.py`

---

### FR-C03: Multi-Factor Candidate Universe & Liquidity Filtering
- **Status:** **IMPLEMENTED**
- **User Input:** Portfolio generation trigger (implicit: active user profile and investment capital).
- **API Endpoint:** `POST /api/v1/portfolio-generation-requests`
- **Backend Service:** `backend/portfolio_engine/candidate_selection.py:CandidateUniverseSelector`
- **Agent / Engine:** `CandidateUniverseSelector.select_eligible_candidates()`
- **Database Tables:** `securities`, `instrument_listings`, `companies`, `sectors`, `market_prices`
- **Output:** Filtered basket of eligible equities passing Tier 1 (Ultra Liquid) and Tier 2 (Broad Liquid) thresholds (ADTV $\ge 25,000$ shares, Daily Turnover $\ge$ ₹25 Lakhs, price freshness $\le 14$ days).
- **Verification:** `backend/tests/test_universe_lookback_news.py`, `backend/tests/test_market_regime_and_universe.py`

---

### FR-C04: Deterministic Portfolio Optimization (SLSQP)
- **Status:** **IMPLEMENTED**
- **User Input:** Approved candidate stock basket and risk category constraints from Agent Graph.
- **API Endpoint:** `POST /api/v1/portfolio-generation-requests`
- **Backend Service:** `backend/portfolio_engine/optimizer.py:optimize_portfolio`
- **Agent / Engine:** `deterministic_optimizer_node` (`backend/agent/nodes.py`) via `scipy.optimize.minimize(method='SLSQP')`
- **Database Tables:** `strategy_versions`, `portfolio_versions`, `portfolio_version_constraints`
- **Output:** Continuous optimal asset weights minimizing negative quadratic utility $0.5 \lambda \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} - \mathbf{w}^T \boldsymbol{\mu}$ subject to single-stock and sector limits.
- **Verification:** `backend/tests/test_portfolio_engine.py`, `scripts/verify_setup.py`

---

### FR-C05: Integer-Share Allocation & Residual Cash Accounting
- **Status:** **IMPLEMENTED**
- **User Input:** Total investment capital in INR (e.g., ₹200,000) and optimal continuous weights.
- **API Endpoint:** `POST /api/v1/portfolio-generation-requests`
- **Backend Service:** `backend/portfolio_engine/math_engine.py:compute_integer_share_allocation`
- **Agent / Engine:** `deterministic_optimizer_node` (`backend/agent/nodes.py`)
- **Database Tables:** `portfolio_security_decisions` (`allocated_shares`, `allocated_amount`, `weight_pct`)
- **Output:** Whole-share purchase quantities ($N_i = \lfloor \frac{w_i \cdot C}{P_i} \rfloor$), exact allocated rupee amounts, and transparent unallocated residual cash balance.
- **Verification:** `backend/tests/test_portfolio_engine.py::test_integer_share_rounding`

---

### FR-C06: Mathematical Safety Guardrails & Concentration Caps
- **Status:** **IMPLEMENTED**
- **User Input:** Risk profile policy rules and user-defined constraints.
- **API Endpoint:** `POST /api/v1/portfolio-generation-requests`
- **Backend Service:** `backend/portfolio_engine/constraints.py:validate_portfolio_constraints`
- **Agent / Engine:** `critic_node` & `critic_final_validation_node` (`backend/agent/nodes.py`)
- **Database Tables:** `portfolio_validation_runs`, `portfolio_validation_results`
- **Output:** Hard enforcement: Single stock cap ($\le 25\%$ moderate, $\le 15\%$ conservative), sector cap ($\le 35\%$), minimum 5 stocks, zero penny-stocks.
- **Verification:** `backend/tests/test_portfolio_engine.py::test_constraint_validator`

---

### FR-C07: Fiduciary Reasoning & Grounded Evidence Citations
- **Status:** **IMPLEMENTED**
- **User Input:** Investor clicks "Why this stock?" or expands recommendation rationale in UI.
- **API Endpoint:** `GET /api/v1/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/why`
- **Backend Service:** `backend/portfolio_engine/stock_why_service.py`
- **Agent / Engine:** `moderator_explanation_node` (`backend/agent/nodes.py`)
- **Database Tables:** `recommendation_explanations`, `explanation_evidence`, `evidence_items`
- **Output:** Multi-dimensional institutional investment thesis with explicit dates, source URLs, P/E vs industry comparisons, ROE, debt-to-equity ratios, and risk disclosures.
- **Verification:** `backend/tests/test_stock_why_experience.py`, `frontend/src/components/StockWhyModal.tsx`

---

### FR-C08: Portfolio Diagnosis & Simulated Whole-Share Rebalancing
- **Status:** **IMPLEMENTED**
- **User Input:** User inputs existing equity portfolio holdings manually or submits structured CAS statement.
- **API Endpoint:** `POST /api/v1/diagnosis/analyze/{existing_portfolio_id}`, `POST /api/v1/diagnosis/{existing_portfolio_id}/chat`
- **Backend Service:** `backend/diagnosis/service.py:PortfolioDiagnosisService`
- **Agent / Engine:** `PortfolioDiagnosisService.diagnose_and_rebalance()`
- **Database Tables:** `existing_portfolios`, `existing_portfolio_holdings`, `portfolio_diagnoses`, `rebalance_suggestions`
- **Output:** Herfindahl-Hirschman Index (HHI) concentration score, sector overlap alerts, and integer BUY/SELL/HOLD order preview with estimated Indian delivery taxes (STT, GST, Stamp Duty).
- **Verification:** `backend/tests/test_diagnosis_and_rebalance.py`, `frontend/src/components/DiagnosisView.tsx`

---

### FR-C09: Macroeconomic Stress Testing & Scenario Simulation
- **Status:** **IMPLEMENTED**
- **User Input:** Investor selects historical crisis scenario (e.g., 2008 Global Financial Crisis, 2020 COVID Market Crash, 2022 Interest Rate Shock).
- **API Endpoint:** `GET /api/v1/portfolios/{portfolio_id}/scenarios`
- **Backend Service:** `backend/portfolio_engine/service.py:simulate_stress_scenarios`
- **Agent / Engine:** `PortfolioScenarioEngine`
- **Database Tables:** `portfolio_scenarios`
- **Output:** Projected drawdown percentage, estimated rupee portfolio loss, and sector vulnerability breakdown.
- **Verification:** `backend/tests/test_benchmark_and_comparison.py`, `frontend/src/components/StressScenariosView.tsx`

---

### FR-C10: Standardized Benchmark Comparative Backtesting
- **Status:** **IMPLEMENTED**
- **User Input:** Target portfolio backtest request.
- **API Endpoint:** `GET /api/v1/portfolios/benchmark-evaluation`, `GET /api/v1/portfolios/compare`
- **Backend Service:** `backend/portfolio_engine/service.py:backtest_portfolio`
- **Agent / Engine:** `compute_portfolio_metrics`
- **Database Tables:** `portfolio_performance_snapshots`
- **Output:** 3-year historical comparative metrics against NIFTY 50: Annualized Return (CAGR), Annualized Volatility, Sharpe Ratio (7.0% risk-free rate), Maximum Drawdown, Beta, and Alpha.
- **Verification:** `backend/tests/test_benchmark_and_comparison.py`, `frontend/src/components/BenchmarksView.tsx`

---

## 3. Supporting Requirements (FR-S01 to FR-S04)

### FR-S01: Cryptographic Authentication & Multi-Tenant User Isolation
- **Status:** **IMPLEMENTED**
- **Implementation:** Salted Argon2id password hashing (`argon2-cffi`), JWT HS256 signed bearer tokens, `revoked_tokens` table for server-side token blacklisting on logout, and row-level `user_id` filtering on all database queries. In staging/production, unauthenticated requests strictly fail-closed with HTTP 401.
- **Verification:** `backend/tests/test_auth_and_security.py`

### FR-S02: Immutable Recommendation Versioning & Audit Trail
- **Status:** **IMPLEMENTED**
- **Implementation:** Every portfolio rebalance or generation creates a monotonically incremented `portfolio_versions` record with its own frozen constraints and allocation decisions. Previous versions cannot be modified in place.
- **Verification:** `frontend/src/components/VersionComparisonModal.tsx`, `backend/tests/test_database.py`

### FR-S03: Stale Market Data Detection & User Warning
- **Status:** **IMPLEMENTED**
- **Implementation:** `verify_listing_freshness()` flags any security whose latest close price is older than 14 calendar days. Securities with stale prices are marked `STALE_PRICE` and automatically excluded from candidate selection.
- **Verification:** `backend/tests/test_market_data.py`, `backend/tests/test_universe_lookback_news.py`

### FR-S04: Responsive Viewports & Accessibility
- **Status:** **IMPLEMENTED**
- **Implementation:** Built with Tailwind CSS v4 using responsive grid and flexbox layouts (`sm:`, `md:`, `lg:`, `xl:`), accessible contrast ratios, and touch-friendly button targets.
- **Verification:** `frontend/e2e/responsive.spec.ts`

---

## 4. Advanced & Out-of-Scope Requirements

| Req ID | Requirement Description | Implementation Status | Technical Rationale & Current Behavior |
|---|---|---|---|
| **FR-A01** | Multi-Version Decision Counterfactuals ("What-If") | **IMPLEMENTED** | Users can adjust capital or risk tolerance in UI and trigger simulated comparisons between candidate portfolios. |
| **FR-A02** | Independent AI Explanation Consistency Validator | **IMPLEMENTED** | Quantitative numbers (weights, shares, rupee amounts) in moderator explanations are verified against optimizer outputs. |
| **FR-A03** | Out-of-Sample Walk-Forward Backtesting Engine | **PLANNED** | Current implementation uses 3-year historical lookback; multi-period rolling walk-forward optimization is planned for Phase 3. |
| **FR-X01** | Live Broker API Order Execution (Zerodha/Groww) | **OUT OF SCOPE / DECISION SUPPORT** | Lucid operates strictly under a non-custodial decision-support model. Order instructions are generated for manual investor execution to comply with retail fiduciary boundaries. Real-money broker order placement is deliberately excluded. |
| **FR-X02** | Account Aggregator Automated Sync | **PLANNED** | Automated API sync via RBI Account Aggregator framework is planned for Phase 3; current system ingests structured demat holdings and CAS statements directly. |
| **FR-X03** | Graph Database & Vector DB (Neo4j / FAISS) | **EXCLUDED** | Lucid's multi-agent system operates efficiently using PostgreSQL 16 relational queries and direct LLM synthesis without graph or vector infrastructure overhead. |
