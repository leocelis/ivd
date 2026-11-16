# mcp_server/auth.py

"""
Authentication for IVD MCP server.

Reads API keys from IVD_API_KEYS environment variable.

For local/stdio: auth not required (process isolation).
For remote/SSE:  API key required in Authorization header:
    Authorization: Bearer <api_key>

A key is either an operator key (listed in IVD_API_KEYS, full tool set) or,
when IVD_TENANT_KEY_SECRET is set, a host-derived tenant key (see
mcp_server/tenant.py). The identity a request runs as is recorded on the
request scope ("ivd_identity"), and as an authenticated user so the MCP
transports bind each session to the identity that opened it.
"""

import hashlib
import os
import secrets
from functools import wraps
from typing import Optional, Tuple

from mcp.server.auth.middleware.bearer_auth import AuthenticatedUser
from mcp.server.auth.provider import AccessToken
from starlette.responses import JSONResponse

from mcp_server import tenant as tenant_keys
from mcp_server.logger import extract_key_id, extract_origin_ip, log_auth_event

# Environment-based API keys (comma-separated)
_raw_keys = os.environ.get("IVD_API_KEYS", "")
VALID_API_KEYS = {k.strip() for k in _raw_keys.split(",") if k.strip()}

# Disable auth for local development
MCP_AUTH_DISABLED = os.environ.get("MCP_AUTH_DISABLED", "false").lower() == "true"


async def validate_api_key(request) -> Tuple[Optional[JSONResponse], Optional[str]]:
    """
    Validate API key from request headers.

    Returns:
        Tuple of (auth_result, api_key):
        - auth_result: None if successful, JSONResponse with error otherwise
        - api_key: The validated API key (for logging) or None
    """
    origin_ip = extract_origin_ip(request)
    
    if MCP_AUTH_DISABLED:
        log_auth_event(
            status="disabled",
            key_id="none",
            origin_ip=origin_ip,
            error="Auth disabled via MCP_AUTH_DISABLED",
        )
        return None, None

    auth_header = request.headers.get("Authorization", "")

    if not auth_header:
        log_auth_event(
            status="error",
            key_id="none",
            origin_ip=origin_ip,
            error="missing_authorization_header",
        )
        return JSONResponse({"error": "Missing Authorization header"}, status_code=401), None

    if not auth_header.startswith("Bearer "):
        log_auth_event(
            status="error",
            key_id="none",
            origin_ip=origin_ip,
            error="invalid_header_format",
        )
        return JSONResponse(
            {"error": "Invalid Authorization header format. Expected: Bearer <token>"},
            status_code=401,
        ), None

    api_key = auth_header[7:]

    if not api_key:
        log_auth_event(
            status="error",
            key_id="none",
            origin_ip=origin_ip,
            error="empty_api_key",
        )
        return JSONResponse({"error": "Empty API key"}, status_code=401), None

    if api_key not in VALID_API_KEYS and tenant_keys.secret():
        # Tenant keys are on. A key that is not an operator key must be a valid
        # tenant key; the "no keys configured" fallback below never applies,
        # or any made-up key would get the full tool set.
        return _validate_tenant_key(request, api_key, origin_ip)

    if not VALID_API_KEYS:
        # No keys configured — fall back to auth disabled behavior
        log_auth_event(
            status="disabled",
            key_id="none",
            origin_ip=origin_ip,
            error="No API keys configured",
        )
        return None, None

    if api_key not in VALID_API_KEYS:
        log_auth_event(
            status="error",
            key_id=extract_key_id(api_key),
            origin_ip=origin_ip,
            error="invalid_api_key",
        )
        return JSONResponse({"error": "Invalid API key"}, status_code=401), None

    # Success
    log_auth_event(
        status="ok",
        key_id=extract_key_id(api_key),
        origin_ip=origin_ip,
    )
    _record_identity(request, tenant_keys.operator_identity(api_key))
    return None, api_key


def _validate_tenant_key(request, api_key: str, origin_ip: str):
    """Verify a host-derived tenant key. The tenant, never the key, is logged."""
    tenant, reason = tenant_keys.verify_tenant_key(api_key)
    if reason is not None:
        log_auth_event(
            status="error",
            key_id=f"tenant:{tenant}" if tenant else "invalid",
            origin_ip=origin_ip,
            error=reason,
            tenant=tenant,
        )
        return JSONResponse({"error": "Invalid API key"}, status_code=401), None
    log_auth_event(
        status="ok",
        key_id=f"tenant:{tenant}",
        origin_ip=origin_ip,
        tenant=tenant,
    )
    _record_identity(request, tenant_keys.tenant_identity(tenant))
    return None, api_key


def _record_identity(request, identity: "tenant_keys.Identity") -> None:
    """Attach the identity to this request's scope.

    The MCP transports build their per-message request from the same scope, so
    tool handlers read the identity of each message, not of the session's
    first request. Setting ``user`` makes the SDK refuse a session continued
    with a key that resolves to a different identity.
    """
    scope = getattr(request, "scope", None)
    if not isinstance(scope, dict):
        return
    scope["ivd_identity"] = identity
    scope["user"] = AuthenticatedUser(
        AccessToken(token="", client_id=identity.principal, scopes=[])
    )


def request_identity(request) -> "Optional[tenant_keys.Identity]":
    """The identity recorded for a request by validate_api_key, if any."""
    scope = getattr(request, "scope", None)
    if not isinstance(scope, dict):
        return None
    return scope.get("ivd_identity")


def require_auth(func):
    """Decorator to require authentication for a route handler."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        auth_result, api_key = await validate_api_key(request)
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
