from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.schemas.common import Location

class IssueType(str, Enum):
    SNOW = "snow"
    POTHOLE = "pothole"
    ROAD_OBSTRUCTION = "road_obstruction"
    FLOODING = "flooding"
    BROKEN_STREETLIGHT = "broken_streetlight"
    BROKEN_SIDEWALK = "broken_sidewalk"
    WATER_LEAK = "water_leak"
    SEWER_OVERFLOW = "sewer_overflow"
    ILLEGAL_DUMPING = "illegal_dumping"
    OTHER = "other"

class ReportStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    RESOLVED = "resolved"

class ReportUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ReportStatus] = None

class ReportPhotoResponse(BaseModel):
    id: UUID
    file_name: str
    file_url: str
    uploaded_at: datetime

class ReportResponse(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    issue_type: IssueType
    location: Location
    status: ReportStatus
    created_by: dict
    created_at: datetime
    updated_at: datetime
    photos: List[ReportPhotoResponse] = []
    user_vote: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    limit: int
    has_next: bool

class ReportItemsResponse(BaseModel):
    items: List[ReportResponse]

class ReportIdResponse(BaseModel):
    id: UUID