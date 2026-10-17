# Unified Database-Design Specification
## Intelligent Portfolio Creation Application for Indian Retail Investors

**Implementation target:** Python + FastAPI + LangGraph + PostgreSQL  
**Supporting components:** SQLAlchemy for persistence, Alembic for schema migrations, optional Neo4j for graph relationships, optional FAISS for document similarity search, and an external identity provider such as Amazon Cognito.

## 1. Objective

Design a complete, internally consistent, normalized relational database for an application that helps Indian retail investors understand their investor profile and receive personalized, explainable, context-aware, mathematically validated portfolio recommendations.

This specification is exclusively about **database design**: entities, attributes, data types, primary keys, foreign keys, candidate keys, constraints, cardinalities, optionality, normalization, data history, diagrams and executable PostgreSQL DDL. Do not substitute an application architecture, component diagram, cloud deployment design, or API catalogue for the database schema.

## 2. Confirmed product capabilities and assumptions

The core scope should support:

- User identity mapping, profiles, preferences and consent history.
- Investor onboarding, experience/knowledge level, financial goals, investment horizon and amount.
- Risk questionnaire versions, individual answers, assessment attempts, risk scores and risk categories.
- Inclusion/exclusion preferences for sectors and securities.
- Canonical companies, securities, exchanges, exchange-specific listings, normalized sector/industry taxonomy, and company-to-industry mappings.
- Historical market prices, company/instrument fundamentals, economic indicators and relevant news.
- Data-provider metadata, provider-specific security/listing mappings, data-ingestion runs and per-run errors, timestamps, provenance, and provider/source consistency checks.
- Portfolio generation requests and normalized request/input snapshots.
- Logical portfolios, immutable/versioned portfolio outputs, selected/excluded/watchlist decisions and target weights.
- Strategy/optimizer version references and applied portfolio constraints.
- Evidence-linked, user-facing explanations; deterministic validation runs and rule-level results.
- Scenario/stress-test results and diagnosis/rebalancing previews for existing user-reported or imported holdings.
- Agent/model/prompt version metadata and execution status/latency/structured summaries.
- Application audit events, feedback, notifications and optional document-index metadata.

The following are **optional or future features**, not assumed to exist in the first prototype:

- Broker authentication, account synchronization, buy/sell orders, executions and reconciliations.
- Portfolio performance tracking based on live broker-confirmed values.
- Payment processing, subscriptions, tax-lot accounting, automated trade execution, and full regulated-advice record workflows.
- A dedicated Neo4j knowledge graph, TimescaleDB, or another time-series infrastructure. Add only after requirements and data volumes justify them.

## 3. Architectural data boundaries

1. PostgreSQL is the system of record for application entities and normalized structured data.
2. FastAPI is responsible for persistence orchestration, validation, authorization and transaction boundaries; SQLAlchemy models and Alembic migrations should match the DDL.
3. LangGraph coordinates AI steps. Persist agent/model/prompt versions, execution status, useful structured output, timings, errors, explanations and evidence—not hidden internal chain-of-thought.
4. Python/NumPy/Pandas/SciPy calculate portfolio weights and risk metrics deterministically. A model-generated allocation is not trusted until deterministic validation passes.
5. The database stores recommendations separately from existing owned holdings, submitted orders and completed executions. A recommendation is not proof of a purchase.
6. Secrets, passwords, broker tokens and raw API keys must not be stored in ordinary relational columns. Store only references to a secret manager when needed.
7. Use JSONB only for genuinely flexible/versioned snapshots, model configuration, audit metadata and variable structured outputs. Do not use JSONB as a replacement for normal entity relationships.
8. Preserve earlier recommendations and the context needed to interpret them. A selective investor/input snapshot and source/version references are justified for reproducibility; do not duplicate the entire market database for every recommendation.
9. Sensitive information should be minimized. Database structure alone does not make the service legally or regulatorily compliant.

## 4. Entity-design requirements

For every table, provide:

- Table name, module, purpose and reason for a separate table.
- Every column and its PostgreSQL type.
- Primary key, foreign keys and exact referenced columns.
- Candidate keys and unique constraints.
- Nullability, defaults, check constraints and validation rules.
- Indexes and the query paths they support.
- Created/updated/effective/retrieved timestamps where meaningful.
- Example value or record for key fields.
- Relationship cardinality, optionality and `ON DELETE` / `ON UPDATE` behaviour.

Use consistent descriptive names. Use UUID identifiers consistently for the proposed implementation and composite primary keys for true junction tables where the relationship itself is the identity. Where composite foreign keys are used to validate that a referenced goal or risk assessment belongs to the same user, document the ownership benefit.

## 5. Required modules and entities to evaluate

### A. User and preferences

Evaluate user identity mappings, profile, preferences, consent history and account lifecycle. Credentials belong to the identity provider. Include only personal data needed by the application.

### B. Goals and risk assessment

Separate financial goals from assessment attempts. Version questionnaire questions/options so old answers remain interpretable. Store one answer per assessment/question. Support single-choice, text, numeric and Boolean answers. Distinguish risk tolerance from risk capacity where the product implements both.

### C. Instrument master data

Separate companies, canonical securities, exchange records and exchange-specific listings. Symbols are exchange-specific; a single security/ISIN may be listed on more than one exchange. Store sector and industry definitions separately; each industry belongs to a sector, while company-to-industry membership is a dated junction. Keep provider-specific instrument identifiers in a separate mapping table rather than on the listing record.

### D. Financial data and source lineage

Model data sources, provider-specific instrument mappings, ingestion runs and per-run error records, prices, fundamental metric definitions and metric observations, economic indicator definitions and observations, news articles and news-to-security mappings. Link imported facts to the ingestion run that supplied them when known, and ensure that the run and fact refer to the same source. Separate relatively stable metadata from time-series observations. Record source and retrieval/publication times. Respect provider licenses and rate limits. Raw API responses should normally be stored in object storage or selective JSONB only when needed for debugging/audit, not copied indiscriminately into core tables.

### E. Portfolio generation and versioning

Separate a logical portfolio from each generated version and its instrument-level decisions. Support selected, excluded and watchlist securities. Preserve alternative versions and do not overwrite earlier results. Store target allocation weights as precise numeric values; derive display amounts when appropriate rather than storing duplicated calculations.

### F. Explainability and safety validation

Store user-facing summaries, structured reasons, source references and optionally captured evidence values. Store validation runs and per-rule results, engine/rule-set versions, risk/constraint metrics, and scenario outputs. Do not persist unrestricted model chain-of-thought.

### G. Agent and strategy reproducibility

Store strategy definitions and versions, agent definitions and versions, model/provider and prompt/schema versions, fingerprints, execution status, token counts where available, latency and errors. Use structured JSONB outputs only where the data shape legitimately varies.

### H. Existing portfolio diagnosis

Keep user-reported or imported holdings separate from proposed recommendations. Model diagnosis attempts and proposed buy/sell/hold rebalance actions. Clearly label whether data is manual, file-imported or broker-confirmed.

### I. Operations and optional modules

Evaluate audit events, notification records, user feedback and knowledge-document/index metadata. Put broker accounts/orders/executions and performance snapshots in a separately labelled optional extension unless the product scope confirms them.

## 6. Normalization requirements

Normalize to 3NF and consider BCNF where appropriate. Explain functional dependencies for important tables:

- 1NF: values are atomic; repeating groups are rows or junction tables.
- 2NF: non-key attributes depend on the whole candidate key; avoid attributes in a junction table that depend on only one side.
- 3NF: company, exchange, sector, metric, source, user and strategy descriptions are centralized in their master tables, rather than repeated in facts or portfolio rows.
- BCNF: use candidate keys and uniqueness constraints so every determinant in the relevant relations is a candidate key where practical.

Explain every justified snapshot/denormalization. Derive values such as `target_amount = investment_amount × target_weight / 100` dynamically unless an immutable, separately meaningful calculation snapshot is needed. Allocation sums across rows cannot be enforced by a normal row-level CHECK; define a transaction/service-layer validation or a carefully designed deferred constraint trigger.

## 7. PostgreSQL-specific requirements

- Use `UUID` consistently for entity identifiers.
- Use `NUMERIC(p,s)` for money, prices, quantities and percentage values requiring decimal precision; never use floating-point for financial amounts. Include an explicit currency code for all independently stored monetary amounts, including financial goals.
- Use `DATE` for date-only data and `TIMESTAMPTZ` for timestamps.
- Use `BOOLEAN`, `TEXT`/`VARCHAR`, `JSONB`, `INET` and other types only where appropriate.
- Define FK behaviour explicitly. Use `RESTRICT` for history/master data whose deletion would break auditability and `CASCADE` for true dependent/junction records where appropriate.
- Include unique, check, FK and index definitions. Identify rules that require multi-row or cross-table logic.
- Keep migration DDL dependency-ordered and executable on PostgreSQL 14+.
- Do not require TimescaleDB or other extensions without a measured need.

## 8. Required diagrams and implementation artifacts

Produce a high-level ER diagram plus module-level Mermaid ER diagrams for:

1. Users, goals and risk assessment.
2. Company/security/listing and market data.
3. Portfolio request, versions, constraints, decisions, evidence, explanation and validation.
4. Existing holdings, diagnosis, agents and operations.

Names and keys in diagrams must match the dictionary and SQL exactly.

Deliver:

1. Unified database-design specification.
2. Scope classification and table inventory.
3. Full data dictionary for every core table.
4. Complete PK/FK/candidate-key/constraint definitions.
5. Relationship/cardinality/optionality map.
6. Normalization analysis.
7. Mermaid ER diagrams.
8. Executable PostgreSQL core DDL.
9. Separate optional broker/performance DDL.
10. Fictional sample-data SQL and an end-to-end example.
11. Representative SQL queries for core use cases.
12. Index rationale, security/privacy/retention notes, validation checklist and unresolved decisions.

## 9. Representative query requirements

The design must support: retrieving an investor's profile/goals/latest completed risk assessment; listing portfolio versions and selected allocations; finding securities in portfolios; retrieving explanation and evidence; reproducing a historical version's inputs, strategy and model references; comparing portfolio versions; fetching latest available price; identifying stale data; querying failed ingestion/agent runs; and fetching audit events for a recommendation. Include sample SQL for the most important queries.

## 10. Quality gate

Before declaring the deliverable ready:

- Every table has a primary key or a justified composite primary key.
- Every relationship is enforced by the correct FK and every M:N relationship has a junction table.
- Relationship cardinality, optionality and delete/update behaviour are documented.
- Column types, nullability and defaults are consistent between SQL and dictionary.
- The schema prevents duplicate listings and inconsistent security/listing references.
- The schema prevents an investor from referencing another investor's goal/profile/risk assessment through generation-request FKs where practical.
- Historical versions are distinguishable and not overwritten.
- Selected holdings and excluded/watchlist decisions have valid allocation fields.
- Monetary values use `NUMERIC`; currency is explicit where amounts are stored.
- All diagrams use actual table/column names.
- SQL is checked for table/column/FK references and can be applied first to a fresh development database.
- Multi-row allocation totals, cross-table ownership rules not expressible by simple constraints, data freshness and validation-gated publication are clearly assigned to service/transaction-level enforcement.

## 11. Implementation-language alignment

The persistence layer is **Python + FastAPI**. Use SQLAlchemy for ORM models and session/transaction handling, and Alembic for migrations. Do not generate Java/Spring Boot-specific entity classes or Maven configuration. The schema remains PostgreSQL-first and should be usable through direct SQL as well as SQLAlchemy.
