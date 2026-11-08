# Lucid — API and Data Source Inventory
## Complete External Data Integrations & Internal REST API Endpoint Specification

---

## Part 1: External APIs & Data Integrations

```
+----------------------------------------------------------------------------------------------------------------------+
|                                            EXTERNAL DATA SOURCE INVENTORY                                            |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| Integration / API    | Provider / Protocol      | Key Data Points       | Production Role     | Deterministic Fallback|
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| Yahoo Finance        | yfinance (Python SDK)    | Real-time quotes,     | Live market price   | Cached quotes in DB  |
| (NSE / BSE Equities) | HTTP REST                | OHLCV 1Y history,     | tracking, factor    | & SimulatedMarket-   |
|                      |                          | Market Cap, P/E, Beta | calculation, drift  | Provider for CI      |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| India VIX            | yfinance (^INDIAVIX)     | Volatility index,     | Macro regime        | 50-day historical    |
| & Nifty 50 Index     | yfinance (^NSEI)         | 50-day & 200-day SMA  | classification      | volatility default   |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| Google Gemini        | google-genai SDK         | Multi-agent research, | Qualitative agent   | Deterministic rule-  |
| (Gemini 2.5 Flash)   | HTTP/gRPC API            | NLP profile extraction| synthesis, why-this-| based heuristic      |
|                      |                          | explanations          | stock generator     | factor scoring       |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| Federal Reserve FRED | FRED API                 | India 10Y Yield,      | Global macro &      | Domestic RBI baseline|
| (FRED Macro Data)    | HTTP GET JSON            | US Fed Funds Rate     | interest rate regime| constants            |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| NewsAPI & Exchange   | NewsAPI / BSE RSS        | Corporate filings,    | Governance risk &   | Cached official BSE  |
| Feeds                | HTTP GET JSON            | quarterly results     | sentiment scoring   | filings in DB        |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
| NSE / BSE Master     | Official JSON Registries | Scrip codes, ISINs,   | Dynamic stock       | Seeded equity master |
| Security Directory   | HTTPS Static Master      | Industry taxonomies   | discovery & search  | database table       |
+----------------------+--------------------------+-----------------------+---------------------+----------------------+
```

---

## Part 2: Internal FastAPI REST Endpoints (`/api/v1`)

### 1. Authentication & Identity (`/api/v1/auth`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `POST` | `/api/v1/auth/register` | Registers a new investor with email and password. | `UserRegistrationRequest` | `UserAuthResponse` | Public |
| `POST` | `/api/v1/auth/login` | Authenticates user via Argon2id hash and issues JWT token. | `UserLoginRequest` | `UserAuthResponse` | Public |
| `POST` | `/api/v1/auth/logout` | Revokes current JWT token and adds JTI to revocation blacklist. | None (Header Token) | `SuccessMessageResponse` | Bearer |
| `GET` | `/api/v1/auth/me` | Fetches authenticated investor profile and role permissions. | None | `AppUserResponse` | Bearer |
| `DELETE` | `/api/v1/auth/account` | Permanently deletes investor account and cascades all data. | `AccountDeletionRequest` | `SuccessMessageResponse` | Bearer |
| `GET` | `/api/v1/auth/export-data` | Exports complete investor data package in JSON format. | None | `InvestorDataExportResponse` | Bearer |

### 2. Portfolio Generation & Management (`/api/v1/portfolios`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `POST` | `/api/v1/portfolios/generate` | Triggers the 13-node LangGraph multi-agent generation pipeline. | `PortfolioGenerationRequest` | `PortfolioVersionResponse` | Bearer / Demo |
| `GET` | `/api/v1/portfolios` | Lists all active and historical portfolios for the investor. | None | `List[InvestorPortfolioResponse]` | Bearer |
| `GET` | `/api/v1/portfolios/{id}` | Fetches active version details, holdings, and risk metrics. | None | `PortfolioDetailResponse` | Bearer |
| `GET` | `/api/v1/portfolios/{id}/versions` | Lists historical versions generated for this portfolio. | None | `List[PortfolioVersionSummary]` | Bearer |
| `GET` | `/api/v1/portfolios/{id}/monitoring` | Evaluates real-time price drift, sector weights, and caps. | None | `PortfolioMonitoringResponse` | Bearer |
| `GET` | `/api/v1/portfolios/{id}/rebalance-preview` | Generates whole-share rebalance trade plan and tax levy preview. | None | `RebalancePreviewResponse` | Bearer |
| `POST` | `/api/v1/portfolios/{id}/apply-rebalance` | Commits rebalance trades, updates version number and holdings. | None | `PortfolioVersionResponse` | Bearer |
| `DELETE` | `/api/v1/portfolios/{id}` | Deletes a specific investor portfolio and associated records. | None | `SuccessMessageResponse` | Bearer |
| `GET` | `/api/v1/portfolios/{id}/export-basket` | Generates broker-ready order CSV (Zerodha, Groww format). | Query: `format` | `FileResponse (CSV)` | Bearer |

### 3. Explainability & Stock Research (`/api/v1/portfolios/{id}/stocks/{symbol}`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `GET` | `/api/v1/portfolios/{id}/stocks/{symbol}/why` | Deep 10-section explainability dossier for a specific stock. | None | `StockWhyResponse` | Bearer |
| `POST` | `/api/v1/portfolios/{id}/chat` | Conversational portfolio copilot for rationale inquiries. | `PortfolioChatRequest` | `PortfolioChatResponse` | Bearer |

### 4. Demat Diagnosis & Copilot (`/api/v1/diagnosis`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `POST` | `/api/v1/diagnosis/upload-holdings` | Parses uploaded Demat statement (CSV/JSON) into existing portfolio. | Multipart File | `DematUploadResponse` | Bearer |
| `POST` | `/api/v1/diagnosis/evaluate` | Conducts comprehensive 7-section portfolio health diagnosis. | `DiagnosisEvaluationRequest` | `PortfolioDiagnosisResponse` | Bearer |
| `POST` | `/api/v1/diagnosis/copilot/chat` | Contextual AI Copilot for interactive diagnosis audit. | `DiagnosisCopilotChatRequest` | `DiagnosisCopilotChatResponse` | Bearer |

### 5. Market Data & Universe Discovery (`/api/v1/market-data`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `GET` | `/api/v1/market-data/quote/{symbol}` | Fetches real-time equity quote, bid/ask, and day range. | None | `LiveQuoteResponse` | Bearer |
| `GET` | `/api/v1/market-data/regime` | Fetches current market regime, India VIX, and Nifty trend. | None | `MarketRegimeResponse` | Bearer |
| `GET` | `/api/v1/market-data/search` | Dynamic fuzzy search across 2,000+ NSE/BSE listed companies. | Query: `q`, `limit` | `List[CompanySearchResult]` | Bearer |

### 6. Notifications & System Alerts (`/api/v1/notifications`)

| Method | Endpoint | Description | Request Body | Response Model | Auth |
|:---:|:---|:---|:---|:---|:---:|
| `GET` | `/api/v1/notifications` | Lists recent notifications, drift alerts, and rebalance triggers. | None | `List[NotificationResponse]` | Bearer |
| `POST` | `/api/v1/notifications/{id}/read` | Marks a specific notification as acknowledged/read. | None | `SuccessMessageResponse` | Bearer |

---
*Lucid API Inventory Specification — Version 2026.11-v2.0*

