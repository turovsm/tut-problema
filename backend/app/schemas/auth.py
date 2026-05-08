from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings
from app.schemas.user import UserResponse


def validate_password_strength(v: str) -> str:
    if len(v) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        )
    if len(v) > settings.PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must be no more than {settings.PASSWORD_MAX_LENGTH} characters"
        )
    if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
        raise ValueError("Password must contain at least one uppercase letter")
    if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in v):
        raise ValueError("Password must contain at least one lowercase letter")
    if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in v):
        raise ValueError("Password must contain at least one number")
    if settings.PASSWORD_REQUIRE_SPECIAL and not any(
        c in settings.PASSWORD_SPECIAL_CHARS for c in v
    ):
        raise ValueError(
            f"Password must contain at least one special character"
        )
    if (
        settings.PASSWORD_DISALLOW_COMMON
        and v.lower() in settings.COMMON_PASSWORDS
    ):
        raise ValueError("Password is too common.")
    return v


class UserRegistration(BaseModel):
    email: EmailStr = Field(
        ...,
        min_length=settings.EMAIL_MIN_LENGTH,
        max_length=settings.EMAIL_MAX_LENGTH,
    )
    username: str = Field(
        ...,
        min_length=settings.USERNAME_MIN_LENGTH,
        max_length=settings.USERNAME_MAX_LENGTH,
        pattern=settings.USERNAME_ALLOWED_PATTERN,
    )
    password: str = Field(..., min_length=settings.PASSWORD_MIN_LENGTH)

    @field_validator("password")
    @classmethod
    def validate_registration_password(cls, v: str) -> str:
        return validate_password_strength(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class UserDataWrapper(BaseModel):
    user: UserResponse


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
