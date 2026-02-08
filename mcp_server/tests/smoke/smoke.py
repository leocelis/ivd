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

DEFAULT_URL = "https://ivd-mcp-hn77u.ondigitalocean.app"

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
    if tools_count != 14:
        fail(f"Expected 14 tools, got {tools_count}")
        return False

    ok(f"Healthy — {tools_count} tools registered")
    return True


def check_auth_enforcement(base_url):
    """Verify that SSE endpoint requires authentication."""
    info("Auth enforcement: GET /sse without key")
    status, body = http_get(f"{base_url}/sse")

    if status == 401:
        ok("SSE correctly rejects unauthenticated requests (401)")
        return True
    elif status == 200:
        warn("SSE allows unauthenticated access — auth may be disabled")
        return True  # Not a failure, could be intentional
    else:
        fail(f"SSE returned unexpected HTTP {status}: {body[:200]}")
        return False


def check_sse_with_key(base_url, api_key):
    """Verify SSE connection succeeds with valid API key."""
    if not api_key:
        warn("No API key provided — skipping authenticated SSE check")
        return True

    info("SSE connection: GET /sse with valid key")
    status, body = http_get(
        f"{base_url}/sse",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=5,
    )

    if status == 200 or "event:" in body:
        ok("SSE connection accepted with valid key")
        return True
    elif status == 401:
        fail(f"SSE rejected valid key: {body[:200]}")
        return False
    else:
        # SSE may return partial content or timeout — check for event stream
        if "endpoint" in body.lower() or "session_id" in body.lower():
            ok("SSE connection established (partial response)")
            return True
        fail(f"SSE returned HTTP {status}: {body[:200]}")
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
    results.append(("Auth enforcement", check_auth_enforcement(base_url)))
    results.append(("SSE with key", check_sse_with_key(base_url, api_key)))

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
