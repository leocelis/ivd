#!/usr/bin/env python3
"""
canon/validation/validate_mcp.py  — Option B: MCP Protocol Validation

Boots the IVD MCP server as a child process via stdio, sends real JSON-RPC
requests to all four Canon tools, and writes every request/response pair to
results/.

No API key required. Tests exactly what Cursor / Claude Desktop / Cline see.
Run from the ivd/ directory:

    cd /path/to/ivd
    python -m canon.validation.validate_mcp

Output:
    canon/validation/results/mcp_<call_id>.json    — per-call request + response
    canon/validation/results/mcp_report.txt         — human-readable summary
    canon/validation/results/mcp_report.json        — machine-readable summary
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------
THIS_DIR = Path(__file__).parent
IVD_ROOT = THIS_DIR.parent.parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN  = "\033[32m" if sys.stdout.isatty() else ""
RED    = "\033[31m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
BOLD   = "\033[1m"  if sys.stdout.isatty() else ""
RESET  = "\033[0m"  if sys.stdout.isatty() else ""

PASS = f"{GREEN}PASS{RESET}"
FAIL = f"{RED}FAIL{RESET}"


# ---------------------------------------------------------------------------
# Minimal JSON-RPC stdio client
# ---------------------------------------------------------------------------

class StdioMcpClient:
    def __init__(self):
        self._proc: Optional[subprocess.Popen] = None
        self._next_id = 1

    def start(self) -> None:
        self._proc = subprocess.Popen(
            [sys.executable, "-m", "mcp_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd=str(IVD_ROOT),
        )
        # Handshake
        self._send({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05",
                               "capabilities": {},
                               "clientInfo": {"name": "canon-validation", "version": "1"}}})
        init = self._recv(lambda m: m.get("id") == 0)
        if not init or "result" not in init:
            raise RuntimeError(f"MCP initialize failed: {init}")
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    def stop(self) -> None:
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def list_tools(self) -> List[str]:
        self._send({"jsonrpc": "2.0", "id": self._next_id,
                    "method": "tools/list", "params": {}})
        msg = self._recv(lambda m: m.get("id") == self._next_id)
        self._next_id += 1
        return [t["name"] for t in msg["result"]["tools"]]

    def call(self, name: str, args: Dict[str, Any]) -> Tuple[Dict, float]:
        call_id = self._next_id
        self._next_id += 1
        request = {"jsonrpc": "2.0", "id": call_id,
                   "method": "tools/call",
                   "params": {"name": name, "arguments": args}}
        t0 = time.perf_counter()
        self._send(request)
        response = self._recv(lambda m: m.get("id") == call_id)
        elapsed = (time.perf_counter() - t0) * 1000
        return response, elapsed

    def _send(self, obj: Dict) -> None:
        self._proc.stdin.write(json.dumps(obj) + "\n")
        self._proc.stdin.flush()

    def _recv(self, predicate, timeout: float = 15.0) -> Optional[Dict]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                break
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if predicate(msg):
                return msg
        return None


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_CASES: List[Dict[str, Any]] = [
    # --------------------------------------------------------
    # T01: tools/list — confirm 4 canon tools present
    # --------------------------------------------------------
    {
        "id": "t01_tools_list",
        "label": "tools/list — confirms all 4 Canon tools are registered",
        "type": "list_tools",
        "expect": {
            "canon_render": True,
            "canon_check": True,
            "canon_diff": True,
            "canon_check_rules_installed": True,
        },
    },

    # --------------------------------------------------------
    # T02: canon_render — Tier 1, high stakes
    # --------------------------------------------------------
    {
        "id": "t02_render_high_stakes",
        "label": "canon_render — irreversible action, high stakes (Tier 1)",
        "tool": "canon_render",
        "args": {
            "text": (
                "I will permanently delete /var/log/old-service/ "
                "to free 40 GB of disk space. This cannot be undone."
            ),
            "stakes": "high",
            "output_format": "both",
        },
        "assertions": [
            ("result.tier == 1",
             lambda r: r.get("tier") == 1),
            ("result.document.body_with_marks is non-empty",
             lambda r: bool(r.get("document", {}).get("body_with_marks"))),
            ("R5 verification beat present (ACTION/REVERSIBLE/APPROVE?)",
             lambda r: len(r.get("document", {}).get("verification_beats", [])) > 0),
            ("result.markdown contains ACTION: ",
             lambda r: "ACTION:" in r.get("markdown", "")),
            ("result.markdown contains REVERSIBLE: ",
             lambda r: "REVERSIBLE:" in r.get("markdown", "")),
            ("result.markdown contains APPROVE?",
             lambda r: "APPROVE?" in r.get("markdown", "")),
            ("R14 identity statement present",
             lambda r: bool(r.get("document", {}).get("identity_statement"))),
        ],
    },

    # --------------------------------------------------------
    # T03: canon_render — Tier 1, low stakes, clean text
    # --------------------------------------------------------
    {
        "id": "t03_render_low_stakes",
        "label": "canon_render — informational response, low stakes (Tier 1)",
        "tool": "canon_render",
        "args": {
            "text": (
                "The capital of France is Paris. It has been the capital since "
                "the 10th century and is home to approximately 2.1 million people."
            ),
            "stakes": "low",
            "output_format": "both",
        },
        "assertions": [
            ("result.tier == 1",
             lambda r: r.get("tier") == 1),
            ("No verification beats for low-stakes informational text",
             lambda r: len(r.get("document", {}).get("verification_beats", [])) == 0),
            ("R14 identity statement present",
             lambda r: bool(r.get("document", {}).get("identity_statement"))),
        ],
    },

    # --------------------------------------------------------
    # T04: canon_check — audit a raw text with no epistemic cues.
    # Text deliberately uses no hedge words (should/likely/believe/etc.)
    # so the inferrer finds no confidence marks → R2 is partial.
    # --------------------------------------------------------
    {
        "id": "t04_check_raw_text",
        "label": "canon_check — audit hedge-free raw text, expect R2 partial (no glyphs)",
        "tool": "canon_check",
        "args": {
            "text": (
                "Kubernetes is the right choice. "
                "Microservices scale better than monoliths. "
                "Container orchestration simplifies deployments."
            ),
            "stakes": "medium",
        },
        "assertions": [
            ("result has 'overall' key",
             lambda r: "overall" in r),
            ("result has 'findings' list",
             lambda r: isinstance(r.get("findings"), list)),
            ("result has reproducible hash (non-empty string)",
             lambda r: bool(r.get("hash"))),
            ("R2 finding is partial — no cue words so no glyph markers injected",
             lambda r: any(
                 f["r"] == "R2" and f["status"] in ("partial", "fail")
                 for f in r.get("findings", [])
             )),
        ],
    },

    # --------------------------------------------------------
    # T05: canon_check — audit pre-marked Canon output
    # --------------------------------------------------------
    {
        "id": "t05_check_canon_marked",
        "label": "canon_check — audit text that already has Canon glyphs",
        "tool": "canon_check",
        "args": {
            "text": (
                "Setting: you asked whether to use Redis or Memcached.\n\n"
                "I am an AI assistant.\n\n"
                "✓ verified Redis supports persistence and pub/sub; Memcached does not. "
                "~ inferred your use case (session cache) does not require pub/sub. "
                "? assumed you have no existing Redis deployment to migrate away from."
            ),
            "stakes": "low",
        },
        "assertions": [
            ("result has 'overall' key",
             lambda r: "overall" in r),
            ("R2 finding is pass (canon glyphs present)",
             lambda r: any(
                 f["r"] == "R2" and f["status"] == "pass"
                 for f in r.get("findings", [])
             )),
        ],
    },

    # --------------------------------------------------------
    # T06: canon_diff — same report → 0 fixed, 0 regressed, N unchanged
    # --------------------------------------------------------
    {
        "id": "t06_diff_identical",
        "label": "canon_diff — identical reports produce no fixed/regressed",
        "type": "diff_workflow",
        "source_text": "I will drop the production database. This cannot be undone.",
        "source_stakes": "high",
        "assertions": [
            ("fixed == 0 (same report)",
             lambda d: len(d.get("fixed", [])) == 0),
            ("regressed == 0 (same report)",
             lambda d: len(d.get("regressed", [])) == 0),
            ("unchanged > 0 (some findings carried over)",
             lambda d: len(d.get("unchanged", [])) > 0),
        ],
    },

    # --------------------------------------------------------
    # T07: canon_check_rules_installed — missing Canon block
    # --------------------------------------------------------
    {
        "id": "t07_check_rules_missing",
        "label": "canon_check_rules_installed — plain .cursorrules → missing + install_payload",
        "type": "check_rules_workflow",
        "file_content": "# plain cursor rules — no Canon block\n",
        "file_name": ".cursorrules",
        "assertions": [
            ("overall_status == 'missing'",
             lambda p: p.get("overall_status") == "missing"),
            ("per_target contains .cursorrules entry",
             lambda p: any(t["file"] == ".cursorrules" for t in p.get("per_target", []))),
            ("cursorrules entry has install_payload",
             lambda p: any(
                 t["file"] == ".cursorrules" and "install_payload" in t
                 for t in p.get("per_target", [])
             )),
            ("install_payload has instruction_to_agent with 'permission'",
             lambda p: any(
                 t["file"] == ".cursorrules"
                 and "permission" in t.get("install_payload", {}).get("instruction_to_agent", "").lower()
                 for t in p.get("per_target", [])
             )),
            ("permission_discipline key present (top-level consent message)",
             lambda p: bool(p.get("permission_discipline"))),
            ("ZERO-WRITE: original file content unchanged after detection",
             None),  # checked separately in the workflow
        ],
    },

    # --------------------------------------------------------
    # T08: canon_check_rules_installed — Canon block installed
    # --------------------------------------------------------
    {
        "id": "t08_check_rules_installed",
        "label": "canon_check_rules_installed — file with Canon block → installed",
        "type": "check_rules_workflow",
        "file_content": (
            "# .cursorrules\n"
            "<BEGIN-CANON v1.0>\n"
            "# Canon rules block placeholder\n"
            "<END-CANON v1.0>\n"
        ),
        "file_name": ".cursorrules",
        "assertions": [
            ("overall_status is installed or partial",
             lambda p: p.get("overall_status") in ("installed", "partial")),
            ("cursorrules canon_block is present",
             lambda p: any(
                 t["file"] == ".cursorrules"
                 and t.get("canon_block") is not None
                 and t["canon_block"].get("present") is True
                 for t in p.get("per_target", [])
             )),
        ],
    },
]


# ---------------------------------------------------------------------------
# Run helpers
# ---------------------------------------------------------------------------

def run_list_tools(client: StdioMcpClient, tc: Dict) -> Dict[str, Any]:
    tool_names = set(client.list_tools())
    assertions = []
    all_ok = True
    for tool, expected_present in tc["expect"].items():
        actual = tool in tool_names
        ok = actual == expected_present
        all_ok = all_ok and ok
        assertions.append({"key": tool, "expected": expected_present, "actual": actual, "ok": ok})

    return {
        "id": tc["id"], "label": tc["label"],
        "tool_names": sorted(tool_names),
        "canon_tools": sorted(n for n in tool_names if n.startswith("canon_")),
        "total_tools": len(tool_names),
        "assertions": assertions,
        "all_assertions_ok": all_ok,
        "elapsed_ms": 0,
    }


def run_tool_call(client: StdioMcpClient, tc: Dict) -> Dict[str, Any]:
    response, elapsed = client.call(tc["tool"], tc["args"])
    raw_text = response.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {"_raw": raw_text}

    assertions = []
    all_ok = True
    for label, predicate in tc["assertions"]:
        try:
            actual = bool(predicate(result))
        except Exception as e:
            actual = False
            label = f"{label}  [exception: {e}]"
        ok = actual
        all_ok = all_ok and ok
        assertions.append({"key": label, "ok": ok})

    return {
        "id": tc["id"], "label": tc["label"],
        "tool": tc["tool"], "args": tc["args"],
        "response": result,
        "elapsed_ms": round(elapsed, 2),
        "assertions": assertions,
        "all_assertions_ok": all_ok,
    }


def run_diff_workflow(client: StdioMcpClient, tc: Dict) -> Dict[str, Any]:
    # Step 1: get a report
    resp, _ = client.call("canon_check", {"text": tc["source_text"], "stakes": tc["source_stakes"]})
    raw = resp.get("result", {}).get("content", [{}])[0].get("text", "")
    report = json.loads(raw)

    # Step 2: diff the report against itself
    diff_resp, elapsed = client.call("canon_diff", {"before": report, "after": report})
    diff_raw = diff_resp.get("result", {}).get("content", [{}])[0].get("text", "")
    diff = json.loads(diff_raw)

    assertions = []
    all_ok = True
    for label, predicate in tc["assertions"]:
        try:
            actual = bool(predicate(diff))
        except Exception as e:
            actual = False
            label = f"{label}  [exception: {e}]"
        ok = actual
        all_ok = all_ok and ok
        assertions.append({"key": label, "ok": ok})

    return {
        "id": tc["id"], "label": tc["label"],
        "diff_result": diff,
        "elapsed_ms": round(elapsed, 2),
        "assertions": assertions,
        "all_assertions_ok": all_ok,
    }


def run_check_rules_workflow(client: StdioMcpClient, tc: Dict) -> Dict[str, Any]:
    original_content = tc["file_content"]
    assertions_def = tc["assertions"]

    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / tc["file_name"]
        target.write_text(original_content)

        resp, elapsed = client.call(
            "canon_check_rules_installed", {"project_root": td}
        )
        raw = resp.get("result", {}).get("content", [{}])[0].get("text", "")
        payload = json.loads(raw)

        # Check zero-write invariant
        after_content = target.read_text()
        zero_write_ok = after_content == original_content

        assertions = []
        all_ok = True
        for label, predicate in assertions_def:
            if predicate is None:
                # Zero-write check handled separately
                ok = zero_write_ok
                assertions.append({"key": label, "ok": ok})
                all_ok = all_ok and ok
                continue
            try:
                actual = bool(predicate(payload))
            except Exception as e:
                actual = False
                label = f"{label}  [exception: {e}]"
            ok = actual
            all_ok = all_ok and ok
            assertions.append({"key": label, "ok": ok})

        return {
            "id": tc["id"], "label": tc["label"],
            "payload": payload,
            "zero_write_ok": zero_write_ok,
            "elapsed_ms": round(elapsed, 2),
            "assertions": assertions,
            "all_assertions_ok": all_ok,
        }


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------

def print_result(r: Dict[str, Any]) -> None:
    status = f"{GREEN}✓{RESET}" if r["all_assertions_ok"] else f"{RED}✗{RESET}"
    print(f"\n{BOLD}[{r['id']}]{RESET}  {status}  {r['label']}")

    if "tool_names" in r:
        print(f"  Total tools: {r['total_tools']}  Canon tools: {r['canon_tools']}")
    if "elapsed_ms" in r and r["elapsed_ms"]:
        print(f"  Elapsed: {r['elapsed_ms']} ms")

    # Show relevant response snippet
    if "response" in r:
        resp = r["response"]
        if "tier" in resp:
            print(f"  tier={resp['tier']}  engine={resp.get('engine_version')}")
        if "markdown" in resp:
            print(f"  {BOLD}Rendered markdown:{RESET}")
            for line in resp["markdown"].splitlines():
                print(f"    {line}")
        if "overall" in resp:
            print(f"  overall={resp['overall']}  partial={resp.get('partial')}"
                  f"  hash={str(resp.get('hash',''))[:12]}…")
    if "diff_result" in r:
        d = r["diff_result"]
        print(f"  fixed={len(d.get('fixed',[]))}  regressed={len(d.get('regressed',[]))}  unchanged={len(d.get('unchanged',[]))}")
    if "payload" in r:
        p = r["payload"]
        print(f"  overall_status={p.get('overall_status')}  per_target={len(p.get('per_target',[]))}")
        print(f"  zero_write={r.get('zero_write_ok')}  (file untouched after detection)")

    print(f"\n  {BOLD}Assertions:{RESET}")
    for a in r["assertions"]:
        sym = f"{GREEN}✓{RESET}" if a["ok"] else f"{RED}✗{RESET}"
        print(f"    {sym}  {a['key']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Canon MCP Protocol Validation  —  Option B{RESET}")
    print(f"  Test cases: {len(TEST_CASES)}  |  Results: {RESULTS_DIR}")
    print(f"  Server: python -m mcp_server  (stdio transport)")
    print(f"{BOLD}{'='*72}{RESET}")

    print(f"\n  Booting IVD MCP server…", end=" ", flush=True)
    client = StdioMcpClient()
    try:
        client.start()
    except Exception as e:
        print(f"{RED}FAILED{RESET}: {e}")
        return 1
    print(f"{GREEN}OK{RESET}")

    results = []
    try:
        for tc in TEST_CASES:
            kind = tc.get("type", "tool_call")
            if kind == "list_tools":
                r = run_list_tools(client, tc)
            elif kind == "diff_workflow":
                r = run_diff_workflow(client, tc)
            elif kind == "check_rules_workflow":
                r = run_check_rules_workflow(client, tc)
            else:
                r = run_tool_call(client, tc)

            results.append(r)
            print_result(r)

            # Save per-call JSON
            out_path = RESULTS_DIR / f"mcp_{tc['id']}.json"
            with out_path.open("w") as fh:
                json.dump(r, fh, indent=2, default=str)

    finally:
        client.stop()

    # Summary
    total      = len(results)
    ok_count   = sum(1 for r in results if r["all_assertions_ok"])
    fail_count = total - ok_count

    print(f"\n{BOLD}{'='*72}{RESET}")
    print(f"{BOLD}  Summary{RESET}")
    print(f"{'='*72}")
    print(f"  Test cases run     : {total}")
    print(f"  All assertions OK  : {GREEN}{ok_count}{RESET} / {total}")
    print(f"  Failures           : {(RED + str(fail_count) + RESET) if fail_count else (GREEN + '0' + RESET)}")
    print(f"  Results saved to   : {RESULTS_DIR}/")
    print(f"{'='*72}\n")

    summary = {
        "total": total, "ok": ok_count, "failed": fail_count,
        "cases": [{"id": r["id"], "ok": r["all_assertions_ok"],
                   "elapsed_ms": r.get("elapsed_ms")} for r in results],
    }
    with (RESULTS_DIR / "mcp_report.json").open("w") as fh:
        json.dump(summary, fh, indent=2)

    lines = ["Canon MCP Protocol Validation Report", "=" * 60,
             f"Cases : {total}", f"OK    : {ok_count}", f"Failed: {fail_count}", ""]
    for r in results:
        status = "PASS" if r["all_assertions_ok"] else "FAIL"
        lines.append(f"[{status}] {r['id']:35}  {r['label']}")
        for a in r["assertions"]:
            ok_str = "ok" if a["ok"] else "FAIL"
            lines.append(f"       [{ok_str}] {a['key']}")
        lines.append("")
    (RESULTS_DIR / "mcp_report.txt").write_text("\n".join(lines))
    print("  mcp_report.json + mcp_report.txt written.\n")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
