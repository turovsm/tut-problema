from app.application.dto.users import UpdateUserDTO
from app.domain.entities.user import User
from app.domain.exceptions.user import (
    UsernameTakenException,
    UserNotFoundException,
)
from app.domain.interfaces.repositories.user_repository import IUserRepository


class UpdateUserUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, dto: UpdateUserDTO) -> User:
        # 1. Поиск пользователя в репозитории
        user = await self.user_repo.get_by_id(dto.user_id)
        if not user:
            raise UserNotFoundException()

        # 2. Если имя пользователя меняется, проверяем его уникальность
        if dto.username and dto.username != user.username:
            existing_user = await self.user_repo.get_by_username(dto.username)

            # Если имя занято другим пользователем — выбрасываем исключение
            if existing_user and existing_user.id != user.id:
                raise UsernameTakenException()

            user.username = dto.username

        # 3. Сохранение обновленной сущности
        return await self.user_repo.save(user)
