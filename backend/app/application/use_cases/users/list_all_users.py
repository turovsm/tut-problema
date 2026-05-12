from app.application.dto.users import ListUsersDTO
from app.domain.entities.enums import UserRole
from app.domain.entities.user import User
from app.domain.exceptions.base import PermissionDeniedException
from app.domain.interfaces.repositories.user_repository import IUserRepository


class ListAllUsersUseCase:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def execute(self, dto: ListUsersDTO) -> tuple[list[User], int]:
        # 1. Проверка прав доступа
        if dto.user_role not in [UserRole.MODERATOR, UserRole.GOV_ORG]:
            raise PermissionDeniedException(
                "Insufficient permissions to view all users"
            )

        # 2. Получение данных из репозитория
        offset = (dto.page - 1) * dto.limit
        users, total = await self.user_repo.get_all(
            limit=dto.limit, offset=offset
        )

        return users, total
