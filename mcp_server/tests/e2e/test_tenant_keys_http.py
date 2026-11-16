# mcp_server/tests/e2e/test_tenant_keys_http.py

"""Tenant keys over the real HTTP app: 401s, tools/list, allowlist, session binding.

Spec: docs/HOST_TENANT_KEYS_TECH_SPEC.md (section 5). Streamable HTTP runs through
Starlette's TestClient; the legacy SSE path runs against a local uvicorn server
on 127.0.0.1, because its GET stream stays open.
"""

import importlib
import json
import socket
import threading
import time

import httpx
import pytest
import uvicorn
from starlette.testclient import TestClient

from mcp_server import tenant as t
from mcp_server.registry import get_all_tools

SECRET = "test-secret-do-not-use"
OPERATOR_KEY = "operator-key-123"
ACME = "ivd_acme_lapHGNV1gUE0w05P_i0KVkw8RF5Y5R_9-vngns5EZ50"
BETA = t.derive_key(SECRET, "v1", "beta")
PROTOCOL = "2025-06-18"

SAMPLE_INTENT = """
scope: {level: module}
intent: {summary: s, goal: g, success_metric: m}
constraints:
  - name: c1
    requirement: r
    test: "mcp_server/tests/unit/test_validate.py::test_it"
    test_provenance: human_authored
rationale: {decision: d}
alternatives: []
risks: []
implementation: {current: x}
verification: {test_cases: []}
"""


def _reload_auth():
    import mcp_server.auth

    importlib.reload(mcp_server.auth)


def _make_app(monkeypatch, *, secret=SECRET, api_keys=OPERATOR_KEY):
    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("COMPLYEDGE_API_KEY", raising=False)
    monkeypatch.delenv("IVD_TENANT_KEY_VERSIONS", raising=False)
    monkeypatch.delenv("IVD_REVOKED_TENANTS", raising=False)
    if secret is None:
        monkeypatch.delenv("IVD_TENANT_KEY_SECRET", raising=False)
    else:
        monkeypatch.setenv("IVD_TENANT_KEY_SECRET", secret)
    monkeypatch.setenv("IVD_API_KEYS", api_keys)
    _reload_auth()
    from mcp_server.server import create_app

    return create_app()


@pytest.fixture
def client(monkeypatch):
    with TestClient(_make_app(monkeypatch)) as c:
        yield c
    monkeypatch.delenv("IVD_API_KEYS", raising=False)
    monkeypatch.delenv("IVD_TENANT_KEY_SECRET", raising=False)
    _reload_auth()


def _headers(key, session_id=None):
    h = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
        "MCP-Protocol-Version": PROTOCOL,
    }
    if session_id:
        h["mcp-session-id"] = session_id
    return h


def _parse(response):
    if response.headers.get("content-type", "").startswith("application/json"):
        return response.json()
    for line in response.text.splitlines():
        if line.startswith("data:") and line[5:].strip():
            return json.loads(line[5:])
    return None


def _open_session(c, key):
    r = c.post(
        "/mcp",
        headers=_headers(key),
        json={
            "jsonrpc": "2.0",
            "id": 0,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
    )
    assert r.status_code == 200, r.text
    sid = r.headers["mcp-session-id"]
    r = c.post(
        "/mcp",
        headers=_headers(key, sid),
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
    )
    assert r.status_code in (200, 202)
    return sid


def _rpc(c, key, sid, method, params, rid=1):
    r = c.post(
        "/mcp",
        headers=_headers(key, sid),
        json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params},
    )
    return r, (_parse(r) if r.status_code == 200 else None)


def _call(c, key, sid, name, arguments, rid=1):
    r, body = _rpc(c, key, sid, "tools/call", {"name": name, "arguments": arguments}, rid)
    assert r.status_code == 200, r.text
    return body["result"]["content"][0]["text"]


class TestRefusedWith401:
    def _status(self, c, key):
        return c.post("/mcp", headers=_headers(key), json={}).status_code

    def test_tampered_mac(self, client):
        assert self._status(client, ACME[:-1] + ("A" if ACME[-1] != "A" else "B")) == 401

    def test_unknown_version(self, client):
        assert self._status(client, t.derive_key(SECRET, "v9", "acme")) == 401

    def test_revoked_tenant(self, client, monkeypatch):
        monkeypatch.setenv("IVD_REVOKED_TENANTS", "acme")
        assert self._status(client, ACME) == 401
        assert self._status(client, BETA) != 401

    def test_tenant_breaking_rule(self, client):
        key = "ivd_ACME_" + t._mac(SECRET, "v1", "ACME")
        assert self._status(client, key) == 401

    def test_made_up_key_refused_when_tenant_keys_on(self, monkeypatch):
        # No operator keys configured: the old "no keys -> auth off" fallback
        # must not let an arbitrary key past while tenant keys are on.
        with TestClient(_make_app(monkeypatch, api_keys="")) as c:
            assert c.post("/mcp", headers=_headers("anything"), json={}).status_code == 401
            assert c.post("/mcp", headers=_headers(ACME), json={}).status_code != 401

    def test_no_secret_configured(self, monkeypatch):
        with TestClient(_make_app(monkeypatch, secret=None)) as c:
            assert c.post("/mcp", headers=_headers(ACME), json={}).status_code == 401
            assert c.post("/mcp", headers=_headers(OPERATOR_KEY), json={}).status_code != 401

    def test_auth_log_names_tenant_not_key(self, client, monkeypatch):
        import mcp_server.auth as auth

        events = []
        monkeypatch.setattr(auth, "log_auth_event", lambda **kw: events.append(kw))
        client.post("/mcp", headers=_headers(ACME), json={})
        assert events[-1]["status"] == "ok"
        assert events[-1]["tenant"] == "acme" and events[-1]["key_id"] == "tenant:acme"
        assert ACME[-43:] not in json.dumps(events)


class TestTenantSession:
    def test_tools_list_shows_three_tools(self, client):
        sid = _open_session(client, ACME)
        _, body = _rpc(client, ACME, sid, "tools/list", {})
        names = sorted(x["name"] for x in body["result"]["tools"])
        assert names == sorted(t.TENANT_TOOLS)
        validate = next(x for x in body["result"]["tools"] if x["name"] == "ivd_validate")
        assert "project_root" not in validate["inputSchema"]["properties"]

    def test_tool_outside_allowlist_refused(self, client):
        sid = _open_session(client, ACME)
        text = _call(client, ACME, sid, "ivd_get_context", {})
        assert "not available with a tenant key" in text

    def test_validate_with_project_root_refused(self, client):
        sid = _open_session(client, ACME)
        text = _call(client, ACME, sid, "ivd_validate", {"artifact_yaml": SAMPLE_INTENT, "project_root": "/"})
        assert "project_root" in text and text.startswith("Error")

    def test_validate_without_project_root_validates(self, client):
        sid = _open_session(client, ACME)
        result = json.loads(_call(client, ACME, sid, "ivd_validate", {"artifact_yaml": SAMPLE_INTENT}))
        assert result["test_paths_checked"] is False
        assert "errors" in result

    def test_session_continued_with_other_tenant_refused(self, client):
        sid = _open_session(client, ACME)
        r, _ = _rpc(client, BETA, sid, "tools/list", {})
        assert r.status_code == 404
        r, _ = _rpc(client, OPERATOR_KEY, sid, "tools/list", {})
        assert r.status_code == 404
        # The owner can still use it.
        r, body = _rpc(client, ACME, sid, "tools/list", {}, rid=2)
        assert r.status_code == 200 and len(body["result"]["tools"]) == 3

    def test_operator_session_not_usable_by_tenant(self, client):
        sid = _open_session(client, OPERATOR_KEY)
        r, _ = _rpc(client, ACME, sid, "tools/list", {})
        assert r.status_code == 404


class TestOperatorKeyUnchanged:
    def test_full_tool_list(self, client):
        sid = _open_session(client, OPERATOR_KEY)
        _, body = _rpc(client, OPERATOR_KEY, sid, "tools/list", {})
        assert len(body["result"]["tools"]) == len(get_all_tools())

    def test_validate_as_before(self, client):
        sid = _open_session(client, OPERATOR_KEY)
        result = json.loads(_call(client, OPERATOR_KEY, sid, "ivd_validate", {"artifact_yaml": SAMPLE_INTENT}))
        assert "test_paths_checked" not in result

    def test_unknown_key_still_401(self, client):
        assert client.post("/mcp", headers=_headers("wrong"), json={}).status_code == 401


# ── Legacy SSE ────────────────────────────────────────────────────────────────

def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def sse_server(monkeypatch):
    app = _make_app(monkeypatch)
    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)
    monkeypatch.delenv("IVD_API_KEYS", raising=False)
    monkeypatch.delenv("IVD_TENANT_KEY_SECRET", raising=False)
    _reload_auth()


def test_sse_session_bound_to_opening_tenant(sse_server):
    base = sse_server
    # Two clients: the GET stream holds its own connection open.
    with httpx.Client(timeout=10) as listener, httpx.Client(timeout=10) as http:
        with listener.stream("GET", f"{base}/sse", headers={"Authorization": f"Bearer {ACME}"}) as stream:
            endpoint = None
            # Keep the line iterator alive: closing it closes the stream, and
            # the server then ends the session.
            lines = stream.iter_lines()
            for line in lines:
                if line.startswith("data:"):
                    endpoint = line[5:].strip()
                    break
            assert endpoint and "session_id=" in endpoint
            url = base + endpoint
            msg = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {"protocolVersion": PROTOCOL, "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}},
            }
            assert http.post(url, json=msg, headers={"Authorization": f"Bearer {ACME}"}).status_code == 202
            assert http.post(url, json=msg, headers={"Authorization": f"Bearer {BETA}"}).status_code == 404
            assert http.post(url, json=msg, headers={"Authorization": f"Bearer {OPERATOR_KEY}"}).status_code == 404
            ping = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
            assert http.post(url, json=ping, headers={"Authorization": f"Bearer {ACME}"}).status_code == 202


# ── Resumable-stream event store (spec section 7) ─────────────────────────────

class _FakeRedis:
    def __init__(self):
        self.n = 0
        self.sets = {}

    async def incr(self, _key):
        self.n += 1
        return self.n

    async def zadd(self, key, mapping):
        self.sets.setdefault(key, []).extend((v, k) for k, v in mapping.items())

    async def expire(self, *_a):
        return True

    async def zrangebyscore(self, key, low, _high, withscores=True):
        floor = float(low.lstrip("("))
        return [(d, s) for s, d in self.sets.get(key, []) if s > floor]

    async def aclose(self):
        return None


def test_session_events_stored_under_the_opening_identity(monkeypatch):
    """The session's own task stores its events under its identity's scope.

    Stream ids are request ids and repeat across sessions; without the scope
    every caller's request-1 results would share one key.
    """
    import hashlib

    import mcp_server.event_store as es

    fake = _FakeRedis()
    monkeypatch.setattr(es, "get_async_redis_connection", lambda *_a, **_k: fake)
    app = _make_app(monkeypatch)
    monkeypatch.setenv("REDIS_URL", "redis://127.0.0.1:1")
    from mcp_server.server import create_app

    with TestClient(create_app()) as c:
        for key in (ACME, BETA):
            sid = _open_session(c, key)
            _call(c, key, sid, "canon_check", {"text": f"note from {key[:8]}"})
    del app
    acme = hashlib.sha256(b"tenant:acme").hexdigest()[:16]
    beta = hashlib.sha256(b"tenant:beta").hexdigest()[:16]
    keys = list(fake.sets)
    assert keys, "no events were stored"
    assert all(k.startswith(f"ivd:events:{acme}:") or k.startswith(f"ivd:events:{beta}:") for k in keys)
    acme_text = json.dumps([d for k in keys if acme in k for _s, d in fake.sets[k]])
    assert "ivd_beta" not in acme_text
    monkeypatch.delenv("IVD_API_KEYS", raising=False)
    monkeypatch.delenv("IVD_TENANT_KEY_SECRET", raising=False)
    _reload_auth()
