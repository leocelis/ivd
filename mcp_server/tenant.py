# mcp_server/tenant.py

"""
Host-derived tenant keys for the hosted IVD MCP server.

A host app shares one secret with the server and derives a key per tenant:

    key = "ivd_" + tenant + "_" + base64url_nopad(HMAC-SHA256(SECRET, "ivd:" + VERSION + ":" + tenant))

The server recomputes the MAC to verify a key. Nothing is stored or provisioned.
A request made with a tenant key runs as that tenant and may only call the
content-only tools in ``TENANT_TOOLS``; no tenant call touches the server's disk.

Settings (read on every call, so rotation and revocation need no restart):
    IVD_TENANT_KEY_SECRET    shared secret; unset -> the feature is off
    IVD_TENANT_KEY_VERSIONS  comma-separated accepted versions (default "v1")
    IVD_REVOKED_TENANTS      comma-separated tenants whose keys are refused
"""

import base64
import copy
import hashlib
import hmac
import os
import re
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterable, List, Optional

KEY_PREFIX = "ivd_"
PRODUCT = "ivd"
MAC_LENGTH = 43  # base64url, no padding, of a 32-byte HMAC-SHA256
TENANT_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,55}$")

# The content-only tools a tenant key may call. Nothing else is listed or run.
TENANT_TOOLS = ("ivd_validate", "ivd_review_intent", "canon_check")
# Arguments that name a path on the server's disk. Refused, never ignored.
REFUSED_ARGUMENTS = ("project_root", "workspace_root")

# Scope for the resumable-stream event store: each identity's events live under
# its own key, so one caller can never replay another caller's stream.
event_scope: ContextVar[Optional[str]] = ContextVar("ivd_event_scope", default=None)


@dataclass(frozen=True)
class Identity:
    """Who a request runs as. ``tenant`` is None for an operator key."""

    kind: str  # "operator" | "tenant"
    principal: str  # stable id, never the key itself
    tenant: Optional[str] = None


def operator_identity(api_key: str) -> Identity:
    digest = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return Identity(kind="operator", principal=f"operator:{digest}")


def tenant_identity(tenant: str) -> Identity:
    return Identity(kind="tenant", principal=f"tenant:{tenant}", tenant=tenant)


def secret() -> str:
    return os.environ.get("IVD_TENANT_KEY_SECRET", "")


def accepted_versions() -> List[str]:
    raw = os.environ.get("IVD_TENANT_KEY_VERSIONS", "v1")
    return [v.strip() for v in raw.split(",") if v.strip()]


def revoked_tenants() -> set:
    raw = os.environ.get("IVD_REVOKED_TENANTS", "")
    return {t.strip() for t in raw.split(",") if t.strip()}


def _mac(secret_value: str, version: str, tenant: str) -> str:
    message = f"{PRODUCT}:{version}:{tenant}".encode()
    digest = hmac.new(secret_value.encode(), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def derive_key(secret_value: str, version: str, tenant: str) -> str:
    """The key a host gives to ``tenant`` (the host runs the same formula)."""
    if not TENANT_RE.match(tenant):
        raise ValueError("tenant must match ^[a-z0-9][a-z0-9-]{0,55}$")
    return f"{KEY_PREFIX}{tenant}_{_mac(secret_value, version, tenant)}"


def parse_tenant(api_key: str) -> Optional[str]:
    """The tenant named in a key, or None when the key is not tenant-shaped.

    The tenant is the text between the prefix and the last 44 characters
    ("_" + 43-character MAC). It is never found by splitting on "_", because a
    base64url MAC can contain "_".
    """
    if not api_key.startswith(KEY_PREFIX):
        return None
    body = api_key[len(KEY_PREFIX):]
    if len(body) < MAC_LENGTH + 2 or body[-(MAC_LENGTH + 1)] != "_":
        return None
    tenant = body[: -(MAC_LENGTH + 1)]
    return tenant if TENANT_RE.match(tenant) else None


def verify_tenant_key(api_key: str) -> "tuple[Optional[str], Optional[str]]":
    """Return (tenant, None) for a valid key, or (tenant_or_None, reason)."""
    secret_value = secret()
    if not secret_value:
        return None, "tenant_keys_disabled"
    tenant = parse_tenant(api_key)
    if tenant is None:
        return None, "invalid_tenant_key_format"
    presented = api_key[-MAC_LENGTH:]
    matched = False
    for version in accepted_versions():
        # Every accepted version is compared, in constant time, so timing does
        # not tell which version (if any) came close.
        if hmac.compare_digest(presented, _mac(secret_value, version, tenant)):
            matched = True
    if not matched:
        return tenant, "invalid_tenant_key"
    if tenant in revoked_tenants():
        return tenant, "revoked_tenant"
    return tenant, None


# ── What a tenant may call ────────────────────────────────────────────────────

def tenant_tool_list(tools: Iterable) -> list:
    """The allowed tools, with path arguments removed from their schemas."""
    out = []
    for tool in tools:
        if tool.name not in TENANT_TOOLS:
            continue
        schema = copy.deepcopy(tool.inputSchema or {})
        props = schema.get("properties") or {}
        for arg in REFUSED_ARGUMENTS:
            props.pop(arg, None)
        required = schema.get("required")
        if isinstance(required, list):
            schema["required"] = [r for r in required if r not in REFUSED_ARGUMENTS]
        out.append(tool.model_copy(update={"inputSchema": schema}))
    return out


def tenant_refusal(tool_name: str, arguments: Optional[dict]) -> Optional[str]:
    """A refusal message when a tenant may not make this call, else None."""
    if tool_name not in TENANT_TOOLS:
        return f"Error: tool '{tool_name}' is not available with a tenant key"
    for arg in REFUSED_ARGUMENTS:
        if arguments and arg in arguments:
            return f"Error: argument '{arg}' is not accepted with a tenant key"
    return None
