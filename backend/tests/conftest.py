import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.sql import text
from testcontainers.core.container import DockerContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.config import settings
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import get_db
from app.infrastructure.redis.client import redis_client
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def containers_infra():
    # 1. Postgres с поддержкой PostGIS
    postgres = PostgresContainer("postgis/postgis:16-3.4", driver="asyncpg")
    # 2. Redis для лимитов
    redis_cont = RedisContainer("redis:7-alpine")
    # 3. Mailpit для тестирования почты
    mailpit = DockerContainer("axllent/mailpit").with_exposed_ports(1025, 8025)

    with postgres, redis_cont, mailpit:
        settings.DATABASE_URL = postgres.get_connection_url()

        settings.REDIS_HOST = redis_cont.get_container_host_ip()
        settings.REDIS_PORT = int(redis_cont.get_exposed_port(6379))
        settings.RATE_LIMIT_ENABLED = True

        settings.SMTP_HOST = mailpit.get_container_host_ip()
        settings.SMTP_PORT = int(mailpit.get_exposed_port(1025))
        settings.SMTP_USE_TLS = False
        settings.SMTP_USER = ""
        settings.SMTP_PASSWORD = ""
        os.environ["MAILPIT_API_URL"] = (
            f"http://{settings.SMTP_HOST}:{mailpit.get_exposed_port(8025)}/api/v1"
        )

        yield {
            "postgres": postgres,
            "redis": redis_cont,
            "mailpit": mailpit,
        }


@pytest_asyncio.fixture(scope="session")
async def setup_db(containers_infra):
    engine = create_async_engine(
        settings.DATABASE_URL, poolclass=pool.NullPool
    )
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    connection = await setup_db.connect()
    trans = await connection.begin()
    Session = async_sessionmaker(
        bind=connection, expire_on_commit=False, class_=AsyncSession
    )
    session = Session()

    yield session

    await session.close()
    await trans.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db

    from app.infrastructure.mail.smtp_email_provider import SmtpEmailProvider
    from app.presentation.api import deps

    deps.email_provider = SmtpEmailProvider()

    await redis_client.disconnect()
    await redis_client.connect()

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac

    await redis_client.disconnect()
    app.dependency_overrides.clear()
