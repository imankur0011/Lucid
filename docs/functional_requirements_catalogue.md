# Functional Requirements Catalogue
**Application:** Arthava (Intelligent Portfolio Creation & Rebalancing Engine)  
**Document:** `docs/functional_requirements_catalogue.md`  
**Classification:** Core, Differentiating, Supporting, Advanced, and Out-of-Scope Requirements  
**Standard:** Rigorous, Testable, Implementation-Ready Specifications with Investor-Implementation Separation

---

## 1. Master Requirements Summary Table

| Req ID | Requirement Name | Category | Status | Priority | User Story | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-C01** | User Onboarding & Risk Profiling | Core / MVP | Implemented & Verified | Must Have | As a beginner investor, I want to answer a structured profile questionnaire so my portfolio matches my real financial capacity. | Automated Pytest (`test_investor_api.py`) & Playwright Module 3 |
| **FR-C02** | Conversational Strategy & Exclusion Parsing | Core / MVP | Implemented & Verified | Must Have | As an investor, I want to specify preferences in natural English so I don't have to navigate complex financial dropdowns. | Automated Integration Test (`test_concurrency_and_failures.py`) |
| **FR-C03** | Multi-Factor Stock Universe Eligibility | Core / MVP | Implemented & Verified | Must Have | As an investor, I want only healthy, liquid, compliant stocks considered so my money isn't put in risky micro-caps. | Database & Seeding Test (`test_market_data.py`) |
| **FR-C04** | Deterministic Portfolio Optimization (SLSQP) | Core / MVP | Implemented & Verified | Must Have | As an investor, I want my asset weights calculated mathematically to minimize risk, rather than guessed by an AI model. | Numerical Unit Test (`test_portfolio_engine.py::test_optimize_portfolio_slsqp`) |
| **FR-C05** | Post-Rounding Integer-Share Feasibility & Cash Accounting | Core / MVP | Implemented & Verified | Must Have | As an investor, I want to see exact share quantities and remaining cash so I know my budget will actually work on the exchange. | Numerical Unit Test (`test_portfolio_engine.py::test_integer_share_rounding`) |
| **FR-C06** | Mathematical Safety Guardrails & Concentration Caps | Core / MVP | Implemented & Verified | Must Have | As an investor, I want firm limits on how much is invested in any one stock or sector to prevent catastrophic losses. | Property Test (`test_portfolio_engine.py::test_constraint_validator`) |
| **FR-C07** | Fiduciary Reasoning & Grounded Evidence Citations | Core / MVP | Implemented & Verified | Must Have | As an investor, I want plain-language explanations with dates and sources for why each company was chosen. | Playwright E2E Module 8 & Schema Validator |
| **FR-C08** | Portfolio Diagnosis & Simulated Whole-Share Rebalancing | Core / MVP | Implemented & Verified | Must Have | As an investor with existing stocks, I want clear buy/sell/hold guidance to fix portfolio drift and reduce risk. | Pytest (`test_diagnosis_and_rebalance.py`) & Playwright Module 7 |
| **FR-C09** | Macroeconomic Stress Testing & Scenario Simulation | Core / MVP | Implemented & Verified | Should Have | As an investor, I want to see how my portfolio would hold up in a market crash before putting real money at risk. | Playwright E2E Module 9 & Stress Engine Tests |
| **FR-C10** | Standardized Benchmark Comparative Backtesting | Core / MVP | Implemented & Verified | Should Have | As an investor, I want to compare this strategy against the Nifty 50 over 3 years to evaluate its historical risk/return. | Automated Pytest (`test_benchmark_and_comparison.py`) & Playwright Module 4 |
| **FR-S01** | Cryptographic Authentication & User Data Isolation | Supporting | Implemented & Verified | Must Have | As an investor, I want my financial goals and portfolios to remain strictly private and inaccessible to others. | Security Pytest (`test_auth_and_security.py`) & Playwright Module 11 |
| **FR-S02** | Immutable Recommendation Versioning & Comparison | Supporting | Implemented & Verified | Must Have | As an investor, I want to save multiple portfolio versions and compare them side by side without losing history. | Database Pytest (`test_database.py`) & Playwright Module 10 |
| **FR-S03** | Stale Market Data Detection & User Warning | Supporting | Implemented & Verified | Must Have | As an investor, I want to know if prices are older than normal so I don't make decisions on outdated information. | Data Quality Pytest (`test_market_data.py`) |
| **FR-S04** | WCAG 2.1 AA Accessibility & Responsive Viewports | Supporting | Implemented & Verified | Must Have | As a user on a mobile device, I want a clean, legible interface that is easy to navigate with one hand. | Playwright Mobile Viewport Test (Module 12) |
| **FR-A01** | Multi-Version Decision Counterfactual ("What-If") | Advanced | Implemented & Verified | Should Have | As an investor, I want to see what happens to my portfolio if I change my time horizon or risk tolerance. | Playwright E2E Interaction Test |
| **FR-A02** | Independent AI Explanation Consistency Validator | Advanced | Partially Implemented | Should Have | As an investor, I want to be certain that written explanations match the exact numbers in my portfolio table. | Deterministic Assertion Script |
| **FR-A03** | Out-of-Sample Walk-Forward Backtesting Engine | Advanced | Missing | Could Have | As an analytical investor, I want walk-forward cross-validation to verify that the strategy doesn't overfit history. | Statistical Python Script & CI Pipeline |
| **FR-X01** | Live Broker API Execution (Real Money Orders) | Out of Scope | Out of Scope | Excluded | As an investor, I want the app to place live orders on Zerodha/Groww. | Deliberately excluded; requires SEBI RIA/Broker license and custody audits. |

---

## 2. Detailed Functional Requirements Specifications

---

### FR-C01: User Onboarding and Risk Capacity Profiling

- **Requirement ID:** `FR-C01`
- **Category:** Core / MVP
- **Implementation Status:** Implemented & Verified
- **User Problem:** Retail investors often conflate psychological risk appetite with objective risk capacity, leading to portfolios they panic-sell during routine market drawdowns.
- **User Story:**  
  *As an inexperienced retail investor, I want a quick, structured onboarding questionnaire that distinguishes my ability to absorb loss from my willingness to take risk, so that my portfolio matches my actual life situation.*
- **User-Facing Behavior:**  
  The interface displays a clean, 5-question behavioral and demographic questionnaire. Clear, non-technical explanations describe why each question is asked. Upon submission, the investor receives a plain-English profile classification (*Conservative, Moderate, Aggressive*) with a summary of what that means for their stock-to-cash mix.
- **Input Parameters:**
  - *Required:* Investment Capital (INR $\geq 10,000$), Investment Horizon (Short/Mid/Long), Behavioral Reaction to -15% drawdown, Primary Goal (Wealth Creation, Retirement, Education).
  - *Optional:* Existing monthly savings rate, liquidity buffer status.
  - *Derived:* Risk Capacity Score ($[1, 5]$), Target Volatility Band ($[8\%, 22\%]$).
- **Business Rules:**
  - Capital must be $\geq ₹10,000$ to ensure viable integer-share diversification across at least 5 securities.
  - If horizon is $< 1$ year, portfolio engine automatically clamps maximum equity exposure to $\leq 30\%$ regardless of user risk appetite to preserve capital.
- **Acceptance Criteria:**
  - *Positive:* Valid inputs produce a confirmed profile and save to the database under the authenticated user's ID.
  - *Negative:* Capital $< ₹10,000$ or missing horizon prevents form submission and displays an actionable validation message: *"Please specify at least ₹10,000 to construct a viable diversified portfolio."*
- **Verification Method:** Pytest `backend/tests/test_investor_api.py::test_create_and_get_investor_profile` and Playwright E2E Module 3.
- **Internal Implementation Note (Developer Only):**  
  Profile data is persisted in the `profiles` table via `POST /api/v1/investor/profile`. The risk profiler algorithm (`backend/portfolio_engine/risk_profiler.py`) computes a deterministic composite score based on age, income regularity, and drawdown tolerance.

---

### FR-C04: Deterministic Portfolio Optimization (SLSQP)

- **Requirement ID:** `FR-C04`
- **Category:** Core / MVP
- **Implementation Status:** Implemented & Verified
- **User Problem:** Black-box AI platforms use generative LLMs to invent asset percentages, leading to ungrounded weights, negative cash balances, or arbitrary risk allocations.
- **User Story:**  
  *As an investor, I want my asset allocations calculated by a proven mathematical optimization algorithm that minimizes risk for my expected return, so that I can trust the numbers.*
- **User-Facing Behavior:**  
  The investor sees target percentage weights and exact rupee allocations for each security. The interface presents a visual verification badge confirming: *"Asset weights mathematically optimized to balance returns against market volatility (Markowitz Mean-Variance)."*
- **Input Parameters:**
  - *Required:* Historical price covariance matrix $\Sigma \in \mathbb{R}^{n \times n}$, expected returns vector $\mu \in \mathbb{R}^n$, single-stock upper bound $u_i \in (0, 1]$, sector caps $S_k \in (0, 1]$.
  - *Derived:* Optimal weight vector $w^* = [w_1^*, \dots, w_n^*]^T$.
- **Business Rules:**
  - Normalized weight constraint: $\sum_{i=1}^n w_i = 1$.
  - Long-only constraint (no shorting): $0 \leq w_i \leq u_i$ for all $i \in \{1, \dots, n\}$.
  - Sector concentration constraint: $\sum_{i \in \text{Sector}_k} w_i \leq S_k$ for all sectors $k$.
  - Optimization objective: $\min_{w} \frac{1}{2} w^T \Sigma w - \lambda \mu^T w$, where $\lambda \geq 0$ corresponds to user risk tolerance.
- **Acceptance Criteria:**
  - *Positive:* SLSQP solver converges within numerical tolerance $\epsilon = 10^{-4}$; returned weights sum to $1.0 \pm 10^{-4}$; no single stock exceeds user cap $u_i$.
  - *Negative:* Infeasible constraints (e.g., $u_i = 0.05$ with only 10 eligible stocks) trigger `PortfolioOptimizationException` returning HTTP 422 with investor-facing explanation: *"Unable to satisfy requested concentration limits with the available eligible securities. Please relax your single-stock cap."*
- **Verification Method:** Pytest `backend/tests/test_portfolio_engine.py::test_optimize_portfolio_slsqp`.
- **Internal Implementation Note (Developer Only):**  
  Implemented in `backend/portfolio_engine/engine.py` using `scipy.optimize.minimize(method='SLSQP')`. The LLM has zero involvement in computing numerical weights.

---

### FR-C05: Post-Rounding Integer-Share Feasibility & Cash Accounting

- **Requirement ID:** `FR-C05`
- **Category:** Core / MVP
- **Implementation Status:** Implemented & Verified
- **User Problem:** Real equity exchanges in India (NSE/BSE) only trade whole shares. Fractional theoretical weights (e.g., "Buy 3.7 shares of Reliance") cannot be executed, and naive rounding causes severe budget overshoots or altered portfolio risk.
- **User Story:**  
  *As an investor with a fixed budget, I want to see the exact whole number of shares to buy and the remaining cash reserve, so that my portfolio is 100% executable without borrowing or exceeding my budget.*
- **User-Facing Behavior:**  
  The holdings table displays exact integer quantities ($q_i \in \mathbb{Z}_{\geq 0}$), share prices, and total cost per holding. A dedicated summary line displays: *"Unallocated Cash Reserve: ₹X,XXX (X.X%) — Retained because Indian equity markets require purchasing whole shares."*
- **Input Parameters:**
  - *Required:* Optimal continuous weights $w_i^*$, Total capital budget $B$, Reference share prices $p_i > 0$.
  - *Derived:* Integer quantities $q_i = \lfloor \frac{w_i^* B}{p_i} \rfloor$, Allocated Capital $C_{alloc} = \sum_{i=1}^n p_i q_i$, Cash Reserve $C_{rem} = B - C_{alloc}$.
- **Business Rules:**
  - Hard Invariant 1 (No Budget Deficit): $C_{alloc} \leq B \iff C_{rem} \geq 0$.
  - Hard Invariant 2 (Budget Conservation): $C_{alloc} + C_{rem} = B$.
  - Minimum Holding Check: If $p_i > w_i^* B$, quantity $q_i$ rounds to 0. If $q_i = 0$ for a primary holding, the engine reallocates unspent capital to the next eligible diversified holding or returns it to cash buffer.
- **Acceptance Criteria:**
  - *Positive:* For budget $B = ₹1,00,000$, all $q_i$ are integers; $\sum p_i q_i \leq 100000$; remaining cash is non-negative and properly displayed.
  - *Negative:* Price $p_i \leq 0$ raises validation error before rounding calculations.
- **Verification Method:** Pytest `backend/tests/test_portfolio_engine.py::test_integer_share_rounding` and Playwright E2E Module 7.
- **Internal Implementation Note (Developer Only):**  
  Handled by `compute_integer_allocations()` in `backend/portfolio_engine/engine.py`. Post-rounding validation runs immediately to confirm invariants before serialization.

---

### FR-C07: Fiduciary Reasoning and Grounded Evidence Citations

- **Requirement ID:** `FR-C07`
- **Category:** Core / MVP
- **Implementation Status:** Implemented & Verified
- **User Problem:** Retail investors are given recommendations without explanations, forcing blind trust, or receive AI hallucinations citing fabricated metrics and non-existent earnings reports.
- **User Story:**  
  *As an investor, I want to read clear, plain-language reasons for why each stock was chosen, accompanied by the actual financial data and dates that justify the recommendation.*
- **User-Facing Behavior:**  
  The "Explainability & Citations" view displays:
  1. *Overall Portfolio Strategy:* A concise 2-sentence investment thesis explaining the macro balance.
  2. *Per-Stock Rationale Cards:* Explains each stock's strategic role (e.g., *"Core defensive compounder providing steady dividends and lower volatility during market pullbacks"*).
  3. *Audited Evidence Citations:* Explicitly lists observed fundamentals (PE Ratio, ROE, 3-Yr Sales Growth) with observation dates and data sources.
  4. *Safety Verification Badge:* Highlights passed constraint checks (Concentration Cap, Sector Cap, Cash Balance).
- **Prohibited UI Output:** Internal agent names (`Strategist`, `Critic`, `Moderator`), prompts, hidden chains of thought, raw JSON payloads, Python stack traces.
- **Acceptance Criteria:**
  - *Positive:* Every recommended holding has a plain-English explanation card and at least 2 verified fundamental citations with source dates.
  - *Negative:* Inability to retrieve verified fundamentals displays: *"Evidence temporarily unavailable from data feed; recommendation based on quantitative index weights."*
- **Verification Method:** Playwright E2E Module 8.
- **Internal Implementation Note (Developer Only):**  
  The backend orchestrates a LangGraph state graph where internal agents generate qualitative theses grounded on audited database metrics from `models/market_data.py`. User-facing serializers strip all internal agent names before returning the payload to Next.js.

---

### FR-C08: Portfolio Diagnosis and Simulated Whole-Share Rebalancing

- **Requirement ID:** `FR-C08`
- **Category:** Core / MVP
- **Implementation Status:** Implemented & Verified
- **User Problem:** Investors holding existing stocks do not know when their portfolio has become overly concentrated or how to rebalance toward their target model without accidentally generating large tax liabilities or odd fractional lots.
- **User Story:**  
  *As an investor with existing stock holdings, I want to diagnose my portfolio's health and see an exact, step-by-step rebalancing preview with whole share buy/sell quantities.*
- **User-Facing Behavior:**  
  The "Diagnosis & Rebalancing" tab presents:
  - *Health Score:* Overall portfolio alignment score ($[0, 100]$).
  - *Risk Warnings:* Highlights stocks that have drifted above the 25% single-stock safety cap.
  - *Actionable Rebalancing Table:* For each holding, shows Current Qty, Target Qty, Action (`BUY`, `SELL`, `HOLD`), Share Adjustment ($\Delta q_i$), and Cash Flow Impact.
  - *Net Cash Balance Summary:* Shows net proceeds/cost of rebalancing and new cash buffer.
- **Acceptance Criteria:**
  - *Positive:* Clicking "Diagnose & Preview Rebalance" calculates integer adjustments; all proposed actions satisfy whole-share constraints; post-rebalance allocations satisfy concentration caps.
  - *Negative:* Empty portfolio displays clean empty state: *"No existing holdings detected. Import your holdings to run portfolio diagnosis."*
- **Verification Method:** Pytest `backend/tests/test_diagnosis_and_rebalance.py` and Playwright E2E Module 5 & 7.
- **Internal Implementation Note (Developer Only):**  
  Implemented in `backend/portfolio_engine/diagnosis.py` and `rebalancer.py`. Compares current weights $w_{curr}$ with target weights $w_{target}$, solves integer adjustment $\Delta q_i$, and validates net cash feasibility.
