from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.config import settings


def validate_password_strength(v: str) -> str:
    if len(v) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")

    if len(v) > settings.PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be no more than {settings.PASSWORD_MAX_LENGTH} characters")

    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")

    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")

    if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one number")

    if settings.PASSWORD_REQUIRE_SPECIAL and not any(c in settings.PASSWORD_SPECIAL_CHARS for c in v):
        raise ValueError(f"Password must contain at least one special character ({settings.PASSWORD_SPECIAL_CHARS})")

    if settings.PASSWORD_DISALLOW_COMMON and v.lower() in settings.COMMON_PASSWORDS:
        raise ValueError("Password is too common. Please choose a stronger password")

    return v


class UserRole(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    GOV_ORG = "gov_org"


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


class VoteType(str, Enum):
    CONFIRM = "confirm"
    DISMISS = "dismiss"


class Location(BaseModel):
    type: str = "Point"
    coordinates: List[float] = Field(..., min_length=2, max_length=2)

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, v: List[float]) -> List[float]:
        lng, lat = v
        if not (-180 <= lng <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {lng}")
        if not (-90 <= lat <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
        return v


class User(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserRegistration(BaseModel):
    email: EmailStr = Field(..., min_length=settings.EMAIL_MIN_LENGTH, max_length=settings.EMAIL_MAX_LENGTH)
    username: str = Field(..., min_length=settings.USERNAME_MIN_LENGTH, max_length=settings.USERNAME_MAX_LENGTH,
                          pattern=settings.USERNAME_ALLOWED_PATTERN)
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)

    @field_validator("password")
    @classmethod
    def validate_registration_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=settings.USERNAME_MIN_LENGTH,
                                    max_length=settings.USERNAME_MAX_LENGTH, pattern=settings.USERNAME_ALLOWED_PATTERN)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int
    user: User


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_change_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: UUID
    new_password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_reset_password(cls, v: str) -> str:
        return validate_password_strength(v)


class EmailVerificationRequest(BaseModel):
    token: UUID


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=settings.REPORT_TITLE_MIN_LENGTH, max_length=settings.REPORT_TITLE_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=settings.REPORT_DESCRIPTION_MAX_LENGTH)
    issue_type: IssueType
    location_lng: float = Field(..., description="Longitude of the reported issue")
    location_lat: float = Field(..., description="Latitude of the reported issue")
    user_location_lng: float = Field(..., description="Longitude of the user's location")
    user_location_lat: float = Field(..., description="Latitude of the user's location")

    @field_validator("location_lng", "user_location_lng")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {v}")
        return v

    @field_validator("location_lat", "user_location_lat")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {v}")
        return v


class ReportUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=settings.REPORT_TITLE_MIN_LENGTH,
                                 max_length=settings.REPORT_TITLE_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=settings.REPORT_DESCRIPTION_MAX_LENGTH)
    status: Optional[ReportStatus] = None


class PhotoUploadResponse(BaseModel):
    id: UUID
    file_name: str
    file_url: str
    uploaded_at: datetime


class ReportPhotoResponse(BaseModel):
    id: UUID
    file_name: str
    file_url: str
    uploaded_at: datetime


class Report(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    issue_type: IssueType
    location: Location
    address: Optional[str] = None
    status: ReportStatus
    created_by: User
    created_at: datetime
    updated_at: datetime
    photos: List[ReportPhotoResponse] = []
    user_vote: Optional[VoteType] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    items: List[Report]
    total: int
    page: int
    limit: int
    has_next: bool


class VoteCreate(BaseModel):
    vote_type: VoteType
    user_location: Location
    accuracy: Optional[float] = Field(None, ge=0, le=settings.VOTE_ACCURACY_MAX)


class Vote(BaseModel):
    id: UUID
    report_id: UUID
    vote_type: VoteType
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    status: str = "success"
    data: Optional[dict] = None
    message: Optional[str] = None
