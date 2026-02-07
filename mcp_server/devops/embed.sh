#!/usr/bin/env bash
# mcp_server/devops/embed.sh
#
# Generate IVD knowledge base embeddings.
#
# Activates venv, loads .env, runs embed.py.
#
# Usage:
#   ./mcp_server/devops/embed.sh              # full run
#   ./mcp_server/devops/embed.sh --dry-run    # scan only, no API calls
#   ./mcp_server/devops/embed.sh --force      # re-embed everything

set -euo pipefail

# Resolve repo root (two levels up from this script: devops → mcp_server → repo root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "IVD Embedding Generator"
echo "Repo root: $REPO_ROOT"

# Activate venv
VENV="$REPO_ROOT/.venv"
if [ ! -d "$VENV" ]; then
    echo "ERROR: Virtual environment not found at $VENV"
    echo "Create it first: python3 -m venv .venv && pip install -r mcp_server/requirements.txt"
    exit 1
fi

echo "Activating venv..."
source "$VENV/bin/activate"

# Load .env if it exists
ENV_FILE="$REPO_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Loading .env..."
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "WARNING: No .env file found at $ENV_FILE"
    echo "Make sure OPENAI_API_KEY is set in your environment."
fi

# Verify OPENAI_API_KEY is available
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY is not set."
    echo "Add it to $ENV_FILE or export it in your shell."
    exit 1
fi

echo "OPENAI_API_KEY: ...${OPENAI_API_KEY: -4}"
echo ""

# Run embedding script (pass through any args like --dry-run, --force)
python "$SCRIPT_DIR/embed.py" "$@"
