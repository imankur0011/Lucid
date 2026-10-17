# Canonical System Inventory & Architecture Specification

**Project:** SAMRUDDHI — Intelligent Portfolio Creation & Rebalancing Engine  
**Version:** Release Hardened v1.0 (Phase 1 Baseline)  
**Database Schema:** PostgreSQL 16 (60 Relational Tables: 59 Application Tables + `alembic_version`)  
**Test Suite:** 42 Pytest Automated Unit/Security/Concurrency Tests + 7 Playwright E2E Browser Journey Tests  

---

## 1. Database Schema Inventory (60 Relational Tables)

### A. Core Master & Security Universe (12 Tables)
1. `app_users`: User identities, auth provider subjects, roles, and timestamps.
2. `companies`: Corporate issuers and company metadata.
3. `securities`: Equity securities, ISIN, asset class definitions.
4. `exchanges`: Exchange master (NSE, BSE).
5. `instrument_listings`: Ticker symbols per exchange with active trading flags.
6. `sectors`: Broad macroeconomic sectors (e.g. Technology, Energy, Banking).
7. `industries`: Detailed industry classifications.
8. `company_sector_memberships`: M2M mapping of companies to sectors.
9. `market_prices`: Historical adjusted close, open, high, low, volume time-series.
10. `corporate_actions`: Dividends, stock splits, bonus shares tracking.
11. `index_definitions`: Benchmark index master (e.g. NIFTY 50, NIFTY 500).
12. `index_constituents`: Index membership weights and effective dates.

### B. Investor Profiling & Risk Assessment (8 Tables)
13. `investor_profiles`: User profile snapshot, investment horizon, experience level.
14. `risk_questions`: Active questionnaire questions with category and weight metadata.
15. `risk_question_options`: Selectable response options with calibrated risk scores.
16. `risk_assessments`: Assessment runs with computed tolerance, capacity, and final category.
17. `risk_assessment_answers`: Individual submitted question-option answers.
18. `risk_tolerance_history`: Historical tolerance score tracking over time.
19. `investor_constraints`: Investor custom constraints (forbidden securities/sectors).
20. `investor_kyc_records`: KYC verification status and regulatory compliance records.

### C. Portfolio Management & Versions (10 Tables)
21. `investor_portfolios`: High-level portfolio container per user.
22. `portfolio_versions`: Immutable generated portfolio versions (v1, v2, ...).
23. `portfolio_allocations`: Optimal security allocations (target weight %, shares quantity, price snapshot).
24. `portfolio_metrics`: Evaluated Sharpe ratio, expected return, volatility, and diversification scores.
25. `portfolio_constraints`: Execution constraints (min stocks, max stock %, max sector %).
26. `portfolio_strategies`: Qualitative strategy rationale and macro stance.
27. `portfolio_validation_runs`: Deterministic safety gate evaluation logs.
28. `portfolio_validation_items`: Individual rule results (`POST_ROUNDING_STOCK_CAP`, `BUDGET_OVERRUN_PROTECTION`, etc.).
29. `portfolio_cash_balances`: Unallocated liquid cash reserve tracking.
30. `portfolio_rebalance_events`: Historical rebalance triggers and execution records.

### D. Multi-Agent Reasoning & Explainability (10 Tables)
31. `agent_execution_traces`: High-level workflow orchestration runs.
32. `agent_execution_steps`: Per-agent step records (Manager, Analyst, Optimizer, Critic, Validator, Moderator).
33. `agent_messages`: Inter-agent communication messages and critique logs.
34. `evidence_items`: Grounded citations with source documents and timestamps.
35. `recommendation_explanations`: Structured explanation cards (strategy, sector rationale, hedging).
36. `explanation_evidence_mappings`: M2M linkage between explanations and cited evidence.
37. `critic_evaluations`: Pre-validation agent critique scoring and feedback loops.
38. `agent_tool_calls`: Audit logs of external tools called during generation.
39. `agent_memory_contexts`: Short-term contextual embeddings and graph state.
40. `moderator_reconciliation_logs`: Conflict resolution and trade-off synthesis records.

### E. Financial Goals & Planning (6 Tables)
41. `financial_goals`: Investor goals (Retirement, House, Wealth Creation).
42. `goal_milestones`: Time-based targets and intermediate valuations.
43. `portfolio_goal_allocations`: Mapping of specific portfolios to investor goals.
44. `goal_sip_schedules`: Systematic Investment Plan schedules and projections.
45. `goal_progress_snapshots`: Historical progress snapshots against target amounts.
46. `goal_risk_limits`: Customized risk guardrails per financial goal.

### F. Market Data Pipelines & Ingestion (7 Tables)
47. `data_sources`: Registered provider metadata (NSE, BSE, YFinance, Simulated).
48. `data_ingestion_runs`: Ingestion audit runs with inserted/updated record counts.
49. `data_quality_checks`: Validation checks for stale prices or anomalous outliers.
50. `macro_indicators`: Macro time-series (RBI Repo Rate, CPI Inflation, G-Sec Yield).
51. `market_sentiment_indices`: News and market sentiment indicators.
52. `corporate_earnings`: Fundamental quarterly results, EPS, and revenue metrics.
53. `fundamental_ratios`: Computed valuation ratios (P/E, P/B, ROE, Debt/Equity).

### G. Diagnosis, Rebalancing & System Audit (7 Tables)
54. `existing_user_portfolios`: External existing holdings imported by investors.
55. `existing_portfolio_holdings`: Individual ticker quantities and purchase prices.
56. `portfolio_diagnosis_reports`: Concentration breach diagnostic summaries.
57. `rebalancing_action_plans`: Generated Buy/Sell/Hold integer-share recommendations.
58. `scenario_stress_runs`: Macroeconomic stress simulation runs.
59. `scenario_asset_impacts`: Stressed asset valuations and projected drawdowns.
60. `alembic_version`: Database migration schema version pointer.

---

## 2. Canonical 5-Tier Risk Classification Taxonomy

All services, schemas, database columns, and frontend modules conform strictly to the following 5 categories:

| Category Code | Display Name | Target Return Prior | Single-Stock Cap | Risk Aversion ($\lambda$) | Max Sector Cap | Suitability Rule |
|---|---|---|---|---|---|---|
| `very_conservative` | Very Conservative | 8.0% | 15.0% | 10.0 | 30.0% | Preserves capital; forced if capacity is low |
| `conservative` | Conservative | 10.0% | 20.0% | 6.0 | 35.0% | Low drawdown; prioritized for short horizons |
| `moderate` | Moderate | 12.5% | 25.0% | 3.5 | 40.0% | Balanced growth with multi-sector diversification |
| `growth` | Growth | 15.0% | 25.0% | 2.0 | 40.0% | Equity tilted; capped by application concentration cap (25%) |
| `aggressive` | Aggressive | 18.0% | 25.0% | 1.0 | 40.0% | Maximum return seeking; capped by application concentration cap (25%) |

*Fiduciary Rule:* Investor risk category is constrained by loss capacity: `final_rank = min(tolerance_rank, capacity_rank)`.

---

## 3. Automated Test Suite Verification

### Backend Pytest Suite (42 Tests):
- `backend/tests/test_database.py`: 16 tests (schema relationships, uniqueness constraints, table counts, health aliases).
- `backend/tests/test_investor_api.py`: 4 tests (investor onboarding, risk questions, capacity-constrained suitability rule).
- `backend/tests/test_portfolio_engine.py`: 8 tests (mean-variance optimizer, post-rounding whole-share validation, HHI metrics).
- `backend/tests/test_diagnosis_and_rebalance.py`: 4 tests (Core 06 diagnosis, turnover calculation, whole-share buy/sell previews).
- `backend/tests/test_benchmark_and_comparison.py`: 4 tests (backtest engine, NIFTY 50 proxy, side-by-side delta version comparison).
- `backend/tests/test_auth_and_security.py`: 7 tests (JWT cryptographic verification, fail-closed production mode, tenant isolation, admin protection on ingestion, insecure key startup checks).
- `backend/tests/test_concurrency_and_failures.py`: 3 tests (boundary validation, conflicting constraints, multithreaded concurrent requests).

### Playwright Browser E2E Suite (7 Tests):
- `Module 1`: Dashboard loads with JWT badge and navigation tabs.
- `Module 2`: Portfolio Generator tab exposes capital and constraint parameters.
- `Module 3`: Tab switching to Risk Questionnaire renders 5-factor assessment.
- `Module 4`: Tab switching to Backtest Benchmarks displays comparative analytics.
- `Module 5`: Tab switching to Diagnosis & Rebalancing displays diagnostic tools.
- `Module 6`: Academic & regulatory disclaimer footer is rendered.
- `Module 7`: Interactive Journey — Diagnose existing holdings and render whole-share rebalancing preview with unallocated cash.
