#!/usr/bin/env bash
# deploy/build.sh
#
# Canonical build script for the IVD MCP Server (DigitalOcean App Platform).
#
# This script lives in the repo (and not in the DO dashboard) so that build
# steps are version-controlled, reviewable in PRs, and testable locally with
# the same code path used in production.
#
# Set the DO build_command to:   bash deploy/build.sh
# (run_command stays defined by deploy/Procfile.)
#
# Steps:
#   1. Install Python dependencies (root requirements.txt for DO auto-detect)
#   2. Verify the env vars needed for embedding generation
#   3. Run mcp_server/devops/embed.py to generate the IVD knowledge base
#      under mcp_server/brain/ivd/  (excluding _private/, mcp_server/, etc.
#      per the SKIP_DIRS contract in mcp_server/knowledge/brain.py)
#   4. Verify the brain materialized — fail the build if it didn't, so that
#      ivd_search never silently degrades in production.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

echo "============================================================"
echo "  IVD MCP Server — build"
echo "  Repo root: $REPO_ROOT"
echo "============================================================"

# ---------------------------------------------------------------------------
# 1. Install dependencies
# ---------------------------------------------------------------------------

echo ""
echo "[build:1/4] Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

# ---------------------------------------------------------------------------
# 2. Verify env vars needed for embedding generation
# ---------------------------------------------------------------------------

echo ""
echo "[build:2/4] Checking embed-time env vars..."
if [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "ERROR: OPENAI_API_KEY is not set in the build environment."
    echo "Set it in the DigitalOcean dashboard under Settings → Environment Variables"
    echo "with scope 'Build & Run' (so it is available to this script)."
    exit 1
fi
echo "  OPENAI_API_KEY: ...${OPENAI_API_KEY: -4}  (ok)"

# ---------------------------------------------------------------------------
# 3. Generate embeddings
# ---------------------------------------------------------------------------

echo ""
echo "[build:3/4] Generating IVD knowledge base embeddings..."
echo "  Source:  $REPO_ROOT  (excludes _private/, mcp_server/, .git/, etc.)"
python mcp_server/devops/embed.py

# ---------------------------------------------------------------------------
# 4. Verify the brain materialized — fail the build on silent embed failure
# ---------------------------------------------------------------------------

echo ""
echo "[build:4/4] Verifying knowledge base..."
BRAIN_INDEX="$REPO_ROOT/mcp_server/brain/ivd/index.json"
if [ ! -f "$BRAIN_INDEX" ]; then
    echo "ERROR: Embeddings step finished but no index.json at $BRAIN_INDEX"
    echo "ivd_search would return 'Knowledge base not found' in production."
    exit 1
fi

DOC_COUNT=$(python - <<'PY'
import json, pathlib, sys
idx = json.loads(pathlib.Path("mcp_server/brain/ivd/index.json").read_text())
print(idx["stats"]["total_docs"])
PY
)

# Sanity floor: we ship far more than 10 framework docs + recipes + templates.
# A brain with <10 docs almost certainly means the scan ran from the wrong cwd
# or with an over-broad skip set.
if [ "$DOC_COUNT" -lt 10 ]; then
    echo "ERROR: brain/ivd/index.json reports only $DOC_COUNT docs (expected >= 10)."
    echo "Check embed.py output above; the scan likely ran from the wrong cwd."
    exit 1
fi

echo "  Brain index: $BRAIN_INDEX"
echo "  Docs indexed: $DOC_COUNT"
echo ""
echo "============================================================"
echo "  Build complete."
echo "============================================================"
