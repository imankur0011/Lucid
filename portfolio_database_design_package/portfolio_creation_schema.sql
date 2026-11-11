-- Intelligent Portfolio Creation Application
-- PostgreSQL 14+ | Backend: Python + FastAPI + LangGraph
-- Core schema. Optional broker/performance tables are in portfolio_optional_extensions.sql.
-- Apply only to a fresh development database first. Manage future changes using Alembic.

BEGIN;

-- UUID generation is built into supported PostgreSQL versions.

-- ============================================================================
-- 1. USER, PROFILE, PREFERENCES, CONSENT, GOALS, AND RISK ASSESSMENT
-- ============================================================================
CREATE TABLE app_users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_provider VARCHAR(40) NOT NULL DEFAULT 'cognito',
    identity_subject VARCHAR(255) NOT NULL,
    email VARCHAR(320),
    password_hash VARCHAR(255),
    email_verified BOOLEAN NOT NULL DEFAULT false,
    mobile_number VARCHAR(20),
    mobile_verified BOOLEAN NOT NULL DEFAULT false,
    account_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (account_status IN ('pending', 'active', 'suspended', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_app_users_identity UNIQUE (identity_provider, identity_subject)
);
CREATE UNIQUE INDEX uq_app_users_email_lower ON app_users (lower(email)) WHERE email IS NOT NULL;
CREATE INDEX ix_app_users_status ON app_users (account_status);

CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES app_users(user_id) ON DELETE CASCADE,
    display_name VARCHAR(120),
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    preferred_currency CHAR(3) NOT NULL DEFAULT 'INR',
    investment_experience VARCHAR(20)
        CHECK (investment_experience IN ('beginner', 'intermediate', 'experienced')),
    investment_knowledge_level VARCHAR(20)
        CHECK (investment_knowledge_level IN ('basic', 'intermediate', 'advanced')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES app_users(user_id) ON DELETE CASCADE,
    preferred_language VARCHAR(12) NOT NULL DEFAULT 'en-IN',
    timezone_name VARCHAR(80) NOT NULL DEFAULT 'Asia/Kolkata',
    email_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    in_app_notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Keep a history of grant/withdrawal events; don't overwrite earlier decisions.
CREATE TABLE user_consents (
    consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    consent_type VARCHAR(60) NOT NULL,
    policy_version VARCHAR(80) NOT NULL,
    consent_status VARCHAR(12) NOT NULL CHECK (consent_status IN ('granted', 'withdrawn')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    capture_source VARCHAR(40) NOT NULL DEFAULT 'application',
    evidence_reference VARCHAR(300),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX ix_user_consents_user_time ON user_consents (user_id, recorded_at DESC);

CREATE TABLE financial_goals (
    goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    goal_name VARCHAR(120) NOT NULL,
    goal_type VARCHAR(40) NOT NULL,
    target_amount NUMERIC(20,2) NOT NULL CHECK (target_amount > 0),
    amount_already_saved NUMERIC(20,2) NOT NULL DEFAULT 0 CHECK (amount_already_saved >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    target_date DATE,
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority BETWEEN 1 AND 5),
    goal_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (goal_status IN ('active', 'paused', 'completed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_financial_goals_id_user UNIQUE (goal_id, user_id)
);
CREATE INDEX ix_financial_goals_user_status ON financial_goals (user_id, goal_status);

-- A question version is immutable once it is used in a completed assessment.
CREATE TABLE risk_questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_code VARCHAR(80) NOT NULL,
    question_version INTEGER NOT NULL CHECK (question_version > 0),
    question_text TEXT NOT NULL,
    answer_type VARCHAR(20) NOT NULL
        CHECK (answer_type IN ('single_choice', 'text', 'numeric', 'boolean')),
    is_required BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    display_order INTEGER NOT NULL DEFAULT 0,
    scoring_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_risk_question_version UNIQUE (question_code, question_version),
    CONSTRAINT uq_risk_question_id_code_version UNIQUE (question_id, question_code, question_version)
);

CREATE TABLE risk_question_options (
    option_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID NOT NULL REFERENCES risk_questions(question_id) ON DELETE RESTRICT,
    option_code VARCHAR(60) NOT NULL,
    option_label TEXT NOT NULL,
    score NUMERIC(8,3),
    display_order INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT uq_risk_option_code UNIQUE (question_id, option_code),
    CONSTRAINT uq_risk_option_question UNIQUE (option_id, question_id)
);

CREATE TABLE risk_assessments (
    risk_assessment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    questionnaire_version VARCHAR(80) NOT NULL,
    assessment_status VARCHAR(20) NOT NULL DEFAULT 'in_progress'
        CHECK (assessment_status IN ('in_progress', 'completed', 'superseded', 'cancelled')),
    risk_tolerance_score NUMERIC(8,3),
    risk_capacity_score NUMERIC(8,3),
    risk_category VARCHAR(30)
        CHECK (risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT ck_risk_assessment_dates CHECK (completed_at IS NULL OR completed_at >= started_at),
    CONSTRAINT ck_risk_assessment_completed CHECK (assessment_status <> 'completed' OR completed_at IS NOT NULL),
    CONSTRAINT uq_risk_assessment_id_user UNIQUE (risk_assessment_id, user_id)
);
CREATE INDEX ix_risk_assessments_user_date ON risk_assessments (user_id, started_at DESC);
CREATE INDEX ix_risk_assessments_status ON risk_assessments (assessment_status);

CREATE TABLE risk_assessment_answers (
    answer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_assessment_id UUID NOT NULL REFERENCES risk_assessments(risk_assessment_id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES risk_questions(question_id) ON DELETE RESTRICT,
    selected_option_id UUID,
    answer_text TEXT,
    answer_numeric NUMERIC(18,6),
    answer_boolean BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_risk_answer_per_question UNIQUE (risk_assessment_id, question_id),
    CONSTRAINT fk_risk_answer_option_question FOREIGN KEY (selected_option_id, question_id)
        REFERENCES risk_question_options(option_id, question_id) ON DELETE RESTRICT,
    CONSTRAINT ck_risk_answer_one_value CHECK (
        num_nonnulls(selected_option_id, answer_text, answer_numeric, answer_boolean) = 1
    )
);
CREATE INDEX ix_risk_answers_assessment ON risk_assessment_answers (risk_assessment_id);

-- ============================================================================
-- 2. COMPANY, CANONICAL SECURITY, EXCHANGE LISTING, SECTOR/INDUSTRY, USER PREFERENCES
-- ============================================================================
CREATE TABLE companies (
    company_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_name VARCHAR(240) NOT NULL,
    common_name VARCHAR(180),
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    website_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_companies_legal_name ON companies (lower(legal_name));

CREATE TABLE exchanges (
    exchange_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exchange_code VARCHAR(20) NOT NULL UNIQUE,
    exchange_name VARCHAR(120) NOT NULL,
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE sectors (
    sector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_code VARCHAR(80) NOT NULL UNIQUE,
    sector_name VARCHAR(120) NOT NULL,
    taxonomy_source VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE industries (
    industry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL REFERENCES sectors(sector_id) ON DELETE RESTRICT,
    industry_code VARCHAR(100) NOT NULL UNIQUE,
    industry_name VARCHAR(160) NOT NULL,
    taxonomy_source VARCHAR(120),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE INDEX ix_industries_sector ON industries (sector_id, industry_name);

CREATE TABLE company_industries (
    company_id UUID NOT NULL REFERENCES companies(company_id) ON DELETE CASCADE,
    industry_id UUID NOT NULL REFERENCES industries(industry_id) ON DELETE RESTRICT,
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_to DATE,
    classification_source VARCHAR(120),
    PRIMARY KEY (company_id, industry_id, effective_from),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
CREATE INDEX ix_company_industries_industry ON company_industries (industry_id, company_id);

-- A security is the canonical financial instrument; listings carry exchange-specific symbols.
-- This correctly allows the same ISIN/security to be listed on more than one exchange.
CREATE TABLE securities (
    security_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(company_id) ON DELETE RESTRICT,
    security_name VARCHAR(240) NOT NULL,
    isin CHAR(12),
    security_type VARCHAR(30) NOT NULL
        CHECK (security_type IN ('stock', 'etf', 'index', 'mutual_fund', 'bond', 'other')),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    security_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (security_status IN ('active', 'inactive', 'matured', 'delisted')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX uq_securities_isin ON securities (isin) WHERE isin IS NOT NULL;
CREATE INDEX ix_securities_company ON securities (company_id);
CREATE INDEX ix_securities_type_status ON securities (security_type, security_status);

CREATE TABLE instrument_listings (
    listing_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    exchange_id UUID NOT NULL REFERENCES exchanges(exchange_id) ON DELETE RESTRICT,
    symbol VARCHAR(80) NOT NULL,
    trading_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (trading_status IN ('active', 'suspended', 'delisted', 'inactive')),
    listed_on DATE,
    delisted_on DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_listing_exchange_symbol UNIQUE (exchange_id, symbol),
    CONSTRAINT uq_listing_id_security UNIQUE (listing_id, security_id),
    CHECK (delisted_on IS NULL OR listed_on IS NULL OR delisted_on >= listed_on)
);
CREATE INDEX ix_listings_security ON instrument_listings (security_id);
CREATE INDEX ix_listings_status ON instrument_listings (trading_status, exchange_id);

CREATE TABLE user_sector_preferences (
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    sector_id UUID NOT NULL REFERENCES sectors(sector_id) ON DELETE RESTRICT,
    preference_type VARCHAR(12) NOT NULL CHECK (preference_type IN ('include', 'exclude')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, sector_id)
);

CREATE TABLE user_security_preferences (
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    preference_type VARCHAR(12) NOT NULL CHECK (preference_type IN ('include', 'exclude')),
    reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, security_id)
);

-- ============================================================================
-- 3. DATA PROVIDERS, INGESTION, PRICE/FUNDAMENTAL/ECONOMIC/NEWS DATA
-- ============================================================================
CREATE TABLE data_sources (
    data_source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_code VARCHAR(80) NOT NULL UNIQUE,
    display_name VARCHAR(160) NOT NULL,
    source_type VARCHAR(30) NOT NULL
        CHECK (source_type IN ('market_data', 'fundamentals', 'news', 'economic', 'broker', 'manual', 'internal')),
    base_url TEXT,
    secret_parameter_name VARCHAR(300),
    terms_url TEXT,
    license_notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE data_ingestion_runs (
    ingestion_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    data_type VARCHAR(60) NOT NULL,
    run_status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (run_status IN ('queued', 'running', 'succeeded', 'partial', 'failed', 'cancelled')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    records_seen BIGINT NOT NULL DEFAULT 0 CHECK (records_seen >= 0),
    records_inserted BIGINT NOT NULL DEFAULT 0 CHECK (records_inserted >= 0),
    records_updated BIGINT NOT NULL DEFAULT 0 CHECK (records_updated >= 0),
    error_code VARCHAR(100),
    error_summary TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (finished_at IS NULL OR finished_at >= started_at),
    CONSTRAINT uq_ingestion_run_source UNIQUE (ingestion_run_id, data_source_id)
);
CREATE INDEX ix_ingestion_source_time ON data_ingestion_runs (data_source_id, started_at DESC);
CREATE INDEX ix_ingestion_status_time ON data_ingestion_runs (run_status, started_at DESC);

CREATE TABLE data_ingestion_errors (
    ingestion_error_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID NOT NULL REFERENCES data_ingestion_runs(ingestion_run_id) ON DELETE CASCADE,
    error_code VARCHAR(100),
    error_message TEXT NOT NULL,
    record_reference VARCHAR(300),
    is_retryable BOOLEAN NOT NULL DEFAULT FALSE,
    error_details JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_ingestion_errors_run_time ON data_ingestion_errors (ingestion_run_id, occurred_at DESC);

CREATE TABLE source_instrument_mappings (
    source_instrument_mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    listing_id UUID NOT NULL REFERENCES instrument_listings(listing_id) ON DELETE RESTRICT,
    external_instrument_code VARCHAR(200) NOT NULL,
    external_symbol VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_source_external_instrument UNIQUE (data_source_id, external_instrument_code),
    CONSTRAINT uq_source_listing_mapping UNIQUE (data_source_id, listing_id)
);
CREATE INDEX ix_source_instrument_listing ON source_instrument_mappings (listing_id, data_source_id);

CREATE TABLE market_prices (
    market_price_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    listing_id UUID NOT NULL REFERENCES instrument_listings(listing_id) ON DELETE RESTRICT,
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    ingestion_run_id UUID,
    price_date DATE NOT NULL,
    open_price NUMERIC(20,6),
    high_price NUMERIC(20,6),
    low_price NUMERIC(20,6),
    close_price NUMERIC(20,6) NOT NULL CHECK (close_price >= 0),
    adjusted_close_price NUMERIC(20,6) CHECK (adjusted_close_price IS NULL OR adjusted_close_price >= 0),
    volume BIGINT CHECK (volume IS NULL OR volume >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    provider_timestamp TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_market_price_listing_date_source UNIQUE (listing_id, price_date, data_source_id),
    CONSTRAINT fk_market_price_ingestion_source FOREIGN KEY (ingestion_run_id, data_source_id)
        REFERENCES data_ingestion_runs(ingestion_run_id, data_source_id) ON DELETE RESTRICT,
    CHECK (open_price IS NULL OR open_price >= 0),
    CHECK (high_price IS NULL OR high_price >= 0),
    CHECK (low_price IS NULL OR low_price >= 0),
    CHECK (high_price IS NULL OR low_price IS NULL OR high_price >= low_price),
    CHECK (high_price IS NULL OR open_price IS NULL OR high_price >= open_price),
    CHECK (high_price IS NULL OR high_price >= close_price),
    CHECK (low_price IS NULL OR open_price IS NULL OR low_price <= open_price),
    CHECK (low_price IS NULL OR low_price <= close_price)
);
CREATE INDEX ix_market_prices_listing_date ON market_prices (listing_id, price_date DESC);
CREATE INDEX ix_market_prices_source_retrieved ON market_prices (data_source_id, retrieved_at DESC);

CREATE TABLE metric_definitions (
    metric_definition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_code VARCHAR(100) NOT NULL UNIQUE,
    metric_name VARCHAR(180) NOT NULL,
    unit_code VARCHAR(40) NOT NULL,
    value_kind VARCHAR(20) NOT NULL DEFAULT 'numeric'
        CHECK (value_kind IN ('numeric')),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE fundamental_metrics (
    fundamental_metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    metric_definition_id UUID NOT NULL REFERENCES metric_definitions(metric_definition_id) ON DELETE RESTRICT,
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    ingestion_run_id UUID,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('quarterly', 'annual', 'ttm', 'point_in_time')),
    period_end_date DATE NOT NULL,
    metric_value NUMERIC(24,8) NOT NULL,
    currency_code CHAR(3),
    reported_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_fundamental_fact UNIQUE
        (security_id, metric_definition_id, period_type, period_end_date, data_source_id),
    CONSTRAINT fk_fundamental_ingestion_source FOREIGN KEY (ingestion_run_id, data_source_id)
        REFERENCES data_ingestion_runs(ingestion_run_id, data_source_id) ON DELETE RESTRICT
);
CREATE INDEX ix_fundamentals_security_metric_date
    ON fundamental_metrics (security_id, metric_definition_id, period_end_date DESC);

CREATE TABLE economic_indicators (
    economic_indicator_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    indicator_code VARCHAR(100) NOT NULL UNIQUE,
    indicator_name VARCHAR(200) NOT NULL,
    country_code CHAR(2) NOT NULL DEFAULT 'IN',
    unit_code VARCHAR(60),
    frequency VARCHAR(20)
        CHECK (frequency IN ('daily', 'weekly', 'monthly', 'quarterly', 'annual', 'irregular')),
    description TEXT
);

CREATE TABLE economic_observations (
    economic_observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    economic_indicator_id UUID NOT NULL REFERENCES economic_indicators(economic_indicator_id) ON DELETE RESTRICT,
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    ingestion_run_id UUID,
    observation_date DATE NOT NULL,
    observation_value NUMERIC(24,8) NOT NULL,
    release_date DATE,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_economic_fact UNIQUE (economic_indicator_id, observation_date, data_source_id),
    CONSTRAINT fk_economic_ingestion_source FOREIGN KEY (ingestion_run_id, data_source_id)
        REFERENCES data_ingestion_runs(ingestion_run_id, data_source_id) ON DELETE RESTRICT
);
CREATE INDEX ix_economic_indicator_date ON economic_observations (economic_indicator_id, observation_date DESC);

CREATE TABLE market_news_articles (
    news_article_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID NOT NULL REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    ingestion_run_id UUID,
    provider_article_id VARCHAR(300),
    article_url TEXT,
    headline TEXT NOT NULL,
    summary TEXT,
    language_code VARCHAR(12),
    published_at TIMESTAMPTZ,
    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sentiment_score NUMERIC(8,5) CHECK (sentiment_score BETWEEN -1 AND 1),
    sentiment_label VARCHAR(20) CHECK (sentiment_label IN ('negative', 'neutral', 'positive', 'mixed')),
    licensing_notes TEXT,
    CONSTRAINT uq_news_provider_article UNIQUE (data_source_id, provider_article_id),
    CONSTRAINT fk_news_ingestion_source FOREIGN KEY (ingestion_run_id, data_source_id)
        REFERENCES data_ingestion_runs(ingestion_run_id, data_source_id) ON DELETE RESTRICT
);
CREATE UNIQUE INDEX uq_news_source_url ON market_news_articles (data_source_id, article_url)
    WHERE article_url IS NOT NULL;
CREATE INDEX ix_news_published_at ON market_news_articles (published_at DESC);
CREATE INDEX ix_news_source_retrieved ON market_news_articles (data_source_id, retrieved_at DESC);

CREATE TABLE news_article_securities (
    news_article_id UUID NOT NULL REFERENCES market_news_articles(news_article_id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    relevance_score NUMERIC(6,5) CHECK (relevance_score IS NULL OR relevance_score BETWEEN 0 AND 1),
    link_method VARCHAR(30) NOT NULL DEFAULT 'provider'
        CHECK (link_method IN ('provider', 'symbol_match', 'entity_match', 'manual', 'model')),
    PRIMARY KEY (news_article_id, security_id)
);
CREATE INDEX ix_news_security ON news_article_securities (security_id, news_article_id);

-- ============================================================================
-- 4. PORTFOLIOS, GENERATION REQUESTS, STRATEGY VERSIONS, DECISIONS, VALIDATION
-- ============================================================================
CREATE TABLE investor_portfolios (
    portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(160) NOT NULL,
    portfolio_status VARCHAR(20) NOT NULL DEFAULT 'draft'
        CHECK (portfolio_status IN ('draft', 'active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_portfolio_id_user UNIQUE (portfolio_id, user_id)
);
CREATE INDEX ix_portfolios_user_updated ON investor_portfolios (user_id, updated_at DESC);

CREATE TABLE portfolio_generation_requests (
    generation_request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,
    user_id UUID NOT NULL,
    goal_id UUID,
    risk_assessment_id UUID,
    request_type VARCHAR(20) NOT NULL DEFAULT 'create'
        CHECK (request_type IN ('create', 'revise', 'scenario')),
    request_status VARCHAR(20) NOT NULL DEFAULT 'queued'
        CHECK (request_status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
    user_prompt TEXT,
    requested_amount NUMERIC(20,2) NOT NULL CHECK (requested_amount > 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    investment_horizon_months INTEGER CHECK (investment_horizon_months IS NULL OR investment_horizon_months > 0),
    normalized_inputs JSONB NOT NULL DEFAULT '{}'::jsonb,
    investor_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    market_context_as_of TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_code VARCHAR(100),
    error_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_generation_portfolio_owner FOREIGN KEY (portfolio_id, user_id)
        REFERENCES investor_portfolios(portfolio_id, user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_generation_goal_owner FOREIGN KEY (goal_id, user_id)
        REFERENCES financial_goals(goal_id, user_id) ON DELETE RESTRICT,
    CONSTRAINT fk_generation_risk_owner FOREIGN KEY (risk_assessment_id, user_id)
        REFERENCES risk_assessments(risk_assessment_id, user_id) ON DELETE RESTRICT,
    CONSTRAINT uq_generation_request_portfolio UNIQUE (generation_request_id, portfolio_id),
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);
CREATE INDEX ix_generation_user_time ON portfolio_generation_requests (user_id, created_at DESC);
CREATE INDEX ix_generation_status_time ON portfolio_generation_requests (request_status, created_at DESC);
CREATE INDEX ix_generation_portfolio_time ON portfolio_generation_requests (portfolio_id, created_at DESC);

CREATE TABLE strategy_definitions (
    strategy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_code VARCHAR(100) NOT NULL UNIQUE,
    strategy_name VARCHAR(180) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE strategy_versions (
    strategy_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy_id UUID NOT NULL REFERENCES strategy_definitions(strategy_id) ON DELETE RESTRICT,
    version_label VARCHAR(80) NOT NULL,
    optimizer_name VARCHAR(160) NOT NULL,
    implementation_revision VARCHAR(160),
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    constraint_set_version VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_strategy_version UNIQUE (strategy_id, version_label)
);

CREATE TABLE portfolio_versions (
    portfolio_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID NOT NULL,
    generation_request_id UUID NOT NULL,
    strategy_version_id UUID NOT NULL REFERENCES strategy_versions(strategy_version_id) ON DELETE RESTRICT,
    version_number INTEGER NOT NULL CHECK (version_number > 0),
    version_status VARCHAR(20) NOT NULL DEFAULT 'generated'
        CHECK (version_status IN ('generated', 'reviewed', 'accepted', 'rejected', 'superseded', 'archived')),
    investment_amount NUMERIC(20,2) NOT NULL CHECK (investment_amount > 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    investment_horizon_months INTEGER CHECK (investment_horizon_months IS NULL OR investment_horizon_months > 0),
    risk_category VARCHAR(30)
        CHECK (risk_category IS NULL OR risk_category IN ('very_conservative', 'conservative', 'moderate', 'growth', 'aggressive')),
    expected_return_pct NUMERIC(9,4),
    expected_volatility_pct NUMERIC(9,4),
    diversification_score NUMERIC(8,4) CHECK (diversification_score IS NULL OR diversification_score BETWEEN 0 AND 100),
    market_context_as_of TIMESTAMPTZ,
    generation_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_version_request_portfolio FOREIGN KEY (generation_request_id, portfolio_id)
        REFERENCES portfolio_generation_requests(generation_request_id, portfolio_id) ON DELETE RESTRICT,
    CONSTRAINT uq_portfolio_version_number UNIQUE (portfolio_id, version_number),
    CONSTRAINT uq_version_id_portfolio UNIQUE (portfolio_version_id, portfolio_id)
);
CREATE INDEX ix_portfolio_versions_recent ON portfolio_versions (portfolio_id, version_number DESC);
CREATE INDEX ix_portfolio_versions_generated ON portfolio_versions (generated_at DESC);

CREATE TABLE portfolio_security_decisions (
    decision_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    listing_id UUID,
    decision_status VARCHAR(20) NOT NULL CHECK (decision_status IN ('selected', 'excluded', 'watchlist')),
    target_weight_pct NUMERIC(9,6),
    decision_reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_version_security UNIQUE (portfolio_version_id, security_id),
    CONSTRAINT uq_decision_version UNIQUE (decision_id, portfolio_version_id),
    CONSTRAINT fk_decision_listing_security FOREIGN KEY (listing_id, security_id)
        REFERENCES instrument_listings(listing_id, security_id) ON DELETE RESTRICT,
    CHECK (
        (decision_status = 'selected' AND target_weight_pct IS NOT NULL AND target_weight_pct > 0 AND target_weight_pct <= 100)
        OR
        (decision_status IN ('excluded', 'watchlist') AND target_weight_pct IS NULL)
    )
);
CREATE INDEX ix_decisions_security ON portfolio_security_decisions (security_id, portfolio_version_id);
CREATE INDEX ix_decisions_version_status ON portfolio_security_decisions (portfolio_version_id, decision_status);

CREATE TABLE portfolio_version_constraints (
    portfolio_constraint_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    constraint_code VARCHAR(100) NOT NULL,
    operator VARCHAR(12) NOT NULL CHECK (operator IN ('<=', '>=', '=', 'between')),
    comparison_value NUMERIC(24,8),
    upper_value NUMERIC(24,8),
    unit_code VARCHAR(40),
    is_mandatory BOOLEAN NOT NULL DEFAULT TRUE,
    applied BOOLEAN NOT NULL DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_version_constraint UNIQUE (portfolio_version_id, constraint_code),
    CHECK (operator <> 'between' OR (comparison_value IS NOT NULL AND upper_value IS NOT NULL AND comparison_value <= upper_value)),
    CHECK (operator = 'between' OR comparison_value IS NOT NULL),
    CHECK (operator = 'between' OR upper_value IS NULL)
);
CREATE INDEX ix_version_constraints_code ON portfolio_version_constraints (constraint_code, portfolio_version_id);

-- Evidence stores user-facing citations and optional snapshots of the values cited.
-- Do not put hidden chain-of-thought or credentials in this table.
CREATE TABLE evidence_items (
    evidence_item_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    security_id UUID REFERENCES securities(security_id) ON DELETE RESTRICT,
    market_price_id UUID REFERENCES market_prices(market_price_id) ON DELETE RESTRICT,
    fundamental_metric_id UUID REFERENCES fundamental_metrics(fundamental_metric_id) ON DELETE RESTRICT,
    economic_observation_id UUID REFERENCES economic_observations(economic_observation_id) ON DELETE RESTRICT,
    news_article_id UUID REFERENCES market_news_articles(news_article_id) ON DELETE RESTRICT,
    evidence_type VARCHAR(40) NOT NULL,
    title VARCHAR(300) NOT NULL,
    evidence_summary TEXT,
    source_url TEXT,
    source_record_reference VARCHAR(300),
    published_at TIMESTAMPTZ,
    observed_at TIMESTAMPTZ,
    cited_value_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (num_nonnulls(market_price_id, fundamental_metric_id, economic_observation_id, news_article_id) <= 1)
);
CREATE INDEX ix_evidence_security_time ON evidence_items (security_id, observed_at DESC);
CREATE INDEX ix_evidence_source_time ON evidence_items (data_source_id, observed_at DESC);

CREATE TABLE recommendation_explanations (
    explanation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    decision_id UUID,
    explanation_type VARCHAR(30) NOT NULL
        CHECK (explanation_type IN ('portfolio', 'selection', 'exclusion', 'risk', 'diversification', 'constraint', 'scenario', 'review')),
    title VARCHAR(240) NOT NULL,
    explanation_text TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_explanation_decision_version FOREIGN KEY (decision_id, portfolio_version_id)
        REFERENCES portfolio_security_decisions(decision_id, portfolio_version_id) ON DELETE RESTRICT
);
CREATE INDEX ix_explanations_version_order ON recommendation_explanations (portfolio_version_id, display_order);

CREATE TABLE explanation_evidence (
    explanation_id UUID NOT NULL REFERENCES recommendation_explanations(explanation_id) ON DELETE RESTRICT,
    evidence_item_id UUID NOT NULL REFERENCES evidence_items(evidence_item_id) ON DELETE RESTRICT,
    relationship_label VARCHAR(40) NOT NULL DEFAULT 'supports'
        CHECK (relationship_label IN ('supports', 'contradicts', 'contextualizes')),
    PRIMARY KEY (explanation_id, evidence_item_id)
);
CREATE INDEX ix_explanation_evidence_evidence ON explanation_evidence (evidence_item_id);

CREATE TABLE portfolio_validation_runs (
    validation_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    rule_set_version VARCHAR(100) NOT NULL,
    calculation_engine_version VARCHAR(100) NOT NULL,
    validation_status VARCHAR(24) NOT NULL
        CHECK (validation_status IN ('running', 'passed', 'failed', 'passed_with_warnings')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (completed_at IS NULL OR completed_at >= started_at)
);
CREATE INDEX ix_validation_runs_version_time ON portfolio_validation_runs (portfolio_version_id, started_at DESC);

CREATE TABLE portfolio_validation_results (
    validation_result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    validation_run_id UUID NOT NULL REFERENCES portfolio_validation_runs(validation_run_id) ON DELETE RESTRICT,
    rule_code VARCHAR(100) NOT NULL,
    result_status VARCHAR(20) NOT NULL CHECK (result_status IN ('pass', 'fail', 'warning', 'not_applicable')),
    severity VARCHAR(20) NOT NULL DEFAULT 'info'
        CHECK (severity IN ('info', 'low', 'medium', 'high', 'critical')),
    security_id UUID REFERENCES securities(security_id) ON DELETE RESTRICT,
    actual_value NUMERIC(24,8),
    threshold_value NUMERIC(24,8),
    result_message TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_validation_results_run_status ON portfolio_validation_results (validation_run_id, result_status);
CREATE INDEX ix_validation_results_rule_status ON portfolio_validation_results (rule_code, result_status);

CREATE TABLE portfolio_scenarios (
    portfolio_scenario_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    scenario_code VARCHAR(80) NOT NULL,
    scenario_name VARCHAR(180) NOT NULL,
    scenario_type VARCHAR(30) NOT NULL CHECK (scenario_type IN ('stress', 'what_if', 'market_regime', 'sensitivity')),
    assumptions JSONB NOT NULL DEFAULT '{}'::jsonb,
    estimated_portfolio_value NUMERIC(20,2) CHECK (estimated_portfolio_value IS NULL OR estimated_portfolio_value >= 0),
    estimated_change_amount NUMERIC(20,2),
    estimated_change_pct NUMERIC(9,4),
    result_summary TEXT,
    calculation_version VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_scenario_code_per_version UNIQUE (portfolio_version_id, scenario_code)
);
CREATE INDEX ix_scenarios_version_time ON portfolio_scenarios (portfolio_version_id, created_at DESC);

-- ============================================================================
-- 5. USER-REPORTED/IMPORTED EXISTING HOLDINGS, DIAGNOSIS, REBALANCE PREVIEW
-- ============================================================================
CREATE TABLE existing_portfolios (
    existing_portfolio_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    portfolio_name VARCHAR(160) NOT NULL,
    source_type VARCHAR(20) NOT NULL DEFAULT 'manual'
        CHECK (source_type IN ('manual', 'file_import', 'broker_import')),
    source_name VARCHAR(160),
    as_of_date DATE NOT NULL DEFAULT CURRENT_DATE,
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    portfolio_status VARCHAR(20) NOT NULL DEFAULT 'active'
        CHECK (portfolio_status IN ('active', 'archived')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_existing_portfolio_id_user UNIQUE (existing_portfolio_id, user_id)
);
CREATE INDEX ix_existing_portfolios_user_date ON existing_portfolios (user_id, as_of_date DESC);

CREATE TABLE existing_portfolio_holdings (
    existing_portfolio_holding_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    existing_portfolio_id UUID NOT NULL REFERENCES existing_portfolios(existing_portfolio_id) ON DELETE CASCADE,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    listing_id UUID,
    quantity NUMERIC(24,8) NOT NULL CHECK (quantity > 0),
    average_purchase_price NUMERIC(20,6) CHECK (average_purchase_price IS NULL OR average_purchase_price >= 0),
    market_value NUMERIC(20,2) CHECK (market_value IS NULL OR market_value >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    source_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_existing_holding_security UNIQUE (existing_portfolio_id, security_id),
    CONSTRAINT fk_existing_holding_listing_security FOREIGN KEY (listing_id, security_id)
        REFERENCES instrument_listings(listing_id, security_id) ON DELETE RESTRICT
);
CREATE INDEX ix_existing_holdings_security ON existing_portfolio_holdings (security_id);

CREATE TABLE portfolio_diagnoses (
    portfolio_diagnosis_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    existing_portfolio_id UUID NOT NULL REFERENCES existing_portfolios(existing_portfolio_id) ON DELETE RESTRICT,
    diagnosis_status VARCHAR(20) NOT NULL DEFAULT 'completed'
        CHECK (diagnosis_status IN ('queued', 'running', 'completed', 'failed')),
    summary TEXT,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    market_context_as_of TIMESTAMPTZ,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CHECK (completed_at IS NULL OR completed_at >= started_at)
);
CREATE INDEX ix_diagnoses_existing_portfolio_time ON portfolio_diagnoses (existing_portfolio_id, started_at DESC);

CREATE TABLE rebalance_suggestions (
    rebalance_suggestion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_diagnosis_id UUID NOT NULL REFERENCES portfolio_diagnoses(portfolio_diagnosis_id) ON DELETE RESTRICT,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    suggested_action VARCHAR(10) NOT NULL CHECK (suggested_action IN ('buy', 'sell', 'hold')),
    current_quantity NUMERIC(24,8) CHECK (current_quantity IS NULL OR current_quantity >= 0),
    target_quantity NUMERIC(24,8) CHECK (target_quantity IS NULL OR target_quantity >= 0),
    current_value NUMERIC(20,2) CHECK (current_value IS NULL OR current_value >= 0),
    target_value NUMERIC(20,2) CHECK (target_value IS NULL OR target_value >= 0),
    change_value NUMERIC(20,2),
    explanation TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_rebalance_security_per_diagnosis UNIQUE (portfolio_diagnosis_id, security_id)
);

-- ============================================================================
-- 6. AGENT/MODEL VERSIONS, OPTIONAL KNOWLEDGE DOCUMENTS, FEEDBACK, NOTIFICATIONS
-- ============================================================================
CREATE TABLE agent_definitions (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_code VARCHAR(80) NOT NULL UNIQUE,
    agent_name VARCHAR(160) NOT NULL,
    purpose TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE agent_versions (
    agent_version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id UUID NOT NULL REFERENCES agent_definitions(agent_id) ON DELETE RESTRICT,
    version_label VARCHAR(80) NOT NULL,
    llm_provider VARCHAR(80),
    model_name VARCHAR(160),
    prompt_version VARCHAR(100),
    prompt_hash VARCHAR(128),
    structured_output_schema_version VARCHAR(100),
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_agent_version UNIQUE (agent_id, version_label)
);

CREATE TABLE agent_execution_runs (
    agent_execution_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    generation_request_id UUID REFERENCES portfolio_generation_requests(generation_request_id) ON DELETE RESTRICT,
    portfolio_version_id UUID REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    agent_version_id UUID NOT NULL REFERENCES agent_versions(agent_version_id) ON DELETE RESTRICT,
    execution_status VARCHAR(20) NOT NULL
        CHECK (execution_status IN ('queued', 'running', 'succeeded', 'failed', 'skipped')),
    input_fingerprint VARCHAR(128),
    output_summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    input_token_count BIGINT CHECK (input_token_count IS NULL OR input_token_count >= 0),
    output_token_count BIGINT CHECK (output_token_count IS NULL OR output_token_count >= 0),
    latency_ms BIGINT CHECK (latency_ms IS NULL OR latency_ms >= 0),
    error_code VARCHAR(100),
    error_summary TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    CHECK (completed_at IS NULL OR completed_at >= started_at),
    CHECK (generation_request_id IS NOT NULL OR portfolio_version_id IS NOT NULL)
);
CREATE INDEX ix_agent_runs_request ON agent_execution_runs (generation_request_id, started_at DESC);
CREATE INDEX ix_agent_runs_version ON agent_execution_runs (portfolio_version_id, started_at DESC);
CREATE INDEX ix_agent_runs_status_time ON agent_execution_runs (execution_status, started_at DESC);

-- Metadata only; actual text chunks/embeddings live in object storage and/or FAISS.
CREATE TABLE knowledge_documents (
    knowledge_document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_source_id UUID REFERENCES data_sources(data_source_id) ON DELETE RESTRICT,
    external_document_id VARCHAR(300),
    document_title VARCHAR(300) NOT NULL,
    document_type VARCHAR(40) NOT NULL,
    source_url TEXT,
    content_hash VARCHAR(128) NOT NULL,
    object_storage_uri TEXT,
    embedding_model VARCHAR(160) NOT NULL,
    vector_index_reference VARCHAR(300),
    index_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (index_status IN ('pending', 'indexed', 'failed', 'retired')),
    published_at TIMESTAMPTZ,
    indexed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_knowledge_document_embedding UNIQUE (content_hash, embedding_model)
);
CREATE INDEX ix_knowledge_documents_status ON knowledge_documents (index_status, created_at DESC);

CREATE TABLE user_feedback (
    user_feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    portfolio_version_id UUID REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    feedback_type VARCHAR(30) NOT NULL CHECK (feedback_type IN ('recommendation', 'explanation', 'application', 'other')),
    rating SMALLINT CHECK (rating IS NULL OR rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_user_feedback_user_time ON user_feedback (user_id, created_at DESC);

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(40) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    delivery_channel VARCHAR(20) NOT NULL DEFAULT 'in_app'
        CHECK (delivery_channel IN ('in_app', 'email', 'sms', 'push')),
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (delivery_status IN ('pending', 'sent', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    dismissed_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    CHECK (sent_at IS NULL OR sent_at >= created_at),
    CHECK (read_at IS NULL OR read_at >= created_at),
    CHECK (dismissed_at IS NULL OR dismissed_at >= created_at)
);
CREATE INDEX ix_notifications_user_status_time ON notifications (user_id, delivery_status, created_at DESC);

CREATE TABLE audit_events (
    audit_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_user_id UUID REFERENCES app_users(user_id) ON DELETE SET NULL,
    action_code VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    outcome VARCHAR(20) NOT NULL DEFAULT 'success' CHECK (outcome IN ('success', 'failure', 'denied')),
    request_id VARCHAR(128),
    ip_address INET,
    user_agent TEXT,
    event_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_audit_resource_time ON audit_events (resource_type, resource_id, created_at DESC);
CREATE INDEX ix_audit_actor_time ON audit_events (actor_user_id, created_at DESC);

-- ============================================================================
-- 7. UPDATED_AT TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_app_users_updated_at BEFORE UPDATE ON app_users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_financial_goals_updated_at BEFORE UPDATE ON financial_goals
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_securities_updated_at BEFORE UPDATE ON securities
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_instrument_listings_updated_at BEFORE UPDATE ON instrument_listings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_source_instrument_mappings_updated_at BEFORE UPDATE ON source_instrument_mappings
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_investor_portfolios_updated_at BEFORE UPDATE ON investor_portfolios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();
CREATE TRIGGER trg_existing_portfolios_updated_at BEFORE UPDATE ON existing_portfolios
    FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

COMMIT;

-- IMPORTANT RULES TO ENFORCE IN FASTAPI SERVICE LOGIC OR TRANSACTION-SAFE DATABASE PROCEDURES:
-- 1. Sum of selected target_weight_pct per portfolio_version_id must be 100% within a documented tolerance.
-- 2. A portfolio version must not be marked reviewed/accepted until required validation passes.
-- 3. Keep generated portfolio versions, inputs, validations, evidence and agent/version references immutable after publication.
-- 4. Validate questionnaire answer types against risk_questions.answer_type (DB CHECK alone cannot join another table).
-- 5. Validate any security/listing availability and market-data freshness before portfolio calculation.
-- 6. Protect user-scoped endpoints with ownership checks; UUIDs are not authorization.
-- 7. Do not store credentials, raw API keys, broker tokens or private chain-of-thought in this schema.
-- 8. Implement account closure/deletion with a documented privacy, retention, and historical-record policy.
