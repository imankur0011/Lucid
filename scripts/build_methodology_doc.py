#!/usr/bin/env python3
"""
Lucid — End-to-End Application Methodology Specification Generator.
Enhances METHODOLOGY.md to cover all sections 7.1 through 7.10 (Flows A through H)
and the 22-step application lifecycle with complete technical precision.
"""

import sys
from pathlib import Path

ROOT_DIR = Path('/Users/ankur/Documents/MajorProject/app')
sys.path.insert(0, str(ROOT_DIR))

def build_methodology():
    print("Building enhanced METHODOLOGY.md...")
    out_file = ROOT_DIR / "METHODOLOGY.md"

    with open(out_file, "w", encoding="utf-8") as f:
        f.write("""# Lucid — Complete End-to-End Application Methodology Specification

**Document Version:** 2026.11-v2.0  
**Authoritative Date:** 2026-11-08  
**Target Audience:** Quantitative Developers, Financial Analysts, Technical Evaluators, System Architects  
**Scope:** End-to-end operational workflows, algorithms, mathematical models, and lifecycle state transitions across all 8 functional flows of the Lucid Platform.

---

## Executive Summary

This document specifies the complete operational methodology governing **Lucid**. It explains how user inputs, macroeconomic indicators, and exchange price feeds are transformed into mathematically optimal, fiduciarily audited equity portfolios, continuously monitored for drift, and safely rebalanced without custody of client capital.

Every stage follows the canonical pipeline:

$$\\mathbf{Input} \\longrightarrow \\mathbf{Processing} \\longrightarrow \\mathbf{Decision} \\longrightarrow \\mathbf{Output} \\longrightarrow \\mathbf{Next\\ Component}$$

---

## Table of Contents

1. [Overall Application Lifecycle (22-Step Specification)](#1-overall-application-lifecycle-22-step-specification)
2. [Flow A — New Portfolio Creation Pipeline](#2-flow-a--new-portfolio-creation-pipeline)
3. [Flow B — Existing Demat Portfolio Diagnosis](#3-flow-b--existing-demat-portfolio-diagnosis)
4. [Flow C — Continuous Unattended Portfolio Monitoring](#4-flow-c--continuous-unattended-portfolio-monitoring)
5. [Flow D — Minimum-Turnover Portfolio Rebalancing](#5-flow-d--minimum-turnover-portfolio-rebalancing)
6. [Flow E — Stock-Level Fiduciary Explanation ('Why This Stock?')](#6-flow-e--stock-level-fiduciary-explanation-why-this-stock)
7. [Flow F — Market Regime Classification](#7-flow-f--market-regime-classification)
8. [Flow G — Stock Universe Ingestion & Candidate Selection](#8-flow-g--stock-universe-ingestion--candidate-selection)
9. [Flow H — Notifications & Multi-Channel Alerting](#9-flow-h--notifications--multi-channel-alerting)
10. [Methodology Diagrams & Flow Visualizations](#10-methodology-diagrams--flow-visualizations)

---

## 1. Overall Application Lifecycle (22-Step Specification)

Lucid executes an institutional investment lifecycle divided into 22 discrete, deterministic steps:

1. **User Registration & Argon2id Authentication:** User credentials hashed using Argon2id ($m=65536, t=3, p=4$); JWT issued upon verification.
2. **Investor Profile Collection:** Captures demographic details, investment experience, income, and liquidity horizon.
3. **Psychometric Risk Assessment:** 8-question questionnaire calculates risk score (0-100) and categorizes into one of 5 risk profiles.
4. **Natural-Language Preference Ingestion:** Optional user prompt parsed for ethical exclusions, sector tilts, and special directives.
5. **Structured Profile & Feasibility Extraction:** Validates capital feasibility (minimum ₹10,000 for equity basket).
6. **Market Intelligence Retrieval:** Ingests live NSE indices, India VIX, and repo rates from PostgreSQL cache.
7. **Market-Regime Classification:** Classifies market climate into `BULL_TREND`, `BEAR_TREND`, `HIGH_VOLATILITY`, or `NEUTRAL`.
8. **Security Universe Retrieval:** Loads active security master (2,639 listed equities).
9. **Candidate Eligibility Screening:** Liquidity screen extracts ~504 candidate stocks meeting ADTV $\\ge$ ₹2 Crore and market cap thresholds.
10. **Fundamental Multi-Factor Scoring:** Computes Winsorized Z-scores across Value ($P/E^{-1}$), Quality (ROE/ROCE), Momentum, and Low Volatility.
11. **News & Disclosure Research:** Scans BSE/NSE corporate filings for promoter pledging, audit qualifications, and regulatory alerts.
12. **Agentic Context Synthesis:** Specialist agents construct structured domain payloads.
13. **Strategy Generation:** Lead Strategist proposes candidate roles (`CORE`, `GROWTH`, `DEFENSIVE`, `DIVERSIFICATION`) and tentative weights.
14. **Independent Risk Critic Audit:** Independent audit verifies compliance against SEBI suitability rules, single-stock caps (20%), and sector caps (30%).
15. **Bounded Strategist Rework:** If rejected, proposal reworked up to `max_rework_count = 2`; else forwarded to optimizer.
16. **SLSQP Mean-Variance Optimization:** SciPy SLSQP solver maximizes Sharpe ratio subject to hard portfolio constraints.
17. **Whole-Share Discrete Allocation:** Converts continuous weights to integer share counts; reserves residual cash ($C_{cash} \\ge 0$).
18. **Transaction Cost & Friction Preview:** Models statutory Indian taxes (STT 0.1%, GST 18%, exchange turnover fees, stamp duty).
19. **Post-Optimization Constraint Validation:** Deterministic arithmetic verification that integer lots do not breach policy caps.
20. **Fiduciary Explanation Generation:** Synthesizes Level 1 executive theses and Level 2 quantitative factor rationales with filing URLs.
21. **ACID State Persistence:** Atomic PostgreSQL commit of portfolio version, security decisions, evidence items, and execution traces.
22. **Client Presentation & Order Export:** Displays allocations, NAV metrics, and downloadable order preview CSV.

---

## 2. Flow A — New Portfolio Creation Pipeline

Flow A handles client requests to generate a brand new equity portfolio.

```mermaid
graph TD
    A["User Request (Amount, Horizon, Risk)"] --> B["API: POST /api/v1/portfolio-generation-requests"]
    B --> C["Manager Node: Context Initialization"]
    C --> D{"Suitability & Feasibility Gate"}
    D -->|Fail: Capital < ₹10,000| Fail1["Abort: Return 422 Feasibility Error"]
    D -->|Pass| E["Specialist Agent Pipeline (Macro, Market, Fundamental, News)"]
    E --> F["Lead Strategist Proposal"]
    F --> G{"Risk Critic Audit"}
    G -->|Objections (Count < 2)| H["Strategist Bounded Rework"]
    H --> G
    G -->|Blocked / Max Rework| Fail2["Abort: Persistence (BLOCKED)"]
    G -->|Approved| I["Deterministic SLSQP Optimizer (SciPy)"]
    I --> J["Whole-Share Integer Lot Rounding & Cash Conservation"]
    J --> K{"Critic Final Validation"}
    K -->|Approved| L["Fiduciary Moderator (Two-Level Stock-Why)"]
    L --> M["ACID PostgreSQL Transaction Commit"]
    M --> N["Client UI Display & CSV Export"]
```

### 2.1 Inputs
- `investment_amount`: Float (min: ₹10,000, max: ₹10,00,00,000).
- `investment_horizon_months`: Integer (min: 3 months, recommended: $\\ge 36$ months).
- `risk_category`: `CONSERVATIVE`, `MODERATE_CONSERVATIVE`, `BALANCED`, `GROWTH`, `AGGRESSIVE`.
- `user_prompt`: Optional natural language guidance.

### 2.2 Mathematical Optimization Formulation
$$\\min_w \\quad - \\frac{w^T \\mu - R_f}{\\sqrt{w^T \\Sigma w}}$$
Subject to:
$$\\sum_{i=1}^N w_i = 1 - w_{cash}$$
$$0.02 \\le w_i \\le 0.20 \\quad \\forall i \\in \\text{Holdings}$$
$$\\sum_{i \\in \\text{Sector}_k} w_i \\le 0.30 \\quad \\forall k$$

### 2.3 Whole-Share Allocation & Residual Cash
$$\\text{Shares}_i = \\left\\lfloor \\frac{C_{total} \\times w_i}{P_i} \\right\\rfloor$$
$$\\text{Cash}_{unallocated} = C_{total} - \\sum_{i=1}^N (\\text{Shares}_i \\times P_i) \\ge 0$$

---

## 3. Flow B — Existing Demat Portfolio Diagnosis

Flow B evaluates external portfolios imported from broker Demat accounts (e.g. Zerodha, Groww, AngelOne).

### 3.1 Processing Sequence
1. **Holdings Import:** User uploads Demat holdings via structured CSV or text payload (`POST /api/v1/diagnosis/upload-csv`).
2. **Entity Resolution:** `CompanyResolutionService` resolves noisy broker ticker strings and company names to canonical ISINs.
3. **Market Valuation:** Fetches latest close prices to compute current holding values and weights.
4. **Concentration Risk Analysis:** Computes the Herfindahl-Hirschman Index (HHI):
   $$\\text{HHI} = \\sum_{i=1}^N (w_i \\times 100)^2$$
   - $\\text{HHI} > 2,500$: High concentration warning.
5. **Sector Over-Exposure Check:** Identifies any sector with weight $> 30\\%$.
6. **Diagnosis Output:** Returns health score (0-100), concentration status, and specific risk recommendations.

---

## 4. Flow C — Continuous Unattended Portfolio Monitoring

Flow C is executed autonomously by the `BackgroundMonitoringScheduler` daemon thread every 300 seconds during Indian equity trading hours (09:15 to 15:30 IST).

### 4.1 Evaluation Logic
For each active investor portfolio:
1. Retrieve latest market prices for all held positions.
2. Compute current portfolio Net Asset Value (NAV):
   $$\\text{NAV} = \\text{Cash} + \\sum_{i=1}^N (\\text{Shares}_i \\times P_{current, i})$$
3. Compute current weight for each holding:
   $$w_{current, i} = \\frac{\\text{Shares}_i \\times P_{current, i}}{\\text{NAV}}$$
4. Calculate individual asset drift:
   $$\\text{Drift}_i = |w_{current, i} - w_{target, i}|$$
5. Calculate aggregate portfolio absolute drift:
   $$\\text{Total Drift} = \\frac{1}{2} \\sum_{i=1}^N |w_{current, i} - w_{target, i}|$$
6. **Trigger Thresholds:**
   - If $\\max_i(\\text{Drift}_i) \\ge 5.0\\%$ OR $\\text{Total Drift} \\ge 15.0\\%$:
     - Create in-app alert in `notifications` table (`DRIFT_WARNING`).
     - Generate a pending rebalancing suggestion in `rebalance_suggestions`.

---

## 5. Flow D — Minimum-Turnover Portfolio Rebalancing

Flow D generates a proposed trade execution schedule to restore an out-of-bounds portfolio to target allocations while minimizing turnover and transaction costs.

### 5.1 Order Generation Rules
$$\\Delta \\text{Capital}_i = \\text{NAV} \\times w_{target, i} - (\\text{Shares}_{current, i} \\times P_i)$$
$$\\Delta \\text{Shares}_i = \\text{Round}\\left(\\frac{\\Delta \\text{Capital}_i}{P_i}\\right)$$

- If $\\Delta \\text{Shares}_i > 0$: Propose `BUY` order of $\\Delta \\text{Shares}_i$.
- If $\\Delta \\text{Shares}_i < 0$: Propose `SELL` order of $|\\Delta \\text{Shares}_i|$.
- If $\\Delta \\text{Shares}_i = 0$: `HOLD`.

### 5.2 Statutory Transaction Cost Friction Preview
Statutory friction is calculated for the order basket:
- **Securities Transaction Tax (STT):** $0.1\\%$ on buy and sell delivery turnover.
- **NSE Transaction Charges:** $0.00345\\%$.
- **GST:** $18\\%$ on brokerage and transaction fees.
- **Stamp Duty:** $0.015\\%$ on total buy turnover.

---

## 6. Flow E — Stock-Level Fiduciary Explanation ('Why This Stock?')

Flow E produces verifiable, human-readable rationales for any recommended equity holding via `GET /api/v1/portfolios/{id}/versions/{vid}/stocks/{symbol}/why`.

### 6.1 Dual-Level Explanation Model
1. **Level 1 (Executive Investment Thesis):**
   A concise 2-3 sentence thesis explaining the company's business model, industry leadership, capital efficiency, and strategic role within the portfolio (e.g. foundational `CORE` compounder vs high-beta `GROWTH`).
2. **Level 2 (Deep Factor Attribution & Evidence Citations):**
   Granular financial evidence with direct hyperlink citations to official BSE/NSE disclosures:
   - **Quality Evidence:** ROCE (>25%), Return on Equity, Debt-to-Equity (<0.5).
   - **Valuation Evidence:** Trailing P/E relative to 5-year historical median.
   - **Market Evidence:** 1-year Beta, RSI, trend vs 200-day SMA.
   - **Official Filing Citation:** URL pointing directly to BSE corporate filing portal.

---

## 7. Flow F — Market Regime Classification

Flow F dynamically determines the broader equity market environment using India VIX and Nifty 50 moving averages (`backend/market_data/regime.py`).

| Regime Token | Trigger Criteria | Portfolio Adaptation |
|---|---|---|
| `HIGH_VOLATILITY` | India VIX $> 24.0$ | Increase cash buffer to 10-15%, lower single-stock caps to 15%, favor Low-Beta / Quality |
| `BULL_TREND` | Nifty 50 Close $> \\text{SMA}_{50} > \\text{SMA}_{200}$ | Maximize equity deployment (98%+), increase Growth/Momentum factor tilt |
| `BEAR_TREND` | Nifty 50 Close $< \\text{SMA}_{50} < \\text{SMA}_{200}$ | Tilt toward Defensive/Value sectors (FMCG, Pharma), restrict high-beta midcaps |
| `NEUTRAL` | All other conditions | Standard balanced weights across Core compounders |

---

## 8. Flow G — Stock Universe Ingestion & Candidate Selection

Flow G filters the full Indian exchange universe into a high-liquidity recommendation pool.

```
Total Stored Exchange Securities (PostgreSQL): 2,639
                │
                ▼ (Tier 1 & Tier 2 Liquidity Filter)
Recommendation Universe: 504 Candidates
  - Nifty 50 / Nifty Next 50 (ADTV ≥ ₹10 Cr, MCap ≥ ₹20k Cr)
  - Liquid Mid-Caps (ADTV ≥ ₹2 Cr, MCap ≥ ₹5k Cr, 250+ days trading)
                │
                ▼ (Pre-Screening: Sector Exclusions & Quality Thresholds)
Top Ranked Candidate Pool: 30 - 50 Candidates
                │
                ▼ (Multi-Agent Research & Risk Critic Audit)
Strategist Proposed Portfolio: 15 - 25 Candidates
                │
                ▼ (SLSQP Optimization & Whole-Share Rounding)
Final Portfolio Holdings: 12 - 20 Stocks + Residual Cash Buffer
```

---

## 9. Flow H — Notifications & Multi-Channel Alerting

Flow H manages system-generated alerts and client notifications (`backend/services/notification_service.py`).

### 9.1 Triggering Events
- **`DRIFT_WARNING`:** Generated when single-stock drift $> 5\\%$ or total drift $> 15\\%$.
- **`REBALANCE_AVAILABLE`:** Generated when a new rebalancing schedule has been computed and awaits client review.
- **`REGIME_CHANGE`:** Generated when the market transitions into `HIGH_VOLATILITY` or `BEAR_TREND`.
- **`PORTFOLIO_GENERATED`:** Dispatched upon completion of multi-agent generation.

### 9.2 Notification Lifecycle
1. Notification row inserted into `notifications` table (`is_read = False`).
2. Client navbar polls `/api/v1/notifications/unread-count` and displays badge indicator.
3. User opens notification flyout panel (`NotificationsPanel.tsx`).
4. User clicks notification; marked as read via `PUT /api/v1/notifications/{id}/read`.

---

## 10. Methodology Diagrams & Flow Visualizations

The complete visual flow diagram is maintained in [METHODOLOGY_FLOW.mmd](file:///Users/ankur/Documents/MajorProject/app/METHODOLOGY_FLOW.mmd), rendered as [METHODOLOGY_FLOW.png](file:///Users/ankur/Documents/MajorProject/app/METHODOLOGY_FLOW.png) and vector SVG.
""")

    print(f"METHODOLOGY.md successfully built: {out_file.stat().st_size:,} bytes.")

if __name__ == "__main__":
    build_methodology()
