# Lucid — PostgreSQL Database Architecture & Developer Setup Guide

**Authoritative Database Version:** PostgreSQL 16+  
**Target Codebase:** `/backend/models/` and `/backend/database/`  
**Relational Scale:** 62 Tables, 565 Columns, 102 Foreign Keys across 8 Functional Domains  

---

## 1. Overview & Architectural Role

PostgreSQL is the **exclusive relational source of truth** for Lucid. All application state—including user identity, SEBI investor risk questionnaires, the full NSE/BSE security master (2,639 securities), historical market prices, LangGraph multi-agent execution telemetry, portfolio versions, integer share allocations, and audit logs—is strictly persisted here.

> [!NOTE]
> Neo4j and Redis are configured in `backend/config.py` for potential future extensions, but **neither is in the active runtime path**. A standard PostgreSQL 16 instance is all that is required to run Lucid.

---

## 2. PostgreSQL Installation by Operating System

### 2.1 macOS (Homebrew — Recommended)
```bash
# 1. Install PostgreSQL 16
brew install postgresql@16

# 2. Start PostgreSQL service
brew services start postgresql@16

# 3. Verify installation
psql --version
pg_isready
```

### 2.2 Linux (Ubuntu / Debian)
```bash
# 1. Install PostgreSQL 16
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 2. Start and enable service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 3. Verify status
sudo -u postgres pg_isready
```

### 2.3 Windows
Download and run the official interactive installer from [EnterpriseDB PostgreSQL](https://www.postgresql.org/download/windows/) and ensure the `psql` command-line tools are added to your System `PATH`.

---

## 3. Database & Schema Initialization

### Step 3.1: Create the Database & User
Run the automated SQL script or execute via `psql`:

```bash
# Method A: Using the provided SQL script
psql -U postgres -f database/create_database.sql

# Method B: Direct terminal commands
createdb majorproject
# Or inside psql:
# CREATE DATABASE majorproject;
```

### Step 3.2: Run Alembic Database Migrations
Lucid manages its 62 relational tables using Alembic:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```
*Expected Output:* Applies migrations up to head, creating all 62 relational tables.

---

## 4. Reference Data Seeding & Security Universe Synchronization

To populate the SEBI risk assessment questionnaire, economic indicators, and the full NSE/BSE equity universe:

```bash
# From the project root:
python database/seed_reference_data.py
```

### What this command does:
1. **SEBI Psychometric Questionnaire**: Populates standardized risk capacity and loss tolerance questions with weighted options.
2. **Economic Indicators**: Seeds the RBI Repo Rate (6.50%), CPI Inflation (5.10%), India VIX, and market baseline news.
3. **Full Exchange Security Master**: Synchronizes 2,632 equities from official NSE `EQUITY_L.csv`, linking ISINs, company profiles, and trading series.
4. **Development Sandbox User**: Creates `developer@lucid.local` (Password: `LucidDevPass123!`).

---

## 5. Verification Queries

Open the `psql` shell to verify your database state:

```bash
psql -U postgres -d majorproject
```

Execute the following verification query:

```sql
SELECT 
    (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE') AS total_tables,
    (SELECT count(*) FROM companies) AS total_companies,
    (SELECT count(*) FROM securities) AS total_securities,
    (SELECT count(*) FROM instrument_listings) AS total_listings,
    (SELECT count(*) FROM risk_questions) AS total_risk_questions;
```

### Expected Output:
| total_tables | total_companies | total_securities | total_listings | total_risk_questions |
|---|---|---|---|---|
| **62** | **2,639** | **2,639** | **2,715** | **10** |

---

## 6. Backup, Restore & Safe Development Reset

### 6.1 Creating a Development Backup
Exports a sanitized SQL dump excluding ephemeral session tokens:
```bash
./database/backup.sh
```
The backup is saved to `database/backups/lucid_dev_backup_<timestamp>.sql.gz`.

### 6.2 Restoring from Backup
```bash
./database/restore.sh database/backups/lucid_dev_backup_<timestamp>.sql.gz
```

### 6.3 Safe Database Reset (Development Only)
> [!CAUTION]
> This drops all tables in the `majorproject` database. Run only in local development.

```bash
cd backend
source .venv/bin/activate

# 1. Downgrade all migrations to clean state
alembic downgrade base

# 2. Re-apply all migrations
alembic upgrade head

# 3. Re-seed reference data and security master
python ../database/seed_reference_data.py
```
