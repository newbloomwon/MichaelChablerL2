"""Redis manager for caching recent logs."""
import json
import logging
import os
from typing import List, Optional

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisManager:
    """Manager for Redis operations with connection pooling."""

    def __init__(self, url: Optional[str] = None):
        """Initialize Redis manager."""
        self.url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        self._pool = None

    async def connect(self):
        """Establish Redis connection with connection pool."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            return

        try:
            self.client = await redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True
            )
            # Test connection
            await self.client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.client = None

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            try:
                await self.client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self.client = None

    async def cache_recent_log(self, tenant_id: str, log: dict) -> bool:
        """
        Cache a recent log entry.
        Uses LPUSH to add to list and LTRIM to keep max 1000 entries.
        Sets TTL to 900 seconds.

        Args:
            tenant_id: Tenant ID
            log: Log entry dict

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.client:
            return False

        try:
            key = f"recent_logs:{tenant_id}"
            log_json = json.dumps(log)

            # Push to list (LPUSH adds to head)
            await self.client.lpush(key, log_json)

            # Trim to max 1000 entries (keep indices 0-999)
            await self.client.ltrim(key, 0, 999)

            # Set TTL to 900 seconds
            await self.client.expire(key, 900)

            return True
        except Exception as e:
            logger.warning(f"Failed to cache log to Redis: {e}")
            return False

    async def get_recent_logs(self, tenant_id: str, count: int = 100) -> List[dict]:
        """
        Get recent logs from cache.

        Args:
            tenant_id: Tenant ID
            count: Number of logs to retrieve

        Returns:
            List of log dicts (most recent first)
        """
        if not self.client:
            return []

        try:
            key = f"recent_logs:{tenant_id}"

            # LRANGE gets from head (index 0 is most recent)
            logs_json = await self.client.lrange(key, 0, count - 1)

            logs = []
            for log_json in logs_json:
                try:
                    log = json.loads(log_json)
                    logs.append(log)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to deserialize cached log: {e}")
                    continue

            return logs
        except Exception as e:
            logger.warning(f"Failed to retrieve logs from Redis: {e}")
            return []

    async def cache_query_result(self, key: str, data: dict, ttl: int = 300) -> bool:
        """
        Cache a query result in Redis.

        Key format: query:{tenant_id}:{sha256_hash_of_query_string}
        TTL defaults to 300 seconds (5 minutes).

        Args:
            key: Cache key
            data: Dict to cache (query result with rows, aggregations, etc.)
            ttl: Time-to-live in seconds (default 300 = 5 minutes)

        Returns:
            True if cached successfully, False if Redis unavailable (graceful fallback)
        """
        if not self.client:
            return False

        try:
            serialized = json.dumps(data)
            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Failed to cache query result in Redis: {e}")
            return False

    async def get_cached_query(self, key: str) -> Optional[dict]:
        """
        Retrieve a cached query result from Redis.

        Args:
            key: Cache key

        Returns:
            Dict if found and valid JSON, None if not found or Redis unavailable
        """
        if not self.client:
            return None

        try:
            raw = await self.client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to deserialize cached query result: {e}")
            return None
        except Exception as e:
            logger.warning(f"Failed to retrieve cached query result from Redis: {e}")
            return None


# Global Redis manager instance
redis_manager = RedisManager()
