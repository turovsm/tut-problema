from app.infrastructure.redis.client import redis_client


class RateLimitService:
    def __init__(self, client=redis_client):
        self._client = client

    async def check_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, int]:
        if not self._client.is_active():
            return True, 0

        is_allowed, _ = await self._client.check_rate_limit(key, limit, window)

        if not is_allowed:
            retry_after = await self._client.get_ttl(key)
            return False, retry_after if retry_after > 0 else window

        return True, 0

    async def reset(self, key: str) -> None:
        if self._client.is_active() and self._client.client:
            await self._client.client.delete(key)
