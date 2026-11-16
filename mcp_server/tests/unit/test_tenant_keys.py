# mcp_server/tests/unit/test_tenant_keys.py

"""Host-derived tenant keys: key format, verification, allowlist, no disk checks.

Spec: docs/HOST_TENANT_KEYS_TECH_SPEC.md (sections 3 and 5).
"""

import asyncio
import builtins
import json
import os
import pathlib
from types import SimpleNamespace

import pytest

from mcp_server import tenant as t
from mcp_server.registry import call_tool, get_all_tools
from mcp_server.tools.validate import validate_artifact_tool

SECRET = "test-secret-do-not-use"
# Shared test vector (section 3.1). Every implementation of this scheme carries
# the same one, so copies cannot drift.
VECTOR_KEY = "ivd_acme_lapHGNV1gUE0w05P_i0KVkw8RF5Y5R_9-vngns5EZ50"


@pytest.fixture
def tenant_env(monkeypatch):
    monkeypatch.setenv("IVD_TENANT_KEY_SECRET", SECRET)
    monkeypatch.delenv("IVD_TENANT_KEY_VERSIONS", raising=False)
    monkeypatch.delenv("IVD_REVOKED_TENANTS", raising=False)


def _tamper(key: str) -> str:
    last = key[-1]
    return key[:-1] + ("A" if last != "A" else "B")


class TestKeyFormat:
    def test_vector_derives(self):
        assert t.derive_key(SECRET, "v1", "acme") == VECTOR_KEY

    def test_vector_verifies(self, tenant_env):
        assert t.verify_tenant_key(VECTOR_KEY) == ("acme", None)

    def test_mac_is_43_chars(self):
        assert len(VECTOR_KEY) - len("ivd_acme_") == 43

    def test_mac_containing_underscore_yields_right_tenant(self, tenant_env):
        # Find a tenant whose MAC contains "_" (the vector's does too).
        found = None
        for i in range(2000):
            tenant = f"team-{i}"
            key = t.derive_key(SECRET, "v1", tenant)
            if "_" in key[-43:]:
                found = (tenant, key)
                break
        assert found is not None
        tenant, key = found
        assert t.parse_tenant(key) == tenant
        assert t.verify_tenant_key(key) == (tenant, None)
        assert "_" in VECTOR_KEY[-43:]
        assert t.parse_tenant(VECTOR_KEY) == "acme"

    def test_tenant_with_hyphens_round_trips(self, tenant_env):
        key = t.derive_key(SECRET, "v1", "acme-eu-1")
        assert t.verify_tenant_key(key) == ("acme-eu-1", None)

    def test_derive_refuses_bad_tenant(self):
        with pytest.raises(ValueError):
            t.derive_key(SECRET, "v1", "Acme")


class TestVerificationRefusals:
    def test_tampered_mac(self, tenant_env):
        tenant, reason = t.verify_tenant_key(_tamper(VECTOR_KEY))
        assert reason == "invalid_tenant_key"

    def test_unknown_version(self, tenant_env):
        key = t.derive_key(SECRET, "v2", "acme")
        assert t.verify_tenant_key(key)[1] == "invalid_tenant_key"

    def test_added_version_accepted(self, tenant_env, monkeypatch):
        monkeypatch.setenv("IVD_TENANT_KEY_VERSIONS", "v1,v2")
        assert t.verify_tenant_key(t.derive_key(SECRET, "v2", "acme")) == ("acme", None)
        assert t.verify_tenant_key(VECTOR_KEY) == ("acme", None)

    def test_revoked_tenant(self, tenant_env, monkeypatch):
        monkeypatch.setenv("IVD_REVOKED_TENANTS", "other, acme")
        assert t.verify_tenant_key(VECTOR_KEY) == ("acme", "revoked_tenant")

    def test_tenant_breaking_rule(self, tenant_env):
        # Uppercase tenant, MAC computed honestly for it: still refused.
        key = "ivd_Acme_" + t._mac(SECRET, "v1", "Acme")
        assert t.verify_tenant_key(key) == (None, "invalid_tenant_key_format")
        long_tenant = "a" * 57
        key = f"ivd_{long_tenant}_" + t._mac(SECRET, "v1", long_tenant)
        assert t.verify_tenant_key(key)[1] == "invalid_tenant_key_format"

    def test_no_secret_configured(self, monkeypatch):
        monkeypatch.delenv("IVD_TENANT_KEY_SECRET", raising=False)
        assert t.verify_tenant_key(VECTOR_KEY) == (None, "tenant_keys_disabled")

    def test_wrong_secret(self, monkeypatch):
        monkeypatch.setenv("IVD_TENANT_KEY_SECRET", "another-secret")
        assert t.verify_tenant_key(VECTOR_KEY)[1] == "invalid_tenant_key"

    def test_other_product_prefix_not_a_tenant_key(self, tenant_env):
        assert t.parse_tenant("eif" + VECTOR_KEY[3:]) is None


class TestAllowlist:
    def test_tenant_tool_list_is_three_tools(self):
        tools = t.tenant_tool_list(get_all_tools())
        assert sorted(x.name for x in tools) == sorted(t.TENANT_TOOLS)

    def test_tenant_schemas_drop_path_arguments(self):
        for tool in t.tenant_tool_list(get_all_tools()):
            props = (tool.inputSchema or {}).get("properties", {})
            assert "project_root" not in props
            assert "workspace_root" not in props

    def test_operator_tool_list_unchanged(self):
        full = get_all_tools()
        validate = next(x for x in full if x.name == "ivd_validate")
        t.tenant_tool_list(full)  # must not mutate the shared schemas
        assert "project_root" in validate.inputSchema["properties"]

    def test_tool_outside_allowlist_refused(self, tmp_path):
        out = call_tool("ivd_init", {"project_root": str(tmp_path)}, tenant="acme")
        assert out.startswith("Error:") and "tenant key" in out
        assert not any(tmp_path.iterdir())
        out = call_tool("ivd_search", {"query": "x"}, tenant="acme")
        assert "not available with a tenant key" in out

    def test_validate_with_project_root_refused(self, sample_intent_yaml_text):
        out = call_tool(
            "ivd_validate",
            {"artifact_yaml": sample_intent_yaml_text, "project_root": "/"},
            tenant="acme",
        )
        assert out == "Error: argument 'project_root' is not accepted with a tenant key"

    def test_workspace_root_refused(self):
        out = call_tool("canon_check", {"text": "hi", "workspace_root": "/"}, tenant="acme")
        assert "workspace_root" in out and out.startswith("Error:")

    def test_validate_without_project_root_validates(self, sample_intent_yaml_text):
        result = json.loads(
            call_tool("ivd_validate", {"artifact_yaml": sample_intent_yaml_text}, tenant="acme")
        )
        assert result["valid"] is True
        assert result["test_paths_checked"] is False

    def test_review_intent_and_canon_check_run(self, sample_intent_yaml_text):
        out = call_tool("ivd_review_intent", {"artifact_yaml": sample_intent_yaml_text}, tenant="acme")
        assert not out.startswith("Error")
        out = call_tool("canon_check", {"text": "The build passed."}, tenant="acme")
        assert not out.startswith("Error")

    def test_operator_call_unchanged(self, sample_intent_yaml_text):
        result = json.loads(call_tool("ivd_validate", {"artifact_yaml": sample_intent_yaml_text}))
        assert "test_paths_checked" not in result


@pytest.fixture
def sample_intent_yaml_text():
    path = pathlib.Path(__file__).parent.parent / "fixtures" / "sample_intent.yaml"
    return path.read_text()


def _intent_naming(test_path: str) -> str:
    return f"""
scope: {{level: module}}
intent: {{summary: s, goal: g, success_metric: m}}
constraints:
  - name: c1
    requirement: r
    test: "{test_path}::test_it"
    test_provenance: execution_derived
    execution_oracle:
      type: golden_fixture
      path: "{test_path}"
      expected: "{test_path}"
  - name: c2
    requirement: r
    test: "{test_path}::test_two"
    test_provenance: human_authored
  - name: c3
    requirement: r
    test: "{test_path}::test_three"
    test_provenance: human_authored
constraint_satisfiability:
  joint_satisfaction_test: "{test_path}::test_joint"
rationale: {{decision: d}}
alternatives: []
risks: []
implementation: {{current: x}}
verification: {{test_cases: []}}
"""


class TestTenantValidateTouchesNoDisk:
    """For a tenant key, no path from the YAML is ever opened or joined to a server folder."""

    EXISTING = "mcp_server/tests/unit/test_validate.py"
    MISSING = "mcp_server/tests/unit/no_such_file_here.py"

    def _run_with_disk_forbidden(self, monkeypatch, yaml_text):
        def forbid(*_a, **_k):
            raise AssertionError("tenant ivd_validate touched the disk")

        for name in ("is_file", "exists", "is_dir", "stat", "open", "resolve"):
            monkeypatch.setattr(pathlib.Path, name, forbid)
        real_open = builtins.open
        monkeypatch.setattr(builtins, "open", forbid)
        monkeypatch.setattr(os, "stat", forbid)
        try:
            return validate_artifact_tool(yaml_text, "intent", None, check_test_paths=False)
        finally:
            monkeypatch.setattr(builtins, "open", real_open)

    @pytest.mark.parametrize("path", [EXISTING, MISSING, "/etc/hosts.py", "/no/such/abs/file.py"])
    def test_no_file_opened(self, monkeypatch, path):
        out = self._run_with_disk_forbidden(monkeypatch, _intent_naming(path))
        result = json.loads(out)
        assert result["test_paths_checked"] is False
        assert not any("not found on disk" in w for w in result["warnings"])

    def test_same_answer_whether_path_exists(self):
        a = validate_artifact_tool(_intent_naming(self.EXISTING), "intent", None, check_test_paths=False)
        b = validate_artifact_tool(_intent_naming(self.MISSING), "intent", None, check_test_paths=False)
        assert a.replace(self.EXISTING, "P") == b.replace(self.MISSING, "P")
        here = str(pathlib.Path(__file__).resolve())  # absolute, exists on this machine
        c = validate_artifact_tool(_intent_naming(here), "intent", None, check_test_paths=False)
        d = validate_artifact_tool(_intent_naming("/no/such/x.py"), "intent", None, check_test_paths=False)
        assert c.replace(here, "P") == d.replace("/no/such/x.py", "P")

    def test_operator_mode_still_checks_disk(self):
        """Control: without the tenant switch the same YAML does reveal the missing file."""
        out = json.loads(validate_artifact_tool(_intent_naming(self.MISSING), "intent"))
        assert any("not found on disk" in w for w in out["warnings"])

    def test_parse_error_carries_flag(self):
        out = json.loads(validate_artifact_tool("a: [", "intent", None, check_test_paths=False))
        assert out["valid"] is False and out["test_paths_checked"] is False


class TestPerMessageCaller:
    """The caller is read from each message's own request, not the session's first."""

    def _ctx(self, scope_identity, session):
        from mcp.shared.context import RequestContext

        request = SimpleNamespace(
            scope={"ivd_identity": scope_identity},
            headers={"Authorization": "Bearer k"},
        )
        return RequestContext(
            request_id=1, meta=None, session=session, lifespan_context=None, request=request
        )

    def test_message_identity_wins_over_session_context(self):
        from mcp.server.lowlevel.server import request_ctx

        from mcp_server import server as srv

        session = SimpleNamespace()
        first = srv._request_context.set({"api_key": "operator-key", "request": None})
        tok = request_ctx.set(self._ctx(t.tenant_identity("acme"), session))
        try:
            api_key, _req, identity = srv._message_caller()
            assert identity.tenant == "acme" and api_key == "k"
        finally:
            request_ctx.reset(tok)
            srv._request_context.reset(first)

    def test_session_continued_by_other_identity_refused(self):
        from mcp.server.lowlevel.server import request_ctx

        from mcp_server import server as srv

        session = SimpleNamespace()
        tok = request_ctx.set(self._ctx(t.tenant_identity("acme"), session))
        srv._message_caller()
        request_ctx.reset(tok)
        for other in (t.tenant_identity("beta"), t.operator_identity("op-key")):
            tok = request_ctx.set(self._ctx(other, session))
            try:
                with pytest.raises(srv._CallerRefused):
                    srv._message_caller()
            finally:
                request_ctx.reset(tok)

    def test_http_message_without_request_refused(self):
        from mcp_server import server as srv

        tok = srv._request_context.set({"api_key": "x", "request": None})
        try:
            with pytest.raises(srv._CallerRefused):
                srv._message_caller()
        finally:
            srv._request_context.reset(tok)

    def test_stdio_runs_as_local_operator(self):
        from mcp_server import server as srv

        assert srv._message_caller() == (None, None, None)


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
        return [(data, score) for score, data in self.sets.get(key, []) if score > floor]


class TestEventStoreScopedPerIdentity:
    """Stream ids repeat across sessions ("1", "2"...): a replay must stay in its own identity."""

    def test_replay_never_crosses_identities(self, monkeypatch):
        from mcp.types import JSONRPCMessage, JSONRPCResponse

        import mcp_server.event_store as es

        fake = _FakeRedis()
        monkeypatch.setattr(es, "get_async_redis_connection", lambda *_a, **_k: fake)
        store = es.RedisEventStore(key_prefix="ivd")
        secret_result = JSONRPCMessage(
            JSONRPCResponse(jsonrpc="2.0", id=1, result={"text": "tenant A content"})
        )

        async def scenario():
            tok = t.event_scope.set("tenant:alpha")
            await store.store_event("1", secret_result)
            t.event_scope.reset(tok)

            seen = []

            async def collect(ev):
                seen.append(ev)

            tok = t.event_scope.set("tenant:beta")
            beta = await store.replay_events_after("1:0", collect)
            t.event_scope.reset(tok)
            tok = t.event_scope.set("operator:abc")
            op = await store.replay_events_after("1:0", collect)
            t.event_scope.reset(tok)
            assert beta is None and op is None and seen == []

            tok = t.event_scope.set("tenant:alpha")
            alpha = await store.replay_events_after("1:0", collect)
            t.event_scope.reset(tok)
            assert alpha == "1" and len(seen) == 1

        asyncio.run(scenario())
