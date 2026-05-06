from fastapi import APIRouter, Depends

from app.api.v1.endpoints import auth, reports, users, votes, uploads
from app.core.config import settings
from app.infrastructure.rate_limiter import rate_limit_auth, rate_limit_api

api_router = APIRouter()

auth_deps = [Depends(rate_limit_auth)] if settings.RATE_LIMIT_ENABLED else []
api_deps = [Depends(rate_limit_api)] if settings.RATE_LIMIT_ENABLED else []

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    dependencies=auth_deps
)
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
    dependencies=api_deps
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    dependencies=api_deps
)
api_router.include_router(
    votes.router,
    prefix="/votes",
    tags=["Votes"],
    dependencies=api_deps
)
api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["Uploads"],
    dependencies=api_deps
)
