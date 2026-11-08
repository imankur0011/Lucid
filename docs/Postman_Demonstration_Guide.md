# Postman Demonstration Guide
## Lucid — Intelligent Investment Portfolio Creation, Analysis and Rebalancing Platform
**Target Market**: Indian Retail Equities Advisory & Quantitative Optimization Engine (NSE and BSE)  
**Backend Framework**: FastAPI + PostgreSQL (`localhost:5433/portfolio_dev`, 62 tables) + LangGraph Multi-Agent Engine + SciPy SLSQP  
**Postman Format**: Collection v2.1.0 (16 folders, 96 requests, 20 environment variables)

---

## 1. Quick Start: Importing into Postman

To get started in under 60 seconds:

1. **Launch Postman** (Desktop application or Web client).
2. Click the **Import** button in the top left workspace navigation pane.
3. Select or drag-and-drop the two files from the `postman/` directory:
   - `Portfolio_Creation_Application_API_Collection.postman_collection.json`
   - `Portfolio_Creation_Application.postman_environment.json`
4. Confirm the import. You will now see:
   - **Collection**: `Intelligent Portfolio Creation & Rebalancing Engine API Collection` (**16 folders, 96 requests**)
   - **Environment**: `Intelligent Portfolio Application - Local Development` (**20 variables**)
5. **Activate the Environment**: In the top right environment dropdown of Postman, select **`Intelligent Portfolio Application - Local Development`**.

---

## 2. Environment Variables & Dynamic Chaining

The collection uses dynamic environment variables and post-response test scripts so that requests can be executed sequentially **without manually copying and pasting IDs, tokens, or hashes**.

| Variable Name | Initial Default Value | How It Is Populated | Description |
|---|---|---|---|
| `baseUrl` | `http://localhost:8000` | Configured in Environment | FastAPI root backend server URL |
| `apiPrefix` | `/api/v1` | Configured in Environment | Master API v1 route prefix |
| `accessToken` | *Empty* | Automatically by Request `02.1` or `02.2` | RFC 7519 HMAC-SHA256 JWT Bearer token |
| `userId` | `00000000-0000-0000-0000-000000000001` | Seeded / Updated on Login | Authenticated investor UUID |
| `userEmail` | `investor@example.invalid` | Seeded / Updated on Login | Registered user email address |
| `symbol` | `RELIANCE` | Configured in Environment | Stock symbol for prices, filings, and 'why' tests |
| `goalId` | *Empty* | Automatically by Request `04.1` | Created financial goal UUID |
| `riskAssessmentId` | *Empty* | Automatically by Request `05.2` | Submitted risk assessment UUID |
| `portfolioId` | *Empty* | Automatically by Request `07.1` | Generated portfolio UUID |
| `portfolioVersionId` | *Empty* | Automatically by Request `07.1` | Generated portfolio version UUID |
| `generationRequestId` | `81000000-0000-4000-8000-000000000001` | Seeded / Updated by `07.1` | Portfolio generation request UUID |
| `existingPortfolioId` | *Empty* | Automatically by Request `13.1` | Ingested existing Demat portfolio UUID |
| `notificationId` | *Empty* | Automatically by Request `15.1` | In-app notification alert UUID |
| `sampleFinancialExpression` | `2.5 lakh` | Configured in Environment | Colloquial Indian numeral expression |
| `sampleCompanyText` | `reliance, larsen, infy` | Configured in Environment | Natural language company resolution string |
| `sampleFilingUrl` | `https://www.bseindia.com/...` | Configured in Environment | Official BSE exchange announcement URL |
| `confirmationPhrase` | `PERMANENTLY DELETE MY ACCOUNT` | Configured in Environment | Strict confirmation phrase for deletion |
| `otpCode` | *Empty* | Automatically by Request `02.4` | 6-digit email/mobile verification OTP |
| `resetCode` | *Empty* | Automatically by Request `02.6` | 6-digit password reset OTP |
| `testEmail` | `new.investor.test@example.com` | Configured in Environment | Email address for new registration tests |

---

## 3. The 16 Postman Collection Folders (96 Requests Total)

```
01 - Health & System Information (5 requests)
02 - Authentication & User Management (12 requests)
03 - Investor Onboarding & Profile (6 requests)
04 - Financial Goals Management (4 requests)
05 - Risk Suitability & Assessment (3 requests)
06 - Market & Security Data (12 requests)
07 - Portfolio Creation & Optimization (9 requests)
08 - Real-Time Portfolio Monitoring & Whole-Share Rebalancing (7 requests)
09 - Reasoning Trace, Stock Why & Evidence (3 requests)
10 - Scenario Analysis & Stress Testing (3 requests)
11 - Portfolio Comparison & Conversational Assistant (4 requests)
12 - Trade Execution Basket Export (3 requests)
13 - Portfolio Diagnosis & Rebalancing (9 requests)
14 - Official Exchange Filings & URL Verification (4 requests)
15 - In-App Notifications System (5 requests)
16 - Negative & Edge Case Tests (7 requests)
```

---

## 4. Key Workflows & Example Invocations

### Workflow A: Natural Language Profile & Dynamic Discovery
1. **Parse Indian Numerals**: Execute `06.9 - Parse Indian Financial Number Expression`.
   - Body: `{"expression": "2.5 lakh"}`
   - Response: `{"parsed_value": 250000.0, "formatted_inr": "₹2,50,000"}`
2. **Dynamic Company Discovery**: Execute `06.10 - Dynamically Resolve Listed Companies`.
   - Body: `{"text": "Invest in Reliance, Larsen, and Infy but avoid ITC"}`
   - Automatically maps "Larsen" to `LT`, "Infy" to `INFY`, and tags `ITC` as excluded.
3. **NLP Onboarding**: Execute `03.6 - Extract Investor Profile from Natural Language Text`.
   - Body: `{"prompt": "I am Ankur, 28 years old, looking to invest 2.5 lakhs for 5 years with high risk appetite."}`
   - Automatically extracts investment capital, horizon, and risk tolerance.

### Workflow B: Autonomous Portfolio Generation & Audit
1. **Generate Portfolio**: Execute `07.1 - Generate Intelligent Portfolio Recommendation`.
   - Runs the 13-node LangGraph orchestrator.
   - Enforces 25% single-stock and 40% sector caps via the Adversarial Critic.
   - Solves Markowitz Mean-Variance optimization via SciPy SLSQP.
   - Computes integer whole shares ($Q_i \in \mathbb{Z}_{\ge 0}$) and non-negative cash ($C \ge 0$).
   - Automatically sets `{{portfolioId}}` and `{{portfolioVersionId}}`.
2. **Inspect Holdings**: Execute `07.4 - Get Portfolio Version Detail`.
3. **Audit Citations**: Execute `09.1 - Get Portfolio Version Explanations`.
4. **Stock 'Why' Dossier**: Execute `09.2 - Deep 10-Section Fiduciary Stock Dossier`.
   - Returns 4-factor scores, 5-year balance sheet metrics, peer valuation comparisons, and official BSE/NSE filing links.

### Workflow C: Real-Time Drift Monitoring & Whole-Share Rebalancing
1. **Live Valuation & Drift**: Execute `08.1 - Evaluate Real-Time Portfolio Valuation, Drift & Sector Caps`.
   - Evaluates real-time price changes, current holding weights, and drift against the 5% single-stock and 10% sector trigger thresholds.
2. **Rebalance Trade Preview**: Execute `08.2 - Generate Whole-Share Rebalance Preview with Indian Taxes`.
   - Generates exact whole-share BUY/SELL/HOLD trades with rationales.
   - Provides itemized Indian statutory transaction costs: STT (0.10%), GST (18%), Stamp Duty (0.015%), Exchange and SEBI fees.
3. **Commit Rebalance**: Execute `08.3 - Apply Whole-Share Rebalance & Increment Version`.
   - Updates holding quantities, increments the version number, and establishes new baseline target weights.

### Workflow D: Official Filings & Regulatory Verification
1. **Verify Link**: Execute `14.1 - Verify Exchange Announcement URL Integrity`.
   - Performs a live HTTP HEAD verification to confirm the corporate disclosure URL returns 200 OK.
2. **Corporate Filings**: Execute `14.2 - Get Verified Corporate Disclosures for Symbol`.
3. **Link Audit Report**: Execute `14.4 - Get System-Wide Link Verification Audit Report`.

### Workflow E: In-App Notifications & Alerts
1. **List Alerts**: Execute `15.1 - List Recent Notifications & Drift Alerts`.
2. **Unread Count**: Execute `15.2 - Get Unread Notifications Count`.
3. **Mark Read**: Execute `15.3 - Mark Single Notification as Read` or `15.4 - Mark All Read`.

---

## 5. Automated Verification in Postman (Collection Runner)

You can run the entire 96-request collection in under 3 minutes using Postman Collection Runner:

1. Click on the collection `Intelligent Portfolio Creation & Rebalancing Engine API Collection`.
2. Click **Run Collection**.
3. Select all 16 folders.
4. Ensure environment **`Intelligent Portfolio Application - Local Development`** is selected.
5. Click **Run Intelligent Portfolio...**.
6. All tests will pass sequentially with green badges (`pm.test` assertions confirmed).

---
*Lucid Postman Demonstration Guide — Version 2026.11-v2.0*
