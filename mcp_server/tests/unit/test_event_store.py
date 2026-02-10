# mcp_server/tests/unit/test_event_store.py

"""Unit tests for the Redis EventStore implementation."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from mcp.types import JSONRPCMessage, JSONRPCRequest


# Mock redis.asyncio to avoid needing a real Redis instance
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_client = AsyncMock()
        mock_from_url.return_value = mock_client
        yield mock_client


class TestRedisEventStore:
    """Tests for RedisEventStore class."""

    def test_imports_successfully(self):
        """The event_store module should import without errors."""
        from mcp_server.event_store import RedisEventStore
        assert RedisEventStore is not None

    def test_initializes_with_redis_url(self, mock_redis):
        """EventStore should initialize with a Redis URL."""
        from mcp_server.event_store import RedisEventStore

        store = RedisEventStore(
            redis_url="redis://localhost:6379",
            key_prefix="test",
            ttl_seconds=600
        )
        assert store._prefix == "test"
        assert store._ttl == 600

    @pytest.mark.anyio
    async def test_store_event_increments_counter(self, mock_redis):
        """store_event should use atomic counter increment."""
        from mcp_server.event_store import RedisEventStore

        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        store = RedisEventStore(redis_url="redis://localhost:6379", key_prefix="test")

        message = JSONRPCRequest(
            jsonrpc="2.0",
            id="test-1",
            method="tools/list",
            params={}
        )

        event_id = await store.store_event("stream-123", message)

        # Should have called incr for counter
        mock_redis.incr.assert_called_once_with("test:evt_counter")

        # Should return stream_id:counter format
        assert event_id == "stream-123:1"

    @pytest.mark.anyio
    async def test_store_event_sets_ttl(self, mock_redis):
        """store_event should set TTL on the events set."""
        from mcp_server.event_store import RedisEventStore

        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        store = RedisEventStore(
            redis_url="redis://localhost:6379",
            key_prefix="test",
            ttl_seconds=3600
        )

        message = JSONRPCRequest(
            jsonrpc="2.0",
            id="test-1",
            method="tools/list",
            params={}
        )

        await store.store_event("stream-123", message)

        # Should have set TTL
        mock_redis.expire.assert_called_once_with("test:events:stream-123", 3600)

    @pytest.mark.anyio
    async def test_replay_events_after_parses_event_id(self, mock_redis):
        """replay_events_after should parse event_id format."""
        from mcp_server.event_store import RedisEventStore

        mock_redis.zrangebyscore = AsyncMock(return_value=[])

        store = RedisEventStore(redis_url="redis://localhost:6379", key_prefix="test")

        callback = AsyncMock()
        result = await store.replay_events_after("stream-123:5", callback)

        # Should have queried Redis with correct range
        mock_redis.zrangebyscore.assert_called_once_with(
            "test:events:stream-123",
            "(5",  # Exclusive: events after counter 5
            "+inf",
            withscores=True
        )

    @pytest.mark.anyio
    async def test_replay_events_after_returns_none_for_invalid_id(self, mock_redis):
        """replay_events_after should return None for invalid event ID format."""
        from mcp_server.event_store import RedisEventStore

        store = RedisEventStore(redis_url="redis://localhost:6379", key_prefix="test")

        callback = AsyncMock()

        # Invalid format (no colon)
        result = await store.replay_events_after("invalid-event-id", callback)
        assert result is None

        # Invalid format (non-numeric counter)
        result = await store.replay_events_after("stream:abc", callback)
        assert result is None

    @pytest.mark.anyio
    async def test_close_closes_redis_connection(self, mock_redis):
        """close() should close the Redis connection."""
        from mcp_server.event_store import RedisEventStore

        mock_redis.aclose = AsyncMock()

        store = RedisEventStore(redis_url="redis://localhost:6379", key_prefix="test")
        await store.close()

        mock_redis.aclose.assert_called_once()


class TestEventStoreIntegration:
    """Integration-style tests (still mocked but closer to real usage)."""

    @pytest.mark.anyio
    async def test_store_and_replay_events(self, mock_redis):
        """Test storing and replaying multiple events."""
        from mcp_server.event_store import RedisEventStore

        # Mock sequence of counters
        counter = 0

        async def mock_incr(key):
            nonlocal counter
            counter += 1
            return counter

        mock_redis.incr = mock_incr
        mock_redis.zadd = AsyncMock(return_value=1)
        mock_redis.expire = AsyncMock(return_value=True)

        # Mock replay: return 2 events
        event1_json = '{"jsonrpc":"2.0","id":"1","method":"tools/list","params":{}}'
        event2_json = '{"jsonrpc":"2.0","id":"2","method":"tools/call","params":{"name":"test"}}'

        mock_redis.zrangebyscore = AsyncMock(return_value=[
            (event1_json, 2.0),
            (event2_json, 3.0),
        ])

        store = RedisEventStore(redis_url="redis://localhost:6379", key_prefix="test")

        # Store 3 events
        message1 = JSONRPCRequest(jsonrpc="2.0", id="1", method="tools/list", params={})
        message2 = JSONRPCRequest(jsonrpc="2.0", id="2", method="tools/call", params={"name": "test"})
        message3 = JSONRPCRequest(jsonrpc="2.0", id="3", method="ping", params={})

        event_id_1 = await store.store_event("stream-abc", message1)
        event_id_2 = await store.store_event("stream-abc", message2)
        event_id_3 = await store.store_event("stream-abc", message3)

        assert event_id_1 == "stream-abc:1"
        assert event_id_2 == "stream-abc:2"
        assert event_id_3 == "stream-abc:3"

        # Replay events after event 1
        callback = AsyncMock()
        stream_id = await store.replay_events_after("stream-abc:1", callback)

        assert stream_id == "stream-abc"
        assert callback.call_count == 2  # 2 events replayed
