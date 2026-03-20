#!/usr/bin/env bash
# mcp_server/devops/setup.sh
#
# Set up local development environment:
# - Creates Python 3.11+ virtual environment
# - Installs all dependencies from requirements.txt
# - Validates installation
#
# Usage:
#   ./mcp_server/devops/setup.sh           # Auto-detect Python 3.11+
#   ./mcp_server/devops/setup.sh python3.12  # Use specific Python version

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
RESET='\033[0m'

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV="$REPO_ROOT/.venv"
REQUIREMENTS="$REPO_ROOT/mcp_server/requirements.txt"

echo -e "${BLUE}========================================${RESET}"
echo -e "${BLUE}  IVD MCP Server - Environment Setup${RESET}"
echo -e "${BLUE}========================================${RESET}"
echo ""

# ==============================================================================
# Step 1: Detect or use specified Python version
# ==============================================================================

if [ -n "${1:-}" ]; then
    PYTHON_CMD="$1"
    echo -e "${BLUE}→${RESET} Using specified Python: ${PYTHON_CMD}"
else
    echo -e "${BLUE}→${RESET} Auto-detecting Python 3.11+..."
    
    # Try to find Python 3.11+ in order of preference
    for py_version in python3.13 python3.12 python3.11 python3.10; do
        if command -v "$py_version" &> /dev/null; then
            PYTHON_CMD="$py_version"
            break
        fi
    done
    
    if [ -z "${PYTHON_CMD:-}" ]; then
        echo -e "${RED}✗ Error: Python 3.10+ not found${RESET}"
        echo ""
        echo "Please install Python 3.11+ via:"
        echo "  - Homebrew: brew install python@3.11"
        echo "  - pyenv: pyenv install 3.11"
        echo ""
        echo "Or specify a Python executable:"
        echo "  $0 /path/to/python3.11"
        exit 1
    fi
fi

# Verify Python version meets minimum requirement
PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$("$PYTHON_CMD" -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$("$PYTHON_CMD" -c "import sys; print(sys.version_info.minor)")

echo -e "${GREEN}✓${RESET} Found: Python ${PYTHON_VERSION} (${PYTHON_CMD})"

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]; }; then
    echo -e "${RED}✗ Error: Python 3.10+ required (found ${PYTHON_VERSION})${RESET}"
    exit 1
fi

# ==============================================================================
# Step 2: Create or recreate virtual environment
# ==============================================================================

echo ""
if [ -d "$VENV" ]; then
    echo -e "${YELLOW}→${RESET} Existing venv found at .venv"
    read -p "   Recreate it? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→${RESET} Removing existing venv..."
        rm -rf "$VENV"
    else
        echo -e "${BLUE}→${RESET} Keeping existing venv"
    fi
fi

if [ ! -d "$VENV" ]; then
    echo -e "${BLUE}→${RESET} Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV"
    echo -e "${GREEN}✓${RESET} Virtual environment created at .venv"
fi

# ==============================================================================
# Step 3: Activate venv and upgrade pip
# ==============================================================================

echo ""
echo -e "${BLUE}→${RESET} Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV/bin/activate"

echo -e "${BLUE}→${RESET} Upgrading pip..."
pip install --quiet --upgrade pip

# ==============================================================================
# Step 4: Install dependencies
# ==============================================================================

echo ""
echo -e "${BLUE}→${RESET} Installing dependencies from requirements.txt..."
echo ""

if [ ! -f "$REQUIREMENTS" ]; then
    echo -e "${RED}✗ Error: requirements.txt not found at ${REQUIREMENTS}${RESET}"
    exit 1
fi

pip install -r "$REQUIREMENTS"

# ==============================================================================
# Step 5: Validate installation
# ==============================================================================

echo ""
echo -e "${BLUE}→${RESET} Validating installation..."

# Check critical packages
MISSING=()

# Check each package (format: "package_name:import_name")
for entry in "mcp:mcp" "starlette:starlette" "sse-starlette:sse_starlette" "uvicorn:uvicorn" "pyyaml:yaml" "numpy:numpy" "openai:openai" "pytest:pytest"; do
    pkg_name="${entry%%:*}"
    import_name="${entry##*:}"
    
    if ! python -c "import ${import_name}" 2>/dev/null; then
        MISSING+=("$pkg_name")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${RED}✗ Missing packages: ${MISSING[*]}${RESET}"
    exit 1
fi

echo -e "${GREEN}✓${RESET} All critical packages installed"

# ==============================================================================
# Step 6: Summary
# ==============================================================================

echo ""
echo -e "${GREEN}========================================${RESET}"
echo -e "${GREEN}  ✓ Setup Complete!${RESET}"
echo -e "${GREEN}========================================${RESET}"
echo ""
echo "Python version: ${PYTHON_VERSION}"
echo "Virtual environment: ${VENV}"
echo ""
echo "Next steps:"
echo "  1. Activate venv:   source .venv/bin/activate"
echo "  2. Run tests:       ./mcp_server/devops/test.sh"
echo "  3. Start server:    python -m mcp_server"
echo ""
echo "Other tools:"
echo "  - ./mcp_server/devops/embed.sh    # Generate embeddings (needs OPENAI_API_KEY)"
echo "  - ./mcp_server/devops/search.sh   # Search knowledge base"
echo "  - ./mcp_server/devops/logs.sh     # View server logs"
echo ""
