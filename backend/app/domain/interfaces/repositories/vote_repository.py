from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.vote import Vote


class IVoteRepository(ABC):
    @abstractmethod
    async def get_user_vote(
        self, user_id: UUID, report_id: UUID
    ) -> Vote | None: ...

    @abstractmethod
    async def get_votes_for_reports(
        self, user_id: UUID, report_ids: list[UUID]
    ) -> dict[UUID, Vote]: ...

    @abstractmethod
    async def save(self, vote: Vote) -> Vote: ...

    @abstractmethod
    async def delete(self, user_id: UUID, report_id: UUID) -> None: ...

    @abstractmethod
    async def get_stats_by_report(self, report_id: UUID) -> dict[str, int]: ...

    @abstractmethod
    async def get_user_votes_paginated(
        self, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[Vote], int]: ...
