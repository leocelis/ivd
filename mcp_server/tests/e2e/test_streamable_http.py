# mcp_server/tests/e2e/test_streamable_http.py

"""End-to-end tests for the StreamableHTTP transport.

Tests the new /mcp endpoint that supports POST/GET/DELETE methods
for StreamableHTTP protocol interactions.
"""

import json

import pytest
from starlette.testclient import TestClient

from mcp_server.server import create_app


@pytest.fixture
def http_client(monkeypatch):
    """Create a Starlette test client with auth disabled and no Redis."""
    monkeypatch.setenv("MCP_AUTH_DISABLED", "true")
    # Ensure no REDIS_URL so we test without event store
    monkeypatch.delenv("REDIS_URL", raising=False)

    # Re-import modules to pick up env changes
    import importlib
    import mcp_server.auth
    importlib.reload(mcp_server.auth)

    app = create_app()
    with TestClient(app) as client:
        yield client

    # Restore
    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)
    importlib.reload(mcp_server.auth)


@pytest.fixture
def http_client_with_redis(monkeypatch):
    """Create a test client with Redis event store enabled."""
    monkeypatch.setenv("MCP_AUTH_DISABLED", "true")
    # Set a fake Redis URL - actual connection won't be made during init
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

    import importlib
    import mcp_server.auth
    importlib.reload(mcp_server.auth)

    app = create_app()
    with TestClient(app) as client:
        yield client

    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)
    importlib.reload(mcp_server.auth)


class TestHealthEndpoint:
    """Tests for the enhanced /health endpoint."""

    def test_health_returns_200(self, http_client):
        response = http_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, http_client):
        response = http_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_tool_count(self, http_client):
        response = http_client.get("/health")
        data = response.json()
        assert data["tools_count"] == 15

    def test_health_has_server_name(self, http_client):
        response = http_client.get("/health")
        data = response.json()
        assert data["server"] == "ivd-tool"

    def test_health_has_version_2(self, http_client):
        """Version should be 2.0.0 after StreamableHTTP upgrade."""
        response = http_client.get("/health")
        data = response.json()
        assert data["version"] == "2.0.0"

    def test_health_reports_transports(self, http_client):
        """Health should report both streamable-http and sse transports."""
        response = http_client.get("/health")
        data = response.json()
        assert "transports" in data
        assert "streamable-http" in data["transports"]
        assert "sse" in data["transports"]

    def test_health_reports_resumable_false_without_redis(self, http_client):
        """Without Redis, resumable should be false."""
        response = http_client.get("/health")
        data = response.json()
        assert "resumable" in data
        assert data["resumable"] is False


class TestStreamableHTTPEndpoint:
    """Tests for the /mcp StreamableHTTP endpoint."""

    def test_mcp_endpoint_exists(self, http_client):
        """The /mcp endpoint should be accessible."""
        # POST without proper MCP headers should not crash
        response = http_client.post("/mcp", json={})
        # Should return some response (not 404)
        assert response.status_code != 404

    def test_mcp_supports_post(self, http_client):
        """POST method should be supported."""
        response = http_client.post("/mcp", json={})
        assert response.status_code != 405  # Method Not Allowed

    def test_mcp_supports_get(self, http_client):
        """GET method should be supported (for notifications)."""
        response = http_client.get("/mcp")
        assert response.status_code != 405

    def test_mcp_supports_delete(self, http_client):
        """DELETE method should be supported (for session termination)."""
        response = http_client.delete("/mcp")
        assert response.status_code != 405


class TestLegacySSEEndpoints:
    """Tests for backward compatibility with legacy SSE endpoints."""

    def test_sse_endpoint_still_exists(self, http_client):
        """Legacy /sse endpoint should still be accessible.

        Note: We test via POST (not GET) because GET on /sse opens a
        long-lived SSE streaming connection that blocks the synchronous
        test client.  A 405 Method Not Allowed proves the route exists
        (404 would mean it was removed).
        """
        response = http_client.post("/sse", json={})
        assert response.status_code != 404

    def test_messages_endpoint_still_exists(self, http_client):
        """Legacy /messages endpoint should still be accessible."""
        response = http_client.post("/messages", json={})
        assert response.status_code != 404


class TestProxyBufferingHeaders:
    """Tests for anti-buffering headers on MCP endpoints."""

    def test_health_has_no_buffering_headers(self, http_client):
        """Health endpoint should not have anti-buffering headers."""
        response = http_client.get("/health")
        # Health is excluded from buffering middleware
        assert "X-Accel-Buffering" not in response.headers

    def test_mcp_endpoint_has_buffering_headers(self, http_client):
        """MCP endpoint should have anti-buffering headers."""
        response = http_client.post("/mcp", json={})
        # These headers should be present on MCP endpoints
        assert response.headers.get("X-Accel-Buffering") == "no"
        assert "no-cache" in response.headers.get("Cache-Control", "")


class TestRedisIntegration:
    """Tests for Redis event store integration."""

    def test_app_initializes_without_redis(self, http_client):
        """App should work without Redis (sessions not resumable)."""
        response = http_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert data["resumable"] is False

    # Note: Full Redis integration tests would require a real Redis instance
    # or mocking the Redis client. For now, we just verify the app starts.
