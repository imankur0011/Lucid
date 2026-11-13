#!/usr/bin/env bash
# ==============================================================================
# Lucid — Complete Application Teardown & Clean-Slate Reset
# Stops running services, drops PostgreSQL database, removes .venv, node_modules,
# .next, .env, and logs, returning the environment to a 100% pristine state.
# ==============================================================================

set -e

# Target directory
if [ -d "$HOME/Lucid" ]; then
    LUCID_DIR="$HOME/Lucid"
else
    LUCID_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}======================================================================${NC}"
echo -e "${RED}${BOLD}             LUCID — COMPLETE TEARDOWN & CLEAN-SLATE RESET            ${NC}"
echo -e "${RED}${BOLD}======================================================================${NC}"

# 1. Stop Services
echo -e "\n${BOLD}[1/5] Stopping all Lucid services...${NC}"
if [ -f "$LUCID_DIR/stop_lucid.sh" ]; then
    bash "$LUCID_DIR/stop_lucid.sh" 2>/dev/null || true
fi
# Force kill ports 8000 and 3000
for port in 8000 3000; do
    if command -v lsof >/dev/null 2>&1; then
        pids=$(lsof -i :"$port" -sTCP:LISTEN -t 2>/dev/null || true)
        [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    elif command -v fuser >/dev/null 2>&1; then
        fuser -k "$port/tcp" 2>/dev/null || true
    fi
done
echo -e "   ${GREEN}✓ Processes stopped and ports 8000/3000 cleared.${NC}"

# 2. Drop PostgreSQL Database
echo -e "\n${BOLD}[2/5] Dropping PostgreSQL database 'portfolio_dev'...${NC}"
DROP_SQL="SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'portfolio_dev'; DROP DATABASE IF EXISTS portfolio_dev;"

if command -v psql >/dev/null 2>&1; then
    sudo -u postgres psql -c "$DROP_SQL" >/dev/null 2>&1 || \
    sudo -n -u postgres psql -c "$DROP_SQL" >/dev/null 2>&1 || \
    psql -U postgres -h 127.0.0.1 -c "$DROP_SQL" >/dev/null 2>&1 || \
    psql -U "$(whoami)" -h 127.0.0.1 -c "$DROP_SQL" >/dev/null 2>&1 || \
    psql -d postgres -c "$DROP_SQL" >/dev/null 2>&1 || true
    echo -e "   ${GREEN}✓ Database 'portfolio_dev' dropped.${NC}"
else
    echo -e "   ${YELLOW}ℹ️ psql not found; skipping database drop.${NC}"
fi

# 3. Clean Python Virtual Environment
echo -e "\n${BOLD}[3/5] Cleaning Python virtual environment...${NC}"
rm -rf "$LUCID_DIR/.venv" "$LUCID_DIR/.pytest_cache"
find "$LUCID_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo -e "   ${GREEN}✓ .venv and Python cache removed.${NC}"

# 4. Clean Frontend Dependencies & Next.js Build
echo -e "\n${BOLD}[4/5] Cleaning Frontend node_modules & build artifacts...${NC}"
rm -rf "$LUCID_DIR/frontend/node_modules" "$LUCID_DIR/frontend/.next"
echo -e "   ${GREEN}✓ frontend/node_modules and frontend/.next removed.${NC}"

# 5. Clean Environment & Logs
echo -e "\n${BOLD}[5/5] Removing .env configuration, logs, and PID files...${NC}"
rm -f "$LUCID_DIR/.env" "$LUCID_DIR/.lucid_backend.pid" "$LUCID_DIR/.lucid_frontend.pid"
rm -rf "$LUCID_DIR/logs"/*.log 2>/dev/null || true
echo -e "   ${GREEN}✓ .env and log files removed.${NC}"

echo -e "\n${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 Clean-slate reset complete! System is completely pristine.${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "\nTo test the fresh one-command installation from scratch, run:"
echo -e "${CYAN}${BOLD}curl -fsSL https://raw.githubusercontent.com/imankur0011/Lucid/main/bootstrap_lucid.sh | bash${NC}"
echo ""
