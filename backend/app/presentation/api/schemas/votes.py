from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.domain.entities.enums import ReportStatus, VoteType

from .common import PaginatedResponse, PaginationQuery


class VoteCreate(BaseModel):
    vote_type: VoteType = Field(..., title="Vote Type")
    user_location_lng: float = Field(..., title="User Location Lng")
    user_location_lat: float = Field(..., title="User Location Lat")
    accuracy: float | None = Field(
        None, ge=0.0, le=settings.VOTE_ACCURACY_MAX, title="Accuracy"
    )


class VoteQuery(PaginationQuery):
    pass


class VoteResponse(BaseModel):
    id: UUID = Field(..., title="Id")
    report_id: UUID = Field(..., title="Report Id")
    vote_type: VoteType = Field(..., title="Vote Type")
    is_verified: bool = Field(..., title="Is Verified")
    created_at: datetime = Field(..., title="Created At")

    model_config = ConfigDict(from_attributes=True)


class VoteListResponse(PaginatedResponse[VoteResponse]):
    pass


class VoteStatsResponse(BaseModel):
    report_id: UUID = Field(..., title="Report Id")
    confirm_count: int = Field(..., title="Confirm Count")
    dismiss_count: int = Field(..., title="Dismiss Count")
    current_status: ReportStatus = Field(..., title="Current Status")

    model_config = ConfigDict(from_attributes=True)
