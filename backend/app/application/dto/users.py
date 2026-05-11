from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UpdateUserDTO:
    user_id: UUID
    username: str | None = None


@dataclass(frozen=True)
class GetUserVotesDTO:
    user_id: UUID
    page: int = 1
    limit: int = 20
