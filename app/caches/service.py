from fastapi import Depends
from typing import Any, Annotated
from settings.config import Configs, get_config
from redis.asyncio import Redis, from_url as redis_from_url

class Cache:
    def __init__(self, url: str):
        self.url = url
        self.redis: Redis = None # type: ignore

    async def connect(self) -> Any: 
        if self.url:
            self.redis = await redis_from_url(self.url)

    async def close(self) -> None:
        if self.redis:
            await self.redis.close()

    async def set(self, key: str, value: Any, exp: int) -> Any:
        if self.redis:
            await self.redis.setex(key, exp, value)

    async def get(self, key: str) -> Any:
        if self.redis:
            return await self.redis.get(key)

    async def delete(self, key: str) -> Any:
        if self.redis:
            await self.redis.delete(key)

async def get_cache_service(config: Configs= Depends(get_config)) -> Cache:
    cache_service = Cache(url=config.REDIS_URL)

    await cache_service.connect()
    return cache_service

CacheService = Annotated[Cache, Depends(get_cache_service)]