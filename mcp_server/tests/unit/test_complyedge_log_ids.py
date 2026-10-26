"""Every checked tool call hands its ComplyEdge Log IDs back to the caller.

ComplyEdge keeps a keyed fingerprint of the checked text, never the text, so
a Log ID (event_id) proves something only next to a copy of that text. IVD
keeps none, so the IDs go to the caller in the result's _meta, outside the
text, and the text returned is exactly the text that was checked. These tests
run the real dispatch and the real MCP request handler against a local stub
of POST /v1/check.
"""

from __future__ import annotations

import asyncio
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from mcp import types

from mcp_server import registry
from mcp_server import server as ivd_server

KEY = "ce_test_key_for_stub"


@pytest.fixture
def stub(monkeypatch):
    """A fake ComplyEdge. `answers` is popped per call; default allows."""
    state = {"seen": [], "answers": [], "status": 200}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["seen"].append(body)
            answer = state["answers"].pop(0) if state["answers"] else {"allowed": True, "violations": []}
            out = json.dumps({"event_id": f"evt-{len(state['seen'])}", **answer}).encode()
            self.send_response(state["status"])
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("COMPLYEDGE_API_KEY", KEY)
    monkeypatch.setenv("COMPLYEDGE_API_URL", f"http://127.0.0.1:{srv.server_port}")
    yield state
    srv.shutdown()


@pytest.fixture
def fake_tool(monkeypatch):
    calls = []

    def handler(**kwargs):
        calls.append(kwargs)
        return {"echo": kwargs.get("q")}

    monkeypatch.setitem(registry.TOOL_HANDLERS, "fake_tool", handler)
    return calls


def _block(rule="EU-AI-ACT-ART5-TEST"):
    return {"allowed": False, "violations": [{"rule_id": rule, "rule_description": "test rule"}]}


def _wire(name: str, arguments: dict) -> dict:
    """One tools/call through the real low-level handler, as the client gets it."""
    handler = ivd_server.server.request_handlers[types.CallToolRequest]
    req = types.CallToolRequest(
        method="tools/call", params=types.CallToolRequestParams(name=name, arguments=arguments)
    )
    result = asyncio.run(handler(req))
    return result.model_dump(by_alias=True, exclude_none=True, mode="json")


def test_dispatch_fills_both_log_ids(stub, fake_tool):
    ids: dict = {}
    out = registry.call_tool("fake_tool", {"q": "hello"}, None, None, ids)
    assert ids == {"input_event_id": "evt-1", "output_event_id": "evt-2"}
    assert stub["seen"][1]["text"] == out


def test_allowed_call_returns_log_ids_outside_the_checked_text(stub, fake_tool):
    wire = _wire("fake_tool", {"q": "hello"})

    assert wire["_meta"]["complyedge"] == {"input_event_id": "evt-1", "output_event_id": "evt-2"}
    text = wire["content"][0]["text"]
    # The caller's copy is exactly what was checked, so it verifies later.
    assert stub["seen"][1]["text"] == text
    assert stub["seen"][0]["text"] == 'fake_tool {"q": "hello"}'
    assert "evt-" not in text


def test_input_block_returns_the_input_log_id_only(stub, fake_tool):
    stub["answers"] = [_block()]
    wire = _wire("fake_tool", {"q": "a"})
    assert fake_tool == []
    assert wire["_meta"]["complyedge"] == {"input_event_id": "evt-1", "output_event_id": None}


def test_output_block_returns_both_log_ids(stub, fake_tool):
    stub["answers"] = [{"allowed": True, "violations": []}, _block("EU-OUT-1")]
    wire = _wire("fake_tool", {"q": "secret"})
    assert wire["_meta"]["complyedge"] == {"input_event_id": "evt-1", "output_event_id": "evt-2"}
    assert "secret" not in wire["content"][0]["text"]


def test_fail_open_reports_null_log_ids(stub, fake_tool):
    stub["status"] = 500
    wire = _wire("fake_tool", {"q": "x"})
    assert wire["_meta"]["complyedge"] == {"input_event_id": None, "output_event_id": None}
    assert json.loads(wire["content"][0]["text"]) == {"echo": "x"}


def _closed_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def test_no_key_means_no_meta(fake_tool, monkeypatch):
    monkeypatch.delenv("COMPLYEDGE_API_KEY", raising=False)
    monkeypatch.setenv("COMPLYEDGE_API_URL", f"http://127.0.0.1:{_closed_port()}")
    wire = _wire("fake_tool", {"q": "z"})
    assert "_meta" not in wire
    assert json.loads(wire["content"][0]["text"]) == {"echo": "z"}
