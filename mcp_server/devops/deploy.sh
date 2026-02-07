#!/usr/bin/env bash
# deploy.sh — IVD MCP Server deployment to DigitalOcean App Platform
#
# Usage:
#   ./mcp_server/devops/deploy.sh              # Full deploy (embed + push + verify)
#   ./mcp_server/devops/deploy.sh --skip-embed  # Skip embedding regeneration
#   ./mcp_server/devops/deploy.sh --status      # Check deployment status
#   ./mcp_server/devops/deploy.sh --health      # Health check
#   ./mcp_server/devops/deploy.sh --create      # First-time: create the DO app
#   ./mcp_server/devops/deploy.sh --logs        # View deployment logs

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="ivd-mcp"
APP_SPEC="$REPO_ROOT/.do/app.yaml"
DO_PROJECT_ID="16526a12-bc99-4e3e-9adb-7321c84805f3"  # ADA project

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
    local app_id ingress
    app_id=$(require_app)
    ingress=$(doctl apps get "$app_id" --format DefaultIngress --no-header)

    if [ -z "$ingress" ]; then
        error "No ingress URL found. App may not be deployed yet."
        exit 1
    fi

    info "Checking: ${ingress}/health"
    local http_code body
    body=$(curl -s -o /dev/null -w "%{http_code}" "${ingress}/health" 2>/dev/null)
    http_code="$body"
    body=$(curl -s "${ingress}/health" 2>/dev/null)

    if [ "$http_code" = "200" ]; then
        success "Health check passed (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
    else
        error "Health check failed (HTTP $http_code)"
        echo "$body"
        exit 1
    fi
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

    # Step 1: Regenerate embeddings (unless --skip-embed)
    if [ "$skip_embed" = false ]; then
        info "Step 1/4: Regenerating embeddings..."
        if [ -f "$SCRIPT_DIR/embed.sh" ]; then
            bash "$SCRIPT_DIR/embed.sh"
            success "Embeddings regenerated"
        else
            warn "embed.sh not found, skipping"
        fi
    else
        info "Step 1/4: Skipping embeddings (--skip-embed)"
    fi

    # Step 2: Commit changes
    info "Step 2/4: Committing changes..."
    if git diff --quiet && git diff --cached --quiet; then
        info "No changes to commit"
    else
        git add -A
        git commit -m "deploy: update embeddings and server"
    fi

    # Step 3: Push to main (triggers auto-deploy)
    info "Step 3/4: Pushing to main..."
    git push origin main

    # Step 4: Wait for deployment
    info "Step 4/4: Waiting for deployment..."
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
                cmd_health
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
            echo "  --logs          View deployment logs"
            echo "  --update-spec   Update app spec on DO"
            ;;
        "")            cmd_deploy ;;
        *)             error "Unknown command: $1. Use --help"; exit 1 ;;
    esac
}

main "$@"
