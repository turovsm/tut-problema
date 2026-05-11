from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

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


def setup_exception_handlers(app: FastAPI):
    app.add_exception_handler(DomainException, domain_exception_handler)
