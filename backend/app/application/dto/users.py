from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.enums import UserRole


@dataclass(frozen=True)
class UpdateUserDTO:
    user_id: UUID
    username: str | None = None


@dataclass(frozen=True)
class GetUserVotesDTO:
    user_id: UUID
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ListUsersDTO:
    user_role: UserRole
    page: int = 1
    limit: int = 20


@dataclass(frozen=True)
class ToggleUserStatusDTO:
    target_user_id: UUID
    is_active: bool
    current_user_role: UserRole
