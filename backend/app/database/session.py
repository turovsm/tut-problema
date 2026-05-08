from asyncio import sleep
from typing import AsyncGenerator, Optional

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.database.base import Base

engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


async def get_engine() -> AsyncEngine:
    global engine
    if engine is None:
        engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=settings.DB_POOL_PRE_PING,
            echo=settings.DB_ECHO,
            pool_recycle=3600,
        )
    return engine


async def get_session_local() -> async_sessionmaker:
    global AsyncSessionLocal
    if AsyncSessionLocal is None:
        engine_instance = await get_engine()
        AsyncSessionLocal = async_sessionmaker(
            engine_instance,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return AsyncSessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_local = await get_session_local()
    async with session_local() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(max_retries: int = None, delay: int = None) -> AsyncEngine:
    max_retries = max_retries or settings.DB_MAX_RETRIES
    delay = delay or settings.DB_RETRY_DELAY_SECONDS
    engine_instance = await get_engine()

    for attempt in range(max_retries):
        try:
            async with engine_instance.connect() as conn:
                await conn.execute(text("SELECT 1"))
                await conn.commit()
                print(
                    f"Successfully connected to database on attempt {attempt + 1}"
                )

                await conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS postgis")
                )
                await conn.commit()
                print("PostGIS extension created successfully")

                return engine_instance
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await sleep(delay)
            else:
                print("Could not connect to database after multiple attempts")
                raise
    return engine_instance


async def create_tables() -> AsyncEngine:
    print("Creating database tables...")
    engine_instance = await get_engine()

    async with engine_instance.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with engine_instance.connect() as conn:
        tables = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_table_names()
        )
        print(f"Tables created successfully: {tables}")

    return engine_instance
