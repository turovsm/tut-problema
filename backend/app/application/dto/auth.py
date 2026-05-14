from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.user import User


@dataclass(frozen=True)
class RegisterUserDTO:
    email: str
    username: str
    password: str


@dataclass(frozen=True)
class LoginDTO:
    email: str
    password: str


@dataclass(frozen=True)
class VerifyEmailDTO:
    token: UUID


@dataclass(frozen=True)
class ResendVerificationDTO:
    email: str


@dataclass(frozen=True)
class ChangePasswordDTO:
    user_id: UUID
    current_password: str
    new_password: str


@dataclass(frozen=True)
class ForgotPasswordDTO:
    email: str


@dataclass(frozen=True)
class ResetPasswordDTO:
    token: UUID
    new_password: str


@dataclass(frozen=True)
class AuthResultDTO:
    user: User
    access_token: str
    refresh_token: str
    access_max_age: int
    refresh_max_age: int


@dataclass(frozen=True)
class RefreshResultDTO:
    user: User
    access_token: str
    refresh_token: str
    access_max_age: int
    refresh_max_age: int


@dataclass(frozen=True)
class RefreshTokenDTO:
    refresh_token: str
