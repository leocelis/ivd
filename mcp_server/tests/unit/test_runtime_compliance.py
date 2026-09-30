"""Every MCP tool call goes through ComplyEdge when the server has a key.

Before this, no IVD MCP tool called ComplyEdge at all: the enforcement seal
counted only the CI probe, never a real tool call. Now registry.call_tool,
the one dispatch every tool passes through, checks the arguments (direction
"prompt") and the result (direction "output") with the attribution fields
the ComplyEdge API reference names. These tests run the real dispatch
against a local stub of POST /v1/check.
"""

from __future__ import annotations

import hashlib
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from mcp_server import registry

KEY = "ce_test_key_for_stub"


class _Req:
    """Minimal stand-in for the Starlette request the server passes along."""

    def __init__(self, headers=None, query=None):
        self.headers = headers or {}
        self.query_params = query or {}
        self.client = None


@pytest.fixture
def stub(monkeypatch):
    """A fake ComplyEdge. `answers` is popped per call; default allows."""
    state = {"seen": [], "auth": [], "answers": [], "status": 200}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["seen"].append(body)
            state["auth"].append(self.headers.get("Authorization"))
            answer = state["answers"].pop(0) if state["answers"] else {"allowed": True, "violations": []}
            out = json.dumps({"event_id": f"evt-{len(state['seen'])}", "latency_ms": 1, **answer}).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("COMPLYEDGE_API_KEY", KEY)
    monkeypatch.setenv("COMPLYEDGE_API_URL", f"http://127.0.0.1:{server.server_port}")
    yield state
    server.shutdown()


@pytest.fixture
def fake_tool(monkeypatch):
    calls = []

    def handler(**kwargs):
        calls.append(kwargs)
        return {"echo": kwargs.get("q")}

    monkeypatch.setitem(registry.TOOL_HANDLERS, "fake_tool", handler)
    return calls


def test_real_tool_is_checked_on_the_way_in_and_out(stub):
    ivd_key = "ivd_live_abcdef123456"
    req = _Req(headers={"mcp-session-id": "sess-42"})
    out = registry.call_tool("ivd_list_recipes", {}, ivd_key, req)

    assert len(stub["seen"]) == 2
    first, second = stub["seen"]
    assert first["direction"] == "prompt" and first["text"].startswith("ivd_list_recipes ")
    assert second["direction"] == "output" and second["text"] == out
    expected_ctx = {
        "user_id": "ivdkey:" + hashlib.sha256(ivd_key.encode()).hexdigest()[:12],
        "user_role": "mcp_client",
        "session_id": "sess-42",
    }
    for body in stub["seen"]:
        assert body["agent_id"] == "ivd-mcp"
        assert body["jurisdiction"] == "EU"
        assert body["context"] == expected_ctx
        # neither credential ever rides in the body
        assert ivd_key not in json.dumps(body) and KEY not in json.dumps(body)
    assert stub["auth"] == [f"Bearer {KEY}"] * 2


def test_sse_session_comes_from_the_query_string(stub, fake_tool):
    registry.call_tool("fake_tool", {"q": "x"}, "k1", _Req(query={"session_id": "sse-7"}))
    assert stub["seen"][0]["context"]["session_id"] == "sse-7"


def test_stdio_call_is_attributed_to_the_local_maintainer(stub, fake_tool, monkeypatch):
    monkeypatch.setenv("USER", "alice")
    registry.call_tool("fake_tool", {"q": "x"}, None, None)
    assert stub["seen"][0]["context"] == {"user_id": "local:alice", "user_role": "maintainer"}


def test_blocked_input_never_runs_the_tool(stub, fake_tool):
    stub["answers"].append({"allowed": False, "violations": [
        {"rule_id": "rego-art5-1c-001", "rule_description": "Article 5(1)(c) social scoring"}]})
    out = registry.call_tool("fake_tool", {"q": "score citizens"}, "k1", None)
    assert fake_tool == []
    assert len(stub["seen"]) == 1
    assert out.startswith("Blocked by ComplyEdge: the input of fake_tool")
    assert "rego-art5-1c-001" in out and "evt-1" in out


def test_blocked_output_is_not_returned(stub, fake_tool):
    stub["answers"] += [{"allowed": True}, {"allowed": False, "violations": [{"rule_id": "r1", "reason": "x"}]}]
    out = registry.call_tool("fake_tool", {"q": "secret-output"}, "k1", None)
    assert fake_tool == [{"q": "secret-output"}]
    assert "secret-output" not in out
    assert out.startswith("Blocked by ComplyEdge: the output of fake_tool")


def test_server_error_fails_open(stub, fake_tool):
    stub["status"] = 500
    out = registry.call_tool("fake_tool", {"q": "hi"}, "k1", None)
    assert json.loads(out) == {"echo": "hi"}


def test_unreachable_complyedge_fails_open(fake_tool, monkeypatch):
    with socket.socket() as s:  # a port nobody listens on
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    monkeypatch.setenv("COMPLYEDGE_API_KEY", KEY)
    monkeypatch.setenv("COMPLYEDGE_API_URL", f"http://127.0.0.1:{port}")
    out = registry.call_tool("fake_tool", {"q": "hi"}, "k1", None)
    assert json.loads(out) == {"echo": "hi"}


def test_no_key_means_no_checks(stub, fake_tool, monkeypatch):
    monkeypatch.delenv("COMPLYEDGE_API_KEY")
    out = registry.call_tool("fake_tool", {"q": "hi"}, "k1", None)
    assert stub["seen"] == []
    assert json.loads(out) == {"echo": "hi"}
