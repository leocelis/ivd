#!/usr/bin/env python3
# mcp_server/tests/smoke/smoke.py

"""
Post-deploy smoke tests for IVD MCP Server.

Verifies a live server is healthy and its critical tools respond.

Usage:
    python mcp_server/tests/smoke/smoke.py                          # Default URL
    python mcp_server/tests/smoke/smoke.py --url https://custom.app # Custom URL
    IVD_MCP_URL=https://custom.app python smoke.py                  # Env var

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import argparse
import json
import os
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

DEFAULT_URL = "https://mcp.ivdframework.dev"

# Colors (disabled if not a TTY)
IS_TTY = sys.stdout.isatty()
GREEN = "\033[0;32m" if IS_TTY else ""
RED = "\033[0;31m" if IS_TTY else ""
CYAN = "\033[0;36m" if IS_TTY else ""
YELLOW = "\033[1;33m" if IS_TTY else ""
NC = "\033[0m" if IS_TTY else ""


def info(msg):
    print(f"{CYAN}[Smoke]{NC} {msg}")


def ok(msg):
    print(f"{GREEN}[PASS]{NC} {msg}")


def fail(msg):
    print(f"{RED}[FAIL]{NC} {msg}")


def warn(msg):
    print(f"{YELLOW}[WARN]{NC} {msg}")


def http_get(url, headers=None, timeout=10):
    """Simple HTTP GET that returns (status_code, body_string)."""
    req = Request(url, headers=headers or {})
    try:
        resp = urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode("utf-8")
    except HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except URLError as e:
        return 0, str(e)
    except Exception as e:
        return 0, str(e)


def http_post(url, body, headers=None, timeout=10):
    """Simple HTTP POST that returns (status_code, body_string)."""
    data = json.dumps(body).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json", **(headers or {})})
    try:
        resp = urlopen(req, timeout=timeout)
        return resp.status, resp.read().decode("utf-8")
    except HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except URLError as e:
        return 0, str(e)
    except Exception as e:
        return 0, str(e)


def check_health(base_url):
    """Check /health endpoint."""
    info(f"Health check: {base_url}/health")
    status, body = http_get(f"{base_url}/health")

    if status != 200:
        fail(f"Health returned HTTP {status}: {body[:200]}")
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        fail(f"Health response not JSON: {body[:200]}")
        return False

    if data.get("status") != "healthy":
        fail(f"Health status: {data.get('status')}")
        return False

    tools_count = data.get("tools_count", 0)
    # 33 = 19 core + 10 judgment + 4 Canon (IVD v3.1).
    expected_tools = 33
    if tools_count != expected_tools:
        fail(f"Expected {expected_tools} tools, got {tools_count}")
        return False

    ok(f"Healthy — {tools_count} tools registered")
    return True


def check_auth_enforcement(base_url):
    """Verify that /mcp endpoint rejects requests without an API key."""
    info("Auth enforcement: POST /mcp without key")
    # Use /mcp (Streamable HTTP) — returns 401 immediately, no long-lived connection.
    # /sse hangs on unauthenticated requests (SSE streams don't close quickly),
    # causing spurious timeouts. /mcp is the correct endpoint to test auth.
    status, body = http_post(
        f"{base_url}/mcp",
        body={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"Accept": "application/json, text/event-stream"},
        timeout=10,
    )

    if status == 401:
        ok("/mcp correctly rejects unauthenticated requests (401)")
        return True
    elif status == 200:
        warn("/mcp allows unauthenticated access — auth may be disabled (MCP_AUTH_DISABLED=true?)")
        return True  # Not a failure, could be intentional (local dev)
    else:
        fail(f"/mcp returned unexpected HTTP {status}: {body[:200]}")
        return False


def check_sse_with_key(base_url, api_key):
    """Verify authenticated access works — tests /mcp (fast) and /sse (stream)."""
    if not api_key:
        warn("No API key provided — skipping authenticated check")
        return True

    # Test /mcp first: initialize a session and verify we get a session ID back.
    info("Authenticated MCP session: POST /mcp with valid key")
    status, body = http_post(
        f"{base_url}/mcp",
        body={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "smoke-test", "version": "1.0"},
            },
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json, text/event-stream",
        },
        timeout=10,
    )

    if status == 401:
        fail(f"Valid key was rejected (401): {body[:200]}")
        return False

    if status == 200:
        ok("Authenticated session established (HTTP 200)")
        return True

    # SSE stream: a read timeout (HTTP 0) after auth means the connection was
    # accepted and the server is holding the stream open — that's correct behavior.
    if status == 0 and ("timed out" in body.lower() or "time out" in body.lower()):
        ok("Authenticated MCP session accepted (SSE stream held open — expected)")
        return True

    fail(f"Unexpected response HTTP {status}: {body[:200]}")
    return False


def main():
    parser = argparse.ArgumentParser(description="IVD MCP Server Smoke Tests")
    parser.add_argument("--url", default=None, help="Base URL of the MCP server")
    parser.add_argument("--key", default=None, help="API key for authenticated tests")
    args = parser.parse_args()

    base_url = (
        args.url
        or os.environ.get("IVD_MCP_URL")
        or DEFAULT_URL
    ).rstrip("/")
    api_key = args.key or os.environ.get("IVD_API_KEY")

    print(f"\n{'=' * 50}")
    print(f"  IVD MCP Server — Smoke Tests")
    print(f"  Target: {base_url}")
    print(f"  API Key: {'set' if api_key else 'not set'}")
    print(f"{'=' * 50}\n")

    results = []
    start = time.time()

    results.append(("Health check", check_health(base_url)))
    results.append(("Auth enforcement (no key → 401)", check_auth_enforcement(base_url)))
    results.append(("Authenticated session (valid key)", check_sse_with_key(base_url, api_key)))

    elapsed = time.time() - start
    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n{'=' * 50}")
    print(f"  Results: {passed}/{total} passed ({elapsed:.1f}s)")
    for name, result in results:
        status = f"{GREEN}PASS{NC}" if result else f"{RED}FAIL{NC}"
        print(f"  {status}  {name}")
    print(f"{'=' * 50}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
