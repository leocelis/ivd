#!/usr/bin/env bash
# mcp_server/devops/test.sh
#
# Run IVD MCP Server test suite.
#
# Activates venv and runs pytest.
#
# Usage:
#   ./mcp_server/devops/test.sh                  # all tests (unit + e2e)
#   ./mcp_server/devops/test.sh --unit           # unit tests only
#   ./mcp_server/devops/test.sh --e2e            # e2e tests only
#   ./mcp_server/devops/test.sh --smoke          # smoke tests (live server)
#   ./mcp_server/devops/test.sh -v               # verbose output
#   ./mcp_server/devops/test.sh -k "validate"    # filter by name

set -euo pipefail

# Resolve repo root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Activate venv
VENV="$REPO_ROOT/.venv"
if [ ! -d "$VENV" ]; then
    echo "ERROR: Virtual environment not found at $VENV"
    echo "Create it: python3 -m venv .venv && pip install -r mcp_server/requirements.txt"
    exit 1
fi
source "$VENV/bin/activate"

TESTS_DIR="$REPO_ROOT/mcp_server/tests"

# Parse first argument for shortcut flags
case "${1:-}" in
    --unit)
        shift
        echo "Running unit tests..."
        python -m pytest "$TESTS_DIR/unit/" "$@"
        ;;
    --e2e)
        shift
        echo "Running e2e tests..."
        python -m pytest "$TESTS_DIR/e2e/" "$@"
        ;;
    --smoke)
        shift
        echo "Running smoke tests against live server..."
        python "$TESTS_DIR/smoke/smoke.py" "$@"
        ;;
    --help|-h)
        echo "Usage: $0 [command] [pytest args]"
        echo ""
        echo "Commands:"
        echo "  (default)    All tests (unit + e2e)"
        echo "  --unit       Unit tests only"
        echo "  --e2e        E2E tests only"
        echo "  --smoke      Smoke tests (live server)"
        echo ""
        echo "Pytest args (pass-through):"
        echo "  -v           Verbose output"
        echo "  -k 'name'   Filter tests by name"
        echo "  --tb=short  Short tracebacks"
        echo "  -x          Stop on first failure"
        ;;
    *)
        echo "Running all tests (unit + e2e)..."
        python -m pytest "$TESTS_DIR" --ignore="$TESTS_DIR/smoke" "$@"
        ;;
esac
