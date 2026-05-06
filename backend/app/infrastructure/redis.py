from typing import Optional, Any

import redis.asyncio as redis
from app.core.config import settings
from redis.asyncio import Redis


class AsyncRedisClient:
    def __init__(self):
        self.client: Optional[Redis] = None
        self.enabled = settings.RATE_LIMIT_ENABLED

    async def connect(self) -> None:
        if self.enabled and not self.client:
            try:
                self.client = await redis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                )
                await self.client.ping()
                print(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            except Exception as e:
                print(f"Failed to connect to Redis: {e}")
                print("Rate limiting will be disabled")
                self.enabled = False
                self.client = None

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

    def is_enabled(self) -> bool:
        return self.enabled and self.client is not None

    async def get(self, key: str) -> Optional[str]:
        if not self.is_enabled():
            return None
        try:
            return await self.client.get(key)
        except Exception as e:
            print(f"Redis get error: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = None) -> bool:
        if not self.is_enabled():
            return False
        try:
            await self.client.set(key, value, ex=expire_seconds)
            return True
        except Exception as e:
            print(f"Redis set error: {e}")
            return False

    async def incr(self, key: str) -> int:
        if not self.is_enabled():
            return 0
        try:
            return await self.client.incr(key)
        except Exception as e:
            print(f"Redis incr error: {e}")
            return 0

    async def expire(self, key: str, seconds: int) -> bool:
        if not self.is_enabled():
            return False
        try:
            return await self.client.expire(key, seconds)
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        if not self.is_enabled():
            return -1
        try:
            return await self.client.ttl(key)
        except Exception as e:
            print(f"Redis ttl error: {e}")
            return -1

    async def delete(self, key: str) -> bool:
        if not self.is_enabled():
            return False
        try:
            return bool(await self.client.delete(key))
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False

    async def check_rate_limit(
            self,
            key: str,
            limit: int,
            window: int
    ) -> tuple[bool, int]:
        if not self.is_enabled():
            return True, 0

        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])

        local current = redis.call('incr', key)
        if current == 1 then
            redis.call('expire', key, window)
        end

        return {current, current <= limit}
        """

        try:
            result = await self.client.eval(lua_script, 1, key, limit, window)
            if isinstance(result, list):
                count = result[0]
                allowed = result[1]
            else:
                count = result
                allowed = count <= limit
            return allowed, count
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True, 0


redis_client = AsyncRedisClient()
