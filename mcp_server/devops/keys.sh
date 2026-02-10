#!/usr/bin/env bash
# keys.sh — IVD MCP API Key Management
#
# Usage:
#   ./mcp_server/devops/keys.sh --generate <username>   # Generate key with user prefix
#   ./mcp_server/devops/keys.sh --list                  # Show keys from .env (partial)
#   ./mcp_server/devops/keys.sh --add <key>             # Add key to production (DO)
#   ./mcp_server/devops/keys.sh --revoke <username>     # Remove key from production (DO)
#   ./mcp_server/devops/keys.sh --verify <key>          # Test key against production

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$REPO_ROOT/.env"
APP_NAME="ivd-mcp"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; DIM='\033[2m'
BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[IVD Keys]${NC} $1"; }
success() { echo -e "${GREEN}[IVD Keys]${NC} $1"; }
warn()    { echo -e "${YELLOW}[IVD Keys]${NC} $1"; }
error()   { echo -e "${RED}[IVD Keys]${NC} $1"; }
header()  { echo -e "\n${MAGENTA}══════════════════════════════════════════════${NC}"; echo -e "${MAGENTA}  $1${NC}"; echo -e "${MAGENTA}══════════════════════════════════════════════${NC}\n"; }

# ── Helpers ────────────────────────────────────────────────────────────────────

require_doctl() {
    if ! command -v doctl &> /dev/null; then
        error "doctl not found. Install: brew install doctl"
        exit 1
    fi
}

extract_key_id() {
    local key="$1"
    echo "${key:0:8}..."
}

# ── Commands ───────────────────────────────────────────────────────────────────

cmd_generate() {
    local username="$1"
    
    if [ -z "$username" ]; then
        error "Usage: $0 --generate <username>"
        exit 1
    fi
    
    # Validate username (alphanumeric + underscore only)
    if ! [[ "$username" =~ ^[a-zA-Z0-9_]+$ ]]; then
        error "Username must be alphanumeric (a-z, A-Z, 0-9, _)"
        exit 1
    fi
    
    header "Generating API Key for User: $username"
    
    # Generate 24-char random token (base64url safe)
    local token
    token=$(python3 -c 'import secrets; print(secrets.token_urlsafe(24))')
    
    # Combine username prefix + token
    local full_key="${username}_${token}"
    
    # Extract partial key for display
    local key_id
    key_id=$(extract_key_id "$full_key")
    
    success "Key generated successfully!"
    echo ""
    echo -e "  ${BOLD}User:${NC}     $username"
    echo -e "  ${BOLD}Key ID:${NC}   ${DIM}$key_id${NC}"
    echo -e "  ${BOLD}Full Key:${NC} ${GREEN}$full_key${NC}"
    echo ""
    
    # Add to local .env as backup
    info "Adding key to local .env as backup..."
    
    if [ ! -f "$ENV_FILE" ]; then
        warn ".env file not found: $ENV_FILE"
        info "Create it manually or the key won't be backed up locally"
    else
        # Check if IVD_API_KEYS exists
        if grep -q "^IVD_API_KEYS=" "$ENV_FILE"; then
            # Get current keys
            local current_keys
            current_keys=$(grep "^IVD_API_KEYS=" "$ENV_FILE" | cut -d'=' -f2-)
            
            # Check if key already exists
            if echo "$current_keys" | grep -q "$full_key"; then
                info "Key already exists in .env"
            else
                # Append to existing keys
                local new_keys="${current_keys},${full_key}"
                # Update the line
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$new_keys|" "$ENV_FILE"
                else
                    sed -i "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$new_keys|" "$ENV_FILE"
                fi
                success "Added to .env"
            fi
        else
            # IVD_API_KEYS doesn't exist, add it
            echo "IVD_API_KEYS=$full_key" >> "$ENV_FILE"
            success "Added IVD_API_KEYS to .env"
        fi
    fi
    
    echo ""
    info "Next steps:"
    echo "  1. Save this key securely (1Password, encrypted storage)"
    echo "  2. Add to production: ${CYAN}$0 --add $full_key${NC}"
    echo "  3. Share with user via secure channel"
    echo "  4. Test: ${CYAN}$0 --verify $full_key${NC}"
    echo ""
    warn "This key will NOT be shown again!"
}

cmd_list() {
    header "IVD MCP API Keys (from .env)"
    
    if [ ! -f "$ENV_FILE" ]; then
        error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    
    # Extract IVD_API_KEYS from .env
    local keys_raw
    keys_raw=$(grep '^IVD_API_KEYS=' "$ENV_FILE" 2>/dev/null | cut -d'=' -f2- | tr -d '"')
    
    if [ -z "$keys_raw" ]; then
        warn "No keys found in $ENV_FILE"
        echo "  Add keys: IVD_API_KEYS=\"key1,key2,key3\""
        return
    fi
    
    info "Keys in .env (partial display):\n"
    
    # Split by comma and show partial
    IFS=',' read -ra keys <<< "$keys_raw"
    for key in "${keys[@]}"; do
        key=$(echo "$key" | xargs) # trim whitespace
        if [ -n "$key" ]; then
            local key_id
            key_id=$(extract_key_id "$key")
            
            # Extract username if present
            local username=""
            if [[ "$key" =~ ^([a-zA-Z0-9_]+)_ ]]; then
                username="${BASH_REMATCH[1]}"
                echo -e "  ${DIM}$key_id${NC}  (user: ${CYAN}$username${NC})"
            else
                echo -e "  ${DIM}$key_id${NC}"
            fi
        fi
    done
    
    echo ""
    info "Total: ${#keys[@]} key(s)"
}

cmd_add() {
    local key="$1"
    
    if [ -z "$key" ]; then
        error "Usage: $0 --add <full_key>"
        exit 1
    fi
    
    require_doctl
    
    local key_id
    key_id=$(extract_key_id "$key")
    
    header "Adding Key to Production"
    
    info "Finding IVD MCP app on DigitalOcean..."
    local app_id
    app_id=$(doctl apps list --format ID,Spec.Name --no-header 2>/dev/null | grep "$APP_NAME" | awk '{print $1}' | head -1)
    
    if [ -z "$app_id" ]; then
        error "App '$APP_NAME' not found on DigitalOcean"
        exit 1
    fi
    
    info "App ID: $app_id"
    info "Fetching current keys from local .env (source of truth)..."
    
    # IMPORTANT: Read current keys from LOCAL .env, NOT from DO spec.
    # DO returns encrypted values (EV[1:...]) that can't be parsed,
    # so we use .env as the source of truth for existing keys.
    local current_keys=""
    if [ -f "$ENV_FILE" ] && grep -q "^IVD_API_KEYS=" "$ENV_FILE"; then
        current_keys=$(grep "^IVD_API_KEYS=" "$ENV_FILE" | cut -d'=' -f2-)
    fi
    
    if [ -z "$current_keys" ]; then
        error "No keys found in local .env — cannot safely add key."
        error ".env must contain all current keys to prevent overwriting."
        error "Restore .env first, then retry."
        exit 1
    fi
    
    # Check if key already exists
    if echo "$current_keys" | grep -q "$key"; then
        warn "Key ${DIM}$key_id${NC} already exists in .env"
        info "Syncing .env keys to production..."
        local new_keys="$current_keys"
    else
        # Append new key
        local new_keys="${current_keys},${key}"
    fi
    
    info "Keys to set in production: $(echo "$new_keys" | tr ',' '\n' | wc -l | xargs) key(s)"
    
    # Step 1: Update .env FIRST (source of truth)
    info "Updating local .env with new key set..."
    if grep -q "^IVD_API_KEYS=" "$ENV_FILE"; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$new_keys|" "$ENV_FILE"
        else
            sed -i "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$new_keys|" "$ENV_FILE"
        fi
    else
        echo "IVD_API_KEYS=$new_keys" >> "$ENV_FILE"
    fi
    success ".env updated"
    
    # Step 2: Push to DigitalOcean
    info "Adding key ${DIM}$key_id${NC} to production..."
    
    local temp_spec
    temp_spec=$(mktemp)
    
    doctl apps spec get "$app_id" > "$temp_spec" 2>/dev/null
    
    if grep -q "key: IVD_API_KEYS" "$temp_spec"; then
        # Use awk to update the value line that comes after IVD_API_KEYS
        awk -v new_val="$new_keys" '
            /key: IVD_API_KEYS/ { found=1; print; next }
            found && /value:/ { 
                sub(/value:.*/, "value: \"" new_val "\""); 
                found=0 
            }
            { print }
        ' "$temp_spec" > "${temp_spec}.new"
        mv "${temp_spec}.new" "$temp_spec"
        
        if doctl apps update "$app_id" --spec "$temp_spec" >/dev/null 2>&1; then
            success "Key added to production! Deployment in progress..."
            echo ""
            info "Monitor deployment: ${CYAN}doctl apps list${NC}"
            info "Verify key works: ${CYAN}$0 --verify $key${NC}"
        else
            error "Failed to update app spec"
            warn ".env was already updated — production may be out of sync"
            rm -f "$temp_spec"
            exit 1
        fi
    else
        error "IVD_API_KEYS not found in app spec"
        rm -f "$temp_spec"
        exit 1
    fi
    
    rm -f "$temp_spec"
}

cmd_revoke() {
    local username="$1"
    
    if [ -z "$username" ]; then
        error "Usage: $0 --revoke <username>"
        exit 1
    fi
    
    require_doctl
    
    header "Revoking Keys for User: $username"
    
    info "Finding IVD MCP app on DigitalOcean..."
    local app_id
    app_id=$(doctl apps list --format ID,Spec.Name --no-header 2>/dev/null | grep "$APP_NAME" | awk '{print $1}' | head -1)
    
    if [ -z "$app_id" ]; then
        error "App '$APP_NAME' not found on DigitalOcean"
        exit 1
    fi
    
    info "App ID: $app_id"
    info "Fetching current keys from local .env (source of truth)..."
    
    # IMPORTANT: Read current keys from LOCAL .env, NOT from DO spec.
    # DO returns encrypted values (EV[1:...]) that can't be parsed.
    local current_keys=""
    if [ -f "$ENV_FILE" ] && grep -q "^IVD_API_KEYS=" "$ENV_FILE"; then
        current_keys=$(grep "^IVD_API_KEYS=" "$ENV_FILE" | cut -d'=' -f2-)
    fi
    
    if [ -z "$current_keys" ]; then
        error "No keys found in local .env — cannot safely revoke."
        error ".env must contain all current keys to prevent data loss."
        exit 1
    fi
    
    # Filter out keys starting with username_
    local new_keys=""
    local removed_count=0
    
    IFS=',' read -ra keys <<< "$current_keys"
    for key in "${keys[@]}"; do
        key=$(echo "$key" | xargs) # trim
        if [[ "$key" =~ ^${username}_ ]]; then
            local key_id
            key_id=$(extract_key_id "$key")
            warn "Removing key ${DIM}$key_id${NC}"
            removed_count=$((removed_count + 1))
        else
            if [ -z "$new_keys" ]; then
                new_keys="$key"
            else
                new_keys="${new_keys},${key}"
            fi
        fi
    done
    
    if [ $removed_count -eq 0 ]; then
        warn "No keys found for user: $username"
        exit 0
    fi
    
    info "Updating production environment..."
    
    # Get current app spec, update IVD_API_KEYS, and apply
    local temp_spec
    temp_spec=$(mktemp)
    
    doctl apps spec get "$app_id" > "$temp_spec" 2>/dev/null
    
    # Update the IVD_API_KEYS value in the YAML
    if grep -q "key: IVD_API_KEYS" "$temp_spec"; then
        awk -v new_val="$new_keys" '
            /key: IVD_API_KEYS/ { found=1; print; next }
            found && /value:/ { 
                sub(/value:.*/, "value: \"" new_val "\""); 
                found=0 
            }
            { print }
        ' "$temp_spec" > "${temp_spec}.new"
        mv "${temp_spec}.new" "$temp_spec"
        
        # Apply the updated spec
        if doctl apps update "$app_id" --spec "$temp_spec" >/dev/null 2>&1; then
            success "Revoked $removed_count key(s) from production for user: $username"
            
            # Also remove from local .env
            if [ -f "$ENV_FILE" ] && grep -q "^IVD_API_KEYS=" "$ENV_FILE"; then
                info "Removing keys from local .env..."
                
                local env_keys
                env_keys=$(grep "^IVD_API_KEYS=" "$ENV_FILE" | cut -d'=' -f2-)
                
                # Filter out keys for this user
                local env_new_keys=""
                local env_removed=0
                
                IFS=',' read -ra keys <<< "$env_keys"
                for key in "${keys[@]}"; do
                    key=$(echo "$key" | xargs) # trim
                    if [[ "$key" =~ ^${username}_ ]]; then
                        env_removed=$((env_removed + 1))
                    else
                        if [ -z "$env_new_keys" ]; then
                            env_new_keys="$key"
                        else
                            env_new_keys="${env_new_keys},${key}"
                        fi
                    fi
                done
                
                # Update .env
                if [[ "$OSTYPE" == "darwin"* ]]; then
                    sed -i '' "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$env_new_keys|" "$ENV_FILE"
                else
                    sed -i "s|^IVD_API_KEYS=.*|IVD_API_KEYS=$env_new_keys|" "$ENV_FILE"
                fi
                
                if [ $env_removed -gt 0 ]; then
                    success "Removed $env_removed key(s) from .env"
                fi
            fi
            
            echo ""
            info "Deployment in progress. Keys will be invalid once deployment completes."
        else
            error "Failed to update app spec"
            rm -f "$temp_spec"
            exit 1
        fi
    else
        error "IVD_API_KEYS not found in app spec"
        rm -f "$temp_spec"
        exit 1
    fi
    
    rm -f "$temp_spec"
}

cmd_verify() {
    local key="$1"
    
    if [ -z "$key" ]; then
        error "Usage: $0 --verify <full_key>"
        exit 1
    fi
    
    local key_id
    key_id=$(extract_key_id "$key")
    
    header "Verifying Key: ${DIM}$key_id${NC}"
    
    info "Testing against production endpoint: mcp.ivdframework.dev"
    echo ""
    
    # Test /sse endpoint
    local response
    response=$(curl -s -w "\n%{http_code}" -N --max-time 5 \
        -H "Authorization: Bearer $key" \
        https://mcp.ivdframework.dev/sse 2>&1 || echo "000")
    
    local http_code
    http_code=$(echo "$response" | tail -1)
    
    case "$http_code" in
        200)
            success "✓ Key is valid! Authentication successful."
            info "Key ${DIM}$key_id${NC} is working in production"
            ;;
        401)
            error "✗ Key is invalid! Authentication failed."
            warn "Key ${DIM}$key_id${NC} was rejected by the server"
            ;;
        000)
            error "✗ Connection failed! Could not reach production."
            warn "Check network connectivity or production status"
            ;;
        *)
            warn "Unexpected response: HTTP $http_code"
            ;;
    esac
}

# ── Main ───────────────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --generate)   cmd_generate "${2:-}" ;;
        --list)       cmd_list ;;
        --add)        cmd_add "${2:-}" ;;
        --revoke)     cmd_revoke "${2:-}" ;;
        --verify)     cmd_verify "${2:-}" ;;
        --help|-h)
            echo "Usage: $0 <command> [args]"
            echo ""
            echo "Commands:"
            echo "  --generate <username>   Generate new API key with user prefix"
            echo "  --list                  Show keys from .env (partial)"
            echo "  --add <key>             Add key to production (DigitalOcean)"
            echo "  --revoke <username>     Remove all keys for user from production"
            echo "  --verify <key>          Test key against production endpoint"
            echo ""
            echo "Examples:"
            echo "  $0 --generate alice                           # Generate key for alice"
            echo "  $0 --list                                     # Show all keys"
            echo "  $0 --add alice_X7W2NqR8KpL4MnV9BtQ6DfH2      # Add to production"
            echo "  $0 --verify alice_X7W2NqR8KpL4MnV9BtQ6DfH2   # Test key"
            echo "  $0 --revoke alice                             # Remove alice's keys"
            ;;
        "")
            error "No command specified. Use --help for usage."
            exit 1
            ;;
        *)
            error "Unknown command: $1. Use --help for usage."
            exit 1
            ;;
    esac
}

main "$@"
