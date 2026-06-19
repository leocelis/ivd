#!/usr/bin/env python3
"""stop — block agent completion while IVD client_enforcement gating is active."""

import json
import sys
from pathlib import Path

STATE_FILE = Path(".ivd/client_gating_state.json")
MAX_LOOP = 5


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    status = payload.get("status", "completed")
    if status == "aborted":
        print("{}")
        return 0

    loop_count = payload.get("loop_count", 0)
    if loop_count >= MAX_LOOP:
        print("{}")
        return 0

    if not STATE_FILE.is_file():
        print("{}")
        return 0

    try:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        print("{}")
        return 0

    if not state.get("implementation_complete_blocked"):
        print("{}")
        return 0

    gates = state.get("active_gates") or []
    gate_text = ", ".join(str(g) for g in gates) if gates else "active"
    event = state.get("monitoring_event", "verification_gating_active")
    clear = state.get("clear_when") or []
    clear_hint = clear[0] if clear else "Re-run ivd_validate after clearing gating conditions."

    message = (
        f"IVD {event}: implementation completion blocked ({gate_text}). "
        f"{clear_hint} Do not mark this task done until client_enforcement clears."
    )
    print(json.dumps({"followup_message": message}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
