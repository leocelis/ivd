# mcp_server/env_check.py

"""
Environment variable validation for IVD MCP Server.

Single source of truth for required environment variables.
Used by:
  - server.py     → validates at boot (refuses to start if missing)
  - deploy.sh     → validates before deploy (gates on missing vars)
  - test suite    → prevents regressions

When adding a new env var dependency:
  1. Add it here (REQUIRED_ENV_VARS_REMOTE or REQUIRED_ENV_VARS_ALL)
  2. Add it to .do/app.yaml
  3. Add it to .env and .env.example
  4. Update mcp_server_intent.yaml deployment section
"""

import os
from typing import Dict, List, Tuple

from termcolor import colored

NAME = "IVD MCP"

# ── Required Environment Variables ────────────────────────────────────────────

# Required for REMOTE (SSE/StreamableHTTP) transport only.
# These are needed when running on DigitalOcean or any production server.
REQUIRED_ENV_VARS_REMOTE: Dict[str, str] = {
    "IVD_API_KEYS": "API key auth for remote MCP clients (comma-separated)",
    "OPENAI_API_KEY": "OpenAI API key for ivd_search embedding generation",
    "REDIS_URL": "Redis connection URL for session resumability",
}

# Required for ALL transports (stdio + remote).
# Currently empty — tools that need env vars at runtime are gated by REMOTE.
REQUIRED_ENV_VARS_ALL: Dict[str, str] = {}


def validate_env(transport: str = "sse") -> Tuple[bool, List[str]]:
    """
    Validate that all required environment variables are set.

    Args:
        transport: "stdio" or "sse" (remote). Determines which vars are checked.

    Returns:
        Tuple of (all_ok, list_of_missing_var_names).
        If all_ok is True, list is empty.
    """
    required = dict(REQUIRED_ENV_VARS_ALL)

    if transport != "stdio":
        required.update(REQUIRED_ENV_VARS_REMOTE)

    missing = []
    for var, description in required.items():
        value = os.environ.get(var, "").strip()
        if not value:
            missing.append(var)

    return (len(missing) == 0, missing)


def check_and_warn(transport: str = "sse") -> None:
    """
    Validate env vars and print warnings for missing ones.

    Called at server boot. For remote transport, exits with error code 1
    if any required vars are missing.

    Args:
        transport: "stdio" or "sse" (remote)
    """
    all_ok, missing = validate_env(transport)

    if all_ok:
        print(colored(f"[{NAME}] All required environment variables present", "green"))
        return

    # Build a clear error message
    required = dict(REQUIRED_ENV_VARS_ALL)
    if transport != "stdio":
        required.update(REQUIRED_ENV_VARS_REMOTE)

    print(colored(f"[{NAME}] FATAL: Missing required environment variables:", "red"))
    for var in missing:
        desc = required.get(var, "")
        print(colored(f"[{NAME}]   - {var}: {desc}", "red"))

    if transport != "stdio":
        print(colored(f"[{NAME}] Server cannot start with missing variables.", "red"))
        print(colored(f"[{NAME}] Add them to .do/app.yaml and redeploy.", "red"))
        raise SystemExit(1)
    else:
        # stdio mode: warn but don't block (local dev may not need all vars)
        print(colored(f"[{NAME}] WARNING: Some tools may fail without these variables.", "yellow"))
