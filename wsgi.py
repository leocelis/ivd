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

from mcp_server.server import create_sse_app

import argparse
import uvicorn

# Create app at module level for uvicorn import string usage
app = create_sse_app()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IVD MCP Server")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    args = parser.parse_args()

    print(f"[IVD MCP] Starting SSE server on port {args.port}")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
