#!/usr/bin/env bash
# logs.sh — Stream and query IVD MCP Server logs
#
# Usage:
#   ./mcp_server/devops/logs.sh                    # Stream from DigitalOcean console (live, auto-reconnect)
#   ./mcp_server/devops/logs.sh --local            # Stream local log file (colored, live)
#   ./mcp_server/devops/logs.sh --tail              # Tail last 20 lines (local)
#   ./mcp_server/devops/logs.sh --tail 50           # Tail last N lines (local)
#   ./mcp_server/devops/logs.sh --tools             # Show tool call summary (local)
#   ./mcp_server/devops/logs.sh --errors            # Show only errors (local)
#   ./mcp_server/devops/logs.sh --auth              # Show auth events (local)
#   ./mcp_server/devops/logs.sh --key O9T4HnV6      # Filter by partial key (local)
#   ./mcp_server/devops/logs.sh --tool ivd_search   # Filter by tool name (local)
#   ./mcp_server/devops/logs.sh --ip 45.123.45.67   # Filter by origin IP (local)
#   ./mcp_server/devops/logs.sh --since 2026-02-08  # Filter by date (local)
#   ./mcp_server/devops/logs.sh --json              # Raw JSON output (local, pipe to jq)
#   ./mcp_server/devops/logs.sh --stats             # Full usage statistics (local)
#   ./mcp_server/devops/logs.sh --files             # List log files with sizes (local)

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_DIR="${LOG_DIR:-$REPO_ROOT/mcp_server/logs}"
LOG_FILE="$LOG_DIR/ivd_mcp.log"
APP_NAME="ivd-mcp"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; DIM='\033[2m'
BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${CYAN}[IVD Logs]${NC} $1"; }
success() { echo -e "${GREEN}[IVD Logs]${NC} $1"; }
warn()    { echo -e "${YELLOW}[IVD Logs]${NC} $1"; }
error()   { echo -e "${RED}[IVD Logs]${NC} $1"; }
header()  { echo -e "\n${MAGENTA}══════════════════════════════════════════════${NC}"; echo -e "${MAGENTA}  $1${NC}"; echo -e "${MAGENTA}══════════════════════════════════════════════${NC}\n"; }

# ── Helpers ────────────────────────────────────────────────────────────────────

require_log_file() {
    if [ ! -f "$LOG_FILE" ]; then
        error "Log file not found: $LOG_FILE"
        info "Run the MCP server first to generate logs"
        exit 1
    fi
}

require_jq() {
    if ! command -v jq &> /dev/null; then
        error "jq not found. Install: brew install jq"
        exit 1
    fi
}

# Colorize a JSON log line for terminal display
colorize_line() {
    local line="$1"
    
    local level event tool status duration_ms key_id origin_ip ts error_msg
    level=$(echo "$line" | jq -r '.level // "INFO"' 2>/dev/null)
    event=$(echo "$line" | jq -r '.event // "log"' 2>/dev/null)
    ts=$(echo "$line" | jq -r '.ts // ""' 2>/dev/null | cut -c1-19)
    
    # Color based on level
    local level_color="$CYAN"
    case "$level" in
        DEBUG)    level_color="$DIM" ;;
        INFO)     level_color="$CYAN" ;;
        WARNING)  level_color="$YELLOW" ;;
        ERROR)    level_color="$RED" ;;
        CRITICAL) level_color="${BOLD}${RED}" ;;
    esac
    
    if [ "$event" = "tool_call" ]; then
        tool=$(echo "$line" | jq -r '.tool // "?"' 2>/dev/null)
        status=$(echo "$line" | jq -r '.status // "?"' 2>/dev/null)
        duration_ms=$(echo "$line" | jq -r '.duration_ms // 0' 2>/dev/null)
        key_id=$(echo "$line" | jq -r '.key_id // "?"' 2>/dev/null)
        origin_ip=$(echo "$line" | jq -r '.origin_ip // "?"' 2>/dev/null)
        error_msg=$(echo "$line" | jq -r '.error // ""' 2>/dev/null)
        
        local status_color="$GREEN"
        [ "$status" = "error" ] && status_color="$RED"
        
        local output="${DIM}${ts}${NC} ${level_color}[${level}]${NC}  ${BOLD}${event}${NC}  ${CYAN}${tool}${NC}  ${duration_ms}ms  ${status_color}${status}${NC}  key=${DIM}${key_id}${NC}  ip=${DIM}${origin_ip}${NC}"
        [ -n "$error_msg" ] && output="${output}  ${RED}error=${error_msg}${NC}"
        echo -e "$output"
    
    elif [ "$event" = "auth" ]; then
        status=$(echo "$line" | jq -r '.status // "?"' 2>/dev/null)
        key_id=$(echo "$line" | jq -r '.key_id // "?"' 2>/dev/null)
        origin_ip=$(echo "$line" | jq -r '.origin_ip // "?"' 2>/dev/null)
        error_msg=$(echo "$line" | jq -r '.error // ""' 2>/dev/null)
        
        local status_color="$GREEN"
        [ "$status" = "error" ] && status_color="$RED"
        [ "$status" = "disabled" ] && status_color="$YELLOW"
        
        local output="${DIM}${ts}${NC} ${level_color}[${level}]${NC}  ${BOLD}${event}${NC}  ${status_color}${status}${NC}  key=${DIM}${key_id}${NC}  ip=${DIM}${origin_ip}${NC}"
        [ -n "$error_msg" ] && output="${output}  ${RED}${error_msg}${NC}"
        echo -e "$output"
    
    else
        local message
        message=$(echo "$line" | jq -r '.message // .event // "?"' 2>/dev/null)
        echo -e "${DIM}${ts}${NC} ${level_color}[${level}]${NC}  ${message}"
    fi
}

# ── Commands ───────────────────────────────────────────────────────────────────

cmd_stream() {
    header "Streaming IVD MCP Logs"
    require_log_file
    require_jq
    
    info "Log file: ${LOG_FILE}"
    info "Press Ctrl+C to stop\n"
    
    tail -f "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_tail() {
    local count="${1:-20}"
    header "Last ${count} Log Entries"
    require_log_file
    require_jq
    
    tail -n "$count" "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_tools() {
    header "Tool Call Summary"
    require_log_file
    require_jq
    
    local total ok errors
    total=$(jq -r 'select(.event == "tool_call") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    ok=$(jq -r 'select(.event == "tool_call" and .status == "ok") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    errors=$(jq -r 'select(.event == "tool_call" and .status == "error") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    
    echo -e "  ${BOLD}Total calls:${NC}  $total"
    echo -e "  ${GREEN}Successful:${NC}   $ok"
    echo -e "  ${RED}Errors:${NC}       $errors"
    echo ""
    
    echo -e "  ${BOLD}Calls per tool:${NC}"
    jq -r 'select(.event == "tool_call") | .tool' "$LOG_FILE" | sort | uniq -c | sort -rn | while read -r count tool; do
        printf "    %-30s %s\n" "$tool" "$count"
    done
    
    echo ""
    echo -e "  ${BOLD}Avg duration (ms) per tool:${NC}"
    jq -r 'select(.event == "tool_call" and .status == "ok") | "\(.tool) \(.duration_ms)"' "$LOG_FILE" | \
        awk '{sum[$1]+=$2; count[$1]++} END {for (t in sum) printf "    %-30s %d\n", t, sum[t]/count[t]}' | sort -k2 -rn
}

cmd_errors() {
    header "Error Log Entries"
    require_log_file
    require_jq
    
    local count
    count=$(jq -r 'select(.status == "error" or .level == "ERROR") | .ts' "$LOG_FILE" | wc -l | tr -d ' ')
    
    if [ "$count" = "0" ]; then
        success "No errors found"
        return 0
    fi
    
    warn "Found $count error(s):\n"
    
    jq -c 'select(.status == "error" or .level == "ERROR")' "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_auth() {
    header "Auth Events"
    require_log_file
    require_jq
    
    jq -c 'select(.event == "auth")' "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
    
    echo ""
    echo -e "  ${BOLD}Auth summary:${NC}"
    jq -r 'select(.event == "auth") | .status' "$LOG_FILE" | sort | uniq -c | sort -rn | while read -r count status; do
        local color="$GREEN"
        [ "$status" = "error" ] && color="$RED"
        [ "$status" = "disabled" ] && color="$YELLOW"
        echo -e "    ${color}${status}${NC}: $count"
    done
}

cmd_filter_key() {
    local key_prefix="$1"
    header "Logs for key: ${key_prefix}..."
    require_log_file
    require_jq
    
    jq -c "select(.key_id | startswith(\"$key_prefix\"))" "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_filter_tool() {
    local tool_name="$1"
    header "Logs for tool: ${tool_name}"
    require_log_file
    require_jq
    
    jq -c "select(.tool == \"$tool_name\")" "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_filter_ip() {
    local ip="$1"
    header "Logs for IP: ${ip}"
    require_log_file
    require_jq
    
    jq -c "select(.origin_ip == \"$ip\")" "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_filter_since() {
    local since="$1"
    header "Logs since: ${since}"
    require_log_file
    require_jq
    
    jq -c "select(.ts >= \"$since\")" "$LOG_FILE" | while IFS= read -r line; do
        colorize_line "$line"
    done
}

cmd_json() {
    require_log_file
    cat "$LOG_FILE"
}

cmd_do_logs() {
    header "Streaming from DigitalOcean (Live Production Logs)"
    
    if ! command -v doctl &> /dev/null; then
        error "doctl not found. Install: brew install doctl"
        exit 1
    fi
    
    local app_id
    app_id=$(doctl apps list --format ID,Spec.Name --no-header 2>/dev/null | grep "$APP_NAME" | awk '{print $1}' | head -1)
    
    if [ -z "$app_id" ]; then
        error "App '$APP_NAME' not found on DigitalOcean"
        exit 1
    fi
    
    info "App ID: $app_id"
    info "Auto-reconnect enabled (will resume on connection loss)"
    info "Press Ctrl+C to stop\n"
    
    local reconnect_count=0
    local max_backoff=30  # max seconds between retries

    while true; do
        if [ $reconnect_count -gt 0 ]; then
            # Exponential backoff: 2, 4, 8, 16, 30, 30, ...
            local delay=$(( 2 ** reconnect_count ))
            [ $delay -gt $max_backoff ] && delay=$max_backoff
            warn "Connection lost. Reconnecting in ${delay}s... (attempt #$reconnect_count)"
            sleep "$delay"
        fi

        # Stream console logs (will exit on disconnect/error/stream rotation)
        doctl apps logs "$app_id" --type=run --follow 2>&1
        local exit_code=$?

        # Only stop on user interrupt (Ctrl+C → 130, SIGTERM → 143)
        if [ $exit_code -eq 130 ] || [ $exit_code -eq 143 ]; then
            break
        fi

        # doctl can exit 0 when DO rotates the log stream — reconnect
        reconnect_count=$((reconnect_count + 1))
    done

    [ $reconnect_count -gt 0 ] && info "Total reconnections: $reconnect_count"
}

cmd_stats() {
    header "IVD MCP Usage Statistics"
    require_log_file
    require_jq
    
    local total_lines first_ts last_ts
    total_lines=$(wc -l < "$LOG_FILE" | tr -d ' ')
    first_ts=$(head -1 "$LOG_FILE" | jq -r '.ts // "?"' 2>/dev/null | cut -c1-10)
    last_ts=$(tail -1 "$LOG_FILE" | jq -r '.ts // "?"' 2>/dev/null | cut -c1-10)
    
    echo -e "  ${BOLD}Log period:${NC}      $first_ts → $last_ts"
    echo -e "  ${BOLD}Total records:${NC}   $total_lines"
    echo ""
    
    # Tool calls
    local tool_total tool_ok tool_err
    tool_total=$(jq -r 'select(.event == "tool_call") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    tool_ok=$(jq -r 'select(.event == "tool_call" and .status == "ok") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    tool_err=$(jq -r 'select(.event == "tool_call" and .status == "error") | .tool' "$LOG_FILE" | wc -l | tr -d ' ')
    
    echo -e "  ${BOLD}── Tool Calls ──${NC}"
    echo -e "  Total:       $tool_total"
    echo -e "  ${GREEN}Success:${NC}     $tool_ok"
    echo -e "  ${RED}Errors:${NC}      $tool_err"
    echo ""
    
    echo -e "  ${BOLD}Top tools:${NC}"
    jq -r 'select(.event == "tool_call") | .tool' "$LOG_FILE" | sort | uniq -c | sort -rn | head -5 | while read -r count tool; do
        printf "    %-30s %s calls\n" "$tool" "$count"
    done
    echo ""
    
    # Unique users (by key_id)
    echo -e "  ${BOLD}── Users (by key) ──${NC}"
    jq -r 'select(.event == "tool_call") | .key_id' "$LOG_FILE" | sort -u | while read -r key; do
        local calls
        calls=$(jq -r "select(.event == \"tool_call\" and .key_id == \"$key\") | .tool" "$LOG_FILE" | wc -l | tr -d ' ')
        echo -e "    ${DIM}${key}${NC}:  $calls calls"
    done
    echo ""
    
    # Unique IPs
    echo -e "  ${BOLD}── Origin IPs ──${NC}"
    jq -r 'select(.event == "tool_call") | .origin_ip' "$LOG_FILE" | sort | uniq -c | sort -rn | head -10 | while read -r count ip; do
        printf "    %-20s %s calls\n" "$ip" "$count"
    done
    echo ""
    
    # Auth events
    local auth_total
    auth_total=$(jq -r 'select(.event == "auth") | .status' "$LOG_FILE" | wc -l | tr -d ' ')
    echo -e "  ${BOLD}── Auth Events ──${NC}"
    echo -e "  Total:  $auth_total"
    jq -r 'select(.event == "auth") | .status' "$LOG_FILE" | sort | uniq -c | sort -rn | while read -r count status; do
        local color="$GREEN"
        [ "$status" = "error" ] && color="$RED"
        [ "$status" = "disabled" ] && color="$YELLOW"
        echo -e "    ${color}${status}${NC}: $count"
    done
}

cmd_files() {
    header "Log Files"
    
    if [ ! -d "$LOG_DIR" ]; then
        error "Log directory not found: $LOG_DIR"
        exit 1
    fi
    
    info "Directory: $LOG_DIR\n"
    
    local total_size=0
    local file_count=0
    
    for f in "$LOG_DIR"/ivd_mcp.log*; do
        [ -f "$f" ] || continue
        local size name
        size=$(wc -c < "$f" | tr -d ' ')
        name=$(basename "$f")
        local human_size
        
        if [ "$size" -gt 1048576 ]; then
            human_size="$(echo "scale=1; $size/1048576" | bc)M"
        elif [ "$size" -gt 1024 ]; then
            human_size="$(echo "scale=1; $size/1024" | bc)K"
        else
            human_size="${size}B"
        fi
        
        local lines
        lines=$(wc -l < "$f" | tr -d ' ')
        
        printf "  %-40s %8s  %6s lines\n" "$name" "$human_size" "$lines"
        total_size=$((total_size + size))
        file_count=$((file_count + 1))
    done
    
    echo ""
    local total_human
    if [ "$total_size" -gt 1048576 ]; then
        total_human="$(echo "scale=1; $total_size/1048576" | bc)M"
    elif [ "$total_size" -gt 1024 ]; then
        total_human="$(echo "scale=1; $total_size/1024" | bc)K"
    else
        total_human="${total_size}B"
    fi
    
    echo -e "  ${BOLD}Total:${NC} $file_count file(s), $total_human"
}

# ── Main ───────────────────────────────────────────────────────────────────────

main() {
    case "${1:-}" in
        --local)      cmd_stream ;;
        --tail)       cmd_tail "${2:-20}" ;;
        --tools)      cmd_tools ;;
        --errors)     cmd_errors ;;
        --auth)       cmd_auth ;;
        --key)        [ -z "${2:-}" ] && { error "Usage: $0 --key <partial_key>"; exit 1; }; cmd_filter_key "$2" ;;
        --tool)       [ -z "${2:-}" ] && { error "Usage: $0 --tool <tool_name>"; exit 1; }; cmd_filter_tool "$2" ;;
        --ip)         [ -z "${2:-}" ] && { error "Usage: $0 --ip <ip_address>"; exit 1; }; cmd_filter_ip "$2" ;;
        --since)      [ -z "${2:-}" ] && { error "Usage: $0 --since <YYYY-MM-DD>"; exit 1; }; cmd_filter_since "$2" ;;
        --json)       cmd_json ;;
        --stats)      cmd_stats ;;
        --files)      cmd_files ;;
        --help|-h)
            echo "Usage: $0 [command]"
            echo ""
            echo "Streaming:"
            echo "  (default)              Stream from DigitalOcean console (live, auto-reconnect)"
            echo "  --local                Stream local log file (colored, live)"
            echo "  --tail [N]             Show last N lines from local (default: 20)"
            echo ""
            echo "Reports (local logs only):"
            echo "  --tools                Tool call summary (counts, avg duration)"
            echo "  --errors               Show only errors"
            echo "  --auth                 Show auth events"
            echo "  --stats                Full usage statistics"
            echo "  --files                List log files with sizes"
            echo ""
            echo "Filters (local logs only):"
            echo "  --key <partial_key>    Filter by partial API key (e.g. O9T4HnV6)"
            echo "  --tool <tool_name>     Filter by tool (e.g. ivd_search)"
            echo "  --ip <ip_address>      Filter by origin IP"
            echo "  --since <YYYY-MM-DD>   Filter entries since date"
            echo ""
            echo "Raw (local logs only):"
            echo "  --json                 Raw JSON output (pipe to jq)"
            echo ""
            echo "Examples:"
            echo "  $0                                     # Stream from DO (default)"
            echo "  $0 --local                             # Stream local file"
            echo "  $0 --stats                             # Local usage report"
            echo "  $0 --tool ivd_search                   # Local search tool logs"
            echo "  $0 --json | jq '.tool'                 # Pipe to jq"
            echo "  $0 --since 2026-02-08 | head -20       # Today's local logs"
            ;;
        "")           cmd_do_logs ;;
        *)            error "Unknown command: $1. Use --help"; exit 1 ;;
    esac
}

main "$@"
