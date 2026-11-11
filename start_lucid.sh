#!/usr/bin/env bash
# ==============================================================================
# Lucid — One-Command Installation, Environment Setup & Application Launcher
# ==============================================================================
# Usage:
#   chmod +x start_lucid.sh
#   ./start_lucid.sh
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p "$ROOT_DIR/logs"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down Lucid services gracefully...${NC}"
    if [ -n "$FRONTEND_PID" ] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "   Stopping Frontend (PID: $FRONTEND_PID)..."
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    if [ -n "$BACKEND_PID" ] && kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "   Stopping Backend (PID: $BACKEND_PID)..."
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    rm -f "$ROOT_DIR/.lucid_backend.pid" "$ROOT_DIR/.lucid_frontend.pid"
    echo -e "${GREEN}👋 Lucid services stopped. PostgreSQL remains active.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo "          LUCID — ONE-COMMAND INSTALLATION & LAUNCHER"
echo "  Capturing Indian Mutual Fund Expertise via Agentic Multi-Agent AI"
echo "======================================================================"
echo -e "${NC}"

# ==============================================================================
# 1. OPERATING SYSTEM & ARCHITECTURE DETECTION
# ==============================================================================
echo -e "${BOLD}[1/10] Detecting Operating System & Architecture...${NC}"
OS_NAME="$(uname -s)"
ARCH_NAME="$(uname -m)"

case "$OS_NAME" in
    Darwin)
        if [ "$ARCH_NAME" = "arm64" ]; then
            OS_DESC="macOS (Apple Silicon)"
        else
            OS_DESC="macOS (Intel x86_64)"
        fi
        ;;
    Linux)
        OS_DESC="Linux ($ARCH_NAME)"
        ;;
    MINGW*|CYGWIN*|MSYS*)
        OS_DESC="Windows / WSL ($ARCH_NAME)"
        ;;
    *)
        OS_DESC="Unknown OS ($OS_NAME $ARCH_NAME)"
        ;;
esac

echo -e "   Operating System : ${GREEN}$OS_DESC${NC}"
echo -e "   Architecture     : ${GREEN}$ARCH_NAME${NC}"
echo -e "   Project Root     : ${BLUE}$ROOT_DIR${NC}"

# ==============================================================================
# 2. CHECK REQUIRED TOOLS & PREREQUISITES
# ==============================================================================
echo -e "\n${BOLD}[2/10] Checking Required System Tools...${NC}"

check_cmd() {
    local cmd="$1"
    local name="$2"
    if command -v "$cmd" >/dev/null 2>&1; then
        echo -e "   $name $(printf '%*s' $((25 - ${#name})) '') : ${GREEN}✓ Installed${NC} ($(command -v "$cmd"))"
        return 0
    else
        echo -e "   $name $(printf '%*s' $((25 - ${#name})) '') : ${RED}✗ Missing${NC}"
        return 1
    fi
}

MISSING_TOOLS=0
check_cmd "git" "Git" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_cmd "python3" "Python 3" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_cmd "node" "Node.js" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_cmd "npm" "npm" || MISSING_TOOLS=$((MISSING_TOOLS + 1))
check_cmd "psql" "PostgreSQL Client (psql)" || MISSING_TOOLS=$((MISSING_TOOLS + 1))

# Check VS Code & Code CLI
VS_CODE_INSTALLED=0
if command -v code >/dev/null 2>&1; then
    VS_CODE_INSTALLED=1
elif [ "$OS_NAME" = "Darwin" ]; then
    if [ -x "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
        export PATH="/Applications/Visual Studio Code.app/Contents/Resources/app/bin:$PATH"
        VS_CODE_INSTALLED=1
    elif [ -x "$HOME/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
        export PATH="$HOME/Applications/Visual Studio Code.app/Contents/Resources/app/bin:$PATH"
        VS_CODE_INSTALLED=1
    fi
fi

if [ $VS_CODE_INSTALLED -eq 1 ]; then
    echo -e "   Visual Studio Code CLI    : ${GREEN}✓ Available${NC} ($(command -v code))"
else
    echo -e "   Visual Studio Code CLI    : ${YELLOW}○ Not Found in PATH${NC}"
    if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
        echo -e "   ${CYAN}ℹ️ Attempting automatic VS Code installation via Homebrew...${NC}"
        brew install --cask visual-studio-code >/dev/null 2>&1 || true
        if [ -x "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]; then
            export PATH="/Applications/Visual Studio Code.app/Contents/Resources/app/bin:$PATH"
            VS_CODE_INSTALLED=1
            echo -e "   Visual Studio Code CLI    : ${GREEN}✓ Installed successfully${NC}"
        fi
    fi
fi

# Optional tool check
if command -v postman >/dev/null 2>&1; then
    echo -e "   Postman                   : ${GREEN}✓ Installed${NC} (Optional)"
else
    echo -e "   Postman                   : ${YELLOW}○ Optional (Not Installed)${NC}"
fi

# Auto-install missing core tools via Homebrew on macOS
if [ $MISSING_TOOLS -gt 0 ]; then
    if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
        echo -e "\n${YELLOW}⚠️ Missing required tools detected. Attempting automatic installation via Homebrew...${NC}"
        command -v python3 >/dev/null 2>&1 || brew install python@3.11
        command -v node >/dev/null 2>&1 || brew install node
        command -v psql >/dev/null 2>&1 || brew install postgresql@16
    else
        echo -e "\n${RED}❌ Missing required tools: Please install Python 3.11+, Node.js 18+, and PostgreSQL before running Lucid.${NC}"
        exit 1
    fi
fi

# Install recommended VS Code extensions in background if code CLI is available
if [ $VS_CODE_INSTALLED -eq 1 ]; then
    echo "   Configuring recommended VS Code workspace extensions in background..."
    RECOMMENDED_EXTS=(
        "ms-python.python"
        "ms-python.vscode-pylance"
        "ms-python.debugpy"
        "dbaeumer.vscode-eslint"
        "esbenp.prettier-vscode"
        "bradlc.vscode-tailwindcss"
        "ckolkman.vscode-postgres"
        "eamodio.gitlens"
        "tamasfe.even-better-toml"
        "redhat.vscode-yaml"
    )
    INSTALLED_EXTS=$(code --list-extensions 2>/dev/null || true)
    for ext in "${RECOMMENDED_EXTS[@]}"; do
        if ! echo "$INSTALLED_EXTS" | grep -qi "^${ext}$"; then
            code --install-extension "$ext" --force >/dev/null 2>&1 &
        fi
    done
fi

# Verify Python version >= 3.11
PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || ([ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 11 ]); then
    echo -e "   ${RED}❌ Python $PY_VERSION is unsupported. Lucid requires Python 3.11 or newer.${NC}"
    exit 1
fi
echo -e "   Python Version Verified   : ${GREEN}$PY_VERSION (>= 3.11)${NC}"

# ==============================================================================
# 3. PREPARE PYTHON VIRTUAL ENVIRONMENT & BACKEND DEPENDENCIES
# ==============================================================================
echo -e "\n${BOLD}[3/10] Preparing Python Virtual Environment...${NC}"

VENV_DIR="$ROOT_DIR/.venv"
REQ_FILE="$ROOT_DIR/backend/requirements.txt"
HASH_FILE="$VENV_DIR/.requirements.hash"

if [ ! -d "$VENV_DIR" ] || [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "   Creating new virtual environment at .venv..."
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel >/dev/null 2>&1
    echo -e "   ${GREEN}✅ Virtual environment created.${NC}"
else
    echo -e "   ${GREEN}✅ Reusing existing virtual environment at .venv.${NC}"
fi

CURRENT_REQ_HASH=""
if command -v md5 >/dev/null 2>&1; then
    CURRENT_REQ_HASH=$(md5 -q "$REQ_FILE" 2>/dev/null || md5sum "$REQ_FILE" | awk '{print $1}')
elif command -v md5sum >/dev/null 2>&1; then
    CURRENT_REQ_HASH=$(md5sum "$REQ_FILE" | awk '{print $1}')
fi

PREV_REQ_HASH=""
[ -f "$HASH_FILE" ] && PREV_REQ_HASH=$(cat "$HASH_FILE")

if [ "$CURRENT_REQ_HASH" != "$PREV_REQ_HASH" ] || [ ! -f "$HASH_FILE" ]; then
    echo "   Installing backend dependencies from backend/requirements.txt..."
    "$VENV_DIR/bin/pip" install -r "$REQ_FILE" > "$ROOT_DIR/logs/pip_install.log" 2>&1
    echo "$CURRENT_REQ_HASH" > "$HASH_FILE"
    echo -e "   ${GREEN}✅ Backend dependencies installed.${NC}"
else
    echo -e "   ${GREEN}✅ Backend dependencies up to date. Skipping re-installation.${NC}"
fi

# ==============================================================================
# 4. PREPARE FRONTEND DEPENDENCIES
# ==============================================================================
echo -e "\n${BOLD}[4/10] Preparing Frontend Dependencies...${NC}"

cd "$ROOT_DIR/frontend"
if [ ! -d "node_modules" ] || [ package.json -nt node_modules ]; then
    echo "   Installing frontend dependencies (Next.js & React 19)..."
    npm install --silent > "$ROOT_DIR/logs/npm_install.log" 2>&1
    echo -e "   ${GREEN}✅ Frontend dependencies installed.${NC}"
else
    echo -e "   ${GREEN}✅ Frontend dependencies up to date. Skipping re-installation.${NC}"
fi
cd "$ROOT_DIR"

# ==============================================================================
# 5. CONFIGURE ENVIRONMENT VARIABLES (.env)
# ==============================================================================
echo -e "\n${BOLD}[5/10] Validating Environment Configuration (.env)...${NC}"

ENV_FILE="$ROOT_DIR/.env"
EXAMPLE_FILE="$ROOT_DIR/.env.example"

if [ ! -f "$ENV_FILE" ]; then
    echo "   '.env' not found. Creating from .env.example..."
    cp "$EXAMPLE_FILE" "$ENV_FILE"
    
    # Auto-generate secure local JWT and App secrets
    JWT_SECRET=$("$VENV_DIR/bin/python" -c "import secrets; print(secrets.token_urlsafe(32))")
    APP_SECRET=$("$VENV_DIR/bin/python" -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Replace placeholder secrets safely
    sed -i '' "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE" 2>/dev/null || sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET/" "$ENV_FILE"
    sed -i '' "s/APP_SECRET_KEY=.*/APP_SECRET_KEY=$APP_SECRET/" "$ENV_FILE" 2>/dev/null || sed -i "s/APP_SECRET_KEY=.*/APP_SECRET_KEY=$APP_SECRET/" "$ENV_FILE"
    
    echo -e "   ${GREEN}✅ Created .env with cryptographically secure random secrets.${NC}"
else
    echo -e "   ${GREEN}✅ Preserving existing .env configuration.${NC}"
fi

# Check for Gemini API Key
GEMINI_KEY=$(grep "^GEMINI_API_KEY=" "$ENV_FILE" | cut -d= -f2- | tr -d '"' | tr -d "'")
if [ -z "$GEMINI_KEY" ] || [ "$GEMINI_KEY" = "your_gemini_api_key_here" ]; then
    if [ -t 0 ]; then
        echo ""
        echo -e "${YELLOW}🔑 Optional Google Gemini API Key:${NC}"
        echo "   Lucid uses Google Gemini 3.8 Flash for qualitative agent research."
        echo "   (If skipped, Lucid runs in fully deterministic rule-based fallback mode)."
        read -t 10 -r -p "   Enter GEMINI_API_KEY (press Enter or wait 10s to skip): " ENTERED_KEY || ENTERED_KEY=""
        if [ -n "$ENTERED_KEY" ]; then
            sed -i '' "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$ENTERED_KEY/" "$ENV_FILE" 2>/dev/null || sed -i "s/GEMINI_API_KEY=.*/GEMINI_API_KEY=$ENTERED_KEY/" "$ENV_FILE"
            echo -e "   ${GREEN}✅ Gemini API key configured.${NC}"
        else
            echo -e "   ${CYAN}ℹ️ Running with deterministic rule-based models.${NC}"
        fi
    fi
fi

# ==============================================================================
# 6. VERIFY & START POSTGRESQL SERVICE
# ==============================================================================
echo -e "\n${BOLD}[6/10] Verifying PostgreSQL Service...${NC}"

# Extract database parameters from .env
PG_HOST=$(grep "^POSTGRES_HOST=" "$ENV_FILE" | cut -d= -f2 | tr -d ' "')
PG_PORT=$(grep "^POSTGRES_PORT=" "$ENV_FILE" | cut -d= -f2 | tr -d ' "')
PG_DB=$(grep "^POSTGRES_DB=" "$ENV_FILE" | cut -d= -f2 | tr -d ' "')
PG_USER=$(grep "^POSTGRES_USER=" "$ENV_FILE" | cut -d= -f2 | tr -d ' "')

PG_HOST=${PG_HOST:-localhost}
PG_PORT=${PG_PORT:-5432}
PG_DB=${PG_DB:-portfolio_dev}
PG_USER=${PG_USER:-$(whoami)}

# Check if PostgreSQL is responding
PG_READY=0
if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "$PG_HOST" -p "$PG_PORT" >/dev/null 2>&1; then
        PG_READY=1
    fi
fi

if [ $PG_READY -eq 0 ]; then
    echo "   PostgreSQL is not responding on $PG_HOST:$PG_PORT. Attempting service start..."
    if [ "$OS_NAME" = "Darwin" ] && command -v brew >/dev/null 2>&1; then
        brew services start postgresql@16 >/dev/null 2>&1 || brew services start postgresql >/dev/null 2>&1 || true
        # Wait for readiness
        for i in {1..15}; do
            if pg_isready -h "$PG_HOST" -p "$PG_PORT" >/dev/null 2>&1; then
                PG_READY=1
                break
            fi
            sleep 1
        done
    fi
fi

if [ $PG_READY -eq 1 ]; then
    echo -e "   ${GREEN}✅ PostgreSQL server is active on $PG_HOST:$PG_PORT.${NC}"
else
    echo -e "   ${YELLOW}⚠️ Could not verify PostgreSQL automatically on $PG_HOST:$PG_PORT.${NC}"
    echo "      Attempting Python-level connection..."
fi

# ==============================================================================
# 7. INITIALIZE DATABASE, MIGRATIONS & SEED REFERENCE DATA
# ==============================================================================
echo -e "\n${BOLD}[7/10] Initializing Database, Migrations & Reference Data...${NC}"

PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/python" "$ROOT_DIR/scripts/init_database.py"

# ==============================================================================
# 8. RESOLVE PORT CONFLICTS & CLEANUP STALE PROCESSES
# ==============================================================================
echo -e "\n${BOLD}[8/10] Checking Port Availability (8000 & 3000)...${NC}"

kill_stale_process() {
    local port="$1"
    local name="$2"
    local pid_file="$3"
    
    # Check if PID file exists
    if [ -f "$pid_file" ]; then
        local old_pid=$(cat "$pid_file")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "   Stopping previous Lucid $name (PID: $old_pid)..."
            kill "$old_pid" 2>/dev/null || true
            sleep 1
        fi
        rm -f "$pid_file"
    fi

    # Check if port is still occupied
    if lsof -i :"$port" -sTCP:LISTEN -t >/dev/null 2>&1; then
        local port_pid=$(lsof -i :"$port" -sTCP:LISTEN -t | head -n 1)
        echo -e "   ${YELLOW}⚠️ Port $port occupied by process $port_pid. Releasing port...${NC}"
        kill "$port_pid" 2>/dev/null || true
        sleep 1
    fi
}

kill_stale_process 8000 "Backend" "$ROOT_DIR/.lucid_backend.pid"
kill_stale_process 3000 "Frontend" "$ROOT_DIR/.lucid_frontend.pid"
echo -e "   ${GREEN}✅ Ports 8000 and 3000 are available.${NC}"

# ==============================================================================
# 9. START BACKEND SERVER (FastAPI / Uvicorn)
# ==============================================================================
echo -e "\n${BOLD}[9/10] Starting Lucid Backend (FastAPI / Uvicorn on Port 8000)...${NC}"

cd "$ROOT_DIR"
PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/uvicorn" backend.main:app --host 0.0.0.0 --port 8000 > "$ROOT_DIR/logs/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$ROOT_DIR/.lucid_backend.pid"

# Wait for backend health check
echo "   Waiting for Backend API readiness (http://localhost:8000/api/health)..."
BACKEND_HEALTHY=0
for i in {1..30}; do
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo -e "   ${RED}❌ Backend process exited prematurely. Showing last 20 log lines:${NC}"
        tail -n 20 "$ROOT_DIR/logs/backend.log"
        exit 1
    fi

    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/health" 2>/dev/null || true)
    if [ "$STATUS_CODE" = "200" ]; then
        BACKEND_HEALTHY=1
        break
    fi
    sleep 1
done

if [ $BACKEND_HEALTHY -eq 1 ]; then
    echo -e "   ${GREEN}✅ Backend API is healthy and listening on http://localhost:8000.${NC}"
else
    echo -e "   ${RED}❌ Backend failed to pass health check within 30 seconds.${NC}"
    tail -n 25 "$ROOT_DIR/logs/backend.log"
    cleanup
    exit 1
fi

# ==============================================================================
# 10. START FRONTEND SERVER (Next.js on Port 3000)
# ==============================================================================
echo -e "\n${BOLD}[10/10] Starting Lucid Frontend (Next.js / React 19 on Port 3000)...${NC}"

cd "$ROOT_DIR/frontend"
npm run dev > "$ROOT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!
cd "$ROOT_DIR"
echo "$FRONTEND_PID" > "$ROOT_DIR/.lucid_frontend.pid"

echo "   Waiting for Frontend readiness (http://localhost:3000)..."
FRONTEND_HEALTHY=0
for i in {1..30}; do
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo -e "   ${RED}❌ Frontend process exited prematurely. Showing last 20 log lines:${NC}"
        tail -n 20 "$ROOT_DIR/logs/frontend.log"
        cleanup
        exit 1
    fi

    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3000" 2>/dev/null || true)
    if [ "$STATUS_CODE" = "200" ] || [ "$STATUS_CODE" = "304" ]; then
        FRONTEND_HEALTHY=1
        break
    fi
    sleep 1
done

if [ $FRONTEND_HEALTHY -eq 1 ]; then
    echo -e "   ${GREEN}✅ Frontend is ready and listening on http://localhost:3000.${NC}"
    
    # Run End-to-End System Verification
    echo -e "
${BOLD}[+] Executing End-to-End System Verification...${NC}"
    PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/python" "$ROOT_DIR/scripts/verify_e2e.py" || true
else
    echo -e "   ${RED}❌ Frontend failed to pass readiness check within 30 seconds.${NC}"
    tail -n 25 "$ROOT_DIR/logs/frontend.log"
    cleanup
    exit 1
fi

# ==============================================================================
# LAUNCH COMPLETE & READY TO USE
# ==============================================================================
echo ""
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo -e "${GREEN}${BOLD}                    🎉 LUCID IS RUNNING & READY!                     ${NC}"
echo -e "${GREEN}${BOLD}======================================================================${NC}"
echo ""
echo -e "  ${BOLD}Investor Frontend:${NC}            ${CYAN}http://localhost:3000${NC}"
echo -e "  ${BOLD}Backend REST API:${NC}             ${CYAN}http://localhost:8000${NC}"
echo -e "  ${BOLD}Interactive Swagger Docs:${NC}     ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  ${BOLD}OpenAPI Schema:${NC}               ${CYAN}http://localhost:8000/openapi.json${NC}"
echo -e "  ${BOLD}PostgreSQL Database:${NC}          ${CYAN}$PG_HOST:$PG_PORT/$PG_DB${NC}"
echo ""
echo -e "  ${BOLD}Default Demo Credentials:${NC}"
echo -e "    Email    : ${YELLOW}developer@lucid.local${NC}"
echo -e "    Password : ${YELLOW}LucidDevPass123!${NC}"
echo ""
echo -e "  ${BOLD}Process IDs:${NC} Backend (PID: $BACKEND_PID) | Frontend (PID: $FRONTEND_PID)"
echo -e "  ${BOLD}Logs:${NC}        tail -f logs/backend.log | tail -f logs/frontend.log"
echo ""
echo -e "${CYAN}Opening Lucid in your default web browser...${NC}"

# Open browser automatically
if [ "$OS_NAME" = "Darwin" ]; then
    open "http://localhost:3000" >/dev/null 2>&1 || true
elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:3000" >/dev/null 2>&1 || true
elif command -v start >/dev/null 2>&1; then
    start "http://localhost:3000" >/dev/null 2>&1 || true
fi

# Open VS Code workspace automatically if code is available
if command -v code >/dev/null 2>&1; then
    echo -e "${CYAN}Opening Lucid workspace in Visual Studio Code...${NC}"
    code "$ROOT_DIR" >/dev/null 2>&1 || true
fi

echo -e "${BOLD}======================================================================${NC}"
echo -e "Press ${RED}${BOLD}[Ctrl+C]${NC} at any time to stop Lucid services."
echo -e "${BOLD}======================================================================${NC}"

# Wait indefinitely for signal
wait
