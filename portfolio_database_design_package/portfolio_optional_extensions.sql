-- Optional future extensions. Apply only if the product scope requires them.
-- Apply after portfolio_creation_schema.sql.
BEGIN;

CREATE TABLE broker_providers (
    broker_provider_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_code VARCHAR(80) NOT NULL UNIQUE,
    provider_name VARCHAR(160) NOT NULL,
    developer_docs_url TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_broker_accounts (
    user_broker_account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES app_users(user_id) ON DELETE RESTRICT,
    broker_provider_id UUID NOT NULL REFERENCES broker_providers(broker_provider_id) ON DELETE RESTRICT,
    external_account_reference VARCHAR(240),
    account_label VARCHAR(120),
    connection_status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (connection_status IN ('pending', 'connected', 'expired', 'revoked', 'error')),
    granted_permissions JSONB NOT NULL DEFAULT '[]'::jsonb,
    secret_reference VARCHAR(400),
    connected_at TIMESTAMPTZ,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, broker_provider_id, external_account_reference)
);
CREATE INDEX ix_user_broker_accounts_user ON user_broker_accounts (user_id, connection_status);

CREATE TABLE broker_orders (
    broker_order_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_broker_account_id UUID NOT NULL REFERENCES user_broker_accounts(user_broker_account_id) ON DELETE RESTRICT,
    security_id UUID NOT NULL REFERENCES securities(security_id) ON DELETE RESTRICT,
    listing_id UUID,
    provider_order_reference VARCHAR(240),
    side VARCHAR(8) NOT NULL CHECK (side IN ('buy', 'sell')),
    order_type VARCHAR(20) NOT NULL CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit', 'other')),
    order_quantity NUMERIC(24,8) NOT NULL CHECK (order_quantity > 0),
    limit_price NUMERIC(20,6) CHECK (limit_price IS NULL OR limit_price >= 0),
    order_status VARCHAR(24) NOT NULL
        CHECK (order_status IN ('created', 'submitted', 'accepted', 'partially_filled', 'filled', 'cancelled', 'rejected', 'expired', 'unknown')),
    submitted_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT fk_broker_order_listing_security FOREIGN KEY (listing_id, security_id)
        REFERENCES instrument_listings(listing_id, security_id) ON DELETE RESTRICT,
    UNIQUE (user_broker_account_id, provider_order_reference)
);
CREATE INDEX ix_broker_orders_account_time ON broker_orders (user_broker_account_id, created_at DESC);
CREATE INDEX ix_broker_orders_status ON broker_orders (order_status, last_updated_at DESC);

CREATE TABLE broker_order_events (
    broker_order_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broker_order_id UUID NOT NULL REFERENCES broker_orders(broker_order_id) ON DELETE RESTRICT,
    event_status VARCHAR(24) NOT NULL,
    event_message TEXT,
    provider_event_reference VARCHAR(240),
    event_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (broker_order_id, provider_event_reference)
);
CREATE INDEX ix_broker_order_events_order_time ON broker_order_events (broker_order_id, occurred_at DESC);

CREATE TABLE broker_executions (
    broker_execution_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broker_order_id UUID NOT NULL REFERENCES broker_orders(broker_order_id) ON DELETE RESTRICT,
    provider_execution_reference VARCHAR(240),
    executed_quantity NUMERIC(24,8) NOT NULL CHECK (executed_quantity > 0),
    execution_price NUMERIC(20,6) NOT NULL CHECK (execution_price >= 0),
    executed_at TIMESTAMPTZ NOT NULL,
    fees_amount NUMERIC(20,2) CHECK (fees_amount IS NULL OR fees_amount >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    UNIQUE (broker_order_id, provider_execution_reference)
);
CREATE INDEX ix_broker_executions_order_time ON broker_executions (broker_order_id, executed_at DESC);

CREATE TABLE portfolio_performance_snapshots (
    performance_snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_version_id UUID NOT NULL REFERENCES portfolio_versions(portfolio_version_id) ON DELETE RESTRICT,
    snapshot_date DATE NOT NULL,
    valuation_amount NUMERIC(20,2) NOT NULL CHECK (valuation_amount >= 0),
    currency_code CHAR(3) NOT NULL DEFAULT 'INR',
    return_since_previous_pct NUMERIC(12,6),
    cumulative_return_pct NUMERIC(12,6),
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('simulated', 'user_reported', 'broker_confirmed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (portfolio_version_id, snapshot_date, source_type)
);
CREATE INDEX ix_performance_snapshot_date ON portfolio_performance_snapshots (portfolio_version_id, snapshot_date DESC);

CREATE OR REPLACE FUNCTION set_optional_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
CREATE TRIGGER trg_user_broker_accounts_updated_at BEFORE UPDATE ON user_broker_accounts
    FOR EACH ROW EXECUTE FUNCTION set_optional_updated_at_timestamp();

COMMIT;

-- Broker tokens are not stored in PostgreSQL. secret_reference must point to a managed secret.
-- These tables do not create broker permission, eligibility, licensing, or regulatory entitlement.
