# Lucid — Technical & Financial Glossary
## A Beginner-Friendly Master Reference for Core AI, Quantitative & Financial Terms

---

### 1. Agentic AI
- **Definition**: Artificial Intelligence systems that do not merely generate text in response to a single prompt, but autonomously perceive their environment, reason through intermediate goals, use specialized tools, validate their own outputs, and adapt their actions iteratively.
- **Lucid Context**: In Lucid, our 13-node LangGraph system acts agentically: when the Critic rejects a portfolio due to risk concentration, the system does not fail or stop; it autonomously triggers a rework cycle to replace the violating stocks before presenting the solution to the user.

### 2. LangGraph
- **Definition**: A stateful orchestration framework developed by LangChain that models multi-agent workflows as directed computational graphs. It supports cyclical execution loops, conditional state branching, and strongly-typed shared state.
- **Lucid Context**: Lucid's core reasoning pipeline is compiled as a `StateGraph` in `backend/agent/graph.py`, managing the coordination between our 13 specialist agents and the quantitative solver.

### 3. Markowitz Mean-Variance Optimization
- **Definition**: A Nobel Prize-winning mathematical framework introduced by Harry Markowitz in 1952. It demonstrates that an investor can construct an 'efficient frontier' of portfolios that maximizes expected return for a given level of risk (variance) through diversification.
- **Lucid Context**: Implemented in `backend/portfolio_engine/optimizer.py`, where SciPy solves the quadratic utility equation: $\min_{\mathbf{w}} \frac{1}{2} \lambda \mathbf{w}^T \mathbf{\Sigma} \mathbf{w} - \mathbf{\mu}^T \mathbf{w}$.

### 4. Covariance Matrix ($\mathbf{\Sigma}$)
- **Definition**: A square mathematical matrix containing the pairwise covariances between every asset in an investment universe. It measures the degree to which asset prices move together.
- **Lucid Context**: Lucid computes the annualized covariance matrix from 252 trading days of daily historical log returns to identify non-correlated equities that reduce overall portfolio risk.

### 5. SciPy SLSQP Solver
- **Definition**: Sequential Least Squares Programming (`SLSQP`) is a numerical optimization algorithm in Python's SciPy library designed to minimize constrained non-linear objective functions with bounds and equality/inequality constraints.
- **Lucid Context**: Lucid uses SLSQP to compute optimal equity weights in under 50 milliseconds while enforcing our 25% single-stock and 40% sector caps.

### 6. Integer Whole-Share Lots ($Q_i \in \mathbb{Z}_{\ge 0}$)
- **Definition**: The legal and technical requirement that securities must be traded in discrete whole units (e.g., 1, 5, or 10 shares) rather than continuous fractions (e.g., 2.37 shares).
- **Lucid Context**: Indian stock exchanges (NSE and BSE) trade exclusively in integer shares. Lucid's floor-and-greedy rounding algorithm ensures that every recommendation is an exact integer lot that can actually be executed on a retail broker.

### 7. Cash Reserve / Unallocated Cash ($C \ge 0$)
- **Definition**: The liquid cash balance remaining in an investment account that is not allocated to equity holdings.
- **Lucid Context**: When integer share rounding leaves a residual cash amount insufficient to buy an additional whole share without violating risk caps, Lucid preserves that capital as an unallocated liquid cash reserve. Cash is guaranteed never to be negative ($C \ge 0$).

### 8. India VIX (`^INDIAVIX`)
- **Definition**: The volatility index calculated by the National Stock Exchange of India (NSE). It measures market expectations of near-term volatility based on Nifty 50 index options prices. Often called the market's 'fear gauge'.
- **Lucid Context**: Lucid queries `^INDIAVIX` live to classify market regimes: values below 13 are Calm, 13–18 are Moderate, 18–24 are Volatile, and above 24 are Extreme.

### 9. Market Regime
- **Definition**: The prevailing macroeconomic or volatility environment governing financial markets (e.g., bull market, high inflation, extreme volatility).
- **Lucid Context**: In `backend/market_data/regime.py`, Lucid dynamically detects market regimes to adjust agent recommendations: volatile regimes automatically prompt defensive tilts toward healthcare and consumer staples.

### 10. Portfolio Drift
- **Definition**: The gradual divergence between a portfolio's current asset weights and its original target weights caused by unequal price movements among holdings over time.
- **Lucid Context**: If Stock A rises 50% while Stock B drops 20%, Stock A's percentage of the portfolio increases, exposing the investor to unintended risk. Lucid tracks this drift daily.

### 11. Rebalancing
- **Definition**: The disciplined financial practice of periodically buying and selling portions of portfolio assets to restore the original target asset allocation and risk profile.
- **Lucid Context**: When single-stock drift exceeds 5% or sector drift exceeds 10%, Lucid generates a whole-share rebalance plan showing exactly how many shares to sell or buy to realign the portfolio.

### 12. Non-Custodial Architecture
- **Definition**: A software design model where the application never takes physical or legal possession of user assets, never holds client money, and does not maintain trading access to broker accounts.
- **Lucid Context**: Lucid is 100% non-custodial. It provides fiduciary advice, trade order slips, and CSV baskets, but the investor retains complete control and executes the trades on their own broker terminal.

### 13. Securities Transaction Tax (STT)
- **Definition**: A direct tax levied by the Government of India on every purchase and sale of securities listed on recognized Indian stock exchanges.
- **Lucid Context**: Lucid models STT at 0.10% on both Buy and Sell delivery equity transactions, displaying the exact tax amount in the Rebalance Preview modal.

### 14. Demat Account
- **Definition**: Short for 'Dematerialized Account'. An electronic account used in India to hold securities and shares in digital format, maintained by depositories (NSDL or CDSL).
- **Lucid Context**: Lucid's Demat Diagnosis module allows investors to upload statements from any Indian Demat account (Zerodha, Groww, AngelOne) to audit their portfolio health.

### 15. Risk Aversion Parameter ($\lambda$)
- **Definition**: A quantitative scaling factor in utility theory that reflects how strongly an investor dislikes volatility relative to potential gains.
- **Lucid Context**: Lucid maps investor risk profiles to lambda values: 8.0 for Very Conservative investors (heavily penalizes risk) down to 0.8 for Very Aggressive investors (favors returns).

### 16. Sharpe Ratio
- **Definition**: A financial metric that measures the risk-adjusted return of an investment portfolio: $\text{Sharpe} = (R_p - R_f) / \sigma_p$, where $R_f$ is the risk-free rate.
- **Lucid Context**: Lucid calculates the Sharpe ratio using the India 10-Year Benchmark G-Sec yield as the risk-free rate, evaluating how much excess return is generated per unit of volatility.

### 17. Return on Equity (ROE)
- **Definition**: A fundamental financial ratio calculated by dividing net profit by shareholders' equity. It measures how efficiently a company uses investors' capital to generate earnings.
- **Lucid Context**: Lucid's Fundamental Analyst agent screens for high-quality companies with sustainable ROE exceeding 15%.

### 18. Debt-to-Equity Ratio (D/E)
- **Definition**: A financial leverage ratio calculated by dividing total liabilities by shareholder equity. It reflects how much debt a company uses to finance its operations.
- **Lucid Context**: In non-financial companies, Lucid filters for low-debt companies ($D/E < 0.5$) to protect retail investors from solvency risk during interest rate hikes.

### 19. Price-to-Earnings Ratio (P/E)
- **Definition**: A valuation metric comparing a company's current share price to its per-share earnings.
- **Lucid Context**: Lucid compares a company's trailing P/E against its 5-year industry median in the 'Why This Stock' modal to assess whether the stock is reasonably valued or overhyped.

### 20. Tracing & Observability
- **Definition**: In software and AI systems, the practice of recording detailed, timestamped execution paths for every function, agent prompt, tool call, and decision.
- **Lucid Context**: Lucid logs complete execution traces in the `agent_traces` table in PostgreSQL, allowing auditors to inspect the exact reasoning path of every portfolio generation request.

### 21. Multi-Tenant Isolation
- **Definition**: An architectural security design where multiple users share the same database infrastructure, but software-level barriers guarantee that no tenant can ever view or manipulate another tenant's data.
- **Lucid Context**: Lucid achieves multi-tenant isolation through composite unique constraints on `(portfolio_id, user_id)` and verified JWT identity extraction on every API call.

### 22. Argon2id
- **Definition**: A state-of-the-art cryptographic password-hashing function that won the Password Hashing Competition. It is memory-hard, making it exceptionally resistant to GPU and ASIC brute-force attacks.
- **Lucid Context**: Lucid uses Argon2id via `argon2-cffi` to hash all investor passwords in `backend/api/v1/auth.py`.

### 23. Stateless JWT (JSON Web Token)
- **Definition**: An open standard (RFC 7519) for securely transmitting authenticated claims between parties as a compact, digitally signed JSON object.
- **Lucid Context**: Lucid issues stateless JWTs upon login. To handle logout and security invalidations, revoked token identifiers (JTIs) are stored in an active blacklist in PostgreSQL.

### 24. SEBI Suitability Guidelines
- **Definition**: Regulatory rules established under the SEBI (Investment Advisers) Regulations, 2013, requiring investment advisors to evaluate client risk capacity, financial horizon, and investment experience before recommending products.
- **Lucid Context**: Lucid's Suitability Node (Node 2) implements SEBI-aligned risk assessment, ensuring high-risk equities are not recommended to capital-preservation investors.

### 25. Account Aggregator (AA)
- **Definition**: A financial entity licensed by the Reserve Bank of India (RBI) that facilitates the secure, consent-based digital sharing of financial data between institutions.
- **Lucid Context**: Lucid's production roadmap incorporates Account Aggregators (Setu, Finvu) to allow investors to sync their Demat holdings directly from CDSL and NSDL with a single OTP.

### 26. Turnaround / Turnover Ratio
- **Definition**: The total volume of purchases and sales divided by the total portfolio valuation during a rebalancing event, expressed as a percentage.
- **Lucid Context**: Lucid calculates rebalancing turnover to ensure that minor price drift does not trigger high turnover that erodes investor capital through unnecessary transaction costs.

### 27. Dividend Yield
- **Definition**: The ratio of a company's annual dividend payments relative to its stock price, expressed as a percentage.
- **Lucid Context**: Evaluated by the Demat Diagnosis module to determine whether an investor's portfolio provides consistent income or lags behind the Nifty 50 benchmark yield.

### 28. Beta ($\beta$)
- **Definition**: A measure of a stock's or portfolio's volatility in relation to the overall market (e.g., Nifty 50). A beta of 1.0 indicates market-matching volatility; a beta $< 1.0$ indicates lower volatility.
- **Lucid Context**: In volatile regimes, Lucid tilts candidate selection toward low-beta equities ($\beta < 0.85$) to reduce drawdowns.

### 29. Bounded Rework Loop
- **Definition**: An iterative algorithmic structure with a fixed upper bound on execution cycles, preventing runaway computational costs or infinite loops.
- **Lucid Context**: Implemented between the Critic and Strategist Rework nodes with an invariant `rework_count <= 2`.

### 30. Fiduciary Duty
- **Definition**: The legal and ethical obligation to act solely in the best financial interest of the client, maintaining transparency, avoiding conflicts of interest, and disclosing all costs.
- **Lucid Context**: Lucid's fiduciary philosophy mandates transparent two-level explanations, zero affiliate commissions, and full disclosure of transaction costs before rebalancing.

### 31. Single-Stock Concentration Cap (25%)
- **Definition**: Lucid's internal house policy establishing that no individual equity holding may exceed 25.0% of an investor's total portfolio equity valuation.
- **Lucid Context**: Centralized in `backend/portfolio_engine/policy.py` and strictly enforced by both the SLSQP solver and the Critic agent.

### 32. Sector Concentration Cap (40%)
- **Definition**: Lucid's internal house policy dictating that the aggregate allocation across all equities in any single industry sector cannot exceed 40.0% of total portfolio valuation.
- **Lucid Context**: Prevents catastrophic exposure to single-sector shocks (e.g., IT downturn or regulatory changes in BFSI).

### 33. Simplex Constraint ($\sum w_i = 1$)
- **Definition**: The mathematical condition in portfolio optimization requiring that the sum of all individual asset weights must exactly equal 100% of available investment capital.
- **Lucid Context**: Configured as an equality constraint in SciPy SLSQP to prevent unallocated mathematical voids.

### 34. Dynamic Company Resolution
- **Definition**: An algorithmic technique using trigram fuzzy matching and Levenshtein distance to resolve colloquial company names to their official exchange ticker symbol.
- **Lucid Context**: Enables Lucid to correctly map an input like 'Tata Motors' or 'TCS' to its corresponding NSE scrip symbol without relying on hardcoded dictionaries.

### 35. Frictional Costs
- **Definition**: The unavoidable economic costs incurred when trading financial assets, including exchange transaction fees, broker commissions, depository fees, and statutory taxes.
- **Lucid Context**: Accurately quantified by Lucid's transaction cost engine so investors understand the exact net cash impact of every proposed rebalance.

---
*Lucid Technical & Financial Glossary — Version 2026.11-v2.0*

