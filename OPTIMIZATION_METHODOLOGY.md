# Lucid — Mathematical & Portfolio Optimization Methodology

This document details the rigorous financial formulas, mathematical models, optimization algorithms, and execution invariants implemented across Lucid's portfolio engine.

---

## 1. Portfolio Optimization Formulation (Markowitz SLSQP)

Lucid executes deterministic mean-variance optimization locally in Python using `scipy.optimize.minimize` with the **Sequential Least Squares Programming (SLSQP)** algorithm (`backend/portfolio_engine/optimizer.py`).

### Mathematical Objective Function
The optimizer minimizes the negative risk-adjusted quadratic utility:

$$\min_{w} \quad \mathcal{U}(w) = \frac{1}{2} \lambda \cdot w^T \Sigma w - \mu^T w$$

Where:
- $w = [w_1, w_2, \dots, w_n]^T$: Vector of candidate allocation weights.
- $\lambda$: Investor-specific risk aversion parameter derived from psychometric profiling:
  - **Conservative**: $\lambda = 5.0$
  - **Moderate**: $\lambda = 3.5$
  - **Aggressive**: $\lambda = 2.0$
- $\Sigma \in \mathbb{R}^{n \times n}$: Sample covariance matrix computed from annualized asset return volatilities and pairwise sector correlations:
  $$\Sigma_{ij} = \sigma_i \sigma_j \rho_{ij}$$
  where $\rho_{ii} = 1.0$, intra-sector correlation $\rho_{ij} = 0.50$, and cross-sector correlation $\rho_{ij} = 0.20$. A small Tikhonov regularization term ($\epsilon = 10^{-6} \mathbf{I}$) is added along the diagonal to ensure positive definiteness.
- $\mu = [E[R_1], E[R_2], \dots, E[R_n]]^T$: Vector of expected annualized asset returns.

### Hard Institutional Constraints
1. **Full Investment (Simplex Budget Equality)**:
   $$\sum_{i=1}^n w_i = 1.0 \quad (100.0\%)$$
2. **Long-Only Asset Bounds (No Short Selling)**:
   $$0.0 \le w_i \le w_{\max} \quad \forall i \in \{1, \dots, n\}$$
   where $w_{\max} = 10.0\%$ for moderate portfolios ($15.0\%$ for aggressive).
3. **Sector Concentration Inequality Constraints**:
   $$\sum_{i \in \text{Sector}_k} w_i \le S_{\max} \quad \forall k \in \{1, \dots, K\}$$
   where $S_{\max} = 30.0\%$ for moderate portfolios ($35.0\%$ for aggressive).

### Deterministic Constrained Fallback Solver
If the SLSQP numerical solver fails to converge due to tight boundary conditions, Lucid executes an **Iterative Sector-Constrained Water-Filling Algorithm** (`_sector_constrained_fallback`):
- Checks feasibility: Verifies that the candidate universe contains at least $\lceil 1 / S_{\max} \rceil$ distinct sectors.
- Iteratively allocates incremental weights $\Delta w = \min(\text{remaining} / m, w_{\max} - w_i, S_{\max} - S_k)$ across eligible assets until the simplex sum strictly equals $1.0$.
- Returns explicit mathematical infeasibility if constraints cannot be satisfied without violating caps.

---

## 2. Integer Share Allocation & Cash Conservation Invariant

Real-world Indian retail equities cannot be purchased in fractional shares. Lucid translates continuous decimal weights into discrete integer lots while preserving total capital (`backend/portfolio_engine/allocation_rounding.py`).

### Integer Lot Formula
$$\text{Target Capital}_i = \text{Total Investment Amount} \times \left(\frac{w_i}{100.0}\right)$$
$$\text{Shares Quantity}_i = \left\lfloor \frac{\text{Target Capital}_i}{\text{Latest Price}_i} \right\rfloor$$
$$\text{Actual Invested Amount}_i = \text{Shares Quantity}_i \times \text{Latest Price}_i$$

### Strict Cash Invariant
$$\text{Total Invested} = \sum_{i=1}^n \text{Actual Invested Amount}_i$$
$$\text{Unallocated Cash} = \text{Total Investment Amount} - \text{Total Invested}$$

**Mathematical Invariant**:
$$\text{Total Invested} + \text{Unallocated Cash} \equiv \text{Total Investment Amount}$$
$$\text{Unallocated Cash} \ge 0.00 \quad \text{(No negative cash balance / no uncollateralized margin)}$$

---

## 3. Financial Metrics & Econometric Formulas

Implemented in `backend/portfolio_engine/math_engine.py`:

### 3.1 Earnings Yield ($E/P$)
Handles operating losses and extreme valuations gracefully:
$$\text{Earnings Yield} = \begin{cases} 
\min\left(\frac{1.0}{\text{P/E}}, 0.50\right) & \text{if } \text{P/E} > 0 \\[6pt]
\max\left(\frac{1.0}{\text{P/E}}, -0.25\right) & \text{if } \text{P/E} < 0 \text{ (Operating Losses)} \\[6pt]
\text{None} & \text{if } \text{P/E} = 0 \text{ or missing}
\end{cases}$$

### 3.2 Compounded Annual Growth Rate (CAGR)
Computed using exact day-count fractions based on Indian trading days ($252$ days/year):
$$\text{CAGR} = \left(\frac{\text{Price}_{T}}{\text{Price}_{0}}\right)^{\frac{252}{D}} - 1.0$$
where $D$ is the number of actual trading days observed ($D \ge 30$).

### 3.3 Systematic Beta & Total Annualized Volatility
Treated as distinct risk dimensions:
$$\text{Total Volatility } (\sigma_i) = \text{Std}(R_i) \times \sqrt{252}$$
$$\text{Systematic Beta } (\beta_i) = \frac{\text{Cov}(R_i, R_{\text{benchmark}})}{\text{Var}(R_{\text{benchmark}})}$$
Requires at least $60$ daily trading observations.

### 3.4 Winsorized Sector-Relative Z-Scores
Protects factor models against extreme corporate outliers:
1. Clip metric values at the 5th percentile ($q_{0.05}$) and 95th percentile ($q_{0.95}$):
   $$\tilde{x}_i = \text{clip}(x_i, q_{0.05}, q_{0.95})$$
2. Compute sector mean $\mu_{\text{sec}}$ and standard deviation $\sigma_{\text{sec}}$.
3. Compute clamped Z-score:
   $$Z_i = \text{clip}\left(\frac{\tilde{x}_i - \mu_{\text{sec}}}{\sigma_{\text{sec}}}, -3.0, +3.0\right)$$

### 3.5 Expected Annual Return Formula
Strictly distinguished from unitless factor Z-scores; blends CAPM systematic risk premium with multi-factor alpha tilts:

$$E[R_i] = R_{\text{base}} + 1.20 \cdot (w_q Z_{q,i} + w_v Z_{v,i} + w_m Z_{m,i}) + 1.50 \cdot (\beta_i - 1.0)$$

Where:
- $R_{\text{base}}$: Base return target (e.g. $12.5\%$ for moderate).
- $w_q, w_v, w_m$: Goal-specific factor loadings (Quality, Value, Momentum) summing to $1.0$.
- Result is bounded within the institutional corridor $[4.0\%, 30.0\%]$.

---

## 4. Portfolio Monitoring & Drift Formulas

Implemented in `backend/portfolio_engine/monitoring_service.py` and `rebalancing_service.py`:

### Asset Allocation Drift
$$\text{Holding Drift}_i = \text{Current Weight}_i - \text{Target Weight}_i$$
Trigger condition: $|\text{Holding Drift}_i| \ge 5.0\%$.

### Sector Allocation Drift
$$\text{Sector Drift}_k = \sum_{i \in \text{Sector}_k} \text{Current Weight}_i - \sum_{i \in \text{Sector}_k} \text{Target Weight}_i$$
Trigger condition: $|\text{Sector Drift}_k| \ge 8.0\%$.

### Rebalancing Turnover Metric
$$\text{Turnover} = \frac{1}{2} \sum_{i=1}^n |w_{\text{post}, i} - w_{\text{current}, i}|$$

---

## 5. Indian Statutory Equity Transaction Costs

Implemented in `backend/portfolio_engine/transaction_costs.py`:

| Fee Component | Statutory Rate | Tax Base |
|---|---|---|
| **Securities Transaction Tax (STT)** | 0.10% | Total delivery trade turnover (BUY and SELL) |
| **Exchange Transaction Charges (NSE)** | 0.00297% | Total trade turnover |
| **SEBI Turnover Fee** | 0.0001% (₹10 per crore) | Total trade turnover |
| **Goods & Services Tax (GST)** | 18.0% | On (Brokerage + Exchange Fees + SEBI Fees) |
| **Stamp Duty** | 0.015% (₹1500 per crore) | On delivery BUY trade value only |
| **Brokerage** | Flat ₹20 or 0.03% | Per executed trade order |
