# mcp_server/server.py

"""
IVD MCP Server — standalone MCP server for Intent-Verified Development tools.

Supports stdio (local/Cursor), SSE (legacy remote), and StreamableHTTP (modern remote).

Usage (local/stdio):
    python -m mcp_server.server

Usage (remote/SSE+StreamableHTTP):
    python -m mcp_server.server --transport sse --port 9999
"""

import argparse
import asyncio
import contextlib
import os
from collections.abc import AsyncIterator
from contextvars import ContextVar
from typing import List, Optional

import uvicorn
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from termcolor import colored

from mcp_server.auth import validate_api_key
from mcp_server.logger import log_health_check
from mcp_server.registry import call_tool, get_all_tools

# ── SSE Keepalive Patch (for legacy /sse endpoint) ───────────────────────────
# Still needed for Cursor clients which only support SSE transport.
import sse_starlette.sse as _sse_module

_OriginalEventSourceResponse = _sse_module.EventSourceResponse


class _KeepaliveEventSourceResponse(_OriginalEventSourceResponse):
    """EventSourceResponse with default keepalive ping for SSE connections."""

    SSE_PING_INTERVAL = 15  # seconds between keepalive pings

    def __init__(self, *args, **kwargs):
        if kwargs.get("ping") is None:
            kwargs["ping"] = self.SSE_PING_INTERVAL
        super().__init__(*args, **kwargs)


_sse_module.EventSourceResponse = _KeepaliveEventSourceResponse
# ── End SSE Keepalive Patch ───────────────────────────────────────────────────

# Context variables to store request info for tool call logging
_request_context: ContextVar[Optional[dict]] = ContextVar("request_context", default=None)

NAME = "IVD MCP"

# MCP Server instance
server = Server("ivd-tool")

print(colored(f"[{NAME}] Initializing IVD MCP Server...", "magenta"))


class SSEHandledResponse(Response):
    """No-op response for when SSE/StreamableHTTP has already handled the HTTP response."""
    async def __call__(self, scope, receive, send) -> None:
        pass


class ProxyBufferMiddleware:
    """Add headers that prevent proxy buffering for all MCP endpoints.

    Cloud providers (DO, AWS) and reverse proxies (nginx, Cloudflare) buffer
    responses by default. This middleware disables buffering so SSE events
    and StreamableHTTP streaming responses are sent immediately.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope["path"] != "/health":
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
    return tools


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Handle tool invocation."""
    try:
        loop = asyncio.get_event_loop()
        
        # Get request context (API key, IP) from context vars (SSE mode)
        # Falls back to None for stdio mode
        ctx = _request_context.get()
        api_key = ctx.get("api_key") if ctx else None
        request = ctx.get("request") if ctx else None
        
        result = await loop.run_in_executor(None, call_tool, name, arguments, api_key, request)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_msg = f"Error executing {name}: {e}"
        return [TextContent(type="text", text=error_msg)]


async def run_stdio() -> None:
    """Run with stdio transport (local/Cursor)."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def create_app() -> Starlette:
    """Create Starlette app with StreamableHTTP + legacy SSE transports."""

    # ── Redis EventStore (optional, enables session resumability) ─────────
    # Uses mcp_server/redis_utils connection helper
    event_store = None
    if os.environ.get("REDIS_URL"):
        from mcp_server.event_store import RedisEventStore
        event_store = RedisEventStore(key_prefix="ivd")  # Connection helper reads REDIS_URL
        print(colored(f"[{NAME}] Redis EventStore enabled (resumable sessions)", "green"))
    else:
        print(colored(f"[{NAME}] No REDIS_URL — sessions not resumable across restarts", "yellow"))

    # ── StreamableHTTP Session Manager ────────────────────────────────────
    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=event_store,
        json_response=False,   # Stream responses via SSE (within POST)
        stateless=False,       # Track sessions for resumability
    )

    # ── Legacy SSE Transport ──────────────────────────────────────────────
    mcp_path_prefix = os.environ.get("MCP_PATH_PREFIX", "")
    messages_path = f"{mcp_path_prefix}/messages" if mcp_path_prefix else "/messages"
    sse_transport = SseServerTransport(messages_path)

    # ── Starlette Lifespan ────────────────────────────────────────────────
    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            print(colored(f"[{NAME}] StreamableHTTP session manager started", "green"))
            try:
                yield
            finally:
                print(colored(f"[{NAME}] StreamableHTTP session manager stopping", "yellow"))
                # Clean up Redis connection if EventStore is enabled
                if event_store is not None:
                    try:
                        await event_store.close()
                        print(colored(f"[{NAME}] Redis EventStore connection closed", "green"))
                    except Exception as e:
                        print(colored(f"[{NAME}] Error closing EventStore: {e}", "yellow"))

    # ── Route Handlers ────────────────────────────────────────────────────

    async def health_check(request: Request) -> JSONResponse:
        """
        Health check endpoint for load balancer and monitoring.
        
        Returns:
            JSON response with server status, version, and capabilities
        """
        tools = get_all_tools()
        log_health_check(len(tools))
        return JSONResponse({
            "status": "healthy",
            "server": "ivd-tool",
            "version": "2.0.0",
            "tools_count": len(tools),
            "transports": ["streamable-http", "sse"],
            "resumable": event_store is not None,
        })

    async def handle_streamable_http(request: Request) -> Response:
        """
        StreamableHTTP endpoint — POST (tool calls), GET (notifications), DELETE (terminate).
        
        Handles modern MCP StreamableHTTP protocol with session management and
        optional Redis-backed event replay for resumability.
        
        Args:
            request: Starlette request object
            
        Returns:
            SSEHandledResponse (no-op, transport handles response directly)
        """
        print(colored(f"[{NAME}] StreamableHTTP {request.method} from {request.client.host}", "cyan"))

        auth_result, api_key = await validate_api_key(request)
        if auth_result is not None:
            return auth_result

        _request_context.set({"api_key": api_key, "request": request})
        try:
            await session_manager.handle_request(
                request.scope, request.receive, request._send
            )
        except Exception as e:
            print(colored(f"[{NAME}] StreamableHTTP error: {e}", "yellow"))
        finally:
            _request_context.set(None)

        return SSEHandledResponse()

    async def handle_sse(request: Request) -> Response:
        """
        [LEGACY] SSE endpoint for Cursor clients.
        
        Maintains backward compatibility with clients that only support SSE transport.
        Once Cursor adds StreamableHTTP support, clients should migrate to /mcp.
        
        Args:
            request: Starlette request object
            
        Returns:
            SSEHandledResponse (no-op, transport handles response directly)
        """
        print(colored(f"[{NAME}] [Legacy SSE] Connection from {request.client.host}", "cyan"))

        auth_result, api_key = await validate_api_key(request)
        if auth_result is not None:
            return auth_result

        _request_context.set({"api_key": api_key, "request": request})
        try:
            async with sse_transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await server.run(
                    streams[0], streams[1],
                    server.create_initialization_options()
                )
        except Exception as e:
            print(colored(f"[{NAME}] [Legacy SSE] Connection error: {e}", "yellow"))
        finally:
            _request_context.set(None)

        return SSEHandledResponse()

    async def handle_messages(request: Request) -> Response:
        """
        [LEGACY] SSE message handler for Cursor clients.
        
        Handles POST messages for legacy SSE transport.
        
        Args:
            request: Starlette request object
            
        Returns:
            SSEHandledResponse (no-op, transport handles response directly)
        """
        auth_result, api_key = await validate_api_key(request)
        if auth_result is not None:
            return auth_result

        _request_context.set({"api_key": api_key, "request": request})
        try:
            await sse_transport.handle_post_message(
                request.scope, request.receive, request._send
            )
        except Exception as e:
            print(colored(f"[{NAME}] [Legacy SSE] Message error: {e}", "yellow"))

        return SSEHandledResponse()

    # ── App Assembly ──────────────────────────────────────────────────────
    return Starlette(
        routes=[
            Route("/health", health_check, methods=["GET"]),
            # StreamableHTTP (recommended — for VS Code Copilot + future Cursor)
            Route("/mcp", handle_streamable_http, methods=["GET", "POST", "DELETE"]),
            # Legacy SSE (for current Cursor clients)
            Route("/sse", handle_sse, methods=["GET"]),
            Route("/messages", handle_messages, methods=["POST"]),
        ],
        middleware=[Middleware(ProxyBufferMiddleware)],
        lifespan=lifespan,
    )


# Backwards-compat alias so wsgi.py doesn't need changes
create_sse_app = create_app


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="IVD MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--port", type=int, default=9999)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    if args.transport == "stdio":
        asyncio.run(run_stdio())
    else:
        uvicorn_kwargs = dict(
            host="0.0.0.0",
            port=args.port,
            timeout_keep_alive=600,
            timeout_graceful_shutdown=30,
        )
        if args.reload:
            uvicorn.run("mcp_server.server:create_app", factory=True, reload=True, **uvicorn_kwargs)
        else:
            app = create_app()
            uvicorn.run(app, **uvicorn_kwargs)


if __name__ == "__main__":
    main()
