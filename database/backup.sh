#!/usr/bin/env bash
# ==============================================================================
# Lucid — Development Database Backup Utility
# ==============================================================================
# Exports a clean, sanitized PostgreSQL dump of the 'majorproject' database.
# Excludes revoked session tokens and temporary verification codes.
# ==============================================================================

set -euo pipefail

DB_NAME="${POSTGRES_DB:-majorproject}"
DB_USER="${POSTGRES_USER:-postgres}"
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/backups"
BACKUP_FILE="${BACKUP_DIR}/lucid_dev_backup_${TIMESTAMP}.sql.gz"

mkdir -p "${BACKUP_DIR}"

echo "================================================================="
echo "📦 Exporting Lucid Development Database: ${DB_NAME}"
echo "   Host: ${DB_HOST}:${DB_PORT} | User: ${DB_USER}"
echo "================================================================="

# Export database excluding ephemeral session tables
pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    --exclude-table-data='revoked_tokens' \
    --exclude-table-data='user_verification_codes' \
    --no-owner --no-acl "${DB_NAME}" | gzip > "${BACKUP_FILE}"

echo "✅ Backup successfully created at:"
echo "   ${BACKUP_FILE}"
echo "   Size: $(du -h "${BACKUP_FILE}" | cut -f1)"
echo "================================================================="
