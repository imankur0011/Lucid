-- Fictional end-to-end seed example for a fresh database after portfolio_creation_schema.sql.
-- All company names, identifiers and prices below are illustrative and do not represent securities.
BEGIN;

INSERT INTO app_users (user_id, identity_provider, identity_subject, email, account_status)
VALUES ('10000000-0000-4000-8000-000000000001', 'local-demo', 'demo-investor-001', 'investor@example.invalid', 'active');

INSERT INTO user_profiles (user_id, display_name, country_code, preferred_currency, investment_experience, investment_knowledge_level)
VALUES ('10000000-0000-4000-8000-000000000001', 'Demo Investor', 'IN', 'INR', 'beginner', 'basic');

INSERT INTO user_preferences (user_id)
VALUES ('10000000-0000-4000-8000-000000000001');

INSERT INTO financial_goals (goal_id, user_id, goal_name, goal_type, target_amount, target_date, priority)
VALUES ('20000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001',
        'Long-term savings goal', 'wealth_creation', 1000000.00, DATE '2032-12-31', 1);

INSERT INTO risk_assessments (risk_assessment_id, user_id, questionnaire_version, assessment_status,
                              risk_tolerance_score, risk_capacity_score, risk_category, started_at, completed_at)
VALUES ('21000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001',
        'demo-questionnaire-v1', 'completed', 55.000, 62.000, 'moderate',
        TIMESTAMPTZ '2026-10-17 10:00:00+05:30', TIMESTAMPTZ '2026-10-17 10:02:00+05:30');

INSERT INTO exchanges (exchange_id, exchange_code, exchange_name, country_code, currency_code)
VALUES ('30000000-0000-4000-8000-000000000001', 'DEMOEX', 'Demo Exchange', 'IN', 'INR');

INSERT INTO companies (company_id, legal_name, common_name, country_code)
VALUES
('40000000-0000-4000-8000-000000000001', 'Fictional Consumer Limited', 'Fictional Consumer', 'IN'),
('40000000-0000-4000-8000-000000000002', 'Fictional Technology Limited', 'Fictional Technology', 'IN'),
('40000000-0000-4000-8000-000000000003', 'Fictional Healthcare Limited', 'Fictional Healthcare', 'IN');

INSERT INTO sectors (sector_id, sector_code, sector_name)
VALUES
('41000000-0000-4000-8000-000000000001', 'DEMO_CONSUMER', 'Illustrative Consumer Sector'),
('41000000-0000-4000-8000-000000000002', 'DEMO_TECH', 'Illustrative Technology Sector'),
('41000000-0000-4000-8000-000000000003', 'DEMO_HEALTH', 'Illustrative Healthcare Sector');

INSERT INTO industries (industry_id, sector_id, industry_code, industry_name)
VALUES
('42000000-0000-4000-8000-000000000001', '41000000-0000-4000-8000-000000000001', 'DEMO_CONSUMER_PRODUCTS', 'Illustrative Consumer Products'),
('42000000-0000-4000-8000-000000000002', '41000000-0000-4000-8000-000000000002', 'DEMO_SOFTWARE', 'Illustrative Software'),
('42000000-0000-4000-8000-000000000003', '41000000-0000-4000-8000-000000000003', 'DEMO_HEALTH_SERVICES', 'Illustrative Healthcare Services');

INSERT INTO company_industries (company_id, industry_id, effective_from)
VALUES
('40000000-0000-4000-8000-000000000001', '42000000-0000-4000-8000-000000000001', DATE '2026-01-01'),
('40000000-0000-4000-8000-000000000002', '42000000-0000-4000-8000-000000000002', DATE '2026-01-01'),
('40000000-0000-4000-8000-000000000003', '42000000-0000-4000-8000-000000000003', DATE '2026-01-01');

INSERT INTO securities (security_id, company_id, security_name, isin, security_type, currency_code)
VALUES
('50000000-0000-4000-8000-000000000001', '40000000-0000-4000-8000-000000000001', 'Fictional Consumer Equity', 'ZZ0000000001', 'stock', 'INR'),
('50000000-0000-4000-8000-000000000002', '40000000-0000-4000-8000-000000000002', 'Fictional Technology Equity', 'ZZ0000000002', 'stock', 'INR'),
('50000000-0000-4000-8000-000000000003', '40000000-0000-4000-8000-000000000003', 'Fictional Healthcare Equity', 'ZZ0000000003', 'stock', 'INR');

INSERT INTO instrument_listings (listing_id, security_id, exchange_id, symbol)
VALUES
('51000000-0000-4000-8000-000000000001', '50000000-0000-4000-8000-000000000001', '30000000-0000-4000-8000-000000000001', 'DEMO-CONS'),
('51000000-0000-4000-8000-000000000002', '50000000-0000-4000-8000-000000000002', '30000000-0000-4000-8000-000000000001', 'DEMO-TECH'),
('51000000-0000-4000-8000-000000000003', '50000000-0000-4000-8000-000000000003', '30000000-0000-4000-8000-000000000001', 'DEMO-HEALTH');

INSERT INTO data_sources (data_source_id, source_code, display_name, source_type, base_url, license_notes)
VALUES ('60000000-0000-4000-8000-000000000001', 'demo_source', 'Illustrative Local Demo Data', 'manual', 'https://example.invalid',
        'Fictional demonstration data only. Not actual market data.');

INSERT INTO market_prices (market_price_id, listing_id, data_source_id, price_date,
                           open_price, high_price, low_price, close_price, adjusted_close_price, volume, currency_code)
VALUES
('61000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', '60000000-0000-4000-8000-000000000001', DATE '2026-10-16', 98, 105, 95, 103, 103, 10000, 'INR'),
('61000000-0000-4000-8000-000000000002', '51000000-0000-4000-8000-000000000002', '60000000-0000-4000-8000-000000000001', DATE '2026-10-16', 198, 211, 194, 205, 205, 20000, 'INR'),
('61000000-0000-4000-8000-000000000003', '51000000-0000-4000-8000-000000000003', '60000000-0000-4000-8000-000000000001', DATE '2026-10-16', 148, 154, 145, 151, 151, 15000, 'INR');

INSERT INTO strategy_definitions (strategy_id, strategy_code, strategy_name, description)
VALUES ('70000000-0000-4000-8000-000000000001', 'demo_diversified', 'Demo Diversified Strategy', 'Illustrative strategy version for schema testing.');

INSERT INTO strategy_versions (strategy_version_id, strategy_id, version_label, optimizer_name, implementation_revision, configuration)
VALUES ('71000000-0000-4000-8000-000000000001', '70000000-0000-4000-8000-000000000001', '0.1.0',
        'demo_optimizer', 'demo-revision-001', '{"purpose":"schema example only"}'::jsonb);

INSERT INTO investor_portfolios (portfolio_id, user_id, portfolio_name)
VALUES ('80000000-0000-4000-8000-000000000001', '10000000-0000-4000-8000-000000000001', 'Demo long-term portfolio');

INSERT INTO portfolio_generation_requests (
    generation_request_id, portfolio_id, user_id, goal_id, risk_assessment_id,
    request_type, request_status, requested_amount, currency_code, investment_horizon_months,
    normalized_inputs, investor_snapshot, market_context_as_of, started_at, completed_at
) VALUES (
    '81000000-0000-4000-8000-000000000001', '80000000-0000-4000-8000-000000000001',
    '10000000-0000-4000-8000-000000000001', '20000000-0000-4000-8000-000000000001',
    '21000000-0000-4000-8000-000000000001', 'create', 'succeeded', 100000.00, 'INR', 72,
    '{"risk_category":"moderate","excluded_sectors":[]}'::jsonb,
    '{"experience":"beginner","knowledge":"basic"}'::jsonb,
    TIMESTAMPTZ '2026-10-16 15:30:00+05:30', TIMESTAMPTZ '2026-10-17 10:03:00+05:30', TIMESTAMPTZ '2026-10-17 10:03:10+05:30'
);

INSERT INTO portfolio_versions (
    portfolio_version_id, portfolio_id, generation_request_id, strategy_version_id,
    version_number, version_status, investment_amount, currency_code, investment_horizon_months,
    risk_category, expected_return_pct, expected_volatility_pct, diversification_score,
    market_context_as_of, generation_context
) VALUES (
    '82000000-0000-4000-8000-000000000001', '80000000-0000-4000-8000-000000000001',
    '81000000-0000-4000-8000-000000000001', '71000000-0000-4000-8000-000000000001',
    1, 'generated', 100000.00, 'INR', 72, 'moderate', 9.50, 14.25, 72.00,
    TIMESTAMPTZ '2026-10-16 15:30:00+05:30', '{"demo":true,"value_is_illustrative":true}'::jsonb
);

INSERT INTO portfolio_security_decisions (decision_id, portfolio_version_id, security_id, listing_id, decision_status, target_weight_pct, decision_reason)
VALUES
('83000000-0000-4000-8000-000000000001', '82000000-0000-4000-8000-000000000001', '50000000-0000-4000-8000-000000000001', '51000000-0000-4000-8000-000000000001', 'selected', 40.000000, 'Illustrative allocation used to demonstrate database relationships.'),
('83000000-0000-4000-8000-000000000002', '82000000-0000-4000-8000-000000000001', '50000000-0000-4000-8000-000000000002', '51000000-0000-4000-8000-000000000002', 'selected', 35.000000, 'Illustrative allocation used to demonstrate database relationships.'),
('83000000-0000-4000-8000-000000000003', '82000000-0000-4000-8000-000000000001', '50000000-0000-4000-8000-000000000003', '51000000-0000-4000-8000-000000000003', 'selected', 25.000000, 'Illustrative allocation used to demonstrate database relationships.');

INSERT INTO evidence_items (evidence_item_id, data_source_id, security_id, market_price_id,
                            evidence_type, title, evidence_summary, source_url, observed_at,
                            cited_value_snapshot)
VALUES ('90000000-0000-4000-8000-000000000001', '60000000-0000-4000-8000-000000000001',
        '50000000-0000-4000-8000-000000000001', '61000000-0000-4000-8000-000000000001',
        'market_price', 'Illustrative closing price', 'Fictional data row used only for schema testing.',
        'https://example.invalid/demo-price', TIMESTAMPTZ '2026-10-16 16:00:00+05:30',
        '{"close_price":103,"currency":"INR","illustrative":true}'::jsonb);

INSERT INTO recommendation_explanations (explanation_id, portfolio_version_id, decision_id, explanation_type, title, explanation_text, display_order)
VALUES ('91000000-0000-4000-8000-000000000001', '82000000-0000-4000-8000-000000000001',
        '83000000-0000-4000-8000-000000000001', 'selection', 'Example of a user-facing explanation',
        'This is a fictional explanation showing how text can be linked to an individual security decision.', 1);

INSERT INTO explanation_evidence (explanation_id, evidence_item_id, relationship_label)
VALUES ('91000000-0000-4000-8000-000000000001', '90000000-0000-4000-8000-000000000001', 'contextualizes');

INSERT INTO portfolio_validation_runs (validation_run_id, portfolio_version_id, rule_set_version, calculation_engine_version, validation_status, started_at, completed_at, summary)
VALUES ('92000000-0000-4000-8000-000000000001', '82000000-0000-4000-8000-000000000001',
        'demo-rules-1', 'demo-engine-1', 'passed', TIMESTAMPTZ '2026-10-17 10:03:05+05:30',
        TIMESTAMPTZ '2026-10-17 10:03:06+05:30', '{"selected_weight_total_pct":100,"illustrative_only":true}'::jsonb);

INSERT INTO portfolio_validation_results (validation_result_id, validation_run_id, rule_code, result_status, severity, result_message, details)
VALUES ('93000000-0000-4000-8000-000000000001', '92000000-0000-4000-8000-000000000001',
        'ALLOCATIONS_SUM_TO_100', 'pass', 'info', 'Illustrative selected target weights total 100%.',
        '{"weight_total_pct":100,"illustrative_only":true}'::jsonb);

COMMIT;

-- Useful demo query: show selected weights and calculated target amounts (not stored redundantly).
SELECT s.security_name, il.symbol, psd.target_weight_pct,
       round(pv.investment_amount * psd.target_weight_pct / 100, 2) AS calculated_target_amount,
       pv.currency_code
FROM portfolio_security_decisions AS psd
JOIN portfolio_versions AS pv ON pv.portfolio_version_id = psd.portfolio_version_id
JOIN securities AS s ON s.security_id = psd.security_id
LEFT JOIN instrument_listings AS il ON il.listing_id = psd.listing_id AND il.security_id = psd.security_id
WHERE pv.portfolio_version_id = '82000000-0000-4000-8000-000000000001'
  AND psd.decision_status = 'selected'
ORDER BY psd.target_weight_pct DESC;
