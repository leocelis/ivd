"""
Redis-backed EventStore for MCP StreamableHTTP session resumability.

Implements the MCP SDK's EventStore interface to persist events in Redis,
enabling clients to resume sessions after disconnection or server restart.

Events stored in Redis Sorted Sets keyed by stream_id, with monotonic
counters as scores for ordering. All keys auto-expire after TTL.
"""

import logging
from collections.abc import Awaitable, Callable
from typing import Optional

from mcp.server.streamable_http import EventStore, EventMessage
from mcp.types import JSONRPCMessage

from mcp_server.redis_utils import get_async_redis_connection

logger = logging.getLogger(__name__)

# Type alias for event callback from MCP SDK
EventCallback = Callable[[EventMessage], Awaitable[None]]


class RedisEventStore(EventStore):
    """Redis-backed event store for MCP session resumability."""

    def __init__(self, redis_url: Optional[str] = None, key_prefix: str = "mcp", ttl_seconds: int = 3600):
        """
        Args:
            redis_url: Optional Redis connection URL. If None, uses REDIS_URL env var or localhost
            key_prefix: Namespace prefix for all Redis keys (e.g., "ivd" or "ada")
            ttl_seconds: TTL for stored events (default: 1 hour)
        """
        self._redis = get_async_redis_connection(redis_url)
        self._prefix = key_prefix
        self._ttl = ttl_seconds

    async def store_event(self, stream_id: str, message: JSONRPCMessage) -> str:
        """
        Store an event and return its unique event ID.
        
        Args:
            stream_id: Unique identifier for the MCP session stream
            message: JSON-RPC message to persist
            
        Returns:
            Event ID in format "stream_id:counter" for resumability tracking
        """
        counter_key = f"{self._prefix}:evt_counter"
        events_key = f"{self._prefix}:events:{stream_id}"

        # Atomic increment for monotonic event IDs
        counter = await self._redis.incr(counter_key)
        event_id = f"{stream_id}:{counter}"

        # Serialize and store in sorted set (score = counter for ordering)
        event_data = message.model_dump_json(by_alias=True, exclude_none=True)
        await self._redis.zadd(events_key, {event_data: counter})

        # Set/refresh TTL on the events set
        await self._redis.expire(events_key, self._ttl)

        logger.debug("Stored event %s for stream %s", event_id, stream_id)
        return event_id

    async def replay_events_after(
        self,
        last_event_id: str,
        send_callback: EventCallback,
    ) -> Optional[str]:
        """
        Replay events that occurred after the given event ID.
        
        Args:
            last_event_id: Last event ID client received (format: "stream_id:counter")
            send_callback: Async callback to send EventMessage to client
            
        Returns:
            Stream ID if events were replayed, None if no events or invalid ID
        """
        # Parse stream_id and counter from "stream_id:counter" format
        parts = last_event_id.rsplit(":", 1)
        if len(parts) != 2:
            logger.warning("Invalid event ID format: %s", last_event_id)
            return None

        stream_id, counter_str = parts
        try:
            last_counter = int(counter_str)
        except ValueError:
            logger.warning("Invalid counter in event ID: %s", last_event_id)
            return None

        events_key = f"{self._prefix}:events:{stream_id}"

        # Get all events with score > last_counter (exclusive)
        events = await self._redis.zrangebyscore(
            events_key, f"({last_counter}", "+inf", withscores=True
        )

        if not events:
            logger.debug("No events to replay after %s", last_event_id)
            return None

        for event_data, score in events:
            event_id = f"{stream_id}:{int(score)}"
            message = JSONRPCMessage.model_validate_json(event_data)
            await send_callback(EventMessage(message=message, event_id=event_id))

        logger.info("Replayed %d events for stream %s", len(events), stream_id)
        return stream_id

    async def close(self) -> None:
        """
        Close the Redis connection.
        
        Should be called during application shutdown to clean up resources.
        """
        await self._redis.aclose()
