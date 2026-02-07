#!/usr/bin/env bash
# mcp_server/devops/search.sh
#
# Search IVD knowledge base from the command line.
#
# Usage:
#   ./mcp_server/devops/search.sh "What are the 8 IVD principles?"
#   ./mcp_server/devops/search.sh "How do recipes work?" --top-k 3
#   ./mcp_server/devops/search.sh "intent artifacts" --verbose

set -euo pipefail

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate venv
VENV="$REPO_ROOT/.venv"
if [ ! -d "$VENV" ]; then
    echo "ERROR: Virtual environment not found at $VENV"
    exit 1
fi
source "$VENV/bin/activate"

# Load .env
ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY is not set."
    exit 1
fi

# Pass all args through
python "$SCRIPT_DIR/search.py" "$@"
