# Lucid — Complete Postman Setup & API Testing Guide

This directory contains the complete, verified Postman collection and development environment for **Lucid**, enabling any developer to import, authenticate, and test all backend REST APIs.

---

## 1. Postman Assets Overview

| Asset File | Purpose | Contents |
|---|---|---|
| [`Lucid_API_Collection.json`](./Lucid_API_Collection.json) | Complete API Test Collection | **96 requests** organized across 16 functional domain folders |
| [`Lucid_Development_Environment.json`](./Lucid_Development_Environment.json) | Local Development Environment | Environment variables (`baseUrl`, `apiPrefix`, `accessToken`, `userId`, etc.) |
| [`Postman_Demonstration_Guide.md`](./Postman_Demonstration_Guide.md) | Step-by-Step API Demonstration | Detailed narrative guide for professor/presentation walkthroughs |

---

## 2. Prerequisites & Installation

### Step 2.1: Download Postman
Download the free desktop application from [Postman Official Download](https://www.postman.com/downloads/) for macOS, Linux, or Windows.

### Step 2.2: Ensure Backend Is Running
The API endpoints require the FastAPI backend running on port 8000:
```bash
cd backend
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```
Verify backend is reachable:
```bash
curl http://localhost:8000/health
```

---

## 3. Importing Assets into Postman

1. Open the Postman desktop application.
2. Click the **Import** button in the top-left navigation pane.
3. Select or drag-and-drop both files:
   - `postman/Lucid_API_Collection.json`
   - `postman/Lucid_Development_Environment.json`
4. Confirm import. The collection **"Lucid — Complete API Collection"** will appear in your left sidebar, and **"Lucid Local Development Environment"** will appear in the environment dropdown in the top-right corner.
5. In the top-right environment selector, choose **"Lucid Local Development Environment"**.

---

## 4. Authentication Automation & Token Handling

Lucid uses JWT bearer authentication. The Postman collection features **automated token extraction**:

1. Expand folder `02 - Authentication & User Management`.
2. Execute request `POST /api/v1/auth/login` (or `POST /api/v1/auth/register`).
3. The embedded Postman test script executes automatically:
   ```javascript
   const jsonData = pm.response.json();
   const token = jsonData.access_token || (jsonData.data && jsonData.data.access_token);
   if (token) {
       pm.environment.set("accessToken", token);
       console.log("✅ Access token saved to environment successfully.");
   }
   ```
4. All subsequent authenticated endpoints automatically attach `Authorization: Bearer {{accessToken}}`. You do **not** need to copy-paste tokens manually.

---

## 5. Recommended Execution Sequence

For a complete end-to-end journey, execute requests in this order:

```text
1. Health & Status
   └── GET /health (Verify API & PostgreSQL status)

2. Authentication
   ├── POST /api/v1/auth/login (Saves accessToken)
   └── GET /api/v1/auth/me (Verifies profile identity)

3. Investor Suitability & Goals
   ├── GET /api/v1/risk-questions (10 standardized SEBI questions)
   ├── POST /api/v1/risk-assessments (Computes risk score: Moderate)
   └── POST /api/v1/goals (Creates ₹1,00,000 Wealth Creation target)

4. Market Data & Security Universe
   ├── GET /api/v1/market-data/universe-stats (2,639 equities, 2,715 listings)
   ├── GET /api/v1/market-data/regime (Classifies Nifty 50 trend & India VIX)
   └── GET /api/v1/market-data/securities/search?q=RELIANCE

5. Multi-Agent Portfolio Generation
   └── POST /api/v1/portfolio-generation-requests (Triggers 13-node LangGraph pipeline)

6. Portfolio Inspection & Reasoning
   ├── GET /api/v1/portfolios/{portfolio_id} (Active portfolio)
   ├── GET /api/v1/portfolios/{portfolio_id}/versions/{version_id}/stocks/RELIANCE/why
   └── POST /api/v1/portfolios/{portfolio_id}/chat (Copilot conversational Q&A)

7. Continuous Monitoring & Rebalancing
   ├── GET /api/v1/portfolios/{portfolio_id}/monitoring (Holding & sector drift radar)
   ├── GET /api/v1/portfolios/{portfolio_id}/rebalance-preview (Whole-share BUY/SELL trades)
   └── POST /api/v1/portfolios/{portfolio_id}/apply-rebalance (Approves rebalance & bumps version)

8. CAS Demat Statement Diagnosis
   └── POST /api/v1/diagnosis/parse-text or /upload-csv (HHI concentration & overlap analysis)
```

---

## 6. Postman Collection Completeness Summary Table

| Folder # | Functional Domain Folder | Requests | Key Endpoints Covered | Test Scripts Included |
|---|---|---:|---|---|
| **01** | Health & System Information | 5 | `/health`, `/api/health`, `/`, `/api/db/stats`, `/api/securities` | Status code 200, DB connected |
| **02** | Authentication & User Management | 12 | `/register`, `/login`, `/token`, `/me`, `/logout`, `/forgot-password`, `/reset-password` | Automated token capture, RBAC checks |
| **03** | Investor Onboarding & Profile | 6 | `/profile`, `/profile/extract-from-text`, `/versions`, `/export` | JSON schema validation, PAN status |
| **04** | Financial Goals Management | 4 | `/goals` (CRUD: GET, POST, PATCH, DELETE) | Target capital and horizon validation |
| **05** | Risk Suitability & Assessment | 3 | `/risk-questions`, `/risk-assessments`, `/risk-assessments/latest` | SEBI capacity scoring, category mapping |
| **06** | Market & Security Data | 12 | `/universe-stats`, `/prices/{sym}`, `/regime`, `/sync-universe`, `/reconcile-universe` | Quote currency, ADTV, turnover checks |
| **07** | Portfolio Creation & Optimization | 9 | `/portfolio-generation-requests`, `/portfolios`, `/benchmark-evaluation` | Integer lots, 100% budget check |
| **08** | Real-Time Monitoring & Rebalance | 7 | `/monitoring`, `/check-drift-and-trigger`, `/rebalance-preview`, `/apply-rebalance` | Drift threshold (5%/8%), cash non-negative |
| **09** | Reasoning Trace & Stock Why | 3 | `.../stocks/{sym}/why`, `.../stocks/{sym}/chat`, `.../explanations` | Dual-level plain & quant explanations |
| **10** | Scenario Analysis & Stress Testing | 3 | `.../scenarios` (2008 Crash, COVID 2020 shock, Rate Spike) | Drawdown limits, Sharpe re-estimation |
| **11** | Comparison & Conversational AI | 4 | `/chat`, `/portfolios/compare`, `.../chat` | Safe harbor disclaimers, no hallucinations |
| **12** | Trade Execution Basket Export | 3 | `.../export-orders` (CSV, JSON, Broker preview) | Statutory costs (STT, GST, Stamp duty) |
| **13** | Portfolio Diagnosis & Rebalancing | 9 | `/diagnosis/portfolios`, `/upload-csv`, `/parse-text`, `.../chat` | HHI concentration, sector skew warnings |
| **14** | Official Exchange Filings & Links | 4 | `/links/verify`, `/links/regulatory`, `/links/filings/{sym}` | Official NSE/BSE link integrity |
| **15** | In-App Notifications System | 5 | `/notifications`, `/mark-all-read`, `/unread-count`, `/{id}/read` | Transactional alerts, unread counters |
| **16** | Negative & Edge Case Tests | 7 | Unauthorized access, invalid tokens, zero-capital, non-existent ticker | HTTP 401, 404, 422, 429 validation |
| **TOTAL** | **16 Structured Folders** | **96** | **All 82 Implemented OpenAPI Paths** | **Automated Tests Across All Folders** |

---

## 7. Running with Postman Collection Runner or Newman

You can execute the entire test suite autonomously:

### In Postman GUI:
1. Click the **"..."** menu on `Lucid — Complete API Collection` and select **Run collection**.
2. Select all folders or specific functional domains.
3. Choose the **Lucid Local Development Environment**.
4. Click **Run Lucid — Complete API Collection**.

### Via Newman CLI (Headless Automation):
```bash
# Install Newman globally
npm install -g newman

# Execute complete collection against local development backend
newman run postman/Lucid_API_Collection.json \
    -e postman/Lucid_Development_Environment.json \
    --bail
```

---

## 8. Troubleshooting Common Issues

| Issue / Symptom | Root Cause | Solution |
|---|---|---|
| `Could not get any response` / Connection Refused | Backend is not running on `localhost:8000` | Start backend via `uvicorn backend.main:app --port 8000` |
| `HTTP 401 Unauthorized` on protected routes | Access token has expired or is empty | Run `02 - Authentication -> Login` to refresh `{{accessToken}}` |
| `HTTP 429 Too Many Requests` | Sliding-window rate limiter triggered | Wait 60 seconds or adjust `InMemoryRateLimiterMiddleware` in `backend/main.py` |
| `HTTP 403 Diagnostic endpoint disabled` | `APP_ENV` is set to production/staging | Ensure `APP_ENV=development` in `.env` for `/api/db/stats` |

