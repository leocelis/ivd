#!/usr/bin/env bash
# deploy.sh — IVD MCP Server deployment to DigitalOcean App Platform
#
# Usage:
#   ./mcp_server/devops/deploy.sh              # Full deploy (embed + push + verify)
#   ./mcp_server/devops/deploy.sh --skip-embed  # Skip embedding regeneration
#   ./mcp_server/devops/deploy.sh --status      # Check deployment status
#   ./mcp_server/devops/deploy.sh --health      # Health check
#   ./mcp_server/devops/deploy.sh --smoke       # Post-deploy smoke tests
#   ./mcp_server/devops/deploy.sh --create      # First-time: create the DO app
#   ./mcp_server/devops/deploy.sh --logs        # View deployment logs

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="ivd-mcp"
APP_SPEC="$REPO_ROOT/.do/app.yaml"
DO_PROJECT_ID="16526a12-bc99-4e3e-9adb-7321c84805f3"  # ADA project
CUSTOM_DOMAIN="https://mcp.ivdframework.dev"  # Custom domain for IVD MCP

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; NC='\033[0m'

info()    { echo -e "${CYAN}[IVD Deploy]${NC} $1"; }
success() { echo -e "${GREEN}[IVD Deploy]${NC} $1"; }
warn()    { echo -e "${YELLOW}[IVD Deploy]${NC} $1"; }
error()   { echo -e "${RED}[IVD Deploy]${NC} $1"; }
header()  { echo -e "\n${MAGENTA}══════════════════════════════════════════════${NC}"; echo -e "${MAGENTA}  $1${NC}"; echo -e "${MAGENTA}══════════════════════════════════════════════${NC}\n"; }

# ── Helpers ────────────────────────────────────────────────────────────────────

get_app_id() {
    doctl apps list --format ID,Spec.Name --no-header 2>/dev/null | \
        grep "$APP_NAME" | awk '{print $1}' | head -1
}

require_doctl() {
    if ! command -v doctl &> /dev/null; then
        error "doctl not found. Install: brew install doctl"
        exit 1
    fi
}

require_app() {
    local app_id
    app_id=$(get_app_id)
    if [ -z "$app_id" ]; then
        error "App '$APP_NAME' not found on DO. Run: $0 --create"
        exit 1
    fi
    echo "$app_id"
}

check_env_vars() {
    # Pre-deploy gate: verify all required env vars are configured in DO.
    # Reads the required list from mcp_server/env_check.py (single source of truth)
    # and checks them against the live DO app spec.
    
    local app_id="$1"
    info "Checking required environment variables in DO app spec..."
    
    # Extract required var names from env_check.py (the canonical list)
    local env_check_file="$REPO_ROOT/mcp_server/env_check.py"
    if [ ! -f "$env_check_file" ]; then
        error "env_check.py not found at $env_check_file"
        exit 1
    fi
    
    # Import and read required vars directly from env_check.py
    local required_vars
    required_vars=$(python3 -c "
import sys
sys.path.insert(0, '$REPO_ROOT')
from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE, REQUIRED_ENV_VARS_ALL
for var in REQUIRED_ENV_VARS_REMOTE:
    print(var)
for var in REQUIRED_ENV_VARS_ALL:
    print(var)
" 2>/dev/null)
    
    if [ -z "$required_vars" ]; then
        error "Could not read required vars from env_check.py"
        error "Check that mcp_server/env_check.py exists and is valid Python"
        exit 1
    fi
    
    # Get current DO app spec env var keys
    local do_env_keys
    do_env_keys=$(doctl apps spec get "$app_id" 2>/dev/null | grep "  - key:" | sed 's/.*key: //' || echo "")
    
    local missing=0
    while IFS= read -r var; do
        if ! echo "$do_env_keys" | grep -q "^${var}$"; then
            error "MISSING in DO app spec: $var"
            missing=$((missing + 1))
        else
            success "  ✓ $var"
        fi
    done <<< "$required_vars"
    
    if [ $missing -gt 0 ]; then
        echo ""
        error "Deploy blocked: $missing required env var(s) missing from DO app spec."
        error "Add them to .do/app.yaml and run: $0 --update-spec"
        exit 1
    fi
    
    success "All required environment variables present in DO"
}

# ── Commands ───────────────────────────────────────────────────────────────────

cmd_create() {
    header "Creating IVD MCP App on DigitalOcean"
    require_doctl

    local existing
    existing=$(get_app_id)
    if [ -n "$existing" ]; then
        warn "App '$APP_NAME' already exists (ID: $existing)"
        info "Use --status to check, or --health to verify"
        return 0
    fi

    info "Creating app from spec: $APP_SPEC"
    doctl apps create --spec "$APP_SPEC" --project-id "$DO_PROJECT_ID" --format ID,DefaultIngress
    
    success "App created. Set IVD_API_KEYS in DO dashboard (Settings > Environment Variables)"
    info "Generate a key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
}

cmd_status() {
    header "IVD MCP Deployment Status"
    require_doctl
    local app_id
    app_id=$(require_app)

    info "App:"
    doctl apps get "$app_id" --format ID,Spec.Name,DefaultIngress

    echo ""
    info "Latest deployment:"
    doctl apps list-deployments "$app_id" --format ID,Phase,Progress,Cause 2>/dev/null | head -3
}

cmd_health() {
    header "IVD MCP Health Check"
    require_doctl
    local app_id
    app_id=$(require_app)

    info "Checking: ${CUSTOM_DOMAIN}/health"
    local http_code body
    body=$(curl -s -o /dev/null -w "%{http_code}" "${CUSTOM_DOMAIN}/health" 2>/dev/null)
    http_code="$body"
    body=$(curl -s "${CUSTOM_DOMAIN}/health" 2>/dev/null)

    if [ "$http_code" = "200" ]; then
        success "Health check passed (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        error "Health check failed (HTTP $http_code)"
        echo "$body"
        exit 1
    fi
}

cmd_smoke() {
    header "IVD MCP Smoke Tests"
    require_doctl
    local app_id
    app_id=$(require_app)

    local smoke_script="$REPO_ROOT/mcp_server/tests/smoke/smoke.py"
    if [ ! -f "$smoke_script" ]; then
        error "Smoke test script not found: $smoke_script"
        exit 1
    fi

    local api_key="${IVD_API_KEY:-}"
    local key_args=""
    if [ -n "$api_key" ]; then
        key_args="--key $api_key"
    fi

    info "Running smoke tests against: $CUSTOM_DOMAIN"
    python3 "$smoke_script" --url "$CUSTOM_DOMAIN" $key_args
}

cmd_logs() {
    header "IVD MCP Deployment Logs"
    require_doctl
    local app_id
    app_id=$(require_app)

    doctl apps logs "$app_id" --type=deploy --follow
}

cmd_update_spec() {
    header "Updating App Spec"
    require_doctl
    local app_id
    app_id=$(require_app)

    # Validate required env vars before applying spec
    check_env_vars "$app_id"

    info "Updating app spec from: $APP_SPEC"
    doctl apps update "$app_id" --spec "$APP_SPEC"
    success "App spec updated"
}

cmd_deploy() {
    local skip_embed=false

    for arg in "$@"; do
        case "$arg" in
            --skip-embed) skip_embed=true ;;
        esac
    done

    header "IVD MCP Server Deployment"
    require_doctl

    local app_id
    app_id=$(require_app)
    info "App ID: $app_id"

    cd "$REPO_ROOT"

    # Step 0: Validate required env vars in DO (gate — blocks deploy if missing)
    check_env_vars "$app_id"

    # Step 1: Regenerate embeddings (unless --skip-embed)
    if [ "$skip_embed" = false ]; then
        info "Step 1/5: Regenerating embeddings..."
        if [ -f "$SCRIPT_DIR/embed.sh" ]; then
            bash "$SCRIPT_DIR/embed.sh"
            success "Embeddings regenerated"
        else
            warn "embed.sh not found, skipping"
        fi
    else
        info "Step 1/5: Skipping embeddings (--skip-embed)"
    fi

    # Step 2: Run tests (gate — must pass before pushing)
    info "Step 2/5: Running tests..."
    if [ -f "$SCRIPT_DIR/test.sh" ]; then
        if bash "$SCRIPT_DIR/test.sh"; then
            success "All tests passed"
        else
            error "Tests failed — aborting deploy"
            info "Fix failing tests, then re-run: $0"
            exit 1
        fi
    else
        warn "test.sh not found, skipping tests"
    fi

    # Step 3: Commit changes
    info "Step 3/5: Committing changes..."
    if git diff --quiet && git diff --cached --quiet; then
        info "No changes to commit"
    else
        git add -A
        git commit -m "deploy: update embeddings and server"
    fi

    # Step 4: Push to main (triggers auto-deploy)
    info "Step 4/5: Pushing to main..."
    git push origin main

    # Step 5: Wait for deployment
    info "Step 5/5: Waiting for deployment..."
    local max_wait=180
    local elapsed=0
    local interval=15

    while [ $elapsed -lt $max_wait ]; do
        sleep $interval
        elapsed=$((elapsed + interval))

        local phase
        phase=$(doctl apps list-deployments "$app_id" --format Phase --no-header 2>/dev/null | head -1)
        phase="${phase:-UNKNOWN}"

        info "  Deployment status: $phase (${elapsed}s / ${max_wait}s)"

        case "$phase" in
            ACTIVE)
                success "Deployment complete!"
                cmd_smoke
                return 0
                ;;
            ERROR|CANCELED)
                error "Deployment failed: $phase"
                info "Check logs: $0 --logs"
                exit 1
                ;;
        esac
    done

    warn "Deployment still in progress after ${max_wait}s. Check: $0 --status"
}

# ── Main ───────────────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --create)      cmd_create ;;
        --status)      cmd_status ;;
        --health)      cmd_health ;;
        --smoke)       cmd_smoke ;;
        --logs)        cmd_logs ;;
        --update-spec) cmd_update_spec ;;
        --skip-embed)  cmd_deploy "$@" ;;
        --help|-h)
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  (default)       Full deploy: embed → commit → push → verify"
            echo "  --skip-embed    Deploy without regenerating embeddings"
            echo "  --create        First-time: create the DO app"
            echo "  --status        Check deployment status"
            echo "  --health        Run health check"
            echo "  --smoke         Post-deploy smoke tests (health + auth + SSE)"
            echo "  --logs          View deployment logs"
            echo "  --update-spec   Update app spec on DO"
            ;;
        "")            cmd_deploy ;;
        *)             error "Unknown command: $1. Use --help"; exit 1 ;;
    esac
}

main "$@"
