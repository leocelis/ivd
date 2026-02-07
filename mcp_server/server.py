# mcp_server/server.py

"""
IVD MCP Server — standalone MCP server for Intent-Verified Development tools.

Supports both stdio (local/Cursor) and SSE (remote/DO) transports.

Usage (local/stdio):
    python -m mcp_server.server

Usage (remote/SSE):
    python -m mcp_server.server --transport sse --port 9999
"""

import argparse
import asyncio
import os
from typing import List

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from termcolor import colored

from mcp_server.auth import validate_api_key
from mcp_server.registry import call_tool, get_all_tools

NAME = "IVD MCP"

# MCP Server instance
server = Server("ivd-tool")

print(colored(f"[{NAME}] Initializing IVD MCP Server...", "magenta"))


class SSEHandledResponse(Response):
    """No-op response for when SSE has already handled the HTTP response."""
    async def __call__(self, scope, receive, send) -> None:
        pass


class SSEProxyMiddleware:
    """Add headers that prevent proxy buffering for SSE endpoints."""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"].endswith("/sse"):
            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.extend([
                        (b"X-Accel-Buffering", b"no"),
                        (b"Cache-Control", b"no-cache, no-transform"),
                        (b"Connection", b"keep-alive"),
                    ])
                    message = {**message, "headers": headers}
                await send(message)
            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Return list of available tools."""
    tools = get_all_tools()
    print(colored(f"[{NAME}] Client requested tool list: {len(tools)} tools", "cyan"))
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool invocation."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, call_tool, name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_msg = f"Error executing {name}: {e}"
        print(colored(f"[{NAME}] {error_msg}", "red"))
        return [TextContent(type="text", text=error_msg)]


async def run_stdio() -> None:
    """Run with stdio transport (local/Cursor)."""
    print(colored(f"[{NAME}] Starting stdio transport...", "magenta"))
    async with stdio_server() as (read_stream, write_stream):
        print(colored(f"[{NAME}] stdio transport ready", "green"))
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def create_sse_app() -> Starlette:
    """Create Starlette app with SSE transport for remote MCP access."""
    mcp_path_prefix = os.environ.get("MCP_PATH_PREFIX", "")
    messages_path = f"{mcp_path_prefix}/messages" if mcp_path_prefix else "/messages"

    print(colored(f"[{NAME}] Messages endpoint: {messages_path}", "cyan"))
    sse = SseServerTransport(messages_path)

    async def health_check(request):
        tools = get_all_tools()
        return JSONResponse({
            "status": "healthy",
            "server": "ivd-tool",
            "version": "1.0.0",
            "tools_count": len(tools),
        })

    async def handle_sse(request):
        print(colored(f"[{NAME}] SSE connection from {request.client.host}", "cyan"))

        auth_result = await validate_api_key(request)
        if auth_result is not None:
            return auth_result

        print(colored(f"[{NAME}] Client connected: {request.client.host}", "green"))

        try:
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
                await server.run(streams[0], streams[1], server.create_initialization_options())
        except Exception as e:
            print(colored(f"[{NAME}] Connection error: {e}", "yellow"))
        finally:
            print(colored(f"[{NAME}] Client disconnected: {request.client.host}", "yellow"))

        return SSEHandledResponse()

    async def handle_messages(request):
        auth_result = await validate_api_key(request)
        if auth_result is not None:
            return auth_result

        try:
            await sse.handle_post_message(request.scope, request.receive, request._send)
        except Exception as e:
            print(colored(f"[{NAME}] Message error: {e}", "yellow"))

        return SSEHandledResponse()

    return Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            Route("/sse", handle_sse, methods=["GET"]),
            Route("/messages", handle_messages, methods=["POST"]),
        ],
        middleware=[Middleware(SSEProxyMiddleware)],
    )


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="IVD MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    if args.transport == "stdio":
        print(colored(f"[{NAME}] Mode: STDIO (local)", "magenta"))
        asyncio.run(run_stdio())
    else:
        print(colored(f"[{NAME}] Mode: SSE (HTTP) on port {args.port}", "magenta"))
        if args.reload:
            uvicorn.run("mcp_server.server:create_sse_app", host="0.0.0.0", port=args.port, reload=True, factory=True)
        else:
            app = create_sse_app()
            uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
