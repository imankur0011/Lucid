# Intelligent Portfolio Creation — Database Package

**Backend target:** Python + FastAPI + LangGraph  
**Database:** PostgreSQL 14+  
**Persistence layer recommendation:** SQLAlchemy 2.x + Alembic

## Files in this package

- `merged_database_design_specification.md` — the combined design brief created by merging the two supplied prompts and aligning it with Python/FastAPI.
- `portfolio_database_design.md` — the detailed schema document: scope, 53-table core inventory, every core-table column, types, keys, defaults, constraints, indexes, relationship map, normalization rationale, Mermaid ER diagrams, and SQL query examples.
- `portfolio_creation_schema.sql` — core PostgreSQL DDL for the first application database.
- `portfolio_optional_extensions.sql` — separate optional broker/order/execution and portfolio-performance tables. Apply only if those features are approved.
- `portfolio_schema_demo.sql` — fictional demo data and an example query. Values and entities are not real market recommendations.
- `validate_schema.py` — a lightweight static checker for table/column/FK/index references, basic quote/parenthesis balance, and demo INSERT columns. This is not a substitute for running the SQL on PostgreSQL.

## Recommended local setup

1. Install and run PostgreSQL 14 or later on your Mac.
2. Create a new, empty development database:

   ```bash
   createdb portfolio_dev
   ```

3. Apply the core schema:

   ```bash
   psql -v ON_ERROR_STOP=1 -d portfolio_dev -f portfolio_creation_schema.sql
   ```

4. Add the fictional test data:

   ```bash
   psql -v ON_ERROR_STOP=1 -d portfolio_dev -f portfolio_schema_demo.sql
   ```

5. Run the demonstration query at the end of the seed script; it shows the selected securities and calculates target amounts from stored weights.
6. Only if broker integrations or performance history become part of the approved scope, apply the optional extension after the core DDL:

   ```bash
   psql -v ON_ERROR_STOP=1 -d portfolio_dev -f portfolio_optional_extensions.sql
   ```

Run these commands from the directory containing the files, or provide their full paths. The SQL files are intended for a **fresh development database**. Do not run them against a database containing valuable data without reviewing and adapting them as a migration.

## Validation status and limitations

Static checks currently report **53 core tables, 482 core columns, 6 optional tables, 55 optional columns, and no missing foreign-key/index references**. The 25 demo `INSERT` statements refer to columns present in the schema. Parentheses and quoted-string balance checks pass.

A PostgreSQL server was not available in the build environment, so the DDL has **not** been executed against a live PostgreSQL instance here. Execute the commands above locally with `ON_ERROR_STOP=1`, review any server errors, and keep future changes in Alembic migrations. Before production, add automated constraint tests, access-control checks, backup/restore testing, and review account-deletion/retention rules.

## Important implementation rules

- Use a least-privileged PostgreSQL role for FastAPI; do not connect as a database superuser.
- Keep production PostgreSQL private and use TLS.
- Store passwords and API/broker credentials in an identity provider or secret manager, not in this schema.
- Enforce user ownership checks on every API operation.
- Validate the sum of selected portfolio weights across all rows in the transaction before accepting/releasing a version; a row-level `CHECK` cannot enforce this aggregate rule.
- Treat recommendations, manually reported holdings, broker orders and executions as distinct concepts.
- Save user-facing explanations and evidence; do not persist unrestricted hidden chain-of-thought.
- Respect market-data and news-provider storage/redistribution licensing.
