# mcp_server/auth.py

"""
Authentication for IVD MCP server.

Reads API keys from IVD_API_KEYS environment variable.

For local/stdio: auth not required (process isolation).
For remote/SSE:  API key required in Authorization header:
    Authorization: Bearer <api_key>
"""

import hashlib
import os
import secrets
from functools import wraps
from typing import Optional

from starlette.responses import JSONResponse
from termcolor import colored

# Environment-based API keys (comma-separated)
_raw_keys = os.environ.get("IVD_API_KEYS", "")
VALID_API_KEYS = {k.strip() for k in _raw_keys.split(",") if k.strip()}

# Disable auth for local development
MCP_AUTH_DISABLED = os.environ.get("MCP_AUTH_DISABLED", "false").lower() == "true"

# Component name for logging
AUTH = "IVD Auth"


async def validate_api_key(request) -> Optional[JSONResponse]:
    """
    Validate API key from request headers.

    Returns:
        None if auth successful, JSONResponse with error otherwise
    """
    if MCP_AUTH_DISABLED:
        print(colored(f"[{AUTH}] Auth disabled — allowing request", "yellow"))
        return None

    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        print(colored(f"[{AUTH}] Missing Authorization header", "red"))
        return JSONResponse({"error": "Missing Authorization header"}, status_code=401)

    if not auth_header.startswith("Bearer "):
        print(colored(f"[{AUTH}] Invalid header format (not Bearer)", "red"))
        return JSONResponse(
            {"error": "Invalid Authorization header format. Expected: Bearer <token>"},
            status_code=401,
        )

    api_key = auth_header[7:]

    if not api_key:
        print(colored(f"[{AUTH}] Empty API key", "red"))
        return JSONResponse({"error": "Empty API key"}, status_code=401)

    if not VALID_API_KEYS:
        # No keys configured — fall back to auth disabled behavior
        print(colored(f"[{AUTH}] No API keys configured, allowing request", "yellow"))
        return None

    if api_key not in VALID_API_KEYS:
        print(colored(f"[{AUTH}] Invalid API key", "red"))
        return JSONResponse({"error": "Invalid API key"}, status_code=401)

    print(colored(f"[{AUTH}] API key valid", "green"))
    return None


def require_auth(func):
    """Decorator to require authentication for a route handler."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        auth_result = await validate_api_key(request)
        if auth_result is not None:
            return auth_result
        return await func(request, *args, **kwargs)
    return wrapper


def generate_api_key() -> str:
    """Generate a new random API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for secure storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()
