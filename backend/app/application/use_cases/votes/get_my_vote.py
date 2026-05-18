from uuid import UUID

from app.domain.entities.vote import Vote
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetMyVoteUseCase:
    def __init__(self, vote_repo: IVoteRepository):
        self.vote_repo = vote_repo

    async def execute(self, user_id: UUID, report_id: UUID) -> Vote | None:
        # 1. Запрашиваем голос
        vote = await self.vote_repo.get_user_vote(
            user_id=user_id, report_id=report_id
        )

        # 2. Возвращаем сущность
        return vote
