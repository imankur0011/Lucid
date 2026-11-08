# Lucid — Complete Data Pipeline, Dataset Inventory & Agent Data-Lineage Architecture

**Document Title:** Intelligent Investment Portfolio Creation, Analysis and Rebalancing Platform — Comprehensive Dataset & Data-Pipeline Technical Architecture  
**Document Version:** 2026.11-v2.0  
**Authoritative Date:** November 8, 2026  
**Platform Scope:** Indian Equities (National Stock Exchange & Bombay Stock Exchange)  
**Target Codebase:** `/Users/ankur/Documents/MajorProject/app`

---

## 1. Executive Summary — What Data Lucid Uses

**Lucid** is an intelligent wealth advisory and portfolio optimization platform built specifically for Indian retail investors. Lucid bridges the gap between raw, overwhelming financial data and actionable, fiduciary-compliant investment decisions.

To construct, monitor, and rebalance personalized equity portfolios, Lucid ingests, processes, and evaluates data across **five primary financial domains**:

1. **Broad Exchange Security Master Data:** Comprehensive company master records, ISIN identifiers, exchange listings, corporate taxonomy (sectors & industries), and trading series (`EQ`, `BE`, `BZ`) spanning **2,639 listed Indian equities** from the National Stock Exchange of India (NSE) and Bombay Stock Exchange (BSE).
2. **Quantitative Market Data:** Daily Open-High-Low-Close-Volume (OHLCV) historical bars, adjusted close price series, trading turnover, 30-day Average Daily Traded Volume (ADTV), and real-time market quotes retrieved via Yahoo Finance (`yfinance`).
3. **Fundamental Company Accounting Data:** Audited balance sheet, income statement, and valuation metrics, including Return on Equity (ROE), Price-to-Earnings (P/E), Price-to-Book (P/B), Debt-to-Equity (D/E), Dividend Yield, Beta, and Market Capitalization.
4. **Macroeconomic & Regulatory Indicators:** Real-time India Volatility Index (`^INDIAVIX`), Nifty 50 directional trends (50-DMA and 200-DMA moving-average slopes), Reserve Bank of India (RBI) Monetary Policy Committee Repo Rates ($6.50\%$), CPI Inflation ($5.10\%$), Real GDP Growth ($7.20\%$), and 10-Year Sovereign G-Sec Yields ($7.04\%$).
5. **Corporate Filings & Governance Disclosures:** Verified exchange announcement URLs and regulatory registries from NSE, BSE, SEBI SCORES 2.0, and SMART ODR to audit management pledges, corporate actions, and forensic accounting flags.

### The Core Architectural Pipeline

$$\text{External APIs / Feeds} \longrightarrow \text{Extraction \& Normalization} \longrightarrow \text{PostgreSQL Storage (62 Tables)} \longrightarrow \text{Candidate Selection Funnel} \longrightarrow \text{LangGraph Multi-Agent Committee} \longrightarrow \text{Deterministic SLSQP Optimizer} \longrightarrow \text{Explainable Retail Portfolio}$$

---

## 2. Complete External API Inventory

Lucid interacts with **four distinct external data providers and archival sources**:

| Provider Name | Exact Endpoint / Resource Identifier | Request Method | Auth Required | Data Retrieved | Fetch Frequency | Consuming Component |
|---|---|:---:|:---:|---|---|---|
| **NSE Official Archive (Full Equities)** | `https://archives.nseindia.com/content/equities/EQUITY_L.csv` | HTTP GET | None (Public) | Complete master of all 2,632 listed equities, symbols, company names, series, ISINs, listing dates | Daily / On-Demand | `exchange_universe_sync.py`, PostgreSQL Security Master |
| **NSE Official Archive (Benchmark Index)** | `https://archives.nseindia.com/content/indices/ind_nifty500list.csv` | HTTP GET | None (Public) | 501 Nifty 500 index constituents with official industry taxonomy | Daily / On-Demand | `exchange_universe_sync.py`, Benchmark Universe |
| **NSE Official Archive (Total Market)** | `https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv` | HTTP GET | None (Public) | 754 top equities with sector and industry classifications | On-Demand | `exchange_universe_sync.py`, Taxonomy Mapper |
| **Yahoo Finance (`yfinance`)** | `https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.NS` | Python SDK / GET | None (Public) | Daily OHLCV price bars (1 month to 5 years), Adjusted Close, Volume | On-Demand / Daily | `adapter.py`, `MarketDataProvider`, Optimizer |
| **Yahoo Finance (`yfinance`)** | FastInfo & Info Dictionaries | Python SDK / GET | None (Public) | Live market quotes, ROE, P/E, P/B, D/E, Dividend Yield, Market Cap, Beta | Live / Cached in DB 7 days | `monitoring_service.py`, `fundamental_research_tool` |
| **Yahoo Finance (India VIX)** | Ticker `^INDIAVIX` via `yfinance` | Python SDK / GET | None (Public) | Real-time Indian equity market volatility level | On-Demand / Cached 24h | `regime.py`, Macro Analyst Agent |
| **Yahoo Finance (Nifty 50)** | Ticker `^NSEI` via `yfinance` | Python SDK / GET | None (Public) | 50-DMA, 200-DMA, and 20-day return slope | On-Demand / Cached 24h | `regime.py`, Market Analyst Agent |
| **Google Gemini API** | `gemini-3.8-flash` via LangChain (`langchain-google-genai`) | HTTPS POST | `GEMINI_API_KEY` | Qualitative fiduciary reasoning, news analysis, risk criticism, explanations | Per portfolio creation & user query | LangGraph Specialist Agents, Fiduciary Moderator |
| **RBI & MOSPI Releases** | Official MPC resolutions (`https://www.rbi.org.in`) | Database Seed / GET | None (Official) | Repo Rate (6.50%), CPI (5.10%), GDP (7.20%), 10Y Yield (7.04%) | Bi-monthly MPC updates | `regime.py`, Macro Analyst Agent |
| **NSE Corporate Filings** | `https://www.nseindia.com/companies-listing/corporate-filings-announcements` | HTTPS URL Link | Browser Session | Verified company exchange filings and corporate actions | Real-time on link click | `exchange_registry.py`, Stock Why Modal |
| **BSE Corporate Filings** | `https://www.bseindia.com/stock-share-price/{sym}/{bse_code}/corp-announcements/` | HTTPS URL Link | Browser Session | Verified BSE corporate announcements for dual-listed equities | Real-time on link click | `exchange_registry.py`, Stock Why Modal |

---

## 3. NSE/BSE Security Universe: The 504-Record Investigation

When inspecting the PostgreSQL database prior to this audit, queries returned:
- `db.query(Security).count()` $\to$ **504**
- `db.query(Company).count()` $\to$ **504**
- `db.query(InstrumentListing).count()` $\to$ **580** (505 NSE, 72 BSE, 3 DEMOEX)

### Why 504 Records Existed:
The exact origin of the 504 records was traced line-by-line:
1. **501 Records from Nifty 500 (`ind_nifty500list.csv`):**
   - In [`backend/market_data/exchange_universe_sync.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py), the function `sync_nifty500_universe(db)` fetched `NIFTY_500_URL` (`https://archives.nseindia.com/content/indices/ind_nifty500list.csv`).
   - This official CSV contains exactly 501 rows (500 companies plus dual-class shares such as Tata Motors Ordinary vs DVR).
   - Each row was converted into a `Company`, a `Security`, and an `InstrumentListing` on the National Stock Exchange (NSE).
2. **3 Records from Test / Migration Fixtures:**
   - Seed scripts and test migrations inserted 3 mock test equities on the fictional exchange `DEMOEX`:
     - `Fictional Consumer Equity` (`ZZ0000000001`)
     - `Fictional Technology Equity` (`ZZ0000000002`)
     - `Fictional Healthcare Equity` (`ZZ0000000003`)
3. **Total:** $501 + 3 = \mathbf{504}$ distinct companies and securities!
4. **72 BSE Listings:**
   - The function `ensure_bse_exchange_and_listings(db)` iterated over a static dictionary of 72 liquid blue-chip equities (`VERIFIED_STOCKS` in `backend/services/exchange_registry.py`), attaching BSE scrip codes (`500325` for Reliance, `532540` for TCS) as secondary listings under the same `Security` entity.

### Terminology Distinction in Indian Market Structure
To ensure legal and financial accuracy, Lucid strictly distinguishes between these six concepts:
1. **Company (`companies` table):** The underlying legal corporate enterprise (e.g. *Reliance Industries Limited*).
2. **Security (`securities` table):** The fungible financial equity asset issued by the company, uniquely identified by a SEBI-mandated 12-character ISIN (`INE002A01018`).
3. **Exchange Listing (`instrument_listings` table):** The specific trading listing of a security on a regulated exchange platform. A single company and security may have multiple listings (e.g., Symbol `RELIANCE` on NSE and Scrip `500325` on BSE).
4. **Trading Symbol:** The alphanumeric exchange ticker assigned by the exchange (e.g. `INFY` on NSE, `500209` on BSE).
5. **ISIN (International Securities Identification Number):** The definitive universal identifier assigned by NSDL/CDSL that connects across exchanges.
6. **Eligible Recommendation Candidate:** A security that belongs to the security master, has an active trading status, possesses price observations $\le 14$ days old, and passes hard retail liquidity thresholds (ADTV $\ge 10,000$ shares and turnover $\ge ₹25$ Lakhs).

---

## 4. Root-Cause Analysis and Fix Implemented

### Root Cause
In [`backend/market_data/exchange_universe_sync.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py#L53):
```python
NSE_FULL_EQUITIES_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
```
The URL constant pointing to the official NSE equity master list was defined in the source code, but **no function in the application ever invoked it**. The application was restricted to the 501 Nifty 500 stocks because only `sync_nifty500_universe()` was implemented and scheduled.

Furthermore, during synchronization dry-runs, a corporate action split issue was discovered: five stocks (`BAJFINANCE`, `DRREDDY`, `HAL`, `KOTAKBANK`, `PERSISTENT`) had older pre-split ISINs in initial seed fixtures (e.g., Bajaj Finance was seeded with `INE296A01024`, whereas the current active exchange ISIN is `INE296A01032`). A naive insertion by ISIN attempted to insert duplicate listings for `BAJFINANCE`, triggering the unique database constraint `uq_listing_exchange_symbol`.

### Architectural Fix Implemented
1. **Full Equity Master Synchronization (`sync_nse_equity_master`):**
   - Implemented in `exchange_universe_sync.py` to ingest `EQUITY_L.csv` (2,632 equities) directly from official NSE archives.
   - Merges industry classifications from `ind_niftytotalmarket_list.csv` (754 stocks) and `ind_niftymicrocap250_list.csv` (253 stocks).
   - Reconciles by **both Symbol and ISIN**:
     - If the symbol already exists on NSE, it matches the existing `Security` entity, updates its ISIN to the current exchange record, and updates the legal name, preserving all foreign keys, historical prices, and portfolio decisions.
     - If the ISIN exists, it reuses the security.
     - If neither exists, it creates new `Company`, `CompanyIndustry`, `Security`, and `InstrumentListing` records.
   - Commits safely in transaction batches of 200 records.
2. **Master Orchestrator (`sync_full_exchange_universe`):**
   - Executes Nifty 500 benchmark sync, full NSE equity master sync, BSE verified scrip linking, and relational reconciliation in one unified, idempotent call.
3. **Database Audit & Verification:**
   - Upgraded `reconcile_universe_against_exchanges(db)` to compute exact live counts across all tables and evaluate candidate liquidity filtering.

### Post-Fix Database Reconciliation Results
- **Total Companies in PostgreSQL:** **2,639** (up from 504, **+423%**)
- **Total Securities in PostgreSQL:** **2,639** (up from 504, **+423%**)
- **Total Exchange Listings:** **2,715** (NSE: 2,640, BSE: 72, DEMOEX: 3)
- **Active NSE Listings:** **2,606** (Series EQ + BE)
- **Suspended / Non-Compliant Listings:** **34** (Series BZ)
- **Unique ISINs:** **2,639** (100% unique)
- **Valid SEBI ISIN Rate:** **99.85%** (2,635 / 2,639)
- **Eligible Recommendation Candidates:** **504**
- **Excluded Retained Securities:** **2,135** (Preserved in DB for search & demat diagnosis)

---

## 5. NSE/BSE Data Sources and Synchronization

```text
                  Official National Stock Exchange (NSE) Archives
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
  EQUITY_L.csv                 ind_nifty500list.csv            ind_niftytotalmarket.csv
(2,632 Equities)                (501 Benchmark)                     (754 Equities)
        │                                │                                │
        └────────────────────────────────┬────────────────────────────────┘
                                         ▼
                 HTTP Fetch & Field Normalization Pipeline
                                         │
                                         ▼
                 Symbol & ISIN Cross-Reconciliation Engine
                                         │
                                         ▼
                 PostgreSQL Relational Master (62 Tables)
                    ├── companies (2,639 Enterprises)
                    ├── securities (2,639 Equities)
                    └── instrument_listings (2,715 Listings)
                                         │
                                         ▼
                 Fiduciary Candidate Selection Funnel
                    ├── ADTV >= 10,000 shares/day
                    ├── Daily Turnover >= ₹25 Lakhs
                    └── Price Freshness <= 14 days
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
       Eligible Recommendation Candidates       Excluded Retained Master
              (~504 Benchmark Stocks)             (2,135 Microcap Stocks)
```

---

## 6. API Request Details

### 6.1 NSE Bulk Master Downloads
- **URL:** `https://archives.nseindia.com/content/equities/EQUITY_L.csv`
- **Method:** `GET`
- **Headers:** `{"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}`
- **Timeout:** 15 seconds.
- **Retry Policy:** 3 retries with exponential backoff (1s, 2s, 4s).

### 6.2 Yahoo Finance Historical Prices (`yfinance`)
- **Ticker Call:** `yf.Ticker(f"{symbol}.NS")`
- **Method Call:** `ticker.history(start="2025-10-01", end="2026-11-05", interval="1d", auto_adjust=False)`
- **Parameters:** `interval="1d"`, `auto_adjust=False` to preserve unadjusted close for exact trade matching and dividend tracking.

### 6.3 Google Gemini Invocation
- **SDK Call:** `ChatGoogleGenerativeAI(model="gemini-3.8-flash", temperature=0.1, max_tokens=2048)`
- **Invocation:** `llm.invoke([SystemMessage(...), HumanMessage(...)])`
- **Payload:** Structured markdown bullet points summarizing verified financial evidence.

---

## 7. API Response Structures

### 7.1 Sample Raw Row from NSE `EQUITY_L.csv`
```csv
SYMBOL,NAME OF COMPANY, SERIES, DATE OF LISTING, PAID UP VALUE, MARKET LOT, ISIN NUMBER, FACE VALUE
RELIANCE,Reliance Industries Limited,EQ,29-NOV-1995,10,1,INE002A01018,10
TCS,Tata Consultancy Services Limited,EQ,25-AUG-2004,1,1,INE467B01029,1
```

### 7.2 Sample Yahoo Finance Quote Summary Response (`fast_info`)
```json
{
  "symbol": "TCS.NS",
  "last_price": 3906.16,
  "open": 3890.00,
  "day_high": 3925.50,
  "day_low": 3878.10,
  "last_volume": 1425890,
  "currency": "INR",
  "market_cap": 14138000000000.0
}
```

---

## 8. Complete Field-Level Extraction Inventory

| Raw API Field | Extracted by Lucid? | Stored in PostgreSQL? | Passed to Agents? | Destination Column & Usage |
|---|:---:|:---:|:---:|---|
| `SYMBOL` | ✅ Yes | ✅ Yes | ✅ Yes | `instrument_listings.symbol` (Trading ticker) |
| `NAME OF COMPANY` | ✅ Yes | ✅ Yes | ✅ Yes | `companies.legal_name`, `securities.security_name` |
| `ISIN NUMBER` | ✅ Yes | ✅ Yes | ✅ Yes | `securities.isin` (Fiduciary identifier) |
| ` SERIES` | ✅ Yes | ✅ Yes | ❌ No | Mapped to `trading_status` (`EQ`/`BE` = active) |
| ` DATE OF LISTING` | ✅ Yes | ✅ Yes | ❌ No | `instrument_listings.listed_on` (Listing age) |
| ` PAID UP VALUE` | ❌ No | ❌ No | ❌ No | Discarded (Not used in mean-variance math) |
| ` MARKET LOT` | ❌ No | ❌ No | ❌ No | Discarded (Indian equity market lot is 1 share) |
| ` FACE VALUE` | ❌ No | ❌ No | ❌ No | Discarded (Not used in portfolio weights) |
| `trailingPE` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `PE`) |
| `returnOnEquity` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `ROE`) |
| `priceToBook` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `PB`) |
| `debtToEquity` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `DEBT_TO_EQUITY`) |
| `dividendYield` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `DIVIDEND_YIELD`) |
| `beta` | ✅ Yes | ✅ Yes | ✅ Yes | `fundamental_metrics` (Metric code: `BETA`) |
| `last_price` | ✅ Yes | ✅ Yes | ✅ Yes | `market_prices.close_price` (Valuation & trade sizing) |
| `volume` | ✅ Yes | ✅ Yes | ✅ Yes | `market_prices.volume` (ADTV liquidity calculation) |
| `^INDIAVIX` Close | ✅ Yes | ✅ Yes | ✅ Yes | `economic_observations` (Market regime classification) |

---

## 9. Data Transformation and Normalization

1. **Symbol Cleaning:** Removes leading/trailing whitespace, converts to uppercase, strips `.NS` and `.BO` suffixes.
2. **ISIN Validation:** Validates exact 12-character format starting with `IN`. Reconciles corporate action splits.
3. **Date Parsing:** Converts exchange dates (`%d-%b-%Y`, e.g. `06-OCT-2008`) to standard ISO `YYYY-MM-DD` SQL dates.
4. **Percentage Scaling:** Financial ratios from Yahoo Finance are standardized: if dividend yield is returned as $1.5\%$, it is normalized to $0.015$; if ROE is returned as $28.4\%$, it is normalized to $0.284$.
5. **Taxonomy Normalization:** Maps 20 NSE industry sectors into standardized macroeconomic sectors via [`INDUSTRY_TO_SECTOR_MAP`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py#L56).

---

## 10. Database Tables and Data Lineage

Lucid structures its persistent schema across **62 relational tables in 8 functional domains**:

```text
Domain 1: User Identity & Security (7 Tables)
  app_users, user_credentials, user_sessions, api_tokens, audit_logs, role_permissions, security_audit_events

Domain 2: Investor Suitability & Goals (5 Tables)
  investor_profiles, risk_questionnaires, risk_assessments, investor_goals, user_sector_preferences

Domain 3: Security Master & Taxonomy (9 Tables)
  companies, securities, instrument_listings, exchanges, sectors, industries, company_industries,
  index_definitions, corporate_actions

Domain 4: Market Data & Fundamentals (11 Tables)
  market_prices, daily_metrics, company_financials, fundamental_metrics, metric_definitions,
  equity_factors, factor_observations, economic_indicators, economic_observations,
  corporate_filings, market_news_sentiment

Domain 5: Portfolio Engine & Optimization (13 Tables)
  investor_portfolios, portfolio_versions, portfolio_security_decisions, portfolio_explanations,
  portfolio_factor_exposures, portfolio_optimization_runs, portfolio_policy_constraints,
  portfolio_risk_criticisms, portfolio_backtest_runs, backtest_daily_metrics,
  portfolio_stress_tests, stress_scenario_results, portfolio_comparison_analyses

Domain 6: Broker Accounts & Auditing (6 Tables)
  broker_connections, broker_orders, broker_executions, broker_holdings_snapshots,
  broker_sync_logs, portfolio_performance_snapshots

Domain 7: Demat Diagnosis & Rebalancing (4 Tables)
  existing_portfolios, existing_portfolio_holdings, portfolio_health_diagnoses,
  portfolio_rebalancing_proposals

Domain 8: Operations & Telemetry (7 Tables)
  agent_execution_logs, agent_node_traces, notifications, research_evidence_store,
  fiduciary_audit_records, system_health_checks, system_configurations
```

---

## 11. Market Data Used

- **Daily OHLCV:** Stored in `market_prices`. Granularity: 1 day. Lookback: 35 days for liquidity checks, 252 days (1 year) for covariance matrix calculation.
- **Live Reference Price ($P_i$):** Used to compute integer lots: $Q_i = \lfloor (V_{\text{portfolio}} \times w_i) / P_i \rfloor$.
- **30-Day Average Daily Traded Volume (ADTV):** Computed via `func.avg(MarketPrice.volume)` over the past 35 calendar days. Must be $\ge 10,000$ shares.
- **Daily Turnover:** $\text{Turnover} = \text{ADTV} \times P_i$. Must be $\ge ₹25\text{ Lakhs}$ ($₹2,500,000$).
- **India VIX (`^INDIAVIX`):** Volatility thresholding:
  - $\text{VIX} < 15$: `CALM` / `LOW`
  - $15 \le \text{VIX} < 22$: `MODERATE`
  - $22 \le \text{VIX} < 28$: `VOLATILE`
  - $\text{VIX} \ge 28$: `EXTREME`
- **Nifty 50 Trend (`^NSEI`):** Evaluates 50-day DMA vs 200-day DMA and 20-day return slope (`UPTREND`, `DOWNTREND`, `SIDEWAYS`).

---

## 12. Fundamental Data Used

Stored in `fundamental_metrics` with `metric_definition_id`:

| Metric Code | Metric Name | Source Field | Fiduciary Benchmark Corridor | Purpose / Consumer |
|---|---|---|:---:|---|
| **`ROE`** | Return on Equity | `returnOnEquity` | $> 15.0\%$ (Preferred $> 18.0\%$) | Quality factor; Fundamental Analyst |
| **`PE`** | Price to Earnings | `trailingPE` | Industry median $\pm 25\%$ | Valuation corridor; Fundamental Analyst |
| **`PB`** | Price to Book | `priceToBook` | $1.0$ to $15.0$ | Valuation check; Fundamental Analyst |
| **`DEBT_TO_EQUITY`**| Debt to Equity | `debtToEquity` | $< 1.0$ (Strictly $< 1.5$) | Solvency audit; Risk Critic |
| **`DIVIDEND_YIELD`** | Dividend Yield | `dividendYield` | $> 0.0\%$ | Income factor tilt; Strategist |
| **`BETA`** | Beta vs Benchmark | `beta` | $0.6$ to $1.2$ | Systematic risk scaling; Optimizer |
| **`MARKET_CAP`** | Market Capitalization | `marketCap` | Large-cap $> ₹50,000\text{ Cr}$ | Size factor; Risk Critic |

---

## 13. Macroeconomic Data Used

Stored in `economic_observations`:
- **RBI Repo Rate ($6.50\%$):** Signals monetary stance (neutral vs tightening).
- **CPI Inflation ($5.10\%$):** Headline consumer inflation in India.
- **Real Policy Rate ($+1.40\%$):** $\text{Repo Rate} - \text{CPI Inflation} = 6.50\% - 5.10\% = +1.40\%$. Positive real rate confirms disciplined macro conditions.
- **10-Year Sovereign G-Sec Yield ($7.04\%$):** Risk-free benchmark rate ($R_f$) used in Sharpe ratio calculations:

$$\text{Sharpe Ratio} = \frac{R_p - R_f}{\sigma_p}$$

- **Real GDP Growth ($7.20\%$):** Underpins domestic corporate revenue projections.

---

## 14. News and Corporate Filing Data Used

- **Verified Corporate Filings:** Generated via [`resolve_stock_filings()`](file:///Users/ankur/Documents/MajorProject/app/backend/services/exchange_registry.py#L190). Links point directly to canonical NSE announcement portals or BSE corporate disclosures.
- **Governance Audit Flags:** Evaluates board independence, promoter share pledges ($< 5\%$ threshold), auditor qualifications, and regulatory circulars.
- **News Sentiment Score:** Normalizes financial news sentiment on a $-1.0$ to $+1.0$ scale to adjust factor ranking weights.

---

## 15. User and Portfolio Data Used

Generated from the retail investor onboarding questionnaire and stored in `investor_profiles` and `risk_assessments`:
- **Risk Capacity & Tolerance:** Weighted score ($1.0$ to $5.0$) categorizing the investor as `VERY_CONSERVATIVE`, `CONSERVATIVE`, `MODERATE`, `GROWTH`, or `AGGRESSIVE`.
- **Target Capital:** Investment amount in INR (minimum ₹10,000).
- **Time Horizon:** Investment duration in months (e.g. 60 months).
- **Negative Sector Constraints:** Sectors explicitly excluded by the investor (e.g., *Alcoholic Beverages*, *Tobacco*, *Defense*).
- **Negative Stock Exclusions:** Specific ticker symbols banned by the investor.

---

## 16. Exact Data Passed to Each Agent

1. **Manager Node:** Receives user profile, investment capital, and request ID. Initializes execution trace.
2. **Suitability Node:** Receives risk score, investment horizon, and capital. Queries `CandidateUniverseSelector` to verify minimum 3 sectors and 5 eligible candidates.
3. **Macro Analyst Node:** Receives India VIX level, Nifty 50 trend, RBI Repo Rate, and CPI inflation. Outputs `MacroAnalystOutput` with market regime and recommended cash buffer ($2.5\% - 8.0\%$).
4. **Market Analyst Node:** Receives 50-DMA and 200-DMA moving averages, market breadth, and sector momentum.
5. **Fundamental Analyst Node:** Receives ROE, P/E, P/B, Debt/Equity, and operating cash flows for all candidate stocks.
6. **News Analyst Node:** Receives corporate filings URLs, disclosure histories, and promoter pledge flags.
7. **Lead Strategist Node:** Receives syntheses from all 4 research agents. Selects the top 8–15 assets and sets target factor weights.
8. **Independent Risk Critic Node:** Receives proposed assets and weights. Audits against single-stock concentration ceiling ($\le 25.0\%$) and sector cap ($\le 40.0\%$).
9. **Strategist Bounded Rework Node:** Receives critic failure instructions. Replaces criticized assets (maximum 2 rework loops).
10. **Deterministic Optimizer Node:** Receives top vetted assets and historical returns. **Runs strictly deterministic SciPy SLSQP optimization with zero LLM intervention.**
11. **Critic Final Allocation Validation Node:** Audits post-optimization allocations: verifies integer whole shares, exact cash conservation, and boundary ceilings.
12. **Fiduciary Moderator Node:** Receives optimized allocations and research evidence. Generates plain-English portfolio-level and stock-level explanations.
13. **Persistence Node:** Writes complete portfolio version, decisions, and execution traces to PostgreSQL within an ACID transaction.

---

## 17. Agent Input JSON Examples

### Fundamental Analyst Input Payload
```json
{
  "symbol": "INFY",
  "company_name": "Infosys Limited",
  "sector": "Information Technology",
  "metrics": {
    "return_on_equity": 0.318,
    "trailing_pe": 27.2,
    "price_to_book": 8.4,
    "debt_to_equity": 0.08,
    "dividend_yield": 0.021,
    "beta": 0.82,
    "adtv_shares": 4820000,
    "daily_turnover_inr": 890000000.0
  },
  "fiduciary_thresholds": {
    "min_roe": 0.18,
    "max_debt_to_equity": 1.0,
    "max_single_stock_cap": 0.25
  }
}
```

---

## 18. LLM Prompt Construction and Context Trimming

- **Prompt Prefix:** Enforces strict SEBI RIA fiduciary identity, objective tone, and zero hallucination.
- **Context Trimming:** Raw JSON objects are transformed into concise 5-line markdown bullet points.
- **Token Budget:** Prompts are capped at 1,500 input tokens; responses are limited to 1,024 output tokens.
- **Temperature:** Set to `0.1` for maximum reproducibility and adherence to factual context.

---

## 19. Data Completeness Versus Summarization

- **Complete Data (Storage Layer):** The PostgreSQL database maintains the complete, lossless representation: 2,639 companies, full price histories, and all audited metrics.
- **Summarized Data (Agent Layer):** Specialists receive distilled evidence records (`MetricEvidenceRecord`) containing only relevant metrics and limitations.
- **Truncated Data (Prompt Layer):** LLM prompts receive top-K candidates (8–15 assets) and the latest 5 corporate announcements to eliminate context clutter.

---

## 20. Data Freshness and Validation

- **Price Freshness:** Rejects any quote older than **14 calendar days** (`max_stale_days=14`).
- **Fundamental Freshness:** Caches balance sheet metrics for **7 calendar days** (`max_stale_days=7`).
- **Missing Value Handling:** If a metric is missing, the system applies conservative fiduciary defaults (e.g. median industry P/E) and records a limitation note (`DataQualityStatus.FALLBACK_ASSUMPTION`).
- **Fail-Closed Rule:** If fewer than 5 eligible securities or fewer than 3 sectors satisfy suitability, the pipeline halts immediately with status `DATA_INSUFFICIENT` rather than recommending an under-diversified portfolio.

---

## 21. API Failure and Fallback Behavior

```text
External Provider Failure (HTTP 500 / 429 / Timeout)
                         │
                         ▼
             Circuit Breaker Activates
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
[Market Data Offline]              [LLM API Offline]
Query latest valid cached          Switch to deterministic
PostgreSQL quote (`market_prices`) rule engine (`fiduciary-rule-engine-v2`)
        │                                 │
        ▼                                 ▼
Log FALLBACK_ASSUMPTION            Log HEURISTIC_FALLBACK
in MetricEvidenceRecord            in AgentNodeTrace
```

---

## 22. Data Flow Diagrams

The complete visual architectural diagrams are generated and available in the repository:
1. **Universe Ingestion & Candidate Selection Pipeline:** [`NSE_BSE_DATA_FLOW.svg`](file:///Users/ankur/Documents/MajorProject/app/NSE_BSE_DATA_FLOW.svg) / [`NSE_BSE_DATA_FLOW.png`](file:///Users/ankur/Documents/MajorProject/app/NSE_BSE_DATA_FLOW.png)
2. **External APIs to LangGraph Agents Pipeline:** [`API_TO_AGENT_DATA_FLOW.svg`](file:///Users/ankur/Documents/MajorProject/app/API_TO_AGENT_DATA_FLOW.svg) / [`API_TO_AGENT_DATA_FLOW.png`](file:///Users/ankur/Documents/MajorProject/app/API_TO_AGENT_DATA_FLOW.png)

---

## 23. Rate Limits, Caching and API Efficiency

1. **Batch Archival Ingestion:** Ingests official bulk CSV files from NSE in a single HTTP request rather than querying individual stocks, saving over 2,600 redundant HTTP calls per sync.
2. **Database-Backed Caching:** Historical prices and fundamental metrics are persisted in PostgreSQL. Subsequent queries hit the local database.
3. **Decoupled LLM Architecture:** The mathematical optimizer (SciPy SLSQP) runs locally with zero API latency and zero LLM token consumption.

---

## 24. Remaining Gaps and Limitations

1. **BSE Cloudflare Anti-Bot Barrier:** Programmatic REST calls to `api.bseindia.com` return HTTP 403 Forbidden. Dual-listed stocks are reconciled via universal ISIN matching.
2. **Intraday Tick Streaming:** Free providers supply 1-day OHLCV bars and snapshots rather than tick-level Level 2 order books.
3. **Automated Filing PDFs:** Corporate disclosures link to official exchange viewing portals; automatic parsing of 200-page PDF annual reports is handled on-demand rather than bulk pre-fetched.

---

## 25. Final Summary — What Data Actually Goes into Lucid

To generate an intelligent, personalized portfolio, Lucid takes:
1. **From the Investor:** Capital (e.g. ₹5,00,000), Risk Score (Conservative), Horizon (60 months), and Exclusions (e.g. Tobacco).
2. **From NSE & BSE:** The complete 2,639 listed equity universe, normalized by ISIN and trading series.
3. **From Candidate Selection:** A filtered pool of ~504 liquid benchmark stocks with ADTV $\ge 10,000$ shares and turnover $\ge ₹25$ Lakhs.
4. **From Yahoo Finance:** 1-year historical price series, current share prices, and financial ratios (ROE, P/E, D/E).
5. **From RBI / Macro Observations:** India VIX (14.2), Repo Rate ($6.50\%$), CPI Inflation ($5.10\%$), and GDP growth ($7.20\%$).
6. **From LangGraph Multi-Agent Committee:** Qualitative thesis, balance sheet audits, and regulatory checks from 6 specialized agents.
7. **From SciPy SLSQP Optimizer:** Exact integer share quantities ($Q_i$), target weights ($w_i$), and cash allocation ($7,946\text{ INR}$).
8. **To the Investor:** An explainable, fiduciary-audited portfolio with whole-share execution plans, single-stock caps $\le 25\%$, and real-time drift monitoring.


---

## 26. Coordinated Universe, Lookback & News Recency Architecture (November 2026 Optimization)

### 26.1 Complete Security Universe & Recommendation Eligibility
Following full synchronization from the official NSE `EQUITY_L.csv` master, Lucid's PostgreSQL database maintains **2,639 listed equity securities** and **2,715 exchange listings**:
- **Eligible Recommendation Candidates: 504 securities (19.1%)**
  - **Tier 1 (Ultra-Liquid)**: 436 securities (Turnover $\ge ₹1\text{ Crore}$, ADTV $\ge 1,00,000$ shares, price fresh $\le 7$ days). Unrestricted eligibility down to ₹10,000 capital.
  - **Tier 2 (Broad-Liquid)**: 68 securities (Turnover $\ge ₹25\text{ Lakhs}$, ADTV $\ge 25,000$ shares, price fresh $\le 14$ days). Eligible for portfolios $\ge ₹50,000$.
- **Excluded Retained Securities: 2,135 securities (80.9%)**
  - **Missing Closing Prices (`MISSING_PRICE`)**: 2,101 securities currently have no price records in `market_prices`. Excluded from recommendation to prevent unpriced allocations, but fully available for search and Demat CAS statement ingestion.
  - **Suspended NSE Listings (`INACTIVE_SECURITY`)**: 34 securities trade under Series BZ (halted for reporting defaults or insolvency). Excluded from recommendations to protect retail investors, but retained so Demat diagnosis can issue critical risk exit warnings.

### 26.2 Dedicated Analytical Lookback Windows by Purpose
Rather than using a single arbitrary historical window, Lucid formalizes distinct lookback horizons implemented in `backend/portfolio_engine/math_engine.py`:
1. **Short-Term Momentum**: 6 Months (126 trading days, min 30 observations).
2. **Market Regime Classification (DMA 50/200)**: 1 Year (252 trading days, min 50 observations).
3. **Portfolio Covariance & Volatility**: 2 Years (504 trading days, min 60 observations). Ensures sample size $T/N \ge 30$, preventing singular covariance matrices.
4. **Systematic Beta & 3-Year CAGR**: 3 Years (756 trading days, min 700 observations). Institutional standard complying with CRISIL and SEBI mutual fund fact sheets.
5. **Macroeconomic Monetary Cycles**: 5 Years (1,260 trading days).

### 26.3 Event-Specific News Recency & Deduplication
To balance timely signal capture with prompt context limits, Lucid enforces category-specific retention rules (`backend/agent/tools.py`):
1. **Daily Market Commentary**: 1 to 3 days (transient noise discarded quickly).
2. **General Sector Sentiment**: 7 to 14 days (bi-weekly macro trends).
3. **Quarterly Financial Results**: 90 days (retained until next quarterly reporting cycle).
4. **Corporate Governance, Fraud & Sanctions**: 180 to 365 days (retained until cleared).
5. **Syndicated Wire Deduplication**: Normalized alphanumeric headline hashing ensures identical syndicated news stories from multiple publishers consume only a single slot.
6. **Downstream Context Guardrail**: The News Analyst LLM synthesizes disclosures into a concise 2-sentence corporate governance summary, passing structured JSON events (`NewsEventAssessment`) to the Lead Strategist and Critic without blowing context token limits.
