# Lucid — End-to-End API Data Lineage & Field Transformation Specifications

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** November 8, 2026  
**Target Codebase:** Lucid Intelligent Investment Platform (`/Users/ankur/Documents/MajorProject/app`)

---

## 1. Master Data Lineage Table: From External Provider to Agent Consumption

| External Source / Feed | Raw Ingested Field | Transformation & Normalization Applied | PostgreSQL Destination Table | Target Column & Type | Consuming LangGraph Agent / Node | Final Output Presentation |
|---|---|---|---|---|---|---|
| **NSE `EQUITY_L.csv`** | `SYMBOL` | `.strip().upper()`, stripped of exchange suffixes | `instrument_listings` | `symbol VARCHAR(80)` | All Agents, Candidate Selector | Stock ticker in Holdings & Why modals |
| **NSE `EQUITY_L.csv`** | `NAME OF COMPANY` | Truncated to 240 chars, title-cased | `companies`, `securities` | `legal_name VARCHAR(240)`, `security_name` | All Agents, Explanations | Displayed company name |
| **NSE `EQUITY_L.csv`** | `ISIN NUMBER` | Stripped, validated 12-char regex `^IN[A-Z0-9]{10}$` | `securities` | `isin CHAR(12)` | Candidate Selector, Reconciler | Fiduciary ISIN provenance |
| **NSE `EQUITY_L.csv`** | `SERIES` | Mapped: `EQ`/`BE` $\to$ `active`, `BZ` $\to$ `suspended` | `instrument_listings` | `trading_status VARCHAR(20)` | Candidate Selector | Excludes suspended securities |
| **NSE `EQUITY_L.csv`** | `DATE OF LISTING` | Parsed format `%d-%b-%Y` $\to$ `datetime.date` | `instrument_listings` | `listed_on DATE` | Candidate Selector | Minimum listing age verification |
| **NSE Index Lists** | `Industry` | Mapped via `INDUSTRY_TO_SECTOR_MAP` to 20 sectors | `sectors`, `industries` | `sector_code`, `industry_name` | Lead Strategist, Optimizer, Critic | 40% sector ceiling enforcement |
| **Yahoo Finance** | `Close` / `last_price` | Checked `price > 0.0`, rounded to 2 decimals | `market_prices` | `close_price NUMERIC(14,4)` | Market Analyst, Optimizer | Live share price, trade preview |
| **Yahoo Finance** | `Volume` | Summed over 30 days $\to$ `func.avg(volume)` | `market_prices` | `volume BIGINT` | Candidate Selector, Risk Critic | ADTV $\ge 10,000$ shares liquidity check |
| **Yahoo Finance** | Daily Returns | Historical price series $\to$ Covariance Matrix $\mathbf{\Sigma}$ | In-Memory Matrix | Covariance float matrix | Deterministic Optimizer Node | Portfolio volatility $\sigma_p$ minimization |
| **Yahoo Finance** | `trailingPE` | Checked $\ge 1.0$, capped at 150.0 | `fundamental_metrics` | `metric_value NUMERIC(18,6)` | Fundamental Analyst, Critic | P/E benchmark corridor evaluation |
| **Yahoo Finance** | `returnOnEquity` | Normalized decimal float (e.g. 0.284 = 28.4%) | `fundamental_metrics` | `metric_value NUMERIC(18,6)` | Fundamental Analyst | ROE $> 18\%$ quality filter |
| **Yahoo Finance** | `dividendYield` | Normalized decimal (e.g. 0.015 = 1.5%) | `fundamental_metrics` | `metric_value NUMERIC(18,6)` | Strategist, Optimizer | Dividend income factor tilt |
| **Yahoo Finance** | `^INDIAVIX` | FastInfo / daily close $\to$ Volatility categorization | `economic_observations` | `observation_value NUMERIC(18,6)` | Macro Analyst Agent | Regime: `CALM`, `MODERATE`, `VOLATILE` |
| **Yahoo Finance** | `^NSEI` | Close vs 50-DMA and 200-DMA $\to$ Trend slope | `economic_observations` | `observation_value NUMERIC(18,6)` | Market Analyst Agent | Trend: `UPTREND`, `DOWNTREND` |
| **RBI Official MPC** | Policy Repo Rate | Parsed as percentage (6.50%) | `economic_observations` | `observation_value NUMERIC(18,6)` | Macro Analyst Agent | Positive real policy rate assessment |
| **MOSPI Official** | Headline CPI | Parsed as percentage (5.10%) | `economic_observations` | `observation_value NUMERIC(18,6)` | Macro Analyst Agent | Inflation corridor assessment |
| **BSE / NSE Disclosures** | Corporate Announcements | Verified URL synthesis via `exchange_registry.py` | In-Memory Evidence | `verified_exchange_filings` | News Analyst Agent, Why Modal | 100% verified 200 OK links |
| **Investor Input** | Investment Amount | Validated `amount >= 10,000 INR` | `investor_portfolios` | `target_total_investment` | Lead Strategist, Optimizer | Scaled whole-share lot allocation |
| **Investor Input** | Risk Questionnaire | Weighted scoring (1.0 to 5.0) $\to$ Category | `risk_assessments` | `risk_category VARCHAR(30)` | Suitability Node, Optimizer | Risk aversion parameter $\lambda$ |
| **Investor Input** | Negative Exclusions | Parsed sector and ticker strings $\to$ Exclusion Set | `user_sector_preferences` | `preference_type = 'exclude'` | Candidate Selector, Critic | Hard elimination from asset pool |

---

## 2. Field-by-Field Detailed Transformations

### 2.1 Symbol Normalization
- **Original Source Data:** `SYMBOL` in `EQUITY_L.csv` (e.g., `RELIANCE   `, `TCS.NS`, `bse:500325`).
- **Transformation Pipeline:**
  ```python
  clean = symbol.strip().upper()
  if clean.endswith(".NS") or clean.endswith(".BO"):
      clean = clean[:-3]
  ```
- **Resulting Data:** Canonical uppercase symbol without exchange suffixes (e.g. `RELIANCE`, `TCS`).
- **Destination:** `InstrumentListing.symbol`.

### 2.2 ISIN Reconciliation & Corporate Actions
- **Original Source Data:** `ISIN NUMBER` in `EQUITY_L.csv`.
- **Validation:** Enforces 12-character alphanumeric code starting with `IN` (NSDL/CDSL standard).
- **Split Handling:** When a stock split occurs, the company symbol remains identical, but the ISIN changes (e.g., Bajaj Finance transitioned from `INE296A01024` to `INE296A01032`).
- **Transformation:**
  ```python
  existing_listing = existing_listings.get(symbol)
  sec_obj = existing_listing.security if existing_listing else existing_securities_isin.get(isin)
  if sec_obj and sec_obj.isin != isin:
      sec_obj.isin = isin  # Updates canonical ISIN without breaking existing security_id foreign keys
  ```
- **Destination:** `Security.isin`.

### 2.3 Financial Ratio Normalization
- **Return on Equity (ROE):**
  - Source: `yf.Ticker.info['returnOnEquity']`.
  - Transformation: Converted to decimal float. If $>1.0$ (e.g. 28.4), divided by 100 to yield `0.284`.
  - Fallback: Defaults to $0.16$ (long-term Indian corporate average) if missing, flagged with limitation note.
- **Price-to-Earnings (P/E):**
  - Source: `yf.Ticker.info['trailingPE']` or `forwardPE`.
  - Transformation: $\text{PE} = \max(1.0, \min(150.0, \text{pe}))$. Negative P/E (loss-making enterprises) is replaced by forward P/E or flagged as high-risk.
- **Dividend Yield:**
  - Source: `yf.Ticker.info['dividendYield']`.
  - Transformation: If `raw > 0.5`, divided by 100 (e.g. $1.5\% \to 0.015$).

---

## 3. Data Completeness vs. Summarization Architecture

A critical architectural principle of Lucid is that **raw API responses are never passed directly to LLM prompts**. Passing raw JSON blobs wastes token budgets, causes latency, and introduces prompt injection vulnerabilities.

Instead, Lucid implements a **5-tier progressive data refinement architecture**:

```text
[Tier 1: Raw External Data]
   Full Yahoo Finance info dict (~200 fields) & NSE CSVs (~10 fields)
                     │
                     ▼ [Extraction & Normalization]
[Tier 2: Relational PostgreSQL Storage]
   Clean, typed tables (62 tables, 565 columns)
                     │
                     ▼ [Candidate Selection & Slicing]
[Tier 3: LangGraph Shared State (PortfolioAgentState)]
   Specialist Pydantic schemas (MetricEvidenceRecord, EvidenceItem)
                     │
                     ▼ [Context Slicing & Prompt Injection]
[Tier 4: Agent-Specific LLM Prompt]
   Concise fiduciary facts (5-8 lines of verified metrics per stock)
                     │
                     ▼ [Deterministic Mathematical Execution]
[Tier 5: Final Recommendation Output]
   Exact integer share counts, portfolio weights, and fiduciary explanations
```

### Truncation & Lookback Boundaries
- **Historical Price Lookback:** Constrained to **35 calendar days** (approx. 25 trading sessions) for liquidity ADTV calculation and **252 trading sessions (1 year)** for covariance optimization.
- **Candidate Pool Slicing:** Dynamically evaluated across the full **2,639 securities** universe by the Candidate Selector (yielding up to 2,605 eligible liquid stocks), and further distilled to **8–15 top candidates** by the Lead Strategist before optimization.
- **News Announcements Lookback:** Truncated to the **latest 5 verified announcements** within the past 90 days.
