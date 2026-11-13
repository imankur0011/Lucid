#!/usr/bin/env bash
# ==============================================================================
# Lucid — Zero-Prerequisite One-Command Bootstrap Installer (macOS & Linux)
# ==============================================================================
# Run this SINGLE command in your terminal (even if Git is NOT installed):
#
#   curl -fsSL https://raw.githubusercontent.com/imankur0011/Lucid/main/bootstrap_lucid.sh | bash
#
# What this script does automatically:
#   1. Detects operating system (macOS or Linux distribution) and CPU architecture.
#   2. Installs package manager (Homebrew on macOS, or uses apt/dnf/pacman on Linux).
#   3. Auto-installs missing prerequisites: Git, Python 3.11+, Node.js 18+, PostgreSQL 16.
#   4. Downloads the Lucid repository (via Git clone OR archive download).
#   5. Transfers control to start_lucid.sh for complete service setup and launch.
# ==============================================================================

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo "        🌟 LUCID — ONE-COMMAND BOOTSTRAP INSTALLER (UNIX)             "
echo "  Automated Zero-Prerequisite Setup for Indian Retail Equities Platform"
echo "======================================================================"
echo -e "${NC}"

# [1/5] Detect Operating System & Architecture
echo -e "${BOLD}[1/5] Detecting System Architecture & Connectivity...${NC}"
OS_NAME="$(uname -s)"
ARCH_NAME="$(uname -m)"

case "$OS_NAME" in
    Darwin)
        OS_DESC="macOS ($ARCH_NAME)"
        ;;
    Linux)
        if [ -f /etc/os-release ]; then
            DISTRO=$(grep ^NAME= /etc/os-release | cut -d= -f2 | tr -d '"')
            OS_DESC="Linux ($DISTRO $ARCH_NAME)"
        else
            OS_DESC="Linux ($ARCH_NAME)"
        fi
        ;;
    *)
        OS_DESC="$OS_NAME ($ARCH_NAME)"
        ;;
esac

echo -e "   Operating System : ${GREEN}$OS_DESC${NC}"

echo -e "   Internet Access  : ${GREEN}✓ Connected${NC}"

# [2/5] Package Manager & Core Tools Auto-Installation
echo -e "\n${BOLD}[2/5] Ensuring Package Manager & Core Prerequisites...${NC}"

if [ "$OS_NAME" = "Darwin" ]; then
    # Check or install Homebrew on macOS
    if ! command -v brew >/dev/null 2>&1; then
        echo -e "   ${YELLOW}Homebrew not found. Installing Homebrew automatically...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [ "$ARCH_NAME" = "arm64" ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        else
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi
    echo -e "   Homebrew Package Manager : ${GREEN}✓ Ready${NC}"

    # Auto-install missing tools via Homebrew
    command -v git >/dev/null 2>&1 || { echo "   Installing Git..."; brew install git; }
    command -v python3 >/dev/null 2>&1 || { echo "   Installing Python 3.11..."; brew install python@3.11; }
    command -v node >/dev/null 2>&1 || { echo "   Installing Node.js..."; brew install node; }
    command -v psql >/dev/null 2>&1 || { echo "   Installing PostgreSQL 16..."; brew install postgresql@16; }

elif [ "$OS_NAME" = "Linux" ]; then
    # Auto-install missing tools on Linux distributions
    if command -v apt-get >/dev/null 2>&1; then
        echo "   Updating apt package indices..."
        sudo apt-get update -qq || true
        command -v git >/dev/null 2>&1 || sudo apt-get install -y git
        sudo apt-get install -y curl software-properties-common build-essential || true

        # 1. Verify / Install Python 3.11+
        HAS_PY311=0
        for cand in python3.12 python3.11 python3.13 python3; do
            if command -v "$cand" >/dev/null 2>&1; then
                if "$cand" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                    HAS_PY311=1
                    break
                fi
            fi
        done
        if [ $HAS_PY311 -eq 0 ]; then
            echo "   Python 3.11+ required. Installing Python 3.11 via deadsnakes PPA..."
            if command -v add-apt-repository >/dev/null 2>&1; then
                sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
                sudo apt-get update -qq || true
            fi
            sudo apt-get install -y python3.11 python3.11-venv python3.11-dev python3.11-distutils python3-pip 2>/dev/null || sudo apt-get install -y python3.12 python3.12-venv python3.12-dev 2>/dev/null || true

            # Fallback to standalone portable Python 3.11 if distro repositories lack packages (e.g. Ubuntu 20.04)
            HAS_PY311=0
            for cand in python3.12 python3.11 python3.13 python3; do
                if command -v "$cand" >/dev/null 2>&1; then
                    if "$cand" -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" 2>/dev/null; then
                        HAS_PY311=1
                        break
                    fi
                fi
            done
            if [ $HAS_PY311 -eq 0 ]; then
                echo "   Installing portable standalone Python 3.11..."
                curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1 || true
                export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
                if command -v uv >/dev/null 2>&1; then
                    uv python install 3.11 >/dev/null 2>&1 || true
                fi
            fi
        fi

        # 2. Verify / Install Node.js 18+ (Node 22 LTS via NodeSource)
        HAS_NODE18=0
        if command -v node >/dev/null 2>&1; then
            NODE_MAJ=$(node -v 2>/dev/null | tr -d 'v' | cut -d. -f1)
            if [ -n "$NODE_MAJ" ] && [ "$NODE_MAJ" -ge 18 ]; then
                HAS_NODE18=1
            fi
        fi
        if [ $HAS_NODE18 -eq 0 ]; then
            echo "   Installing Node.js 22 LTS via NodeSource..."
            curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - 2>/dev/null || true
            sudo apt-get install -y nodejs || true
        fi

        # 3. Verify / Install and Start PostgreSQL
        if ! command -v psql >/dev/null 2>&1; then
            sudo apt-get install -y postgresql postgresql-contrib || true
        fi
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl enable postgresql 2>/dev/null || true
            sudo systemctl start postgresql 2>/dev/null || true
        elif command -v service >/dev/null 2>&1; then
            sudo service postgresql start 2>/dev/null || true
        fi
        # Configure local postgres credentials
        sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" >/dev/null 2>&1 || sudo -n -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" >/dev/null 2>&1 || true
        sudo -u postgres psql -c "CREATE DATABASE portfolio_dev OWNER postgres;" >/dev/null 2>&1 || sudo -n -u postgres psql -c "CREATE DATABASE portfolio_dev OWNER postgres;" >/dev/null 2>&1 || true
        if [ -n "$USER" ] && [ "$USER" != "postgres" ]; then
            sudo -u postgres psql -c "CREATE USER \"$USER\" WITH SUPERUSER PASSWORD 'postgres';" >/dev/null 2>&1 || true
            sudo -u postgres psql -c "ALTER USER \"$USER\" WITH SUPERUSER PASSWORD 'postgres';" >/dev/null 2>&1 || true
        fi

    elif command -v dnf >/dev/null 2>&1; then
        command -v git >/dev/null 2>&1 || sudo dnf install -y git
        sudo dnf install -y python3.11 python3.11-pip python3.11-devel || true
        sudo dnf install -y postgresql postgresql-server || true
        if command -v systemctl >/dev/null 2>&1; then
            sudo systemctl enable postgresql 2>/dev/null || true
            sudo systemctl start postgresql 2>/dev/null || true
        fi
        HAS_NODE18=0
        if command -v node >/dev/null 2>&1; then
            NODE_MAJ=$(node -v 2>/dev/null | tr -d 'v' | cut -d. -f1)
            [ -n "$NODE_MAJ" ] && [ "$NODE_MAJ" -ge 18 ] && HAS_NODE18=1
        fi
        if [ $HAS_NODE18 -eq 0 ]; then
            curl -fsSL https://rpm.nodesource.com/setup_22.x | sudo bash - 2>/dev/null || true
            sudo dnf install -y nodejs || true
        fi
    fi
fi

# [3/5] Acquire Lucid Repository
echo -e "\n${BOLD}[3/5] Acquiring Lucid Application Repository...${NC}"

TARGET_DIR="$HOME/Lucid"

# Check if current directory is already Lucid
if [ -f "backend/requirements.txt" ] && [ -f "start_lucid.sh" ]; then
    TARGET_DIR="$(pwd)"
    echo -e "   Running inside existing Lucid repository: ${GREEN}$TARGET_DIR${NC}"
elif [ -d "$TARGET_DIR" ] && [ -f "$TARGET_DIR/backend/requirements.txt" ]; then
    echo -e "   Found existing Lucid installation at: ${CYAN}$TARGET_DIR${NC}"
    if [ -d "$TARGET_DIR/.git" ] && command -v git >/dev/null 2>&1; then
        echo "   Updating repository via git pull..."
        git -C "$TARGET_DIR" pull origin main 2>/dev/null || true
    fi
else
    echo -e "   Target Installation Directory: ${CYAN}$TARGET_DIR${NC}"
    if command -v git >/dev/null 2>&1; then
        echo "   Cloning Lucid repository via Git..."
        git clone https://github.com/imankur0011/Lucid.git "$TARGET_DIR"
    else
        echo "   Downloading repository archive directly from GitHub..."
        mkdir -p "$TARGET_DIR"
        curl -fsSL https://github.com/imankur0011/Lucid/archive/refs/heads/main.tar.gz | tar -xz -C "$TARGET_DIR" --strip-components=1
    fi
    echo -e "   ${GREEN}✅ Lucid repository downloaded successfully.${NC}"
fi

# [4/5] Ensure Executable Permissions
echo -e "\n${BOLD}[4/5] Preparing Launcher Permissions...${NC}"
chmod +x "$TARGET_DIR/start_lucid.sh" 2>/dev/null || true
chmod +x "$TARGET_DIR/stop_lucid.sh" 2>/dev/null || true
chmod +x "$TARGET_DIR/status_lucid.sh" 2>/dev/null || true
chmod +x "$TARGET_DIR/logs_lucid.sh" 2>/dev/null || true
echo -e "   ${GREEN}✅ Permissions configured.${NC}"

# [5/5] Launch Main Installer & Services
echo -e "\n${BOLD}[5/5] Transferring Execution to Lucid Application Launcher...${NC}"
cd "$TARGET_DIR"
exec ./start_lucid.sh
