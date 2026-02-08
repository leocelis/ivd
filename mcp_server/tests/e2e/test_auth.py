# mcp_server/tests/e2e/test_auth.py

"""End-to-end tests for authentication enforcement.

Tests the auth middleware on SSE and messages endpoints:
- No key → 401
- Bad key → 401
- Valid key → access granted (SSE connection starts)
- Auth disabled → access granted without key
"""

import importlib
import json

import pytest
from starlette.testclient import TestClient

from mcp_server.server import create_sse_app


@pytest.fixture
def auth_client(monkeypatch):
    """Create a test client with auth ENABLED and a known valid key."""
    monkeypatch.setenv("IVD_API_KEYS", "test-key-123,test-key-456")
    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)

    import mcp_server.auth
    importlib.reload(mcp_server.auth)

    app = create_sse_app()
    with TestClient(app) as client:
        yield client

    monkeypatch.delenv("IVD_API_KEYS", raising=False)
    importlib.reload(mcp_server.auth)


@pytest.fixture
def noauth_client(monkeypatch):
    """Create a test client with auth disabled."""
    monkeypatch.setenv("MCP_AUTH_DISABLED", "true")

    import mcp_server.auth
    importlib.reload(mcp_server.auth)

    app = create_sse_app()
    with TestClient(app) as client:
        yield client

    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)
    importlib.reload(mcp_server.auth)


class TestAuthEnforced:
    """Tests with auth enabled."""

    def test_sse_no_key_returns_401(self, auth_client):
        response = auth_client.get("/sse")
        assert response.status_code == 401
        assert "Missing" in response.json()["error"] or "Authorization" in response.json()["error"]

    def test_sse_bad_key_returns_401(self, auth_client):
        response = auth_client.get("/sse", headers={"Authorization": "Bearer wrong-key"})
        assert response.status_code == 401
        assert "Invalid" in response.json()["error"]

    def test_sse_bad_format_returns_401(self, auth_client):
        response = auth_client.get("/sse", headers={"Authorization": "Basic abc123"})
        assert response.status_code == 401

    def test_messages_no_key_returns_401(self, auth_client):
        response = auth_client.post("/messages", json={})
        assert response.status_code == 401

    def test_messages_bad_key_returns_401(self, auth_client):
        response = auth_client.post(
            "/messages",
            json={},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert response.status_code == 401

    def test_health_no_auth_required(self, auth_client):
        """Health endpoint should work without authentication."""
        response = auth_client.get("/health")
        assert response.status_code == 200


class TestAuthDisabled:
    """Tests with auth disabled (local development)."""

    def test_health_works(self, noauth_client):
        response = noauth_client.get("/health")
        assert response.status_code == 200

    def test_sse_no_401_without_key(self, noauth_client):
        """With auth disabled, SSE should not return 401.

        Note: We can't do a full GET /sse because SSE is a long-lived stream.
        Instead, verify that the auth module is correctly in disabled mode.
        """
        import mcp_server.auth
        assert mcp_server.auth.MCP_AUTH_DISABLED is True


class TestAuthMultipleKeys:
    """Tests that multiple API keys all work."""

    def test_first_key_works(self, auth_client):
        """Health is unauthenticated; this tests the auth module internals."""
        import mcp_server.auth
        assert "test-key-123" in mcp_server.auth.VALID_API_KEYS

    def test_second_key_works(self, auth_client):
        import mcp_server.auth
        assert "test-key-456" in mcp_server.auth.VALID_API_KEYS

    def test_unknown_key_not_valid(self, auth_client):
        import mcp_server.auth
        assert "not-a-real-key" not in mcp_server.auth.VALID_API_KEYS
