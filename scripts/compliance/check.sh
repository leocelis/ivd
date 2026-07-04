#!/usr/bin/env bash
# scripts/compliance/check.sh
#
# Offline TrustLint compliance gate for IVD LLM-facing artifacts.
# Canonical pattern: REUSE (CLI + CI) + OpenSSF automated gates.
#
# Usage (from repo root):
#   ./scripts/compliance/check.sh
#
# Requires: pip install 'trustlint>=2.0.0'
# No COMPLYEDGE_API_KEY — offline Tier 1 regex only.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

JURISDICTION="${TRUSTLINT_JURISDICTION:-EU}"

if ! command -v trustlint >/dev/null 2>&1; then
  echo "ERROR: trustlint not found. Install: pip install 'trustlint>=2.0.0'" >&2
  exit 2
fi

# PyPI 2.0.0+ bundles rules; older installs may need rules update.
if ! trustlint rules list -j "$JURISDICTION" >/dev/null 2>&1; then
  echo "TrustLint rules missing — running trustlint rules update..." >&2
  trustlint rules update
fi

checked=0
failed=0

check_file() {
  local f="$1"
  [ -f "$f" ] || return 0
  checked=$((checked + 1))
  if ! trustlint check "$f" -j "$JURISDICTION"; then
    echo "FAIL: $f" >&2
    failed=$((failed + 1))
  fi
}

should_skip() {
  local f="$1"
  case "$f" in
    */.venv/*|*/brain/*|*/__pycache__/*|*/.git/*) return 0 ;;
  esac
  return 1
}

while IFS= read -r -d '' f; do
  should_skip "$f" && continue
  check_file "$f"
done < <(find recipes templates -type f \( -name '*.yaml' -o -name '*.yml' \) -print0 2>/dev/null || true)

while IFS= read -r -d '' f; do
  should_skip "$f" && continue
  check_file "$f"
done < <(find . -name '*_intent.yaml' -not -path './.venv/*' -not -path './.git/*' -not -path '*/brain/*' -print0)

if [ -f ivd_system_intent.yaml ]; then
  check_file ivd_system_intent.yaml
fi

if [ "$failed" -gt 0 ]; then
  echo "TrustLint compliance check failed ($failed file(s))." >&2
  exit 1
fi

echo "TrustLint OK — $checked file(s) scanned (jurisdiction: $JURISDICTION)"
