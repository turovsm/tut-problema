from uuid import UUID

from app.domain.exceptions.base import EntityNotFoundException
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class RemoveVoteUseCase:
    def __init__(self, vote_repo: IVoteRepository):
        self.vote_repo = vote_repo

    async def execute(self, user_id: UUID, report_id: UUID) -> None:
        # 1. Проверяем, существует ли голос
        vote = await self.vote_repo.get_user_vote(
            user_id=user_id, report_id=report_id
        )

        if not vote:
            raise EntityNotFoundException("Vote not found")

        # 2. Удаляем голос из репозитория
        await self.vote_repo.delete(user_id=user_id, report_id=report_id)
