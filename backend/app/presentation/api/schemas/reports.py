from datetime import datetime
from uuid import UUID

from fastapi import Form
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.domain.entities.enums import IssueType, ReportStatus, VoteType

from .auth import UserResponse
from .common import Location, PaginatedResponse, PaginationQuery


class ReportFilterQuery(PaginationQuery):
    issue_type: IssueType | None = Field(None, title="Issue Type")
    status_filter: ReportStatus | None = Field(None, title="Status Filter")


class NearbyReportQuery(BaseModel):
    lat: float = Field(..., ge=-90, le=90, title="Lat")
    lon: float = Field(..., ge=-180, le=180, title="Lon")
    radius: int = Field(
        settings.DEFAULT_RADIUS_METERS,
        ge=settings.MIN_RADIUS_METERS,
        le=settings.MAX_RADIUS_METERS,
        title="Radius",
    )
    limit: int = Field(
        settings.DEFAULT_PAGE_SIZE,
        ge=settings.MIN_PAGE_SIZE,
        le=settings.MAX_PAGE_SIZE,
        title="Limit",
    )


class ReportCreateForm(BaseModel):
    title: str = Field(
        ...,
        min_length=settings.REPORT_TITLE_MIN_LENGTH,
        max_length=settings.REPORT_TITLE_MAX_LENGTH,
        title="Title",
    )
    description: str | None = Field(
        None,
        max_length=settings.REPORT_DESCRIPTION_MAX_LENGTH,
        title="Description",
    )
    issue_type: IssueType = Field(..., title="Issue Type")
    location_lng: float = Field(..., title="Location Lng")
    location_lat: float = Field(..., title="Location Lat")
    user_location_lng: float = Field(..., title="User Location Lng")
    user_location_lat: float = Field(..., title="User Location Lat")

    @classmethod
    def as_form(
        cls,
        title: str = Form(...),
        description: str | None = Form(None),
        issue_type: IssueType = Form(...),
        location_lng: float = Form(...),
        location_lat: float = Form(...),
        user_location_lng: float = Form(...),
        user_location_lat: float = Form(...),
    ):
        return cls(
            title=title,
            issue_type=issue_type,
            location_lng=location_lng,
            location_lat=location_lat,
            user_location_lng=user_location_lng,
            user_location_lat=user_location_lat,
            description=description,
        )


class ReportPhotoResponse(BaseModel):
    id: UUID = Field(..., title="Id")
    file_name: str = Field(..., title="File Name")
    file_url: str = Field(..., title="File Url")
    uploaded_at: datetime = Field(..., title="Uploaded At")

    model_config = ConfigDict(from_attributes=True)


class ReportResponse(BaseModel):
    id: UUID = Field(..., title="Id")
    title: str = Field(..., title="Title")
    description: str | None = Field(None, title="Description")
    issue_type: IssueType = Field(..., title="IssueType")
    location: Location = Field(..., title="Location")
    status: ReportStatus = Field(..., title="ReportStatus")
    created_by: UserResponse = Field(..., title="Created By")
    created_at: datetime = Field(..., title="Created At")
    updated_at: datetime = Field(..., title="Updated At")
    photos: list[ReportPhotoResponse] = Field(default=[], title="Photos")
    user_vote: VoteType | None = Field(None, title="User Vote")

    model_config = ConfigDict(from_attributes=True)


class ReportListQuery(PaginationQuery):
    pass


class ReportListResponse(PaginatedResponse[ReportResponse]):
    pass


class ReportItemsResponse(BaseModel):
    items: list[ReportResponse] = Field(..., title="Items")


class ReportIdResponse(BaseModel):
    id: UUID = Field(..., title="Id")


class ReportUpdate(BaseModel):
    title: str | None = Field(
        None,
        min_length=settings.REPORT_TITLE_MIN_LENGTH,
        max_length=settings.REPORT_TITLE_MAX_LENGTH,
        title="Title",
    )
    description: str | None = Field(
        None,
        max_length=settings.REPORT_DESCRIPTION_MAX_LENGTH,
        title="Description",
    )
    status: ReportStatus | None = Field(None, title="Status")
