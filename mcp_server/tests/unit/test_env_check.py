# mcp_server/tests/unit/test_env_check.py

"""
Unit tests for mcp_server/env_check.py.

Tests the environment variable validation system that prevents
production deployments with missing env vars. This is the test layer
in the validation chain:

  env_check.py (declares) → deploy.sh (gates) → wsgi.py (boots) → tests (prevent regression)

Critical bug this prevents:
  ivd_search was broken in production because OPENAI_API_KEY was never
  added to the DO app spec. The server started fine but the tool failed
  at runtime. Now the server refuses to start without required vars.
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


class TestRequiredEnvVars:
    """Tests that the canonical list of required env vars is correct."""

    def test_env_check_module_imports(self):
        """env_check module should import without errors."""
        from mcp_server.env_check import (
            REQUIRED_ENV_VARS_REMOTE,
            REQUIRED_ENV_VARS_ALL,
            validate_env,
            check_and_warn,
        )
        assert REQUIRED_ENV_VARS_REMOTE is not None
        assert REQUIRED_ENV_VARS_ALL is not None
        assert callable(validate_env)
        assert callable(check_and_warn)

    def test_required_remote_vars_include_ivd_api_keys(self):
        """IVD_API_KEYS must be in required remote vars (auth for MCP clients)."""
        from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE
        assert "IVD_API_KEYS" in REQUIRED_ENV_VARS_REMOTE

    def test_required_remote_vars_include_openai_api_key(self):
        """OPENAI_API_KEY must be in required remote vars (ivd_search needs it)."""
        from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE
        assert "OPENAI_API_KEY" in REQUIRED_ENV_VARS_REMOTE

    def test_required_remote_vars_include_redis_url(self):
        """REDIS_URL must be in required remote vars (session resumability)."""
        from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE
        assert "REDIS_URL" in REQUIRED_ENV_VARS_REMOTE


class TestValidateEnv:
    """Tests for the validate_env() function."""

    def test_all_vars_present_returns_ok(self, monkeypatch):
        """When all required vars are set, validation passes."""
        from mcp_server.env_check import validate_env, REQUIRED_ENV_VARS_REMOTE, REQUIRED_ENV_VARS_ALL

        # Set all required vars
        for var in {**REQUIRED_ENV_VARS_ALL, **REQUIRED_ENV_VARS_REMOTE}:
            monkeypatch.setenv(var, "test_value")

        all_ok, missing = validate_env(transport="sse")
        assert all_ok is True
        assert missing == []

    def test_missing_var_returns_not_ok(self, monkeypatch):
        """When a required var is missing, validation fails with its name."""
        from mcp_server.env_check import validate_env, REQUIRED_ENV_VARS_REMOTE

        # Set all vars except OPENAI_API_KEY
        for var in REQUIRED_ENV_VARS_REMOTE:
            if var != "OPENAI_API_KEY":
                monkeypatch.setenv(var, "test_value")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        all_ok, missing = validate_env(transport="sse")
        assert all_ok is False
        assert "OPENAI_API_KEY" in missing

    def test_empty_var_treated_as_missing(self, monkeypatch):
        """An empty string is not a valid value — treated as missing."""
        from mcp_server.env_check import validate_env, REQUIRED_ENV_VARS_REMOTE

        for var in REQUIRED_ENV_VARS_REMOTE:
            monkeypatch.setenv(var, "test_value")
        # Set one to empty
        monkeypatch.setenv("OPENAI_API_KEY", "")

        all_ok, missing = validate_env(transport="sse")
        assert all_ok is False
        assert "OPENAI_API_KEY" in missing

    def test_whitespace_only_treated_as_missing(self, monkeypatch):
        """Whitespace-only value is not valid — treated as missing."""
        from mcp_server.env_check import validate_env, REQUIRED_ENV_VARS_REMOTE

        for var in REQUIRED_ENV_VARS_REMOTE:
            monkeypatch.setenv(var, "test_value")
        monkeypatch.setenv("REDIS_URL", "   ")

        all_ok, missing = validate_env(transport="sse")
        assert all_ok is False
        assert "REDIS_URL" in missing

    def test_stdio_skips_remote_vars(self, monkeypatch):
        """stdio transport should not require remote-only vars."""
        from mcp_server.env_check import validate_env, REQUIRED_ENV_VARS_ALL

        # Only set ALL vars (not remote)
        for var in REQUIRED_ENV_VARS_ALL:
            monkeypatch.setenv(var, "test_value")
        # Explicitly unset remote vars
        monkeypatch.delenv("IVD_API_KEYS", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)

        all_ok, missing = validate_env(transport="stdio")
        assert all_ok is True
        assert missing == []

    def test_multiple_missing_vars_all_reported(self, monkeypatch):
        """All missing vars should be reported, not just the first one."""
        from mcp_server.env_check import validate_env

        # Unset everything
        monkeypatch.delenv("IVD_API_KEYS", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)

        all_ok, missing = validate_env(transport="sse")
        assert all_ok is False
        assert "IVD_API_KEYS" in missing
        assert "OPENAI_API_KEY" in missing
        assert "REDIS_URL" in missing


class TestCheckAndWarn:
    """Tests for the check_and_warn() function (boot-time validation)."""

    def test_remote_transport_exits_on_missing_vars(self, monkeypatch):
        """Remote transport must exit with SystemExit(1) if vars are missing."""
        from mcp_server.env_check import check_and_warn

        monkeypatch.delenv("IVD_API_KEYS", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("REDIS_URL", raising=False)

        with pytest.raises(SystemExit) as exc_info:
            check_and_warn(transport="sse")
        assert exc_info.value.code == 1

    def test_stdio_transport_does_not_exit(self, monkeypatch):
        """stdio transport should warn but NOT exit — local dev flexibility."""
        from mcp_server.env_check import check_and_warn

        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Should not raise
        check_and_warn(transport="stdio")

    def test_all_vars_present_does_not_exit(self, monkeypatch):
        """When all vars are present, should not exit."""
        from mcp_server.env_check import check_and_warn, REQUIRED_ENV_VARS_REMOTE, REQUIRED_ENV_VARS_ALL

        for var in {**REQUIRED_ENV_VARS_ALL, **REQUIRED_ENV_VARS_REMOTE}:
            monkeypatch.setenv(var, "test_value")

        # Should not raise
        check_and_warn(transport="sse")


class TestAppYamlSync:
    """Tests that _private/do/app.yaml stays in sync with env_check.py."""

    def test_app_yaml_has_all_required_vars(self):
        """
        Every var in REQUIRED_ENV_VARS_REMOTE must exist in _private/do/app.yaml.
        
        This is the test that would have caught the OPENAI_API_KEY bug.
        If someone adds a new required var to env_check.py but forgets
        to add it to app.yaml, this test fails.
        """
        from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE

        app_yaml_path = Path(__file__).parent.parent.parent.parent / "_private" / "do" / "app.yaml"
        if not app_yaml_path.exists():
            pytest.skip("_private/do/app.yaml not available (private repo not cloned)")

        app_yaml_content = app_yaml_path.read_text()

        missing = []
        for var in REQUIRED_ENV_VARS_REMOTE:
            if f"key: {var}" not in app_yaml_content:
                missing.append(var)

        assert missing == [], (
            f"Required env vars missing from _private/do/app.yaml: {missing}. "
            f"Add them to _private/do/app.yaml envs section."
        )

    def test_env_example_has_all_required_vars(self):
        """
        Every var in REQUIRED_ENV_VARS_REMOTE must exist in .env.example.
        
        Ensures developers know which vars to set for local development.
        """
        from mcp_server.env_check import REQUIRED_ENV_VARS_REMOTE, REQUIRED_ENV_VARS_ALL

        env_example_path = Path(__file__).parent.parent.parent / ".env.example"
        assert env_example_path.exists(), f".env.example not found at {env_example_path}"

        env_example_content = env_example_path.read_text()

        all_required = {**REQUIRED_ENV_VARS_ALL, **REQUIRED_ENV_VARS_REMOTE}
        missing = []
        for var in all_required:
            if var not in env_example_content:
                missing.append(var)

        assert missing == [], (
            f"Required env vars missing from .env.example: {missing}. "
            f"Add them to mcp_server/.env.example."
        )
