from typing import Optional

from fastapi import Request, HTTPException, status

from app.config import settings
from app.database.redis_client import redis_client


class RateLimiter:
    def __init__(self):
        self.enabled = settings.RATE_LIMIT_ENABLED

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    @staticmethod
    def _get_user_id(request: Request) -> Optional[str]:
        return getattr(request.state, "user_id", None)

    def _get_key(self, request: Request, key_type: str) -> str:
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)

        if user_id and settings.RATE_LIMIT_BY_USER:
            return f"rate_limit:{key_type}:user:{user_id}"
        return f"rate_limit:{key_type}:ip:{client_ip}"

    async def check_rate_limit(
            self,
            request: Request,
            key_type: str = "global",
            limit: Optional[int] = None,
            window: Optional[int] = None
    ) -> bool:
        if not self.enabled:
            return True

        if limit is None:
            limit = getattr(settings, f"RATE_LIMIT_{key_type.upper()}_REQUESTS", settings.RATE_LIMIT_REQUESTS)
        if window is None:
            window = getattr(settings, f"RATE_LIMIT_{key_type.upper()}_PERIOD_SECONDS",
                             settings.RATE_LIMIT_PERIOD_SECONDS)

        key = self._get_key(request, key_type)

        allowed, _ = await redis_client.check_rate_limit(key, limit, window)

        if not allowed:
            ttl = await redis_client.get_ttl(key)
            request.state.rate_limit_retry_after = ttl if ttl > 0 else window
            return False

        return True

    async def get_remaining(self, request: Request, key_type: str = "global") -> int:
        if not self.enabled:
            return -1

        limit = getattr(settings, f"RATE_LIMIT_{key_type.upper()}_REQUESTS", settings.RATE_LIMIT_REQUESTS)
        key = self._get_key(request, key_type)

        current = await redis_client.get(key)
        if current is None:
            return limit

        count = int(current)
        return max(0, limit - count)

    async def reset_limit(self, request: Request, key_type: str = "global") -> bool:
        if not self.enabled:
            return False

        key = self._get_key(request, key_type)
        return await redis_client.delete(key)


rate_limiter = RateLimiter()


async def rate_limit_global(request: Request):
    if not await rate_limiter.check_rate_limit(request, "global"):
        retry_after = getattr(request.state, "rate_limit_retry_after", 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


async def rate_limit_auth(request: Request):
    if not await rate_limiter.check_rate_limit(request, "auth"):
        retry_after = getattr(request.state, "rate_limit_retry_after", 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )


async def rate_limit_api(request: Request):
    if not await rate_limiter.check_rate_limit(request, "api"):
        retry_after = getattr(request.state, "rate_limit_retry_after", 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
