#!/usr/bin/env python3
"""postToolUse — capture client_enforcement from ivd_validate / ivd_review_intent."""

import json
import sys
from pathlib import Path

STATE_DIR = Path(".ivd")
STATE_FILE = STATE_DIR / "client_gating_state.json"
IVD_TOOLS = ("ivd_validate", "ivd_review_intent")


def _tool_name(payload: dict) -> str:
    for key in ("tool_name", "name", "tool", "mcpToolName"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


def _tool_output(payload: dict) -> str:
    for key in ("tool_output", "result", "output", "response"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def _matches_ivd_tool(name: str) -> bool:
    lower = name.lower()
    return any(t in lower for t in IVD_TOOLS)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    name = _tool_name(payload)
    if not _matches_ivd_tool(name):
        return 0

    raw = _tool_output(payload)
    if not raw:
        return 0

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    enforcement = data.get("client_enforcement")
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if enforcement and enforcement.get("implementation_complete_blocked"):
        STATE_FILE.write_text(json.dumps(enforcement, indent=2), encoding="utf-8")
    else:
        if STATE_FILE.exists():
            STATE_FILE.unlink()

    return 0


if __name__ == "__main__":
    sys.exit(main())
