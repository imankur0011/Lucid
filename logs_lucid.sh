#!/usr/bin/env bash
# ==============================================================================
# Lucid — Log Inspection and Streaming Utility
# Streams or displays service logs for Backend, Frontend, and Installation tasks.
# ==============================================================================

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

TARGET="${1:-all}"
LINES="${2:-50}"

# Handle numeric first argument (e.g., ./logs_lucid.sh 100)
if [[ "$TARGET" =~ ^[0-9]+$ ]]; then
    LINES="$TARGET"
    TARGET="all"
fi

show_help() {
    echo -e "${CYAN}${BOLD}Lucid Log Inspector${NC}"
    echo "Usage: ./logs_lucid.sh [target] [lines]"
    echo ""
    echo "Targets:"
    echo "  backend    Tail backend FastAPI/Uvicorn server logs (logs/backend.log)"
    echo "  frontend   Tail frontend Next.js server logs (logs/frontend.log)"
    echo "  all        Tail both backend and frontend logs concurrently (default)"
    echo "  pip        View Python pip installation log (logs/pip_install.log)"
    echo "  npm        View Node npm installation log (logs/npm_install.log)"
    echo "  clear      Clear/truncate all log files in logs/"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./logs_lucid.sh backend"
    echo "  ./logs_lucid.sh frontend 100"
    echo "  ./logs_lucid.sh clear"
    exit 0
}

case "$TARGET" in
    backend|api)
        echo -e "${CYAN}${BOLD}==> Streaming Lucid Backend Logs (logs/backend.log)...${NC}"
        touch "$LOG_DIR/backend.log"
        tail -n "$LINES" -f "$LOG_DIR/backend.log"
        ;;
    frontend|web)
        echo -e "${CYAN}${BOLD}==> Streaming Lucid Frontend Logs (logs/frontend.log)...${NC}"
        touch "$LOG_DIR/frontend.log"
        tail -n "$LINES" -f "$LOG_DIR/frontend.log"
        ;;
    pip|python)
        echo -e "${CYAN}${BOLD}==> Python Pip Installation Log (logs/pip_install.log):${NC}"
        if [ -f "$LOG_DIR/pip_install.log" ]; then
            tail -n "$LINES" "$LOG_DIR/pip_install.log"
        else
            echo "No pip_install.log found."
        fi
        ;;
    npm|node)
        echo -e "${CYAN}${BOLD}==> Frontend NPM Installation Log (logs/npm_install.log):${NC}"
        if [ -f "$LOG_DIR/npm_install.log" ]; then
            tail -n "$LINES" "$LOG_DIR/npm_install.log"
        else
            echo "No npm_install.log found."
        fi
        ;;
    clear|clean)
        echo -e "${YELLOW}Truncating all log files in $LOG_DIR...${NC}"
        for f in "$LOG_DIR"/*.log; do
            [ -f "$f" ] && : > "$f"
        done
        echo -e "${GREEN}✓ All log files cleared.${NC}"
        ;;
    help|--help|-h)
        show_help
        ;;
    all|*)
        echo -e "${CYAN}${BOLD}==> Streaming Lucid Backend & Frontend Logs Concurrently...${NC}"
        touch "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
        tail -n "$LINES" -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log"
        ;;
esac

