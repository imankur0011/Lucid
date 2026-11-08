-- ==============================================================================
-- Lucid — PostgreSQL Database Initialization Script
-- ==============================================================================
-- Usage:
--   psql -U postgres -f database/create_database.sql
-- ==============================================================================

-- 1. Create development database if not exists
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'majorproject') THEN
      PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE majorproject');
   END IF;
END
$$;

-- Alternative direct execution:
-- CREATE DATABASE majorproject;

-- 2. Connect to the majorproject database
\c majorproject;

-- 3. Required Extensions
-- pgcrypto provides gen_random_uuid() for standard UUID primary keys
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 4. Verification Query
SELECT 
    current_database() AS database_name,
    current_user AS database_user,
    version() AS postgresql_version;

