from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    status: str = Field(default="success", title="Status")
    data: T | None = Field(default=None, title="Data")
    message: str | None = Field(default=None, title="Message")


class Location(BaseModel):
    type: str = Field(default="Point", title="Type")
    coordinates: list[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        title="Coordinates",
        description="[longitude, latitude]",
    )


class ValidationErrorDetail(BaseModel):
    loc: list[str | int] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")
    input: object | None = Field(default=None, title="Input")
    ctx: dict | None = Field(default=None, title="Context")


class HTTPValidationError(BaseModel):
    detail: list[ValidationErrorDetail] | None = Field(None, title="Detail")


class PaginationQuery(BaseModel):
    page: int = Field(1, ge=1, title="Page")
    limit: int = Field(
        settings.DEFAULT_PAGE_SIZE,
        ge=settings.MIN_PAGE_SIZE,
        le=settings.MAX_PAGE_SIZE,
        title="Limit",
    )


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T] = Field(..., title="Items")
    total: int = Field(..., title="Total")
    page: int = Field(..., title="Page")
    limit: int = Field(..., title="Limit")
    has_next: bool = Field(..., title="Has Next")
