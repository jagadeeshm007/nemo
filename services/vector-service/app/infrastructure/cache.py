# ==============================================================================
# Vector Service — Redis Cache
# ==============================================================================

from __future__ import annotations

import json
import logging

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def init_cache(redis_url: str) -> None:
    global _redis
    _redis = aioredis.from_url(redis_url, decode_responses=True)
    await _redis.ping()
    logger.info("Redis connection established")


async def close_cache() -> None:
    global _redis
    if _redis:
        await _redis.close()
        logger.info("Redis connection closed")


def get_redis() -> aioredis.Redis:
    assert _redis is not None, "Redis not initialized"
    return _redis


async def cache_search_results(key: str, results: list[dict], ttl: int = 300) -> None:
    r = get_redis()
    await r.set(f"search:{key}", json.dumps(results), ex=ttl)


async def get_cached_search(key: str) -> list[dict] | None:
    r = get_redis()
    raw = await r.get(f"search:{key}")
    return json.loads(raw) if raw else None
