from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.core.config import settings
from app.schemas.common import Location

class VoteType(str, Enum):
    CONFIRM = "confirm"
    DISMISS = "dismiss"

class VoteCreate(BaseModel):
    vote_type: VoteType
    user_location: Location
    accuracy: Optional[float] = Field(None, ge=0, le=settings.VOTE_ACCURACY_MAX)

class VoteResponse(BaseModel):
    id: UUID
    report_id: UUID
    vote_type: VoteType
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VoteListResponse(BaseModel):
    items: List[VoteResponse]
    total: int
    page: int
    limit: int

class VoteStatsResponse(BaseModel):
    report_id: UUID
    confirm_count: int
    dismiss_count: int
    current_status: str