# Comprehensive SEBI Regulatory Research and Compliance Requirements Specification
**Application:** Lucid — Intelligent Investment Portfolio Creation, Analysis & Rebalancing Platform  
**Target Jurisdiction:** Republic of India (Securities and Exchange Board of India — SEBI)  
**Target Market:** Indian Retail & Mass-Affluent Equity Investors  
**Legal Framework Status:** Authoritative Analysis (Regulations, Master Circulars & Amendments as of 2026)  
**Document Classification:** Regulatory Research, Fiduciary Architecture & Engineering Compliance Roadmap  

---

## 1. Executive Summary

### 1.1 Commercial Vision and Regulatory Reality
**Lucid** is engineered to transform retail equity investing in India from unguided speculation and opaque product distribution into an explainable, fiduciary, and mathematically optimized experience. It combines a multi-agent AI architecture, deterministic portfolio optimization, real-time exchange validation, risk diagnosis of imported demat holdings, and an interactive Fiduciary AI Copilot.

A critical legal finding governs Lucid’s roadmap to a commercial launch: **In the Indian securities regime, algorithmic intelligence, personalized risk profiling, and bespoke equity basket generation are strictly regulated activities.** Under the **Securities and Exchange Board of India (Investment Advisers) Regulations, 2013**, any entity that provides personalized investment recommendations on specific securities for consideration must obtain a certificate of registration as an **Investment Adviser (IA)**. 

Operating purely under a technology banner or disclaiming fiduciary responsibility through "educational disclaimers" does not insulate an application from SEBI enforcement if its core user experience generates personalized, ticker-level buy/sell/trim advice.

```
       ┌─────────────────────────────────────────────────────────────┐
       │                   LUCID USER TOUCHPOINTS                    │
       │  • Onboarding & Risk Profiling  • Natural Language Strategy │
       │  • Demat Portfolio Diagnosis    • AI Rebalancing Copilot    │
       └──────────────────────────────┬──────────────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              ▼                                               ▼
┌───────────────────────────┐                   ┌───────────────────────────┐
│     PHASE 1: RESEARCH     │                   │   PHASE 2: COMMERCIAL     │
│   ANALYST (RA) FRAMEWORK  │                   │  INVESTMENT ADVISER (IA)  │
├───────────────────────────┤                   ├───────────────────────────┤
│ • Model Portfolios        │                   │ • Bespoke Suitability     │
│ • Non-Personalized Baskets│                   │ • Personalized Rebalance  │
│ • Research Reports & RPs  │                   │ • Demat Import Diagnosis  │
│ • Capital-Neutral Alphas  │                   │ • Individual Stock Trims  │
│ • Broad Distribution      │                   │ • Bipartite Agreement     │
└───────────────────────────┘                   └───────────────────────────┘
```

### 1.2 Core Legal Findings and Critical Clarifications
1. **The Single-Stock Allocation Fallacy**:
   * *Popular Misconception*: "SEBI caps any individual stock allocation in a retail portfolio at 10% or 25%."
   * *Actual Legal Position*: **SEBI imposes zero legal percentage caps on how an individual Indian retail investor allocates their own private capital across listed equity securities.** An investor has the absolute statutory right to hold 100% of their demat portfolio in a single stock.
   * *Regulatory Origin*: The **10% single-stock ceiling** is a statutory constraint exclusively applicable to **Mutual Fund Schemes** (*SEBI (Mutual Funds) Regulations, 1996, Seventh Schedule, Clause 1*).
   * *Lucid Implementation*: The 15%, 20%, and 25% single-stock ceilings enforced inside Lucid are **Lucid House Risk Policies**, derived under the fiduciary mandate of **Regulation 17 of the SEBI IA Regulations (Suitability Assessment)** to prevent catastrophic idiosyncratic ruin. They must be explicitly labeled as internal fiduciary risk policies, not statutory mandates.

2. **The Corporate Ownership vs. Portfolio Allocation Separation**:
   * Systemic errors often conflate an investor's **portfolio weight** ($\frac{\text{Capital in Stock } i}{\text{Total Portfolio Capital}}$) with the investor's **ownership of voting equity** ($\frac{\text{Shares Owned}}{\text{Total Listed Equity Shares of Target Co.}}$).
   * Takeover thresholds under the **SEBI (Substantial Acquisition of Shares and Takeovers) Regulations, 2011 (SAST)**—such as the **5% disclosure trigger (Reg 29)** and **25% mandatory open-offer trigger (Reg 3(1))**—apply to voting rights in the issuing company. For retail allocations ($\le ₹10\text{ Crore}$), this is practically unreachable in liquid large- and mid-caps, but Lucid's engine must mathematically separate and track both metrics.

3. **Non-Custodial Architecture Eliminates PMS Classification**:
   * Lucid does not accept investor funds into proprietary pooling accounts, does not take custody of securities, and does not operate under a Power of Attorney (POA) to unilaterally execute orders.
   * Consequently, Lucid is strictly exempt from the **SEBI (Portfolio Managers) Regulations, 2020**, avoiding the **₹50 Lakh minimum client ticket size** and **₹5 Crore corporate net-worth requirement**.

4. **Algorithmic and AI Accountability**:
   * Under SEBI's regulatory doctrine, **legal and regulatory liability for automated recommendations cannot be delegated to an AI model or a third-party software provider**.
   * Lucid, its board of directors, and its designated **Principal Officer** bear 100% strict fiduciary liability for all outputs produced by its multi-agent committee and Copilot. Lucid must implement a deterministic mathematical firewall where no generative LLM can override statutory safety caps, fabricate market prices, or execute unvalidated trades.

---

## 2. Lucid Business Model and Regulatory Classification

To evaluate Lucid’s regulatory classification, we examine every user interaction and system capability against the SEBI Act, 1992, and subordinate regulations.

### 2.1 Regulatory Classification Matrix

| Application Feature | Potential Framework | Registration Required | Legal Basis | Applicability Conditions | Regulatory Risk & Boundary |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Personalized Risk Profiling & Questionnaire** | SEBI IA Regulations, 2013 | Yes (if coupled with advice) | Reg 16 & 17, SEBI IA Regs | Mandatory if personalized portfolio or advice is rendered. | Profiling alone is data collection; coupled with specific stock recommendations, it constitutes regulated advisory. |
| **Bespoke Portfolio Creation (e.g. ₹50k, 2 Yrs, Custom Caps)** | SEBI IA Regulations, 2013 | **Mandatory** | Reg 2(1)(l) & Reg 2(1)(m), SEBI IA Regs | Triggered whenever specific securities and integer lots are generated for a specific user. | High regulatory risk if unmonetized but marketed to public without registration. |
| **General Stock Research & Thematic Model Portfolios** | SEBI RA Regulations, 2014 | Yes (Research Analyst) | Reg 2(1)(u), SEBI RA Regs | Permitted if portfolios are published uniformly to all subscribers without personal profiling. | Cannot customize weights or tickers based on user's personal financial situation under RA. |
| **Demat Import & Concentration Diagnosis** | SEBI IA or Analytical Tool | Conditional | Reg 2(1)(l), SEBI IA Regs | Pure mathematical diagnostics (e.g., "Reliance is 45%") is informational; proposing trims is advisory. | Diagnostic facts are informational; recommending exact BUY/SELL/HOLD trades triggers IA. |
| **Stock-Specific Trims & Rebalancing (Whole Shares)** | SEBI IA Regulations, 2013 | **Mandatory** | Reg 2(1)(l), SEBI IA Regs | Directly instructs an investor to execute rebalancing trades in their demat account. | Definitive investment advice under Indian law. Cannot be operated without IA license. |
| **AI Copilot Answering Investment Queries** | SEBI IA / RA Guidelines | Conditional | SEBI Circular on AI Tools (2019/2024) | If Copilot provides opinions on whether to buy/sell/hold a stock, it is investment advice. | Strict separation required: factual calculations vs opinions. AI hallucinations carry direct regulatory liability. |
| **Broker Deep-Link Execution (1-Click Basket Export)** | Broker / Technology Partner | None (for Lucid directly) | Exchange Circulars on API Architecture | Permitted without broker license if using official broker redirect APIs where user authenticates and confirms on broker UI. | Must NOT handle client broker passwords, TOTP tokens, or directly execute trades via unauthorized server-side loops. |
| **Automated Trade Execution via Order Routing** | Stock Broker / Algorithmic Trading | Stock Broker / AP / Algo Approval | SEBI Algo Circulars 2021/2022 | Placing orders directly to exchange without user intervention requires broker/algo approvals. | Violates regulatory boundaries if executed without exchange-approved algo framework. |

### 2.2 Commercial Operating Models for Lucid

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       COMMERCIAL PATHWAYS FOR LUCID                         │
├──────────────────────────────────────┬──────────────────────────────────────┤
│ PATHWAY A: THE REGISTERED INVESTMENT │ PATHWAY B: THE RESEARCH ANALYST (RA) │
│          ADVISER (CORP RIA)          │           MODEL PORTFOLIO            │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Full personalized portfolio engine │ • Non-personalized model baskets     │
│ • Custom whole-share rebalancing     │ • Standardized weightings (e.g. 10%) │
│ • Demat portfolio diagnosis & trims  │ • Universal rebalance alerts         │
│ • Bipartite client agreement signed  │ • No personalized risk profiling     │
│ • Fee capped at ₹1.25L or 2.5% AUA   │ • Flexible subscription pricing      │
│ • Net worth required: ₹50 Lakhs      │ • Net worth required: ₹25 Lakhs      │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## 3. Applicability of SEBI (Investment Advisers) Regulations, 2013

### 3.1 Statutory Scope of Investment Advice
Under **Regulation 2(1)(l)** of the IA Regulations:
> *"Investment advice means an advice relating to investing in, purchasing, selling or otherwise dealing in securities or investment products, and advice on investment portfolio containing securities or investment products, whether written, oral or through any other means of communication for the benefit of the client and shall include financial planning."*

**Application to Lucid**: Lucid accepts an investor’s capital (₹50,000), time horizon (24 months), and risk tolerance, and returns an integer-lot allocation: `BUY 19 RELIANCE, BUY 14 TCS, BUY 33 HDFCBANK`. This is an unambiguous formulation of **Investment Advice**.

### 3.2 Individual vs. Non-Individual (Corporate) Registration
- **Client Volume Ceiling**: Under **Regulation 13(2)**, an individual investment adviser can service a maximum of **300 clients**. Once the 301st client registers, the individual IA must mandatorily cease onboarding and apply for registration as a body corporate.
- **Strategic Imperative**: As a B2C automated platform targeting retail scale, Lucid **must incorporate as a private limited company and apply directly as a Non-Individual (Corporate) Investment Adviser**.
- **Net Worth Requirement**: Under **Regulation 8(2)(a)**, a body corporate IA must maintain a minimum net worth of **₹50 Lakhs** (Fifty Lakh Rupees) at all times.

### 3.3 Key Personnel, Qualifications, and Certifications
Under **Regulation 7(1) & 7(2)**:
1. **Principal Officer**: Must possess:
   - A professional degree/postgraduate diploma in finance, accountancy, business management, commerce, economics, capital markets, or banking from a recognized university/institution; AND
   - Minimum **5 years of experience** in activities relating to advice in financial products, securities, fund management, or asset management.
2. **Certification Mandate**: The Principal Officer and all persons associated with investment advice must obtain valid certifications:
   - **NISM-Series-X-A**: Investment Adviser (Level 1) Certification Examination; AND
   - **NISM-Series-X-B**: Investment Adviser (Level 2) Certification Examination; OR
   - Approved equivalent certifications (e.g., CFP, CFA with requisite NISM CPE modules).

### 3.4 Client Agreements and Onboarding Mandate
Under the **SEBI Master Circular for Investment Advisers (SEBI/HO/MIRSD/MIRSD-PoD-2/P/CIR/2024/0056)**:
- **No advice can be provided without an executed written agreement**.
- Agreements may be executed digitally via Aadhaar e-Sign or electronic signatures compliant with the Information Technology Act, 2000.
- Mandatory clauses include: scope of advisory, fee schedule, risk disclosures, conflict-of-interest declarations, termination rights, and access to the SEBI SCORES / SMART ODR grievance mechanisms.

### 3.5 Advisory Fee Restrictions and Collection Mechanisms
Under **Regulation 15A** and regulatory circulars, an IA can charge fees under only one of two alternative modes across an entire client family:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        SEBI IA PERMITTED FEE MODES                     │
├───────────────────────────────────┬────────────────────────────────────┤
│         MODE 1: FIXED FEE         │    MODE 2: ASSETS UNDER ADVICE     │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Maximum Ceiling: ₹1,25,000 / yr │ • Maximum Ceiling: 2.50% p.a.      │
│ • Applied across entire family    │ • Calculated on verified AUA       │
│ • Transparent subscription tier   │ • Requires portfolio audit trail   │
│ • No percentage skimming          │ • Ideal for HNIs and wealth tier   │
└───────────────────────────────────┴────────────────────────────────────┘
```

- **Advance Fee Cap**: Maximum advance fee collectable is **up to 2 quarters (6 months)** in advance.
- **Collection Channels**: Fees must be received exclusively through audited banking channels (NEFT/RTGS/IMPS/UPI/Direct Mandate). Cash is strictly prohibited.
- **Strict Segregation of Advisory and Distribution (Reg 22)**:
  - An IA entity cannot offer mutual fund distribution or stockbroking execution services to the same client.
  - Lucid cannot collect distribution commissions, referral kickbacks, or brokerage revenue share from brokers on trades executed by its advisory clients.

---

## 4. Applicability of SEBI (Research Analysts) Regulations, 2014

### 4.1 Statutory Definition of Research Analyst
Under **Regulation 2(1)(u)** of the RA Regulations:
> *"Research report means any written or electronic communication that includes research analysis or research recommendation or an opinion concerning securities or public offer, providing a basis for investment decision..."*

### 4.2 The Model Portfolio Operational Boundary
Under recent regulatory circulars and interpretations (e.g., SEBI adjudication in *Stallion Asset*):
- **Permissible Under RA Framework**: An RA may create, maintain, and publish **Weighted Model Portfolios** (e.g., "Lucid Nifty Bluechip 10", "Digital India Tech Basket") provided:
  1. The portfolio is distributed identically to all subscribers of that research product.
  2. Individual stock allocations are derived from published research reports with published financial theses.
  3. The model portfolio does **not** evaluate the subscriber's personal financial situation, age, or risk tolerance.
  4. The subscriber independently decides whether their risk profile matches the model.
- **Prohibited Under RA Framework**: The moment Lucid allows Ankur to input ₹50,000 and dynamically tailors the weights, eliminates sectors, or diagnoses his Demat account holdings, **it has crossed into personalized Investment Advice and violates the RA framework if not registered as an IA**.

---

## 5. Applicability of SEBI (Portfolio Managers) Regulations, 2020

### 5.1 Defining Characteristics of a Portfolio Management Service (PMS)
Under **Regulation 2(1)(o)** of the PMS Regulations, a Portfolio Manager is a body corporate that, pursuant to a contract, advises, directs, or undertakes on behalf of the client the **management or administration** of a portfolio of securities or funds.

### 5.2 Mandatory Statutory Thresholds for PMS
1. **Minimum Investment Ticket Size**: **₹50 Lakhs (Fifty Lakh Rupees)** per client (*Regulation 23(2)*). A retail product accepting ₹10,000 or ₹50,000 cannot operate as a PMS under Indian law.
2. **Net Worth Requirement**: **₹5 Crores (Five Crore Rupees)** (*Regulation 9*).
3. **Custodial Mandate**: Securities and funds must be managed through designated depository participant (DP) and banking accounts with an independent SEBI-registered Custodian.

### 5.3 Lucid's Strict Non-Custodial Architecture
Lucid is engineered to be **strictly Non-Custodial**:
- Lucid **never** holds custody of investor cash or equity securities.
- Lucid **never** accepts a Power of Attorney (POA) or Demat Debit and Pledge Instruction (DDPI) to move securities.
- All buy/sell/rebalance orders are executed exclusively by the investor inside their own broker terminal.
- **Legal Conclusion**: Lucid is exempt from the PMS Regulations.

---

## 6. Broker and Exchange Integration Requirements

### 6.1 Architecture of Broker Connections
Lucid can connect with Indian stockbrokers (e.g., Zerodha Kite Connect, Upstox API, Groww, Angel One) using three distinct technical architectures, each carrying different regulatory burdens:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       BROKER INTEGRATION ARCHITECTURES                      │
├───────────────────────────────────┬─────────────────────────────────────────┤
│ ARCHITECTURE 1: DEEP-LINK BASKET  │ ARCHITECTURE 2: AUTHENTICATED REST API  │
│      REDIRECT (RECOMMENDED)       │         ORDER ROUTING (COMPLEX)         │
├───────────────────────────────────┼─────────────────────────────────────────┤
│ • Lucid constructs integer slip   │ • User inputs API Key & Secret in app   │
│ • 1-Click Redirect to Broker Web  │ • Lucid backend submits order API calls │
│ • User authenticates on Broker UI │ • Requires SEBI Algorithmic Approval    │
│ • User confirms & executes order  │ • Lucid classified as Authorized Person │
│ • No credential exposure to Lucid │ • Heavy exchange audit requirements     │
│ • Zero broker registration needed │ • Risk of regulatory sandbox violations │
└───────────────────────────────────┴─────────────────────────────────────────┘
```

### 6.2 SEBI & Exchange Algorithmic Trading Safeguards
Under **SEBI Circular SEBI/HO/MRD1/DSAP/CIR/P/2022/68** and NSE/BSE circulars:
- Any automated software placing orders without manual human intervention on a per-order basis is classified as **Algorithmic Trading (Algo)**.
- Broker APIs that offer automated order routing must receive prior approval from stock exchanges.
- To maintain compliance without becoming an exchange-approved algo facility, **Lucid must enforce human-in-the-loop confirmation**: every rebalance trade proposal must require an explicit, individual confirmation click by the user within the broker's sanctioned terminal.

---

## 7. Numerical Constraints: Allocation Caps and Mathematical Thresholds

The following master reference establishes the exact regulatory origin and legal classification of every allocation threshold inside Lucid.

### 7.1 Comprehensive Allocation Constraints Table

| Constraint Name | Exact Threshold | Legal Classification | Regulatory Source / Citation | Applicable Entity | How Lucid Must Implement in Engine |
| :--- | :---: | :--- | :--- | :--- | :--- |
| **Direct Retail Equity Stock Cap** | **None (No Cap)** | **Statutory Freedom** | SEBI Act, 1992 / Constitution of India | Individual Retail Investors | Allow user full freedom, but issue soft fiduciary warnings if weight > 25%. |
| **Mutual Fund Single Stock Cap** | **10.0% of NAV** (12% with approval) | **SEBI Statutory Mandate** | SEBI (Mutual Funds) Regs, 1996, 7th Schedule, Cl 1 | Mutual Fund Asset Management Companies (AMCs) | Apply only when evaluating mutual fund constituents, not direct equity portfolios. |
| **Mutual Fund Sector Exposure Cap** | **20.0% of NAV** (+5% HFCs) | **SEBI Statutory Mandate** | SEBI Circular SEBI/HO/IMD/DF2/CIR/P/2016/35 | Mutual Fund Schemes (except thematic/sector funds) | Used as a benchmark reference in explainability comparisons; not an equity hard-lock. |
| **Lucid Very Conservative Single-Stock Cap** | **15.0% of Portfolio** | **Lucid House Policy** | Fiduciary Duty under SEBI IA Regs, Reg 17 (Suitability) | Lucid Very Conservative Risk Tier | **HARD_CONSTRAINT** in SLSQP optimizer: $w_i \le 0.15$ for all securities. |
| **Lucid Conservative Single-Stock Cap** | **20.0% of Portfolio** | **Lucid House Policy** | Fiduciary Duty under SEBI IA Regs, Reg 17 (Suitability) | Lucid Conservative Risk Tier | **HARD_CONSTRAINT** in SLSQP optimizer: $w_i \le 0.20$ for all securities. |
| **Lucid Moderate / Growth Single-Stock Cap** | **25.0% of Portfolio** | **Lucid House Policy** | Fiduciary Duty under SEBI IA Regs, Reg 17 (Suitability) | Lucid Moderate & Growth Risk Tiers | **HARD_CONSTRAINT** in SLSQP optimizer: $w_i \le 0.25$ for all securities. |
| **Lucid Sector Exposure Cap (Conservative)** | **35.0% of Portfolio** | **Lucid House Policy** | Prudent Risk Management Standard | Lucid Conservative Portfolios | **HARD_CONSTRAINT** in SLSQP optimizer: $\sum_{i \in S_k} w_i \le 0.35$ for all sectors $S_k$. |
| **Lucid Sector Exposure Cap (Standard)** | **40.0% of Portfolio** | **Lucid House Policy** | Prudent Risk Management Standard | Lucid Standard Portfolios | **HARD_CONSTRAINT** in SLSQP optimizer: $\sum_{i \in S_k} w_i \le 0.40$ for all sectors $S_k$. |
| **Takeover Substantial Acquisition Trigger** | **5.0% of Voting Capital** | **SEBI Statutory Mandate** | SEBI (SAST) Regulations, 2011, Regulation 29(1) | Any Acquirer / Investor + PAC | Mandatory exchange disclosure within 2 trading days if company ownership $\ge 5\%$. |
| **Mandatory Takeover Open Offer Trigger** | **25.0% of Voting Capital** | **SEBI Statutory Mandate** | SEBI (SAST) Regulations, 2011, Regulation 3(1) | Any Acquirer / Investor + PAC | Triggers mandatory public tender offer for additional 26% equity. Block trade if triggered. |
| **Annual Creeping Acquisition Limit** | **5.0% of Voting Capital / Year** | **SEBI Statutory Mandate** | SEBI (SAST) Regulations, 2011, Regulation 3(2) | Investors holding between 25% and 75% | Limits annual purchases without an open offer. |
| **Minimum Portfolio Cash Residual** | **₹0.00 (Zero Deficit)** | **Mathematical & Exchange** | NSE/BSE Cash Market Delivery Settlement | All Cash Segment Orders | Invariant: $\text{Post-Rounding Cash} \ge 0$. No unbacked leverage allowed. |

---

## 8. Share Quantity and Ownership Restrictions

### 8.1 Corporate Takeover vs. Retail Allocation Mechanics
Lucid's constraint validator must execute two mathematically distinct calculations:

$$\text{Portfolio Weight } w_i = \frac{Q_i \times P_i}{C_{\text{total}}} \quad \text{vs.} \quad \text{Company Ownership } \Omega_i = \frac{Q_i + Q_{\text{existing}}}{N_{\text{total\_shares\_outstanding}}}$$

Where:
- $Q_i$ is the proposed whole-share quantity.
- $P_i$ is the current market price per share.
- $C_{\text{total}}$ is the investor's total capital.
- $N_{\text{total\_shares\_outstanding}}$ is the company's total issued equity share capital.

For an investor with ₹1,00,000 investing in Reliance Industries ($N \approx 6.76 \times 10^9$ shares), $w_i = 15\%$ represents ₹15,000 ($\approx 5$ shares). Here, $\Omega_i \approx 7.39 \times 10^{-10}$, which is seven orders of magnitude below the 5% SAST disclosure threshold. However, for micro-cap illiquid stocks, Lucid must validate that $Q_i$ does not breach statutory disclosure or market impact limits.

### 8.2 Execution and Settlement Constraints (NSE/BSE Cash Market)
1. **Integer Lot Sizing**: The minimum tradable market lot in the standard cash market segment of NSE and BSE is **1 share**. Fractional share trading does not legally exist in Indian equity markets.
2. **Tick Size Rules**: Orders must conform to the exchange tick size (minimum price movement). Historically ₹0.05, revised under recent NSE/BSE operational circulars to **₹0.01 for securities priced below ₹250**.
3. **Settlement Cycle ($T+1$ and $T+0$)**: Indian equity markets operate on an atomic **$T+1$ rolling settlement cycle**, with ongoing phased rollout of optional **$T+0$ same-day settlement** for eligible bluechips. Lucid's rebalancing calculations must account for settlement cycles when computing proceeds from SELL trades to fund BUY orders.

---

## 9. Complete Investor Risk Profiling and Investment Suitability

Under **Regulations 16 and 17 of the SEBI IA Regulations**, risk profiling is a mandatory prerequisite to rendering investment advice.

### 9.1 Mandatory Risk Capacity vs. Risk Tolerance Separation
SEBI mandates that an adviser must evaluate an investor's **Risk Capacity** (objective financial ability to absorb capital loss) independently of their **Risk Tolerance** (subjective psychological willingness to endure volatility).

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TWO-PILLAR SUITABILITY ARCHITECTURE                    │
├──────────────────────────────────────┬──────────────────────────────────────┤
│      PILLAR 1: RISK CAPACITY         │       PILLAR 2: RISK TOLERANCE       │
│        (OBJECTIVE ABILITY)           │       (PSYCHOLOGICAL ATTITUDE)       │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Age & Earning Horizon              │ • Response to -20% Market Drawdown   │
│ • Net Disposable Monthly Income      │ • Self-Described Risk Personality    │
│ • Liquid Emergency Reserve Buffer    │ • Historical Investment Experience   │
│ • Existing Debt & Loan Liabilities   │ • Preference for Safety vs Returns   │
│ • Capital Loss Tolerance (Rupees)    │ • Volatility Comfort Corridor        │
└──────────────────────────────────────┴──────────────────────────────────────┘
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │            CONSERVATIVE PRUDENCE RULE            │
             │ Assessed Profile = MIN(Risk Capacity, Tolerance) │
             └──────────────────────────────────────────────────┘
```

**The Conservative Prudence Invariant**: If a 22-year-old investor with zero savings displays "Aggressive" psychological tolerance, their **Risk Capacity is Low**, forcing their overall assigned tier to **Conservative**. Conversely, a high-net-worth individual with high capacity but zero psychological volatility tolerance is mapped to **Conservative**. Recommendations must never exceed the lower of the two bounds.

### 9.2 Mandatory Suitability Engine Validations
Before a portfolio is delivered to an investor, the engine must execute the following checks:
1. **Horizon Compatibility**: If target horizon is $< 24\text{ months}$, equity volatility budget is capped at $\le 10\%$.
2. **Emergency Reserve Guardrail**: If liquid bank emergency fund is $< 3\text{ months}$ of living expenses, an advisory disclosure flags capital as unsuitable for 100% equity allocation.
3. **Knowledge & Experience Filter**: If the investor reports zero equity experience, high-beta ($> 1.30$) or complex cyclical candidates are excluded.

---

## 10. Portfolio Construction and Concentration Restrictions

### 10.1 Multi-Tiered Portfolio Policy Framework
To ensure complete transparency, every constraint enforced in Lucid’s deterministic engine is tagged with an authoritative identifier, source, and severity:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LUCID FIVE-TIER RISK POLICY STANDARDS                    │
├───────────────────┬──────────────┬──────────────┬─────────────┬─────────────┤
│ Risk Tier         │ Max Stock Wt │ Max Sect Wt  │ Min Stocks  │ Max Beta    │
├───────────────────┼──────────────┼──────────────┼─────────────┼─────────────┤
│ Very Conservative │ 15.0%        │ 35.0%        │ 7 Stocks    │ 0.90        │
│ Conservative      │ 20.0%        │ 35.0%        │ 5 Stocks    │ 1.05        │
│ Moderate          │ 25.0%        │ 40.0%        │ 4 Stocks    │ 1.25        │
│ Growth            │ 25.0%        │ 40.0%        │ 4 Stocks    │ 1.45        │
│ Aggressive        │ 25.0%        │ 40.0%        │ 4 Stocks    │ 1.65        │
└───────────────────┴──────────────┴──────────────┴─────────────┴─────────────┘
```

### 10.2 Disallowed and Restricted Instruments
Under SEBI retail suitability guidelines, Lucid's equity universe filtering must exclude:
- **Unlisted Equities**: Purely unlisted shares are excluded from automated retail portfolios.
- **SME Exchange Listings (BSE SME / NSE Emerge)**: Excluded from general retail portfolios unless the investor qualifies as an Accredited Investor under SEBI norms (minimum lot sizes of ₹1 Lakh+).
- **Physical Demat Defaulters / Banned Promoters**: Companies whose promoters or directors are barred from the securities market by SEBI orders.

---

## 11. Rebalancing and Portfolio Management Requirements

### 11.1 The Whole-Share Rebalancing Mechanics
When an existing portfolio is imported, market movements cause allocations to drift away from model targets. Lucid’s whole-share rebalancing algorithm operates under strict mathematical and operational invariants:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INTEGER REBALANCING INVARIANTS                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Cash Inflow from Trims:                                                  │
│    Proceeds = SUM( (Current_Shares_i - Target_Shares_i) * Price_i )         │
│    (For all securities where Target_Shares < Current_Shares)                │
│                                                                             │
│ 2. Discrete Lot Allocation:                                                 │
│    Target_Shares_j = FLOOR( (Allocated_Capital * Weight_j) / Price_j )      │
│                                                                             │
│ 3. Cash Buffer Invariant:                                                   │
│    Post_Rebalance_Cash = Available_Cash + Proceeds - Purchases >= 0.00      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 11.2 Statutory Communications for Rebalancing Trades
- **No Automatic Execution**: In a non-custodial IA service, Lucid **cannot automatically place trades**.
- **Transparency on Drift**: When a portfolio drifts by more than 5% absolute weight from its target model, a rebalancing notification must explain:
  - Exactly which securities breached concentration ceilings.
  - The deterministic mathematical justification for the trim.
  - Estimated statutory transaction costs (Securities Transaction Tax — STT, Exchange Turnover Fees, SEBI Turnover Fees, GST, and Stamp Duty).

---

## 12. NSE and BSE Trading Restrictions and Surveillance Measures

Lucid must ingest and process real-time and end-of-day exchange surveillance masters to prevent recommending compromised or illiquid securities.

### 12.1 Surveillance Frameworks Reference Table

| Framework | Full Form | Stage / Level | Trading Restriction | Order Margin Requirement | Lucid Technical Action |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **GSM** | Graded Surveillance Measure | Stage 0 / I | Price band locked to 5% | Normal margins | **WARNING**: Highlight surveillance to user. |
| **GSM** | Graded Surveillance Measure | Stage II | Price band locked to 5% | 100% upfront + 50% ASD | **HARD_BLOCK**: Exclude from BUY recommendations. |
| **GSM** | Graded Surveillance Measure | Stage III / IV | Trading allowed only once a week / month | 100% upfront + 100% ASD | **HARD_BLOCK**: Exclude from all portfolio proposals. |
| **ASM** | Additional Surveillance Measure | Short-Term (I & II) | Price band narrowed (5% or 10%) | 50% to 100% margin | **WARNING**: Flag high volatility and margin impact. |
| **ASM** | Additional Surveillance Measure | Long-Term (I to IV) | Price band 5%, no intraday leverage | 100% gross delivery margin | **WARNING**: Notify user of delivery-only mandate. |
| **T2T** | Trade-to-Trade Settlement | Series 'BE' / 'T' Group | Delivery only; intraday squaring prohibited | 100% cash upfront margin | **INFORMATION**: Confirm delivery-only settlement. |
| **SUSP** | Suspended Trading | N/A | Total trading halt on exchange | Zero trading permitted | **CRITICAL_BLOCK**: Security rejected from universe. |

---

## 13. AI, Automation, and Multi-Agent Governance

### 13.1 Regulatory Accountability for AI Tools
Under **SEBI Circular SEBI/HO/MIRSD/DOS2/CIR/P/2019/38** (Reporting of AI/ML Applications) and subsequent guidelines:
1. **Registered Intermediary Liability**: The registered entity is **fully responsible and legally accountable** for all advice, recommendations, and reports generated using AI, Machine Learning, or Large Language Models.
2. **Model Governance**: The entity must maintain an inventory of all AI models, system prompts, deterministic algorithms, and risk boundaries.
3. **Auditable Decision Trail**: For every recommendation generated, the exact agent outputs, retrieval sources, factor inputs, and quantitative scores must be retained in an immutable audit database for **5 years**.

### 13.2 Deterministic Firewall Architecture
To eliminate LLM hallucinations and enforce regulatory boundaries, Lucid implements a strict architectural firewall:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LUCID FIDUCIARY AI FIREWALL                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────┐ ┌──────────────────────────────────┐ │
│ │  GENERATIVE MULTI-AGENT COMMITTEE  │ │  DETERMINISTIC FIDUCIARY ENGINE  │ │
│ │  • Strategist Agent (Macro Trends) │ │  • SLSQP Portfolio Optimizer     │ │
│ │  • Fundamental Analyst (ROE/PE)    │ │  • Integer Share Lot Sizer       │ │
│ │  • News & Sentiment Extractor      │ │  • Regulatory Constraint Checks  │ │
│ │  • AI Copilot Explanation Drafter  │ │  • Cash & STT Accounting Engine  │ │
│ └──────────────────┬─────────────────┘ └──────────────────┬───────────────┘ │
│                    │                                      │                 │
│                    ▼                                      ▼                 │
│         ┌─────────────────────────────────────────────────────┐             │
│         │        STRICT FIDUCIARY VALIDATION GATEWAY          │             │
│         │ • Verifies that LLM text does not contradict math  │             │
│         │ • Enforces single-stock & sector hard ceilings      │             │
│         │ • Prevents fabrication of returns or guarantees     │             │
│         │ • Signs recommendation with cryptographic timestamp │             │
│         └─────────────────────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 14. Registration, Eligibility, and Certification Checklist

### 14.1 Corporate IA Incorporation Checklist (SEBI IA Regs, 2013)
- [ ] **Incorporation**: Incorporate as a Private Limited Company under the Companies Act, 2013, with main objects in the Memorandum of Association (MOA) authorizing investment advisory activities.
- [ ] **Capitalization**: Maintain paid-up capital and tangible net worth $\ge \mathbf{₹50,00,000}$ (Fifty Lakh Rupees), certified by an independent statutory auditor.
- [ ] **Principal Officer**: Appoint a designated Principal Officer meeting the Regulation 7 criteria (Postgraduate degree + 5 years relevant experience + valid NISM X-A & X-B certificates).
- [ ] **Compliance Officer**: Appoint a dedicated Compliance Officer under Regulation 13(1) responsible for monitoring statutory compliance.
- [ ] **Infrastructure & Security**: Establish secure server infrastructure, SSL/TLS 1.3 encryption, and auditable database storage in compliance with CERT-In directions.
- [ ] **SEBI Application Filing**: Submit Form A via the SEBI Intermediary Portal with application fee (₹10,000) and registration fee (₹5,00,000 for body corporate for 5-year validity).

---

## 15. Fees, Billing, and Commercial Payment Restrictions

### 15.1 Statutory Fee Ceilings
Under SEBI IA Regulation 15A:
- **Fixed Fee Mode**: Maximum ₹1,25,000 per annum per client family.
- **AUA Mode**: Maximum 2.50% per annum of Assets under Advice per client family.
- **Advance Collections**: Limited strictly to a maximum of 6 months (2 quarters) in advance. Refunds for early termination must be calculated on a pro-rata basis for unexpired periods.
- **Zero Commission Integrity**: Lucid cannot collect any distribution kickbacks or volume-based broker rebates from advisory clients.

---

## 16. Disclosures, Advertising Code, and Conflicts of Interest

### 16.1 SEBI Advertising Code Mandates (SEBI Circular 2023)
Under the **Code of Conduct and Advertising Guidelines for Investment Advisers**:
- **Prohibited Claims**:
  - Guaranteeing returns, capital protection, or zero-risk investments.
  - Making misleading, exaggerated, or cherry-picked performance claims.
  - Using terms such as "Best Stock", "Multi-Bagger", or "Guaranteed Wealth".
- **Mandatory Disclosures**:
  - *"Investments in securities market are subject to market risks. Read all the related documents carefully before investing."*
  - Display of SEBI Registration Number, registered office address, CIN, and grievance officer details on all website footers, apps, and reports.

---

## 17. Client Agreements, Record Keeping, and Statutory Audit

### 17.1 Record Retention Mandate (Regulation 19)
Lucid must preserve the following records for a minimum period of **5 years**:
1. Client profiling records and risk assessments.
2. Signed bipartite client agreements.
3. Every investment advice and rebalancing proposal with dated rationale.
4. Complete audit logs of multi-agent deliberation and deterministic calculations.
5. Record of fees charged and payment receipts.
6. Record of customer complaints and resolution timelines.

### 17.2 Annual Compliance and Technical Audit
Under **Regulation 19(3)**:
- An independent Chartered Accountant or Company Secretary must conduct an **annual compliance audit** within 6 months of the close of each financial year.
- A **System Audit** by an independent CERT-In empanelled auditor must be conducted annually to verify data security, algorithm integrity, and AI governance.

---

## 18. Investor Grievance Redressal and SCORES / SMART ODR Integration

### 18.1 Escalation Matrix and Portals
1. **Level 1 (Internal)**: Direct resolution by Lucid's Grievance Officer within **21 calendar days**.
2. **Level 2 (SEBI SCORES 2.0)**: Centralized SEBI Complaints Redress System. Failure to resolve complaints within 21 days leads to automatic regulatory escalation.
3. **Level 3 (SMART ODR)**: Securities Market Approach for Resolution Through ODR Portal (online conciliation and arbitration).

---

## 19. Data Privacy, Cybersecurity, and Other Applicable Indian Laws

### 19.1 Digital Personal Data Protection Act, 2023 (DPDP Act)
- **Notice & Consent**: Clear, itemized notice explaining what personal financial data is collected and for what specified purpose.
- **Data Principal Rights**: Right to access, right to correction, right to erasure (subject to statutory SEBI 5-year retention rules), and right of grievance redressal.
- **Penalties**: Fines up to **₹250 Crores** for failing to implement reasonable security safeguards to prevent personal data breaches.

### 19.2 CERT-In Cybersecurity Directions (2022)
- Mandatory reporting of cybersecurity incidents (unauthorized access, DDoS, ransomware) to CERT-In within **6 hours** of detection.
- Synchronization of system clocks with NTP servers of National Physical Laboratory (NPL).
- Maintenance of system access logs within Indian jurisdiction for **180 days**.

---

## 20. Required APIs and Regulatory Data Sources

### 20.1 Master Data Feeds and Acquisition Matrix

| Data Domain | Specific Data Elements | Official Regulatory Source | Access Method & Frequency | Alternative / Authorized Vendor |
| :--- | :--- | :--- | :--- | :--- |
| **Exchange Security Master** | Symbol, ISIN, BSE Scrip Code, Series, Status | NSE & BSE Official FTP / Portals | Daily Batch Download (Free / Commercial) | Authorized Market Data Feeds (e.g., Upstox, Zerodha) |
| **Surveillance Masters** | GSM, ASM, T2T, Price Bands (2%, 5%, 10%, 20%) | NSE/BSE Surveillance Circulars & CSVs | Daily EOD Batch Download | NSE/BSE Market Operations FTP |
| **Shareholding & Takeover** | Promoter holding, FII/DII holding, Total Equity | BSE/NSE Corporate Announcements | Quarterly filings / BSE Corporate Data API | CMIE Prowess / Accord Fintech / Prime Database |
| **Financial Fundamentals** | Audited Quarterly/Annual P&L, Balance Sheet, ROE | BSE/NSE Regulatory Filings (XBRL) | Quarterly / Annual XBRL Ingestion | Capitaline / TickerPlant / Refinitiv |
| **Market Quotes (LTP)** | Closing prices, traded volume, adjusted prices | NSE Real-time / 15-min Delayed Feeds | Continuous / End-of-Day | Commercial Data Vendor Feed Agreement |

---

## 21. Centralized Regulatory and Portfolio Constraint Engine Design

To eliminate scattered hardcoded rules, Lucid centralizes all regulatory, exchange, suitability, and house policy checks into a unified **Policy and Constraint Engine**:

```
                                  INCOMING REQUEST
                       (Portfolio Generation / Rebalance Audit)
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │          CENTRAL CONSTRAINT ENGINE            │
                 └───────────────────────┬───────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌──────────────────┐           ┌──────────────────┐           ┌──────────────────┐
│ REGULATORY RULES │           │ SUITABILITY &    │           │ TRADING &        │
│ ENGINE           │           │ RISK ENGINE      │           │ EXCHANGE ENGINE  │
├──────────────────┤           ├──────────────────┤           ├──────────────────┤
│ • SEBI IA Norms  │           │ • Capacity Score │           │ • GSM / ASM Lock │
│ • SAST 5% Limits │           │ • Horizon Clamp  │           │ • Price Bands    │
│ • No Leverage    │           │ • Loss Buffer    │           │ • Integer Lots   │
└──────────────────┘           └──────────────────┘           └──────────────────┘
         │                               │                               │
         └───────────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │       UNIFIED VALIDATION & AUDIT RESULT       │
                 │   PASS / BLOCK / WARNING + Grounded Rationale │
                 └───────────────────────────────────────────────┘
```

---

## 22. Product Implementation Roadmap

### Phase 1: Institutional Foundation & RA Model Portfolios (Months 1–3)
- Incorporate Private Limited entity with ₹50L+ equity capitalization.
- Designate Principal Officer and complete NISM X-A & X-B certifications.
- Build Centralized Policy Engine enforcing deterministic single-stock (15%-25%) and sector (35%-40%) house limits.
- Implement GSM/ASM/T2T exchange surveillance filter.
- Launch non-personalized Model Portfolios under RA operational model.

### Phase 2: SEBI Corporate IA Licensing & Suitability Gateway (Months 4–7)
- File Form A application with SEBI for Corporate Investment Adviser registration.
- Build full 11-point Risk Capacity vs Risk Tolerance onboarding gateway.
- Implement Aadhaar e-Sign digital client agreement workflow.
- Enforce strict statutory fee billing engine (max ₹1.25L fixed fee or 2.5% AUA).
- Deploy immutable 5-year decision logging database.

### Phase 3: Demat Portfolio Diagnosis & Whole-Share Rebalancing (Months 8–10)
- Roll out multi-source Demat import (CSV, manual, paste, Demat fetch).
- Integrate deterministic integer-lot whole-share rebalance engine.
- Deploy 7-Section Fiduciary Rebalancing Audit report in frontend.
- Launch context-aware Fiduciary AI Copilot with hallucination firewall.

### Phase 4: Non-Custodial Broker Integrations (Months 11–12)
- Establish deep-link order basket integration with premier Indian brokers (Zerodha, Upstox, Groww).
- Implement user-confirmed basket review and execution without credential handling.
- Conduct annual CERT-In System Audit and statutory compliance review.

---

## 23. Comprehensive Regulatory Constraint Matrix

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       MASTER REGULATORY CONSTRAINT MATRIX                                        │
├──────────────┬──────────────────┬──────────────┬───────────────┬─────────────────────────┬───────────┬───────────┤
│ Rule ID      │ Rule Description │ Exact Limit  │ Legal Origin  │ Regulatory Reference    │ Severity  │ Action    │
├──────────────┼──────────────────┼──────────────┼───────────────┼─────────────────────────┼───────────┼───────────┤
│ POL-STAT-01  │ Max Retail Stock │ None (0-100%)│ Legal Freedom │ SEBI Act, 1992          │ INFO      │ No block  │
│ POL-SAST-01  │ SAST Acquisition │ 5.00% Voting │ SEBI Law      │ SEBI (SAST) Reg 29(1)   │ BLOCK     │ Alert/Dis │
│ POL-SAST-02  │ Open Offer Trig  │ 25.0% Voting │ SEBI Law      │ SEBI (SAST) Reg 3(1)    │ BLOCK     │ Reject    │
│ POL-MF-01    │ Mutual Fund Stock│ 10.0% of NAV │ SEBI Law (MF) │ SEBI MF Regs, 7th Sched │ Benchmark │ Compare   │
│ POL-MF-02    │ Mutual Fund Sect │ 20.0% of NAV │ SEBI Law (MF) │ SEBI Circular 2016/35   │ Benchmark │ Compare   │
│ POL-HOUS-01  │ Very Conserv Stk │ 15.0% Portf. │ House Policy  │ Fiduciary / Suitability │ BLOCK     │ Optimizer │
│ POL-HOUS-02  │ Conserv Stock Cap│ 20.0% Portf. │ House Policy  │ Fiduciary / Suitability │ BLOCK     │ Optimizer │
│ POL-HOUS-03  │ Moderate Stock   │ 25.0% Portf. │ House Policy  │ Fiduciary / Suitability │ BLOCK     │ Optimizer │
│ POL-HOUS-04  │ Sector Cap (Con) │ 35.0% Portf. │ House Policy  │ Fiduciary / Suitability │ BLOCK     │ Optimizer │
│ POL-HOUS-05  │ Sector Cap (Mod) │ 40.0% Portf. │ House Policy  │ Fiduciary / Suitability │ BLOCK     │ Optimizer │
│ POL-EXCH-01  │ GSM II/III/IV    │ Stage 2+     │ Exchange Rule │ NSE/BSE Surveillance    │ BLOCK     │ Exclude   │
│ POL-EXCH-02  │ ASM Surveillance │ Short/Long   │ Exchange Rule │ NSE/BSE Surveillance    │ WARNING   │ Disclose  │
│ POL-EXCH-03  │ T2T Settlement   │ Series BE/T  │ Exchange Rule │ 100% Delivery Mandate   │ WARNING   │ Cash Lock │
│ POL-EXCH-04  │ Market Lot Size  │ 1 Whole Sh.  │ Exchange Rule │ NSE/BSE Cash Market     │ BLOCK     │ Round Int │
│ POL-FEE-01   │ Max IA Fixed Fee │ ₹1,25,000/yr │ SEBI Law      │ SEBI IA Reg 15A         │ BLOCK     │ Cap Price │
│ POL-FEE-02   │ Max IA AUA Fee   │ 2.50% AUA    │ SEBI Law      │ SEBI IA Reg 15A         │ BLOCK     │ Cap Price │
│ POL-FEE-03   │ Max Advance Fee  │ 2 Quarters   │ SEBI Law      │ SEBI IA Master Circ     │ BLOCK     │ Cap Bill  │
│ POL-CUST-01  │ Non-Custodial    │ ₹0 Client Ac │ Statutory Bnd │ SEBI PMS Regs Reg 2(1)  │ INVARIANT │ Enforce   │
└──────────────┴──────────────────┴──────────────┴───────────────┴─────────────────────────┴───────────┴───────────┘
```

---

## 24. Unresolved Legal Questions Requiring Formal Securities Counsel Opinion

1. **AI Copilot Free-Form Responses**: Does an AI agent providing natural-language reasoning (e.g., explaining why Reliance was trimmed) without generating a new quantitative buy/sell instruction constitute an independent advisory act under Regulation 2(1)(l)?
2. **Freemium Diagnostic Tiers**: Can Lucid offer automated Demat diagnosis and concentration warnings for free to non-subscribers under the "educational information" doctrine, provided rebalance execution slips remain locked behind an executed IA client agreement?
3. **Execution Deep-Link Liability**: Does providing pre-populated 1-click order basket deep-links to registered brokers expose Lucid to joint liability under exchange algorithmic trading circulars if a client's third-party browser script malfunctions?
4. **Research Analyst vs. Advisory Transition**: Can Lucid run a hybrid business model where non-personalized model portfolios are sold via an RA registration, while bespoke portfolio creation is routed to a subsidiary Corporate IA?

---

## 25. Official References and Statutory Register

1. **Securities and Exchange Board of India Act, 1992 (15 of 1992)**.
2. **SEBI (Investment Advisers) Regulations, 2013** (*No. LAD-NRO/GN/2012-13/31/1778*, as amended up to 2024/2026).
3. **SEBI (Research Analysts) Regulations, 2014** (*No. LAD-NRO/GN/2014-15/12/1520*).
4. **SEBI (Portfolio Managers) Regulations, 2020** (*No. SEBI/LAD-NRO/GN/2020/03*).
5. **SEBI (Mutual Funds) Regulations, 1996** (*Seventh Schedule - Restrictions on Investments*).
6. **SEBI (Substantial Acquisition of Shares and Takeovers) Regulations, 2011** (*Regulations 3, 29, and 30*).
7. **SEBI Master Circular for Investment Advisers** (*SEBI/HO/MIRSD/MIRSD-PoD-2/P/CIR/2024/0056*).
8. **SEBI Circular on AI & Machine Learning Technologies** (*SEBI/HO/MIRSD/DOS2/CIR/P/2019/38*).
9. **SEBI Circular on Algorithmic Trading Facilities** (*SEBI/HO/MRD1/DSAP/CIR/P/2022/68*).
10. **Digital Personal Data Protection Act, 2023 (No. 22 of 2023)**.
11. **NSE & BSE Surveillance Operating Circulars (GSM, ASM, T2T & Price Bands 2024/2026)**.
12. **Consumer Protection (E-Commerce) Rules, 2020 & CCPA Dark Patterns Guidelines, 2023**.

