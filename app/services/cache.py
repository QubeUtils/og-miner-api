import redis.asyncio as redis
import orjson
from typing import Optional, Any
from app.core.config import settings

class CacheService:
    def __init__(self):
        # ssl_cert_reqs=None is often required for Heroku Redis
        self.redis = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True, ssl_cert_reqs=None)

    async def get(self, key: str) -> Optional[dict]:
        data = await self.redis.get(key)
        if data:
            return orjson.loads(data)
        return None

    async def set(self, key: str, value: Any, ttl: int = 86400):
        await self.redis.set(key, orjson.dumps(value), ex=ttl)

    async def close(self):
        await self.redis.close()

    async def ping(self) -> bool:
        try:
            return await self.redis.ping()
        except:
            return False

cache_service = CacheService()
