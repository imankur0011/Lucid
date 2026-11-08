# Lucid — Complete External API Inventory & Provider Specifications

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** November 8, 2026  
**Target Codebase:** Lucid Intelligent Investment Platform (`/Users/ankur/Documents/MajorProject/app`)

---

## 1. Master API Inventory Summary Table

| # | Provider / Organization | Exact Endpoint / Resource URL | Protocol / Method | Auth Required | Data Retrieved | Fetch Frequency | Used By (Components & Agents) | Mandatory / Optional |
|---|---|---|---|---|---|---|---|---|
| **1** | **NSE Official Archive (Equities)** | `https://archives.nseindia.com/content/equities/EQUITY_L.csv` | HTTP GET | None (Public Bulk File) | Master list of all 2,632 listed equities (Symbol, Name, Series, ISIN, Face Value, Date) | Daily / On-Demand Sync | Ingestion Service (`exchange_universe_sync.py`), Security Master DB | **Mandatory** (Base universe) |
| **2** | **NSE Official Archive (Indices)** | `https://archives.nseindia.com/content/indices/ind_nifty500list.csv` | HTTP GET | None (Public Bulk File) | 501 Nifty 500 constituents, ISINs, official sector and industry classifications | Daily / On-Demand Sync | Ingestion Service, Benchmark Universe, Industry Taxonomy | **Mandatory** (Benchmark) |
| **3** | **NSE Official Archive (Total Market)** | `https://archives.nseindia.com/content/indices/ind_niftytotalmarket_list.csv` | HTTP GET | None (Public Bulk File) | 754 top equities with standardized industry taxonomy | On-Demand Sync | Ingestion Service, Sector/Industry Mapper | **Optional** (Taxonomy enrichment) |
| **4** | **NSE Official Archive (Microcap)** | `https://archives.nseindia.com/content/indices/ind_niftymicrocap250_list.csv` | HTTP GET | None (Public Bulk File) | 253 micro-cap constituents with industry mappings | On-Demand Sync | Ingestion Service, Sector/Industry Mapper | **Optional** (Taxonomy enrichment) |
| **5** | **Yahoo Finance (`yfinance`)** | `https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.NS` (via Python SDK) | Python SDK / HTTP GET | None (Public Yahoo Endpoint) | Historical daily OHLCV price bars (1 month to 5 years), Adjusted Close, Volume | On-Demand / Daily Ingestion | Market Data Adapter (`adapter.py`), Optimizer, Risk Critic | **Mandatory** (Price history) |
| **6** | **Yahoo Finance (`yfinance`)** | `fast_info` properties (`last_price`, `open`, `day_high`, `day_low`, `last_volume`) | Python SDK / HTTP GET | None (Public Yahoo Endpoint) | Real-time / delayed current market quotes, daily trading volume | Live on-demand (< 15s cache) | Portfolio Monitoring (`monitoring_service.py`), Rebalancing | **Mandatory** (Live quotes) |
| **7** | **Yahoo Finance (`yfinance`)** | `info` dictionary (`trailingPE`, `returnOnEquity`, `priceToBook`, `dividendYield`, `beta`) | Python SDK / HTTP GET | None (Public Yahoo Endpoint) | Fundamental valuation ratios, profitability, leverage, market cap | Weekly / On-Demand (Cached in DB 7 days) | Fundamental Analyst Agent (`fundamental_research_tool`), Factor Ranking | **Mandatory** (Financial ratios) |
| **8** | **Yahoo Finance (India VIX)** | Ticker `^INDIAVIX` via `yfinance` history & fast_info | Python SDK / HTTP GET | None (Public Yahoo Endpoint) | Realized India Volatility Index (Level, Daily Change, Historical Volatility) | On-Demand / Cached in DB 24h | Market Regime Engine (`regime.py`), Macro Analyst Agent | **Mandatory** (Market regime) |
| **9** | **Yahoo Finance (Nifty 50 Trend)** | Ticker `^NSEI` via `yfinance` history (`period="1y"`) | Python SDK / HTTP GET | None (Public Yahoo Endpoint) | Nifty 50 50-day DMA, 200-day DMA, 20-day return slope | On-Demand / Cached in DB 24h | Market Regime Engine (`regime.py`), Market Analyst Agent | **Mandatory** (Trend classification) |
| **10** | **Google Gemini API** | `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash` | REST / HTTPS POST via LangChain | `GEMINI_API_KEY` (Bearer Token) | Qualitative fiduciary synthesis, news sentiment analysis, risk critique, natural language extraction | Per portfolio generation run & interactive query | Specialist Agents (Macro, Market, Fundamental, News, Strategist, Critic, Moderator, Copilot) | **Optional with Fallback** (Strict deterministic fallback if key missing) |
| **11** | **NSE Corporate Filings Portal** | `https://www.nseindia.com/companies-listing/corporate-filings-announcements?symbol={sym}` | HTTPS Portal Links | Browser Session | Live exchange announcements, financial disclosures, shareholding patterns | Real-time on link click | News Analyst Agent (`news_analyst_node`), Stock Why Modal, Investor UI | **Informational** (Audit provenance) |
| **12** | **BSE Corporate Filings Portal** | `https://www.bseindia.com/stock-share-price/{sym}/{bse_code}/corp-announcements/` | HTTPS Portal Links | Browser Session | Official BSE corporate disclosures and quarterly reports | Real-time on link click | Exchange Registry (`exchange_registry.py`), Stock Why Modal, Investor UI | **Informational** (Audit provenance) |
| **13** | **Reserve Bank of India (RBI)** | `https://www.rbi.org.in` (Official Monetary Policy Releases) | Database Observation | Public Official Release | RBI Repo Rate (6.50%), CPI Inflation (5.10%), 10Y G-Sec Yield (7.04%), Real GDP (7.20%) | Monthly / Bi-monthly MPC updates | Macro Analyst Agent (`macro_data_tool`), Optimizer Cash Buffer | **Mandatory** (Macro baseline) |

---

## 2. Detailed Technical Provider Specifications

### 2.1 National Stock Exchange of India (NSE Official Archives)
- **Primary Host:** `archives.nseindia.com`
- **Authentication:** None. Direct HTTP GET with standard browser `User-Agent`.
- **Response Format:** Comma-Separated Values (CSV), UTF-8-SIG encoded.
- **Calling Functions:**
  - `fetch_csv_from_url(url, timeout=15)` in [`backend/market_data/exchange_universe_sync.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py).
  - `sync_nse_equity_master(db)`: Ingests `EQUITY_L.csv` (2,632 records).
  - `sync_nifty500_universe(db)`: Ingests `ind_nifty500list.csv` (501 records).
- **Extracted Fields:**
  - `SYMBOL`: Normalized uppercase ticker (e.g., `RELIANCE`, `TCS`).
  - `NAME OF COMPANY`: Company legal name (e.g., `Reliance Industries Limited`).
  - `SERIES`: Trading series (`EQ` for rolling settlement, `BE` for trade-to-trade, `BZ` for non-compliant).
  - `ISIN NUMBER`: 12-character International Securities Identification Number (`INE002A01018`).
  - `DATE OF LISTING`: Historical listing date parsed to `date` object.
  - `Industry`: Mapped to standardized macro sectors via `INDUSTRY_TO_SECTOR_MAP`.
- **Discarded Fields:** `PAID UP VALUE`, `MARKET LOT`, `FACE VALUE` (retained in raw memory but not stored as primary optimization parameters).
- **Target Database Tables:** `companies`, `securities`, `instrument_listings`, `sectors`, `industries`, `company_industries`.
- **Error & Fallback Handling:** If the network request fails, the service falls back to cached records in the PostgreSQL database without interrupting portfolio generation.

### 2.2 Yahoo Finance (`yfinance` Python SDK)
- **Primary Package:** `yfinance>=0.2.36`
- **Endpoints Used Internally by Library:**
  - `https://query2.finance.yahoo.com/v8/finance/chart/{symbol}.NS`
  - `https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}.NS`
- **Symbol Normalization:** Automatically appends `.NS` for National Stock Exchange listings or `.BO` for Bombay Stock Exchange listings.
- **Calling Classes & Modules:**
  - `YFinanceProvider` in [`backend/market_data/adapter.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/adapter.py).
  - `fetch_live_india_vix()` & `fetch_nifty500_trend()` in [`backend/market_data/regime.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/regime.py).
  - `sync_company_fundamentals()` in [`backend/market_data/exchange_universe_sync.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/exchange_universe_sync.py).
- **Extracted Fields & Transformations:**
  - `last_price`: Extracted from `fast_info.last_price`. Validated to ensure `price > 0`.
  - `historical_prices`: Daily bars containing `Open`, `High`, `Low`, `Close`, `Adj Close`, `Volume`. Stored in `market_prices`.
  - `trailingPE` / `forwardPE`: Sanitized: $\text{PE} = \max(1.0, \text{pe})$. Stored in `fundamental_metrics`.
  - `returnOnEquity`: Extracted as float (e.g. `0.284`). Stored in `fundamental_metrics`.
  - `priceToBook`: Extracted as float (e.g. `4.2`). Stored in `fundamental_metrics`.
  - `dividendYield`: Normalized from percentage (e.g., $1.2\% \to 0.012$).
  - `marketCap`: Stored in INR.
  - `beta`: Stored as float (e.g. `0.85`).
- **Caching & Freshness Controls:**
  - Quotes are cached in memory. Historical prices are cached permanently in `market_prices`.
  - Fundamentals are cached in `fundamental_metrics` for 7 days (`max_stale_days=7`) to prevent rate-limiting.
- **Error & Fallback Handling:** If Yahoo Finance times out, returns HTTP 429, or fails connectivity, the adapter automatically switches to `SimulatedMarketProvider` or queries the latest valid observation from PostgreSQL, logging a `DataQualityStatus.FALLBACK_ASSUMPTION` trace.

### 2.3 Google Gemini Generative AI (`ChatGoogleGenerativeAI`)
- **Primary Package:** `langchain-google-genai>=2.0.0`
- **Model:** `gemini-3.8-flash` (Configurable via `LLM_MODEL` in `.env`).
- **Endpoint:** `https://generativelanguage.googleapis.com/v1beta/`
- **Calling Function:** `get_gemini_llm()` in [`backend/agent/nodes.py`](file:///Users/ankur/Documents/MajorProject/app/backend/agent/nodes.py).
- **Parameters:**
  - `temperature`: `0.1` (low temperature ensures strict fiduciary determinism and prevents creative hallucinations).
  - `max_tokens`: `1024` to `2048`.
- **Calling Agents:**
  1. `MacroAnalystAgent`: Ingests GDP, CPI, Repo Rate, India VIX; outputs macro narrative and sector guidance.
  2. `MarketAnalystAgent`: Ingests Nifty 50 DMA trend and RSI/momentum; outputs technical market climate.
  3. `FundamentalAnalystAgent`: Ingests ROE, P/E, Debt/Equity; outputs balance sheet quality assessment.
  4. `NewsAnalystAgent`: Ingests corporate disclosures; outputs governance flags and regulatory audit.
  5. `LeadStrategistAgent`: Ingests specialist findings; outputs thematic investment thesis and factor weights.
  6. `RiskCriticAgent`: Ingests proposed portfolio; audits single-stock caps (≤25%) and liquidity; outputs approval verdict.
  7. `FiduciaryModerator`: Synthesizes plain-English portfolio-level and stock-level explanations for retail investors.
  8. `ConversationalAssistant`: Answers user queries regarding holdings, stress scenarios, and macro conditions.
- **Deterministic Decoupling Guarantee:** The output of Gemini is **NEVER** used to calculate portfolio weights. All portfolio weights are calculated deterministically by the SciPy SLSQP optimizer in `deterministic_optimizer_node`.
- **Fallback Behavior:** If `GEMINI_API_KEY` is not configured, invalid, or times out, every specialist agent automatically falls back to deterministic rule-based output (`dynamic_heuristic_fallback`), setting `model_name = "fiduciary-rule-engine-v2"`.

### 2.4 Reserve Bank of India (RBI) & Central Bank Disclosures
- **Primary Source:** Official Monetary Policy Committee (MPC) bi-monthly resolutions.
- **Calling Function:** `seed_macro_and_news_data(db)` in [`backend/market_data/regime.py`](file:///Users/ankur/Documents/MajorProject/app/backend/market_data/regime.py) and `macro_data_tool(db)` in [`backend/agent/tools.py`](file:///Users/ankur/Documents/MajorProject/app/backend/agent/tools.py).
- **Tracked Indicators:**
  - `RBI_REPO_RATE`: $6.50\%$
  - `INDIA_CPI_INFLATION`: $5.10\%$
  - `INDIA_GDP_GROWTH`: $7.20\%$
  - `INDIA_10Y_GSEC_YIELD`: $7.04\%$
  - `Real Policy Rate`: Calculated as $\text{Repo Rate} - \text{CPI Inflation} = 6.50\% - 5.10\% = +1.40\%$
- **Target Database Tables:** `economic_indicators`, `economic_observations`.
- **Fiduciary Usage:** A positive real rate ($>+1.0\%$) signals disciplined monetary conditions, prompting the Macro Agent to assign an equity accumulation stance and setting the portfolio cash buffer to $2.5\% - 4.0\%$.

---

## 3. Provider Authentication & Security Specifications

1. **Zero Hardcoded Secrets:** All external API credentials (`GEMINI_API_KEY`, database credentials, JWT secret keys) are injected via environment variables (`.env`) and parsed by `pydantic-settings` in [`backend/config.py`](file:///Users/ankur/Documents/MajorProject/app/backend/config.py).
2. **Read-Only Exchange Ingestion:** NSE and BSE bulk archival ingestion uses standard public HTTP GET requests with browser `User-Agent` strings; no exchange trading credentials or sensitive tokens are stored or transmitted.
3. **Redaction in Logs:** All API request logging automatically sanitizes authorization tokens, passwords, and private user identifiers.
