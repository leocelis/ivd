# mcp_server/compliance.py

"""
Runtime ComplyEdge enforcement around every MCP tool call.

Off unless the server has COMPLYEDGE_API_KEY. When on, each tool call is
checked twice through POST /v1/check (ComplyEdge API reference):

  1. the arguments, direction "prompt", before the tool runs
  2. the result,    direction "output", before it is returned

A blocked check replaces the tool's answer with the rule that fired. If
ComplyEdge cannot be reached the tool still answers: an outage of the
compliance service never breaks IVD (fail-open, logged).

Attribution on every check (the three fields ComplyEdge writes on the audit
record):
  user_id    "ivdkey:<sha256 prefix>" of the caller's IVD API key, never the
             key; "local:<login>" over stdio
  user_role  "mcp_client" (remote) or "maintainer" (stdio)
  session_id the MCP session (Mcp-Session-Id header, or ?session_id= on SSE)

Env:
  COMPLYEDGE_API_KEY      turns the checks on (never commit it)
  COMPLYEDGE_API_URL      default https://api.complyedge.io
  COMPLYEDGE_AGENT_ID     default ivd-mcp
  COMPLYEDGE_JURISDICTION default EU
  COMPLYEDGE_TIMEOUT_S    default 5
"""

from __future__ import annotations

import getpass
import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

MAX_TEXT = 50000  # /v1/check rejects text longer than this


@dataclass
class Verdict:
    """Outcome of one check. checked=False means ComplyEdge was not consulted."""

    allowed: bool = True
    checked: bool = False
    violations: list = field(default_factory=list)
    event_id: Optional[str] = None
    error: Optional[str] = None


def enabled() -> bool:
    return bool(os.environ.get("COMPLYEDGE_API_KEY", "").strip())


def attribution(api_key: Optional[str], request: Optional[Any]) -> dict:
    """user_id / user_role / session_id for the audit record. Never a credential."""
    if api_key:
        digest = hashlib.sha256(api_key.encode()).hexdigest()[:12]
        ctx = {"user_id": f"ivdkey:{digest}", "user_role": "mcp_client"}
    else:
        try:
            login = os.environ.get("USER") or getpass.getuser()
        except Exception:
            login = "unknown"
        ctx = {"user_id": f"local:{login}", "user_role": "maintainer"}
    session = _session_id(request)
    if session:
        ctx["session_id"] = session
    return ctx


def _session_id(request: Optional[Any]) -> Optional[str]:
    if request is None:
        return None
    try:
        sid = request.headers.get("mcp-session-id")
        if not sid and getattr(request, "query_params", None) is not None:
            sid = request.query_params.get("session_id")
        return sid or None
    except Exception:
        return None


def check(text: str, direction: str, context: dict) -> Verdict:
    """One /v1/check call. Fail-open: any transport or server error allows."""
    key = os.environ.get("COMPLYEDGE_API_KEY", "").strip()
    if not key:
        return Verdict()
    url = os.environ.get("COMPLYEDGE_API_URL", "https://api.complyedge.io").rstrip("/")
    body = {
        "text": text[:MAX_TEXT],
        "agent_id": os.environ.get("COMPLYEDGE_AGENT_ID", "ivd-mcp"),
        "jurisdiction": os.environ.get("COMPLYEDGE_JURISDICTION", "EU"),
        "direction": direction,
        "context": context,
    }
    try:
        resp = httpx.post(
            f"{url}/v1/check",
            json=body,
            headers={"Authorization": f"Bearer {key}"},
            timeout=float(os.environ.get("COMPLYEDGE_TIMEOUT_S", "5")),
        )
        if resp.status_code != 200:
            return Verdict(error=f"HTTP {resp.status_code}")
        data = resp.json()
        return Verdict(
            allowed=bool(data.get("allowed", True)),
            checked=True,
            violations=data.get("violations") or [],
            event_id=data.get("event_id"),
        )
    except Exception as exc:  # network, timeout, bad JSON
        return Verdict(error=type(exc).__name__)


def arguments_text(tool_name: str, arguments: dict) -> str:
    return f"{tool_name} {json.dumps(arguments, default=str, sort_keys=True)}"


def blocked_message(tool_name: str, stage: str, verdict: Verdict) -> str:
    """What the client sees instead of the tool's answer when a check blocks."""
    rules = [
        f"- {v.get('rule_id', 'rule')}: {v.get('rule_description') or v.get('reason') or ''}".rstrip(": ")
        for v in verdict.violations
    ] or ["- no rule detail returned"]
    return "\n".join(
        [
            f"Blocked by ComplyEdge: the {stage} of {tool_name} failed the EU AI Act check.",
            *rules,
            f"Audit event: {verdict.event_id or 'n/a'}",
        ]
    )
