# Lucid — Viva Examination Questions & Model Answers
## Comprehensive Viva Defense Pack for Evaluators, Guides, and Technical Panels

---

## Category 1: General Project Overview & Vision (Q1 – Q6)

### Q1: What is the core problem Lucid solves, and who is the target user?
- **Concise Verbal Answer**:
  > "Lucid addresses the high failure rate among Indian retail equity investors—where over 90% lose money due to speculative finfluencer tips, severe portfolio concentration, and inability to rebalance. Our target users are retail investors looking to construct, monitor, and rebalance personalized, diversified, whole-share equity portfolios aligned with SEBI suitability standards."
- **Deep Technical Proof & Code Citation**:
  - The problem is formally framed in `backend/portfolio_engine/policy.py` and SEBI consultation papers.
  - Retail portfolio concentration is prevented at the code level via `MAX_PERMITTED_SINGLE_STOCK_PCT = 25.0` and `MAX_PERMITTED_SECTOR_PCT = 40.0` defined in `backend/portfolio_engine/policy.py` and audited in `backend/agent/nodes.py:720-780` (`adversarial_critic_node`).

### Q2: Why is Lucid designed as a non-custodial platform?
- **Concise Verbal Answer**:
  > "Lucid is strictly non-custodial to eliminate counterparty risk and operate cleanly within SEBI regulatory boundaries. We do not hold client funds or demat assets, and we do not auto-execute broker trades. We provide mathematically validated trade previews and order slips that the investor reviews and executes manually through their preferred broker."
- **Deep Technical Proof & Code Citation**:
  - Non-custodial boundaries are defined in `backend/portfolio_engine/rebalancing_service.py:145-180` and exported via standard CSV/JSON order slips in `backend/api/v1/portfolios.py:1550-1610` (`export_basket`).
  - No broker API secret keys with trading permissions are stored in plaintext; all broker models in `backend/models/broker.py` represent read-only holding snapshots.

### Q3: How is Lucid different from existing robo-advisors like Scripbox or Zerodha Coin?
- **Concise Verbal Answer**:
  > "Unlike traditional robo-advisors that place investors into static mutual fund risk buckets with zero visibility, Lucid directly optimizes direct equity portfolios with integer whole shares. We combine multi-agent AI research with deterministic Markowitz optimization, an adversarial Critic risk audit, and transparent stock-level 'Why This Stock' explainability citing live exchange filings."
- **Deep Technical Proof & Code Citation**:
  - Direct equity factor modeling in `backend/portfolio_engine/factors.py` calculates real-time factor exposures (Quality, Value, Momentum, Low Volatility).
  - The 10-section explainability dossier is generated dynamically in `backend/portfolio_engine/stock_why_service.py` with verified exchange announcement URLs.

### Q4: How does Lucid handle Indian colloquial expressions for money, like "2.5 Lakhs" or "50k"?
- **Concise Verbal Answer**:
  > "We built a specialized deterministic financial number parser that extracts Indian numerical words and abbreviations—such as 'lakh', 'lac', 'crore', 'cr', 'k', and words like 'twenty-five thousand'—and converts them into exact float rupee values without relying on error-prone LLM string manipulation."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/services/financial_number_parser.py:parse_indian_financial_number`.
  - Thoroughly tested across 14 edge cases in `backend/tests/test_dynamic_stock_and_number_parsing.py`.

### Q5: What is the dynamic stock discovery mechanism, and why was it necessary?
- **Concise Verbal Answer**:
  > "Previously, many systems relied on small hardcoded dictionaries of 10 or 15 tickers like RELIANCE and TCS. We replaced this with a dynamic fuzzy resolution service over our entire database of 2,000+ NSE and BSE equity instruments. It resolves informal brand names like 'Larsen' or 'Infy' to canonical NSE tickers dynamically."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/services/company_resolution_service.py` using trigram similarity and Levenshtein distance against the `companies`, `securities`, and `instrument_listings` tables in PostgreSQL.

### Q6: What market data feeds does Lucid connect to?
- **Concise Verbal Answer**:
  > "Lucid connects to Yahoo Finance for live quotes, historical OHLCV data, fundamentals, and India VIX (`^INDIAVIX`). It connects to the FRED API for macroeconomic interest rate series, NewsAPI and BSE RSS feeds for corporate filings, and maintains an offline `SimulatedMarketProvider` for deterministic testing in CI pipelines."
- **Deep Technical Proof & Code Citation**:
  - Architecture defined in `backend/market_data/adapter.py` (`MarketDataProvider`, `YFinanceProvider`, `SimulatedMarketProvider`).
  - Regime classifier implemented in `backend/market_data/regime.py:classify_market_regime`.

---

## Category 2: Agentic AI & LangGraph Multi-Agent Architecture (Q7 – Q14)

### Q7: Why did you choose LangGraph instead of a simple linear LangChain chain or a monolithic LLM prompt?
- **Concise Verbal Answer**:
  > "Portfolio creation is inherently non-linear and requires cyclical revision. A linear chain or single prompt cannot perform adversarial self-correction. LangGraph allows us to compile a state machine with conditional branching, parallel specialist agent execution, and bounded iteration loops where our Critic agent can reject an allocation and force the Strategist to rework it."
- **Deep Technical Proof & Code Citation**:
  - State machine graph defined in `backend/agent/graph.py:create_portfolio_graph` using `langgraph.graph.StateGraph`.
  - Conditional edge defined via `_route_critic_verdict` routing to either `optimizer` or `strategist_rework`.

### Q8: What are the 13 nodes in the Lucid agentic graph, and what does each do?
- **Concise Verbal Answer**:
  > "The graph comprises 13 nodes: (1) Manager for validation, (2) Suitability for risk/exclusions, (3-6) four parallel specialists for Macro, Market Volatility, Fundamentals, and News, (7) Lead Strategist for proposal synthesis, (8) Critic for adversarial audit, (9) Strategist Rework for bounded loop corrections, (10) Deterministic Optimizer for SciPy SLSQP math, (11) Post-Optimization Critic for rounding validation, (12) Moderator for fiduciary explanations, and (13) Persistence for atomic database commit."
- **Deep Technical Proof & Code Citation**:
  - All 13 nodes are explicitly declared and registered in `backend/agent/graph.py:35-75` and implemented in `backend/agent/nodes.py`.

### Q9: What prevents the Critic and Strategist Rework loop from running into an infinite cycle?
- **Concise Verbal Answer**:
  > "We enforce a strict mathematical invariant: `rework_count < max_rework_count = 2`. The state tracks how many rework cycles have occurred. If the Critic rejects the allocation twice, the rework node terminates the loop and deterministically injects a guaranteed-feasible, diversified candidate basket."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/agent/nodes.py:840-895` (`strategist_rework_node`).
  - Conditional transition logic verified in `backend/agent/graph.py:70-85` (`_route_critic_verdict`).

### Q10: How do the agents communicate with each other?
- **Concise Verbal Answer**:
  > "Agents do not pass arbitrary text strings. They communicate through an immutable, strongly-typed shared state called `PortfolioAgentState` implemented as a Python `TypedDict`. Each node receives the current state, performs its specialized task, and returns a validated dictionary update."
- **Deep Technical Proof & Code Citation**:
  - Defined in `backend/agent/state.py:PortfolioAgentState`.
  - Pydantic contract schemas defined in `backend/agent/schemas.py` (`CriticOutput`, `OptimizerOutput`, `ModeratorOutput`).

### Q11: How do you prevent LLM hallucinations from corrupting portfolio weights?
- **Concise Verbal Answer**:
  > "We strictly prohibit LLMs from calculating or adjusting asset weights. Node 10, the Optimizer, contains zero LLM calls. It is pure Python, NumPy, and SciPy. The LLM only helps identify qualitative factors and candidate tickers; the actual percentage allocations and whole-share counts are computed mathematically by SciPy SLSQP."
- **Deep Technical Proof & Code Citation**:
  - Inspected in `backend/agent/nodes.py:900-1040` (`deterministic_optimizer_node`): uses `optimize_portfolio_allocations` and `calculate_integer_shares_and_amounts`. Zero LLM invocations occur in this node.

### Q12: What happens if the Gemini API goes down or hits a rate limit during generation?
- **Concise Verbal Answer**:
  > "Lucid incorporates comprehensive fallback resilience. If Google Gemini returns an API quota or timeout error, the system automatically catches the exception and switches to a deterministic heuristic fallback engine that scores candidates using stored database fundamentals and generates standard fiduciary explanations."
- **Deep Technical Proof & Code Citation**:
  - Implemented across all LLM node wrappers in `backend/agent/nodes.py` via `try...except (ResourceExhausted, GoogleAPICallError, Exception)` blocks.
  - Tested in `backend/tests/test_llm_resilience.py`.

### Q13: What is the role of the Fiduciary Moderator Node?
- **Concise Verbal Answer**:
  > "The Moderator acts as the client-facing communicator. It translates complex mathematical allocations, factor scores, and macro considerations into transparent, plain-English narratives answering two questions: 'Why this overall portfolio?' and 'Why this specific stock?'."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/agent/nodes.py:1260-1340` (`fiduciary_moderator_node`).
  - Outputs are committed to the `recommendation_explanations` table in PostgreSQL.

### Q14: How are agent execution traces audited?
- **Concise Verbal Answer**:
  > "Every single generation request logs its step-by-step execution trace—including node start/finish timestamps, tool inputs, LLM token counts, Critic verdicts, and optimizer metrics—into the `generation_requests`, `agent_traces`, and `critic_verdicts` tables in PostgreSQL."
- **Deep Technical Proof & Code Citation**:
  - Models declared in `backend/models/agent.py` and saved during Node 13 in `backend/agent/nodes.py:1350-1450`.

---

## Category 3: System Architecture, Database & Security (Q15 – Q20)

### Q15: Why did you choose PostgreSQL 17, and how is the database organized?
- **Concise Verbal Answer**:
  > "PostgreSQL provides ACID transactional guarantees, JSONB support for execution traces, and robust indexing. Our schema consists of 58 normalized tables organized into 8 domains: Identity, Security Master, Portfolio Versions, Market Data, Broker Holdings, Demat Diagnosis, Agent Logs, and Compliance."
- **Deep Technical Proof & Code Citation**:
  - Database schema declared across `backend/models/*.py` and documented in `LUCID_DATABASE_AND_SYSTEM_ARCHITECTURE.md`.

### Q16: How does Lucid enforce multi-tenant isolation?
- **Concise Verbal Answer**:
  > "We enforce composite unique constraints on `(portfolio_id, user_id)` in the `investor_portfolios` table. Every database query for portfolio inspection or mutation includes both the `portfolio_id` and the authenticated `user_id` extracted from the verified JWT token."
- **Deep Technical Proof & Code Citation**:
  - Declared in `backend/models/portfolio.py:52`: `UniqueConstraint('portfolio_id', 'user_id', name='uq_portfolio_id_user')`.
  - Filtered in `backend/api/v1/portfolios.py` across all endpoints via `InvestorPortfolio.user_id == current_user.user_id`.

### Q17: How is user authentication and password security handled?
- **Concise Verbal Answer**:
  > "We use Argon2id via `argon2-cffi` for password hashing, which is memory-hard and GPU-resistant. Sessions are managed through stateless JWT tokens containing the user UUID, with server-side revocation tracking stored in the `revoked_tokens` table."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/api/v1/auth.py` and `backend/models/users.py:RevokedToken`.

### Q18: How does Lucid comply with India's Digital Personal Data Protection (DPDP) Act, 2023?
- **Concise Verbal Answer**:
  > "Lucid implements user data export in JSON format, explicit consent logging in `user_consents`, and a permanent account deletion workflow that cascadingly purges all user records, portfolios, broker snapshots, and audit logs."
- **Deep Technical Proof & Code Citation**:
  - Deletion service implemented in `backend/services/account_deletion_service.py:delete_user_account_permanently`.
  - Tested in `backend/tests/test_deletion_and_data_management.py`.

### Q19: Why are portfolio versions immutable?
- **Concise Verbal Answer**:
  > "In fiduciary finance, auditability is non-negotiable. When an investor rebalances or updates their portfolio, Lucid does not overwrite existing rows. Instead, it increments the version number and creates a new `portfolio_versions` record linked to new decision rows. This maintains an immutable historical audit trail of every recommendation ever made."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/api/v1/portfolios.py:1600-1660` (`apply_rebalance`): increments `next_ver_num = (latest_ver.version_number or 1) + 1` and creates a fresh `PortfolioVersion`.

### Q20: What is the purpose of the 7-section Demat Diagnosis module?
- **Concise Verbal Answer**:
  > "It allows investors to upload existing brokerage statements from other platforms and instantly receive a health score (0–100) and detailed diagnostic breakdown across 7 risk dimensions: single-stock concentration, sector skew, market cap split, dividend yield, valuation, quality, and beta."
- **Deep Technical Proof & Code Citation**:
  - Evaluated in `backend/api/v1/diagnosis.py` and `backend/portfolio_engine/diagnosis_copilot_service.py`.

---

## Category 4: Financial Mathematics & Quantitative Methods (Q21 – Q28)

### Q21: What mathematical formula does the optimizer solve?
- **Concise Verbal Answer**:
  > "It solves Markowitz Mean-Variance Quadratic Utility: $\min_{\mathbf{w}} \frac{1}{2} \lambda \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} - \mathbf{\mu}^T \mathbf{w}$, subject to simplex bounds $\sum w_i = 1$, $0 \le w_i \le 0.25$, and sector bounds $\sum_{i \in \text{Sector}_k} w_i \le 0.40$, using SciPy SLSQP."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/portfolio_engine/optimizer.py:102-180` (`optimize_portfolio_allocations`).

### Q22: What is the risk aversion parameter $\lambda$, and how is it calibrated?
- **Concise Verbal Answer**:
  > "Lambda ($\lambda$) represents the marginal penalty on portfolio variance relative to expected return. A higher lambda prioritizes variance reduction, while a lower lambda prioritizes return. We map lambda dynamically based on investor suitability: 8.0 for Very Conservative, 5.0 for Conservative, 3.0 for Moderate, 1.5 for Aggressive, and 0.8 for Very Aggressive."
- **Deep Technical Proof & Code Citation**:
  - Declared in `backend/portfolio_engine/optimizer.py:25-35` (`RISK_AVERSION_MAP`).

### Q23: How does Lucid calculate the covariance matrix $\mathbf{\Sigma}$?
- **Concise Verbal Answer**:
  > "We calculate annualized historical covariance using 252 trading days of log-returns: $r_t = \ln(P_t / P_{t-1})$. The sample covariance matrix is multiplied by 252 to annualize. Where histories are short, we apply Ledoit-Wolf shrinkage toward the diagonal to prevent ill-conditioned inversion."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/portfolio_engine/optimizer.py:140-170`.

### Q24: How does Lucid convert continuous weights into whole shares without violating constraints?
- **Concise Verbal Answer**:
  > "We use a two-stage floor-and-greedy algorithm. First, we compute the floor integer shares $Q_i = \lfloor w_i \cdot V_{\text{total}} / P_i \rfloor$. Then, we iteratively evaluate the remaining cash: if enough cash exists to buy an additional whole share of the highest-ranked stock without exceeding the 25% single-stock or 40% sector caps, it is added. Any remainder is held as liquid cash."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/portfolio_engine/optimizer.py:220-275` (`calculate_integer_shares_and_amounts`).

### Q25: Can the unallocated cash reserve ever be negative?
- **Concise Verbal Answer**:
  > "Never. The integer rounding algorithm enforces a strict mathematical invariant: $C = V_{\text{total}} - \sum Q_i P_i \ge 0$. Because we floor the base quantities, invested capital is strictly $\le V_{\text{total}}$, guaranteeing non-negative cash."
- **Deep Technical Proof & Code Citation**:
  - Asserted in `backend/portfolio_engine/optimizer.py:265` and audited by `backend/agent/nodes.py:1150-1200` (`critic_final_validation_node`).

### Q26: How does drift detection work, and what are the exact trigger thresholds?
- **Concise Verbal Answer**:
  > "We compute current weights dynamically: $w_i(t) = (Q_i \cdot P_i(t) / V_{\text{total}}(t)) \times 100\%$. A rebalance event is triggered if any single stock drifts by $\ge 5.0\%$ from its target weight, or any sector drifts by $\ge 10.0\%$, or if internal concentration caps (25% stock, 40% sector) are breached."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/portfolio_engine/monitoring_service.py:230-285` (`monitor_native_portfolio`).
  - Constants declared in `backend/portfolio_engine/monitoring_service.py:35-45`.

### Q27: What Indian statutory transaction costs are modeled in the rebalance preview?
- **Concise Verbal Answer**:
  > "We model all statutory Indian equity delivery levies: Securities Transaction Tax (STT) at 0.10% on Buy and Sell, Exchange turnover fees at 0.00325%, SEBI turnover fees at 0.0001% (₹10/crore), Stamp Duty at 0.015% on Buy orders only, and 18% GST on brokerage and exchange charges."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/portfolio_engine/transaction_costs.py:calculate_indian_transaction_costs`.

### Q28: How does the market regime engine classify India VIX?
- **Concise Verbal Answer**:
  > "We query `^INDIAVIX` live. Values below 13 are classified as Calm; 13 to 18 as Moderate; 18 to 24 as Volatile; and above 24 as Extreme. This classification directly commands the agent factor tilts and risk-aversion parameters."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `backend/market_data/regime.py:classify_market_regime`.

---

## Category 5: Practical Application & Frontend UX (Q29 – Q33)

### Q29: What is the user journey from landing page to portfolio creation?
- **Concise Verbal Answer**:
  > "An investor arrives on the landing page, enters their goals in natural language or completes a 6-stage guided wizard specifying capital, horizon, risk tolerance, and exclusions. They click 'Generate My Portfolio', watch the honest multi-stage agent progress bar, and arrive at their interactive dashboard displaying whole shares, cash, and risk health metrics."
- **Deep Technical Proof & Code Citation**:
  - Components orchestrated in `frontend/src/app/page.tsx`, `frontend/src/components/OnboardingWizard.tsx`, and `frontend/src/components/HoldingsView.tsx`.
  - Verified by Playwright in `frontend/e2e/onboarding.spec.ts`.

### Q30: How does the investor execute the rebalancing trades proposed by Lucid?
- **Concise Verbal Answer**:
  > "Under our non-custodial model, Lucid provides a 'Copy Order Slip' button and an 'Export Basket' dropdown generating CSV formats tailored for Zerodha Kite, Groww, and standard broker terminals. The investor reviews the whole-share order slip and places the orders directly through their broker."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `frontend/src/components/RebalancePreviewModal.tsx:49-72` (`handleCopy`) and `backend/api/v1/portfolios.py:1550-1610`.

### Q31: What does the user see in the 'Why This Stock?' modal?
- **Concise Verbal Answer**:
  > "They see four tabs: (1) Fiduciary Factors displaying radar percentiles for Quality, Value, Momentum, and Low Volatility; (2) Official Disclosures with verified BSE/NSE filing links; (3) Financial Health showing 5-year balance sheet trends; and (4) Peer Comparison evaluating industry multiples."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `frontend/src/components/StockWhyModal.tsx`.

### Q32: How is responsive design and accessibility ensured in the frontend?
- **Concise Verbal Answer**:
  > "The frontend is built with Tailwind CSS following mobile-first principles, tested across Desktop (1280x800), Tablet (768x1024), and Mobile (375x667). Modals feature accessible keyboard traps (Escape key dismissal, aria labels), high-contrast text, and zero layout shift."
- **Deep Technical Proof & Code Citation**:
  - Tested across multiple viewports in `frontend/e2e/portfolio_dashboard.spec.ts:220-245`.

### Q33: How does the frontend handle real-time portfolio updates after rebalancing?
- **Concise Verbal Answer**:
  > "When the investor clicks 'Apply Rebalance & Update Portfolio', the modal invokes `POST /api/v1/portfolios/{id}/apply-rebalance`. Upon success, it switches to the 'Updated Portfolio Preview' tab, displays a success confirmation, and calls `onPortfolioUpdated` to refresh the parent dashboard state optimistically without requiring a page reload."
- **Deep Technical Proof & Code Citation**:
  - Implemented in `frontend/src/components/RebalancePreviewModal.tsx:74-95` (`handleApply`) and `frontend/src/app/page.tsx:handlePortfolioUpdated`.

---

## Category 6: Limitations & Future Roadmap (Q34 – Q38)

### Q34: What are the current limitations of the Lucid platform?
- **Concise Verbal Answer**:
  > "First, we do not support intraday or derivative (F&O) trading—we are strictly a medium-to-long-term delivery equity platform. Second, market data relies on daily close bars during off-market hours rather than live Level 2 order book feeds. Third, execution remains non-custodial and manual, requiring the investor to copy trades to their broker."
- **Deep Technical Proof & Code Citation**:
  - Documented in `LUCID_COMPLETE_PROJECT_DOCUMENTATION.md:Section 12`.

### Q35: How do you plan to eliminate manual trade entry in the future?
- **Concise Verbal Answer**:
  > "We plan to integrate official broker OAuth partner APIs—such as Zerodha Kite Connect, Upstox Developer API, and Groww Partner Gateway—allowing users to authorize one-click basket order execution while still retaining full fiduciary consent."
- **Deep Technical Proof & Code Citation**:
  - Architecture prepared in `backend/models/broker.py:BrokerIntegration` and `broker_accounts`.

### Q36: How will automated Demat statement syncing be implemented?
- **Concise Verbal Answer**:
  > "We will integrate with licensed SEBI Account Aggregators (AAs) like Setu or Finvu. Under the RBI/SEBI Account Aggregator framework, users can grant consent to fetch their real-time Demat holdings directly from CDSL/NSDL depositories without manual file uploads."
- **Deep Technical Proof & Code Citation**:
  - Roadmap detailed in `LUCID_COMPLETE_PROJECT_DOCUMENTATION.md:Section 12.2`.

### Q37: Can Lucid be expanded beyond Indian equities to other asset classes?
- **Concise Verbal Answer**:
  > "Yes. The mathematical optimizer and SciPy SLSQP engine are asset-agnostic. By extending the security master to ingest Gold ETF prices, Sovereign Gold Bonds (SGBs), Real Estate Investment Trusts (REITs), and Government G-Secs, the same quadratic programming framework can optimize multi-asset portfolios."
- **Deep Technical Proof & Code Citation**:
  - Supported by `backend/models/security.py:ck_securities_type` which already permits `'stock', 'etf', 'index', 'mutual_fund', 'bond', 'other'`.

### Q38: What has been the most challenging technical hurdle in developing Lucid?
- **Concise Verbal Answer**:
  > "The most challenging hurdle was reconciling theoretical continuous portfolio mathematics with real-world Indian market frictions: eliminating LLM arithmetic hallucinations through the 13-node LangGraph separation, guaranteeing integer whole shares with zero fractional lots and non-negative cash, and ensuring sub-second response times during live market drift audits."
- **Deep Technical Proof & Code Citation**:
  - Solved through the decoupled architecture in `backend/agent/nodes.py` and integer rounding in `backend/portfolio_engine/optimizer.py`.

---
*Lucid Viva Examination Questions & Answers — Version 2026.11-v2.0*

