# mcp_server/redis_utils.py

"""
Redis connection utilities for IVD MCP Server.

Provides async Redis connection helper that respects REDIS_URL environment
variable for managed Redis instances (e.g., DigitalOcean).
"""

import os
from typing import Optional

import redis.asyncio as aioredis
from termcolor import colored


def get_async_redis_connection(redis_url: Optional[str] = None) -> aioredis.Redis:
    """
    Get async Redis connection.
    
    Used by MCP server for event persistence and session management.
    Checks REDIS_URL environment variable if redis_url not provided.
    Falls back to localhost:6379 for local development.
    
    Args:
        redis_url: Optional Redis URL. If None, uses REDIS_URL env var or localhost
        
    Returns:
        Async Redis connection with decode_responses=True
        
    Examples:
        >>> conn = get_async_redis_connection()
        >>> await conn.set('key', 'value')
        >>> await conn.get('key')
        'value'
    """
    if redis_url is None:
        redis_url = os.environ.get('REDIS_URL')
    
    if redis_url:
        print(colored(f"[Redis] Async connection to managed Redis: {redis_url[:50]}...", "cyan"))
        return aioredis.from_url(redis_url, decode_responses=True)
    else:
        print(colored("[Redis] Async connection to localhost:6379", "cyan"))
        return aioredis.from_url("redis://localhost:6379", decode_responses=True)
