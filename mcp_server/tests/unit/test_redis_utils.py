"""Redis connection helper: survives a server-closed idle connection and never logs credentials.

Managed Redis closes connections that sit idle. ``redis.asyncio.from_url`` builds its
own pool without the client's default ``Retry``, so a closed connection failed the next
command outright (``ConnectionError: Connection closed by server``) instead of
reconnecting. The test server below speaks just enough RESP to answer the commands
the client sends, and can drop every client connection on demand.
"""

import asyncio

import pytest

from mcp_server import redis_utils


class _DroppingRedis:
    """Minimal RESP server: HELLO, INCR/INCRBY, PING, +OK for the rest; can drop all clients."""

    def __init__(self):
        self.counter = 0
        self.writers = []
        self.server = None

    async def start(self) -> int:
        self.server = await asyncio.start_server(self._handle, "127.0.0.1", 0)
        return self.server.sockets[0].getsockname()[1]

    async def stop(self):
        self.drop_all()
        self.server.close()
        await self.server.wait_closed()

    def drop_all(self):
        for w in self.writers:
            w.close()
        self.writers.clear()

    async def _read_command(self, reader):
        line = await reader.readline()
        if not line:
            return None
        n = int(line[1:].strip())
        parts = []
        for _ in range(n):
            size = int((await reader.readline())[1:].strip())
            parts.append((await reader.readexactly(size + 2))[:-2].decode())
        return parts

    async def _handle(self, reader, writer):
        self.writers.append(writer)
        try:
            while True:
                cmd = await self._read_command(reader)
                if cmd is None:
                    break
                name = cmd[0].upper()
                if name in ("INCR", "INCRBY"):
                    self.counter += int(cmd[2]) if name == "INCRBY" else 1
                    writer.write(f":{self.counter}\r\n".encode())
                elif name == "HELLO":
                    writer.write(b"%1\r\n+proto\r\n:3\r\n")
                elif name == "PING":
                    writer.write(b"+PONG\r\n")
                else:
                    writer.write(b"+OK\r\n")
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass


def test_command_after_server_closed_the_connection_succeeds():
    async def run():
        server = _DroppingRedis()
        port = await server.start()
        client = redis_utils.get_async_redis_connection(f"redis://127.0.0.1:{port}/0")
        try:
            assert await client.incr("k") == 1
            server.drop_all()  # what managed Redis does to an idle connection
            await asyncio.sleep(0.05)
            assert await client.incr("k") == 2
        finally:
            await client.aclose()
            await server.stop()

    asyncio.run(run())


@pytest.mark.parametrize(
    "url",
    [
        "rediss://default:s3cr3t-pass@redis.example.com:25061",
        "redis://:s3cr3t-pass@localhost:6379/0",
    ],
)
def test_connection_log_never_contains_the_password(url, capsys):
    redis_utils.get_async_redis_connection(url)
    out = capsys.readouterr().out
    assert "s3cr3t-pass" not in out
    assert "[Redis]" in out
