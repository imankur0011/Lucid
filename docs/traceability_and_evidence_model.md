# End-to-End Traceability, Evidence Schema, and Neuro-Symbolic Decoupling
**Application:** Arthava (Intelligent Portfolio Creation & Rebalancing Engine)  
**Document:** `docs/traceability_and_evidence_model.md`  
**Standard:** Complete Fiduciary Traceability with Zero Implementation Leakage

---

## 1. The End-to-End Fiduciary Traceability Chain

Arthava implements an unbroken, auditable link from an investor's first questionnaire answer to the final whole-share allocation:

```mermaid
flowchart TD
    A[1. Investor Goals & Capital] --> B[2. Fiduciary Constraints & Risk Band]
    B --> C[3. Market Data & Corporate Filings]
    C --> D[4. Eligibility Filter & Exclusion Screening]
    D --> E[5. Deterministic SLSQP Optimization]
    E --> F[6. Integer Share Rounding & Cash Balance Invariant]
    F --> G[7. Deterministic Constraint & Safety Verification]
    G --> H[8. Immutable Version Snapshot Saved]
    H --> I[9. Plain-Language Explanation & Evidence Grounding]

    subgraph Investor Visible Outcomes
        I --> J[Level 1: Plain-English Fiduciary Summary]
        I --> K[Level 2: Audited Metric Citations & Safety Badges]
    end

    subgraph Protected Developer Audit Trail (Never in Investor UI)
        H -.-> L[Database Provenance Hash & Software Commit ID]
        E -.-> M[Solver Convergence Logs & Optimization Matrix]
    end
```

### Stage-by-Stage Traceability Description

| Stage | Input Parameters | Processing & Transformation | Output Artifact | Investor-Visible Representation |
| :--- | :--- | :--- | :--- | :--- |
| **1. Goals & Capital** | Rupee Budget $B$, Time Horizon, Financial Goal | Sanitization, currency parsing, integer clamping | Structured User Profile Record | Summary card displaying Capital and Horizon |
| **2. Constraints & Risk** | Risk Questionnaire answers, single-stock cap $u_i$, sector cap $S_k$, ethical exclusions | Risk capacity scoring ($[1, 5]$); volatility bounds ($[8\%, 22\%]$) | Fiduciary Constraint Vector | Displayed guardrails: *"Max 25% per stock, Max 40% per sector"* |
| **3. Market Data & Evidence** | Closing prices $p_i$, historical covariance $\Sigma$, audited fundamentals (PE, ROE, D/E) | Data freshness verification ($\Delta t < 24$h), zero-price / anomaly detection | Verified Universe Matrix | Date stamps: *"Market data observed 30 Sept 2026"* |
| **4. Eligibility Screening** | Excluded sectors/tickers, market cap minimums | Boolean exclusion mask ($M_{elig} \in \{0, 1\}^N$) | Eligible Asset Universe | Exclusion confirmation: *"Tobacco and Defense excluded"* |
| **5. Deterministic SLSQP** | Eligible covariance $\Sigma_{sub}$, expected returns $\mu$, risk aversion $\lambda$ | Scipy SLSQP quadratic optimization subject to linear constraints | Optimal Continuous Weights $w_i^*$ | Visual weight breakdown (%) |
| **6. Whole-Share Rounding** | Continuous weights $w_i^*$, Budget $B$, Share prices $p_i$ | Whole-share floor calculation: $q_i = \lfloor w_i^* B / p_i \rfloor$ | Integer quantities $q_i$, Cash reserve $C_{rem}$ | Executable holdings table with whole share counts |
| **7. Safety Verification** | Rounded holdings $q_i$, prices $p_i$, user caps $u_i, S_k$ | Deterministic invariant check: $C_{rem} \geq 0$, $\sum p_i q_i + C_{rem} = B$ | Validation Status: `PASS` / `FAIL` | Safety verification badges (all green checks) |
| **8. Version Persistence** | Validated portfolio instance, user ID, timestamp | UUID generation, relational persistence in PostgreSQL | Version Snapshot Record | Version badge (e.g., *"Version #2 — 18 Oct 2026"*) |
| **9. Evidence Grounding** | Holding data + audited fundamental facts | Synthesis of plain-English rationale citing verified metrics | Fiduciary Explanation Package | Plain-language rationale cards with audited citation pills |

---

## 2. Evidence Metadata Schema

Every empirical financial fact presented to an investor or used in selection rationale conforms to the structured evidence schema below:

```json
{
  "evidence_id": "EVID-NSE-RELIANCE-2026Q2-ROE",
  "subject_symbol": "RELIANCE",
  "company_name": "Reliance Industries Limited",
  "metric_name": "Return on Equity (ROE)",
  "metric_category": "OBSERVED_FACT",
  "raw_value": 18.4,
  "unit": "PERCENTAGE",
  "source_name": "NSE Audited Financial Filings",
  "source_type": "REGULATORY_FILING",
  "source_reference_url": "https://www.nseindia.com/corporate-filings",
  "observation_date": "2026-09-30",
  "retrieval_timestamp": "2026-10-18T09:30:00Z",
  "freshness_status": "CURRENT",
  "quality_flag": "AUDITED_VERIFIED",
  "associated_claim": "Demonstrates resilient operating efficiency and sustained return on equity above 18% over trailing 12 months.",
  "provenance_notes": "Derived from consolidated trailing twelve-month profit attributable to owners divided by average shareholder equity."
}
```

### Classification of Financial Information

To prevent misrepresenting estimates as facts, every piece of content shown to investors is strictly tagged into one of seven clear epistemological categories:

| Category | Definition | Investor-Facing Label | Example |
| :--- | :--- | :--- | :--- |
| **1. Observed Facts** | Objective, historical financial data from official regulatory filings or exchange feeds. | **Audited Fact** | *"Q2 FY26 Net Profit: ₹19,250 Cr (NSE Filing)"* |
| **2. Derived Metrics** | Values computed using standard, deterministic mathematical formulas from observed facts. | **Calculated Ratio** | *"Price-to-Earnings Ratio: 24.2"* |
| **3. Assumptions** | Baseline conditions or hypothetical parameters used to define the optimization model. | **Model Assumption** | *"Assumes an annual risk-free rate of 6.8% (India 10Y G-Sec)"* |
| **4. Explicit Rules** | Strict fiduciary boundaries and user-specified guardrails that the portfolio cannot cross. | **Safety Guardrail** | *"Single-stock limit: Max 25% of total capital"* |
| **5. Model Estimates** | Statistically inferred figures generated by quantitative models (e.g., CAPM expected return). | **Statistical Estimate** | *"Expected Annual Return: 12.8% (Historical Covariance Model)"* |
| **6. Interpretations** | Plain-English explanations describing why a company or allocation fits the investor's situation. | **Fiduciary Explanation** | *"Chosen as a core compounder to anchor portfolio stability during market corrections."* |
| **7. Limitations** | Explicit conditions, missing data, or uncertainties that constrain the conclusions. | **Important Limitation** | *"Historical volatility does not guarantee future drawdown protection."* |

---

## 3. Strict Neuro-Symbolic Decoupling (AI-Math Separation)

Arthava enforces a non-negotiable architectural boundary: **Generative AI components are never allowed to perform financial arithmetic or determine numerical asset weights.**

```
+--------------------------------------------------------------------------+
|                       STRICT ARCHITECTURAL BOUNDARY                      |
+--------------------------------------------------------------------------+
|  GENERATIVE AI LAYER (LLM)                  DETERMINISTIC NUMERICAL ENGINE|
|  - Natural language parsing                 - Scipy SLSQP Quadratic Optimizer|
|  - Qualitative investment thesis            - Whole-share rounding algorithm  |
|  - Plain-English translation                - Invariant constraint validator  |
|  - Educational term explanations            - Covariance matrix calculations  |
|                                                                          |
|  ❌ STRICTLY FORBIDDEN FOR LLM:             ✅ DETERMINISTIC GUARANTEES:   |
|  - Calculating portfolio weights            - Weights strictly sum to 1.0     |
|  - Computing cash balances                  - Non-negative cash balance       |
|  - Inventing P/E or ROE ratios              - Zero constraint violations      |
|  - Altering mathematical outputs            - Post-rounding budget check      |
+--------------------------------------------------------------------------+
```

### Verification Against Hallucinations & Inconsistencies

Before any generated explanation is rendered to an investor, a deterministic validator checks that:
1. **Numeric Consistency:** Every financial number mentioned in the written text matches the database value to within $\pm 0.1\%$.
2. **Holding Alignment:** The text only references companies that actually exist in the final optimized holdings table.
3. **Citation Integrity:** Every metric cited is linked to an existing `evidence_id` with an observation date $\leq 365$ days old.
4. **Resolution of Discrepancies:** If the LLM generates a claim that contradicts the numerical output, the system **blocks** the text, falls back to a standardized deterministic template, and logs an internal warning.

---

## 4. Audit Trail, Versioning, and Reproducibility

### Definition of Reproducibility
A portfolio recommendation in Arthava is defined as **Reproducible within declared numerical tolerance ($\epsilon = 10^{-4}$)** if, given the recorded inputs:
$$\{ B, \text{Horizon}, \text{RiskScore}, u_i, S_k, \text{Exclusions}, \text{MarketDataSnapshotId} \}$$
the system recalculates identical integer holdings $\{ q_1, \dots, q_n \}$ and identical cash balance $C_{rem}$.

### Version Snapshot Schema (Database Model)
- `portfolio_id`: Primary UUID.
- `user_id`: Foreign key linking to authenticated investor.
- `version_number`: Monotonically increasing integer per user (v1, v2, v3).
- `created_at`: Immutable UTC timestamp.
- `input_hash`: Cryptographic SHA-256 hash of all user parameters and constraints.
- `market_data_snapshot_id`: Reference to exact historical price and covariance records used.
- `allocations`: JSON array of target weights, integer share quantities, and reference prices.
- `cash_buffer`: Exact unallocated cash reserve.
- `validation_outcome`: JSON payload confirming all passed mathematical constraints.
- `explanation_text`: Plain-English narrative generated for this version.
