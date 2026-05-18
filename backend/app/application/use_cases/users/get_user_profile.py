from uuid import UUID

from app.domain.entities.user import User
from app.domain.exceptions.user import UserNotFoundException
from app.domain.interfaces.repositories.user_repository import IUserRepository


class GetUserProfileUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, user_id: UUID) -> User:
        # 1. Поиск пользователя в репозитории
        user = await self.user_repo.get_by_id(user_id)

        # 2. Если пользователь не найден — выбрасываем исключение
        if not user:
            raise UserNotFoundException()

        return user
