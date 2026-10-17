# Comprehensive Methodology & Implementation Plan
## Intelligent Portfolio Creation by Capturing Fund Manager Experience via Agentic AI

---

# Section 1: Literature-to-Architecture Mapping

## 1.1 Research Paper → Design Decision Matrix

| # | Paper | Technique We Adopt | Modification Required | Where It Fits | Expected Benefit |
|---|-------|-------------------|----------------------|---------------|-----------------|
| 1 | Kotekar & Mohan (2026) | MFKG + Case-Based Reasoning via Neo4j | Replace static cosine similarity with GraphRAG; add LLM reasoning layer on top | **Knowledge Layer** — Neo4j graph database storing historical fund manager episodes | Provides episodic memory of expert behavior; solves LLM amnesia |
| 2 | Fatouros et al. (2025) — MarketSenseAI 2.0 | Specialized multi-agent pipeline (News, Fundamentals, Macro, Signal agents) | Adapt from S&P 100 to Indian NIFTY market; replace GPT-4o with open-source models for cost | **Data Ingestion Layer** — Parallel specialist agents that process live market data | Prevents context-window overload; each agent handles one data domain |
| 3 | Hajaghaie & Thulasiram (2025) | LangGraph state machine separating Reasoning Nodes from Functional Nodes | Extend to include MFKG queries as a functional node; add retry/validation loops | **Orchestration Layer** — LangGraph DAG controlling entire workflow | Eliminates mathematical hallucinations; deterministic math execution |
| 4 | Kulpa & Wojarnik (2025) | Triad architecture: Strategist → Critic (CoVe) → Moderator | Implement as actual Python code (paper is theoretical); embed M-SAEA probes into Critic | **Debate Layer** — The core reasoning loop for portfolio decisions | Prevents hallucination and policy violations through adversarial debate |
| 5 | Chen et al. (2026) — M-SAEA | 10 audit probes across 4 risk layers | Internalize probes into the Critic node instead of using as external auditor | **Safety Layer** — Hardcoded into the Critic agent's verification pipeline | Provides quantifiable safety guarantees; detects optimistic trust |
| 6 | Chhalotre et al. (2025) — AlphaNiftyAI | FAISS-based historical news grounding + Confidence-scored CoT | Use FAISS for news similarity; adopt confidence scoring (1-10) for weight scaling | **Sentiment Layer** — News agent grounds current headlines against historical reactions | Prevents naive LLM assumptions about breaking news |
| 7 | Maheswari & Reddy (2023) | Jensen's Alpha + Henriksson-Merton model findings | Use findings as architectural constraint: trust stock-picking, distrust market timing | **Design Principle** — Separate stock selection from market timing in agent responsibilities | Architecture mirrors empirically validated human skill decomposition |
| 8 | Bhambhani et al. (2025) | India VIX as regime classifier | Program VIX thresholds into Critic agent: VIX > 20 triggers defensive mode | **Risk Layer** — Automatic constraint tightening during high-volatility regimes | Mimics the defensive posture of successful Indian managers during crashes |
| 9 | Raju et al. (2024) | Investment Strategy as mediator between timing and performance | Implement as a deterministic "Strategy Enforcement" functional node | **Constraint Layer** — Risk tolerance + asset allocation rules enforced in Python | Ensures market predictions are filtered through disciplined rules |
| 10 | Stein (2022) | Smart Copycat identification via VAR-Granger Causality | Use concept (selective imitation) as the philosophical basis for MFKG queries | **Query Strategy** — Agents selectively imitate only the best manager for each regime | Economic justification for selective behavioral imitation |
| 11 | Mathuraswamy et al. (2023) | PCA-validated performance factors: Manager Skill, Fees, Fund Size, Market Conditions | Encode as operational constraints in Functional Nodes | **Feature Engineering** — These 4 dimensions shape agent prompts and constraints | Grounds agent behavior in empirically validated human factors |
| 12 | Mantshimuli & Mwamba (2026) | Proof that LLMs fail at precise portfolio weighting | Validates our decision to use Python for all math | **Architectural Validation** — Confirms Reasoning/Functional node separation is necessary | Prevents the #1 failure mode in LLM-based finance |
| 13 | Abe et al. (2024) | Persona-Based Ensemble (Short/Medium/Long-term investor personas) | Adapt to Indian fund manager personas (Short Term/Mid Term/Long Term) | **Persona Layer** — Multiple digital twins debate before consensus | Reduces single-persona bias; improves crash detection |
| 14 | Halperin et al. (2024) | IRL/RL for intent reverse-engineering | **Do NOT adopt** — serves as mathematical baseline for comparison only | **Evaluation** — Compare our explainable approach against IRL's black-box tracking error | Proves our system achieves comparable imitation with full explainability |

## 1.2 Approaches We Explicitly Avoid

| Approach | Source | Why We Avoid It |
|----------|--------|----------------|
| Deep Reinforcement Learning (DRL) for portfolio optimization | Wang (2024), Zhao (2026) | Black-box; cannot explain *why* a trade was made; unacceptable for SEBI compliance |
| Direct LLM weight generation | Mantshimuli & Mwamba (2026) | LLMs are mathematically incompetent at precise decimal allocations |
| Single-agent monolithic LLM | Generic chatbot approaches | Context window overload; no separation of concerns; no adversarial verification |
| Pure cosine similarity matching | Kotekar & Mohan (2026) original | Cannot generalize to unprecedented "black swan" events; needs LLM reasoning |
| Inverse RL (T-REX/G-Learner) | Halperin et al. (2024) | Produces unexplainable policies; used only as evaluation baseline |

---

# Section 2: Complete System Architecture

## 2.1 Architecture Overview

The system is organized into **7 architectural layers**:

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│              (Next.js Frontend Application)              │
├─────────────────────────────────────────────────────────┤
│                      API LAYER                           │
│              (FastAPI REST + WebSocket)                   │
├─────────────────────────────────────────────────────────┤
│                  ORCHESTRATION LAYER                      │
│         (LangGraph State Machine / DAG)                   │
├──────────┬──────────┬──────────┬────────────────────────┤
│ REASONING│  DEBATE  │  DATA    │    SAFETY              │
│  LAYER   │  LAYER   │ INGESTION│    LAYER               │
│(LLM Agents│(Strategist│  LAYER  │(M-SAEA Probes         │
│ Personas)│ Critic   │(Specialist│ VIX Thresholds        │
│          │ Moderator)│ Agents)  │ SEBI Constraints)     │
├──────────┴──────────┴──────────┴────────────────────────┤
│               COMPUTATIONAL LAYER                        │
│    (Python: NumPy, Pandas, SciPy — Deterministic Math)   │
├─────────────────────────────────────────────────────────┤
│                   KNOWLEDGE LAYER                        │
│  (Neo4j MFKG + FAISS Vector Store + PostgreSQL + Redis)  │
├─────────────────────────────────────────────────────────┤
│                   EXTERNAL DATA LAYER                    │
│   (Market APIs + News APIs + RBI Data + Web Scraping)    │
└─────────────────────────────────────────────────────────┘
```

## 2.2 End-to-End Data Flow

```
User Input (e.g., "Create a defensive portfolio for current market")
    │
    ▼
[1] INPUT PROCESSING (FastAPI)
    ├── Parse user intent
    ├── Extract parameters (risk tolerance, investment horizon, amount)
    └── Create LangGraph initial state dictionary
    │
    ▼
[2] ORCHESTRATOR (LangGraph Supervisor Node)
    ├── Determines which agents to activate
    ├── Sets execution order (parallel where possible)
    └── Initializes shared state
    │
    ▼
[3] DATA INGESTION (Parallel Specialist Agents)
    ├── Market Data Agent → yfinance API → OHLCV, P/E, ROE
    ├── News Agent → NewsAPI/RSS → FAISS similarity search
    ├── Macro Agent → RBI API → Inflation, Repo Rate, GDP
    └── VIX Agent → NSE India VIX → Regime classification
    │
    ▼
[4] DATA VALIDATION & FRESHNESS CHECK (Functional Node)
    ├── Timestamp verification (reject data older than TTL)
    ├── Source cross-validation
    ├── Missing data handling
    └── Regime classification (Bull/Bear/Volatile)
    │
    ▼
[5] KNOWLEDGE RETRIEVAL (Functional Node)
    ├── Query Neo4j MFKG: "Find top 3 historical regimes matching current state"
    ├── Extract historical fund manager actions from those regimes
    ├── Retrieve relevant news episodes from FAISS
    └── Package as "Historical Context" for reasoning agents
    │
    ▼
[6] REASONING & DEBATE (LLM Reasoning Nodes)
    ├── STRATEGIST: Proposes 2-3 portfolio alternatives with reasoning
    ├── CRITIC: Applies CoVe + M-SAEA probes to challenge proposals
    ├── Loop: If Critic finds High-severity issues → back to Strategist
    └── MODERATOR: Synthesizes final approved allocation (qualitative)
    │
    ▼
[7] MATHEMATICAL EXECUTION (Python Functional Node)
    ├── Convert qualitative allocation → exact decimal weights
    ├── Apply SEBI constraints (sector caps, minimum diversification)
    ├── Calculate: Sharpe ratio, expected return, max drawdown
    ├── Verify: weights sum to 100%, no constraint violations
    └── If validation fails → retry loop back to Reasoning
    │
    ▼
[8] RESPONSE GENERATION (Functional Node)
    ├── Package portfolio with full reasoning trace
    ├── Attach citations (which historical episodes were used)
    ├── Attach confidence score (1-10)
    ├── Generate human-readable summary
    └── Create visualization data (pie chart, sector breakdown)
    │
    ▼
[9] FRONTEND PRESENTATION
    ├── Portfolio allocation table
    ├── Reasoning trace (expandable)
    ├── Historical comparison chart
    ├── Risk metrics dashboard
    └── Source citations
```

---

# Section 3: Multimodal Agentic Architecture

## 3.1 Agent Inventory — Minimum Viable Set

We need exactly **7 agents** organized into 3 tiers. Each agent is justified below.

### Tier 1: Data Ingestion Agents (4 agents, run in parallel)

#### Agent 1: Market Data Agent
| Property | Value |
|----------|-------|
| **Purpose** | Fetch and structure real-time Indian equity market data |
| **Inputs** | List of NIFTY stocks, date range |
| **Outputs** | Structured JSON: OHLCV, P/E, ROE, market cap, 52-week high/low |
| **Tools** | yfinance Python library, NSE India scraper |
| **APIs** | Yahoo Finance (free), NSE India website |
| **Model** | None — purely functional (Python) |
| **Memory** | Redis cache (TTL: 15 minutes for intraday, 24h for daily) |
| **Math Operations** | Calculate returns, volatility, Sharpe ratio, drawdown |
| **Communicates With** | Orchestrator (sends structured market data to shared state) |
| **Failure Cases** | API rate limit → retry with exponential backoff; API down → use cached data |
| **Validation** | Verify all numeric fields are present; cross-check with backup source |
| **Why Necessary** | Raw market data is the foundation; without it, no agent can reason |

#### Agent 2: News & Sentiment Agent
| Property | Value |
|----------|-------|
| **Purpose** | Fetch financial news and ground it against historical news reactions |
| **Inputs** | Stock tickers, current date |
| **Outputs** | Structured JSON: headline, source, timestamp, sentiment score (-1 to 1), top-3 FAISS-matched historical headlines with actual returns |
| **Tools** | NewsAPI, FAISS vector store, Sentence Transformers |
| **APIs** | NewsAPI (free: 100 requests/day), Google News RSS (free, unlimited) |
| **Model** | Sentence-BERT (all-MiniLM-L6-v2) for embeddings; LLM for sentiment scoring |
| **Memory** | FAISS index (persistent on disk); historical news corpus |
| **Math Operations** | Cosine similarity for FAISS retrieval |
| **Communicates With** | Orchestrator (sends sentiment context to shared state) |
| **Failure Cases** | NewsAPI limit hit → fallback to Google News RSS scraping |
| **Validation** | Timestamp check (reject news older than 48 hours for "current" queries) |
| **Why Necessary** | Sentiment drives short-term market moves; FAISS grounding prevents naive LLM assumptions (AlphaNiftyAI finding) |

#### Agent 3: Macroeconomic Agent
| Property | Value |
|----------|-------|
| **Purpose** | Fetch and interpret Indian macroeconomic indicators |
| **Inputs** | Current date |
| **Outputs** | Structured JSON: Repo Rate, CPI, GDP growth, FII flows, India VIX, USD/INR |
| **Tools** | RBI DBIE API, FRED API, yfinance (for VIX) |
| **APIs** | RBI DBIE (free), FRED (free: 120 requests/min), Yahoo Finance |
| **Model** | None for data fetch; LLM for interpretation summary |
| **Memory** | PostgreSQL (historical macro data, updated daily) |
| **Math Operations** | Regime classification: VIX > 25 = "Crisis", 20-25 = "High Vol", 15-20 = "Normal", < 15 = "Low Vol" |
| **Communicates With** | Orchestrator (sends macro context + regime classification) |
| **Failure Cases** | RBI API delayed → use last known values with staleness warning |
| **Validation** | Cross-validate repo rate with multiple sources |
| **Why Necessary** | Maheswari & Reddy (2023) proved market timing requires macro awareness; Bhambhani (2025) proved VIX drives defensive rotations |

#### Agent 4: MFKG Knowledge Agent
| Property | Value |
|----------|-------|
| **Purpose** | Query the Neo4j Mutual Fund Knowledge Graph for historical fund manager episodes |
| **Inputs** | Current market state vector (from Agents 1-3) |
| **Outputs** | Top-K matching historical episodes: {regime, date, fund_name, manager_action, sector_weights, return_achieved} |
| **Tools** | Neo4j Python driver, Cypher queries |
| **APIs** | None (local Neo4j instance) |
| **Model** | None — deterministic graph queries |
| **Memory** | Neo4j graph database (the MFKG itself) |
| **Math Operations** | Cosine similarity between current state vector and historical state vectors |
| **Communicates With** | Orchestrator (sends historical episodes to shared state) |
| **Failure Cases** | No close match found (cosine sim < 0.6) → flag as "unprecedented regime" |
| **Validation** | Verify retrieved episodes are from funds that actually outperformed benchmark |
| **Why Necessary** | This is the episodic memory — the core innovation from Kotekar & Mohan (2026) that solves LLM amnesia |

### Tier 2: Reasoning Agents (The Triad — 3 LLM agents, run sequentially)

#### Agent 5: The Strategist
| Property | Value |
|----------|-------|
| **Purpose** | Analyze all data and propose 2-3 portfolio allocation alternatives with explicit reasoning |
| **Inputs** | Full shared state: market data, sentiment, macro context, MFKG historical episodes |
| **Outputs** | 2-3 portfolio proposals, each with: sector weights, stock picks, reasoning chain, risk assessment, confidence (1-10) |
| **Tools** | None (pure LLM reasoning) |
| **APIs** | LLM API (Gemini / local Llama) |
| **Model** | Primary: Gemini 2.5 Flash (free tier); Fallback: Llama 3.1 8B (local) |
| **Memory** | Conversation context within current session |
| **Math Operations** | None — qualitative reasoning only; all math deferred to Functional Nodes |
| **Communicates With** | Critic (sends proposals for adversarial review) |
| **Failure Cases** | Hallucination detected → Critic sends back for revision (max 3 loops) |
| **Validation** | Must provide explicit Chain-of-Thought reasoning; must cite historical episodes |
| **Why Necessary** | The core "brain" that converts data into investment theses — mirrors the human fund manager's qualitative reasoning |

#### Agent 6: The Critic
| Property | Value |
|----------|-------|
| **Purpose** | Adversarially audit the Strategist's proposals using Chain-of-Verification (CoVe) and M-SAEA probes |
| **Inputs** | Strategist's proposals + all shared state data |
| **Outputs** | Critique report: {issues: [{severity: High/Medium/Low, description, fix}], approved: bool} |
| **Tools** | M-SAEA probe scripts (Python), SEBI constraint checker |
| **APIs** | LLM API (same as Strategist) |
| **Model** | Same LLM as Strategist |
| **Memory** | None (stateless adversarial review) |
| **Math Operations** | Runs 6 key M-SAEA probes: (1) Hallucination Detection, (2) Temporal Awareness, (3) Confidence Calibration, (4) Cross-Agent Divergence, (5) Error Propagation, (6) SEBI Constraint Compliance |
| **Communicates With** | Strategist (sends critique back for revision) → Moderator (forwards if approved) |
| **Failure Cases** | If 3 revision loops fail → escalate to user with explanation |
| **Validation** | Must answer its own verification questions (CoVe); must score each probe pass/fail |
| **Why Necessary** | Without adversarial checking, the Strategist's hallucinations would propagate unchecked (Chen et al., 2026 "Optimistic Trust" problem) |

#### Agent 7: The Moderator
| Property | Value |
|----------|-------|
| **Purpose** | Make the final portfolio decision; reject any proposal with unresolved High-severity critiques |
| **Inputs** | Strategist's final proposal + Critic's approval report |
| **Outputs** | Final approved qualitative allocation → sent to Mathematical Execution node |
| **Tools** | None (pure LLM synthesis) |
| **APIs** | LLM API |
| **Model** | Same LLM |
| **Memory** | Conversation context |
| **Math Operations** | None — final mathematical execution is in the Functional Node |
| **Communicates With** | Mathematical Execution Functional Node (sends approved qualitative allocation) |
| **Failure Cases** | If any High-severity critique is unresolved → reject and return to user |
| **Validation** | Decision log generation (auditable); confidence score aggregation |
| **Why Necessary** | Prevents the system from acting on contested decisions; provides final consensus point and audit trail |

### Functional Nodes (Not agents — deterministic Python code)

| Node | Responsibility | Libraries |
|------|---------------|-----------|
| **Data Validation Node** | Timestamp checks, missing data handling, schema validation | Pydantic, datetime |
| **Regime Classification Node** | Classify market regime from VIX + momentum indicators | NumPy, Pandas |
| **Mathematical Execution Node** | Convert qualitative allocation → exact weights; apply constraints | NumPy, SciPy (optimize), Pandas |
| **SEBI Constraint Node** | Enforce: sector caps, minimum diversification, category mandates | Pure Python rule engine |
| **Portfolio Metrics Node** | Calculate Sharpe, CAGR, Max Drawdown, tracking error | NumPy, Pandas |
| **Response Formatting Node** | Package results into frontend-ready JSON | JSON, Jinja2 |

## 3.2 Agent Communication Architecture

```
                    ┌──────────────┐
                    │ ORCHESTRATOR │
                    │  (LangGraph  │
                    │   Supervisor)│
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐ ┌────▼─────┐ ┌───▼──────┐
        │ PARALLEL  │ │ PARALLEL │ │ PARALLEL │
        │ Market    │ │ News     │ │ Macro    │
        │ Data Agt  │ │ Sent Agt │ │ Agent    │
        └─────┬─────┘ └────┬─────┘ └───┬──────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼───────┐
                    │  DATA        │
                    │  VALIDATION  │
                    │  (Func Node) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  MFKG        │
                    │  KNOWLEDGE   │
                    │  AGENT       │
                    └──────┬───────┘
                           │
              ┌────────────▼────────────┐
              │                         │
              │    DEBATE LOOP                                       │
              │  ┌───────────────────────────────────────────────┐   │
              │  │                  STRATEGIST                   │   │
              │  │ ┌──────────┐    ┌──────────┐    ┌───────────┐ │   │
              │  │ │Short Term│    │ Mid Term │    │ Long Term │ │◄─┐│
              │  │ └────┬─────┘    └────┬─────┘    └─────┬─────┘ │  ││
              │  └──────┼───────────────┼────────────────┼───────┘  ││
              │         │               │                │          ││
              │  ┌──────▼───────────────▼────────────────▼───────┐  ││
              │  │                    CRITIC                     │──┘│
              │  │                (CoVe+M-SAEA)                  │   │
              │  └──────────────────────┬────────────────────────┘   │
              │                         │                            │
              │  ┌──────────────────────▼────────────────────────┐   │
              │  │                   MODERATOR                   │   │
              │  └──────────────────────┬────────────────────────┘   │
              └─────────────────────────┼────────────────────────────┘
                         │
                  ┌──────▼───────┐
                  │ MATHEMATICAL │
                  │  EXECUTION   │
                  │ (Func Node)  │
                  └──────┬───────┘
                         │
                  ┌──────▼───────┐
                  │  RESPONSE    │
                  │  GENERATION  │
                  └──────────────┘
```

**Information passed between agents:**
- Data Agents → Orchestrator: Structured JSON (market data, sentiment scores, macro indicators)
- Orchestrator → MFKG Agent: Current state vector
- MFKG Agent → Strategist: Historical episodes (past regimes + expert actions)
- Strategist → Critic: Portfolio proposals with reasoning chains
- Critic → Strategist: Critique with severity-classified issues (revision loop)
- Critic → Moderator: Approved proposal + audit report
- Moderator → Math Node: Qualitative allocation intent
- Math Node → Response: Exact numerical portfolio + metrics

---

# Section 4: Separation of LLM Reasoning from Deterministic Computation

## 4.1 What LLMs Handle vs. What Python Handles

| Operation | Handled By | Rationale |
|-----------|-----------|-----------|
| Reading and summarizing news articles | LLM | Qualitative text comprehension |
| Interpreting macroeconomic conditions | LLM | Requires contextual understanding |
| Proposing investment theses | LLM | Creative reasoning about market dynamics |
| Debating and critiquing proposals | LLM | Adversarial reasoning requires language |
| Generating human-readable explanations | LLM | Natural language generation |
| **Calculating portfolio weights** | **Python** | Precise decimal arithmetic |
| **Computing Sharpe ratio, CAGR, drawdown** | **Python** | Deterministic mathematical formulas |
| **Enforcing SEBI constraints** | **Python** | Rule-based logic, no ambiguity |
| **Querying Neo4j graph database** | **Python** | Structured Cypher queries |
| **Computing cosine similarity** | **Python** | NumPy linear algebra |
| **Validating weights sum to 100%** | **Python** | Arithmetic verification |
| **Currency/unit conversion** | **Python** | Deterministic lookup |
| **Backtesting portfolio performance** | **Python** | Statistical computation |

## 4.2 Agent-to-Computation Interface

```
AGENT LAYER (LLM)
    │
    │  Structured JSON Output (via Pydantic schema)
    │  e.g., {"intent": "allocate", "sectors": {"IT": "high", "Banking": "medium"}}
    │
    ▼
TOOL/FUNCTION LAYER (LangGraph Tool Nodes)
    │
    │  Converts qualitative intent → numerical parameters
    │  e.g., "high" → 0.25-0.35 weight range
    │
    ▼
PYTHON COMPUTATIONAL LAYER
    │
    │  NumPy/SciPy optimization
    │  Constraint satisfaction (weights sum to 1.0, sector caps)
    │  Portfolio metrics calculation
    │
    ▼
VALIDATION LAYER
    │
    │  Pydantic schema validation
    │  Constraint verification
    │  If FAIL → return error to Agent Layer with specific violation
    │
    ▼
AGENT LAYER (receives validated result or error for retry)
```

**Why this separation is beneficial:**
1. **Reproducibility**: Same inputs to Python always produce same outputs
2. **Auditability**: Every mathematical step is logged and traceable
3. **Correctness**: Eliminates the #1 failure mode identified by Mantshimuli & Mwamba (2026)
4. **Testability**: Mathematical functions can be unit-tested independently
5. **SEBI Compliance**: Regulatory constraints are enforced by code, not by LLM "promises"

---

# Section 5: Data Architecture

## 5.1 Complete Data Requirements

| Data Category | Required Data | Primary Source | API | Free? | Free Limits | Paid Alternative | Real-Time? | Historical? | Backup Source | Notes |
|--------------|---------------|---------------|-----|-------|-------------|-----------------|------------|-------------|---------------|-------|
| **Stock Prices** | OHLCV for NIFTY 50/200 stocks | Yahoo Finance | yfinance (Python) | ✅ Yes | Unofficial, no formal limits | Zerodha Kite API (₹2000/mo) | 15-min delay | ✅ Full history | Google Finance | yfinance is reliable but unofficial |
| **Mutual Fund NAV** | Daily NAV for top 50 funds | AMFI India | amfiindia.com/spits/NAVAll.txt | ✅ Yes | No limits | N/A | Daily (EOD) | ✅ Full history | mfapi.in (free) | Official AMFI data, updated daily at 11 PM IST |
| **Mutual Fund Holdings** | Monthly portfolio disclosures | AMFI / SEBI | Manual download / web scrape | ✅ Yes | Monthly only | N/A | Monthly | ✅ 3+ years | ValueResearchOnline | Key data for MFKG construction |
| **India VIX** | Real-time volatility index | NSE India | nseindia.com scraper | ✅ Yes | Rate limited | N/A | ✅ Real-time | ✅ Daily since 2009 | yfinance (^INDIAVIX) | Critical for regime classification |
| **Macroeconomic (India)** | Repo Rate, CPI, GDP, WPI | RBI DBIE | dbie.rbi.org.in/DBIE | ✅ Yes | No formal limits | N/A | Monthly/Quarterly | ✅ Since 1991 | FRED (for select India series) | Official RBI database |
| **Global Macro** | US Fed Rate, US CPI, Global VIX | FRED (St. Louis Fed) | api.stlouisfed.org | ✅ Yes | 120 req/min | N/A | Daily | ✅ Decades | World Bank API | Need API key (free registration) |
| **Financial News (India)** | Headlines for NIFTY stocks | NewsAPI.org | newsapi.org | ✅ Free tier | 100 req/day, 1 month history | NewsAPI Paid ($449/mo) | ✅ Near real-time | ❌ 1 month only | Google News RSS (free, unlimited) | Free tier sufficient for development |
| **Financial News (Global)** | Bloomberg/Reuters style | Google News RSS | RSS feeds | ✅ Yes | Unlimited | N/A | ✅ Near real-time | ❌ Limited | Finviz RSS | No authentication needed |
| **Fundamental Data** | P/E, ROE, EPS, Market Cap | Yahoo Finance | yfinance | ✅ Yes | No formal limits | Financial Modeling Prep ($19/mo) | Daily | ✅ 5+ years | Screener.in (scrape) | yfinance provides comprehensive fundamentals |
| **FII/DII Flows** | Daily institutional buy/sell data | NSDL / NSE | depositories.in scraper | ✅ Yes | Rate limited | N/A | ✅ Daily | ✅ Years | Moneycontrol.com | Important for flow-based regime detection |
| **Sector Indices** | NIFTY Bank, IT, Pharma, etc. | NSE India | nseindia.com / yfinance | ✅ Yes | No limits | N/A | 15-min delay | ✅ Full | Google Finance | Track sector rotation patterns |

---

# Section 6: Complete API Inventory

## 6A. Completely Free APIs

| API | Provider | Purpose | Auth | Free Limits | Real-Time? | Historical? | Reliability | Agent Using It |
|-----|----------|---------|------|-------------|------------|-------------|-------------|---------------|
| **yfinance** | Yahoo Finance (unofficial) | Stock prices, fundamentals, VIX | None | Unofficial; ~2000 req/hr | 15-min delay | ✅ Full | High (widely used) | Market Data Agent |
| **AMFI NAV API** | AMFI India | Mutual fund NAV data | None | Unlimited | Daily EOD | ✅ Full | Very High (official) | MFKG Knowledge Agent |
| **mfapi.in** | Community | Mutual fund NAV/history | None | Unlimited | Daily | ✅ Full | Medium | Backup for AMFI |
| **RBI DBIE** | Reserve Bank of India | Macro indicators | None | No formal limits | Monthly/Qtr | ✅ Since 1991 | Very High (official) | Macroeconomic Agent |
| **FRED API** | St. Louis Federal Reserve | US/Global macro data | API Key (free) | 120 req/min | Daily | ✅ Decades | Very High (official) | Macroeconomic Agent |
| **Google News RSS** | Google | News headlines | None | Unlimited | Near real-time | Limited | High | News & Sentiment Agent |
| **World Bank API** | World Bank | GDP, inflation by country | None | Unlimited | Annual/Qtr | ✅ Decades | Very High | Macroeconomic Agent (backup) |

## 6B. Freemium APIs

| API | Provider | Free Tier | Free Limits | When Insufficient | Cost to Upgrade | Recommendation |
|-----|----------|-----------|-------------|-------------------|-----------------|----------------|
| **NewsAPI** | newsapi.org | 100 req/day | 1 month history; no commercial use | When we need >100 daily queries or production deployment | $449/mo (Business) | Use free tier for dev; switch to RSS scraping for production |
| **Gemini API** | Google | 15 RPM, 1M tokens/min | Rate limited; may throttle | When running batch backtests or >15 concurrent users | Pay-as-you-go (~$0.15/1M input tokens for Flash) | Use free tier; sufficient for single-user application |
| **Financial Modeling Prep** | financialmodelingprep.com | 250 req/day | Limited endpoints | When we need full SEC filings / earnings transcripts | $19/mo | Skip — yfinance covers our needs |

## 6C. Paid APIs (with justification for whether needed)

| API | Why Potentially Needed | Free Alternative | Alternative Limitations | Cost | Recommendation |
|-----|----------------------|------------------|------------------------|------|----------------|
| **Zerodha Kite API** | True real-time Indian stock data | yfinance (15-min delay) | 15-minute delay; unofficial | ₹2000/mo | **Not needed** for v1. 15-min delay is acceptable for portfolio-level decisions (not HFT) |
| **Bloomberg Terminal API** | Institutional-grade data | yfinance + AMFI | Less comprehensive corporate actions data | $24,000/yr | **Not needed**. Academic project; free data is sufficient |
| **OpenAI GPT-4o** | Best-in-class LLM reasoning | Gemini Flash (free) / Llama 3.1 (local) | Slightly lower reasoning quality | $2.50/1M input | **Not needed**. Gemini Flash is competitive and free |

---

# Section 7: Data Sources Beyond APIs

| Category | Required? | Method | Justification |
|----------|-----------|--------|---------------|
| **Financial News** | ✅ Yes | RSS + NewsAPI | Core input for sentiment analysis |
| **Mutual Fund Holdings (PDFs)** | ✅ Yes | Web Scrape + PDF Parsing | Monthly SEBI disclosures are in PDF format |
| **RBI Press Releases** | ✅ Yes | Web Scrape (RBI website) | Monetary policy decisions affect all asset classes |
| **SEBI Circulars** | ✅ Yes | Web Scrape | Regulatory changes affect fund constraints |
| **Earnings Call Transcripts** | ⚠️ Nice-to-have | Web Scrape (MoneyControl) | Used by MarketSenseAI but not critical for v1 |
| **Social/Community Data** | ❌ No | N/A | Unreliable; introduces noise; legal concerns |
| **Images/Video/Audio** | ❌ No | N/A | Not relevant to portfolio management |
| **OCR** | ⚠️ Limited | PyMuPDF / pdfplumber | Only for extracting tables from mutual fund PDFs |
| **Weather/Environmental** | ❌ No | N/A | Not relevant |
| **Geospatial/Maps** | ❌ No | N/A | Not relevant |

---

# Section 8: Live Data and Staleness Prevention

## 8.1 Data Freshness Layer

| Data Type | Freshness Requirement | TTL (Cache) | Refresh Mechanism | Fallback if Stale |
|-----------|----------------------|-------------|-------------------|-------------------|
| Stock Prices | < 15 minutes | 15 min | API poll every 15 min during market hours | Use last cached price + warn user |
| India VIX | < 30 minutes | 30 min | API poll every 30 min | Use last known VIX + warn |
| Mutual Fund NAV | < 24 hours | 24 hours | Daily fetch at 11:30 PM IST | Use previous day NAV |
| News Headlines | < 4 hours | 4 hours | Poll NewsAPI/RSS every 2 hours | Use cached headlines + warn |
| RBI Macro Data | < 7 days | 7 days | Weekly check for updates | Use last known values (stable) |
| MFKG Data | Static (monthly updates) | No expiry | Manual update when new AMFI data released | Always valid |

## 8.2 Freshness Validation Logic

```python
def validate_freshness(data_item):
    """Reject stale data before any agent can use it."""
    age = datetime.now() - data_item.retrieved_at
    if age > data_item.ttl:
        return {
            "status": "STALE",
            "message": f"Data is {age} old, exceeds TTL of {data_item.ttl}",
            "action": "REFRESH_OR_WARN"
        }
    return {"status": "FRESH"}
```

Every data item entering the shared LangGraph state must pass through this validation. The Critic agent's Temporal Awareness probe (M-SAEA Layer 1, Probe 2) will independently verify that no stale data was used in the Strategist's reasoning.

---

# Section 9: Agent Memory and Knowledge Architecture

| Component | What Is Stored | Where | How Long | Who Accesses | When Retrieved | When Deleted |
|-----------|---------------|-------|----------|-------------|----------------|-------------|
| **MFKG (Episodic Memory)** | Historical fund manager actions, market states, returns | Neo4j | Permanent | MFKG Agent, Strategist | Every portfolio creation request | Never (grows over time) |
| **News Embedding Index** | FAISS vectors of 30K+ historical news articles | FAISS (disk) | Permanent | News Agent | During sentiment grounding | Never |
| **Session State** | Current conversation, user preferences, active portfolio | LangGraph State Dict (in-memory) | Duration of session | All agents | Throughout the workflow | End of session |
| **User Profiles** | Risk tolerance, investment horizon, preferred sectors | PostgreSQL | Until user deletes | Orchestrator, Strategist | Start of each request | On user request |
| **Cached Market Data** | Recent stock prices, VIX, macro indicators | Redis | Per TTL (15 min to 7 days) | Data Ingestion Agents | Before making API calls | On TTL expiry |
| **Decision Logs** | Full reasoning traces, audit trails | PostgreSQL | 1 year | Moderator (writes), User (reads) | On user request for historical decisions | After 1 year or on user request |
| **Agent Conversation History** | The Strategist-Critic debate transcript | LangGraph State | Duration of request | Moderator | During final synthesis | End of request |

**What we do NOT store:**
- Long-term "personality" memory for agents (agents are stateless between requests)
- Embeddings of every user message (unnecessary for portfolio creation)
- Full document stores of news articles (only embeddings + metadata)

---

# Section 10: Multimodal Processing Pipeline

For v1, the system is primarily **text + structured data**. Multimodal is limited to:

| Modality | Input | Preprocessing | Extraction | Agent | Output |
|----------|-------|---------------|------------|-------|--------|
| **Structured Data** (OHLCV, NAV, Macro) | API JSON responses | Pydantic validation, NaN handling | Pandas DataFrame | Market Data / Macro Agent | Metrics, regime classification |
| **Unstructured Text** (News) | RSS/API headlines | Deduplication, language filtering (English only) | Sentence-BERT embeddings → FAISS | News Agent | Sentiment scores + historical grounding |
| **PDF Documents** (Fund Holdings) | AMFI/SEBI monthly PDF reports | pdfplumber table extraction | Pandas DataFrame | MFKG Agent (offline pipeline) | Structured holdings data → Neo4j |
| **User Text** (Chat input) | Natural language query | Intent classification | Parameter extraction | Orchestrator | Structured request parameters |

**Models used per modality:**
- **Text comprehension**: LLM (Gemini Flash / Llama 3.1)
- **Text embedding**: Sentence-BERT (all-MiniLM-L6-v2) — open source, runs locally
- **PDF extraction**: pdfplumber (Python library) — no ML needed
- **Structured data**: Pure Python (Pandas, NumPy) — no ML needed

---

# Section 11: Model Selection

| Purpose | Primary Model | Why | Fallback | Cost | Context Window |
|---------|--------------|-----|----------|------|----------------|
| **LLM Reasoning (Strategist, Critic, Moderator)** | Gemini 2.5 Flash | Free tier (15 RPM); excellent tool-calling; structured output | Llama 3.1 8B Instruct (local via Ollama) | Free / Free | 1M tokens / 128K tokens |
| **Text Embeddings** | all-MiniLM-L6-v2 | Open source; 384-dim; fast; runs on CPU | text-embedding-3-small (OpenAI) | Free / $0.02/1M tokens | 512 tokens |
| **Sentiment Scoring** | Gemini Flash (via prompt) | Already loaded for reasoning; saves model switching | FinBERT (HuggingFace, local) | Free | N/A |
| **PDF Table Extraction** | pdfplumber (rule-based) | Deterministic; no GPU needed; handles Indian mutual fund PDFs well | Camelot (Python) | Free | N/A |

**Hardware Requirements:**
- **Development**: MacBook (Apple Silicon) — sufficient for Llama 3.1 8B via Ollama + all Python computation
- **Production**: Any Linux server with 16GB RAM — Neo4j + FastAPI + FAISS + Ollama

---

# Section 12: Backend Architecture

## 12.1 Technology Choices

| Component | Technology | Why |
|-----------|-----------|-----|
| **Language** | Python 3.11+ | LangGraph, ML libraries, and financial computation are all Python-native |
| **Web Framework** | FastAPI | Async support; WebSocket for real-time; auto-generated OpenAPI docs |
| **Agent Orchestration** | LangGraph | Validated by Hajaghaie & Thulasiram (2025); supports Reasoning + Functional nodes natively |
| **Graph Database** | Neo4j Community Edition | Free; Cypher query language; perfect for MFKG relationship modeling |
| **Relational Database** | PostgreSQL | User profiles, decision logs, macro data history |
| **Cache** | Redis | TTL-based caching for market data; session state |
| **Vector Store** | FAISS (disk-based) | Free; fast cosine similarity; handles 30K+ news vectors easily |
| **Task Queue** | Celery + Redis | Background data refresh jobs (market data polling, MFKG updates) |
| **Real-time** | WebSocket (FastAPI native) | Stream agent reasoning to frontend in real-time |
| **Authentication** | JWT (PyJWT) | Stateless auth; simple for academic project |
| **Containerization** | Docker + Docker Compose | Reproducible deployment; isolate Neo4j, Redis, FastAPI |
| **Monitoring** | Python logging + Loguru | Structured JSON logs; agent-specific log channels |
| **Secrets** | python-dotenv + .env files | Simple; sufficient for academic project |

## 12.2 Backend Flow Diagram

```
Frontend (Next.js)
    │
    ▼ REST API / WebSocket
┌───────────────────────┐
│       FastAPI          │
│  ┌─────────────────┐  │
│  │ Auth Middleware  │  │
│  │ (JWT validation) │  │
│  └────────┬────────┘  │
│           │           │
│  ┌────────▼────────┐  │
│  │ Request Router   │  │
│  │ /api/portfolio   │  │
│  │ /api/backtest    │  │
│  │ /api/explain     │  │
│  └────────┬────────┘  │
│           │           │
│  ┌────────▼────────┐  │
│  │  LangGraph      │  │
│  │  Orchestrator   │  │◄──── Redis (cache)
│  │  (State Machine)│  │◄──── Neo4j (MFKG)
│  │                 │  │◄──── FAISS (vectors)
│  │  Agents run here│  │◄──── PostgreSQL (users)
│  └────────┬────────┘  │
│           │           │
│  ┌────────▼────────┐  │
│  │ WebSocket Stream │  │
│  │ (real-time agent │  │
│  │  reasoning feed) │  │
│  └─────────────────┘  │
└───────────────────────┘
```

---

# Section 13: Frontend Architecture

## 13.1 Screens and User Flow

| Screen | Purpose | Key Components |
|--------|---------|---------------|
| **1. Dashboard** | Overview of current market regime and active portfolio | VIX gauge, regime indicator (Bull/Bear/Volatile), portfolio summary card, recent news feed |
| **2. Portfolio Creation** | Main interaction page — user describes goals, AI creates portfolio | Chat interface, risk tolerance selector, investment amount input, timeline picker |
| **3. Portfolio Result** | Display AI-generated portfolio with full reasoning | Sector allocation pie chart, stock table with weights, confidence score badge, expandable reasoning trace |
| **4. Historical Comparison** | Compare AI portfolio vs. actual fund manager performance | Line chart (AI vs. benchmark vs. manager), metrics table (Sharpe, CAGR, Max DD) |
| **5. Agent Activity** | (Optional) View real-time agent debate | Strategist proposal cards, Critic critique highlights, Moderator decision summary |
| **6. Decision Log** | Past portfolio decisions with audit trail | Sortable table with date, regime, decision, reasoning, outcome |

## 13.2 Technology

| Component | Technology | Why |
|-----------|-----------|-----|
| **Framework** | Next.js 14 (App Router) | SSR for SEO; API routes; React ecosystem |
| **Styling** | Tailwind CSS | Rapid UI development; consistent design system |
| **Charts** | Recharts | React-native; handles financial charts well |
| **Real-time** | WebSocket (native) | Stream agent reasoning during portfolio creation |
| **State Management** | React Context + SWR | Lightweight; SWR for API data caching |

## 13.3 What Users See vs. What Stays Internal

| Visible to User | Internal Only |
|-----------------|---------------|
| Final portfolio allocation | Raw API responses |
| Confidence score (1-10) | M-SAEA probe pass/fail details |
| Reasoning summary | Full Strategist-Critic debate transcript |
| Historical episodes cited | MFKG Cypher queries |
| Risk metrics (Sharpe, DD) | Intermediate computational steps |
| Current market regime | VIX threshold logic |
| Source citations | FAISS similarity scores |

---

# Section 14: Security Architecture

| Risk | Mitigation | Implementation |
|------|-----------|---------------|
| **API Key Exposure** | Environment variables; never in source code | python-dotenv; .env in .gitignore |
| **Prompt Injection** | Input sanitization; system prompts are read-only | Pydantic input validation; LangGraph system messages |
| **LLM Hallucination** | Critic agent + M-SAEA probes + mathematical verification | Hardcoded in Critic node; Python validation layer |
| **Malicious File Upload** | Restrict to PDF only; validate MIME type | FastAPI file validation; pdfplumber safe parsing |
| **Agent Privilege Boundaries** | Agents cannot execute arbitrary code; tools are whitelisted | LangGraph tool binding; no shell access |
| **Data Leakage** | User portfolios isolated by user_id | PostgreSQL row-level security; JWT user context |
| **Rate Limiting** | Limit API requests per user | FastAPI middleware (slowapi) |
| **External API Security** | All external calls over HTTPS; no credentials in URLs | requests library with proper headers |

**Agent Permission Matrix:**

| Agent | Can Call External APIs | Can Write to DB | Can Execute Code | Can Access Other Users |
|-------|----------------------|-----------------|-----------------|----------------------|
| Market Data | ✅ (yfinance only) | ❌ | ❌ | ❌ |
| News Agent | ✅ (NewsAPI, RSS only) | ❌ | ❌ | ❌ |
| Macro Agent | ✅ (RBI, FRED only) | ❌ | ❌ | ❌ |
| MFKG Agent | ❌ | ✅ (read-only Neo4j) | ❌ | ❌ |
| Strategist | ❌ | ❌ | ❌ | ❌ |
| Critic | ❌ | ❌ | ✅ (M-SAEA probes only) | ❌ |
| Moderator | ❌ | ✅ (write decision log) | ❌ | ❌ |

---

# Section 15: Agent Guardrails and Verification

| Guardrail | Implementation | Trigger |
|-----------|---------------|---------|
| **Structured Output** | Pydantic models for all agent outputs | Every agent call |
| **Schema Validation** | JSON schema enforcement via LangGraph | Every state transition |
| **Source Attribution** | Agents must cite MFKG episode IDs or news sources | Strategist output validation |
| **Data Freshness** | Timestamp verification in Data Validation Node | Before data enters shared state |
| **Mathematical Verification** | Python asserts: `abs(sum(weights) - 1.0) < 0.001` | After Mathematical Execution Node |
| **SEBI Constraint Check** | Rule engine: sector caps, category mandates | After weight calculation |
| **Cross-Agent Verification** | Critic independently recalculates key metrics | During CoVe phase |
| **Confidence Threshold** | If confidence < 4/10, refuse to execute; ask user for guidance | Moderator output |
| **Retry Mechanism** | Max 3 Strategist-Critic loops before escalation | Debate loop counter |
| **Hallucination Detection** | M-SAEA Probe 1: Cross-reference claims against MFKG data | Critic node |
| **Temporal Awareness** | M-SAEA Probe 2: Verify data dates match current period | Critic node |
| **Human-in-the-Loop** | Present portfolio to user with "Approve/Modify/Reject" buttons | Before any execution |

**When an agent is uncertain (confidence < 4):**
1. Moderator flags the decision as "LOW CONFIDENCE"
2. The full debate transcript is surfaced to the user
3. User is presented with: "The AI is uncertain. Here are the alternatives considered. Please choose or modify."
4. No autonomous action is taken

---

# Section 16: End-to-End Workflow Examples

## Example 1: Simple Portfolio Creation

**User Input:** "Create a balanced portfolio for ₹5,00,000 with moderate risk tolerance"

| Step | Component | Action | Output |
|------|-----------|--------|--------|
| 1 | FastAPI | Parse intent: portfolio_creation, amount=500000, risk=moderate | Structured request |
| 2 | Orchestrator | Activate all 4 data agents in parallel | Parallel execution |
| 3 | Market Data Agent | Fetch NIFTY 50 prices via yfinance | 50 stocks with OHLCV, P/E, ROE |
| 4 | News Agent | Fetch top 20 headlines; FAISS-match against historical corpus | 20 headlines with sentiment + 3 historical matches each |
| 5 | Macro Agent | Fetch: VIX=17.2, Repo=6.5%, CPI=4.8% | Regime: "Normal" (VIX < 20) |
| 6 | Data Validation | All data fresh (within TTL); no missing fields | ✅ Pass |
| 7 | MFKG Agent | Query: "Find top 3 'Normal' regime episodes where moderate-risk funds outperformed" | 3 episodes: {HDFC Balanced 2023-Q2, ICICI Prudential 2024-Q1, SBI Equity Hybrid 2023-Q4} |
| 8 | Strategist | Proposes 2 alternatives: (A) 60% equity / 40% debt, heavy IT+Banking; (B) 50/50 with pharma tilt | 2 proposals with CoT reasoning |
| 9 | Critic | CoVe: "Does Proposal A violate the 25% single-sector cap?" → No. "Is historical episode from same regime?" → Yes. All M-SAEA probes pass. | ✅ Approved with 0 High-severity issues |
| 10 | Moderator | Selects Proposal A (higher alignment with historical episodes, confidence 8/10) | Approved qualitative allocation |
| 11 | Math Execution | Converts to exact weights: HDFC Bank 8.2%, Infosys 7.5%, TCS 6.8%, ... (20 stocks). Validates sum = 100% | Exact portfolio JSON |
| 12 | SEBI Check | No sector > 25%, minimum 10 stocks, equity portion > 65% for hybrid categorization → ✅ | Constraints satisfied |
| 13 | Metrics | Sharpe: 1.42, Expected Return: 14.2%, Max DD: -8.3% | Performance estimates |
| 14 | Response | Package: portfolio table + reasoning + citations + metrics + pie chart data | Frontend-ready JSON |
| 15 | Frontend | Render portfolio page with chart, table, reasoning accordion, and "Approve" button | User sees result |

## Example 2: Crisis Scenario (High VIX)

**User Input:** "Markets are crashing. What should I do with my existing portfolio?"

| Step | Component | Action | Output |
|------|-----------|--------|--------|
| 1 | FastAPI | Parse intent: portfolio_review, context=crisis | Structured request |
| 3 | Macro Agent | VIX = 28.5 → Regime: "Crisis" | 🔴 Crisis mode activated |
| 7 | MFKG Agent | Query: "Find all 'Crisis' regime episodes (VIX > 25)" | Episodes: {2020 COVID crash, 2022 Russia-Ukraine, 2023 banking crisis} — shows how top managers shifted to defensive sectors (Pharma, FMCG, Govt bonds) |
| 8 | Strategist | Proposes: Reduce equity to 40%, increase debt to 50%, gold 10%; shift equity from Banking/IT to Pharma/FMCG | Crisis defense proposal |
| 9 | Critic | CoVe: "Is VIX truly in crisis?" → Yes (28.5 > 25). "Do historical crisis episodes support pharma shift?" → Yes (3/3 episodes show same pattern). "M-SAEA Temporal Probe: Is VIX reading current?" → Yes (17 min old). ✅ Approved | ✅ High confidence (9/10) |
| 11 | Math Execution | Calculate exact weights; apply 10% max single-stock constraint (tighter during crisis) | Defensive portfolio |
| 14 | Response | "Based on 3 historical crisis episodes, top fund managers shifted to defensive sectors. Here is the recommended reallocation..." | With full reasoning trace |

---

# Section 17: Complete Technology Stack

| Layer | Technology | Why This Option | Free? | Production Alternative |
|-------|-----------|----------------|-------|----------------------|
| **Frontend** | Next.js 14 | SSR, React ecosystem, API routes | ✅ | Same |
| **Styling** | Tailwind CSS | Rapid; consistent; utility-first | ✅ | Same |
| **Charts** | Recharts | React-native; financial chart support | ✅ | TradingView (paid) |
| **Backend** | FastAPI (Python) | Async; WebSocket; auto-docs; ML ecosystem | ✅ | Same |
| **Orchestration** | LangGraph | Reasoning/Functional node separation; state machine | ✅ | Same |
| **LLM** | Gemini 2.5 Flash | Free tier; excellent tool-calling | ✅ | Gemini Pro / GPT-4o |
| **Local LLM** | Ollama + Llama 3.1 8B | Offline development; no API costs | ✅ | Same |
| **Embeddings** | all-MiniLM-L6-v2 | Open source; fast; CPU-friendly | ✅ | OpenAI text-embedding-3-small |
| **Vector Store** | FAISS | Fast; disk-persistent; no server needed | ✅ | Pinecone (paid) |
| **Graph DB** | Neo4j Community | Free; Cypher queries; relationship modeling | ✅ | Neo4j AuraDB (cloud, paid) |
| **Relational DB** | PostgreSQL | Robust; JSON support; free | ✅ | Same |
| **Cache** | Redis | TTL caching; pub/sub for events | ✅ | Same |
| **Task Queue** | Celery + Redis | Background data refresh jobs | ✅ | Same |
| **PDF Parsing** | pdfplumber | Deterministic; handles Indian MF PDFs | ✅ | Amazon Textract (paid) |
| **Web Scraping** | BeautifulSoup + requests | Simple; sufficient for NSE/AMFI | ✅ | Playwright (for JS-heavy sites) |
| **Auth** | PyJWT | Stateless; simple | ✅ | Auth0 (freemium) |
| **Containerization** | Docker + Docker Compose | Reproducible; multi-service | ✅ | Kubernetes |
| **Monitoring** | Loguru + Python logging | Structured logs; simple setup | ✅ | Grafana + Prometheus |
| **Deployment** | Docker on any VPS / NITK server | Academic project; single server sufficient | ✅ | AWS/GCP |
| **CI/CD** | GitHub Actions | Free for public repos | ✅ | Same |

---

# Section 18: Project Repository Structure

```
major-project/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── main.py                      # FastAPI entry point
│   ├── config.py                    # Environment config (Pydantic Settings)
│   ├── requirements.txt
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── portfolio.py         # POST /api/portfolio/create
│   │   │   ├── backtest.py          # POST /api/portfolio/backtest
│   │   │   ├── explain.py           # GET  /api/portfolio/{id}/explain
│   │   │   └── auth.py              # POST /api/auth/login
│   │   └── middleware/
│   │       ├── auth.py              # JWT verification
│   │       └── rate_limit.py        # Request throttling
│   │
│   ├── agents/
│   │   ├── orchestrator.py          # LangGraph graph definition
│   │   ├── market_data_agent.py     # Agent 1: Stock prices + fundamentals
│   │   ├── news_sentiment_agent.py  # Agent 2: News + FAISS grounding
│   │   ├── macro_agent.py           # Agent 3: RBI, FRED, VIX
│   │   ├── mfkg_agent.py            # Agent 4: Neo4j MFKG queries
│   │   ├── strategist.py            # Agent 5: Proposes allocations
│   │   ├── critic.py                # Agent 6: CoVe + M-SAEA probes
│   │   └── moderator.py             # Agent 7: Final decision
│   │
│   ├── tools/
│   │   ├── yfinance_tool.py         # yfinance wrapper
│   │   ├── news_tool.py             # NewsAPI + RSS fetcher
│   │   ├── rbi_tool.py              # RBI DBIE scraper
│   │   ├── fred_tool.py             # FRED API wrapper
│   │   ├── nse_tool.py              # NSE India VIX/FII scraper
│   │   └── pdf_parser.py            # pdfplumber for MF holdings
│   │
│   ├── computation/
│   │   ├── portfolio_math.py        # Weight calculation, optimization
│   │   ├── risk_metrics.py          # Sharpe, CAGR, Max Drawdown, Beta
│   │   ├── regime_classifier.py     # VIX-based regime detection
│   │   ├── constraint_engine.py     # SEBI rules enforcement
│   │   └── backtester.py            # Historical portfolio simulation
│   │
│   ├── safety/
│   │   ├── msaea_probes.py          # 10 M-SAEA audit probes
│   │   ├── hallucination_detector.py # Cross-reference claims vs data
│   │   └── temporal_checker.py       # Verify data timestamps
│   │
│   ├── knowledge/
│   │   ├── neo4j_client.py          # Neo4j connection + Cypher queries
│   │   ├── faiss_index.py           # FAISS vector store management
│   │   ├── mfkg_builder.py          # Offline: Build MFKG from AMFI data
│   │   └── state_vector.py          # Market state vector construction
│   │
│   ├── models/
│   │   ├── schemas.py               # Pydantic models for all data
│   │   ├── portfolio.py             # Portfolio data model
│   │   └── agent_state.py           # LangGraph state definition
│   │
│   ├── prompts/
│   │   ├── strategist_prompt.py     # System prompt for Strategist
│   │   ├── critic_prompt.py         # System prompt for Critic (CoVe)
│   │   ├── moderator_prompt.py      # System prompt for Moderator
│   │   └── persona_templates.py     # Short/Mid/Long-term personas
│   │
│   └── database/
│       ├── postgres.py              # PostgreSQL connection
│       └── redis_client.py          # Redis connection
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   │
│   ├── app/
│   │   ├── layout.tsx               # Root layout
│   │   ├── page.tsx                 # Dashboard
│   │   ├── portfolio/
│   │   │   ├── create/page.tsx      # Portfolio creation chat
│   │   │   └── [id]/page.tsx        # Portfolio result view
│   │   ├── backtest/page.tsx        # Historical comparison
│   │   └── logs/page.tsx            # Decision log viewer
│   │
│   ├── components/
│   │   ├── PortfolioChart.tsx        # Pie chart (Recharts)
│   │   ├── ReasoningTrace.tsx        # Expandable reasoning accordion
│   │   ├── MetricsCard.tsx           # Sharpe, CAGR, DD display
│   │   ├── VixGauge.tsx              # Real-time VIX indicator
│   │   ├── AgentActivity.tsx         # Real-time agent status
│   │   └── ChatInterface.tsx         # User input interface
│   │
│   └── lib/
│       ├── api.ts                    # API client
│       └── websocket.ts             # WebSocket connection
│
├── data/
│   ├── raw/                         # Raw downloaded data (gitignored)
│   ├── processed/                   # Cleaned data
│   ├── faiss_index/                 # FAISS index files
│   └── scripts/
│       ├── download_amfi.py          # Download mutual fund data
│       ├── download_news_corpus.py   # Build historical news corpus
│       ├── build_mfkg.py            # Construct Neo4j knowledge graph
│       └── build_faiss_index.py     # Build news embedding index
│
├── tests/
│   ├── test_computation/
│   │   ├── test_portfolio_math.py
│   │   ├── test_risk_metrics.py
│   │   └── test_constraint_engine.py
│   ├── test_agents/
│   │   ├── test_strategist.py
│   │   ├── test_critic.py
│   │   └── test_moderator.py
│   ├── test_safety/
│   │   └── test_msaea_probes.py
│   └── test_integration/
│       └── test_end_to_end.py
│
├── evaluation/
│   ├── benchmark_dataset.json        # Known-answer test scenarios
│   ├── evaluate_accuracy.py          # Compare AI vs. actual manager
│   ├── evaluate_safety.py           # Run M-SAEA evaluation suite
│   └── ablation_study.py            # Test with/without each component
│
└── docs/
    ├── architecture.md
    ├── api_reference.md
    └── deployment.md
```

---

# Section 19: Development Roadmap

## Phase 1: Data Foundation (Week 1-2)
- **Tasks**: Download AMFI data, stock prices, news corpus; set up PostgreSQL, Redis, Neo4j
- **Dependencies**: None
- **Deliverables**: Raw data pipeline; database schemas created
- **Technologies**: Python, yfinance, BeautifulSoup, PostgreSQL, Neo4j
- **Gate**: All data sources verified and downloadable

## Phase 2: Knowledge Graph Construction (Week 3-4)
- **Tasks**: Build MFKG in Neo4j from AMFI holdings data; build FAISS news index
- **Dependencies**: Phase 1 complete
- **Deliverables**: Populated Neo4j with 3+ years of fund manager episodes; FAISS index with 30K+ news embeddings
- **Technologies**: Neo4j, Cypher, FAISS, Sentence-BERT
- **Gate**: Successfully query "Find historical episodes similar to current market"

## Phase 3: Computational Layer (Week 5-6)
- **Tasks**: Implement portfolio_math.py, risk_metrics.py, constraint_engine.py, regime_classifier.py
- **Dependencies**: Phase 1 (needs price data for testing)
- **Deliverables**: Fully tested mathematical computation library
- **Technologies**: NumPy, SciPy, Pandas
- **Gate**: All unit tests pass; Sharpe/CAGR/DD calculations verified against known values

## Phase 4: Agent Development (Week 7-10)
- **Tasks**: Implement all 7 agents; define LangGraph state machine; implement Strategist-Critic debate loop
- **Dependencies**: Phase 2 (MFKG), Phase 3 (computation)
- **Deliverables**: Working LangGraph pipeline from data ingestion → debate → mathematical execution
- **Technologies**: LangGraph, LangChain, Gemini API
- **Gate**: End-to-end portfolio creation works in Python script (no frontend yet)

## Phase 5: Safety Layer (Week 11-12)
- **Tasks**: Implement M-SAEA probes; integrate into Critic agent; implement data freshness validation
- **Dependencies**: Phase 4 (agents exist)
- **Deliverables**: All 6 key M-SAEA probes operational; Critic successfully catches injected errors
- **Technologies**: Python, Pydantic
- **Gate**: Error propagation test: Critic catches 100% of deliberately corrupted Strategist outputs

## Phase 6: Backend API (Week 13-14)
- **Tasks**: Build FastAPI routes; WebSocket streaming; JWT auth; rate limiting
- **Dependencies**: Phase 4 (agents), Phase 5 (safety)
- **Deliverables**: REST API that accepts natural language and returns portfolio JSON
- **Technologies**: FastAPI, PyJWT, Redis
- **Gate**: API responds correctly to all example workflows from Section 16

## Phase 7: Frontend (Week 15-17)
- **Tasks**: Build Next.js dashboard, portfolio creation page, result display, charts
- **Dependencies**: Phase 6 (API exists)
- **Deliverables**: Working web application with all 6 screens
- **Technologies**: Next.js, Tailwind, Recharts
- **Gate**: User can create a portfolio through the web interface

## Phase 8: Integration & Testing (Week 18-19)
- **Tasks**: End-to-end integration testing; backtesting against historical manager portfolios; ablation studies
- **Dependencies**: All prior phases
- **Deliverables**: Test results; benchmark comparisons
- **Technologies**: pytest, custom evaluation scripts
- **Gate**: System passes all evaluation metrics

## Phase 9: Deployment (Week 20)
- **Tasks**: Dockerize all services; deploy on server; configure monitoring
- **Dependencies**: Phase 8 (tested system)
- **Deliverables**: Deployed, accessible web application
- **Technologies**: Docker, Docker Compose
- **Gate**: Application accessible via URL; all services running

---

# Section 20: Testing and Evaluation Methodology

## 20.1 Evaluation Metrics

| Metric | What It Measures | Target | How Calculated |
|--------|-----------------|--------|---------------|
| **Portfolio Tracking Error** | How closely AI portfolio matches actual manager | < 5% annualized | `std(R_ai - R_manager)` |
| **Action Agreement Rate** | % of months where AI makes same Buy/Sell/Hold as manager | > 70% | Direct comparison |
| **Sharpe Ratio** | Risk-adjusted return | > 1.0 | `(R_p - R_f) / σ_p` |
| **CAGR** | Compound annual growth | > Benchmark NIFTY 50 | `(V_end/V_start)^(1/years) - 1` |
| **Maximum Drawdown** | Worst peak-to-trough decline | < 20% | `min((V - V_peak) / V_peak)` |
| **M-SAEA Safety Score** | Multi-agent safety assessment | > 80% (8/10 probes pass) | Run 10 M-SAEA probes |
| **Hallucination Rate** | % of claims not supported by source data | < 5% | Manual review of 50 random outputs |
| **Response Latency** | Time from user input to portfolio display | < 30 seconds | End-to-end timing |
| **Mathematical Accuracy** | Weights sum to 100%, constraints satisfied | 100% | Automated assertion |
| **Data Freshness Compliance** | % of decisions using current data | 100% | Timestamp audit |

## 20.2 Comparison Framework

| System | Description |
|--------|-------------|
| **Baseline 1**: NIFTY 50 Index (Buy & Hold) | Passive benchmark |
| **Baseline 2**: MFKG-only (Kotekar 2026 original) | Static cosine similarity without LLM reasoning |
| **Baseline 3**: LLM-only (no MFKG) | LLM generates portfolio without historical memory |
| **Full System**: LLM + MFKG + Triad Debate + M-SAEA | Our complete architecture |

## 20.3 Ablation Studies

| Ablation | What We Remove | What We Expect |
|----------|---------------|----------------|
| Remove MFKG | No historical episodes | Higher hallucination; less regime-appropriate decisions |
| Remove Critic | No adversarial review | More constraint violations; lower safety score |
| Remove Math Node | LLM generates weights directly | Weight errors; sum ≠ 100%; SEBI violations |
| Remove VIX regime detection | No crisis mode | Worse performance during high-volatility periods |
| Remove FAISS news grounding | No historical news context | Naive sentiment reactions |

---

# Section 21: Research Contribution

## 21.1 What Existing Approaches Already Do
- **Kotekar (2026)**: Uses MFKG for static historical matching
- **Hajaghaie (2025)**: Uses LangGraph for LLM/math separation
- **Kulpa (2025)**: Proposes theoretical triad debate architecture
- **Chen (2026)**: Provides external M-SAEA audit framework
- **Fatouros (2025)**: Builds specialized multi-agent data pipeline

## 21.2 What We Combine and Extend

Our project is the **first system to combine all five approaches** into a single, deployed application:

1. **MFKG (Kotekar) + LLM Reasoning (Hajaghaie)**: We place an LLM reasoning layer *on top of* the MFKG, enabling causal reasoning about historical episodes rather than pure cosine matching.
2. **Theoretical Triad (Kulpa) → Working Software**: We implement the Strategist-Critic-Moderator debate as actual code with measurable safety scores.
3. **External Audit (Chen) → Internal Safety**: We internalize M-SAEA probes into the Critic agent, making safety an inherent property rather than an external test.

## 21.3 Technical Gap Addressed
No existing system provides **explainable behavioral imitation** of Indian mutual fund managers through an agentic architecture with provable safety guarantees. Our system achieves:
- **Explainability** that IRL (Halperin 2024) lacks
- **Active reasoning** that static MFKG (Kotekar 2026) lacks
- **Mathematical correctness** that direct LLM allocation (Mantshimuli 2026) lacks
- **Safety guarantees** that most multi-agent systems (Fatouros 2025) lack

## 21.4 Measurable Claims
- Compare tracking error against Kotekar's original MFKG (expect improvement via LLM reasoning)
- Compare safety score against system without M-SAEA probes (expect measurable reduction in constraint violations)
- Compare explainability: our system produces natural-language audit trails; IRL produces opaque weight vectors

---

# Section 22: Final Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER                                          │
│                    (Browser / Next.js Frontend)                            │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ REST API / WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐     │
│  │ JWT Auth │  │ Rate Limiter │  │ Input Valid. │  │ Request Router │     │
│  └──────────┘  └──────────────┘  └──────────────┘  └───────┬────────┘     │
└────────────────────────────────────────────────────────────┬────────────────┘
                                                             │
                             ┌───────────────────────────────▼──────────────┐
                             │        LANGGRAPH ORCHESTRATOR                │
                             │        (Supervisor State Machine)            │
                             └──────┬─────┬──────┬──────────┬──────────────┘
                                    │     │      │          │
              ┌─────────────────────▼─────▼──────▼──┐       │
              │      PARALLEL DATA INGESTION         │       │
              │  ┌──────────┐ ┌──────┐ ┌───────┐   │       │
              │  │ Market   │ │ News │ │ Macro │   │       │
              │  │ Data Agt │ │ Agt  │ │ Agent │   │       │
              │  └────┬─────┘ └──┬───┘ └───┬───┘   │       │
              └───────┼──────────┼─────────┼────────┘       │
                      │          │         │                 │
        ┌─────────────▼──────────▼─────────▼─────────┐      │
        │         DATA VALIDATION NODE                │      │
        │    (Freshness + Schema + Completeness)      │      │
        └─────────────────────┬───────────────────────┘      │
                              │                              │
        ┌─────────────────────▼───────────────────────┐      │
        │           MFKG KNOWLEDGE AGENT              │      │
        │    (Neo4j GraphRAG: Historical Episodes)    │◄─────┘
        └─────────────────────┬───────────────────────┘
                              │
              ┌───────────────▼──────────────────┐
              │        DEBATE LOOP (Sequential)   │
              │                                   │
              │   ┌───────────────────────────┐   │
              │   │      STRATEGIST           │◄──┤─── Revision Loop
              │   │   (LLM Reasoning Node)    │   │    (max 3x)
              │   └───────────┬───────────────┘   │
              │               │                   │
              │   ┌───────────▼───────────────┐   │
              │   │        CRITIC             │───┘
              │   │   (CoVe + M-SAEA Probes)  │
              │   └───────────┬───────────────┘
              │               │
              │   ┌───────────▼───────────────┐
              │   │      MODERATOR            │
              │   │   (Consensus + Audit Log) │
              │   └───────────┬───────────────┘
              └───────────────┼──────────────────┘
                              │
        ┌─────────────────────▼───────────────────────┐
        │       MATHEMATICAL EXECUTION NODE            │
        │   (Python: NumPy, SciPy, Pandas)            │
        │   ┌──────────┐ ┌──────────┐ ┌────────────┐ │
        │   │ Weight   │ │ SEBI     │ │ Portfolio  │ │
        │   │ Optimizer│ │ Checker  │ │ Metrics    │ │
        │   └──────────┘ └──────────┘ └────────────┘ │
        └─────────────────────┬───────────────────────┘
                              │
        ┌─────────────────────▼───────────────────────┐
        │          RESPONSE GENERATION NODE            │
        │  (JSON packaging + reasoning trace + charts) │
        └─────────────────────┬───────────────────────┘
                              │
                              ▼
                         USER (Frontend)

═══════════════════ EXTERNAL SERVICES ═══════════════════

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ Neo4j    │ │ FAISS    │ │ Redis    │ │ PostgreSQL   │
│ (MFKG)   │ │ (News    │ │ (Cache)  │ │ (Users,Logs) │
│          │ │ Vectors) │ │          │ │              │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘

┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐
│ yfinance │ │ NewsAPI  │ │ RBI DBIE │ │ FRED API     │
│ (Stocks) │ │ (News)   │ │ (Macro)  │ │ (Global)     │
└──────────┘ └──────────┘ └──────────┘ └──────────────┘
```

---

# Section 23: Final Deliverables Checklist

| # | Deliverable | Status |
|---|------------|--------|
| 1 | Literature-to-Architecture Mapping | ✅ Section 1 |
| 2 | Complete System Architecture | ✅ Section 2 |
| 3 | Exact Number of Agents (7) | ✅ Section 3 |
| 4 | Detailed Responsibility of Every Agent | ✅ Section 3.1 |
| 5 | Agent Communication Architecture | ✅ Section 3.2 |
| 6 | Mathematical/Computational Layer | ✅ Section 4 |
| 7 | Multimodal Processing Architecture | ✅ Section 10 |
| 8 | Complete Data Requirements | ✅ Section 5 |
| 9 | Free API List | ✅ Section 6A |
| 10 | Freemium API List | ✅ Section 6B |
| 11 | Paid API List and Justification | ✅ Section 6C |
| 12 | Alternative Data Sources | ✅ Section 7 |
| 13 | Web Search/Scraping Requirements | ✅ Section 7 |
| 14 | Live Data/Freshness Architecture | ✅ Section 8 |
| 15 | Database and Memory Architecture | ✅ Section 9 |
| 16 | Model Selection | ✅ Section 11 |
| 17 | Backend Architecture | ✅ Section 12 |
| 18 | Frontend Architecture | ✅ Section 13 |
| 19 | Security Architecture | ✅ Section 14 |
| 20 | Agent Guardrails | ✅ Section 15 |
| 21 | Complete Technology Stack | ✅ Section 17 |
| 22 | Repository/Code Structure | ✅ Section 18 |
| 23 | End-to-End Workflows | ✅ Section 16 |
| 24 | Testing Strategy | ✅ Section 20 |
| 25 | Evaluation Metrics | ✅ Section 20.1 |
| 26 | Research Contribution | ✅ Section 21 |
| 27 | Development Roadmap | ✅ Section 19 |
| 28 | Final Architecture Diagram | ✅ Section 22 |
| 29 | Complete Dependency List | ✅ Section 17 |
| 30 | Risks, Limitations, and Backup Plans | ✅ Sections 5 (backup sources), 6C (alternatives), 8 (fallbacks) |

---

## Risks, Limitations, and Backup Plans

| Risk | Impact | Mitigation |
|------|--------|-----------|
| yfinance API becomes unavailable | No stock data | Fallback to Google Finance scraping; cache last known data |
| Gemini free tier rate-limited | Agents cannot reason | Fallback to local Llama 3.1 via Ollama |
| Neo4j runs out of memory | MFKG queries fail | Limit graph to top 50 funds; optimize Cypher queries |
| MFKG has no match for current regime | No historical episodes | Flag as "unprecedented"; use general defensive allocation |
| LLM hallucination passes Critic | Incorrect portfolio | M-SAEA probes + mathematical verification layer as final safeguard |
| Monthly MF holdings data is delayed | MFKG becomes stale | Use last available data; flag staleness to user |
| India VIX source changes format | Regime detection breaks | Multiple VIX sources (NSE, yfinance); format validation |
| SEBI regulation changes | Constraint engine outdated | Constraint rules in separate config file; easy to update |

---

> **This document is ready for review.** Once approved, we can proceed directly to Phase 1 implementation — downloading data and setting up the database infrastructure.
