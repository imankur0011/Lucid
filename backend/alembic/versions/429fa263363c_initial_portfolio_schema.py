"""initial_portfolio_schema

Revision ID: 429fa263363c
Revises: 
Create Date: 2026-10-17 18:55:23.934396

"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '429fa263363c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: executes the authoritative DDL scripts to create all 59 tables."""
    # Resolve app root directory (4 levels up from this version file)
    app_dir = Path(__file__).resolve().parent.parent.parent.parent
    pkg_dir = app_dir / "portfolio_database_design_package"

    core_sql_file = pkg_dir / "portfolio_creation_schema.sql"
    opt_sql_file = pkg_dir / "portfolio_optional_extensions.sql"

    if not core_sql_file.exists():
        raise FileNotFoundError(f"Core schema file not found at: {core_sql_file}")
    if not opt_sql_file.exists():
        raise FileNotFoundError(f"Optional extensions file not found at: {opt_sql_file}")

    bind = op.get_bind()
    raw_conn = bind.connection.dbapi_connection
    cursor = raw_conn.cursor()

    cursor.execute(core_sql_file.read_text(encoding="utf-8"))
    cursor.execute(opt_sql_file.read_text(encoding="utf-8"))

    raw_conn.commit()


def downgrade() -> None:
    """Downgrade schema: drops all tables in reverse dependency order."""
    tables_to_drop = [
        "portfolio_performance_snapshots",
        "broker_executions",
        "broker_order_events",
        "broker_orders",
        "user_broker_accounts",
        "broker_providers",
        "audit_events",
        "notifications",
        "user_feedback",
        "knowledge_documents",
        "agent_execution_runs",
        "agent_versions",
        "agent_definitions",
        "rebalance_suggestions",
        "portfolio_diagnoses",
        "existing_portfolio_holdings",
        "existing_portfolios",
        "portfolio_scenarios",
        "portfolio_validation_results",
        "portfolio_validation_runs",
        "explanation_evidence",
        "recommendation_explanations",
        "evidence_items",
        "portfolio_version_constraints",
        "portfolio_security_decisions",
        "portfolio_versions",
        "strategy_versions",
        "strategy_definitions",
        "portfolio_generation_requests",
        "investor_portfolios",
        "news_article_securities",
        "market_news_articles",
        "economic_observations",
        "economic_indicators",
        "fundamental_metrics",
        "metric_definitions",
        "market_prices",
        "source_instrument_mappings",
        "data_ingestion_errors",
        "data_ingestion_runs",
        "data_sources",
        "user_security_preferences",
        "user_sector_preferences",
        "instrument_listings",
        "securities",
        "company_industries",
        "industries",
        "sectors",
        "exchanges",
        "companies",
        "risk_assessment_answers",
        "risk_assessments",
        "risk_question_options",
        "risk_questions",
        "financial_goals",
        "user_consents",
        "user_preferences",
        "user_profile_versions",
        "user_verification_codes",
        "revoked_tokens",
        "user_profiles",
        "app_users",
    ]
    for table in tables_to_drop:
        op.execute(sa.text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_updated_at_timestamp() CASCADE;"))
    op.execute(sa.text("DROP FUNCTION IF EXISTS set_optional_updated_at_timestamp() CASCADE;"))
