#!/usr/bin/env bash
# ==============================================================================
# Lucid — Development Database Restore Utility
# ==============================================================================
# Restores a gzipped SQL dump into the 'majorproject' database.
# Requires explicit confirmation before overwriting development data.
# ==============================================================================

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "${BACKUP_FILE}" ]; then
    echo "❌ Error: Backup file not found: ${BACKUP_FILE}"
    exit 1
fi

DB_NAME="${POSTGRES_DB:-majorproject}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

echo "================================================================="
echo "⚠️  CAUTION: Restoring database '${DB_NAME}'"
echo "   File: ${BACKUP_FILE}"
echo "   Host: ${DB_HOST}:${DB_PORT} | User: ${DB_USER}"
echo "================================================================="
read -p "Are you sure you want to restore and overwrite data in '${DB_NAME}'? (y/N): " -r CONFIRM
if [[ ! "${CONFIRM}" =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo "Restoring database from compressed backup..."
gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"

echo "================================================================="
echo "✅ Database restored successfully!"
echo "================================================================="

