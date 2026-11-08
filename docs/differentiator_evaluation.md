# Differentiator Evaluation & Competitor Analysis
**Application:** Arthava (Intelligent Portfolio Creation & Rebalancing Engine)  
**Document:** `docs/differentiator_evaluation.md`  
**Market Scope:** Indian Retail Wealthtech & Robo-Advisory Ecosystem (September/October 2026 Deep Research)  
**Competitors Analyzed:** smallcase, Univest, Motilal Oswal IAP, Savart, Wright Research, Jarvis Invest  
**Technical Benchmark:** MarketSenseAI (Alpha Tensor Technologies / Academic Multi-Agent Benchmark)

---

## 1. Competitive Landscape Matrix

Every competitor capability is classified based on reviewed public product documentation, regulatory filings, and deep-research findings:
- **Confirmed Present (✓):** Formally documented and active in the live product.
- **Not Found in Reviewed Sources (—):** Absent from public product screens, documentation, and regulatory disclosures after systematic review.
- **Unverified Hypothesis (?):** Reported in marketing literature, but technical implementation and investor availability could not be independently confirmed.

| Capability / Dimension | smallcase | Univest | Motilal Oswal IAP | Savart (APART AI) | Wright Research | Jarvis Invest | **Arthava (Our Solution)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Primary Business Model** | Model Basket Marketplace | Advisory + Brokerage | Packaged RIA Portfolios | AI Advisory + PMS | Quant Advisory + PMS | AI Advisory + PMS | Fiduciary Engine |
| **Universal Goal Onboarding** | — | ✓ | — | ✓ | ✓ | ✓ | **✓ (Structured & Traceable)** |
| **Bespoke Portfolio Generation** | — (Pre-packaged) | ✓ (Analyst sign-off) | — (Fixed baskets) | ✓ (Algorithmic) | ✓ (Factor-based) | ✓ (Risk-calibrated) | **✓ (Deterministic SLSQP)** |
| **Grounded Per-Stock Evidence** | — | — | — | — (Black Box) | Factor Scores only | — (Black Box) | **✓ (Audited Dates & Sources)** |
| **Post-Rounding Share Feasibility** | Broker-dependent | Broker-dependent | Broker-dependent | Internal PMS | Broker-dependent | Broker-dependent | **✓ (Built-in Invariant Engine)** |
| **Rebalance Impact Preview** | Partial | Partial | — (All-or-none) | Partial (PMS) | Diagnostic view | Partial | **✓ (Before $\rightarrow$ After Metrics)** |
| **Two-Level Investor Disclosure** | — | — | — | — | — | — | **✓ (Simple vs. Financial Detail)** |
| **Conversational "What-If" Stress** | — | — | — | — | — | — | **✓ (Hypothetical Shock Models)** |
| **Version History & Comparison** | Order history only | Transaction history | Order history | Portfolio history | Portfolio tracking | Portfolio tracking | **✓ (Multi-Version Audit Matrix)** |
| **Zero Implementation Leakage** | N/A | N/A | N/A | N/A | N/A | N/A | **✓ (Zero Agent/Stack Exposure)** |

---

## 2. In-Depth Analysis of the Six Competitors

### 1. smallcase (CASE Platforms Pvt. Ltd.)
- **Primary Role:** Technology platform offering themed baskets of stocks/ETFs managed by SEBI-registered professionals; integrated broker execution across 30+ brokers.
- **Scale:** Over 1 crore registered users across partner brokerages.
- **Verified Capabilities:** Excellent broker connectivity, one-click execution, recurring SIPs, historical backtests of model baskets.
- **Observed Gaps:**
  - *No Individual Goal-to-Allocation Personalization:* Users select pre-assembled thematic baskets (e.g., "All Weather Investing"); weights are not customized to an individual's personal capital or risk capacity.
  - *Lack of Narrative Explanation:* Does not provide plain-language, evidence-grounded rationales for why specific stocks are held at specific weights.
  - *No Counterfactual Simulator:* Users cannot test how changing their investment horizon alters the basket.

### 2. Univest (Univest Technologies Pvt. Ltd.)
- **Primary Role:** Integrated stock advisory, portfolio review, and discount brokerage.
- **Scale:** 20 lakh+ app downloads, SEBI RA / RIA registered entities.
- **Verified Capabilities:** AI preliminary screening combined with mandatory human SEBI analyst review before dispatching trade calls.
- **Observed Gaps:**
  - *Fragmented Disclosures:* Individual stock tips are distributed, but holistic portfolio-level optimization and risk-budgeting are secondary.
  - *Opaque Factor Models:* Underlying quantitative screening parameters are proprietary and not cited with verifiable source dates.

### 3. Motilal Oswal IAP (Intelligent Advisory Portfolios)
- **Primary Role:** Pre-packaged, algorithmic equity baskets managed by Motilal Oswal's RIA division.
- **Verified Capabilities:** Institutional research backing, automated rebalancing execution, disciplined risk profiling.
- **Observed Gaps:**
  - *All-or-None Customization:* Investors cannot customize an IAP—they can only accept or reject the entire portfolio basket.
  - *No Transparent Before-and-After Rebalance Preview:* Investors receive execution alerts without seeing the exact quantitative drift or risk reduction that triggered the rebalance.

### 4. Savart (Svobodha Infinity Pvt. Ltd.)
- **Primary Role:** AI-driven personalized advisory and Portfolio Management Services (PMS).
- **Scale:** 4 lakh+ registered users, ₹4,500+ crore Assets Under Advisory (AUA).
- **Verified Capabilities:** Proprietary "APART" AI system (Quant, IRIS, and Synapse neural networks) creating bespoke portfolios for individual risk profiles.
- **Observed Gaps:**
  - *Black-Box Problem:* APART operates as an entirely proprietary neural model. Investors cannot inspect the underlying calculations, constraint boundaries, or data freshness dates behind stock weights.
  - *Absence of Multi-Version Comparison:* No transparent mechanism for investors to compare Version 1 vs. Version 2 and see whether changes were caused by personal profile updates vs. market regime shifts.

### 5. Wright Research (Wright Research & Capital Pvt. Ltd.)
- **Primary Role:** Quantitative factor-investing advisory and SEBI-registered PMS.
- **Scale:** ₹2,000+ crore AUM/AUA across smallcase and PMS.
- **Verified Capabilities:** 300+ quantitative factor screens across 10 factor groups (Momentum, Value, Quality, Volatility); market regime classification via ML. Portfolio diagnostic tools are the most detailed in India.
- **Observed Gaps:**
  - *Complex Quant Dashboards Overwhelming for Beginners:* Factor score tables and regime diagrams assume significant statistical and financial sophistication.
  - *Lack of Plain-English Fiduciary Narrative:* Quantitative outputs are not translated into simple explanations for first-time investors.

### 6. Jarvis Invest (Ventura Securities / Jarvis Technology)
- **Primary Role:** AI-driven equity model portfolios with 24/7 Risk Management System (RMS).
- **Scale:** ~70,000 investors, ₹1,500+ crore AUA, integrated with 32+ brokers.
- **Verified Capabilities:** Dynamic risk-off alerts, automated exit calls when underlying company fundamentals deteriorate.
- **Observed Gaps:**
  - *Silent Execution Triggers:* While RMS alerts users to exit, it does not provide an interactive counterfactual preview showing how the exit alters portfolio-level concentration, volatility, and unallocated cash.

---

## 3. Detailed Evaluation of Arthava's Defensible Differentiators

---

### Differentiator 1: Complete Goal-to-Holding Traceability (Investor-Facing Provenance)

- **User Problem:** In black-box apps, investors have no idea why they received 12% in ICICI Bank and 8% in Infosys. They cannot tell if recommendations were personalized or drawn from a static template.
- **Target User & Use Case:** First-time and conservative retail investors seeking reassurance that recommendations directly reflect their stated goals, constraints, and risk capacity.
- **Competitor Evidence:**
  - *Savart:* Algorithmic, but proprietary black box; no inspectable chain.
  - *smallcase / MO IAP:* Static model baskets; zero individual traceability.
  - *Wright / Jarvis:* Factor screens and RMS run internally; explicit provenance chain is not exposed.
- **Specific Improvement:**  
  Arthava records and displays a clean 4-stage provenance breadcrumb:  
  *Goal (Wealth Creation) $\rightarrow$ Constraints (Max 25% single stock, No Tobacco) $\rightarrow$ Selection Criteria (Top ROE & Dividend Compounders) $\rightarrow$ Optimized Whole Shares (18.5% = 6 Shares).*
- **Investor-Visible Behavior:**  
  The investor clicks any holding card to expand a "Decision Journey" modal showing exactly which stated goal and mathematical constraints shaped that holding's quantity.
- **Internal Technical Mechanism (Developer Only):**  
  Tracked via `provenance_id` linking the `portfolio_requests`, `portfolios`, `allocations`, and `market_universe` database records.
- **Acceptance & Verification:**  
  Verified by Playwright Module 10 and database foreign key integration tests.
- **Priority:** **MVP / Core Trustworthiness (Stage 1)**.

---

### Differentiator 2: Audited Evidence Citations with Observation Timestamps

- **User Problem:** AI chat tools and black-box robo-advisors frequently hallucinate metrics or cite outdated, unverified corporate figures.
- **Target User & Use Case:** Skeptical investors who want to verify that claims are supported by audited corporate filings before committing hard-earned savings.
- **Competitor Evidence:**
  - *Univest / Jarvis / Savart:* Show high-level analyst commentary or AI summaries without verifiable observation timestamps or audited source tags.
- **Specific Improvement:**  
  Every material financial assertion is tied to a specific evidence record:
  - Metric: Return on Equity (ROE) = 18.4%
  - Source: Audited Financial Results / NSE Corporate Data
  - Observation Date: 30 September 2026
  - Quality Status: Verified / Non-Stale
- **Investor-Visible Behavior:**  
  In the Explainability tab, an "Audited Evidence" pill tag accompanies each holding. Clicking it reveals the date, filing source, and raw metric value.
- **Acceptance & Verification:**  
  Verified by Playwright Module 8 and Pytest `test_market_data.py`.
- **Priority:** **MVP / Core Trustworthiness (Stage 1)**.

---

### Differentiator 3: Post-Rounding Integer-Share Invariant Engine

- **User Problem:** Every textbook optimizer produces fractional shares ($w_i^* B / p_i \notin \mathbb{Z}$). When an investor attempts to purchase ₹1,00,000 of shares on Zerodha or Upstox, they cannot buy 4.3 shares. Naive rounding up causes budget overruns; rounding down leaves large unmanaged cash.
- **Target User & Use Case:** Retail investors with finite budgets (₹10,000 to ₹5,00,000) who need exact, executable share counts.
- **Competitor Evidence:**
  - *smallcase:* Uses pre-calculated minimum investment thresholds based on whole shares, but does not solve a personalized budget-constrained integer optimization for arbitrary user budgets.
  - *Others:* Offload rounding to broker execution or PMS custody without exposing the post-rounding balance before execution.
- **Specific Improvement:**  
  Arthava's mathematical validation engine deterministically computes $q_i = \lfloor w_i^* B / p_i \rfloor$, validates that $\sum p_i q_i \leq B$, computes the exact cash buffer $C_{rem}$, and displays it with a plain-English explanation of why partial shares cannot be purchased.
- **Acceptance & Verification:**  
  Verified by Pytest `test_portfolio_engine.py::test_integer_share_rounding`.
- **Priority:** **MVP / Core Trustworthiness (Stage 1)**.

---

### Differentiator 4: Two-Level Progressive Disclosure (Zero Implementation Disclosure)

- **User Problem:** Advanced quant platforms (e.g., Wright Research) overwhelm beginner retail investors with 300 factor charts, whereas AI prototypes expose messy developer logs ("Agent Strategist returned status 200").
- **Target User & Use Case:** All retail investors. Novices read Level 1; analytical investors expand to Level 2.
- **Competitor Evidence:**
  - Competitors either hide everything behind a simple "Buy" button (Savart, smallcase) or display dense quant jargon (Wright). None implement a systematic two-level investor disclosure with strict suppression of backend engineering details.
- **Specific Improvement:**  
  Clean, institutional-grade presentation. Level 1 provides plain-English summaries, target holdings, whole shares, and primary risks. Level 2 provides quantitative ratios (Sharpe, Beta), mathematical constraint outcomes, and audited filing dates. **Never** exposes agent names, prompt templates, or database schemas.
- **Acceptance & Verification:**  
  Verified by complete visual audit (`arthava_dashboard_demo_1792317568065.webp`) and Playwright E2E suite.
- **Priority:** **MVP / Core Trustworthiness (Stage 1)**.

---

### Differentiator 5: Interactive Counterfactual "What-If" Trade-Off Preview

- **User Problem:** Investors do not understand the trade-offs of their own choices. If they choose "Conservative" instead of "Moderate", they do not know what returns they surrender or what drawdown protection they gain.
- **Target User & Use Case:** Inexperienced investors learning to calibrate their risk appetite.
- **Competitor Evidence:**
  - Not found in any reviewed Indian competitor. Users must discard their portfolio and generate a completely new profile to see differences.
- **Specific Improvement:**  
  A controlled counterfactual slider allows the user to see the exact reallocation and risk shift:
  - *"If you shift from Moderate to Conservative: Equity drops from 80% to 55%; Expected Volatility decreases by 3.8%; Maximum historical drawdown drops from -18.2% to -10.4%."*
- **Acceptance & Verification:**  
  Verified by Playwright E2E Module 9 & 10.
- **Priority:** **Stage 2: Advanced Differentiation**.

---

## 4. Differentiator Summary & Defensibility Ranking

| Differentiator | User Benefit | Technical Feasibility | Defensibility | Recommended Phase |
| :--- | :---: | :---: | :---: | :---: |
| **1. Complete Goal-to-Holding Traceability** | High | High (Implemented) | High | **Stage 1 (MVP)** |
| **2. Audited Evidence Citations & Dates** | High | High (Implemented) | High | **Stage 1 (MVP)** |
| **3. Post-Rounding Whole-Share Invariants** | High | High (Implemented) | Medium | **Stage 1 (MVP)** |
| **4. Two-Level Investor Progressive Disclosure** | Very High | High (Implemented) | Very High | **Stage 1 (MVP)** |
| **5. Transparent Rebalance Drift & Cash Preview** | High | High (Implemented) | High | **Stage 1 (MVP)** |
| **6. Conversational Counterfactual "What-If"** | High | Medium (Implemented) | High | **Stage 2 (Advanced)** |
| **7. Multi-Version Change Attribution Matrix** | Medium | High (Implemented) | High | **Stage 2 (Advanced)** |
| **8. Dynamic Ethical Exclusion Engine** | Medium | High (Implemented) | Medium | **Stage 1 (MVP)** |
| **9. Stale Data & Source Conflict Alerter** | High | High (Implemented) | High | **Stage 1 (MVP)** |
| **10. Out-of-Sample Walk-Forward Backtester** | Medium | Medium (Planned) | High | **Stage 3 (Future)** |
