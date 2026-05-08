from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.config import settings


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    GOV_ORG = "gov_org"


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserResponse(UserBase):
    id: UUID
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        None,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        pattern=settings.USERNAME_ALLOWED_PATTERN,
    )


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
