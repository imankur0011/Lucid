# Market Data Policy, Licensing, and Attribution Guide

## 1. Regulatory & Licensing Scope
- **Current Operational Mode:** Academic & Educational Research Demonstration.
- **Providers Configured:**
  - `SimulatedMarketProvider`: Deterministic pseudo-random historical prices tailored for automated CI testing, reproducibility, and offline evaluation.
  - `YFinanceProvider`: Prototype historical quote retriever intended strictly for personal research and educational development.
- **Commercial Disclaimer:**
  > [!WARNING]
  > Public or commercial deployment providing live securities recommendations or data redistribution requires an authorized data feed licensing agreement directly from the National Stock Exchange of India (NSE) or Bombay Stock Exchange (BSE), or an authorized broker/data vendor (e.g., Upstox API with appropriate commercial tier).

---

## 2. Ingestion & Quality Rules Reference

| Rule Code | Description | Handling Policy |
| :--- | :--- | :--- |
| `POSITIVE_TRADED_PRICE` | Close and open prices must be strictly $> 0$ | Record rejected; logged in `data_ingestion_errors`. |
| `HIGH_LOW_INVERSION` | High price must be $\ge$ Low price | Record rejected. |
| `PRICE_IN_RANGE` | Open and Close must be within $[Low, High]$ | Record rejected if out of range. |
| `NON_NEGATIVE_VOLUME` | Traded shares volume must be $\ge 0$ | Ingestion default set to 0 if null. |
| `NON_FUTURE_DATE` | Price date cannot exceed current date | Record rejected. |
| `STALE_PRICE_GUARD` | Data older than 7 calendar days flagged | Portfolio engine rejects candidate or issues warning. |
| `ADJUSTED_PRICE_POLICY` | Both raw Close and Adjusted Close stored | Optimization algorithms operate on split/dividend adjusted prices; trade share sizing operates on unadjusted traded Close. |

---

## 3. Provider Failover and Resiliency
- Ingestion runs record exact execution status (`succeeded`, `partial`, `failed`) and row counts in `data_ingestion_runs`.
- Database upserts use `ON CONFLICT (listing_id, price_date, data_source_id) DO UPDATE` to guarantee idempotency across retries.
