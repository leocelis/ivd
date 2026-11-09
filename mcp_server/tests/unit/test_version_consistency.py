"""The server reports one version everywhere.

Before this test, initialize said 1.30.0 (the mcp library's own version, because
Server() was built without one), /health said 2.0.0, pyproject.toml 3.1.0 and the
registry's server.json 3.1.2.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _pyproject_version():
    m = re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(), re.M)
    return m.group(1)


def test_server_pyproject_and_registry_agree():
    from mcp_server.server import SERVER_VERSION

    registry = json.loads((ROOT / "server.json").read_text())
    versions = {registry["version"]} | {p["version"] for p in registry.get("packages", []) if "version" in p}
    assert versions == {SERVER_VERSION}
    assert _pyproject_version() == SERVER_VERSION


def test_initialize_reports_the_server_version():
    from mcp_server.server import SERVER_VERSION, server

    assert server.create_initialization_options().server_version == SERVER_VERSION
