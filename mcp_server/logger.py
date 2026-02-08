# mcp_server/logger.py

"""
Structured logging for IVD MCP Server using Python logging stdlib.

Implements:
- Colored console output (human-readable, always)
- Rotating JSON log files (daily rotation, configurable retention)
- Third-party handler extensibility (Datadog, Papertrail, etc.)
- Rich dimensions: tool name, duration, status, partial key, origin IP, payload/response previews
- Security: no full secrets, redacts sensitive fields

Configuration (environment variables):
- LOG_DIR: Directory for log files (default: mcp_server/logs/)
- LOG_RETENTION_DAYS: Number of daily logs to retain (default: 365)
- LOG_LEVEL: Minimum log level (default: INFO)

Usage:
    from mcp_server.logger import log_tool_call, log_auth_event

    log_tool_call(
        tool="ivd_search",
        duration_ms=670,
        status="ok",
        key_id="O9T4HnV6...",
        origin_ip="45.123.45.67",
        payload_preview='{"query": "What are the eight principles?"}',
        response_preview="**Result 1** (similarity: 0.57)...",
    )

Intent artifact: mcp_server/logger_intent.yaml
Recipe: infra-structured-logging.yaml
"""

import json
import logging
import logging.handlers
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# ==============================================================================
# Configuration
# ==============================================================================

LOG_DIR = Path(os.environ.get("LOG_DIR", "mcp_server/logs/"))
LOG_RETENTION_DAYS = int(os.environ.get("LOG_RETENTION_DAYS", "365"))
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# ANSI Color Codes for Console
# ==============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright foreground
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"


# ==============================================================================
# Custom Formatters
# ==============================================================================

class ColoredConsoleFormatter(logging.Formatter):
    """Colored, human-readable formatter for console output."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.DIM + Colors.WHITE,
        logging.INFO: Colors.CYAN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        try:
            level_color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
            level_name = f"{level_color}[{record.levelname}]{Colors.RESET}"
            
            # Timestamp
            ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
            
            # Event type (from extra fields)
            event = getattr(record, "event", "log")
            
            # Build compact line based on event type
            if event == "tool_call":
                tool = getattr(record, "tool", "unknown")
                duration_ms = getattr(record, "duration_ms", 0)
                status = getattr(record, "status", "unknown")
                key_id = getattr(record, "key_id", "none")
                origin_ip = getattr(record, "origin_ip", "local")
                
                # Color status
                status_colored = status
                if status == "ok":
                    status_colored = f"{Colors.GREEN}{status}{Colors.RESET}"
                elif status == "error":
                    status_colored = f"{Colors.RED}{status}{Colors.RESET}"
                
                return (
                    f"{ts} {level_name}  {Colors.BOLD}{event}{Colors.RESET}  "
                    f"{Colors.BRIGHT_CYAN}{tool}{Colors.RESET}  "
                    f"{duration_ms}ms  {status_colored}  "
                    f"key={Colors.DIM}{key_id}{Colors.RESET}  "
                    f"ip={Colors.DIM}{origin_ip}{Colors.RESET}"
                )
            
            elif event == "auth":
                status = getattr(record, "status", "unknown")
                key_id = getattr(record, "key_id", "none")
                origin_ip = getattr(record, "origin_ip", "local")
                error = getattr(record, "error", "")
                
                # Color status
                status_colored = status
                if status == "ok":
                    status_colored = f"{Colors.GREEN}{status}{Colors.RESET}"
                elif status == "error":
                    status_colored = f"{Colors.RED}{status}{Colors.RESET}"
                elif status == "disabled":
                    status_colored = f"{Colors.YELLOW}{status}{Colors.RESET}"
                
                line = (
                    f"{ts} {level_name}  {Colors.BOLD}{event}{Colors.RESET}  "
                    f"{status_colored}  "
                    f"key={Colors.DIM}{key_id}{Colors.RESET}  "
                    f"ip={Colors.DIM}{origin_ip}{Colors.RESET}"
                )
                if error:
                    line += f"  {Colors.RED}error={error}{Colors.RESET}"
                return line
            
            else:
                # Generic log message
                return f"{ts} {level_name}  {record.getMessage()}"
        
        except Exception:
            # Fallback: plain format if anything goes wrong
            return f"{record.levelname}: {record.getMessage()}"


class JSONFileFormatter(logging.Formatter):
    """JSON formatter for rotating log files."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON line."""
        try:
            # Base fields
            log_entry: Dict[str, Any] = {
                "ts": datetime.fromtimestamp(record.created).isoformat() + "Z",
                "level": record.levelname,
            }
            
            # Add event-specific fields from extra
            for key, value in record.__dict__.items():
                if key not in {
                    "name", "msg", "args", "created", "filename", "funcName", "levelname",
                    "levelno", "lineno", "module", "msecs", "message", "pathname",
                    "process", "processName", "relativeCreated", "thread", "threadName",
                    "exc_info", "exc_text", "stack_info", "taskName",
                }:
                    log_entry[key] = value
            
            # Add message if present
            if record.msg:
                log_entry["message"] = record.getMessage()
            
            return json.dumps(log_entry, default=str)
        
        except Exception:
            # Fallback: minimal JSON
            return json.dumps({
                "ts": datetime.now().isoformat() + "Z",
                "level": "ERROR",
                "message": "Failed to format log record",
            })


# ==============================================================================
# Logger Setup
# ==============================================================================

def setup_logger() -> logging.Logger:
    """
    Create and configure the IVD MCP logger with:
    - StreamHandler (colored console output)
    - TimedRotatingFileHandler (daily rotation, JSON format)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("ivd_mcp")
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    logger.propagate = False  # Don't propagate to root logger
    
    # Remove existing handlers (in case of re-setup)
    logger.handlers.clear()
    
    # --- Console Handler (colored, human-readable) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Show all levels in console
    console_handler.setFormatter(ColoredConsoleFormatter())
    logger.addHandler(console_handler)
    
    # --- File Handler (JSON, rotating daily) ---
    log_file = LOG_DIR / "ivd_mcp.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",  # Rotate at midnight
        interval=1,  # Every 1 day
        backupCount=LOG_RETENTION_DAYS,  # Retain this many days
        encoding="utf-8",
        utc=True,  # Use UTC for rotation timing
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(JSONFileFormatter())
    logger.addHandler(file_handler)
    
    return logger


# Global logger instance
_logger = setup_logger()


# ==============================================================================
# Helper Functions
# ==============================================================================

def extract_key_id(api_key: Optional[str]) -> str:
    """
    Extract a partial key ID for logging (first 8 chars + "...").
    
    Args:
        api_key: Full API key or None
    
    Returns:
        Partial key ID (e.g., "O9T4HnV6...") or "stdio" if None
    """
    if not api_key:
        return "stdio"
    if len(api_key) <= 8:
        return api_key + "..."
    return api_key[:8] + "..."


def extract_origin_ip(request: Optional[Any]) -> str:
    """
    Extract client IP from request object.
    
    Checks X-Forwarded-For header first (for proxies like DO), then client.host.
    
    Args:
        request: Starlette request object or None
    
    Returns:
        IP address or "local" if no request
    """
    if not request:
        return "local"
    
    try:
        # Check X-Forwarded-For (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For", "")
        if forwarded_for:
            # Take first IP (original client)
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    except Exception:
        return "unknown"


def redact_sensitive(data: Any, max_length: int = 200) -> str:
    """
    Redact sensitive fields and truncate data for logging.
    
    Sensitive field patterns (case-insensitive):
    - key, token, secret, password, authorization, bearer
    
    Args:
        data: Any data structure (dict, str, list, etc.)
        max_length: Maximum characters to return
    
    Returns:
        Redacted and truncated string representation
    """
    try:
        # Convert to string first
        if isinstance(data, dict):
            data_str = json.dumps(data, default=str)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)
        
        # Redact sensitive patterns (case-insensitive)
        sensitive_patterns = [
            r'"(api_key|token|secret|password|authorization|bearer)":\s*"[^"]*"',
            r"'(api_key|token|secret|password|authorization|bearer)':\s*'[^']*'",
        ]
        
        for pattern in sensitive_patterns:
            data_str = re.sub(
                pattern,
                lambda m: f'"{m.group(1)}": "[REDACTED]"',
                data_str,
                flags=re.IGNORECASE,
            )
        
        # Truncate if too long
        if len(data_str) > max_length:
            return data_str[:max_length] + "..."
        
        return data_str
    
    except Exception:
        return "[redaction_failed]"


# ==============================================================================
# Public Logging API
# ==============================================================================

def log_tool_call(
    tool: str,
    duration_ms: int,
    status: str,
    key_id: str = "stdio",
    origin_ip: str = "local",
    payload_preview: str = "",
    response_preview: str = "",
    error: Optional[str] = None,
) -> None:
    """
    Log a tool call event.
    
    Args:
        tool: Tool name (e.g., "ivd_search")
        duration_ms: Execution time in milliseconds
        status: "ok" or "error"
        key_id: Partial API key (first 8 chars + "...")
        origin_ip: Client IP address
        payload_preview: Truncated input arguments
        response_preview: Truncated response
        error: Error message if status is "error"
    """
    try:
        level = logging.INFO if status == "ok" else logging.ERROR
        
        extra = {
            "event": "tool_call",
            "tool": tool,
            "duration_ms": duration_ms,
            "status": status,
            "key_id": key_id,
            "origin_ip": origin_ip,
        }
        
        if payload_preview:
            extra["payload_preview"] = redact_sensitive(payload_preview, 200)
        
        if response_preview:
            extra["response_preview"] = redact_sensitive(response_preview, 200)
        
        if error:
            extra["error"] = error[:500]  # Truncate errors to 500 chars
        
        _logger.log(level, "", extra=extra)
    
    except Exception:
        # Fire-and-forget: never crash on logging failure
        pass


def log_auth_event(
    status: str,
    key_id: str = "none",
    origin_ip: str = "local",
    error: Optional[str] = None,
) -> None:
    """
    Log an authentication event.
    
    Args:
        status: "ok", "error", or "disabled"
        key_id: Partial API key (first 8 chars + "...")
        origin_ip: Client IP address
        error: Rejection reason if status is "error"
    """
    try:
        level = logging.INFO if status == "ok" else logging.WARNING
        
        extra = {
            "event": "auth",
            "status": status,
            "key_id": key_id,
            "origin_ip": origin_ip,
        }
        
        if error:
            extra["error"] = error[:200]  # Truncate errors
        
        _logger.log(level, "", extra=extra)
    
    except Exception:
        # Fire-and-forget: never crash on logging failure
        pass


def log_health_check(tools_count: int) -> None:
    """
    Log a health check event.
    
    Args:
        tools_count: Number of registered tools
    """
    try:
        _logger.debug(
            "",
            extra={
                "event": "health_check",
                "status": "ok",
                "tools_count": tools_count,
            },
        )
    except Exception:
        pass


# ==============================================================================
# Module Initialization
# ==============================================================================

# Log setup completion
_logger.info(
    "",
    extra={
        "event": "logger_init",
        "log_dir": str(LOG_DIR),
        "retention_days": LOG_RETENTION_DAYS,
        "log_level": LOG_LEVEL,
    },
)
