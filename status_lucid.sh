#!/usr/bin/env bash
# ==============================================================================
# Lucid — System & Service Status Inspector
# Provides comprehensive diagnostics of Lucid's services, database, and ports.
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}======================================================================${NC}"
echo -e "${CYAN}${BOLD}                    LUCID SYSTEM STATUS INSPECTOR                     ${NC}"
echo -e "${CYAN}${BOLD}======================================================================${NC}"

# 1. System Environment
echo -e "\n${BOLD}[1] System & Runtime Environment:${NC}"
echo -e "   OS / Arch        : $(uname -s) ($(uname -m))"
if command -v python3 >/dev/null 2>&1; then
    PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    echo -e "   Python           : ${GREEN}${PY_VER}${NC} ($(command -v python3))"
else
    echo -e "   Python           : ${RED}Not installed${NC}"
fi

if [ -f "$ROOT_DIR/.venv/bin/python" ]; then
    echo -e "   Virtualenv       : ${GREEN}Active (.venv)${NC}"
else
    echo -e "   Virtualenv       : ${YELLOW}Missing (.venv)${NC}"
fi

if command -v node >/dev/null 2>&1; then
    echo -e "   Node.js          : ${GREEN}$(node -v)${NC} ($(command -v node))"
else
    echo -e "   Node.js          : ${RED}Not installed${NC}"
fi

if command -v npm >/dev/null 2>&1; then
    echo -e "   npm              : ${GREEN}$(npm -v)${NC}"
else
    echo -e "   npm              : ${RED}Not installed${NC}"
fi

# 2. Backend Service Status
echo -e "\n${BOLD}[2] Backend API Service (Port 8000):${NC}"
BACKEND_PID=""
[ -f "$ROOT_DIR/.lucid_backend.pid" ] && BACKEND_PID=$(cat "$ROOT_DIR/.lucid_backend.pid" 2>/dev/null || true)
BACKEND_PORT_PID=$(lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null | head -n 1 || true)

BACKEND_RUNNING=0
if [ -n "$BACKEND_PORT_PID" ]; then
    HEALTH_RESP=$(curl -s -m 2 "http://localhost:8000/api/health" 2>/dev/null || true)
    if [ -n "$HEALTH_RESP" ]; then
        BACKEND_RUNNING=1
        echo -e "   Status           : ${GREEN}● RUNNING & HEALTHY${NC}"
        echo -e "   PID              : ${BACKEND_PORT_PID} (Recorded PID: ${BACKEND_PID:-none})"
        echo -e "   URL              : http://localhost:8000"
        echo -e "   Health Response  : ${CYAN}${HEALTH_RESP}${NC}"
    else
        echo -e "   Status           : ${YELLOW}● LISTENING BUT UNRESPONSIVE${NC} (PID: ${BACKEND_PORT_PID})"
    fi
else
    echo -e "   Status           : ${RED}○ STOPPED${NC} (Port 8000 is free)"
fi

# 3. Frontend Web Application (Port 3000):
echo -e "\n${BOLD}[3] Frontend Web Application (Port 3000):${NC}"
FRONTEND_PID=""
[ -f "$ROOT_DIR/.lucid_frontend.pid" ] && FRONTEND_PID=$(cat "$ROOT_DIR/.lucid_frontend.pid" 2>/dev/null || true)
FRONTEND_PORT_PID=$(lsof -i :3000 -sTCP:LISTEN -t 2>/dev/null | head -n 1 || true)

FRONTEND_RUNNING=0
if [ -n "$FRONTEND_PORT_PID" ]; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -m 2 "http://localhost:3000" 2>/dev/null || true)
    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
        FRONTEND_RUNNING=1
        echo -e "   Status           : ${GREEN}● RUNNING & READY${NC}"
        echo -e "   PID              : ${FRONTEND_PORT_PID} (Recorded PID: ${FRONTEND_PID:-none})"
        echo -e "   URL              : http://localhost:3000"
        echo -e "   HTTP Status      : ${GREEN}${HTTP_CODE} OK${NC}"
    else
        echo -e "   Status           : ${YELLOW}● STARTING / RESPONDING WITH ${HTTP_CODE}${NC} (PID: ${FRONTEND_PORT_PID})"
    fi
else
    echo -e "   Status           : ${RED}○ STOPPED${NC} (Port 3000 is free)"
fi

# 4. PostgreSQL Database Inspection
echo -e "\n${BOLD}[4] PostgreSQL Database Status & Record Counts:${NC}"
PY_EXEC="python3"
[ -f "$ROOT_DIR/.venv/bin/python" ] && PY_EXEC="$ROOT_DIR/.venv/bin/python"

DATABASE_OK=0
if [ -f "$ROOT_DIR/.env" ]; then
    DB_STATUS_OUTPUT=$(PYTHONPATH="$ROOT_DIR" "$PY_EXEC" -c "
from dotenv import load_dotenv
load_dotenv('$ROOT_DIR/.env')
try:
    from backend.database import engine
    from sqlalchemy import text
    with engine.connect() as conn:
        res_tables = conn.execute(text(\"SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'\")).scalar()
        res_sec = conn.execute(text('SELECT count(*) FROM securities')).scalar()
        res_users = conn.execute(text('SELECT count(*) FROM app_users')).scalar()
        res_macro = conn.execute(text('SELECT count(*) FROM economic_indicators')).scalar()
        print(f'OK|{res_tables}|{res_sec}|{res_users}|{res_macro}')
except Exception as e:
    print(f'ERR|{str(e)}')
" 2>&1)

    if [[ "$DB_STATUS_OUTPUT" == OK* ]]; then
        DATABASE_OK=1
        IFS='|' read -r status tables securities users macro <<< "$DB_STATUS_OUTPUT"
        echo -e "   Connection       : ${GREEN}✓ CONNECTED${NC}"
        echo -e "   Schema Tables    : ${GREEN}${tables}${NC} tables registered"
        echo -e "   Exchange Stocks  : ${GREEN}${securities}${NC} securities stored (NSE/BSE)"
        echo -e "   User Accounts    : ${GREEN}${users}${NC} user account(s)"
        echo -e "   Macro Indicators : ${GREEN}${macro}${NC} economic series registered"
    else
        echo -e "   Connection       : ${RED}✗ FAILED${NC}"
        echo -e "   Error Detail     : ${YELLOW}${DB_STATUS_OUTPUT#ERR|}${NC}"
    fi
else
    echo -e "   Configuration    : ${RED}✗ .env file missing${NC}"
fi

# 5. Overall Verdict
echo -e "\n${BOLD}======================================================================${NC}"
if [ $BACKEND_RUNNING -eq 1 ] && [ $FRONTEND_RUNNING -eq 1 ] && [ $DATABASE_OK -eq 1 ]; then
    echo -e "${GREEN}${BOLD}🟢 OVERALL STATUS: ALL SYSTEMS OPERATIONAL${NC}"
    echo -e "   Lucid is fully running and accessible at ${CYAN}http://localhost:3000${NC}"
elif [ $BACKEND_RUNNING -eq 1 ] || [ $FRONTEND_RUNNING -eq 1 ]; then
    echo -e "${YELLOW}${BOLD}🟡 OVERALL STATUS: PARTIALLY RUNNING${NC}"
    echo -e "   Run ${BOLD}./start_lucid.sh${NC} to start remaining services or resolve issues."
else
    echo -e "${RED}${BOLD}🔴 OVERALL STATUS: ALL SERVICES STOPPED${NC}"
    echo -e "   Start Lucid using: ${BOLD}./start_lucid.sh${NC}"
fi
echo -e "${BOLD}======================================================================${NC}"
