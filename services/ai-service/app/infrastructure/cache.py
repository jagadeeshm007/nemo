# ==============================================================================
# AI Service — Redis Cache
# ==============================================================================

import json
from typing import Any

import redis.asyncio as aioredis

from app.config import Settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Async Redis client for caching, sessions, and transient state."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            self._settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
        await self._client.ping()
        logger.info("Redis connected")

    async def disconnect(self) -> None:
        if self._client:
            await self._client.close()
            logger.info("Redis disconnected")

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("Redis not connected")
        return self._client

    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def get_json(self, key: str) -> Any | None:
        data = await self.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        await self.set(key, json.dumps(value), ttl)

    # Model config cache
    async def get_model_config(self) -> dict | None:
        return await self.get_json("model:config")

    async def set_model_config(self, config: dict) -> None:
        await self.set_json("model:config", config, ttl=600)

    # Response cache
    async def get_cached_response(self, cache_key: str) -> str | None:
        return await self.get(f"cache:response:{cache_key}")

    async def set_cached_response(self, cache_key: str, response: str, ttl: int = 300) -> None:
        await self.set(f"cache:response:{cache_key}", response, ttl)
