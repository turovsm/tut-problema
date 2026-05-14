from fastapi import APIRouter, Depends

from app.presentation.api.rate_limit import rate_limit_api, rate_limit_auth
from app.presentation.api.v1.endpoints import (
    auth,
    reports,
    uploads,
    users,
    votes,
)

api_router = APIRouter()

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(rate_limit_auth)],
)

api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["Reports"],
    dependencies=[Depends(rate_limit_api)],
)

api_router.include_router(
    votes.router,
    prefix="/votes",
    tags=["Votes"],
    dependencies=[Depends(rate_limit_api)],
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(rate_limit_api)],
)

api_router.include_router(
    uploads.router,
    prefix="/uploads",
    tags=["Uploads"],
    dependencies=[Depends(rate_limit_api)],
)
