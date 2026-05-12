from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.config import settings
from app.domain.entities.enums import UserRole
from app.domain.services.password_validator import PasswordValidator

from .common import PaginatedResponse, PaginationQuery


def validate_password_strength(v: str) -> str:
    PasswordValidator.validate(
        password=v,
        min_length=settings.PASSWORD_MIN_LENGTH,
        max_length=settings.PASSWORD_MAX_LENGTH,
        require_uppercase=settings.PASSWORD_REQUIRE_UPPERCASE,
        require_lowercase=settings.PASSWORD_REQUIRE_LOWERCASE,
        require_digits=settings.PASSWORD_REQUIRE_DIGITS,
        require_special=settings.PASSWORD_REQUIRE_SPECIAL,
        special_chars=settings.PASSWORD_SPECIAL_CHARS,
        forbidden_passwords=settings.COMMON_PASSWORDS,
    )
    return v


class UserResponse(BaseModel):
    email: EmailStr = Field(..., title="Email")
    username: str = Field(..., title="Username")
    id: UUID = Field(..., title="Id")
    role: UserRole = Field(..., title="Role")
    is_active: bool = Field(..., title="Is Active")
    is_verified: bool = Field(..., title="Is Verified")
    created_at: datetime = Field(..., title="Created At")

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class UserListQuery(PaginationQuery):
    pass


class UserListResponse(PaginatedResponse[UserResponse]):
    pass


class UserRegistration(BaseModel):
    email: EmailStr = Field(
        ...,
        min_length=settings.EMAIL_MIN_LENGTH,
        max_length=settings.EMAIL_MAX_LENGTH,
        title="Email",
    )
    username: str = Field(
        ...,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        pattern=settings.USERNAME_ALLOWED_PATTERN,
        title="Username",
    )
    password: str = Field(..., title="Password")

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    username: str | None = Field(
        None,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        pattern=settings.USERNAME_ALLOWED_PATTERN,
        title="Username",
    )


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., title="Email")
    password: str = Field(..., title="Password")
    remember_me: bool = Field(default=False, title="Remember Me")


class EmailVerificationRequest(BaseModel):
    token: UUID = Field(..., title="Token")


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., title="Email")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., title="Current Password")
    new_password: str = Field(..., title="New Password")

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., title="Email")


class ResetPasswordRequest(BaseModel):
    token: UUID = Field(..., title="Token")
    new_password: str = Field(..., title="New Password")

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)
