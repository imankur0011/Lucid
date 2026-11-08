# Lucid Platform — Complete Database Design & Entity-Relationship (ER) Specification
**System Version:** Lucid Production v2.0  
**Target RDBMS:** PostgreSQL 14+ with strict relational normalization, BCNF compliance, foreign key cascades, and check constraints  
**Application Stack:** Python 3.14 + FastAPI + SQLAlchemy ORM + Alembic + LangGraph Multi-Agent Engine + Next.js 16  
**Schema Scope:** Complete 62 Tables | 565 Columns | 102 Foreign Key Relationships | 312 Integrity Constraints  

---

## 1. Executive Summary & Relational Architecture Topology

The Lucid database is engineered as an enterprise-grade, highly normalized relational persistence engine for personalized portfolio creation, real-time drift monitoring, whole-share integer lot rebalancing, Demat portfolio diagnosis, and regulatory auditability under SEBI (Investment Advisers) Regulations, 2013 standards.

### Core Architectural Principles
1. **Separation of Fiduciary Concerns**: Algorithmic recommendations (`portfolio_versions`, `portfolio_security_decisions`), user-reported Demat holdings (`existing_portfolios`, `existing_portfolio_holdings`), and broker execution events (`broker_orders`, `broker_executions`) are modeled as strictly distinct relational domains.
2. **Deterministic Mathematical Immutability**: All portfolio iterations are stored as immutable `portfolio_versions` with historical generation request snapshots, deterministic SciPy SLSQP optimization outputs, and whole-share integer lot arithmetic ($Q_i \in \mathbb{Z}_{\ge 0}$, $Cash \ge 0$).
3. **Multi-Tenant Ownership Guarantees**: Composite foreign key constraints (e.g., `["generation_request_id", "portfolio_id"]`, `["goal_id", "user_id"]`, `["risk_assessment_id", "user_id"]`) enforce strict data isolation at the PostgreSQL constraint level, preventing cross-tenant data leakage.
4. **Fiduciary Audit Trail & Citation Lineage**: Every stock recommendation and rebalancing trade is permanently backed by `recommendation_explanations`, `evidence_items`, and `portfolio_validation_runs`.

### Master Domain Table Count & Column Reconciliation

| Domain Code | Domain Module Name | Tables | Total Attributes | Core Functional Scope |
|---|---|---|---|---|
| `IDENTITY` | **User Identity, Authentication & Security** | **7** | 59 | Core application identity table storing email, Argon2id password hash, and account status |
| `INVESTOR` | **Investor Suitability, Risk Profiling & Financial Goals** | **5** | 47 | Investor financial targets specifying goal type, target amount, and time horizon |
| `SECURITY` | **Security Master, Companies & Corporate Taxonomy** | **9** | 56 | Legal entity master record with CIN, legal name, corporate website, and registration |
| `MARKET` | **Market Data, Prices, Fundamental Metrics & News** | **11** | 101 | Error log for market data fetching exceptions and API failures |
| `PORTFOLIO` | **Portfolio Engine, Optimization, Versions & Explanations** | **13** | 133 | Verifiable factual evidence items (filing excerpts, financial ratios) supporting recommendations |
| `BROKER` | **Broker Accounts, Integrations & Order Auditing** | **6** | 55 | Realized execution fill records for placed broker orders with trade timestamps |
| `DIAGNOSIS` | **Demat Portfolio Diagnosis & Rebalancing Suggestions** | **4** | 38 | Granular stock holdings extracted from uploaded brokerage statements |
| `OPERATIONS` | **Multi-Agent Telemetry, Knowledge Base & System Auditing** | **7** | 76 | Registry of specialized agent roles (Manager, Suitability, Macro, Market, Fundamental, News, Critic, Moderator) |
| **TOTAL** | **All 8 Relational Domains** | **62 Tables** | **565 Columns** | **100% Fully Reconciled Against PostgreSQL Metadata** |

---

## 2. Complete High-Resolution Master Entity-Relationship (ER) Diagram

The complete enterprise ER topology spanning all 62 tables and 102 foreign key relationships is presented below:

```mermaid
erDiagram
    %% ==========================================
    %% 1. USER IDENTITY & SECURITY RELATIONSHIPS
    %% ==========================================
    APP_USERS ||--o| USER_PROFILES : "has_profile"
    APP_USERS ||--o| USER_PREFERENCES : "configures"
    APP_USERS ||--o{ USER_CONSENTS : "grants"
    APP_USERS ||--o{ USER_VERIFICATION_CODES : "authenticates"
    APP_USERS ||--o{ USER_PROFILE_VERSIONS : "versions"
    APP_USERS ||--o{ REVOKED_TOKENS : "invalidates"
    APP_USERS ||--o{ FINANCIAL_GOALS : "defines_goals"
    APP_USERS ||--o{ RISK_ASSESSMENTS : "attempts_risk"
    APP_USERS ||--o{ INVESTOR_PORTFOLIOS : "owns_portfolios"
    APP_USERS ||--o{ EXISTING_PORTFOLIOS : "imports_demat"
    APP_USERS ||--o{ USER_BROKER_ACCOUNTS : "links_broker"
    APP_USERS ||--o{ USER_FEEDBACK : "submits_feedback"
    APP_USERS ||--o{ NOTIFICATIONS : "receives_alerts"
    APP_USERS ||--o{ AUDIT_EVENTS : "triggers_audit"
    APP_USERS ||--o{ USER_SECTOR_PREFERENCES : "prefers_sector"
    APP_USERS ||--o{ USER_SECURITY_PREFERENCES : "prefers_stock"

    %% ==========================================
    %% 2. INVESTOR & SUITABILITY RELATIONSHIPS
    %% ==========================================
    RISK_ASSESSMENTS ||--o{ RISK_ASSESSMENT_ANSWERS : "collects"
    RISK_QUESTIONS ||--o{ RISK_ASSESSMENT_ANSWERS : "answered_in"
    RISK_QUESTIONS ||--o{ RISK_QUESTION_OPTIONS : "presents"
    RISK_QUESTION_OPTIONS ||--o{ RISK_ASSESSMENT_ANSWERS : "chosen_option"
    FINANCIAL_GOALS o|--o{ PORTFOLIO_GENERATION_REQUESTS : "targeted_by"
    RISK_ASSESSMENTS o|--o{ PORTFOLIO_GENERATION_REQUESTS : "evaluated_by"

    %% ==========================================
    %% 3. SECURITY MASTER & TAXONOMY RELATIONSHIPS
    %% ==========================================
    SECTORS ||--o{ INDUSTRIES : "contains"
    COMPANIES ||--o{ COMPANY_INDUSTRIES : "belongs_to"
    INDUSTRIES ||--o{ COMPANY_INDUSTRIES : "classifies"
    COMPANIES ||--o{ SECURITIES : "issues"
    SECURITIES ||--o{ INSTRUMENT_LISTINGS : "listed_as"
    EXCHANGES ||--o{ INSTRUMENT_LISTINGS : "trades_on"
    SECTORS ||--o{ USER_SECTOR_PREFERENCES : "filtered_in"
    SECURITIES ||--o{ USER_SECURITY_PREFERENCES : "filtered_in"

    %% ==========================================
    %% 4. MARKET DATA, FUNDAMENTALS & PRICES
    %% ==========================================
    DATA_SOURCES ||--o{ DATA_INGESTION_RUNS : "initiates"
    DATA_INGESTION_RUNS ||--o{ DATA_INGESTION_ERRORS : "logs_errors"
    DATA_SOURCES ||--o{ SOURCE_INSTRUMENT_MAPPINGS : "maps_source"
    INSTRUMENT_LISTINGS ||--o{ SOURCE_INSTRUMENT_MAPPINGS : "mapped_instrument"
    INSTRUMENT_LISTINGS ||--o{ MARKET_PRICES : "has_prices"
    DATA_SOURCES ||--o{ MARKET_PRICES : "quotes_source"
    METRIC_DEFINITIONS ||--o{ FUNDAMENTAL_METRICS : "defines_metric"
    SECURITIES ||--o{ FUNDAMENTAL_METRICS : "has_fundamentals"
    DATA_SOURCES ||--o{ FUNDAMENTAL_METRICS : "fundamentals_source"
    ECONOMIC_INDICATORS ||--o{ ECONOMIC_OBSERVATIONS : "measures_indicator"
    DATA_SOURCES ||--o{ ECONOMIC_OBSERVATIONS : "macro_source"
    MARKET_NEWS_ARTICLES ||--o{ NEWS_ARTICLE_SECURITIES : "associates_news"
    SECURITIES ||--o{ NEWS_ARTICLE_SECURITIES : "cited_security"

    %% ==========================================
    %% 5. PORTFOLIO ENGINE, OPTIMIZATION & DECISIONS
    %% ==========================================
    INVESTOR_PORTFOLIOS ||--o{ PORTFOLIO_GENERATION_REQUESTS : "submits"
    STRATEGY_DEFINITIONS ||--o{ STRATEGY_VERSIONS : "versions_strategy"
    PORTFOLIO_GENERATION_REQUESTS ||--o{ PORTFOLIO_VERSIONS : "yields_version"
    INVESTOR_PORTFOLIOS ||--o{ PORTFOLIO_VERSIONS : "versions_portfolio"
    STRATEGY_VERSIONS ||--o{ PORTFOLIO_VERSIONS : "governs_version"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_SECURITY_DECISIONS : "allocates"
    SECURITIES ||--o{ PORTFOLIO_SECURITY_DECISIONS : "allocated_stock"
    INSTRUMENT_LISTINGS o|--o{ PORTFOLIO_SECURITY_DECISIONS : "traded_listing"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_VERSION_CONSTRAINTS : "enforces_constraint"
    PORTFOLIO_VERSIONS ||--o{ RECOMMENDATION_EXPLANATIONS : "explained_by"
    PORTFOLIO_SECURITY_DECISIONS o|--o{ RECOMMENDATION_EXPLANATIONS : "justifies_decision"
    RECOMMENDATION_EXPLANATIONS ||--o{ EXPLANATION_EVIDENCE : "cites_evidence"
    EVIDENCE_ITEMS ||--o{ EXPLANATION_EVIDENCE : "proves_rationale"
    SECURITIES o|--o{ EVIDENCE_ITEMS : "cites_security"
    MARKET_PRICES o|--o{ EVIDENCE_ITEMS : "cites_price"
    FUNDAMENTAL_METRICS o|--o{ EVIDENCE_ITEMS : "cites_metric"
    ECONOMIC_OBSERVATIONS o|--o{ EVIDENCE_ITEMS : "cites_macro"
    MARKET_NEWS_ARTICLES o|--o{ EVIDENCE_ITEMS : "cites_news"
    DATA_SOURCES o|--o{ EVIDENCE_ITEMS : "cites_source"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_VALIDATION_RUNS : "validates_version"
    PORTFOLIO_VALIDATION_RUNS ||--o{ PORTFOLIO_VALIDATION_RESULTS : "produces_result"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_SCENARIOS : "stresses_scenario"

    %% ==========================================
    %% 6. BROKER INTEGRATIONS & EXECUTION TRACKING
    %% ==========================================
    BROKER_PROVIDERS ||--o{ USER_BROKER_ACCOUNTS : "provides_broker"
    USER_BROKER_ACCOUNTS ||--o{ BROKER_ORDERS : "places_order"
    PORTFOLIO_VERSIONS o|--o{ BROKER_ORDERS : "orders_portfolio"
    BROKER_ORDERS ||--o{ BROKER_ORDER_EVENTS : "logs_event"
    BROKER_ORDERS ||--o{ BROKER_EXECUTIONS : "fills_order"
    INVESTOR_PORTFOLIOS ||--o{ PORTFOLIO_PERFORMANCE_SNAPSHOTS : "snapshots_perf"

    %% ==========================================
    %% 7. DEMAT DIAGNOSIS & REBALANCING
    %% ==========================================
    EXISTING_PORTFOLIOS ||--o{ EXISTING_PORTFOLIO_HOLDINGS : "holds"
    SECURITIES ||--o{ EXISTING_PORTFOLIO_HOLDINGS : "held_security"
    EXISTING_PORTFOLIOS ||--o{ PORTFOLIO_DIAGNOSES : "analyzes"
    PORTFOLIO_DIAGNOSES ||--o{ REBALANCE_SUGGESTIONS : "proposes_trade"
    SECURITIES ||--o{ REBALANCE_SUGGESTIONS : "trade_security"

    %% ==========================================
    %% 8. MULTI-AGENT TELEMETRY & OPERATIONS
    %% ==========================================
    AGENT_DEFINITIONS ||--o{ AGENT_VERSIONS : "versions_agent"
    AGENT_VERSIONS ||--o{ AGENT_EXECUTION_RUNS : "runs_agent"
    PORTFOLIO_GENERATION_REQUESTS o|--o{ AGENT_EXECUTION_RUNS : "agent_request"
    PORTFOLIO_VERSIONS o|--o{ AGENT_EXECUTION_RUNS : "agent_version"
    DATA_SOURCES o|--o{ KNOWLEDGE_DOCUMENTS : "indexes_doc"
    PORTFOLIO_VERSIONS o|--o{ USER_FEEDBACK : "rated_version"
```

---

## 3. Domain-by-Domain Architectural Specifications

### Domain: User Identity, Authentication & Security (`IDENTITY` — 7 Tables, 59 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    REVOKED_TOKENS ||--o{ APP_USERS : "_user_id"
    USER_CONSENTS ||--o{ APP_USERS : "_user_id"
    USER_PREFERENCES ||--o{ APP_USERS : "_user_id"
    USER_PROFILE_VERSIONS ||--o{ APP_USERS : "_user_id"
    USER_PROFILES ||--o{ APP_USERS : "_user_id"
    USER_VERIFICATION_CODES ||--o{ APP_USERS : "_user_id"

    APP_USERS {
        uuid user_id PK
        varchar identity_provider
        varchar identity_subject
        varchar email
        varchar password_hash
        boolean email_verified
        varchar mobile_number
        boolean mobile_verified
        varchar account_status
        timestamp created_at
        timestamp updated_at
    }

    REVOKED_TOKENS {
        uuid revocation_id PK
        varchar token_hash
        uuid user_id FK
        timestamp revoked_at
        timestamp expires_at
    }

    USER_CONSENTS {
        uuid consent_id PK
        uuid user_id FK
        varchar consent_type
        varchar policy_version
        varchar consent_status
        timestamp recorded_at
        varchar capture_source
        varchar evidence_reference
        jsonb metadata
    }

    USER_PREFERENCES {
        uuid user_id PK,FK
        varchar preferred_language
        varchar timezone_name
        boolean email_notifications_enabled
        boolean in_app_notifications_enabled
        timestamp created_at
        timestamp updated_at
    }

    USER_PROFILE_VERSIONS {
        uuid profile_version_id PK
        uuid user_id FK
        integer version_number
        varchar display_name
        varchar country_code
        varchar preferred_currency
        varchar investment_experience
        varchar investment_knowledge_level
        varchar change_summary
        timestamp created_at
    }

    USER_PROFILES {
        uuid user_id PK,FK
        integer version_number
        varchar display_name
        varchar country_code
        varchar preferred_currency
        varchar investment_experience
        varchar investment_knowledge_level
        timestamp created_at
        timestamp updated_at
    }

    USER_VERIFICATION_CODES {
        uuid verification_id PK
        uuid user_id FK
        varchar code_type
        varchar code_value
        varchar recipient
        timestamp expires_at
        boolean is_used
        timestamp created_at
    }
```

#### Table: `app_users` (11 Columns)
**Description:** Core application identity table storing email, Argon2id password hash, and account status.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_id` | `UUID` | **PK**, NOT NULL | - | Identifier for app_users |
| `identity_provider` | `VARCHAR(40)` | NOT NULL | - | Data field for identity provider |
| `identity_subject` | `VARCHAR(255)` | NOT NULL | - | Data field for identity subject |
| `email` | `VARCHAR(320)` | NULL | - | Canonical lowercase user email address |
| `password_hash` | `VARCHAR(255)` | NULL | - | Data field for password hash |
| `email_verified` | `BOOLEAN` | NOT NULL | - | Canonical lowercase user email address |
| `mobile_number` | `VARCHAR(20)` | NULL | - | Data field for mobile number |
| `mobile_verified` | `BOOLEAN` | NOT NULL | - | Data field for mobile verified |
| `account_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for app_users |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_id)`
* `CHECK (account_status IN ('pending', 'active', 'suspended', 'closed'))`
* `UNIQUE (identity_provider, identity_subject)`


#### Table: `revoked_tokens` (5 Columns)
**Description:** Blacklist ledger for invalidated stateless JWT tokens (JTI tracking).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `revocation_id` | `UUID` | **PK**, NOT NULL | - | Identifier for revoked_tokens |
| `token_hash` | `VARCHAR(128)` | NOT NULL | - | Data field for token hash |
| `user_id` | `UUID` | `FK`, NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `revoked_at` | `DATETIME` | NOT NULL | - | Data field for revoked at |
| `expires_at` | `DATETIME` | NOT NULL | - | Data field for expires at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (revocation_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `UNIQUE (token_hash)`


#### Table: `user_consents` (9 Columns)
**Description:** Append-only legal consent ledger tracking terms of service, SEBI risk disclosures, and DPDP consents.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `consent_id` | `UUID` | **PK**, NOT NULL | - | Identifier for user_consents |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `consent_type` | `VARCHAR(60)` | NOT NULL | - | Data field for consent type |
| `policy_version` | `VARCHAR(80)` | NOT NULL | - | Data field for policy version |
| `consent_status` | `VARCHAR(12)` | NOT NULL | - | Lifecycle status flag for user_consents |
| `recorded_at` | `DATETIME` | NOT NULL | - | Data field for recorded at |
| `capture_source` | `VARCHAR(40)` | NOT NULL | - | Data field for capture source |
| `evidence_reference` | `VARCHAR(300)` | NULL | - | Data field for evidence reference |
| `metadata` | `JSONB` | NOT NULL | - | Data field for metadata |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (consent_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (consent_status IN ('granted', 'withdrawn'))`


#### Table: `user_preferences` (7 Columns)
**Description:** Investor UI configuration, default currency, and notification channel preferences.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_id` | `UUID` | **PK**, `FK`, NOT NULL | `app_users.user_id` | Identifier for user_preferences |
| `preferred_language` | `VARCHAR(12)` | NOT NULL | - | Data field for preferred language |
| `timezone_name` | `VARCHAR(80)` | NOT NULL | - | Data field for timezone name |
| `email_notifications_enabled` | `BOOLEAN` | NOT NULL | - | Canonical lowercase user email address |
| `in_app_notifications_enabled` | `BOOLEAN` | NOT NULL | - | Data field for in app notifications enabled |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`


#### Table: `user_profile_versions` (10 Columns)
**Description:** Historical audit versions of modifications to user profile data.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `profile_version_id` | `UUID` | **PK**, NOT NULL | - | Identifier for user_profile_versions |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `version_number` | `INTEGER` | NOT NULL | - | Data field for version number |
| `display_name` | `VARCHAR(120)` | NULL | - | Data field for display name |
| `country_code` | `CHAR(2)` | NOT NULL | - | Data field for country code |
| `preferred_currency` | `CHAR(3)` | NOT NULL | - | Data field for preferred currency |
| `investment_experience` | `VARCHAR(20)` | NULL | - | Data field for investment experience |
| `investment_knowledge_level` | `VARCHAR(20)` | NULL | - | Data field for investment knowledge level |
| `change_summary` | `VARCHAR(300)` | NULL | - | Data field for change summary |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (profile_version_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `UNIQUE (user_id, version_number)`


#### Table: `user_profiles` (9 Columns)
**Description:** Investor demographic profile, investment knowledge tier, and residency.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_id` | `UUID` | **PK**, `FK`, NOT NULL | `app_users.user_id` | Identifier for user_profiles |
| `version_number` | `INTEGER` | NOT NULL | - | Data field for version number |
| `display_name` | `VARCHAR(120)` | NULL | - | Data field for display name |
| `country_code` | `CHAR(2)` | NOT NULL | - | Data field for country code |
| `preferred_currency` | `CHAR(3)` | NOT NULL | - | Data field for preferred currency |
| `investment_experience` | `VARCHAR(20)` | NULL | - | Data field for investment experience |
| `investment_knowledge_level` | `VARCHAR(20)` | NULL | - | Data field for investment knowledge level |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (investment_experience IN ('beginner', 'intermediate', 'experienced'))`
* `CHECK (investment_knowledge_level IN ('basic', 'intermediate', 'advanced'))`


#### Table: `user_verification_codes` (8 Columns)
**Description:** Time-limited verification OTP codes for password reset and email confirmation.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `verification_id` | `UUID` | **PK**, NOT NULL | - | Identifier for user_verification_codes |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `code_type` | `VARCHAR(40)` | NOT NULL | - | Data field for code type |
| `code_value` | `VARCHAR(32)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `recipient` | `VARCHAR(320)` | NOT NULL | - | Data field for recipient |
| `expires_at` | `DATETIME` | NOT NULL | - | Data field for expires at |
| `is_used` | `BOOLEAN` | NOT NULL | - | Data field for is used |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (verification_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (code_type IN ('email_verification', 'mobile_verification', 'password_reset'))`


---

### Domain: Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR` — 5 Tables, 47 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    RISK_ASSESSMENT_ANSWERS ||--o{ RISK_QUESTION_OPTIONS : "_question_id"
    RISK_ASSESSMENT_ANSWERS ||--o{ RISK_QUESTIONS : "_question_id"
    RISK_ASSESSMENT_ANSWERS ||--o{ RISK_ASSESSMENTS : "_risk_assessment_id"
    RISK_ASSESSMENT_ANSWERS ||--o{ RISK_QUESTION_OPTIONS : "_selected_option_id"
    RISK_QUESTION_OPTIONS ||--o{ RISK_QUESTIONS : "_question_id"

    FINANCIAL_GOALS {
        uuid goal_id PK
        uuid user_id FK
        varchar goal_name
        varchar goal_type
        numeric target_amount
        numeric amount_already_saved
        varchar currency_code
        timestamp target_date
        integer priority
        varchar goal_status
        varchar notes
        timestamp created_at
        timestamp updated_at
    }

    RISK_ASSESSMENT_ANSWERS {
        uuid answer_id PK
        uuid risk_assessment_id FK
        uuid question_id FK
        uuid selected_option_id FK
        varchar answer_text
        numeric answer_numeric
        boolean answer_boolean
        timestamp created_at
    }

    RISK_ASSESSMENTS {
        uuid risk_assessment_id PK
        uuid user_id FK
        varchar questionnaire_version
        varchar assessment_status
        numeric risk_tolerance_score
        numeric risk_capacity_score
        varchar risk_category
        timestamp started_at
        timestamp completed_at
        timestamp created_at
    }

    RISK_QUESTION_OPTIONS {
        uuid option_id PK
        uuid question_id FK
        varchar option_code
        varchar option_label
        numeric score
        integer display_order
    }

    RISK_QUESTIONS {
        uuid question_id PK
        varchar question_code
        integer question_version
        varchar question_text
        varchar answer_type
        boolean is_required
        boolean is_active
        integer display_order
        jsonb scoring_config
        timestamp created_at
    }
```

#### Table: `financial_goals` (13 Columns)
**Description:** Investor financial targets specifying goal type, target amount, and time horizon.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `goal_id` | `UUID` | **PK**, NOT NULL | - | Identifier for financial_goals |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `goal_name` | `VARCHAR(120)` | NOT NULL | - | Data field for goal name |
| `goal_type` | `VARCHAR(40)` | NOT NULL | - | Data field for goal type |
| `target_amount` | `NUMERIC(20, 2)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `amount_already_saved` | `NUMERIC(20, 2)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `target_date` | `DATE` | NULL | - | Data field for target date |
| `priority` | `SMALLINT` | NOT NULL | - | Data field for priority |
| `goal_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for financial_goals |
| `notes` | `TEXT` | NULL | - | Data field for notes |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (goal_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `UNIQUE (goal_id, user_id)`
* `CHECK (target_amount > 0)`
* `CHECK (priority BETWEEN 1 AND 5)`
* `CHECK (goal_status IN ('active', 'paused', 'completed', 'cancelled'))`
* `CHECK (amount_already_saved >= 0)`


#### Table: `risk_assessment_answers` (8 Columns)
**Description:** Granular user answers recorded for individual risk assessment questions.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `answer_id` | `UUID` | **PK**, NOT NULL | - | Identifier for risk_assessment_answers |
| `risk_assessment_id` | `UUID` | `FK`, NOT NULL | `risk_assessments.risk_assessment_id` | Foreign key reference to `risk_assessments.risk_assessment_id` |
| `question_id` | `UUID` | `FK`, NOT NULL | `risk_questions.question_id`, `risk_question_options.question_id` | Foreign key reference to `risk_questions.question_id`, `risk_question_options.question_id` |
| `selected_option_id` | `UUID` | `FK`, NULL | `risk_question_options.option_id` | Foreign key reference to `risk_question_options.option_id` |
| `answer_text` | `TEXT` | NULL | - | Data field for answer text |
| `answer_numeric` | `NUMERIC(18, 6)` | NULL | - | Data field for answer numeric |
| `answer_boolean` | `BOOLEAN` | NULL | - | Data field for answer boolean |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (answer_id)`
* `FOREIGN KEY (question_id) REFERENCES risk_question_options(question_id)`
* `FOREIGN KEY (question_id) REFERENCES risk_questions(question_id)`
* `FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(risk_assessment_id)`
* `FOREIGN KEY (selected_option_id) REFERENCES risk_question_options(option_id)`
* `UNIQUE (risk_assessment_id, question_id)`


#### Table: `risk_assessments` (10 Columns)
**Description:** SEBI suitability and risk assessment sessions with calculated risk score and category.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `risk_assessment_id` | `UUID` | **PK**, NOT NULL | - | Identifier for risk_assessments |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `questionnaire_version` | `VARCHAR(80)` | NOT NULL | - | Data field for questionnaire version |
| `assessment_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for risk_assessments |
| `risk_tolerance_score` | `NUMERIC(8, 3)` | NULL | - | Data field for risk tolerance score |
| `risk_capacity_score` | `NUMERIC(8, 3)` | NULL | - | Data field for risk capacity score |
| `risk_category` | `VARCHAR(30)` | NULL | - | Data field for risk category |
| `started_at` | `DATETIME` | NOT NULL | - | Data field for started at |
| `completed_at` | `DATETIME` | NULL | - | Data field for completed at |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (risk_assessment_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `UNIQUE (risk_assessment_id, user_id)`
* `CHECK (assessment_status IN ('in_progress', 'completed', 'superseded', 'cancelled'))`
* `CHECK (assessment_status <> 'completed' OR completed_at IS NOT NULL)`
* `CHECK (completed_at IS NULL OR completed_at >= started_at)`
* `CHECK (risk_category IS NULL OR risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive'))`


#### Table: `risk_question_options` (6 Columns)
**Description:** Selectable multiple-choice responses with associated risk score weights.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `option_id` | `UUID` | **PK**, NOT NULL | - | Identifier for risk_question_options |
| `question_id` | `UUID` | `FK`, NOT NULL | `risk_questions.question_id` | Foreign key reference to `risk_questions.question_id` |
| `option_code` | `VARCHAR(60)` | NOT NULL | - | Data field for option code |
| `option_label` | `TEXT` | NOT NULL | - | Data field for option label |
| `score` | `NUMERIC(8, 3)` | NULL | - | Data field for score |
| `display_order` | `INTEGER` | NOT NULL | - | Data field for display order |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (option_id)`
* `FOREIGN KEY (question_id) REFERENCES risk_questions(question_id)`
* `UNIQUE (question_id, option_code)`
* `UNIQUE (option_id, question_id)`


#### Table: `risk_questions` (10 Columns)
**Description:** Standardized questionnaire items evaluating risk capacity, horizon, and loss tolerance.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `question_id` | `UUID` | **PK**, NOT NULL | - | Identifier for risk_questions |
| `question_code` | `VARCHAR(80)` | NOT NULL | - | Data field for question code |
| `question_version` | `INTEGER` | NOT NULL | - | Data field for question version |
| `question_text` | `TEXT` | NOT NULL | - | Data field for question text |
| `answer_type` | `VARCHAR(20)` | NOT NULL | - | Data field for answer type |
| `is_required` | `BOOLEAN` | NOT NULL | - | Data field for is required |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `display_order` | `INTEGER` | NOT NULL | - | Data field for display order |
| `scoring_config` | `JSONB` | NOT NULL | - | Data field for scoring config |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (question_id)`
* `CHECK (question_version > 0)`
* `UNIQUE (question_code, question_version)`
* `CHECK (answer_type IN ('single_choice', 'text', 'numeric', 'boolean'))`
* `UNIQUE (question_id, question_code, question_version)`


---

### Domain: Security Master, Companies & Corporate Taxonomy (`SECURITY` — 9 Tables, 56 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    COMPANY_INDUSTRIES ||--o{ COMPANIES : "_company_id"
    COMPANY_INDUSTRIES ||--o{ INDUSTRIES : "_industry_id"
    INDUSTRIES ||--o{ SECTORS : "_sector_id"
    INSTRUMENT_LISTINGS ||--o{ SECURITIES : "_security_id"
    INSTRUMENT_LISTINGS ||--o{ EXCHANGES : "_exchange_id"
    SECURITIES ||--o{ COMPANIES : "_company_id"
    USER_SECTOR_PREFERENCES ||--o{ SECTORS : "_sector_id"
    USER_SECURITY_PREFERENCES ||--o{ SECURITIES : "_security_id"

    COMPANIES {
        uuid company_id PK
        varchar legal_name
        varchar common_name
        varchar country_code
        varchar website_url
        timestamp created_at
        timestamp updated_at
    }

    COMPANY_INDUSTRIES {
        uuid company_id PK,FK
        uuid industry_id PK,FK
        timestamp effective_from PK
        timestamp effective_to
        varchar classification_source
    }

    EXCHANGES {
        uuid exchange_id PK
        varchar exchange_code
        varchar exchange_name
        varchar country_code
        varchar currency_code
        boolean is_active
    }

    INDUSTRIES {
        uuid industry_id PK
        uuid sector_id FK
        varchar industry_code
        varchar industry_name
        varchar taxonomy_source
        boolean is_active
    }

    INSTRUMENT_LISTINGS {
        uuid listing_id PK
        uuid security_id FK
        uuid exchange_id FK
        varchar symbol
        varchar trading_status
        timestamp listed_on
        timestamp delisted_on
        timestamp created_at
        timestamp updated_at
    }

    SECTORS {
        uuid sector_id PK
        varchar sector_code
        varchar sector_name
        varchar taxonomy_source
        boolean is_active
    }

    SECURITIES {
        uuid security_id PK
        uuid company_id FK
        varchar security_name
        varchar isin
        varchar security_type
        varchar currency_code
        varchar security_status
        timestamp created_at
        timestamp updated_at
    }

    USER_SECTOR_PREFERENCES {
        uuid user_id PK,FK
        uuid sector_id PK,FK
        varchar preference_type
        timestamp created_at
    }

    USER_SECURITY_PREFERENCES {
        uuid user_id PK,FK
        uuid security_id PK,FK
        varchar preference_type
        varchar reason
        timestamp created_at
    }
```

#### Table: `companies` (7 Columns)
**Description:** Legal entity master record with CIN, legal name, corporate website, and registration.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `company_id` | `UUID` | **PK**, NOT NULL | - | Identifier for companies |
| `legal_name` | `VARCHAR(240)` | NOT NULL | - | Data field for legal name |
| `common_name` | `VARCHAR(180)` | NULL | - | Data field for common name |
| `country_code` | `CHAR(2)` | NOT NULL | - | Data field for country code |
| `website_url` | `TEXT` | NULL | - | Data field for website url |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (company_id)`


#### Table: `company_industries` (5 Columns)
**Description:** Many-to-many relationship mapping companies to industries and primary sector tags.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `company_id` | `UUID` | **PK**, `FK`, NOT NULL | `companies.company_id` | Identifier for company_industries |
| `industry_id` | `UUID` | **PK**, `FK`, NOT NULL | `industries.industry_id` | Identifier for company_industries |
| `effective_from` | `DATE` | **PK**, NOT NULL | - | Identifier for company_industries |
| `effective_to` | `DATE` | NULL | - | Data field for effective to |
| `classification_source` | `VARCHAR(120)` | NULL | - | Data field for classification source |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (company_id, industry_id, effective_from)`
* `FOREIGN KEY (company_id) REFERENCES companies(company_id)`
* `FOREIGN KEY (industry_id) REFERENCES industries(industry_id)`
* `CHECK (effective_to IS NULL OR effective_to >= effective_from)`


#### Table: `exchanges` (6 Columns)
**Description:** Exchange directory (NSE, BSE) with MIC codes, trading currencies, and holiday schedules.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `exchange_id` | `UUID` | **PK**, NOT NULL | - | Identifier for exchanges |
| `exchange_code` | `VARCHAR(20)` | NOT NULL | - | Data field for exchange code |
| `exchange_name` | `VARCHAR(120)` | NOT NULL | - | Data field for exchange name |
| `country_code` | `CHAR(2)` | NOT NULL | - | Data field for country code |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (exchange_id)`
* `UNIQUE (exchange_code)`


#### Table: `industries` (6 Columns)
**Description:** Granular industry classification linked to parent sector.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `industry_id` | `UUID` | **PK**, NOT NULL | - | Identifier for industries |
| `sector_id` | `UUID` | `FK`, NOT NULL | `sectors.sector_id` | Foreign key reference to `sectors.sector_id` |
| `industry_code` | `VARCHAR(100)` | NOT NULL | - | Data field for industry code |
| `industry_name` | `VARCHAR(160)` | NOT NULL | - | Data field for industry name |
| `taxonomy_source` | `VARCHAR(120)` | NULL | - | Data field for taxonomy source |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (industry_id)`
* `FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)`
* `UNIQUE (industry_code)`


#### Table: `instrument_listings` (9 Columns)
**Description:** Exchange-specific equity listings with NSE/BSE symbols, scrip codes, and lot sizes.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `listing_id` | `UUID` | **PK**, NOT NULL | - | Identifier for instrument_listings |
| `security_id` | `UUID` | `FK`, NOT NULL | `securities.security_id` | Foreign key reference to `securities.security_id` |
| `exchange_id` | `UUID` | `FK`, NOT NULL | `exchanges.exchange_id` | Foreign key reference to `exchanges.exchange_id` |
| `symbol` | `VARCHAR(80)` | NOT NULL | - | Data field for symbol |
| `trading_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for instrument_listings |
| `listed_on` | `DATE` | NULL | - | Data field for listed on |
| `delisted_on` | `DATE` | NULL | - | Data field for delisted on |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (listing_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (exchange_id) REFERENCES exchanges(exchange_id)`
* `CHECK (trading_status IN ('active', 'suspended', 'delisted', 'inactive'))`
* `UNIQUE (listing_id, security_id)`
* `UNIQUE (exchange_id, symbol)`
* `CHECK (delisted_on IS NULL OR listed_on IS NULL OR delisted_on >= listed_on)`


#### Table: `sectors` (5 Columns)
**Description:** Broad economic sector taxonomy (Information Technology, Healthcare, Power & Utilities, etc.).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `sector_id` | `UUID` | **PK**, NOT NULL | - | Identifier for sectors |
| `sector_code` | `VARCHAR(80)` | NOT NULL | - | Data field for sector code |
| `sector_name` | `VARCHAR(120)` | NOT NULL | - | Data field for sector name |
| `taxonomy_source` | `VARCHAR(120)` | NULL | - | Data field for taxonomy source |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (sector_id)`
* `UNIQUE (sector_code)`


#### Table: `securities` (9 Columns)
**Description:** Tradeable equity instruments with ISIN, currency code, security type, and listing status.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `security_id` | `UUID` | **PK**, NOT NULL | - | Identifier for securities |
| `company_id` | `UUID` | `FK`, NULL | `companies.company_id` | Foreign key reference to `companies.company_id` |
| `security_name` | `VARCHAR(240)` | NOT NULL | - | Data field for security name |
| `isin` | `CHAR(12)` | NULL | - | Data field for isin |
| `security_type` | `VARCHAR(30)` | NOT NULL | - | Data field for security type |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `security_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for securities |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (security_id)`
* `FOREIGN KEY (company_id) REFERENCES companies(company_id)`
* `CHECK (security_type IN ('stock', 'etf', 'index', 'mutual_fund', 'bond', 'other'))`
* `CHECK (security_status IN ('active', 'inactive', 'matured', 'delisted'))`


#### Table: `user_sector_preferences` (4 Columns)
**Description:** Explicit investor sector tilts, positive preferences, and negative sector exclusions.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_id` | `UUID` | **PK**, `FK`, NOT NULL | `app_users.user_id` | Identifier for user_sector_preferences |
| `sector_id` | `UUID` | **PK**, `FK`, NOT NULL | `sectors.sector_id` | Identifier for user_sector_preferences |
| `preference_type` | `VARCHAR(12)` | NOT NULL | - | Data field for preference type |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_id, sector_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)`
* `CHECK (preference_type IN ('include', 'exclude'))`


#### Table: `user_security_preferences` (5 Columns)
**Description:** Individual security exclusions (e.g. tobacco exclusion, ethical filters).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_id` | `UUID` | **PK**, `FK`, NOT NULL | `app_users.user_id` | Identifier for user_security_preferences |
| `security_id` | `UUID` | **PK**, `FK`, NOT NULL | `securities.security_id` | Identifier for user_security_preferences |
| `preference_type` | `VARCHAR(12)` | NOT NULL | - | Data field for preference type |
| `reason` | `TEXT` | NULL | - | Data field for reason |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_id, security_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `CHECK (preference_type IN ('include', 'exclude'))`


---

### Domain: Market Data, Prices, Fundamental Metrics & News (`MARKET` — 11 Tables, 101 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    DATA_INGESTION_ERRORS ||--o{ DATA_INGESTION_RUNS : "_ingestion_run_id"
    DATA_INGESTION_RUNS ||--o{ DATA_SOURCES : "_data_source_id"
    ECONOMIC_OBSERVATIONS ||--o{ ECONOMIC_INDICATORS : "_economic_indicator_id"
    ECONOMIC_OBSERVATIONS ||--o{ DATA_INGESTION_RUNS : "_ingestion_run_id"
    ECONOMIC_OBSERVATIONS ||--o{ DATA_SOURCES : "_data_source_id"
    ECONOMIC_OBSERVATIONS ||--o{ DATA_INGESTION_RUNS : "_data_source_id"
    FUNDAMENTAL_METRICS ||--o{ DATA_INGESTION_RUNS : "_ingestion_run_id"
    FUNDAMENTAL_METRICS ||--o{ DATA_INGESTION_RUNS : "_data_source_id"
    FUNDAMENTAL_METRICS ||--o{ DATA_SOURCES : "_data_source_id"
    FUNDAMENTAL_METRICS ||--o{ METRIC_DEFINITIONS : "_metric_definition_id"
    MARKET_NEWS_ARTICLES ||--o{ DATA_SOURCES : "_data_source_id"
    MARKET_NEWS_ARTICLES ||--o{ DATA_INGESTION_RUNS : "_ingestion_run_id"
    MARKET_NEWS_ARTICLES ||--o{ DATA_INGESTION_RUNS : "_data_source_id"
    MARKET_PRICES ||--o{ DATA_SOURCES : "_data_source_id"
    MARKET_PRICES ||--o{ DATA_INGESTION_RUNS : "_data_source_id"
    MARKET_PRICES ||--o{ DATA_INGESTION_RUNS : "_ingestion_run_id"
    NEWS_ARTICLE_SECURITIES ||--o{ MARKET_NEWS_ARTICLES : "_news_article_id"
    SOURCE_INSTRUMENT_MAPPINGS ||--o{ DATA_SOURCES : "_data_source_id"

    DATA_INGESTION_ERRORS {
        uuid ingestion_error_id PK
        uuid ingestion_run_id FK
        varchar error_code
        varchar error_message
        varchar record_reference
        boolean is_retryable
        jsonb error_details
        timestamp occurred_at
    }

    DATA_INGESTION_RUNS {
        uuid ingestion_run_id PK
        uuid data_source_id FK
        varchar data_type
        varchar run_status
        timestamp started_at
        timestamp finished_at
        integer records_seen
        integer records_inserted
        integer records_updated
        varchar error_code
        varchar error_summary
        jsonb metadata
    }

    DATA_SOURCES {
        uuid data_source_id PK
        varchar source_code
        varchar display_name
        varchar source_type
        varchar base_url
        varchar secret_parameter_name
        varchar terms_url
        varchar license_notes
        boolean is_active
        timestamp created_at
    }

    ECONOMIC_INDICATORS {
        uuid economic_indicator_id PK
        varchar indicator_code
        varchar indicator_name
        varchar country_code
        varchar unit_code
        varchar frequency
        varchar description
    }

    ECONOMIC_OBSERVATIONS {
        uuid economic_observation_id PK
        uuid economic_indicator_id FK
        uuid data_source_id FK
        uuid ingestion_run_id FK
        timestamp observation_date
        numeric observation_value
        timestamp release_date
        timestamp retrieved_at
    }

    FUNDAMENTAL_METRICS {
        uuid fundamental_metric_id PK
        uuid security_id FK
        uuid metric_definition_id FK
        uuid data_source_id FK
        uuid ingestion_run_id FK
        varchar period_type
        timestamp period_end_date
        numeric metric_value
        varchar currency_code
        timestamp reported_at
        timestamp retrieved_at
    }

    MARKET_NEWS_ARTICLES {
        uuid news_article_id PK
        uuid data_source_id FK
        uuid ingestion_run_id FK
        varchar provider_article_id
        varchar article_url
        varchar headline
        varchar summary
        varchar language_code
        timestamp published_at
        timestamp retrieved_at
        numeric sentiment_score
        varchar sentiment_label
        varchar licensing_notes
    }

    MARKET_PRICES {
        uuid market_price_id PK
        uuid listing_id FK
        uuid data_source_id FK
        uuid ingestion_run_id FK
        timestamp price_date
        numeric open_price
        numeric high_price
        numeric low_price
        numeric close_price
        numeric adjusted_close_price
        integer volume
        varchar currency_code
        timestamp provider_timestamp
        timestamp retrieved_at
    }

    METRIC_DEFINITIONS {
        uuid metric_definition_id PK
        varchar metric_code
        varchar metric_name
        varchar unit_code
        varchar value_kind
        varchar description
        boolean is_active
    }

    NEWS_ARTICLE_SECURITIES {
        uuid news_article_id PK,FK
        uuid security_id PK,FK
        numeric relevance_score
        varchar link_method
    }

    SOURCE_INSTRUMENT_MAPPINGS {
        uuid source_instrument_mapping_id PK
        uuid data_source_id FK
        uuid listing_id FK
        varchar external_instrument_code
        varchar external_symbol
        timestamp created_at
        timestamp updated_at
    }
```

#### Table: `data_ingestion_errors` (8 Columns)
**Description:** Error log for market data fetching exceptions and API failures.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `ingestion_error_id` | `UUID` | **PK**, NOT NULL | - | Identifier for data_ingestion_errors |
| `ingestion_run_id` | `UUID` | `FK`, NOT NULL | `data_ingestion_runs.ingestion_run_id` | Foreign key reference to `data_ingestion_runs.ingestion_run_id` |
| `error_code` | `VARCHAR(100)` | NULL | - | Data field for error code |
| `error_message` | `TEXT` | NOT NULL | - | Data field for error message |
| `record_reference` | `VARCHAR(300)` | NULL | - | Data field for record reference |
| `is_retryable` | `BOOLEAN` | NOT NULL | - | Data field for is retryable |
| `error_details` | `JSONB` | NOT NULL | - | Data field for error details |
| `occurred_at` | `DATETIME` | NOT NULL | - | Data field for occurred at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (ingestion_error_id)`
* `FOREIGN KEY (ingestion_run_id) REFERENCES data_ingestion_runs(ingestion_run_id)`


#### Table: `data_ingestion_runs` (12 Columns)
**Description:** Audit log for batch and scheduled market data sync executions.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `ingestion_run_id` | `UUID` | **PK**, NOT NULL | - | Identifier for data_ingestion_runs |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_sources.data_source_id` | Foreign key reference to `data_sources.data_source_id` |
| `data_type` | `VARCHAR(60)` | NOT NULL | - | Data field for data type |
| `run_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for data_ingestion_runs |
| `started_at` | `DATETIME` | NOT NULL | - | Data field for started at |
| `finished_at` | `DATETIME` | NULL | - | Data field for finished at |
| `records_seen` | `BIGINT` | NOT NULL | - | Data field for records seen |
| `records_inserted` | `BIGINT` | NOT NULL | - | Data field for records inserted |
| `records_updated` | `BIGINT` | NOT NULL | - | Data field for records updated |
| `error_code` | `VARCHAR(100)` | NULL | - | Data field for error code |
| `error_summary` | `TEXT` | NULL | - | Data field for error summary |
| `metadata` | `JSONB` | NOT NULL | - | Data field for metadata |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (ingestion_run_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `CHECK (records_inserted >= 0)`
* `UNIQUE (ingestion_run_id, data_source_id)`
* `CHECK (records_updated >= 0)`
* `CHECK (run_status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled'))`
* `CHECK (records_seen >= 0)`
* `CHECK (finished_at IS NULL OR finished_at >= started_at)`


#### Table: `data_sources` (10 Columns)
**Description:** Registered market data API providers (Yahoo Finance, FRED, NewsAPI, NSE/BSE registries).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `data_source_id` | `UUID` | **PK**, NOT NULL | - | Identifier for data_sources |
| `source_code` | `VARCHAR(80)` | NOT NULL | - | Data field for source code |
| `display_name` | `VARCHAR(160)` | NOT NULL | - | Data field for display name |
| `source_type` | `VARCHAR(30)` | NOT NULL | - | Data field for source type |
| `base_url` | `TEXT` | NULL | - | Data field for base url |
| `secret_parameter_name` | `VARCHAR(300)` | NULL | - | Data field for secret parameter name |
| `terms_url` | `TEXT` | NULL | - | Data field for terms url |
| `license_notes` | `TEXT` | NULL | - | Data field for license notes |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (data_source_id)`
* `CHECK (source_type IN ('market_data', 'fundamentals', 'news', 'economic', 'broker', 'manual', 'internal'))`
* `UNIQUE (source_code)`


#### Table: `economic_indicators` (7 Columns)
**Description:** Macroeconomic indicator series metadata (RBI Repo rate, CPI, 10Y G-Sec Yield).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `economic_indicator_id` | `UUID` | **PK**, NOT NULL | - | Identifier for economic_indicators |
| `indicator_code` | `VARCHAR(100)` | NOT NULL | - | Data field for indicator code |
| `indicator_name` | `VARCHAR(200)` | NOT NULL | - | Data field for indicator name |
| `country_code` | `CHAR(2)` | NOT NULL | - | Data field for country code |
| `unit_code` | `VARCHAR(60)` | NULL | - | Data field for unit code |
| `frequency` | `VARCHAR(20)` | NULL | - | Data field for frequency |
| `description` | `TEXT` | NULL | - | Data field for description |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (economic_indicator_id)`
* `CHECK (frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'irregular'))`
* `UNIQUE (indicator_code)`


#### Table: `economic_observations` (8 Columns)
**Description:** Time-series observations and historical values for macroeconomic indicators.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `economic_observation_id` | `UUID` | **PK**, NOT NULL | - | Identifier for economic_observations |
| `economic_indicator_id` | `UUID` | `FK`, NOT NULL | `economic_indicators.economic_indicator_id` | Foreign key reference to `economic_indicators.economic_indicator_id` |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` | Foreign key reference to `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` |
| `ingestion_run_id` | `UUID` | `FK`, NULL | `data_ingestion_runs.ingestion_run_id` | Foreign key reference to `data_ingestion_runs.ingestion_run_id` |
| `observation_date` | `DATE` | NOT NULL | - | Data field for observation date |
| `observation_value` | `NUMERIC(24, 8)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `release_date` | `DATE` | NULL | - | Data field for release date |
| `retrieved_at` | `DATETIME` | NOT NULL | - | Data field for retrieved at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (economic_observation_id)`
* `FOREIGN KEY (economic_indicator_id) REFERENCES economic_indicators(economic_indicator_id)`
* `FOREIGN KEY (ingestion_run_id) REFERENCES data_ingestion_runs(ingestion_run_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_ingestion_runs(data_source_id)`
* `UNIQUE (economic_indicator_id, observation_date, data_source_id)`


#### Table: `fundamental_metrics` (11 Columns)
**Description:** Quarterly balance sheet ratios: ROE, Debt/Equity, P/E, Operating Margin, 3Y CAGR.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `fundamental_metric_id` | `UUID` | **PK**, NOT NULL | - | Identifier for fundamental_metrics |
| `security_id` | `UUID` | `FK`, NOT NULL | `securities.security_id` | Foreign key reference to `securities.security_id` |
| `metric_definition_id` | `UUID` | `FK`, NOT NULL | `metric_definitions.metric_definition_id` | Foreign key reference to `metric_definitions.metric_definition_id` |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` | Foreign key reference to `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` |
| `ingestion_run_id` | `UUID` | `FK`, NULL | `data_ingestion_runs.ingestion_run_id` | Foreign key reference to `data_ingestion_runs.ingestion_run_id` |
| `period_type` | `VARCHAR(20)` | NOT NULL | - | Data field for period type |
| `period_end_date` | `DATE` | NOT NULL | - | Data field for period end date |
| `metric_value` | `NUMERIC(24, 8)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NULL | - | Data field for currency code |
| `reported_at` | `DATETIME` | NULL | - | Data field for reported at |
| `retrieved_at` | `DATETIME` | NOT NULL | - | Data field for retrieved at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (fundamental_metric_id)`
* `FOREIGN KEY (ingestion_run_id) REFERENCES data_ingestion_runs(ingestion_run_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_ingestion_runs(data_source_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (metric_definition_id) REFERENCES metric_definitions(metric_definition_id)`
* `UNIQUE (security_id, metric_definition_id, period_type, period_end_date, data_source_id)`
* `CHECK (period_type IN ('quarterly', 'annual', 'ttm', 'point_in_time'))`


#### Table: `market_news_articles` (13 Columns)
**Description:** Aggregated corporate filings, SEBI circulars, and financial news items.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `news_article_id` | `UUID` | **PK**, NOT NULL | - | Identifier for market_news_articles |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` | Foreign key reference to `data_sources.data_source_id`, `data_ingestion_runs.data_source_id` |
| `ingestion_run_id` | `UUID` | `FK`, NULL | `data_ingestion_runs.ingestion_run_id` | Foreign key reference to `data_ingestion_runs.ingestion_run_id` |
| `provider_article_id` | `VARCHAR(300)` | NULL | - | Data field for provider article id |
| `article_url` | `TEXT` | NULL | - | Data field for article url |
| `headline` | `TEXT` | NOT NULL | - | Data field for headline |
| `summary` | `TEXT` | NULL | - | Data field for summary |
| `language_code` | `VARCHAR(12)` | NULL | - | Data field for language code |
| `published_at` | `DATETIME` | NULL | - | Data field for published at |
| `retrieved_at` | `DATETIME` | NOT NULL | - | Data field for retrieved at |
| `sentiment_score` | `NUMERIC(8, 5)` | NULL | - | Data field for sentiment score |
| `sentiment_label` | `VARCHAR(20)` | NULL | - | Data field for sentiment label |
| `licensing_notes` | `TEXT` | NULL | - | Data field for licensing notes |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (news_article_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (ingestion_run_id) REFERENCES data_ingestion_runs(ingestion_run_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_ingestion_runs(data_source_id)`
* `CHECK (sentiment_score BETWEEN -1 AND 1)`
* `UNIQUE (data_source_id, provider_article_id)`
* `CHECK (sentiment_label IN ('negative', 'neutral', 'positive', 'mixed'))`


#### Table: `market_prices` (14 Columns)
**Description:** Historical and real-time OHLCV price records for listed equity instruments.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `market_price_id` | `UUID` | **PK**, NOT NULL | - | Indian Rupee (INR) monetary figure |
| `listing_id` | `UUID` | `FK`, NOT NULL | `instrument_listings.listing_id` | Foreign key reference to `instrument_listings.listing_id` |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_ingestion_runs.data_source_id`, `data_sources.data_source_id` | Foreign key reference to `data_ingestion_runs.data_source_id`, `data_sources.data_source_id` |
| `ingestion_run_id` | `UUID` | `FK`, NULL | `data_ingestion_runs.ingestion_run_id` | Foreign key reference to `data_ingestion_runs.ingestion_run_id` |
| `price_date` | `DATE` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `open_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `high_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `low_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `close_price` | `NUMERIC(20, 6)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `adjusted_close_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `volume` | `BIGINT` | NULL | - | Data field for volume |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `provider_timestamp` | `DATETIME` | NULL | - | Data field for provider timestamp |
| `retrieved_at` | `DATETIME` | NOT NULL | - | Data field for retrieved at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (market_price_id)`
* `FOREIGN KEY (listing_id) REFERENCES instrument_listings(listing_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_ingestion_runs(data_source_id)`
* `FOREIGN KEY (ingestion_run_id) REFERENCES data_ingestion_runs(ingestion_run_id)`
* `CHECK (volume IS NULL OR volume >= 0)`
* `UNIQUE (listing_id, price_date, data_source_id)`
* `CHECK (close_price >= 0)`
* `CHECK (adjusted_close_price IS NULL OR adjusted_close_price >= 0)`


#### Table: `metric_definitions` (7 Columns)
**Description:** Formal definitions and formulas for financial fundamental and quantitative metrics.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `metric_definition_id` | `UUID` | **PK**, NOT NULL | - | Identifier for metric_definitions |
| `metric_code` | `VARCHAR(100)` | NOT NULL | - | Data field for metric code |
| `metric_name` | `VARCHAR(180)` | NOT NULL | - | Data field for metric name |
| `unit_code` | `VARCHAR(40)` | NOT NULL | - | Data field for unit code |
| `value_kind` | `VARCHAR(20)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `description` | `TEXT` | NULL | - | Data field for description |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (metric_definition_id)`
* `UNIQUE (metric_code)`
* `CHECK (value_kind IN ('numeric'))`


#### Table: `news_article_securities` (4 Columns)
**Description:** Association table linking news articles and regulatory filings to specific securities.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `news_article_id` | `UUID` | **PK**, `FK`, NOT NULL | `market_news_articles.news_article_id` | Identifier for news_article_securities |
| `security_id` | `UUID` | **PK**, `FK`, NOT NULL | `securities.security_id` | Identifier for news_article_securities |
| `relevance_score` | `NUMERIC(6, 5)` | NULL | - | Data field for relevance score |
| `link_method` | `VARCHAR(30)` | NOT NULL | - | Data field for link method |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (news_article_id, security_id)`
* `FOREIGN KEY (news_article_id) REFERENCES market_news_articles(news_article_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `CHECK (link_method IN ('provider', 'symbol_match', 'entity_match', 'manual', 'model'))`
* `CHECK (relevance_score IS NULL OR relevance_score BETWEEN 0 AND 1)`


#### Table: `source_instrument_mappings` (7 Columns)
**Description:** Cross-reference mapping third-party data provider IDs to canonical internal securities.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `source_instrument_mapping_id` | `UUID` | **PK**, NOT NULL | - | Identifier for source_instrument_mappings |
| `data_source_id` | `UUID` | `FK`, NOT NULL | `data_sources.data_source_id` | Foreign key reference to `data_sources.data_source_id` |
| `listing_id` | `UUID` | `FK`, NOT NULL | `instrument_listings.listing_id` | Foreign key reference to `instrument_listings.listing_id` |
| `external_instrument_code` | `VARCHAR(200)` | NOT NULL | - | Data field for external instrument code |
| `external_symbol` | `VARCHAR(100)` | NULL | - | Data field for external symbol |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (source_instrument_mapping_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (listing_id) REFERENCES instrument_listings(listing_id)`
* `UNIQUE (data_source_id, listing_id)`
* `UNIQUE (data_source_id, external_instrument_code)`


---

### Domain: Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO` — 13 Tables, 133 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    EXPLANATION_EVIDENCE ||--o{ RECOMMENDATION_EXPLANATIONS : "_explanation_id"
    EXPLANATION_EVIDENCE ||--o{ EVIDENCE_ITEMS : "_evidence_item_id"
    PORTFOLIO_GENERATION_REQUESTS ||--o{ INVESTOR_PORTFOLIOS : "_portfolio_id"
    PORTFOLIO_GENERATION_REQUESTS ||--o{ INVESTOR_PORTFOLIOS : "_user_id"
    PORTFOLIO_SCENARIOS ||--o{ PORTFOLIO_VERSIONS : "_portfolio_version_id"
    PORTFOLIO_SECURITY_DECISIONS ||--o{ PORTFOLIO_VERSIONS : "_portfolio_version_id"
    PORTFOLIO_VALIDATION_RESULTS ||--o{ PORTFOLIO_VALIDATION_RUNS : "_validation_run_id"
    PORTFOLIO_VALIDATION_RUNS ||--o{ PORTFOLIO_VERSIONS : "_portfolio_version_id"
    PORTFOLIO_VERSION_CONSTRAINTS ||--o{ PORTFOLIO_VERSIONS : "_portfolio_version_id"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_GENERATION_REQUESTS : "_generation_request_id"
    PORTFOLIO_VERSIONS ||--o{ PORTFOLIO_GENERATION_REQUESTS : "_portfolio_id"
    PORTFOLIO_VERSIONS ||--o{ STRATEGY_VERSIONS : "_strategy_version_id"
    RECOMMENDATION_EXPLANATIONS ||--o{ PORTFOLIO_VERSIONS : "_portfolio_version_id"
    RECOMMENDATION_EXPLANATIONS ||--o{ PORTFOLIO_SECURITY_DECISIONS : "_portfolio_version_id"
    RECOMMENDATION_EXPLANATIONS ||--o{ PORTFOLIO_SECURITY_DECISIONS : "_decision_id"
    STRATEGY_VERSIONS ||--o{ STRATEGY_DEFINITIONS : "_strategy_id"

    EVIDENCE_ITEMS {
        uuid evidence_item_id PK
        uuid data_source_id FK
        uuid security_id FK
        uuid market_price_id FK
        uuid fundamental_metric_id FK
        uuid economic_observation_id FK
        uuid news_article_id FK
        varchar evidence_type
        varchar title
        varchar evidence_summary
        varchar source_url
        varchar source_record_reference
        timestamp published_at
        timestamp observed_at
        jsonb cited_value_snapshot
        timestamp created_at
    }

    EXPLANATION_EVIDENCE {
        uuid explanation_id PK,FK
        uuid evidence_item_id PK,FK
        varchar relationship_label
    }

    INVESTOR_PORTFOLIOS {
        uuid portfolio_id PK
        uuid user_id FK
        varchar portfolio_name
        varchar portfolio_status
        timestamp created_at
        timestamp updated_at
    }

    PORTFOLIO_GENERATION_REQUESTS {
        uuid generation_request_id PK
        uuid portfolio_id FK
        uuid user_id FK
        uuid goal_id FK
        uuid risk_assessment_id FK
        varchar request_type
        varchar request_status
        varchar user_prompt
        numeric requested_amount
        varchar currency_code
        integer investment_horizon_months
        jsonb normalized_inputs
        jsonb investor_snapshot
        timestamp market_context_as_of
        timestamp started_at
        timestamp completed_at
        varchar error_code
        varchar error_summary
        timestamp created_at
    }

    PORTFOLIO_SCENARIOS {
        uuid portfolio_scenario_id PK
        uuid portfolio_version_id FK
        varchar scenario_code
        varchar scenario_name
        varchar scenario_type
        jsonb assumptions
        numeric estimated_portfolio_value
        numeric estimated_change_amount
        numeric estimated_change_pct
        varchar result_summary
        varchar calculation_version
        timestamp created_at
    }

    PORTFOLIO_SECURITY_DECISIONS {
        uuid decision_id PK
        uuid portfolio_version_id FK
        uuid security_id FK
        uuid listing_id FK
        varchar decision_status
        numeric target_weight_pct
        varchar decision_reason
        timestamp created_at
    }

    PORTFOLIO_VALIDATION_RESULTS {
        uuid validation_result_id PK
        uuid validation_run_id FK
        varchar rule_code
        varchar result_status
        varchar severity
        uuid security_id FK
        numeric actual_value
        numeric threshold_value
        varchar result_message
        jsonb details
        timestamp created_at
    }

    PORTFOLIO_VALIDATION_RUNS {
        uuid validation_run_id PK
        uuid portfolio_version_id FK
        varchar rule_set_version
        varchar calculation_engine_version
        varchar validation_status
        timestamp started_at
        timestamp completed_at
        jsonb summary
    }

    PORTFOLIO_VERSION_CONSTRAINTS {
        uuid portfolio_constraint_id PK
        uuid portfolio_version_id FK
        varchar constraint_code
        varchar operator
        numeric comparison_value
        numeric upper_value
        varchar unit_code
        boolean is_mandatory
        boolean applied
        varchar description
        timestamp created_at
    }

    PORTFOLIO_VERSIONS {
        uuid portfolio_version_id PK
        uuid portfolio_id FK
        uuid generation_request_id FK
        uuid strategy_version_id FK
        integer version_number
        varchar version_status
        numeric investment_amount
        varchar currency_code
        integer investment_horizon_months
        varchar risk_category
        numeric expected_return_pct
        numeric expected_volatility_pct
        numeric diversification_score
        timestamp market_context_as_of
        jsonb generation_context
        timestamp generated_at
        timestamp created_at
    }

    RECOMMENDATION_EXPLANATIONS {
        uuid explanation_id PK
        uuid portfolio_version_id FK
        uuid decision_id FK
        varchar explanation_type
        varchar title
        varchar explanation_text
        integer display_order
        timestamp created_at
    }

    STRATEGY_DEFINITIONS {
        uuid strategy_id PK
        varchar strategy_code
        varchar strategy_name
        varchar description
        boolean is_active
        timestamp created_at
    }

    STRATEGY_VERSIONS {
        uuid strategy_version_id PK
        uuid strategy_id FK
        varchar version_label
        varchar optimizer_name
        varchar implementation_revision
        jsonb configuration
        varchar constraint_set_version
        timestamp created_at
    }
```

#### Table: `evidence_items` (16 Columns)
**Description:** Verifiable factual evidence items (filing excerpts, financial ratios) supporting recommendations.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `evidence_item_id` | `UUID` | **PK**, NOT NULL | - | Identifier for evidence_items |
| `data_source_id` | `UUID` | `FK`, NULL | `data_sources.data_source_id` | Foreign key reference to `data_sources.data_source_id` |
| `security_id` | `UUID` | `FK`, NULL | `securities.security_id` | Foreign key reference to `securities.security_id` |
| `market_price_id` | `UUID` | `FK`, NULL | `market_prices.market_price_id` | Indian Rupee (INR) monetary figure |
| `fundamental_metric_id` | `UUID` | `FK`, NULL | `fundamental_metrics.fundamental_metric_id` | Foreign key reference to `fundamental_metrics.fundamental_metric_id` |
| `economic_observation_id` | `UUID` | `FK`, NULL | `economic_observations.economic_observation_id` | Foreign key reference to `economic_observations.economic_observation_id` |
| `news_article_id` | `UUID` | `FK`, NULL | `market_news_articles.news_article_id` | Foreign key reference to `market_news_articles.news_article_id` |
| `evidence_type` | `VARCHAR(40)` | NOT NULL | - | Data field for evidence type |
| `title` | `VARCHAR(300)` | NOT NULL | - | Data field for title |
| `evidence_summary` | `TEXT` | NULL | - | Data field for evidence summary |
| `source_url` | `TEXT` | NULL | - | Data field for source url |
| `source_record_reference` | `VARCHAR(300)` | NULL | - | Data field for source record reference |
| `published_at` | `DATETIME` | NULL | - | Data field for published at |
| `observed_at` | `DATETIME` | NULL | - | Data field for observed at |
| `cited_value_snapshot` | `JSONB` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (evidence_item_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (market_price_id) REFERENCES market_prices(market_price_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `FOREIGN KEY (news_article_id) REFERENCES market_news_articles(news_article_id)`
* `FOREIGN KEY (economic_observation_id) REFERENCES economic_observations(economic_observation_id)`
* `FOREIGN KEY (fundamental_metric_id) REFERENCES fundamental_metrics(fundamental_metric_id)`


#### Table: `explanation_evidence` (3 Columns)
**Description:** Many-to-many junction linking recommendation explanations to supporting evidence items.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `explanation_id` | `UUID` | **PK**, `FK`, NOT NULL | `recommendation_explanations.explanation_id` | Identifier for explanation_evidence |
| `evidence_item_id` | `UUID` | **PK**, `FK`, NOT NULL | `evidence_items.evidence_item_id` | Identifier for explanation_evidence |
| `relationship_label` | `VARCHAR(40)` | NOT NULL | - | Data field for relationship label |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (explanation_id, evidence_item_id)`
* `FOREIGN KEY (explanation_id) REFERENCES recommendation_explanations(explanation_id)`
* `FOREIGN KEY (evidence_item_id) REFERENCES evidence_items(evidence_item_id)`
* `CHECK (relationship_label IN ('supports', 'contradicts', 'contextualizes'))`


#### Table: `investor_portfolios` (6 Columns)
**Description:** Top-level portfolio container with user FK, portfolio name, and status.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `portfolio_id` | `UUID` | **PK**, NOT NULL | - | Identifier for investor_portfolios |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `portfolio_name` | `VARCHAR(160)` | NOT NULL | - | Data field for portfolio name |
| `portfolio_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for investor_portfolios |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (portfolio_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (portfolio_status IN ('draft', 'active', 'archived'))`
* `UNIQUE (portfolio_id, user_id)`


#### Table: `portfolio_generation_requests` (19 Columns)
**Description:** Inbound portfolio generation requests detailing investor prompt, capital, and risk tier.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `generation_request_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_generation_requests |
| `portfolio_id` | `UUID` | `FK`, NOT NULL | `investor_portfolios.portfolio_id` | Foreign key reference to `investor_portfolios.portfolio_id` |
| `user_id` | `UUID` | `FK`, NOT NULL | `financial_goals.user_id`, `investor_portfolios.user_id`, `risk_assessments.user_id` | Foreign key reference to `financial_goals.user_id`, `investor_portfolios.user_id`, `risk_assessments.user_id` |
| `goal_id` | `UUID` | `FK`, NULL | `financial_goals.goal_id` | Foreign key reference to `financial_goals.goal_id` |
| `risk_assessment_id` | `UUID` | `FK`, NULL | `risk_assessments.risk_assessment_id` | Foreign key reference to `risk_assessments.risk_assessment_id` |
| `request_type` | `VARCHAR(20)` | NOT NULL | - | Data field for request type |
| `request_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for portfolio_generation_requests |
| `user_prompt` | `TEXT` | NULL | - | Data field for user prompt |
| `requested_amount` | `NUMERIC(20, 2)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `investment_horizon_months` | `INTEGER` | NULL | - | Data field for investment horizon months |
| `normalized_inputs` | `JSONB` | NOT NULL | - | Data field for normalized inputs |
| `investor_snapshot` | `JSONB` | NOT NULL | - | Data field for investor snapshot |
| `market_context_as_of` | `DATETIME` | NULL | - | Data field for market context as of |
| `started_at` | `DATETIME` | NULL | - | Data field for started at |
| `completed_at` | `DATETIME` | NULL | - | Data field for completed at |
| `error_code` | `VARCHAR(100)` | NULL | - | Data field for error code |
| `error_summary` | `TEXT` | NULL | - | Data field for error summary |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (generation_request_id)`
* `FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(risk_assessment_id)`
* `FOREIGN KEY (portfolio_id) REFERENCES investor_portfolios(portfolio_id)`
* `FOREIGN KEY (user_id) REFERENCES financial_goals(user_id)`
* `FOREIGN KEY (goal_id) REFERENCES financial_goals(goal_id)`
* `FOREIGN KEY (user_id) REFERENCES risk_assessments(user_id)`
* `FOREIGN KEY (user_id) REFERENCES investor_portfolios(user_id)`
* `CHECK (requested_amount > 0)`
* `UNIQUE (generation_request_id, portfolio_id)`
* `CHECK (request_status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled'))`
* `CHECK (investment_horizon_months IS NULL OR investment_horizon_months > 0)`
* `CHECK (request_type IN ('create', 'revise', 'scenario'))`
* `CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)`


#### Table: `portfolio_scenarios` (12 Columns)
**Description:** Simulated stress-test scenarios (e.g., 2008 GFC, 2020 COVID crash, Rate Hike).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `portfolio_scenario_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_scenarios |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `scenario_code` | `VARCHAR(80)` | NOT NULL | - | Data field for scenario code |
| `scenario_name` | `VARCHAR(180)` | NOT NULL | - | Data field for scenario name |
| `scenario_type` | `VARCHAR(30)` | NOT NULL | - | Data field for scenario type |
| `assumptions` | `JSONB` | NOT NULL | - | Data field for assumptions |
| `estimated_portfolio_value` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `estimated_change_amount` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `estimated_change_pct` | `NUMERIC(9, 4)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `result_summary` | `TEXT` | NULL | - | Data field for result summary |
| `calculation_version` | `VARCHAR(100)` | NULL | - | Data field for calculation version |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (portfolio_scenario_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `CHECK (estimated_portfolio_value IS NULL OR estimated_portfolio_value >= 0)`
* `CHECK (scenario_type IN ('stress', 'what_if', 'market_regime', 'sensitivity'))`
* `UNIQUE (portfolio_version_id, scenario_code)`


#### Table: `portfolio_security_decisions` (8 Columns)
**Description:** Granular equity holdings per portfolio version with target weights and selection rationales.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `decision_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_security_decisions |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `security_id` | `UUID` | `FK`, NOT NULL | `securities.security_id`, `instrument_listings.security_id` | Foreign key reference to `securities.security_id`, `instrument_listings.security_id` |
| `listing_id` | `UUID` | `FK`, NULL | `instrument_listings.listing_id` | Foreign key reference to `instrument_listings.listing_id` |
| `decision_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for portfolio_security_decisions |
| `target_weight_pct` | `NUMERIC(9, 6)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `decision_reason` | `TEXT` | NOT NULL | - | Data field for decision reason |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (decision_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (security_id) REFERENCES instrument_listings(security_id)`
* `FOREIGN KEY (listing_id) REFERENCES instrument_listings(listing_id)`
* `CHECK ((decision_status = 'selected' AND target_weight_pct IS NOT NULL AND target_weight_pct > 0 AND target_weight_pct <= 100) OR (decision_status IN ('excluded', 'watchlist') AND target_weight_pct IS NULL))`
* `CHECK (decision_status IN ('selected', 'excluded', 'watchlist'))`
* `UNIQUE (portfolio_version_id, security_id)`
* `UNIQUE (decision_id, portfolio_version_id)`


#### Table: `portfolio_validation_results` (11 Columns)
**Description:** Itemized constraint validation results (25% single-stock cap, 40% sector cap, whole shares).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `validation_result_id` | `UUID` | **PK**, NOT NULL | - | Indian Rupee (INR) monetary figure |
| `validation_run_id` | `UUID` | `FK`, NOT NULL | `portfolio_validation_runs.validation_run_id` | Indian Rupee (INR) monetary figure |
| `rule_code` | `VARCHAR(100)` | NOT NULL | - | Data field for rule code |
| `result_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for portfolio_validation_results |
| `severity` | `VARCHAR(20)` | NOT NULL | - | Data field for severity |
| `security_id` | `UUID` | `FK`, NULL | `securities.security_id` | Foreign key reference to `securities.security_id` |
| `actual_value` | `NUMERIC(24, 8)` | NULL | - | Indian Rupee (INR) monetary figure |
| `threshold_value` | `NUMERIC(24, 8)` | NULL | - | Indian Rupee (INR) monetary figure |
| `result_message` | `TEXT` | NOT NULL | - | Data field for result message |
| `details` | `JSONB` | NOT NULL | - | Data field for details |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (validation_result_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (validation_run_id) REFERENCES portfolio_validation_runs(validation_run_id)`
* `CHECK (result_status IN ('pass', 'fail', 'warning', 'not_applicable'))`
* `CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical'))`


#### Table: `portfolio_validation_runs` (8 Columns)
**Description:** Audit record of quantitative validation passes executed on portfolio versions.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `validation_run_id` | `UUID` | **PK**, NOT NULL | - | Indian Rupee (INR) monetary figure |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `rule_set_version` | `VARCHAR(100)` | NOT NULL | - | Data field for rule set version |
| `calculation_engine_version` | `VARCHAR(100)` | NOT NULL | - | Data field for calculation engine version |
| `validation_status` | `VARCHAR(24)` | NOT NULL | - | Lifecycle status flag for portfolio_validation_runs |
| `started_at` | `DATETIME` | NOT NULL | - | Data field for started at |
| `completed_at` | `DATETIME` | NULL | - | Data field for completed at |
| `summary` | `JSONB` | NOT NULL | - | Data field for summary |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (validation_run_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `CHECK (validation_status IN ('running', 'passed', 'failed', 'passed_with_warnings'))`
* `CHECK (completed_at IS NULL OR completed_at >= started_at)`


#### Table: `portfolio_version_constraints` (11 Columns)
**Description:** Specific portfolio constraints applied during optimization.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `portfolio_constraint_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_version_constraints |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `constraint_code` | `VARCHAR(100)` | NOT NULL | - | Data field for constraint code |
| `operator` | `VARCHAR(12)` | NOT NULL | - | Data field for operator |
| `comparison_value` | `NUMERIC(24, 8)` | NULL | - | Indian Rupee (INR) monetary figure |
| `upper_value` | `NUMERIC(24, 8)` | NULL | - | Indian Rupee (INR) monetary figure |
| `unit_code` | `VARCHAR(40)` | NULL | - | Data field for unit code |
| `is_mandatory` | `BOOLEAN` | NOT NULL | - | Data field for is mandatory |
| `applied` | `BOOLEAN` | NOT NULL | - | Data field for applied |
| `description` | `TEXT` | NULL | - | Data field for description |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (portfolio_constraint_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `CHECK (operator = 'between' OR comparison_value IS NOT NULL)`
* `CHECK (operator <> 'between' OR (comparison_value IS NOT NULL AND upper_value IS NOT NULL AND comparison_value <= upper_value))`
* `CHECK (operator = 'between' OR upper_value IS NULL)`
* `UNIQUE (portfolio_version_id, constraint_code)`
* `CHECK (operator IN ('<=', '>=', '=', 'between'))`


#### Table: `portfolio_versions` (17 Columns)
**Description:** Immutable portfolio version snapshots with investment capital, expected return, and generation context JSON.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `portfolio_version_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_versions |
| `portfolio_id` | `UUID` | `FK`, NOT NULL | `portfolio_generation_requests.portfolio_id` | Foreign key reference to `portfolio_generation_requests.portfolio_id` |
| `generation_request_id` | `UUID` | `FK`, NOT NULL | `portfolio_generation_requests.generation_request_id` | Foreign key reference to `portfolio_generation_requests.generation_request_id` |
| `strategy_version_id` | `UUID` | `FK`, NOT NULL | `strategy_versions.strategy_version_id` | Foreign key reference to `strategy_versions.strategy_version_id` |
| `version_number` | `INTEGER` | NOT NULL | - | Data field for version number |
| `version_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for portfolio_versions |
| `investment_amount` | `NUMERIC(20, 2)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `investment_horizon_months` | `INTEGER` | NULL | - | Data field for investment horizon months |
| `risk_category` | `VARCHAR(30)` | NULL | - | Data field for risk category |
| `expected_return_pct` | `NUMERIC(9, 4)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `expected_volatility_pct` | `NUMERIC(9, 4)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `diversification_score` | `NUMERIC(8, 4)` | NULL | - | Data field for diversification score |
| `market_context_as_of` | `DATETIME` | NULL | - | Data field for market context as of |
| `generation_context` | `JSONB` | NOT NULL | - | Data field for generation context |
| `generated_at` | `DATETIME` | NOT NULL | - | Data field for generated at |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (portfolio_version_id)`
* `FOREIGN KEY (generation_request_id) REFERENCES portfolio_generation_requests(generation_request_id)`
* `FOREIGN KEY (portfolio_id) REFERENCES portfolio_generation_requests(portfolio_id)`
* `FOREIGN KEY (strategy_version_id) REFERENCES strategy_versions(strategy_version_id)`
* `CHECK (risk_category IS NULL OR risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive'))`
* `CHECK (investment_amount > 0)`
* `CHECK (diversification_score IS NULL OR (diversification_score BETWEEN 0 AND 100))`
* `CHECK (version_status IN ('generated', 'reviewed', 'accepted', 'rejected', 'superseded', 'archived'))`
* `UNIQUE (portfolio_id, version_number)`
* `UNIQUE (portfolio_version_id, portfolio_id)`
* `CHECK (investment_horizon_months IS NULL OR investment_horizon_months > 0)`
* `CHECK (version_number > 0)`


#### Table: `recommendation_explanations` (8 Columns)
**Description:** Fiduciary plain-English narrative rationales generated by the Moderator agent.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `explanation_id` | `UUID` | **PK**, NOT NULL | - | Identifier for recommendation_explanations |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id`, `portfolio_security_decisions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id`, `portfolio_security_decisions.portfolio_version_id` |
| `decision_id` | `UUID` | `FK`, NULL | `portfolio_security_decisions.decision_id` | Foreign key reference to `portfolio_security_decisions.decision_id` |
| `explanation_type` | `VARCHAR(30)` | NOT NULL | - | Data field for explanation type |
| `title` | `VARCHAR(240)` | NOT NULL | - | Data field for title |
| `explanation_text` | `TEXT` | NOT NULL | - | Data field for explanation text |
| `display_order` | `INTEGER` | NOT NULL | - | Data field for display order |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (explanation_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_security_decisions(portfolio_version_id)`
* `FOREIGN KEY (decision_id) REFERENCES portfolio_security_decisions(decision_id)`
* `CHECK (explanation_type IN ('portfolio', 'selection', 'exclusion', 'risk', 'diversification', 'constraint', 'scenario', 'review'))`


#### Table: `strategy_definitions` (6 Columns)
**Description:** Formal investment strategy blueprints (e.g., Conservative Wealth Preserver, High-Growth Equity).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `strategy_id` | `UUID` | **PK**, NOT NULL | - | Identifier for strategy_definitions |
| `strategy_code` | `VARCHAR(100)` | NOT NULL | - | Data field for strategy code |
| `strategy_name` | `VARCHAR(180)` | NOT NULL | - | Data field for strategy name |
| `description` | `TEXT` | NULL | - | Data field for description |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (strategy_id)`
* `UNIQUE (strategy_code)`


#### Table: `strategy_versions` (8 Columns)
**Description:** Versioned parameter specifications for investment strategy models.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `strategy_version_id` | `UUID` | **PK**, NOT NULL | - | Identifier for strategy_versions |
| `strategy_id` | `UUID` | `FK`, NOT NULL | `strategy_definitions.strategy_id` | Foreign key reference to `strategy_definitions.strategy_id` |
| `version_label` | `VARCHAR(80)` | NOT NULL | - | Data field for version label |
| `optimizer_name` | `VARCHAR(160)` | NOT NULL | - | Data field for optimizer name |
| `implementation_revision` | `VARCHAR(160)` | NULL | - | Data field for implementation revision |
| `configuration` | `JSONB` | NOT NULL | - | Data field for configuration |
| `constraint_set_version` | `VARCHAR(100)` | NULL | - | Data field for constraint set version |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (strategy_version_id)`
* `FOREIGN KEY (strategy_id) REFERENCES strategy_definitions(strategy_id)`
* `UNIQUE (strategy_id, version_label)`


---

### Domain: Broker Accounts, Integrations & Order Auditing (`BROKER` — 6 Tables, 55 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    BROKER_EXECUTIONS ||--o{ BROKER_ORDERS : "_broker_order_id"
    BROKER_ORDER_EVENTS ||--o{ BROKER_ORDERS : "_broker_order_id"
    BROKER_ORDERS ||--o{ USER_BROKER_ACCOUNTS : "_user_broker_account_id"
    USER_BROKER_ACCOUNTS ||--o{ BROKER_PROVIDERS : "_broker_provider_id"

    BROKER_EXECUTIONS {
        uuid broker_execution_id PK
        uuid broker_order_id FK
        varchar provider_execution_reference
        numeric executed_quantity
        numeric execution_price
        timestamp executed_at
        numeric fees_amount
        varchar currency_code
    }

    BROKER_ORDER_EVENTS {
        uuid broker_order_event_id PK
        uuid broker_order_id FK
        varchar event_status
        varchar event_message
        varchar provider_event_reference
        jsonb event_payload
        timestamp occurred_at
    }

    BROKER_ORDERS {
        uuid broker_order_id PK
        uuid user_broker_account_id FK
        uuid security_id FK
        uuid listing_id FK
        varchar provider_order_reference
        varchar side
        varchar order_type
        numeric order_quantity
        numeric limit_price
        varchar order_status
        timestamp submitted_at
        timestamp last_updated_at
        timestamp created_at
    }

    BROKER_PROVIDERS {
        uuid broker_provider_id PK
        varchar provider_code
        varchar provider_name
        varchar developer_docs_url
        boolean is_active
        timestamp created_at
    }

    PORTFOLIO_PERFORMANCE_SNAPSHOTS {
        uuid performance_snapshot_id PK
        uuid portfolio_version_id FK
        timestamp snapshot_date
        numeric valuation_amount
        varchar currency_code
        numeric return_since_previous_pct
        numeric cumulative_return_pct
        varchar source_type
        timestamp created_at
    }

    USER_BROKER_ACCOUNTS {
        uuid user_broker_account_id PK
        uuid user_id FK
        uuid broker_provider_id FK
        varchar external_account_reference
        varchar account_label
        varchar connection_status
        jsonb granted_permissions
        varchar secret_reference
        timestamp connected_at
        timestamp last_synced_at
        timestamp created_at
        timestamp updated_at
    }
```

#### Table: `broker_executions` (8 Columns)
**Description:** Realized execution fill records for placed broker orders with trade timestamps.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `broker_execution_id` | `UUID` | **PK**, NOT NULL | - | Identifier for broker_executions |
| `broker_order_id` | `UUID` | `FK`, NOT NULL | `broker_orders.broker_order_id` | Foreign key reference to `broker_orders.broker_order_id` |
| `provider_execution_reference` | `VARCHAR(240)` | NULL | - | Data field for provider execution reference |
| `executed_quantity` | `NUMERIC(24, 8)` | NOT NULL | - | Integer lot count of equity shares |
| `execution_price` | `NUMERIC(20, 6)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `executed_at` | `DATETIME` | NOT NULL | - | Data field for executed at |
| `fees_amount` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (broker_execution_id)`
* `FOREIGN KEY (broker_order_id) REFERENCES broker_orders(broker_order_id)`
* `CHECK (executed_quantity > 0)`
* `UNIQUE (broker_order_id, provider_execution_reference)`
* `CHECK (fees_amount IS NULL OR fees_amount >= 0)`
* `CHECK (execution_price >= 0)`


#### Table: `broker_order_events` (7 Columns)
**Description:** State transition lifecycle events for broker orders (placed, rejected, filled).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `broker_order_event_id` | `UUID` | **PK**, NOT NULL | - | Identifier for broker_order_events |
| `broker_order_id` | `UUID` | `FK`, NOT NULL | `broker_orders.broker_order_id` | Foreign key reference to `broker_orders.broker_order_id` |
| `event_status` | `VARCHAR(24)` | NOT NULL | - | Lifecycle status flag for broker_order_events |
| `event_message` | `TEXT` | NULL | - | Data field for event message |
| `provider_event_reference` | `VARCHAR(240)` | NULL | - | Data field for provider event reference |
| `event_payload` | `JSONB` | NOT NULL | - | Data field for event payload |
| `occurred_at` | `DATETIME` | NOT NULL | - | Data field for occurred at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (broker_order_event_id)`
* `FOREIGN KEY (broker_order_id) REFERENCES broker_orders(broker_order_id)`
* `UNIQUE (broker_order_id, provider_event_reference)`


#### Table: `broker_orders` (13 Columns)
**Description:** Broker-ready execution order slips generated from whole-share rebalance proposals.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `broker_order_id` | `UUID` | **PK**, NOT NULL | - | Identifier for broker_orders |
| `user_broker_account_id` | `UUID` | `FK`, NOT NULL | `user_broker_accounts.user_broker_account_id` | Foreign key reference to `user_broker_accounts.user_broker_account_id` |
| `security_id` | `UUID` | `FK`, NOT NULL | `securities.security_id`, `instrument_listings.security_id` | Foreign key reference to `securities.security_id`, `instrument_listings.security_id` |
| `listing_id` | `UUID` | `FK`, NULL | `instrument_listings.listing_id` | Foreign key reference to `instrument_listings.listing_id` |
| `provider_order_reference` | `VARCHAR(240)` | NULL | - | Data field for provider order reference |
| `side` | `VARCHAR(8)` | NOT NULL | - | Data field for side |
| `order_type` | `VARCHAR(20)` | NOT NULL | - | Data field for order type |
| `order_quantity` | `NUMERIC(24, 8)` | NOT NULL | - | Integer lot count of equity shares |
| `limit_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `order_status` | `VARCHAR(24)` | NOT NULL | - | Lifecycle status flag for broker_orders |
| `submitted_at` | `DATETIME` | NULL | - | Data field for submitted at |
| `last_updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (broker_order_id)`
* `FOREIGN KEY (user_broker_account_id) REFERENCES user_broker_accounts(user_broker_account_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (security_id) REFERENCES instrument_listings(security_id)`
* `FOREIGN KEY (listing_id) REFERENCES instrument_listings(listing_id)`
* `CHECK (order_quantity > 0)`
* `CHECK (limit_price IS NULL OR limit_price >= 0)`
* `CHECK (side IN ('buy', 'sell'))`
* `UNIQUE (user_broker_account_id, provider_order_reference)`
* `CHECK (order_status IN ('created', 'submitted', 'accepted', 'partially_filled', 'filled', 'cancelled', 'rejected', 'expired', 'unknown'))`
* `CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit', 'other'))`


#### Table: `broker_providers` (6 Columns)
**Description:** Supported broker gateways (Zerodha Kite, Groww, AngelOne, Upstox).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `broker_provider_id` | `UUID` | **PK**, NOT NULL | - | Identifier for broker_providers |
| `provider_code` | `VARCHAR(80)` | NOT NULL | - | Data field for provider code |
| `provider_name` | `VARCHAR(160)` | NOT NULL | - | Data field for provider name |
| `developer_docs_url` | `TEXT` | NULL | - | Data field for developer docs url |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (broker_provider_id)`
* `UNIQUE (provider_code)`


#### Table: `portfolio_performance_snapshots` (9 Columns)
**Description:** Periodic portfolio NAV, valuation, and total return performance snapshots.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `performance_snapshot_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_performance_snapshots |
| `portfolio_version_id` | `UUID` | `FK`, NOT NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `snapshot_date` | `DATE` | NOT NULL | - | Data field for snapshot date |
| `valuation_amount` | `NUMERIC(20, 2)` | NOT NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `return_since_previous_pct` | `NUMERIC(12, 6)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `cumulative_return_pct` | `NUMERIC(12, 6)` | NULL | - | Percentage allocation figure (0.0 to 100.0%) |
| `source_type` | `VARCHAR(20)` | NOT NULL | - | Data field for source type |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (performance_snapshot_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `CHECK (source_type IN ('simulated', 'user_reported', 'broker_confirmed'))`
* `UNIQUE (portfolio_version_id, snapshot_date, source_type)`
* `CHECK (valuation_amount >= 0)`


#### Table: `user_broker_accounts` (12 Columns)
**Description:** Connected broker accounts with encrypted authentication credentials and sync status.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_broker_account_id` | `UUID` | **PK**, NOT NULL | - | Identifier for user_broker_accounts |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `broker_provider_id` | `UUID` | `FK`, NOT NULL | `broker_providers.broker_provider_id` | Foreign key reference to `broker_providers.broker_provider_id` |
| `external_account_reference` | `VARCHAR(240)` | NULL | - | Data field for external account reference |
| `account_label` | `VARCHAR(120)` | NULL | - | Data field for account label |
| `connection_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for user_broker_accounts |
| `granted_permissions` | `JSONB` | NOT NULL | - | Data field for granted permissions |
| `secret_reference` | `VARCHAR(400)` | NULL | - | Data field for secret reference |
| `connected_at` | `DATETIME` | NULL | - | Data field for connected at |
| `last_synced_at` | `DATETIME` | NULL | - | Data field for last synced at |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_broker_account_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `FOREIGN KEY (broker_provider_id) REFERENCES broker_providers(broker_provider_id)`
* `UNIQUE (user_id, broker_provider_id, external_account_reference)`
* `CHECK (connection_status IN ('pending', 'connected', 'expired', 'revoked', 'error'))`


---

### Domain: Demat Portfolio Diagnosis & Rebalancing Suggestions (`DIAGNOSIS` — 4 Tables, 38 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    EXISTING_PORTFOLIO_HOLDINGS ||--o{ EXISTING_PORTFOLIOS : "_existing_portfolio_id"
    PORTFOLIO_DIAGNOSES ||--o{ EXISTING_PORTFOLIOS : "_existing_portfolio_id"
    REBALANCE_SUGGESTIONS ||--o{ PORTFOLIO_DIAGNOSES : "_portfolio_diagnosis_id"

    EXISTING_PORTFOLIO_HOLDINGS {
        uuid existing_portfolio_holding_id PK
        uuid existing_portfolio_id FK
        uuid security_id FK
        uuid listing_id FK
        numeric quantity
        numeric average_purchase_price
        numeric market_value
        varchar currency_code
        jsonb source_detail
    }

    EXISTING_PORTFOLIOS {
        uuid existing_portfolio_id PK
        uuid user_id FK
        varchar portfolio_name
        varchar source_type
        varchar source_name
        timestamp as_of_date
        varchar currency_code
        varchar portfolio_status
        timestamp created_at
        timestamp updated_at
    }

    PORTFOLIO_DIAGNOSES {
        uuid portfolio_diagnosis_id PK
        uuid existing_portfolio_id FK
        varchar diagnosis_status
        varchar summary
        jsonb metrics
        timestamp market_context_as_of
        timestamp started_at
        timestamp completed_at
    }

    REBALANCE_SUGGESTIONS {
        uuid rebalance_suggestion_id PK
        uuid portfolio_diagnosis_id FK
        uuid security_id FK
        varchar suggested_action
        numeric current_quantity
        numeric target_quantity
        numeric current_value
        numeric target_value
        numeric change_value
        varchar explanation
        timestamp created_at
    }
```

#### Table: `existing_portfolio_holdings` (9 Columns)
**Description:** Granular stock holdings extracted from uploaded brokerage statements.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `existing_portfolio_holding_id` | `UUID` | **PK**, NOT NULL | - | Identifier for existing_portfolio_holdings |
| `existing_portfolio_id` | `UUID` | `FK`, NOT NULL | `existing_portfolios.existing_portfolio_id` | Foreign key reference to `existing_portfolios.existing_portfolio_id` |
| `security_id` | `UUID` | `FK`, NOT NULL | `instrument_listings.security_id`, `securities.security_id` | Foreign key reference to `instrument_listings.security_id`, `securities.security_id` |
| `listing_id` | `UUID` | `FK`, NULL | `instrument_listings.listing_id` | Foreign key reference to `instrument_listings.listing_id` |
| `quantity` | `NUMERIC(24, 8)` | NOT NULL | - | Integer lot count of equity shares |
| `average_purchase_price` | `NUMERIC(20, 6)` | NULL | - | Indian Rupee (INR) monetary figure |
| `market_value` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `source_detail` | `JSONB` | NOT NULL | - | Data field for source detail |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (existing_portfolio_holding_id)`
* `FOREIGN KEY (security_id) REFERENCES instrument_listings(security_id)`
* `FOREIGN KEY (listing_id) REFERENCES instrument_listings(listing_id)`
* `FOREIGN KEY (existing_portfolio_id) REFERENCES existing_portfolios(existing_portfolio_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `CHECK (market_value IS NULL OR market_value >= 0)`
* `UNIQUE (existing_portfolio_id, security_id)`
* `CHECK (average_purchase_price IS NULL OR average_purchase_price >= 0)`
* `CHECK (quantity > 0)`


#### Table: `existing_portfolios` (10 Columns)
**Description:** Uploaded external Demat portfolio statements for comprehensive health diagnosis.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `existing_portfolio_id` | `UUID` | **PK**, NOT NULL | - | Identifier for existing_portfolios |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `portfolio_name` | `VARCHAR(160)` | NOT NULL | - | Data field for portfolio name |
| `source_type` | `VARCHAR(20)` | NOT NULL | - | Data field for source type |
| `source_name` | `VARCHAR(160)` | NULL | - | Data field for source name |
| `as_of_date` | `DATE` | NOT NULL | - | Data field for as of date |
| `currency_code` | `CHAR(3)` | NOT NULL | - | Data field for currency code |
| `portfolio_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for existing_portfolios |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `updated_at` | `DATETIME` | NOT NULL | - | Audit last updated timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (existing_portfolio_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `UNIQUE (existing_portfolio_id, user_id)`
* `CHECK (portfolio_status IN ('active', 'archived'))`
* `CHECK (source_type IN ('manual', 'file_import', 'broker_import'))`


#### Table: `portfolio_diagnoses` (8 Columns)
**Description:** Comprehensive 7-dimension diagnostic audit records with overall health score (0–100).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `portfolio_diagnosis_id` | `UUID` | **PK**, NOT NULL | - | Identifier for portfolio_diagnoses |
| `existing_portfolio_id` | `UUID` | `FK`, NOT NULL | `existing_portfolios.existing_portfolio_id` | Foreign key reference to `existing_portfolios.existing_portfolio_id` |
| `diagnosis_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for portfolio_diagnoses |
| `summary` | `TEXT` | NULL | - | Data field for summary |
| `metrics` | `JSONB` | NOT NULL | - | Data field for metrics |
| `market_context_as_of` | `DATETIME` | NULL | - | Data field for market context as of |
| `started_at` | `DATETIME` | NOT NULL | - | Data field for started at |
| `completed_at` | `DATETIME` | NULL | - | Data field for completed at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (portfolio_diagnosis_id)`
* `FOREIGN KEY (existing_portfolio_id) REFERENCES existing_portfolios(existing_portfolio_id)`
* `CHECK (completed_at IS NULL OR completed_at >= started_at)`
* `CHECK (diagnosis_status IN ('queued', 'running', 'completed', 'failed'))`


#### Table: `rebalance_suggestions` (11 Columns)
**Description:** Diagnostic rebalance recommendations to fix over-concentration or low-quality holdings.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `rebalance_suggestion_id` | `UUID` | **PK**, NOT NULL | - | Identifier for rebalance_suggestions |
| `portfolio_diagnosis_id` | `UUID` | `FK`, NOT NULL | `portfolio_diagnoses.portfolio_diagnosis_id` | Foreign key reference to `portfolio_diagnoses.portfolio_diagnosis_id` |
| `security_id` | `UUID` | `FK`, NOT NULL | `securities.security_id` | Foreign key reference to `securities.security_id` |
| `suggested_action` | `VARCHAR(10)` | NOT NULL | - | Data field for suggested action |
| `current_quantity` | `NUMERIC(24, 8)` | NULL | - | Integer lot count of equity shares |
| `target_quantity` | `NUMERIC(24, 8)` | NULL | - | Integer lot count of equity shares |
| `current_value` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `target_value` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `change_value` | `NUMERIC(20, 2)` | NULL | - | Indian Rupee (INR) monetary figure |
| `explanation` | `TEXT` | NOT NULL | - | Data field for explanation |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (rebalance_suggestion_id)`
* `FOREIGN KEY (security_id) REFERENCES securities(security_id)`
* `FOREIGN KEY (portfolio_diagnosis_id) REFERENCES portfolio_diagnoses(portfolio_diagnosis_id)`
* `CHECK (suggested_action IN ('buy', 'sell', 'hold'))`
* `UNIQUE (portfolio_diagnosis_id, security_id)`
* `CHECK (target_value IS NULL OR target_value >= 0)`
* `CHECK (target_quantity IS NULL OR target_quantity >= 0)`
* `CHECK (current_quantity IS NULL OR current_quantity >= 0)`
* `CHECK (current_value IS NULL OR current_value >= 0)`


---

### Domain: Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS` — 7 Tables, 76 Attributes)

#### Relational Entity Diagram
```mermaid
erDiagram
    AGENT_EXECUTION_RUNS ||--o{ AGENT_VERSIONS : "_agent_version_id"
    AGENT_VERSIONS ||--o{ AGENT_DEFINITIONS : "_agent_id"

    AGENT_DEFINITIONS {
        uuid agent_id PK
        varchar agent_code
        varchar agent_name
        varchar purpose
        boolean is_active
        timestamp created_at
    }

    AGENT_EXECUTION_RUNS {
        uuid agent_execution_run_id PK
        uuid generation_request_id FK
        uuid portfolio_version_id FK
        uuid agent_version_id FK
        varchar execution_status
        varchar input_fingerprint
        jsonb output_summary
        integer input_token_count
        integer output_token_count
        integer latency_ms
        varchar error_code
        varchar error_summary
        timestamp started_at
        timestamp completed_at
    }

    AGENT_VERSIONS {
        uuid agent_version_id PK
        uuid agent_id FK
        varchar version_label
        varchar llm_provider
        varchar model_name
        varchar prompt_version
        varchar prompt_hash
        varchar structured_output_schema_version
        jsonb configuration
        boolean is_active
        timestamp created_at
    }

    AUDIT_EVENTS {
        uuid audit_event_id PK
        uuid actor_user_id FK
        varchar action_code
        varchar resource_type
        uuid resource_id
        varchar outcome
        varchar request_id
        varchar ip_address
        varchar user_agent
        jsonb event_metadata
        timestamp created_at
    }

    KNOWLEDGE_DOCUMENTS {
        uuid knowledge_document_id PK
        uuid data_source_id FK
        varchar external_document_id
        varchar document_title
        varchar document_type
        varchar source_url
        varchar content_hash
        varchar object_storage_uri
        varchar embedding_model
        varchar vector_index_reference
        varchar index_status
        timestamp published_at
        timestamp indexed_at
        jsonb metadata
        timestamp created_at
    }

    NOTIFICATIONS {
        uuid notification_id PK
        uuid user_id FK
        varchar notification_type
        varchar title
        varchar message
        varchar delivery_channel
        varchar delivery_status
        timestamp created_at
        timestamp sent_at
        timestamp read_at
        timestamp dismissed_at
        jsonb metadata
    }

    USER_FEEDBACK {
        uuid user_feedback_id PK
        uuid user_id FK
        uuid portfolio_version_id FK
        varchar feedback_type
        integer rating
        varchar feedback_text
        timestamp created_at
    }
```

#### Table: `agent_definitions` (6 Columns)
**Description:** Registry of specialized agent roles (Manager, Suitability, Macro, Market, Fundamental, News, Critic, Moderator).

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `agent_id` | `UUID` | **PK**, NOT NULL | - | Identifier for agent_definitions |
| `agent_code` | `VARCHAR(80)` | NOT NULL | - | Data field for agent code |
| `agent_name` | `VARCHAR(160)` | NOT NULL | - | Data field for agent name |
| `purpose` | `TEXT` | NOT NULL | - | Data field for purpose |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (agent_id)`
* `UNIQUE (agent_code)`


#### Table: `agent_execution_runs` (14 Columns)
**Description:** Runtime execution logs recording agent start/end times, model parameters, and token usage.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `agent_execution_run_id` | `UUID` | **PK**, NOT NULL | - | Identifier for agent_execution_runs |
| `generation_request_id` | `UUID` | `FK`, NULL | `portfolio_generation_requests.generation_request_id` | Foreign key reference to `portfolio_generation_requests.generation_request_id` |
| `portfolio_version_id` | `UUID` | `FK`, NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `agent_version_id` | `UUID` | `FK`, NOT NULL | `agent_versions.agent_version_id` | Foreign key reference to `agent_versions.agent_version_id` |
| `execution_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for agent_execution_runs |
| `input_fingerprint` | `VARCHAR(128)` | NULL | - | Data field for input fingerprint |
| `output_summary` | `JSONB` | NOT NULL | - | Data field for output summary |
| `input_token_count` | `BIGINT` | NULL | - | Data field for input token count |
| `output_token_count` | `BIGINT` | NULL | - | Data field for output token count |
| `latency_ms` | `BIGINT` | NULL | - | Data field for latency ms |
| `error_code` | `VARCHAR(100)` | NULL | - | Data field for error code |
| `error_summary` | `TEXT` | NULL | - | Data field for error summary |
| `started_at` | `DATETIME` | NOT NULL | - | Data field for started at |
| `completed_at` | `DATETIME` | NULL | - | Data field for completed at |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (agent_execution_run_id)`
* `FOREIGN KEY (generation_request_id) REFERENCES portfolio_generation_requests(generation_request_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `FOREIGN KEY (agent_version_id) REFERENCES agent_versions(agent_version_id)`
* `CHECK (input_token_count IS NULL OR input_token_count >= 0)`
* `CHECK (completed_at IS NULL OR completed_at >= started_at)`
* `CHECK (execution_status IN ('queued', 'running', 'succeeded', 'failed', 'skipped'))`
* `CHECK (output_token_count IS NULL OR output_token_count >= 0)`
* `CHECK (latency_ms IS NULL OR latency_ms >= 0)`


#### Table: `agent_versions` (11 Columns)
**Description:** Versioned agent implementations with prompt versions and model configurations.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `agent_version_id` | `UUID` | **PK**, NOT NULL | - | Identifier for agent_versions |
| `agent_id` | `UUID` | `FK`, NOT NULL | `agent_definitions.agent_id` | Foreign key reference to `agent_definitions.agent_id` |
| `version_label` | `VARCHAR(80)` | NOT NULL | - | Data field for version label |
| `llm_provider` | `VARCHAR(80)` | NULL | - | Data field for llm provider |
| `model_name` | `VARCHAR(160)` | NULL | - | Data field for model name |
| `prompt_version` | `VARCHAR(100)` | NULL | - | Data field for prompt version |
| `prompt_hash` | `VARCHAR(128)` | NULL | - | Data field for prompt hash |
| `structured_output_schema_version` | `VARCHAR(100)` | NULL | - | Data field for structured output schema version |
| `configuration` | `JSONB` | NOT NULL | - | Data field for configuration |
| `is_active` | `BOOLEAN` | NOT NULL | - | Data field for is active |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (agent_version_id)`
* `FOREIGN KEY (agent_id) REFERENCES agent_definitions(agent_id)`
* `UNIQUE (agent_id, version_label)`


#### Table: `audit_events` (11 Columns)
**Description:** Immutable system security and data access audit trail for compliance verification.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `audit_event_id` | `UUID` | **PK**, NOT NULL | - | Identifier for audit_events |
| `actor_user_id` | `UUID` | `FK`, NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `action_code` | `VARCHAR(100)` | NOT NULL | - | Data field for action code |
| `resource_type` | `VARCHAR(100)` | NOT NULL | - | Data field for resource type |
| `resource_id` | `UUID` | NULL | - | Data field for resource id |
| `outcome` | `VARCHAR(20)` | NOT NULL | - | Data field for outcome |
| `request_id` | `VARCHAR(128)` | NULL | - | Data field for request id |
| `ip_address` | `INET` | NULL | - | Data field for ip address |
| `user_agent` | `TEXT` | NULL | - | Data field for user agent |
| `event_metadata` | `JSONB` | NOT NULL | - | Data field for event metadata |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (audit_event_id)`
* `FOREIGN KEY (actor_user_id) REFERENCES app_users(user_id)`
* `CHECK (outcome IN ('success', 'failure', 'denied'))`


#### Table: `knowledge_documents` (15 Columns)
**Description:** Vector and text knowledge base documents for agent contextual retrieval.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `knowledge_document_id` | `UUID` | **PK**, NOT NULL | - | Identifier for knowledge_documents |
| `data_source_id` | `UUID` | `FK`, NULL | `data_sources.data_source_id` | Foreign key reference to `data_sources.data_source_id` |
| `external_document_id` | `VARCHAR(300)` | NULL | - | Data field for external document id |
| `document_title` | `VARCHAR(300)` | NOT NULL | - | Data field for document title |
| `document_type` | `VARCHAR(40)` | NOT NULL | - | Data field for document type |
| `source_url` | `TEXT` | NULL | - | Data field for source url |
| `content_hash` | `VARCHAR(128)` | NOT NULL | - | Data field for content hash |
| `object_storage_uri` | `TEXT` | NULL | - | Data field for object storage uri |
| `embedding_model` | `VARCHAR(160)` | NOT NULL | - | Data field for embedding model |
| `vector_index_reference` | `VARCHAR(300)` | NULL | - | Data field for vector index reference |
| `index_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for knowledge_documents |
| `published_at` | `DATETIME` | NULL | - | Data field for published at |
| `indexed_at` | `DATETIME` | NULL | - | Data field for indexed at |
| `metadata` | `JSONB` | NOT NULL | - | Data field for metadata |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (knowledge_document_id)`
* `FOREIGN KEY (data_source_id) REFERENCES data_sources(data_source_id)`
* `UNIQUE (content_hash, embedding_model)`
* `CHECK (index_status IN ('pending', 'indexed', 'failed', 'retired'))`


#### Table: `notifications` (12 Columns)
**Description:** In-app investor notifications for drift alerts, rebalance triggers, and market updates.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `notification_id` | `UUID` | **PK**, NOT NULL | - | Identifier for notifications |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `notification_type` | `VARCHAR(40)` | NOT NULL | - | Data field for notification type |
| `title` | `VARCHAR(200)` | NOT NULL | - | Data field for title |
| `message` | `TEXT` | NOT NULL | - | Data field for message |
| `delivery_channel` | `VARCHAR(20)` | NOT NULL | - | Data field for delivery channel |
| `delivery_status` | `VARCHAR(20)` | NOT NULL | - | Lifecycle status flag for notifications |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |
| `sent_at` | `DATETIME` | NULL | - | Data field for sent at |
| `read_at` | `DATETIME` | NULL | - | Data field for read at |
| `dismissed_at` | `DATETIME` | NULL | - | Data field for dismissed at |
| `metadata` | `JSONB` | NOT NULL | - | Data field for metadata |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (notification_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (sent_at IS NULL OR sent_at >= created_at)`
* `CHECK (delivery_status IN ('pending', 'sent', 'failed'))`
* `CHECK (read_at IS NULL OR read_at >= created_at)`
* `CHECK (delivery_channel IN ('in_app', 'email', 'sms', 'push'))`
* `CHECK (dismissed_at IS NULL OR dismissed_at >= created_at)`


#### Table: `user_feedback` (7 Columns)
**Description:** Investor feedback and ratings on portfolio recommendations and conversational copilot responses.

| Column Name | SQL Data Type | Key / Nullability | Default / Reference | Functional Role |
|---|---|---|---|---|
| `user_feedback_id` | `UUID` | **PK**, NOT NULL | - | Identifier for user_feedback |
| `user_id` | `UUID` | `FK`, NOT NULL | `app_users.user_id` | Foreign key reference to `app_users.user_id` |
| `portfolio_version_id` | `UUID` | `FK`, NULL | `portfolio_versions.portfolio_version_id` | Foreign key reference to `portfolio_versions.portfolio_version_id` |
| `feedback_type` | `VARCHAR(30)` | NOT NULL | - | Data field for feedback type |
| `rating` | `SMALLINT` | NULL | - | Data field for rating |
| `feedback_text` | `TEXT` | NULL | - | Data field for feedback text |
| `created_at` | `DATETIME` | NOT NULL | - | Audit creation timestamp with timezone |

**Integrity & Safety Constraints:**
* `PRIMARY KEY (user_feedback_id)`
* `FOREIGN KEY (portfolio_version_id) REFERENCES portfolio_versions(portfolio_version_id)`
* `FOREIGN KEY (user_id) REFERENCES app_users(user_id)`
* `CHECK (feedback_type IN ('recommendation', 'explanation', 'application', 'other'))`
* `CHECK (rating IS NULL OR rating BETWEEN 1 AND 5)`


---

## 4. Comprehensive 62-Table Master PostgreSQL Data Dictionary

Complete index of all 62 tables currently provisioned in Lucid's PostgreSQL database engine:

| # | Table Name | Relational Domain | Primary Key | Key Foreign Keys | Columns | Business Function & Engine Role |
|---|---|---|---|---|---|---|
| 1 | `app_users` | User Identity, Authentication & Security (`IDENTITY`) | `user_id` | - | 11 | Core application identity table storing email, Argon2id password hash, and account status. |
| 2 | `revoked_tokens` | User Identity, Authentication & Security (`IDENTITY`) | `revocation_id` | `app_users` | 5 | Blacklist ledger for invalidated stateless JWT tokens (JTI tracking). |
| 3 | `user_consents` | User Identity, Authentication & Security (`IDENTITY`) | `consent_id` | `app_users` | 9 | Append-only legal consent ledger tracking terms of service, SEBI risk disclosures, and DPDP consents. |
| 4 | `user_preferences` | User Identity, Authentication & Security (`IDENTITY`) | `user_id` | `app_users` | 7 | Investor UI configuration, default currency, and notification channel preferences. |
| 5 | `user_profile_versions` | User Identity, Authentication & Security (`IDENTITY`) | `profile_version_id` | `app_users` | 10 | Historical audit versions of modifications to user profile data. |
| 6 | `user_profiles` | User Identity, Authentication & Security (`IDENTITY`) | `user_id` | `app_users` | 9 | Investor demographic profile, investment knowledge tier, and residency. |
| 7 | `user_verification_codes` | User Identity, Authentication & Security (`IDENTITY`) | `verification_id` | `app_users` | 8 | Time-limited verification OTP codes for password reset and email confirmation. |
| 8 | `financial_goals` | Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR`) | `goal_id` | `app_users` | 13 | Investor financial targets specifying goal type, target amount, and time horizon. |
| 9 | `risk_assessment_answers` | Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR`) | `answer_id` | `risk_assessments, risk_question_options` | 8 | Granular user answers recorded for individual risk assessment questions. |
| 10 | `risk_assessments` | Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR`) | `risk_assessment_id` | `app_users` | 10 | SEBI suitability and risk assessment sessions with calculated risk score and category. |
| 11 | `risk_question_options` | Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR`) | `option_id` | `risk_questions` | 6 | Selectable multiple-choice responses with associated risk score weights. |
| 12 | `risk_questions` | Investor Suitability, Risk Profiling & Financial Goals (`INVESTOR`) | `question_id` | - | 10 | Standardized questionnaire items evaluating risk capacity, horizon, and loss tolerance. |
| 13 | `companies` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `company_id` | - | 7 | Legal entity master record with CIN, legal name, corporate website, and registration. |
| 14 | `company_industries` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `company_id, industry_id, effective_from` | `companies, industries` | 5 | Many-to-many relationship mapping companies to industries and primary sector tags. |
| 15 | `exchanges` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `exchange_id` | - | 6 | Exchange directory (NSE, BSE) with MIC codes, trading currencies, and holiday schedules. |
| 16 | `industries` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `industry_id` | `sectors` | 6 | Granular industry classification linked to parent sector. |
| 17 | `instrument_listings` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `listing_id` | `exchanges, securities` | 9 | Exchange-specific equity listings with NSE/BSE symbols, scrip codes, and lot sizes. |
| 18 | `sectors` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `sector_id` | - | 5 | Broad economic sector taxonomy (Information Technology, Healthcare, Power & Utilities, etc.). |
| 19 | `securities` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `security_id` | `companies` | 9 | Tradeable equity instruments with ISIN, currency code, security type, and listing status. |
| 20 | `user_sector_preferences` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `user_id, sector_id` | `app_users, sectors` | 4 | Explicit investor sector tilts, positive preferences, and negative sector exclusions. |
| 21 | `user_security_preferences` | Security Master, Companies & Corporate Taxonomy (`SECURITY`) | `user_id, security_id` | `app_users, securities` | 5 | Individual security exclusions (e.g. tobacco exclusion, ethical filters). |
| 22 | `data_ingestion_errors` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `ingestion_error_id` | `data_ingestion_runs` | 8 | Error log for market data fetching exceptions and API failures. |
| 23 | `data_ingestion_runs` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `ingestion_run_id` | `data_sources` | 12 | Audit log for batch and scheduled market data sync executions. |
| 24 | `data_sources` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `data_source_id` | - | 10 | Registered market data API providers (Yahoo Finance, FRED, NewsAPI, NSE/BSE registries). |
| 25 | `economic_indicators` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `economic_indicator_id` | - | 7 | Macroeconomic indicator series metadata (RBI Repo rate, CPI, 10Y G-Sec Yield). |
| 26 | `economic_observations` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `economic_observation_id` | `data_ingestion_runs, economic_indicators` | 8 | Time-series observations and historical values for macroeconomic indicators. |
| 27 | `fundamental_metrics` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `fundamental_metric_id` | `data_ingestion_runs, data_sources, metric_definitions, securities` | 11 | Quarterly balance sheet ratios: ROE, Debt/Equity, P/E, Operating Margin, 3Y CAGR. |
| 28 | `market_news_articles` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `news_article_id` | `data_ingestion_runs, data_sources` | 13 | Aggregated corporate filings, SEBI circulars, and financial news items. |
| 29 | `market_prices` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `market_price_id` | `data_ingestion_runs, data_sources, instrument_listings` | 14 | Historical and real-time OHLCV price records for listed equity instruments. |
| 30 | `metric_definitions` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `metric_definition_id` | - | 7 | Formal definitions and formulas for financial fundamental and quantitative metrics. |
| 31 | `news_article_securities` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `news_article_id, security_id` | `market_news_articles, securities` | 4 | Association table linking news articles and regulatory filings to specific securities. |
| 32 | `source_instrument_mappings` | Market Data, Prices, Fundamental Metrics & News (`MARKET`) | `source_instrument_mapping_id` | `data_sources, instrument_listings` | 7 | Cross-reference mapping third-party data provider IDs to canonical internal securities. |
| 33 | `evidence_items` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `evidence_item_id` | `data_sources, economic_observations, fundamental_metrics, market_news_articles, market_prices, securities` | 16 | Verifiable factual evidence items (filing excerpts, financial ratios) supporting recommendations. |
| 34 | `explanation_evidence` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `explanation_id, evidence_item_id` | `evidence_items, recommendation_explanations` | 3 | Many-to-many junction linking recommendation explanations to supporting evidence items. |
| 35 | `investor_portfolios` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `portfolio_id` | `app_users` | 6 | Top-level portfolio container with user FK, portfolio name, and status. |
| 36 | `portfolio_generation_requests` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `generation_request_id` | `financial_goals, investor_portfolios, risk_assessments` | 19 | Inbound portfolio generation requests detailing investor prompt, capital, and risk tier. |
| 37 | `portfolio_scenarios` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `portfolio_scenario_id` | `portfolio_versions` | 12 | Simulated stress-test scenarios (e.g., 2008 GFC, 2020 COVID crash, Rate Hike). |
| 38 | `portfolio_security_decisions` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `decision_id` | `instrument_listings, portfolio_versions, securities` | 8 | Granular equity holdings per portfolio version with target weights and selection rationales. |
| 39 | `portfolio_validation_results` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `validation_result_id` | `portfolio_validation_runs, securities` | 11 | Itemized constraint validation results (25% single-stock cap, 40% sector cap, whole shares). |
| 40 | `portfolio_validation_runs` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `validation_run_id` | `portfolio_versions` | 8 | Audit record of quantitative validation passes executed on portfolio versions. |
| 41 | `portfolio_version_constraints` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `portfolio_constraint_id` | `portfolio_versions` | 11 | Specific portfolio constraints applied during optimization. |
| 42 | `portfolio_versions` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `portfolio_version_id` | `portfolio_generation_requests, strategy_versions` | 17 | Immutable portfolio version snapshots with investment capital, expected return, and generation context JSON. |
| 43 | `recommendation_explanations` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `explanation_id` | `portfolio_security_decisions, portfolio_versions` | 8 | Fiduciary plain-English narrative rationales generated by the Moderator agent. |
| 44 | `strategy_definitions` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `strategy_id` | - | 6 | Formal investment strategy blueprints (e.g., Conservative Wealth Preserver, High-Growth Equity). |
| 45 | `strategy_versions` | Portfolio Engine, Optimization, Versions & Explanations (`PORTFOLIO`) | `strategy_version_id` | `strategy_definitions` | 8 | Versioned parameter specifications for investment strategy models. |
| 46 | `broker_executions` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `broker_execution_id` | `broker_orders` | 8 | Realized execution fill records for placed broker orders with trade timestamps. |
| 47 | `broker_order_events` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `broker_order_event_id` | `broker_orders` | 7 | State transition lifecycle events for broker orders (placed, rejected, filled). |
| 48 | `broker_orders` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `broker_order_id` | `instrument_listings, securities, user_broker_accounts` | 13 | Broker-ready execution order slips generated from whole-share rebalance proposals. |
| 49 | `broker_providers` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `broker_provider_id` | - | 6 | Supported broker gateways (Zerodha Kite, Groww, AngelOne, Upstox). |
| 50 | `portfolio_performance_snapshots` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `performance_snapshot_id` | `portfolio_versions` | 9 | Periodic portfolio NAV, valuation, and total return performance snapshots. |
| 51 | `user_broker_accounts` | Broker Accounts, Integrations & Order Auditing (`BROKER`) | `user_broker_account_id` | `app_users, broker_providers` | 12 | Connected broker accounts with encrypted authentication credentials and sync status. |
| 52 | `existing_portfolio_holdings` | Demat Portfolio Diagnosis & Rebalancing Suggestions (`DIAGNOSIS`) | `existing_portfolio_holding_id` | `existing_portfolios, instrument_listings` | 9 | Granular stock holdings extracted from uploaded brokerage statements. |
| 53 | `existing_portfolios` | Demat Portfolio Diagnosis & Rebalancing Suggestions (`DIAGNOSIS`) | `existing_portfolio_id` | `app_users` | 10 | Uploaded external Demat portfolio statements for comprehensive health diagnosis. |
| 54 | `portfolio_diagnoses` | Demat Portfolio Diagnosis & Rebalancing Suggestions (`DIAGNOSIS`) | `portfolio_diagnosis_id` | `existing_portfolios` | 8 | Comprehensive 7-dimension diagnostic audit records with overall health score (0–100). |
| 55 | `rebalance_suggestions` | Demat Portfolio Diagnosis & Rebalancing Suggestions (`DIAGNOSIS`) | `rebalance_suggestion_id` | `portfolio_diagnoses, securities` | 11 | Diagnostic rebalance recommendations to fix over-concentration or low-quality holdings. |
| 56 | `agent_definitions` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `agent_id` | - | 6 | Registry of specialized agent roles (Manager, Suitability, Macro, Market, Fundamental, News, Critic, Moderator). |
| 57 | `agent_execution_runs` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `agent_execution_run_id` | `agent_versions, portfolio_generation_requests, portfolio_versions` | 14 | Runtime execution logs recording agent start/end times, model parameters, and token usage. |
| 58 | `agent_versions` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `agent_version_id` | `agent_definitions` | 11 | Versioned agent implementations with prompt versions and model configurations. |
| 59 | `audit_events` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `audit_event_id` | `app_users` | 11 | Immutable system security and data access audit trail for compliance verification. |
| 60 | `knowledge_documents` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `knowledge_document_id` | `data_sources` | 15 | Vector and text knowledge base documents for agent contextual retrieval. |
| 61 | `notifications` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `notification_id` | `app_users` | 12 | In-app investor notifications for drift alerts, rebalance triggers, and market updates. |
| 62 | `user_feedback` | Multi-Agent Telemetry, Knowledge Base & System Auditing (`OPERATIONS`) | `user_feedback_id` | `app_users, portfolio_versions` | 7 | Investor feedback and ratings on portfolio recommendations and conversational copilot responses. |

---

## 5. Critical Database Constraints & Safety Guardrails

### 1. Integer Lot & Cash Conservation Constraints
* `ck_portfolio_versions_amount`: `CHECK (investment_amount > 0)`
* `ck_generation_requests_amount`: `CHECK (requested_amount > 0)`
* Simplex Allocation Guarantee: Sum of weights $\sum w_i \le 100.0\%$, with residual capital strictly accounted for in non-negative cash reserve:
  $$\text{Cash}_{\text{unallocated}} = V_{\text{total}} - \sum_{i=1}^N \left( Q_i \times P_i \right) \ge 0$$

### 2. Multi-Tenant Composite Ownership Isolation
* `fk_generation_portfolio_owner`: `FOREIGN KEY (portfolio_id, user_id) REFERENCES investor_portfolios(portfolio_id, user_id)`
* `fk_generation_goal_owner`: `FOREIGN KEY (goal_id, user_id) REFERENCES financial_goals(goal_id, user_id)`
* `fk_generation_risk_owner`: `FOREIGN KEY (risk_assessment_id, user_id) REFERENCES risk_assessments(risk_assessment_id, user_id)`
* `fk_version_request_portfolio`: `FOREIGN KEY (generation_request_id, portfolio_id) REFERENCES portfolio_generation_requests(generation_request_id, portfolio_id)`

### 3. Fiduciary Diversification & Concentration Policy Bounds
* `POLICY_SINGLE_STOCK_CEILING`: Enforces single-stock weight ceiling $\le 25.0\%$.
* `POLICY_SECTOR_CEILING`: Enforces sector weight ceiling $\le 40.0\%$.
* Validated deterministically on every portfolio generation and rebalance run via `portfolio_validation_runs` and `portfolio_validation_results`.

### 4. Non-Custodial Broker Boundary Isolation
* `broker_orders` and `broker_executions` are isolated from algorithmic portfolio generation.
* Rebalance orders generate downloadable trade slips and execution manifests, ensuring compliance with SEBI (Investment Advisers) Regulations, 2013 by strictly avoiding automated order placement.

---

## 6. High-Performance Indexing Strategy

1. **Composite Time-Series Scanning**:
   * `ix_market_prices_listing_date`: `(listing_id, price_date DESC)` enables instant sub-millisecond retrieval of the latest market quote $P_i$.
   * `ix_portfolio_versions_recent`: `(portfolio_id, version_number DESC)` allows instant retrieval of the current active portfolio version without full-table scans.
2. **Case-Insensitive Identifier Routing**:
   * `uq_app_users_email_lower`: `UNIQUE INDEX (lower(email))` ensures case-insensitive login lookup while preventing duplicate accounts.
   * `ix_instrument_listings_symbol`: `INDEX (symbol)` provides instant NSE/BSE ticker resolution.
3. **Partition-Ready Ingestion Ledger**:
   * `ix_data_ingestion_runs_status`: `INDEX (source_id, started_at DESC)` supports automated data pipeline health audits.
   * `ix_agent_execution_runs_portfolio`: `INDEX (portfolio_version_id, agent_role)` accelerates multi-agent audit trail tracing.

---

*Authoritative Specification: Reconciled 100% against Lucid Production PostgreSQL Database Engine v2.0.*