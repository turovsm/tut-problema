import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars
from uvicorn import run

from app.config import settings
from app.database.redis_client import redis_client
from app.database.session import init_db, create_tables, get_engine
from app.logging_config import setup_logging, get_logger
from app.rate_limiter import rate_limit_auth, rate_limit_api
from app.routers import auth_router, reports_router, votes_router, users_router, uploads_router

setup_logging()
logger = get_logger("app.main")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        start_time = time.time()
        logger.info("Request started")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            log_method = logger.warning if process_time > 0.5 else logger.info
            log_method(
                "Request completed",
                status_code=response.status_code,
                process_time=f"{process_time:.3f}s",
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                error=str(e),
                error_type=type(e).__name__,
                process_time=f"{process_time:.3f}s",
                exc_info=True,
            )
            raise
        finally:
            clear_contextvars()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Starting up application...")
    try:
        await init_db()
        await create_tables()
        await redis_client.connect()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error("Failed to start application", error=str(e), exc_info=True)
        raise

    yield

    logger.info("Shutting down application...")
    await redis_client.disconnect()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS if hasattr(settings, 'ALLOWED_HOSTS') else ["localhost", "127.0.0.1"]
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

if settings.RATE_LIMIT_ENABLED:
    app.include_router(auth_router, prefix=settings.API_PREFIX, dependencies=[Depends(rate_limit_auth)])
    app.include_router(uploads_router, prefix=settings.API_PREFIX, dependencies=[Depends(rate_limit_api)])
    app.include_router(reports_router, prefix=settings.API_PREFIX, dependencies=[Depends(rate_limit_api)])
    app.include_router(votes_router, prefix=settings.API_PREFIX, dependencies=[Depends(rate_limit_api)])
    app.include_router(users_router, prefix=settings.API_PREFIX, dependencies=[Depends(rate_limit_api)])
else:
    app.include_router(auth_router, prefix=settings.API_PREFIX)
    app.include_router(reports_router, prefix=settings.API_PREFIX)
    app.include_router(votes_router, prefix=settings.API_PREFIX)
    app.include_router(users_router, prefix=settings.API_PREFIX)
    app.include_router(uploads_router, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    logger.debug("Root endpoint accessed")
    return {"name": settings.APP_NAME, "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/health/detailed")
async def detailed_health():
    engine = await get_engine()
    pool = engine.pool

    health_data = {
        "status": "healthy",
        "database": {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "overflow": pool.overflow(),
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_pre_ping": settings.DB_POOL_PRE_PING
        },
        "redis": "connected" if redis_client.is_enabled() else "disabled"
    }
    return health_data


if __name__ == "__main__":
    workers = getattr(settings, 'WORKERS', 1)
    reload = getattr(settings, 'RELOAD', settings.DEBUG)
    run("app.main:app", host=settings.HOST, port=settings.PORT, reload=reload, workers=workers)
