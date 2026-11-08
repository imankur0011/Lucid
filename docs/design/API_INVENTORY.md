# Lucid — Complete Backend API Inventory

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Total Implemented Endpoints:** Exactly 82 Unique Paths / 88 HTTP Operations  
**Source of Truth:** `/Users/ankur/Documents/MajorProject/app/backend/main.py` & FastAPI OpenAPI Spec  

---

## Searchable Endpoint Inventory Table

| # | API Name | Method | Endpoint Path | Functional Domain | Auth Required | Status |
|---|---|---|---|---|---|---|
| 1 | Authenticate user and issue JWT token pair | `POST` | `/api/v1/auth/login` | Authentication and Account Management | No (Public) | Implemented |
| 2 | Issue OAuth2-compatible bearer token | `POST` | `/api/v1/auth/token` | Authentication and Account Management | No (Public) | Implemented |
| 3 | Register a new investor account with Argon2id hashing | `POST` | `/api/v1/auth/register` | Authentication and Account Management | No (Public) | Implemented |
| 4 | Request email or SMS verification OTP | `POST` | `/api/v1/auth/request-verification` | Authentication and Account Management | No (Public) | Implemented |
| 5 | Verify OTP security code | `POST` | `/api/v1/auth/verify-code` | Authentication and Account Management | No (Public) | Implemented |
| 6 | Initiate password recovery with temporary token | `POST` | `/api/v1/auth/forgot-password` | Authentication and Account Management | No (Public) | Implemented |
| 7 | Reset password using verified recovery token | `POST` | `/api/v1/auth/reset-password` | Authentication and Account Management | No (Public) | Implemented |
| 8 | Change password for authenticated user | `POST` | `/api/v1/auth/change-password` | Authentication and Account Management | Yes (Bearer JWT) | Implemented |
| 9 | Revoke active JWT token and persist to blacklist | `POST` | `/api/v1/auth/logout` | Authentication and Account Management | Yes (Bearer JWT) | Implemented |
| 10 | Retrieve current authenticated user profile snapshot | `GET` | `/api/v1/auth/me` | Authentication and Account Management | Yes (Bearer JWT) | Implemented |
| 11 | Export complete user data archive (GDPR/DPDP) | `GET` | `/api/v1/auth/export-data` | Authentication and Account Management | No (Public) | Implemented |
| 12 | Permanently delete account (Legacy route) | `DELETE` | `/api/v1/auth/account` | Authentication and Account Management | No (Public) | Implemented |
| 13 | Permanently delete account with password verification | `POST` | `/api/v1/auth/delete-account` | Authentication and Account Management | No (Public) | Implemented |
| 14 | List all active financial goals for current user | `GET` | `/api/v1/goals` | Financial Goals Management | Yes (Bearer JWT) | Implemented |
| 15 | Create a new financial investment goal | `POST` | `/api/v1/goals` | Financial Goals Management | Yes (Bearer JWT) | Implemented |
| 16 | Update financial goal target amount or horizon | `PATCH` | `/api/v1/goals/{goal_id}` | Financial Goals Management | Yes (Bearer JWT) | Implemented |
| 17 | Delete an existing financial goal | `DELETE` | `/api/v1/goals/{goal_id}` | Financial Goals Management | Yes (Bearer JWT) | Implemented |
| 18 | Retrieve investor profile and investment experience | `GET` | `/api/v1/profile` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 19 | Delete user profile and account | `DELETE` | `/api/v1/profile` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 20 | Update investor profile details and currency | `PATCH` | `/api/v1/profile` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 21 | Retrieve historical audit versions of investor profile | `GET` | `/api/v1/profile/versions` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 22 | Extract structured profile from natural language prompt | `POST` | `/api/v1/profile/extract-from-text` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 23 | Export comprehensive investor data package | `GET` | `/api/v1/profile/export` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 24 | Permanent account deletion with confirmation phrase | `POST` | `/api/v1/profile/delete-account` | Investor Profile & Preferences | Yes (Bearer JWT) | Implemented |
| 25 | Retrieve 8-question psychometric risk questionnaire | `GET` | `/api/v1/risk-questions` | Risk Assessment & Questionnaire | No (Public) | Implemented |
| 26 | Submit questionnaire answers and compute risk score | `POST` | `/api/v1/risk-assessments` | Risk Assessment & Questionnaire | Yes (Bearer JWT) | Implemented |
| 27 | Retrieve latest completed risk assessment score | `GET` | `/api/v1/risk-assessments/latest` | Risk Assessment & Questionnaire | Yes (Bearer JWT) | Implemented |
| 28 | Initiate multi-agent portfolio generation workflow | `POST` | `/api/v1/portfolio-generation-requests` | Portfolio Generation & Version Management | No (Public) | Implemented |
| 29 | Retrieve status and telemetry of generation request | `GET` | `/api/v1/portfolio-generation-requests/{request_id}` | Portfolio Generation & Version Management | No (Public) | Implemented |
| 30 | List all portfolios belonging to current user | `GET` | `/api/v1/portfolios` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 31 | Delete all portfolios for current user | `DELETE` | `/api/v1/portfolios` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 32 | Batch delete selected portfolios | `POST` | `/api/v1/portfolios/batch-delete` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 33 | Permanently delete an individual portfolio | `DELETE` | `/api/v1/portfolios/{portfolio_id}` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 34 | List historical versions for a portfolio | `GET` | `/api/v1/portfolios/{portfolio_id}/versions` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 35 | Retrieve details of a specific portfolio version | `GET` | `/api/v1/portfolios/{portfolio_id}/versions/{version_id}` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 36 | Retrieve multi-agent research explanations | `GET` | `/api/v1/portfolios/{portfolio_id}/versions/{version_id}/explanations` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 37 | Retrieve dual-level stock justification rationale | `GET` | `/api/v1/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/why` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 38 | Interactive chat about specific stock holding | `POST` | `/api/v1/portfolios/{portfolio_id}/versions/{version_id}/stocks/{symbol}/chat` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 39 | Universal side-by-side comparison of portfolios | `POST` | `/api/v1/portfolios/compare` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 40 | Compare two versions of the same portfolio | `POST` | `/api/v1/portfolios/{portfolio_id}/compare` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 41 | Execute macroeconomic stress-testing scenarios | `POST` | `/api/v1/portfolios/{portfolio_id}/scenarios` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 42 | Evaluate portfolio performance against Nifty 50/500 | `GET` | `/api/v1/portfolios/benchmark-evaluation` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 43 | Export proposed orders as JSON or downloadable CSV | `GET` | `/api/v1/portfolios/{portfolio_id}/versions/{version_id}/export-orders` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 44 | Retrieve live valuation, NAV, and drift radar metrics | `GET` | `/api/v1/portfolios/{portfolio_id}/monitoring` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 45 | Trigger immediate real-time portfolio valuation check | `POST` | `/api/v1/portfolios/{portfolio_id}/monitor-now` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 46 | Generate proposed rebalance trade orders preview | `GET` | `/api/v1/portfolios/{portfolio_id}/rebalance-preview` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 47 | Evaluate drift thresholds and trigger rebalancing | `POST` | `/api/v1/portfolios/{portfolio_id}/check-drift-and-trigger` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 48 | Confirm and apply rebalanced portfolio version | `POST` | `/api/v1/portfolios/{portfolio_id}/apply-rebalance` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 49 | Interactive portfolio assistant chat | `POST` | `/api/v1/portfolios/{portfolio_id}/chat` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 50 | General conversational assistant chat | `POST` | `/api/v1/chat` | Portfolio Generation & Version Management | No (Public) | Implemented |
| 51 | Manually trigger background monitoring scheduler run | `POST` | `/api/v1/portfolios/monitoring/run-scheduler-cycle` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 52 | Retrieve background monitoring scheduler telemetry | `GET` | `/api/v1/portfolios/monitoring/scheduler-status` | Portfolio Generation & Version Management | Yes (Bearer JWT) | Implemented |
| 53 | Download sample CSV template for Demat holdings import | `GET` | `/api/v1/diagnosis/csv-template` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 54 | Upload Demat statement CSV and import holdings | `POST` | `/api/v1/diagnosis/upload-csv` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 55 | Parse raw unstructured holdings text into structured records | `POST` | `/api/v1/diagnosis/parse-text` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 56 | List all imported external Demat portfolios | `GET` | `/api/v1/diagnosis/portfolios` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 57 | Create empty Demat portfolio container | `POST` | `/api/v1/diagnosis/portfolios` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 58 | Delete an imported Demat portfolio | `DELETE` | `/api/v1/diagnosis/portfolios/{existing_portfolio_id}` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 59 | Execute HHI concentration and diversification diagnosis | `POST` | `/api/v1/diagnosis/analyze/{existing_portfolio_id}` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 60 | Retrieve detailed explanation of diagnosis results | `GET` | `/api/v1/diagnosis/{existing_portfolio_id}/explanation` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 61 | Interactive AI copilot chat for Demat diagnosis | `POST` | `/api/v1/diagnosis/{existing_portfolio_id}/chat` | Existing Portfolio Diagnosis | Yes (Bearer JWT) | Implemented |
| 62 | Check health and connectivity of market data feeds | `GET` | `/api/v1/market-data/health` | Market Data & Universe Management | No (Public) | Implemented |
| 63 | Trigger manual market data price ingestion | `POST` | `/api/v1/market-data/ingest` | Market Data & Universe Management | No (Public) | Implemented |
| 64 | List historical market data ingestion runs | `GET` | `/api/v1/market-data/ingestion-runs` | Market Data & Universe Management | No (Public) | Implemented |
| 65 | Retrieve historical OHLCV daily price bars for a symbol | `GET` | `/api/v1/market-data/prices/{symbol}` | Market Data & Universe Management | No (Public) | Implemented |
| 66 | Retrieve current market regime classification and VIX | `GET` | `/api/v1/market-data/regime` | Market Data & Universe Management | No (Public) | Implemented |
| 67 | Retrieve Indian macroeconomic indicators (RBI, CPI) | `GET` | `/api/v1/market-data/macro-indicators` | Market Data & Universe Management | No (Public) | Implemented |
| 68 | Retrieve recent BSE/NSE market news and disclosures | `GET` | `/api/v1/market-data/news` | Market Data & Universe Management | No (Public) | Implemented |
| 69 | Retrieve counts of stored and recommendation securities | `GET` | `/api/v1/market-data/universe-stats` | Market Data & Universe Management | No (Public) | Implemented |
| 70 | Trigger full NSE EQUITY_L.csv universe sync (2,639 stocks) | `POST` | `/api/v1/market-data/sync-universe` | Market Data & Universe Management | No (Public) | Implemented |
| 71 | Reconcile exchange universe and candidate eligibility | `GET` | `/api/v1/market-data/reconcile-universe` | Market Data & Universe Management | No (Public) | Implemented |
| 72 | Fuzzy search securities by name, symbol, or ISIN | `GET` | `/api/v1/market-data/securities/search` | Market Data & Universe Management | No (Public) | Implemented |
| 73 | Resolve company names to canonical ISINs and symbols | `POST` | `/api/v1/market-data/securities/resolve-text` | Market Data & Universe Management | No (Public) | Implemented |
| 74 | Parse Indian financial expressions (Crore, Lakh, %) | `POST` | `/api/v1/market-data/parse-financial-expression` | Market Data & Universe Management | No (Public) | Implemented |
| 75 | Retrieve in-app notifications for current user | `GET` | `/api/v1/notifications` | Notifications & System Alerts | Yes (Bearer JWT) | Implemented |
| 76 | Retrieve count of unread notifications | `GET` | `/api/v1/notifications/unread-count` | Notifications & System Alerts | Yes (Bearer JWT) | Implemented |
| 77 | Mark a single notification as read | `PUT` | `/api/v1/notifications/{notification_id}/read` | Notifications & System Alerts | Yes (Bearer JWT) | Implemented |
| 78 | Mark all notifications as read for current user | `PUT` | `/api/v1/notifications/mark-all-read` | Notifications & System Alerts | Yes (Bearer JWT) | Implemented |
| 79 | Dismiss and delete a notification | `DELETE` | `/api/v1/notifications/{notification_id}` | Notifications & System Alerts | Yes (Bearer JWT) | Implemented |
| 80 | Verify URL safety and reachability against allowed domains | `GET` | `/api/v1/links/verify` | Link Verification & Disclosures | No (Public) | Implemented |
| 81 | Retrieve official BSE/NSE corporate announcement links | `GET` | `/api/v1/links/filings/{symbol}` | Link Verification & Disclosures | No (Public) | Implemented |
| 82 | Retrieve official SEBI, SCORES, and SMART ODR links | `GET` | `/api/v1/links/regulatory` | Link Verification & Disclosures | No (Public) | Implemented |
| 83 | Retrieve system link audit report | `GET` | `/api/v1/links/audit-report` | Link Verification & Disclosures | No (Public) | Implemented |
| 84 | API root service welcome and version check | `GET` | `/` | System Health & Diagnostics | No (Public) | Implemented |
| 85 | Comprehensive backend health and DB status | `GET` | `/api/health` | System Health & Diagnostics | No (Public) | Implemented |
| 86 | Kubernetes/Docker liveness health check | `GET` | `/health` | System Health & Diagnostics | No (Public) | Implemented |
| 87 | PostgreSQL database table count and active connections | `GET` | `/api/db/stats` | System Health & Diagnostics | No (Public) | Implemented |
| 88 | List active securities (Legacy root endpoint) | `GET` | `/api/securities` | System Health & Diagnostics | No (Public) | Implemented |

---
*End of API Inventory. For complete parameter contracts, schemas, and payload examples, refer to [API_CONTRACT.md](API_CONTRACT.md).*
