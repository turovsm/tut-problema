from app.application.dto.users import ToggleUserStatusDTO
from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.exceptions.user import UserNotFoundException
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ToggleUserStatusUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, dto: ToggleUserStatusDTO) -> User:
        # Проверка прав (только модераторы)
        if dto.current_user_role != UserRole.MODERATOR:
            raise PermissionDeniedException(
                "Only moderators can toggle user status"
            )

        # Ищем пользователя
        user = await self.user_repo.get_by_id(dto.target_user_id)
        if not user:
            raise UserNotFoundException()

        # Не даем модератору забанить другого модератора / себя (вдруг захочет)
        if user.role == UserRole.MODERATOR:
            raise PermissionDeniedException(
                "Cannot change status of another moderator"
            )

        # Меняем статус и сохраняем
        user.is_active = dto.is_active
        return await self.user_repo.save(user)
