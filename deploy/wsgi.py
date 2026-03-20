"""
WSGI entry point for IVD MCP Server on DigitalOcean App Platform.

Handles path setup for the DO environment, then creates the SSE app.

Usage:
    python wsgi.py [--port PORT]
"""

import os
import sys

# App Platform compatibility: ensure mcp_server.* imports work
workspace_path = "/workspace"
if os.path.exists(workspace_path):
    sys.path.insert(0, workspace_path)
else:
    # Local development — ensure repo root is on path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server.env_check import check_and_warn
from mcp_server.server import create_sse_app

import argparse
import uvicorn

# Validate all required environment variables BEFORE creating the app.
# Exits with code 1 if any are missing — prevents silent production failures.
check_and_warn(transport="sse")

# Create app at module level for uvicorn import string usage
app = create_sse_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IVD MCP Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    args = parser.parse_args()

    print(f"[IVD MCP] Starting SSE server on port {args.port}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        # SSE connections are long-lived; default 5s is far too low and causes
        # DO load balancer to close idle connections.  600s = 10 minutes.
        timeout_keep_alive=600,
        # Give in-flight SSE streams time to drain on deploy/restart
        timeout_graceful_shutdown=30,
    )
