from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions.base import (
    AlreadyExistsException,
    BusinessRuleException,
    DomainException,
    EntityNotFoundException,
    PermissionDeniedException,
    UnauthorizedException,
)
from app.domain.exceptions.user import EmailNotVerifiedException


async def domain_exception_handler(request: Request, exc: DomainException):
    if isinstance(exc, EntityNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, UnauthorizedException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, PermissionDeniedException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, EmailNotVerifiedException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, AlreadyExistsException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, BusinessRuleException):
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_400_BAD_REQUEST

    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "error": exc.message, "code": status_code},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "code": exc.status_code,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error": "Validation error",
            "details": exc.errors(),
            "code": 422,
        },
    )


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(DomainException, domain_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )
