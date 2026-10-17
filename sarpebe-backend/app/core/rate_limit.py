import logging
import redis.asyncio as redis
from redis.exceptions import RedisError

from app.config import settings

logger = logging.getLogger(__name__)

_client: redis.Redis | None = None


def _get_client() -> redis.Redis:
    global _client
    if _client is None:
        kwargs = {}
        # Same relaxation the Celery broker URL gets for Upstash-style rediss:// endpoints.
        if settings.redis_url.startswith("rediss://") and "ssl_cert_reqs" not in settings.redis_url:
            kwargs["ssl_cert_reqs"] = "none"
        _client = redis.from_url(settings.redis_url, decode_responses=True, **kwargs)
    return _client


# Counters fail open: if Redis is unreachable, authentication keeps working without
# rate limiting rather than locking everyone out.

async def get_count(key: str) -> int:
    try:
        value = await _get_client().get(key)
        return int(value) if value else 0
    except (RedisError, OSError) as e:
        logger.warning("Rate limit read failed for %s: %s", key, e)
        return 0


async def increment(key: str, window_seconds: int) -> int:
    """Adds one to the counter and starts its expiry window on first use. Returns the new count."""
    try:
        client = _get_client()
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return count
    except (RedisError, OSError) as e:
        logger.warning("Rate limit increment failed for %s: %s", key, e)
        return 0


async def reset(key: str) -> None:
    try:
        await _get_client().delete(key)
    except (RedisError, OSError) as e:
        logger.warning("Rate limit reset failed for %s: %s", key, e)
