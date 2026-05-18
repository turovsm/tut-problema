from app.application.dto.users import GetUserVotesDTO
from app.domain.entities.vote import Vote
from app.domain.interfaces.repositories.vote_repository import IVoteRepository


class GetUserVotesUseCase:
    def __init__(self, vote_repo: IVoteRepository):
        self.vote_repo = vote_repo

    async def execute(self, dto: GetUserVotesDTO) -> tuple[list[Vote], int]:
        # 1. Рассчитываем смещение для пагинации
        offset = (dto.page - 1) * dto.limit

        # 2. Получаем данные из репозитория
        votes, total = await self.vote_repo.get_user_votes_paginated(
            user_id=dto.user_id, limit=dto.limit, offset=offset
        )

        return votes, total
