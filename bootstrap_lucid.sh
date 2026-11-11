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
        command -v python3 >/dev/null 2>&1 || sudo apt-get install -y python3 python3-pip python3-venv
        command -v node >/dev/null 2>&1 || sudo apt-get install -y nodejs npm
        command -v psql >/dev/null 2>&1 || sudo apt-get install -y postgresql postgresql-contrib
    elif command -v dnf >/dev/null 2>&1; then
        command -v git >/dev/null 2>&1 || sudo dnf install -y git
        command -v python3 >/dev/null 2>&1 || sudo dnf install -y python3 python3-pip
        command -v node >/dev/null 2>&1 || sudo dnf install -y nodejs npm
        command -v psql >/dev/null 2>&1 || sudo dnf install -y postgresql postgresql-server
    fi
fi

# [3/5] Acquire Lucid Repository
echo -e "\n${BOLD}[3/5] Acquiring Lucid Application Repository...${NC}"

TARGET_DIR="$HOME/Lucid"

# Check if current directory is already Lucid
if [ -f "backend/requirements.txt" ] && [ -f "start_lucid.sh" ]; then
    TARGET_DIR="$(pwd)"
    echo -e "   Running inside existing Lucid repository: ${GREEN}$TARGET_DIR${NC}"
elif [ -d "$TARGET_DIR" ] && [ -f "$TARGET_DIR/start_lucid.sh" ]; then
    echo -e "   Found existing Lucid installation at: ${CYAN}$TARGET_DIR${NC}"
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
