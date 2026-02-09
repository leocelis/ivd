# mcp_server/tests/e2e/test_sse.py

"""End-to-end tests for the SSE (HTTP) transport.

Starts a real Starlette test client against the SSE app and verifies:
- Health endpoint works
- Health response has expected structure
- Tool count matches expected 14
"""

import json

import pytest
from starlette.testclient import TestClient

from mcp_server.server import create_sse_app


@pytest.fixture
def sse_client(monkeypatch):
    """Create a Starlette test client with auth disabled."""
    monkeypatch.setenv("MCP_AUTH_DISABLED", "true")

    # Re-import auth module to pick up env change
    import importlib
    import mcp_server.auth
    importlib.reload(mcp_server.auth)

    app = create_sse_app()
    with TestClient(app) as client:
        yield client

    # Restore
    monkeypatch.delenv("MCP_AUTH_DISABLED", raising=False)
    importlib.reload(mcp_server.auth)


class TestSSEHealth:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, sse_client):
        response = sse_client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, sse_client):
        response = sse_client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_has_tool_count(self, sse_client):
        response = sse_client.get("/health")
        data = response.json()
        assert data["tools_count"] == 15

    def test_health_has_server_name(self, sse_client):
        response = sse_client.get("/health")
        data = response.json()
        assert data["server"] == "ivd-tool"

    def test_health_has_version(self, sse_client):
        response = sse_client.get("/health")
        data = response.json()
        assert "version" in data
