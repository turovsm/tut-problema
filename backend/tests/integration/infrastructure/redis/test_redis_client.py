import pytest
import pytest_asyncio

from app.infrastructure.redis.client import redis_client
from app.infrastructure.redis.rate_limit_service import RateLimitService


@pytest.mark.usefixtures("containers_infra")
class TestRedisIntegration:
    @pytest_asyncio.fixture(autouse=True)
    async def prepare_redis(self):
        await redis_client.connect()
        if redis_client.client:
            await redis_client.client.flushdb()
        yield
        await redis_client.disconnect()

    async def test_redis_connection(self):
        assert redis_client.is_active() is True
        assert await redis_client.client.ping() is True

    async def test_rate_limit_lua_script(self):
        key = "test_limit_key"
        limit = 2
        window = 10

        allowed, count = await redis_client.check_rate_limit(
            key, limit, window
        )
        assert allowed is True
        assert count == 1

        allowed, count = await redis_client.check_rate_limit(
            key, limit, window
        )
        assert allowed is True
        assert count == 2

        allowed, count = await redis_client.check_rate_limit(
            key, limit, window
        )
        assert allowed is False
        assert count == 3

    async def test_rate_limit_ttl_refresh(self):
        key = "test_ttl_key"
        await redis_client.check_rate_limit(key, limit=5, window=60)
        ttl = await redis_client.get_ttl(key)
        assert 0 < ttl <= 60

    async def test_rate_limit_service_reset(self):
        service = RateLimitService()
        key = "reset_key"

        await service.check_limit(key, limit=1, window=60)
        allowed, _ = await service.check_limit(key, limit=1, window=60)
        assert allowed is False

        await service.reset(key)

        allowed, _ = await service.check_limit(key, limit=1, window=60)
        assert allowed is True
