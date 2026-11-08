#!/usr/bin/env bash
# ==============================================================================
# Lucid — Service Stop Script
# Gracefully terminates Lucid Backend and Frontend services.
# ==============================================================================

set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}======================================================================${NC}"
echo -e "${CYAN}${BOLD}                    LUCID SERVICE STOP UTILITY                        ${NC}"
echo -e "${CYAN}${BOLD}======================================================================${NC}"

stopped_anything=0

stop_by_pid_file() {
    local service_name="$1"
    local pid_file="$2"

    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file" 2>/dev/null || true)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            echo -e "   Stopping ${service_name} (PID: ${pid})..."
            kill "$pid" 2>/dev/null || true
            
            # Wait up to 5 seconds for process termination
            for _ in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    break
                fi
                sleep 1
            done

            # Force kill if still lingering
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "   ${YELLOW}Force terminating lingering ${service_name} (PID: ${pid})...${NC}"
                kill -9 "$pid" 2>/dev/null || true
            fi
            echo -e "   ${GREEN}✓ ${service_name} stopped.${NC}"
            stopped_anything=1
        fi
        rm -f "$pid_file"
    fi
}

stop_by_port() {
    local service_name="$1"
    local port="$2"

    local port_pids=""
    if command -v lsof >/dev/null 2>&1; then
        port_pids=$(lsof -i :"$port" -sTCP:LISTEN -t 2>/dev/null || true)
    elif command -v fuser >/dev/null 2>&1; then
        port_pids=$(fuser "$port/tcp" 2>/dev/null || true)
    fi

    if [ -n "$port_pids" ]; then
        for pid in $port_pids; do
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "   Releasing port ${port} (PID: ${pid} - ${service_name})..."
                kill "$pid" 2>/dev/null || true
                sleep 1
                if kill -0 "$pid" 2>/dev/null; then
                    kill -9 "$pid" 2>/dev/null || true
                fi
                echo -e "   ${GREEN}✓ Port ${port} released.${NC}"
                stopped_anything=1
            fi
        done
    fi
}

echo -e "\n${BOLD}[1/2] Terminating Lucid Processes by PID file...${NC}"
stop_by_pid_file "Lucid Frontend" "$ROOT_DIR/.lucid_frontend.pid"
stop_by_pid_file "Lucid Backend" "$ROOT_DIR/.lucid_backend.pid"

echo -e "\n${BOLD}[2/2] Checking Ports 8000 and 3000 for Remaining Listeners...${NC}"
stop_by_port "FastAPI Backend" 8000
stop_by_port "Next.js Frontend" 3000

echo ""
if [ $stopped_anything -eq 1 ]; then
    echo -e "${GREEN}${BOLD}✅ All Lucid application services have been stopped successfully.${NC}"
else
    echo -e "${YELLOW}ℹ️ No running Lucid services were found on ports 8000 or 3000.${NC}"
fi

echo -e "${CYAN}Note: PostgreSQL database server remains untouched and running.${NC}"
echo -e "${BOLD}======================================================================${NC}"
