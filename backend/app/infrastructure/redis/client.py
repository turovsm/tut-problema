import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings


class AsyncRedisClient:
    def __init__(self):
        self.client: Redis | None = None
        self.enabled = settings.RATE_LIMIT_ENABLED

    async def connect(self) -> None:
        if self.enabled and not self.client:
            try:
                self.client = await redis.from_url(
                    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}",
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True,
                    encoding="utf-8",
                    socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
                    max_connections=settings.REDIS_MAX_CONNECTIONS,
                )
                await self.client.ping()
                print(
                    f"Successfully connected to Redis at {settings.REDIS_HOST}"
                )
            except Exception as e:
                print(
                    f"Failed to connect to Redis: {e}. Rate limiting disabled."
                )
                self.enabled = False
                self.client = None

    async def disconnect(self) -> None:
        if self.client:
            await self.client.close()
            self.client = None

    def is_active(self) -> bool:
        return self.enabled and self.client is not None

    async def check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int]:
        if not self.is_active():
            return True, 0

        lua_script = """
        local current = redis.call('incr', KEYS[1])
        if current == 1 then
            redis.call('expire', KEYS[1], ARGV[1])
        end
        return current
        """

        try:
            current_count = await self.client.eval(lua_script, 1, key, window)
            return current_count <= limit, current_count
        except Exception as e:
            print(f"Redis rate limit error: {e}")
            return True, 0

    async def get_ttl(self, key: str) -> int:
        if self.is_active():
            try:
                ttl = await self.client.ttl(key)
                return ttl if ttl > 0 else 0
            except Exception:
                return 0
        return 0


redis_client = AsyncRedisClient()
