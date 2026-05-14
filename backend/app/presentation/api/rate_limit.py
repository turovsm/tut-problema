from fastapi import HTTPException, Request, status

from app.core.config import settings
from app.infrastructure.redis.rate_limit_service import RateLimitService

_rate_limit_service = RateLimitService()


class RateLimitDependency:
    def __init__(self, key_type: str, limit: int, window: int):
        self.key_type = key_type
        self.limit = limit
        self.window = window

    async def __call__(self, request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return

        user_id = getattr(request.state, "user_id", None)

        if user_id and settings.RATE_LIMIT_BY_USER:
            identifier = f"user:{user_id}"
        else:
            client_ip = request.client.host if request.client else "unknown"
            identifier = f"ip:{client_ip}"

        key = f"rate_limit:{self.key_type}:{identifier}"

        is_allowed, retry_after = await _rate_limit_service.check_limit(
            key=key, limit=self.limit, window=self.window
        )

        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )


# TODO: создать и прокинуть остальные ограничения

rate_limit_auth = RateLimitDependency(
    key_type="auth",
    limit=settings.RATE_LIMIT_AUTH_REQUESTS,
    window=settings.RATE_LIMIT_AUTH_PERIOD_SECONDS,
)

rate_limit_api = RateLimitDependency(
    key_type="api",
    limit=settings.RATE_LIMIT_API_REQUESTS,
    window=settings.RATE_LIMIT_API_PERIOD_SECONDS,
)
